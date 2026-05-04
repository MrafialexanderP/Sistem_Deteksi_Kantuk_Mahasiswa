from collections import deque
from src.utils.config import PERCLOS_WINDOW

class PERCLOS:
    def __init__(self):
        self.window = deque(maxlen=PERCLOS_WINDOW)

    def update(self, eye_closed: bool):
        """
        eye_closed = True jika mata tertutup
        """
        self.window.append(1 if eye_closed else 0)

    def get_value(self):
        if len(self.window) == 0:
            return 0.0

        return sum(self.window) / len(self.window)