from inky.auto import auto
import datetime
import threading

class InkyRenderer:
    def __init__(self, min_render_interval = 60):
        self.inky = auto(ask_user=True, verbose=False)

        self.height = self.inky.height
        self.width = self.inky.width

        self.min_render_interval = min_render_interval
        self.last_render = datetime.datetime.fromtimestamp(0)
        self.timer = None
        self.pending_render = None
        return

    def render(self, img):
        if img == None:
            img = self.pending_render
            if img == None:
                return
            
        self.pending_render = img
        now = datetime.datetime.now()
        time_diff = (now - self.last_render).total_seconds()

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