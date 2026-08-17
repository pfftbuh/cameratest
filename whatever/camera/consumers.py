"""
WebSocket endpoint for live proctoring.

One connection == one student == one GazeSession. The browser pushes JPEG frames
as binary messages and control commands as JSON text; every frame comes back as a
JSON result. Nothing here holds module-level state, so two students connecting at
once get fully independent pipelines.

Protocol
--------
client -> server
    <binary>                                 a JPEG frame
    {"type": "calibrate_next"}               advance calibration (was the '{' key)
    {"type": "keystrokes", "keys": [...]}    suspicious keys seen in the browser
    {"type": "ping"}                         keepalive

server -> client
    {"type": "ready", ...}                   sent once the pipeline is warm
    {"type": "frame_result", ...}            one per processed frame
    {"type": "calibration", ...}             reply to calibrate_next
    {"type": "session_closed", ...}
    {"type": "error", "message": ...}
"""

import json
import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

from gaze_session import GazeSession

logger = logging.getLogger(__name__)


class ProctorConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.session = None
        self.busy = False
        self._calibration_saved = False  # Flag to prevent duplicate saves

        # No login system exists yet, so anonymous connections are allowed by
        # default. Flip GAZE_REQUIRE_AUTH once students actually sign in.
        if getattr(settings, 'GAZE_REQUIRE_AUTH', False):
            user = self.scope.get('user')
            if user is None or not user.is_authenticated:
                await self.close(code=4401)
                return

        await self.accept()

        # Constructing a GazeSession loads two MediaPipe models (~1s), which would
        # stall the whole server if it ran on the event loop.
        try:
            self.session = await sync_to_async(self._build_session, thread_sensitive=False)()
        except Exception:
            logger.exception('failed to start session %s', self.session_id)
            await self.send_json({'type': 'error', 'message': 'could not start the tracking pipeline'})
            await self.close(code=4500)
            return

        await self.send_json({
            'type': 'ready',
            'session_id': self.session.session_id,
            'calibration': self.session.calibration_status(),
        })

    def _build_session(self):
        output_dir = getattr(settings, 'SESSION_OUTPUT_DIR', None)
        return GazeSession(
            session_id=self.session_id,
            output_dir=str(output_dir / self.session_id) if output_dir else None,
            include_debug_frames=getattr(settings, 'GAZE_DEBUG_FRAMES', True),
        )

    async def receive(self, text_data=None, bytes_data=None):
        if self.session is None:
            return

        if text_data is not None:
            await self._handle_command(text_data)
            return

        if bytes_data is None:
            return

        # Drop frames while one is in flight. Queueing instead would let the
        # backlog grow without bound and leave the overlay lagging seconds behind
        # the student — a stale frame is worse than no frame.
        if self.busy:
            return

        self.busy = True
        try:
            result = await sync_to_async(self.session.process_frame, thread_sensitive=False)(bytes_data)
            
            # 🔑 Check if calibration just completed in this frame
            cal_status = result.get('calibration', {})
            if cal_status.get('calibrated') and not self._calibration_saved:
                user = self.scope.get('user')
                logger.info(f'Calibration detected in frame. User: {user}, Authenticated: {user.is_authenticated if user else False}')
                
                if user and user.is_authenticated:
                    try:
                        await self._save_calibration_to_db(user)
                        self._calibration_saved = True  # Prevent duplicate saves
                        logger.info(f'✓ Calibration saved to database for user {user.id} in session {self.session_id}')
                        
                        # Notify browser of successful save
                        await self.send_json({
                            "type": "calibration_complete",
                            "session_id": self.session.session_id,
                            "message": "✓ Calibration saved to database"
                        })
                    except Exception as e:
                        logger.exception(f'Failed to save calibration to database for session {self.session_id}')
                else:
                    logger.warning(f'User not authenticated - calibration not saved for session {self.session_id}')
            
            await self.send_json(result)
        except Exception:
            logger.exception('frame processing failed for session %s', self.session_id)
            await self.send_json({'type': 'error', 'message': 'frame processing failed'})
        finally:
            self.busy = False

    async def _handle_command(self, text_data):
        try:
            payload = json.loads(text_data)
        except (ValueError, TypeError):
            await self.send_json({'type': 'error', 'message': 'malformed JSON'})
            return

        command = payload.get('type')

        if command == 'calibrate_next':
            status = await sync_to_async(self.session.begin_calibration_stage, thread_sensitive=False)()
            await self.send_json({'type': 'calibration', **status})

        elif command == 'keystrokes':
            self.session.note_keystrokes(payload.get('keys') or [])

        elif command == 'ping':
            await self.send_json({'type': 'pong'})

        else:
            await self.send_json({'type': 'error', 'message': f'unknown command: {command!r}'})
        


    async def _save_calibration_to_db(self, user):
        """Save calibration thresholds directly to database.
        
        This eliminates the browser roundtrip and saves thresholds immediately
        when calibration completes.
        """
        from studentside.models import StudentTrackingThresholds
        
        thresholds = self.session.eye_calibrator.calibrated_thresholds
        
        try:
            obj, created = await sync_to_async(StudentTrackingThresholds.objects.update_or_create)(
                student=user,
                defaults={
                    'calibration_up': thresholds.get('up', 0.0),
                    'calibration_down': thresholds.get('down', 0.0),
                    'calibration_center': thresholds.get('center', 0.0),
                    'calibration_left': thresholds.get('left', 0.0),
                    'calibration_right': thresholds.get('right', 0.0),
                    'calibration_v_center': thresholds.get('v_center', 0.0),
                    'iris_boxheight_center': thresholds.get('iris_boxheight_center', 0.0),
                    'iris_boxheight_up': thresholds.get('iris_boxheight_up', 0.0),
                    'iris_boxheight_down': thresholds.get('iris_boxheight_down', 0.0),
                }
            )
            action = "created" if created else "updated"
            logger.info(f'Calibration thresholds {action} for user {user.id} in session {self.session_id}')
        except Exception as e:
            logger.exception(f'Failed to save calibration for user {user.id} in session {self.session_id}: {e}')
            raise

    async def disconnect(self, code):
        if self.session is None:
            return
        try:
            summary = await sync_to_async(self.session.finalize, thread_sensitive=False)()
            logger.info('session %s closed: %s', self.session_id, summary)
        except Exception:
            logger.exception('failed to finalize session %s', self.session_id)
        finally:
            self.session = None

    async def send_json(self, payload):
        await self.send(text_data=json.dumps(payload))
