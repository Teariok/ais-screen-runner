from inky.auto import auto
from inky.eeprom import read_eeprom
import datetime
import threading
import logging

class InkyRenderer:
    def __init__(self, min_render_interval:int = 60):
        self.logger = logging.getLogger(__name__)
        self.inky: any = auto(verbose=False)

        display = read_eeprom()
        if display is None:
                self.logger.critical("Cannot identify Inky board")
        else:
                self.logger.info("Inky Board: {}".format(display.get_variant()))
                self.logger.info(display)

        self.inky_type = display.get_color()

        self.height: int = self.inky.height
        self.width: int = self.inky.width

        self.min_render_interval: int = min_render_interval
        self.last_render: datetime = datetime.datetime.fromtimestamp(0)
        self.timer: threading.Timer|None = None
        self.pending_render = None

    def render(self, img:any, force:bool = False):
        try:
            if img is None:
                img = self.pending_render
                if img is None:
                    return

            self.pending_render = img
            now: datetime = datetime.datetime.now()

            if force:
                if self.timer:
                    self.timer.cancel()
            else:
                time_diff: int = (now - self.last_render).total_seconds()

                if self.timer and time_diff < self.min_render_interval:
                    return

                if time_diff < self.min_render_interval:
                    self.timer = threading.Timer(self.min_render_interval - time_diff, self.render, [None])
                    self.timer.start()
                    return

            self.timer = None
            self.last_render = now
            self.pending_render = None
            img = img.rotate(90,expand=1)

            self.inky.set_image(img)
            self.inky.show()
        except Exception as e:
            self.logger.exception("Failure in inky renderer", exc_info=e)
