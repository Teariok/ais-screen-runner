import datetime
import logging
import os
import threading
import urllib

from font_hanken_grotesk import HankenGroteskBold
from PIL import Image, ImageDraw, ImageFont

from screen.screen_base import ScreenBase


class ShipMapScreen(ScreenBase):
    def __init__(self, img_dir:str, renderer:any, api_key:str, bounds:list[int], light_style:str, dark_style:str, time_window:int = 60 * 5, render_interval:int = 60 * 3, max_tracked:int = 20):
        super().__init__(img_dir, renderer)
        self.logger: logging.Logger = logging.getLogger(__name__)

        self.api_key:str = api_key
        self.light_style:str = light_style
        self.dark_style:str = dark_style

        self.time_window:int = time_window
        self.max_tracked:int = max_tracked
        self.visible_ships: dict[str,dict[str,any]] = {}

        self.hanken_bold_8:ImageFont.FreeTypeFont = ImageFont.truetype(HankenGroteskBold, 8)
        
        self.render_interval:int = render_interval
        self.timer:threading.Timer|None = None

        self.bounds:list[int] = bounds
        self.min_lon:float = float(bounds[0])
        self.min_lat:float = float(bounds[1])
        self.max_lon:float = float(bounds[2])
        self.max_lat:float = float(bounds[3])

        self.__load_maps()
        self._load_icon("ship", "icon_ship.png", self._LARGE_ICON_SIZE)

        self.map_image:Image.Image = Image.open(os.path.join(self.img_dir, "light.png"))

    def __load_maps(self):
        for map in [("light",self.light_style),("dark",self.dark_style)]:
            img_path:str = os.path.join(self.img_dir, map[0]+".png")
            if os.path.exists(img_path):
                continue

            try:
                style:str = map[1]
                size:str = f"{self.renderer.height}x{self.renderer.width}"
                bounds:str = f"[{self.bounds[0]},{self.bounds[1]},{self.bounds[2]},{self.bounds[3]}]"

                url:str = f"https://api.mapbox.com/styles/v1/mapbox/{style}/static/{bounds}/{size}?access_token={self.api_key}"
                urllib.request.urlretrieve(url, img_path)
                print(f"Image has been downloaded and saved as '{img_path}'")
            except Exception as e:
                print(f"Failed to download the image. Error: {e}")

    def set_active(self, active:bool):
        super().set_active(active)

        if self.active:
            self.__handle_timer()
        else:
            self.timer.cancel()
            self.timer = None

    def set_mode(self, dark_mode:bool):
        img_name:str = "dark.png" if dark_mode else "light.png"
        self.map_image:Image.Image = Image.open(os.path.join(self.img_dir, img_name))

        # Call super last as it will force a redraw
        super().set_mode(dark_mode)

    def __handle_timer(self):
        self.timer = threading.Timer(self.render_interval, self.__handle_timer)
        self.timer.start()
        self._render_screen()

    def update(self, msg:tuple[str,...]):
        if msg[0] != "update":
            return
        
        ship:dict[str,any] = msg[1]

        self.visible_ships[ship['mmsi']] = ship
        # Reduce the list down if it's longer than the max we can track
        self.visible_ships = dict(sorted(self.visible_ships.items(), key=lambda item: item[1]['ts'], reverse=True)[:self.max_tracked])

    def _render_screen(self, force:bool = False):
        if not self.active:
            return
        
        self.logger.info("Draw Map")

        img:Image.Image = Image.new("RGB", (self.width,self.height), color=self.BLUE)
        draw:Image.ImageDraw = ImageDraw.Draw(img)

        img.paste(self.map_image)

        now:datetime = datetime.datetime.now()

        for ship in self.visible_ships.values():
            ts:datetime = datetime.datetime.fromtimestamp(ship.get('ts', 0))

            # Don't draw vessels if they haven't been updated within the time window
            if (now - ts).total_seconds() > self.time_window:
                continue

            point_lat:float = ship.get("lat", 0)
            point_lon:float = ship.get("lon", 0)

            # Skip any vessels that aren't within the map bounds
            if point_lat < self.min_lat or point_lat > self.max_lat:
                continue

            if point_lon < self.min_lon or point_lon > self.max_lon:
                continue

            # Map lat/lon to x/y image position
            point_y:int = self.height - (((point_lat - self.min_lat) / (self.max_lat - self.min_lat)) * self.height)
            point_x:int = ((point_lon - self.min_lon) / (self.max_lon - self.min_lon)) * self.width

            point_size:int = 5
            text_offset_y:int = 5

            draw.ellipse([point_x-point_size/2,point_y-point_size/2,point_x+point_size/2,point_y+point_size/2], self.YELLOW if self._dark_mode else self.BLACK)
            text_size:tuple[int,int] = self._get_text_size(self.hanken_bold_8, ship.get("name"))
            draw.text((point_x - (text_size[0]/2), point_y - text_offset_y - (point_size/2) - text_size[1]), ship.get("name"), self.YELLOW if self._dark_mode else self.RED, font=self.hanken_bold_8)

        img = img.convert("RGB")
        self.renderer.render(img, force)