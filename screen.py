import logging
    
class Screen:
    def __init__(self,screens,vessel_queue):
        self.logger = logging.getLogger(__name__)
        self.screens = screens
        self.activeScreen = 0
        self.vessel_queue = vessel_queue

    def begin_processing(self):
        while True:
            msg = self.vessel_queue.get()
            if msg == None:
                continue

            self.screens[self.activeScreen].update(msg)

    def setMode(self, mode):
        if self.mode != mode and (mode == self.MODE_LIGHT or mode == self.MODE_DARK):
            self.mode = mode
            self._renderScreen()