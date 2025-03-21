import logging
    
class ScreenManager:
    def __init__(self,screens,vessel_queue):
        self.logger = logging.getLogger(__name__)
        self.screens = screens
        self.active_screen = 0
        self.vessel_queue = vessel_queue
        self.screens[self.active_screen].set_active(True)

    def begin_processing(self):
        while True:
            msg = self.vessel_queue.get()
            if msg == None:
                continue

            for screen in self.screens:
                screen.update(msg)

    def set_mode(self, mode):
        if self.mode != mode and (mode == self.MODE_LIGHT or mode == self.MODE_DARK):
            self.mode = mode
            self._renderScreen()