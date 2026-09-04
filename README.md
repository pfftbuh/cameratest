# MAKITEST: Suspicious Exam Behaviour Detection

MAKITEST is a Django exam application with browser camera proctoring. The browser sends JPEG frames to Django Channels, where the server runs face tracking, eye tracking, gaze estimation, suspicious-behaviour scoring, heatmap generation, and evidence recording.

After submission, the application runs a session-level classifier against the registered exam artifacts. It uses the exam CSV only, stores the prediction on the exam attempt, and writes a JSON prediction artifact.

## Current Features

- Student and teacher authentication with role-based pages.
- Teacher exam creation, question management, student class assignment, and attempt review.
- Multiple choice, true/false, numeric, and fill-in-the-blank questions.
- Browser camera selection and live camera preview.
- Five-stage gaze calibration with saved student thresholds.
- Browser-to-server JPEG streaming over Django Channels.
- Face landmarks, eye landmarks, face pose, eye gaze, weighted screen position, and gaze direction.
- Browser-side suspicious-key, focus-loss, and hidden-tab reporting.
- Server-side violation scoring, CSV logging, and video evidence capture.
- Heatmap generation using `heatmap_<session_id>.png`.
- Database linkage between attempts, proctoring sessions, and artifacts.
- Post-submission prediction using the exam CSV, never the calibration CSV.

## Project Layout

```text
gaze_session.py                  Per-WebSocket tracking session
main_trackerprocess.py           Optional standalone OpenCV tracker
web_session_predict.py           Web-app prediction service
predict_session.py               Standalone prediction script
heatmap_feature_extractor.py     Heatmap and CSV feature extraction
suspicion_model.joblib            Trained classifier
feature_columns.json             Classifier feature order
face_landmarker.task              MediaPipe model
whatever/                         Django project
  camera/                         Camera page and Channels consumer
  studentside/                    Student flow, attempts, artifacts, prediction
  teacherside/                    Exams and proctoring review
  homepage/                       Authentication and landing pages
  media/sessions/                 Generated session artifacts
```

## Setup

Requirements:

- Python 3.10 or higher.
- A webcam and browser camera permission.
- Windows is recommended for the standalone `keyboard` processor. Browser proctoring uses browser events instead of a server global keyboard hook.

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python whatever/manage.py migrate
python whatever/manage.py check
```

## Run the Web Application

Start the ASGI development server from the repository root:

```powershell
python whatever/manage.py runserver
```

Daphne and Channels are configured so the development server supports `/ws/proctor/<session_id>/`.

## Student Proctoring Flow

1. `exam_details` creates a unique `proctoring_session_id` and stores it temporarily in the Django session.
2. The camera page reuses the ID and opens a WebSocket for calibration.
3. Calibration proceeds through center, up, down, left, and right stages.
4. Thresholds are saved for the student and `eye_calibration.json` is written.
5. The exam page creates `StudentExamAttempt` and opens a new WebSocket with the same ID.
6. Exam frames generate gaze data, violations, CSV logs, heatmaps, and video evidence.
7. Submission saves and grades answers, marks the attempt complete, and registers files in `ProctoringSessionFiles`.
8. Prediction uses the final registered CSV as the exam CSV and the registered heatmap.
9. Prediction fields are saved to `StudentExamAttempt` and the JSON result is written under `prediction/`.

The durable relationship is:

```text
StudentExamAttempt.proctoring_session_id
        -> ProctoringSessionFiles.session_id
        -> media/sessions/<session_id>/
```

## Session Artifacts

Web sessions are stored below `whatever/media/sessions/<session_id>/`:

| Artifact | Purpose |
|---|---|
| `eye_calibration.json` | Calibrated eye and face thresholds |
| `session_log_*.csv` | Calibration and exam event logs |
| `heatmap_<session_id>.png` | Final exam gaze heatmap |
| `*_violation_*.mp4` | Violation evidence clips |
| `prediction/predicted_values.json` | Classifier probabilities and extracted features |

The first CSV is the calibration log. The final registered CSV is the exam log. Prediction does not fall back to the calibration CSV.

## Prediction

The web integration is implemented in `web_session_predict.py` and accepts explicit registered artifact paths:

```python
from web_session_predict import predict_session_files

result = predict_session_files(
    heatmap_path=heatmap_path,
    csv_path=exam_csv_path,
    session_directory=session_directory,
)
```

The result contains `predicted_label`, `confidence`, both class probabilities, the model version, feature columns, and extracted features. The standalone `predict_session.py` remains available for manual folder-based prediction and is separate from the Django submission flow.

## Database and Migrations

`StudentExamAttempt` stores grading, proctoring, and prediction state. `ProctoringSessionFiles` stores relative paths to artifacts and links them to the attempt.

After model changes:

```powershell
python whatever/manage.py makemigrations
python whatever/manage.py migrate
```

The current prediction migration is `studentside.0004_studentexamattempt_prediction`.

## Standalone Tracker

The original OpenCV tracker remains available:

```powershell
python main_trackerprocess.py
```

It uses a local webcam, OpenCV windows, keyboard controls, and standalone output defaults. It is separate from the browser/Django workflow, which uses `GazeSession` through Django Channels.

## Limitations

- Prediction currently runs synchronously during submission.
- A prediction is unavailable or failed when the separate exam CSV or heatmap is missing.
- The model is a proof-of-concept trained on a small session-level dataset and should not be treated as an autonomous cheating decision.
- Final artifacts must exist before the submission scan and prediction run.
