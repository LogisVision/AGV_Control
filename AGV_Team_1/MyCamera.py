import traitlets
from traitlets.config.configurable import SingletonConfigurable
import atexit
import cv2
import threading
import numpy as np


class Camera(SingletonConfigurable):
    value = traitlets.Any()

    # config
    width = traitlets.Integer(default_value=640).tag(config=True)
    height = traitlets.Integer(default_value=480).tag(config=True)
    fps = traitlets.Integer(default_value=21).tag(config=True)
    capture_width = traitlets.Integer(default_value=3280).tag(config=True)
    capture_height = traitlets.Integer(default_value=2464).tag(config=True)
 
    def __init__(self, *args, **kwargs):
        self.ori_value = np.empty((self.height, self.width, 3), dtype=np.uint8)
        self.value = np.empty((self.height, self.width, 3), dtype=np.uint8)
        super(Camera, self).__init__(*args, **kwargs)

        try:
            self.cap = cv2.VideoCapture(self._gst_str(), cv2.CAP_GSTREAMER)

            re, image = self.cap.read()

            if not re:
                raise RuntimeError('Could not read image from camera.')

            self.ori_value = image
            start_x = 208
            start_y = 128
            cropped_image = image[start_y:start_y+224, start_x:start_x+224, :]
            self.value = cropped_image
            self.start()
        except:
            self.stop()
            raise RuntimeError(
                'Could not initialize camera.  Please see error trace.')

        atexit.register(self.stop)

    def reset_camera(self):
        self.cap.release()
        self.cap = cv2.VideoCapture(self._gst_str(), cv2.CAP_GSTREAMER)
        self.cap.open(self._gst_str(), cv2.CAP_GSTREAMER)

    def _capture_frames(self):
        while True:
            re, image = self.cap.read()
            if re:
                self.ori_value = image
                h, w = image.shape[:2]
                start_x = 208
                start_y = 128
                cropped_image = image[start_y:start_y+224, start_x:start_x+224, :]
                self.value = cropped_image
            else:
                break

    def _gst_str(self):
        return 'nvarguscamerasrc ! video/x-raw(memory:NVMM), width=%d, height=%d, format=(string)NV12, framerate=(fraction)%d/1 ! nvvidconv ! video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! videoconvert ! appsink' % (
            self.capture_width, self.capture_height, self.fps, self.width, self.height)

    def start(self):
        if not self.cap.isOpened():
            self.cap.open(self._gst_str(), cv2.CAP_GSTREAMER)
        if not hasattr(self, 'thread') or not self.thread.isAlive():
            self.thread = threading.Thread(target=self._capture_frames)
            self.thread.start()

    def stop(self):
        if hasattr(self, 'cap'):
            self.cap.release()
        if hasattr(self, 'thread'):
            self.thread.join()

    def restart(self):
        self.stop()
        self.start()
