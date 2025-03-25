import logging
    
class ScreenManager:
    def __init__(self, screens:list[any], command_queue):
        assert len(screens) != 0, "At least one screen must be passed to Screen Manager"

        self.logger:logging.Logger = logging.getLogger(__name__)

        self.command_queue = command_queue

        self.screens:list[any] = screens
        self.active_screen:int = 0
        
        self.screens[self.active_screen].set_active(True)
        self.dark_mode:int = False

    def begin_processing(self):
        while True:
            msg:tuple[str,...] = self.command_queue.get()
            if msg is None:
                continue

            # Screen Manager can handle "screen" and "mode" commands.
            # Anything else we assume is something for the screens to handle.

            if msg[0] == "screen":
                self.__activate_screen(msg[1])
            elif msg[0] == "mode":
                self.__set_mode(not self.dark_mode)
            else:
                for screen in self.screens:
                    screen.update(msg)

    def __activate_screen(self, index:int):
        if index < len(self.screens) and index >= 0 and index != self.active_screen:
            self.screens[self.active_screen].set_active(False)
            self.active_screen = index
            self.screens[self.active_screen].set_active(True)

    def __set_mode(self, dark_mode:bool):
        if self.dark_mode == dark_mode:
            return

        self.dark_mode = dark_mode
        for screen in self.screens:
            screen.set_mode(self.dark_mode)