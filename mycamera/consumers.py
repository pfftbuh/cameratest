import json
import asyncio
import cv2
from channels.generic.websocket import AsyncWebsocketConsumer
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate

class WebRTCConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.pc = RTCPeerConnection()

        @self.pc.on("track")
        def on_track(track):
            if track.kind == "video":
                async def process():
                    while True:
                        frame = await track.recv()
                        img = frame.to_ndarray(format="bgr24")
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        cv2.imshow("Processed Frame", gray)
                        if cv2.waitKey(1) & 0xFF == ord("q"):
                            break
                asyncio.create_task(process())

    async def receive(self, text_data):
        data = json.loads(text_data)
        if "sdp" in data:
            desc = RTCSessionDescription(
                sdp=data["sdp"]["sdp"], type=data["sdp"]["type"]
            )
            await self.pc.setRemoteDescription(desc)
            if desc.type == "offer":
                answer = await self.pc.createAnswer()
                await self.pc.setLocalDescription(answer)
                await self.send(text_data=json.dumps({
                    "sdp": {
                        "sdp": self.pc.localDescription.sdp,
                        "type": self.pc.localDescription.type
                    }
                }))
        elif "candidate" in data:
            candidate = data["candidate"]
            ice = RTCIceCandidate(
                sdp=candidate.get("candidate"),
                sdpMid=candidate.get("sdpMid"),
                sdpMLineIndex=candidate.get("sdpMLineIndex")
            )
            await self.pc.addIceCandidate(ice)
