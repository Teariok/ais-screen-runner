from font_hanken_grotesk import HankenGroteskBold
from PIL import Image, ImageDraw, ImageFont, ImageOps
import datetime
import os
import logging
from screen.screen_base import ScreenBase
    
class ShipZoneScreen(ScreenBase):
    def __init__(self,img_dir,renderer):
        super().__init__(img_dir, renderer)

        self.logger = logging.getLogger(__name__)

        self.visible_ship = None

        self.hanken_bold_35 = ImageFont.truetype(HankenGroteskBold, 35)
        self.hanken_bold_20 = ImageFont.truetype(HankenGroteskBold, 20)
        self.hanken_bold_14 = ImageFont.truetype(HankenGroteskBold, 14)

        self._load_icon("ship", "icon_ship.png", self._LARGE_ICON_SIZE)
        self._load_icon("mmsi", "icon_mmsi.png", self._SMALL_ICON_SIZE)
        self._load_icon("callsign", "icon_callsign.png", self._SMALL_ICON_SIZE)
        self._load_icon("shiptype", "icon_shiptype.png", self._SMALL_ICON_SIZE)
        self._load_icon("dest", "icon_dest.png", self._SMALL_ICON_SIZE)
        self._load_icon("speed", "icon_speed.png", self._SMALL_ICON_SIZE)

    def update(self, msg):
        if msg[0] == "zone":
            ship = msg[1]
            zone_prev = msg[2]

            self.logger.info(f"{ship['name']} changed zone from {zone_prev} to {ship.get('zone','None')}")
        
            if ship.get("zone", None) != None:
                self.__display_ship(ship)

    def __display_ship(self, ship_data):
        self.logger.info(f"Request to display ship {ship_data.get('mmsi',None)}")
        if self.visible_ship is not None and self.visible_ship["mmsi"] == ship_data["mmsi"]:
            self.logger.info("Skip display - ship is already displayed")
            return

        self.visible_ship = ship_data
        self.__render_screen()

    def __render_screen(self):
        if not self.active or self.visible_ship == None:
            return
        
        self.logger.info(f"Draw Ship {self.visible_ship}")

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

        text_y += 35
        image_y = text_y

        # Draw the picture
        img_padding = 0
        imgPath = os.path.join(self.img_dir, self.visible_ship["mmsi"])
        if os.path.exists(imgPath):
            pic = Image.open(imgPath)

            max_width = self.width - ((screen_padding+container_padding_horz)*2)
            max_height = 400 #298 - text_y

            pic = self._resize_image(pic, max_width, max_height)

            #img.paste(pic, (screen_padding+container_padding_horz, text_y))
        else:
            ship_len = (self.visible_ship["stern"] + self.visible_ship["bow"])
            ship_wid = (self.visible_ship["port"] + self.visible_ship["starboard"])

            if ship_len == 0 or ship_wid == 0:
                return
            
            max_width = self.width - ((screen_padding+container_padding_horz)*2)
            max_height = 370 - text_y

            tl = (screen_padding+container_padding_horz,text_y)
            tr = (tl[0]+max_width,text_y)
            bl = (tl[0],text_y+max_height)
            br = (tr[0],bl[1])

            draw.line([tl,tr,br,bl,tl], fill=self.BLUE, width=2)

            img_padding = 5
            max_width -= img_padding*2
            max_height -= img_padding*2

            pic = Image.new("RGB", (max_width, max_height), color=self.WHITE)
            pic_draw = ImageDraw.Draw(pic)

            text_size = self._get_text_size(self.hanken_bold_14,str(ship_wid))
            left_reserve = 5+text_size[1]

            inner_padding = 30
            max_width -= (inner_padding*2) + left_reserve
            max_height -= inner_padding*2

            width_ratio = max_width / ship_len
            height_ratio = max_height / ship_wid

            scale_factor = min(width_ratio, height_ratio)

            ship_len = int(ship_len * scale_factor)
            ship_wid = int(ship_wid * scale_factor)
            
            img_centre = ((max_width/2)+left_reserve, max_height/2)

            wh_ratio = 0.6 * (ship_wid/ship_len)
            nose_len = ship_len * wh_ratio

            tl = (inner_padding+img_centre[0] - ship_len/2, inner_padding+img_centre[1] - ship_wid/2)
            tr = (inner_padding+img_centre[0] + ship_len/2 - nose_len, inner_padding+img_centre[1] - ship_wid/2)
            n = (inner_padding+img_centre[0] + ship_len/2, inner_padding+img_centre[1])
            bl = (inner_padding+img_centre[0] - ship_len/2, inner_padding+img_centre[1] + ship_wid/2)
            br = (inner_padding+img_centre[0] + ship_len/2 - nose_len, inner_padding+img_centre[1] + ship_wid/2)

            pic_draw.line([tl,tr,n,br,bl,tl], fill=self.BLACK, width=2)

            mast_pos = (tl[0]+self.visible_ship["stern"]*scale_factor, tl[1]+self.visible_ship["port"]*scale_factor)
            mast_size = 10
            pic_draw.ellipse([mast_pos[0]-mast_size/2,mast_pos[1]-mast_size/2,mast_pos[0]+mast_size/2,mast_pos[1]+mast_size/2], self.BLACK)

            size_spacing = 5

            pic_draw.line([
                (bl[0], bl[1]+size_spacing),
                (bl[0], bl[1]+size_spacing*2),
                (inner_padding+img_centre[0], bl[1]+size_spacing*2),
                (inner_padding+img_centre[0], bl[1]+size_spacing*3),
                (inner_padding+img_centre[0], bl[1]+size_spacing*2),
                (n[0], bl[1]+size_spacing*2),
                (n[0], bl[1]+size_spacing),
            ], fill=self.BLACK, width=2)

            text_size = self._get_text_size(self.hanken_bold_14,str(ship_len))
            pic_draw.text((inner_padding+img_centre[0]-(text_size[0]/2), bl[1]+size_spacing*4),str(ship_len), self.BLACK, font=self.hanken_bold_14)

            pic_draw.line([
                (tl[0]-size_spacing, tl[1]),
                (tl[0]-size_spacing*2, tl[1]),
                (tl[0]-size_spacing*2, n[1]),
                (tl[0]-size_spacing*3, n[1]),
                (tl[0]-size_spacing*2, n[1]),
                (tl[0]-size_spacing*2, bl[1]),
                (tl[0]-size_spacing, bl[1]),
            ], fill=self.BLACK, width=2)

            text_size = self._get_text_size(self.hanken_bold_14,str(ship_wid))
            pic_draw.text((tl[0]-text_size[0]-size_spacing*4, n[1]-text_size[1]/2),str(ship_wid), self.BLACK, font=self.hanken_bold_14)

            if self.mode == self.MODE_DARK:
                pic = ImageOps.invert(pic)

        text_y += 298

        # Draw the ship name
        text = self.visible_ship["name"]
        tx_w,tx_h = self._get_text_size(self.hanken_bold_35,text)
        draw.text((int(self.width/2-tx_w/2),text_y), text, self.BLUE, font=self.hanken_bold_35)

        text_y += tx_h+2

        draw.line([(int(self.width/2-tx_w/2),text_y),(int(self.width/2+tx_w/2),text_y)], fill=self.BLUE, width=2)

        text_y += 45

        lines = [{
            "icon": self.icons["mmsi"],
            "name": "MMSI",
            "value": str(self.visible_ship["mmsi"])
        },{
            "icon": self.icons["callsign"],
            "name": "Callsign",
            "value": str(self.visible_ship["callsign"])
        },{
            "icon": self.icons["shiptype"],
            "name": "Vessel Type",
            "value": self._get_vessel_type(self.visible_ship["type"])
        }]

        if "destination" in self.visible_ship:
            lines.append({
                "icon": self.icons["dest"],
                "name": "Destination",
                "value": self.visible_ship["destination"]
            })

        if "speed" in self.visible_ship:
            lines.append({
                "icon": self.icons["speed"],
                "name": "Speed",
                "value": str(self.visible_ship["speed"])+"kts"
            })

        # Loop Start
        for item in lines:
            text_x = screen_padding+container_padding_horz

            # Draw Icon
            img.paste(item["icon"], (text_x,text_y))

            text_x += 30

            # Draw Text
            text = item["value"]
            tx_w,tx_h = self._get_text_size(self.hanken_bold_20,text)
            draw.text((text_x,text_y), item["name"], self.BLUE, font=self.hanken_bold_20)
            draw.text((self.width-screen_padding-container_padding_horz-tx_w,text_y), text, self.BLUE, font=self.hanken_bold_20)

            text_x = screen_padding+container_padding_horz
            text_y += 30

            draw.line([(text_x,text_y),(self.width-text_x,text_y)], fill=self.BLUE, width=2)

            text_y += 35

        if self.mode == self.MODE_DARK:
            img = ImageOps.invert(img)
        
        img.paste(pic, (screen_padding+container_padding_horz+img_padding, image_y+img_padding))

        img = img.convert("RGB")

        self.renderer.render(img)