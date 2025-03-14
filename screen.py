from font_hanken_grotesk import HankenGroteskBold
from PIL import Image, ImageDraw, ImageFont, ImageOps
import datetime
import os
import math
import logging

VESSEL_TYPES = {
    -1: "Unknown",
    0: "Unknown",
    20: "Wing in Ground",
    30: "Fishing",
    31: "Towing",
    32: "Towing (Large)",
    33: "Dredge",
    34: "Diving Vessel",
    35: "Military Ops",
    36: "Sailing",
    37: "Pleasure Craft",
    40: "High Speed Craft",
    50: "Pilot Vessel",
    51: "Search & Rescue",
    52: "Tug",
    53: "Port Tender",
    54: "Anti-pollution Equip.",
    55: "Law Enforcement",
    56: "Local",
    57: "Local",
    58: "Medical Transport",
    59: "Non-combatant Ship",
    60: "Passenger Ship",
    70: "Cargo Ship",
    80: "Tanker",
    90: "Other"
}

VESSEL_SUBCATS = {
    1: "Hazardous (High)",
    2: "Hazardous",
    3: "Hazardous (Low)",
    4: "Non-hazardous"
}
    
class Screen:
    WHITE="#FFFFFF"
    BLACK="#000000"
    RED="#FF0000"
    GREEN="#00FF00"
    BLUE="#0000FF"
    YELLOW="#FFFF00"

    MODE_LIGHT=0
    MODE_DARK=1

    __LARGE_ICON_SIZE = 40
    __SMALL_ICON_SIZE = 24

    def __init__(self,imgDir,renderer,mode = None):
        self.logger = logging.getLogger(__name__)

        self.activeShip = None
        self.imgDir = imgDir
        self.mode = mode if mode else self.MODE_LIGHT

        self.hanken_bold_35 = ImageFont.truetype(HankenGroteskBold, 35)
        self.hanken_bold_20 = ImageFont.truetype(HankenGroteskBold, 20)
        self.hanken_bold_14 = ImageFont.truetype(HankenGroteskBold, 14)

        self.renderer = renderer

        self.height = self.renderer.width
        self.width = self.renderer.height

        self.icons = {}
        self.__loadIcon("ship", "icon_ship.png", self.__LARGE_ICON_SIZE)
        self.__loadIcon("mmsi", "icon_mmsi.png", self.__SMALL_ICON_SIZE)
        self.__loadIcon("callsign", "icon_callsign.png", self.__SMALL_ICON_SIZE)
        self.__loadIcon("shiptype", "icon_shiptype.png", self.__SMALL_ICON_SIZE)
        self.__loadIcon("dest", "icon_dest.png", self.__SMALL_ICON_SIZE)
        self.__loadIcon("speed", "icon_speed.png", self.__SMALL_ICON_SIZE)

    def __loadIcon(self, key, filename, size):
        icon = Image.open(os.path.join("icon", filename))
        self.icons[key] = self.resizeImage(icon, size, size)

    def setMode(self, mode):
        if self.mode != mode and (mode == self.MODE_LIGHT or mode == self.MODE_DARK):
            self.mode = mode
            self._renderScreen()

    def getTextSize(self, font, text):
        _, _, right, bottom = font.getbbox(text)
        return (right, bottom)

    def getVesselType(self, value):
        vessel_type = VESSEL_TYPES.get(value)

        if vessel_type:
            return vessel_type

        base_cat = math.floor(value / 10) * 10
        vessel_type = VESSEL_TYPES.get(base_cat)

        if vessel_type is None:
            return "Reserved"

        sub_cat = value % 10
        sub_cat_type = VESSEL_SUBCATS.get(sub_cat)

        if sub_cat_type:
            return f"{vessel_type} - {sub_cat_type}"

        return vessel_type

    def resizeImage(self, pic, maxWidth, maxHeight):
        original_width, original_height = pic.size

        width_ratio = maxWidth / original_width
        height_ratio = maxHeight / original_height

        scale_factor = min(width_ratio, height_ratio)

        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)

        return pic.resize((new_width, new_height), Image.LANCZOS)

    def displayShip(self, shipData):
        self.logger.info(f"Request to display ship {shipData.get('mmsi',None)}")
        if self.activeShip is not None and self.activeShip["mmsi"] == shipData["mmsi"]:
            self.logger.info("Skip display - ship is already displayed")
            return

        self.activeShip = shipData
        self._renderScreen()

    def _renderScreen(self):
        if self.activeShip == None:
            return
        
        self.logger.info(f"Draw Ship {self.activeShip}")

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
        text_x += self.__LARGE_ICON_SIZE

        # Draw the title
        draw.text((text_x,text_y), "Ship Tracker", self.BLUE, font=self.hanken_bold_20)

        text_y += 24

        # Draw the subtitle
        now = datetime.datetime.now()
        draw.text((text_x,text_y), now.strftime("%A - %d/%m/%y %H:%M"), self.BLUE, font=self.hanken_bold_14)

        text_y += 35
        image_y = text_y

        # Draw the picture
        imgPath = os.path.join(self.imgDir, self.activeShip["mmsi"])
        if os.path.exists(imgPath):
            pic = Image.open(imgPath)

            maxWidth = self.width - ((screen_padding+container_padding_horz)*2)
            maxHeight = 400 #298 - text_y

            original_width, original_height = pic.size

            width_ratio = maxWidth / original_width
            height_ratio = maxHeight / original_height

            scale_factor = min(width_ratio, height_ratio)

            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)

            pic = pic.resize((new_width, new_height), Image.LANCZOS)

            #img.paste(pic, (screen_padding+container_padding_horz, text_y))
        else:
            shipLen = (self.activeShip["stern"] + self.activeShip["bow"])
            shipWid = (self.activeShip["port"] + self.activeShip["starboard"])

            if shipLen == 0 or shipWid == 0:
                return
            
            maxWidth = self.width - ((screen_padding+container_padding_horz)*2)
            maxHeight = 370 - text_y

            tl = (screen_padding+container_padding_horz,text_y)
            tr = (tl[0]+maxWidth,text_y)
            bl = (tl[0],text_y+maxHeight)
            br = (tr[0],bl[1])

            draw.line([tl,tr,br,bl,tl], fill=self.BLUE, width=2)

            img_padding = 5
            maxWidth -= img_padding*2
            maxHeight -= img_padding*2

            pic = Image.new("RGB", (maxWidth, maxHeight), color=self.WHITE)
            picDraw = ImageDraw.Draw(pic)

            text_size = self.getTextSize(self.hanken_bold_14,str(shipWid))
            left_reserve = 5+text_size[1]

            inner_padding = 30
            maxWidth -= (inner_padding*2) + left_reserve
            maxHeight -= inner_padding*2

            width_ratio = maxWidth / shipLen
            height_ratio = maxHeight / shipWid

            scale_factor = min(width_ratio, height_ratio)

            shipLen = int(shipLen * scale_factor)
            shipWid = int(shipWid * scale_factor)
            
            img_centre = ((maxWidth/2)+left_reserve, maxHeight/2)

            wh_ratio = 0.6 * (shipWid/shipLen)
            nose_len = shipLen * wh_ratio

            tl = (inner_padding+img_centre[0] - shipLen/2, inner_padding+img_centre[1] - shipWid/2)
            tr = (inner_padding+img_centre[0] + shipLen/2 - nose_len, inner_padding+img_centre[1] - shipWid/2)
            n = (inner_padding+img_centre[0] + shipLen/2, inner_padding+img_centre[1])
            bl = (inner_padding+img_centre[0] - shipLen/2, inner_padding+img_centre[1] + shipWid/2)
            br = (inner_padding+img_centre[0] + shipLen/2 - nose_len, inner_padding+img_centre[1] + shipWid/2)

            picDraw.line([tl,tr,n,br,bl,tl], fill=self.BLACK, width=2)

            mast_pos = (tl[0]+self.activeShip["stern"]*scale_factor, tl[1]+self.activeShip["port"]*scale_factor)
            mast_size = 10
            picDraw.ellipse([mast_pos[0]-mast_size/2,mast_pos[1]-mast_size/2,mast_pos[0]+mast_size/2,mast_pos[1]+mast_size/2], self.BLACK)

            size_spacing = 5

            picDraw.line([
                (bl[0], bl[1]+size_spacing),
                (bl[0], bl[1]+size_spacing*2),
                (inner_padding+img_centre[0], bl[1]+size_spacing*2),
                (inner_padding+img_centre[0], bl[1]+size_spacing*3),
                (inner_padding+img_centre[0], bl[1]+size_spacing*2),
                (n[0], bl[1]+size_spacing*2),
                (n[0], bl[1]+size_spacing),
            ], fill=self.BLACK, width=2)

            text_size = self.getTextSize(self.hanken_bold_14,str(shipLen))
            picDraw.text((inner_padding+img_centre[0]-(text_size[0]/2), bl[1]+size_spacing*4),str(shipLen), self.BLACK, font=self.hanken_bold_14)

            picDraw.line([
                (tl[0]-size_spacing, tl[1]),
                (tl[0]-size_spacing*2, tl[1]),
                (tl[0]-size_spacing*2, n[1]),
                (tl[0]-size_spacing*3, n[1]),
                (tl[0]-size_spacing*2, n[1]),
                (tl[0]-size_spacing*2, bl[1]),
                (tl[0]-size_spacing, bl[1]),
            ], fill=self.BLACK, width=2)

            text_size = self.getTextSize(self.hanken_bold_14,str(shipWid))
            picDraw.text((tl[0]-text_size[0]-size_spacing*4, n[1]-text_size[1]/2),str(shipWid), self.BLACK, font=self.hanken_bold_14)

            if self.mode == self.MODE_DARK:
                pic = ImageOps.invert(pic)

        text_y += 298

        # Draw the ship name
        text = self.activeShip["name"]
        tx_w,tx_h = self.getTextSize(self.hanken_bold_35,text)
        draw.text((int(self.width/2-tx_w/2),text_y), text, self.BLUE, font=self.hanken_bold_35)

        text_y += tx_h+2

        draw.line([(int(self.width/2-tx_w/2),text_y),(int(self.width/2+tx_w/2),text_y)], fill=self.BLUE, width=2)

        text_y += 45

        lines = [{
            "icon": self.icons["mmsi"],
            "name": "MMSI",
            "value": str(self.activeShip["mmsi"])
        },{
            "icon": self.icons["callsign"],
            "name": "Callsign",
            "value": str(self.activeShip["callsign"])
        },{
            "icon": self.icons["shiptype"],
            "name": "Vessel Type",
            "value": self.getVesselType(self.activeShip["type"])
        }]

        if "destination" in self.activeShip:
            lines.append({
                "icon": self.icons["dest"],
                "name": "Destination",
                "value": self.activeShip["destination"]
            })

        if "speed" in self.activeShip:
            lines.append({
                "icon": self.icons["speed"],
                "name": "Speed",
                "value": str(self.activeShip["speed"])+"kts"
            })

        # Loop Start
        for item in lines:
            text_x = screen_padding+container_padding_horz

            # Draw Icon
            img.paste(item["icon"], (text_x,text_y))

            text_x += 30

            # Draw Text
            text = item["value"]
            tx_w,tx_h = self.getTextSize(self.hanken_bold_20,text)
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