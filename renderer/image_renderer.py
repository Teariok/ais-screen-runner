import datetime
import threading


class ImageRenderer:
    def __init__(self, name:str, width:int = 800, height:int = 480, min_render_interval:int = 60):
        self.img_name: str = name

        self.height: int = height
        self.width: int = width

        self.min_render_interval: int = min_render_interval
        self.last_render: datetime = datetime.datetime.fromtimestamp(0)
        self.timer: threading.Timer = None
        self.pending_render: any = None

    def render(self, img:any, force:bool = False):
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
                self.timer: threading.Timer = threading.Timer(self.min_render_interval - time_diff, self.render, [None])
                self.timer.start()
                return

        self.timer = None
        self.last_render = now
        self.pending_render = None

        img.save(self.img_name)