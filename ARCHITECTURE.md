# MAKITEST System Architecture

This diagram shows the complete flow of the Django-based proctoring system, from camera capture in the browser to suspicious activity detection on the server.

```mermaid
graph TB
    subgraph "Browser/Frontend"
        A[User Opens home.html] --> B[Camera Selection Dropdown]
        B --> C[getUserMedia API]
        C --> D[Video Element Hidden]
        D --> E[Canvas Capture @ 10 FPS]
        E --> F[JPEG Compression 0.7]
        F --> G[WebSocket Binary Send]
        
        H[WebSocket JSON Receive] --> I{Message Type?}
        I -->|ready| J[Enable Calibration Button]
        I -->|frame_result| K[Update UI Metrics]
        K --> L[Update Annotated Image]
        K --> M[Update Screen Position Dots]
        K --> N[Update Suspicion Alert]
        I -->|calibration| O[Update Calibration Progress]
        
        P[User Keystrokes] --> Q[Detect Suspicious Keys]
        Q --> R[Send Keystrokes JSON]
        
        S[Calibration Button] --> T[Send calibrate_next]
        
        U[Camera Switch Event] --> V[Stop Current Stream]
        V --> W[Clear Annotated Frame]
        W --> X[Start New Camera]
        X --> Y[Resume Frame Capture]
    end
    
    subgraph "Django Channels/WebSocket"
        G --> Z[ws://host/ws/proctor/session_id/]
        Z --> AA[ProctorConsumer.receive]
        R --> Z
        T --> Z
        
        AA --> AB{Data Type?}
        AB -->|binary| AC[JPEG Frame Bytes]
        AB -->|JSON| AD{Command Type?}
        AD -->|calibrate_next| AE[Call begin_calibration_stage]
        AD -->|keystrokes| AF[Queue Keystrokes]
        
        AC --> AG[sync_to_async Thread Pool]
        AG --> AH[GazeSession.process_frame]
        
        AI[JSON Response] --> H
    end
    
    subgraph "GazeSession Pipeline"
        AH --> AJ[Decode JPEG to numpy array]
        AJ --> AK[FaceTrackProcessor MediaPipe]
        AK --> AL{Face Landmarks?}
        AL -->|Yes| AM[Draw Landmarks & Annotations]
        AL -->|No| AN[Return Original Frame]
        AM --> AO[Calculate Yaw/Pitch]
        AN --> AP[Encode to Base64 JPEG]
        AM --> AP
        
        AJ --> AQ[EyeTrackProcessor MediaPipe]
        AQ --> AR{Eye Landmarks?}
        AR -->|Yes| AS[Extract Raw Eye Data]
        AR -->|No| AT[Skip Eye Processing]
        
        AO --> AU[FaceAxisProcessor]
        AU --> AV[Calculate Face Screen Position]
        
        AS --> AW{Calibrated?}
        AW -->|No & Collecting| AX[Add to Calibration Samples]
        AX --> AY{Enough Samples?}
        AY -->|Yes| AZ[Calibrate Thresholds]
        AZ --> BA[Next Stage 1→2→3→4→5]
        
        AW -->|Yes| BB[EyeScreenPosProcessor]
        BB --> BC[Calculate Eye Screen Position]
        
        AV --> BD[GazeDirectionProcessor]
        BC --> BD
        BD --> BE[Weighted Position 45% Face / 55% Eye]
        
        BE --> BF[HeatmapProcessor]
        BF --> BG[Accumulate Gaze Points]
        
        BD --> BH[SuspicionScoringProcessor]
        AF --> BH
        BH --> BI{Violation Detected?}
        BI -->|Yes| BJ[Start Recording Evidence]
        BI -->|No| BK[Normal Monitoring]
        
        AP --> BL[Build frame_result JSON]
        AV --> BL
        BC --> BL
        BE --> BL
        BD --> BL
        BH --> BL
        AZ --> BL
        
        BL --> AI
    end
    
    subgraph "Calibration States"
        BM[-1: Not Started] --> BN[0: Center]
        BN --> BO[1: Top Left]
        BO --> BP[2: Top Right]
        BP --> BQ[3: Bottom Left]
        BQ --> BR[4: Bottom Right]
        BR --> BS[5: CALIBRATED]
    end
    
    subgraph "Frontend Display"
        L --> BT[img#annotated Visible]
        M --> BU[3x3 Grid Overlay]
        BU --> BV[Face Dot Green]
        BU --> BW[Eye Dot Red]
        BU --> BX[Weighted Dot Cyan]
        N --> BY{is_recording?}
        BY -->|Yes| BZ[Show Alert Banner]
        BY -->|No| CA[Hide Alert]
    end
    
    subgraph "Suspicious Activity Detection"
        CB[Window Blur] --> Q
        CC[Tab Hidden] --> Q
        CD[Ctrl+C/V/X] --> Q
        CE[Ctrl+T/N/W] --> Q
        CF[F11/Escape] --> Q
        CG[Print Screen] --> Q
        
        BH --> CH{Check Conditions}
        CH -->|Multi-Face| CI[Record: multiple_faces]
        CH -->|No Face Long| CJ[Record: no_face_detected]
        CH -->|Off-Center Gaze| CK[Record: looking_off_screen]
        CH -->|Suspicious Keys| CL[Record: suspicious_keystrokes]
    end
    
    style A fill:#3ecf8e
    style Z fill:#4cc9f0
    style AH fill:#f5a623
    style BL fill:#ef4b4b
    style BS fill:#3ecf8e
    style BJ fill:#ef4b4b
```

## System Components

### 1. Frontend (Browser)
- **File**: `whatever/camera/templates/camera/home.html`
- **Purpose**: Capture webcam frames, handle camera switching, display annotated results
- **Key Features**:
  - Multi-camera selection with graceful switching
  - Canvas-based frame capture (640x480 @ 10 FPS)
  - Hidden video element for background processing
  - Real-time UI updates with screen position visualization
  - Suspicious keystroke detection

### 2. Django Channels WebSocket
- **File**: `whatever/camera/consumers.py`
- **Endpoint**: `/ws/proctor/{session_id}/`
- **Purpose**: Handle persistent WebSocket connections for real-time bidirectional communication
- **Protocol**:
  - Client → Server: Binary (JPEG frames), JSON (commands, keystrokes)
  - Server → Client: JSON (frame results, calibration status, alerts)

### 3. GazeSession Pipeline
- **File**: `gaze_session.py`
- **Purpose**: Core processing pipeline with MediaPipe models
- **Processors**:
  - `FaceTrackProcessor`: Detect face landmarks, draw annotations
  - `EyeTrackProcessor`: Detect iris positions for gaze tracking
  - `FaceAxisProcessor`: Convert head pose to screen coordinates
  - `EyeScreenPosProcessor`: Convert eye gaze to screen coordinates
  - `GazeDirectionProcessor`: Combine face and eye data (45%/55% weighting)
  - `HeatmapProcessor`: Track gaze patterns over time
  - `SuspicionScoringProcessor`: Detect violations and trigger recording

### 4. Calibration System
- **5-Stage Process**: Center → Top-Left → Top-Right → Bottom-Left → Bottom-Right
- **Purpose**: Personalize eye tracking for each student
- **Mechanism**: Collect eye samples at known screen positions, calculate thresholds

### 5. Suspicious Activity Detection
- **Browser-Side**: Keystroke detection (Ctrl+C/V/X/T/N/W, F11, Print Screen, Alt+Tab, window blur, tab hidden)
- **Server-Side**: Face detection, multi-face detection, off-screen gaze, prolonged absence

## Data Flow

1. **Camera Capture**: Browser captures frames from selected camera via getUserMedia
2. **Frame Transmission**: JPEG frames sent as binary WebSocket messages at 10 FPS
3. **Server Processing**: MediaPipe models analyze face/eye landmarks in thread pool
4. **Annotation**: Server draws tracking overlays and encodes as base64 JPEG
5. **Response**: JSON message with metrics, screen positions, and annotated frame
6. **Frontend Update**: Display annotated frame, update dots on 3x3 grid, show alerts

## Key Features

- ✅ Multi-camera support with live switching
- ✅ Device-agnostic (works with OBS virtual cameras, static images)
- ✅ Graceful frame filtering during camera transitions
- ✅ Always-on frame transmission (even without face detection)
- ✅ Session persistence across camera switches
- ✅ Real-time suspicious activity monitoring
- ✅ Evidence recording system for violations
