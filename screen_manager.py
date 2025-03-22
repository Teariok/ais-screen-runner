import logging
    
class ScreenManager:
    def __init__(self,screens,vessel_queue):
        self.logger = logging.getLogger(__name__)
        self.screens = screens
        self.active_screen = 0
        self.vessel_queue = vessel_queue
        self.screens[self.active_screen].set_active(True)
        self.dark_mode = False

    def begin_processing(self):
        while True:
            msg = self.vessel_queue.get()
            if msg == None:
                continue

            if msg[0] == "screen":
                self.__activate_screen(msg[1])
            elif msg[0] == "mode":
                self.__set_mode(not self.dark_mode)
            else:
                for screen in self.screens:
                    screen.update(msg)

    def __activate_screen(self, index):
        if index < len(self.screens) and index >= 0 and index != self.active_screen:
            self.screens[self.active_screen].set_active(False)
            self.active_screen = index
            self.screens[self.active_screen].set_active(True)

    def __set_mode(self, dark_mode):
        if self.dark_mode != dark_mode:
            self.dark_mode = dark_mode
            for screen in self.screens:
                screen.set_mode(self.dark_mode)