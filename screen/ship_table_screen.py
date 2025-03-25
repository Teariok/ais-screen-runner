import datetime
import logging
import threading

from font_hanken_grotesk import HankenGroteskBold
from PIL import Image, ImageDraw, ImageFont, ImageOps

from screen.screen_base import ScreenBase


class ShipTableScreen(ScreenBase):
    def __init__(self,img_dir:str, renderer:any, render_interval:int = 2.5*60, max_tracked:int = 20):
        super().__init__(img_dir, renderer)
        self.logger:logging.Logger = logging.getLogger(__name__)

        self.max_tracked:int = max_tracked
        self.visible_ships:dict[str,dict[str,any]] = {}

        self.hanken_bold_20:Image.TrueTypeFont = ImageFont.truetype(HankenGroteskBold, 20)
        self.hanken_bold_14:Image.TrueTypeFont = ImageFont.truetype(HankenGroteskBold, 14)

        self.render_interval:int = render_interval
        self.timer:threading.Timer|None = None

        self._load_icon("ship", "icon_ship.png", self._LARGE_ICON_SIZE)

    def set_active(self, active:bool):
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

    def update(self, msg:tuple[str,...]):
        if msg[0] != "update":
            return
        
        ship:dict[str,any] = msg[1]

        self.visible_ships[ship['mmsi']] = ship
        self.visible_ships = dict(sorted(self.visible_ships.items(), key=lambda item: item[1]['ts'], reverse=True)[:self.max_tracked])

    def _render_screen(self, force:bool = False):
        if not self.active:
            return
        
        self.logger.info("Draw Table")

        img:Image.Image = Image.new("RGB", (self.width,self.height), color=self.BLUE)
        draw:Image.ImageDraw = ImageDraw.Draw(img)

        screen_padding:int = 10
        container_padding_horz:int = 30
        container_padding_vert:int = 10
        text_x:int = screen_padding+container_padding_horz
        text_y:int = screen_padding+container_padding_vert

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
        now:datetime = datetime.datetime.now()
        draw.text((text_x,text_y), now.strftime("%A - %d/%m/%y %H:%M"), self.BLUE, font=self.hanken_bold_14)

        text_x -= self._LARGE_ICON_SIZE
        text_y += 35

        widest_name:int = 0
        widest_type:int = 0
        widest_time:int = 0
        for ship in self.visible_ships.values():
            ship_name:str = ship.get("name","Unknown")
            ship_type:int = self._get_vessel_type(ship.get("type", -1))
            timestamp:datetime = datetime.datetime.fromtimestamp(ship.get("ts",0)).strftime("%H:%M:%S")

            text_size:tuple[int,int] = self._get_text_size(self.hanken_bold_14, ship_name)
            if text_size[0] > widest_name:
                widest_name = text_size[0]

            text_size = self._get_text_size(self.hanken_bold_14, ship_type)
            if text_size[0] > widest_type:
                widest_type = text_size[0]

            text_size = self._get_text_size(self.hanken_bold_14, timestamp)
            if text_size[0] > widest_time:
                widest_time = text_size[0]

        gap:int = (self.width-(text_x+text_x+widest_name+widest_type+widest_time))/2

        text_size = self._get_text_size(self.hanken_bold_14, "Last Seen")
        draw.text((text_x,text_y), "Ship Name", self.BLUE, font=self.hanken_bold_14)
        draw.text((text_x+widest_name+gap,text_y), "Ship Type", self.BLUE, font=self.hanken_bold_14)
        draw.text((self.width-text_x-text_size[0],text_y), "Last Seen", self.BLUE, font=self.hanken_bold_14)

        text_y += text_size[1] + 10
        draw.line([(text_x,text_y),(self.width-text_x,text_y)], fill=self.BLUE, width=2)
        text_y += 10

        ships:list[dict[str,any]] = self.visible_ships.values()
        for ship in ships:
            ship_name:str = ship.get("name","Unknown")
            ship_type:str = self._get_vessel_type(ship.get("type", -1))
            timestamp:datetime = datetime.datetime.fromtimestamp(ship.get("ts",0)).strftime("%H:%M:%S")

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