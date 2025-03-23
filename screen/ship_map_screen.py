from font_hanken_grotesk import HankenGroteskBold
from PIL import Image, ImageDraw, ImageFont, ImageOps
import datetime
import threading
import logging
from screen.screen_base import ScreenBase
import os
import urllib

class ShipMapScreen(ScreenBase):
    def __init__(self, img_dir, renderer, api_key, bounds, light_style, dark_style, time_window = 60 * 5, render_interval = 10, max_tracked = 20):
        super().__init__(img_dir, renderer)
        self.logger = logging.getLogger(__name__)

        self.api_key = api_key
        self.light_style = light_style
        self.dark_style = dark_style

        self.visible_ships = {}

        self.hanken_bold_20 = ImageFont.truetype(HankenGroteskBold, 20)
        self.hanken_bold_14 = ImageFont.truetype(HankenGroteskBold, 14)
        self.hanken_bold_8 = ImageFont.truetype(HankenGroteskBold, 8)

        self.max_tracked = max_tracked
        self.render_interval = render_interval

        self.time_window = time_window

        self.bounds = bounds
        self.min_lon = float(bounds[0])
        self.min_lat = float(bounds[1])
        self.max_lon = float(bounds[2])
        self.max_lat = float(bounds[3])

        self.timer = None

        self.__load_maps()

        self._load_icon("ship", "icon_ship.png", self._LARGE_ICON_SIZE)

        self.map_image = Image.open(os.path.join(self.img_dir, "light.png"))

    def __load_maps(self):
        for map in [("light",self.light_style),("dark",self.dark_style)]:
            img_path = os.path.join(self.img_dir, map[0]+".png")
            if os.path.exists(img_path):
                continue

            try:
                style = map[1]
                size = f"{self.renderer.height}x{self.renderer.width}"
                bounds = f"[{self.bounds[0]},{self.bounds[1]},{self.bounds[2]},{self.bounds[3]}]"

                url = f"https://api.mapbox.com/styles/v1/mapbox/{style}/static/{bounds}/{size}?access_token={self.api_key}"
                urllib.request.urlretrieve(url, img_path)
                print(f"Image has been downloaded and saved as '{img_path}'")
            except Exception as e:
                print(f"Failed to download the image. Error: {e}")

    def set_active(self, active):
        super().set_active(active)
        if self.active:
            self.__handle_timer()
        else:
            self.timer.cancel()
            self.timer = None

    def set_mode(self, dark_mode):
        img_name = "dark.png" if dark_mode else "light.png"
        self.map_image = Image.open(os.path.join(self.img_dir, img_name))
        super().set_mode(dark_mode)

    def __handle_timer(self):
        self.timer = threading.Timer(self.render_interval, self.__handle_timer)
        self.timer.start()
        self._render_screen()

    def update(self, msg):
        if msg[0] != "update":
            return
        
        ship = msg[1]

        self.visible_ships[ship['mmsi']] = ship
        self.visible_ships = dict(sorted(self.visible_ships.items(), key=lambda item: item[1]['ts'], reverse=True)[:self.max_tracked])

    def _render_screen(self, force = False):
        if not self.active:
            return
        
        self.logger.info(f"Draw Map")

        img = Image.new("RGB", (self.width,self.height), color=self.BLUE)
        draw = ImageDraw.Draw(img)

        img.paste(self.map_image)

        now = datetime.datetime.now()

        for ship in self.visible_ships.values():
            ts = datetime.datetime.fromtimestamp(ship.get('ts', 0))

            if (now - ts).total_seconds() > self.time_window:
                continue

            point_lat = ship.get("lat", 0)
            point_lon = ship.get("lon", 0)

            if point_lat < self.min_lat or point_lat > self.max_lat:
                continue

            if point_lon < self.min_lon or point_lon > self.max_lon:
                continue

            point_y = self.height - (((point_lat - self.min_lat) / (self.max_lat - self.min_lat)) * self.height)
            point_x = ((point_lon - self.min_lon) / (self.max_lon - self.min_lon)) * self.width

            point_size = 5
            text_offset_y = 5

            draw.ellipse([point_x-point_size/2,point_y-point_size/2,point_x+point_size/2,point_y+point_size/2], self.YELLOW if self._dark_mode else self.BLACK)
            text_size = self._get_text_size(self.hanken_bold_8, ship.get("name"))
            draw.text((point_x - (text_size[0]/2), point_y - text_offset_y - (point_size/2) - text_size[1]), ship.get("name"), self.YELLOW if self._dark_mode else self.RED, font=self.hanken_bold_8)

        img = img.convert("RGB")
        self.renderer.render(img, force)