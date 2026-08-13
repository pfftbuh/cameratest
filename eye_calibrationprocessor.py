import os
import json
import numpy as np
from collections import deque

class EyeCalibrationProcessor:
    def __init__(self, session_folder=None):
        self.sample_count = 60
        self.session_folder = session_folder

        # Calibration values
        self.calibration_up = 0.0
        self.calibration_down = 0.0
        self.calibration_h_center = 0.0
        self.calibration_left = 0.0
        self.calibration_right = 0.0
        self.calibration_v_center = 0.0
        self.calibration_iris_boxheight_center = 0.0
        self.calibration_iris_boxheight_up = 0.0
        self.calibration_iris_boxheight_down = 0.0

        self.calibration_stage = -1
        self.calibrated = False

        # Rolling sample buffers
        self.calibration_h_center_values = deque(maxlen=self.sample_count)
        self.calibration_v_center_values = deque(maxlen=self.sample_count)
        self.calibration_up_values = deque(maxlen=self.sample_count)
        self.calibration_down_values = deque(maxlen=self.sample_count)
        self.calibration_left_values = deque(maxlen=self.sample_count)
        self.calibration_right_values = deque(maxlen=self.sample_count)
        self.calibration_iris_boxheight_center_values = deque(maxlen=self.sample_count)
        self.calibration_iris_boxheight_up_values = deque(maxlen=self.sample_count)
        self.calibration_iris_boxheight_down_values = deque(maxlen=self.sample_count)

        self.calibrated_thresholds = {}

    def calibrate(self, raw_eye_data_list):
        for raw_eye_data in raw_eye_data_list:
            if self.calibration_stage == 0:
                avg_pupil_x = (raw_eye_data['left']['pupil'][0] + raw_eye_data['right']['pupil'][0]) / 2.0
                avg_pupil_y = (raw_eye_data['left']['pupil'][1] + raw_eye_data['right']['pupil'][1]) / 2.0
                self.calibration_h_center_values.append(avg_pupil_x)
                self.calibration_v_center_values.append(avg_pupil_y)
                self.calibration_iris_boxheight_center_values.append(
                    (raw_eye_data['left']['iris_boxheight'] + raw_eye_data['right']['iris_boxheight']) / 2.0
                )
            elif self.calibration_stage == 1:
                avg_pupil_y = (raw_eye_data['left']['pupil'][1] + raw_eye_data['right']['pupil'][1]) / 2.0
                self.calibration_up_values.append(avg_pupil_y)
                self.calibration_iris_boxheight_up_values.append(
                    (raw_eye_data['left']['iris_boxheight'] + raw_eye_data['right']['iris_boxheight']) / 2.0
                )
            elif self.calibration_stage == 2:
                avg_pupil_y = (raw_eye_data['left']['pupil'][1] + raw_eye_data['right']['pupil'][1]) / 2.0
                self.calibration_down_values.append(avg_pupil_y)
                self.calibration_iris_boxheight_down_values.append(
                    (raw_eye_data['left']['iris_boxheight'] + raw_eye_data['right']['iris_boxheight']) / 2.0
                )
            elif self.calibration_stage == 3:
                avg_pupil_x = (raw_eye_data['left']['pupil'][0] + raw_eye_data['right']['pupil'][0]) / 2.0
                self.calibration_left_values.append(avg_pupil_x)
            elif self.calibration_stage == 4:
                avg_pupil_x = (raw_eye_data['left']['pupil'][0] + raw_eye_data['right']['pupil'][0]) / 2.0
                self.calibration_right_values.append(avg_pupil_x)

    def next_stage(self):
        if self.calibration_stage < 5:
            self.calibration_stage += 1
        else:
            print("Calibration already complete. No more stages.")

        if self.calibration_stage == 5:
            # Compute averages
            self.calibration_h_center = np.mean(self.calibration_h_center_values) if self.calibration_h_center_values else 0.0
            self.calibration_v_center = np.mean(self.calibration_v_center_values) if self.calibration_v_center_values else 0.0
            self.calibration_up = np.mean(self.calibration_up_values) if self.calibration_up_values else 0.0
            self.calibration_down = np.mean(self.calibration_down_values) if self.calibration_down_values else 0.0
            self.calibration_left = np.mean(self.calibration_left_values) if self.calibration_left_values else 0.0
            self.calibration_right = np.mean(self.calibration_right_values) if self.calibration_right_values else 0.0
            self.calibration_iris_boxheight_center = np.mean(self.calibration_iris_boxheight_center_values) if self.calibration_iris_boxheight_center_values else 0.0
            self.calibration_iris_boxheight_up = np.mean(self.calibration_iris_boxheight_up_values) if self.calibration_iris_boxheight_up_values else 0.0
            self.calibration_iris_boxheight_down = np.mean(self.calibration_iris_boxheight_down_values) if self.calibration_iris_boxheight_down_values else 0.0

            # Store thresholds
            self.calibrated_thresholds = {
                'up': self.calibration_up,
                'down': self.calibration_down,
                'center': self.calibration_h_center,
                'left': self.calibration_left,
                'right': self.calibration_right,
                'v_center': self.calibration_v_center,
                'iris_boxheight_center': self.calibration_iris_boxheight_center,
                'iris_boxheight_up': self.calibration_iris_boxheight_up,
                'iris_boxheight_down': self.calibration_iris_boxheight_down
            }

            self.calibrated = True
            print("Calibration complete!")

            # Save JSON immediately
            if self.session_folder:
                try:
                    os.makedirs(self.session_folder, exist_ok=True)
                    calibration_path = os.path.join(self.session_folder, "eye_calibration.json")
                    with open(calibration_path, "w") as f:
                        json.dump(self.calibrated_thresholds, f, indent=4)
                    print(f"Calibration JSON saved at {calibration_path}")
                except Exception as e:
                    print(f"Failed to save calibration JSON: {e}")
