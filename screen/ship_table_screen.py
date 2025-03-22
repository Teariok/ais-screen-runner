from font_hanken_grotesk import HankenGroteskBold
from PIL import Image, ImageDraw, ImageFont, ImageOps
import datetime
import threading
import logging
from screen.screen_base import ScreenBase

class ShipTableScreen(ScreenBase):
    def __init__(self,img_dir,renderer, render_interval = 2.5*60, max_tracked = 20):
        super().__init__(img_dir, renderer)
        self.logger = logging.getLogger(__name__)

        self.visible_ships = {}

        self.hanken_bold_20 = ImageFont.truetype(HankenGroteskBold, 20)
        self.hanken_bold_14 = ImageFont.truetype(HankenGroteskBold, 14)

        self.max_tracked = max_tracked
        self.render_interval = render_interval

        self.timer = None

        self._load_icon("ship", "icon_ship.png", self._LARGE_ICON_SIZE)

    def set_active(self, active):
        super().set_active(active)
        if self.active:
            self.__handle_timer()
        else:
            self.timer.cancel()
            self.timer = None

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
        
        self.logger.info(f"Draw Table")

        img = Image.new("RGB", (self.width,self.height), color=self.BLUE)
        draw = ImageDraw.Draw(img)

        screen_padding = 10
        container_padding_horz = 30
        container_padding_vert = 10
        text_x = screen_padding+container_padding_horz
        text_y = screen_padding+container_padding_vert

        # Draw the content container
        draw.rounded_rectangle([(screen_padding,screen_padding),(self.width - screen_padding,self.height - screen_padding)], radius=8, fill=self.WHITE)

        text_y += 10

        # Draw the boat icon
        img.paste(self.icons["ship"], (text_x,text_y))
        text_x += self._LARGE_ICON_SIZE

        # Draw the title
        draw.text((text_x,text_y), "Ship Tracker", self.BLUE, font=self.hanken_bold_20)

        text_y += 24

        # Draw the subtitle
        now = datetime.datetime.now()
        draw.text((text_x,text_y), now.strftime("%A - %d/%m/%y %H:%M"), self.BLUE, font=self.hanken_bold_14)

        text_x -= self._LARGE_ICON_SIZE
        text_y += 35

        widest_name = 0
        widest_type = 0
        widest_time = 0
        for ship in self.visible_ships.values():
            ship_name = ship.get("name","Unknown")
            ship_type = self._get_vessel_type(ship.get("type", -1))
            timestamp = datetime.datetime.fromtimestamp(ship.get("ts",0)).strftime("%H:%M:%S")

            text_size = self._get_text_size(self.hanken_bold_14, ship_name)
            if text_size[0] > widest_name:
                widest_name = text_size[0]

            text_size = self._get_text_size(self.hanken_bold_14, ship_type)
            if text_size[0] > widest_type:
                widest_type = text_size[0]

            text_size = self._get_text_size(self.hanken_bold_14, timestamp)
            if text_size[0] > widest_time:
                widest_time = text_size[0]

        gap = (self.width-(text_x+text_x+widest_name+widest_type+widest_time))/2

        text_size = self._get_text_size(self.hanken_bold_14, "Last Seen")
        draw.text((text_x,text_y), "Ship Name", self.BLUE, font=self.hanken_bold_14)
        draw.text((text_x+widest_name+gap,text_y), "Ship Type", self.BLUE, font=self.hanken_bold_14)
        draw.text((self.width-text_x-text_size[0],text_y), "Last Seen", self.BLUE, font=self.hanken_bold_14)

        text_y += text_size[1] + 10
        draw.line([(text_x,text_y),(self.width-text_x,text_y)], fill=self.BLUE, width=2)
        text_y += 10

        ships = self.visible_ships.values()
        for ship in ships:
            ship_name = ship.get("name","Unknown")
            ship_type = self._get_vessel_type(ship.get("type", -1))
            timestamp = datetime.datetime.fromtimestamp(ship.get("ts",0)).strftime("%H:%M:%S")

            draw.text((text_x,text_y), ship_name, self.BLUE, font=self.hanken_bold_14)
            draw.text((text_x+widest_name+gap,text_y), ship_type, self.BLUE, font=self.hanken_bold_14)
            draw.text((self.width-text_x-widest_time,text_y), timestamp, self.BLUE, font=self.hanken_bold_14)

            text_y += text_size[1] + 10
            draw.line([(text_x,text_y),(self.width-text_x,text_y)], fill=self.BLUE, width=2)
            text_y += 10

        if self._dark_mode:
            img = ImageOps.invert(img)

        img = img.convert("RGB")

        self.renderer.render(img, force)