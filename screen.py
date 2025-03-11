from inky.auto import auto
from font_hanken_grotesk import HankenGroteskBold, HankenGroteskMedium
from PIL import Image, ImageDraw, ImageFont, ImageChops
import datetime
import os
import math

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

    def __init__(self,imgDir):
        self.activeShip = None
        self.imgDir = imgDir

        self.hanken_bold_35 = ImageFont.truetype(HankenGroteskBold, 35)
        self.hanken_bold_20 = ImageFont.truetype(HankenGroteskBold, 20)
        self.hanken_bold_14 = ImageFont.truetype(HankenGroteskBold, 14)

        self.ship_icon_size = 40
        self.info_icon_size = 24

        self.inky = auto(ask_user=True, verbose=False)
        
        self.height = self.inky.width
        self.width = self.inky.height

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
        if self.activeShip is not None and self.activeShip["mmsi"] == shipData["mmsi"]:
            return
        
        self.activeShip = shipData
        
        #print("Draw Ship")
        #print(shipData)
        
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
        icon = Image.open("icon_ship.png")
        icon = self.resizeImage(icon, self.ship_icon_size, self.ship_icon_size)
        img.paste(icon, (text_x,text_y))

        text_x += 40

        # Draw the title
        draw.text((text_x,text_y), "Ship Tracker", self.BLUE, font=self.hanken_bold_20)

        text_y += 24

        # Draw the subtitle
        now = datetime.datetime.now()
        draw.text((text_x,text_y), now.strftime("%A - %d/%m/%y %H:%M"), self.BLUE, font=self.hanken_bold_14)

        text_y += 35

        # Draw the picture
        imgPath = os.path.join(self.imgDir, shipData["mmsi"])
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

            img.paste(pic, (screen_padding+container_padding_horz, text_y))

        text_y += 298

        # Draw the ship name
        text = shipData["name"]
        tx_w,tx_h = self.getTextSize(self.hanken_bold_35,text)
        draw.text((int(self.width/2-tx_w/2),text_y), text, self.BLUE, font=self.hanken_bold_35)

        text_y += tx_h+2

        draw.line([(int(self.width/2-tx_w/2),text_y),(int(self.width/2+tx_w/2),text_y)], fill=self.BLUE, width=2)

        text_y += 45

        cats = ["MMSI","Callsign","Vessel Type"]
        icons = ["icon_mmsi","icon_callsign","icon_shiptype"]
        vals = [str(shipData["mmsi"]),shipData["callsign"],self.getVesselType(shipData["type"])]

        if "dynamic" in shipData:
            dynamic = shipData["dynamic"]

            if "destination" in dynamic and dynamic["destination"]:
                cats.append("Destination")
                icons.append("icon_dest")
                vals.append(dynamic["destination"])

            if "speed" in dynamic:
                cats.append("Speed")
                icons.append("icon_speed")
                vals.append(str(dynamic["speed"])+"kts")

        # Loop Start
        for idx, k in enumerate(cats):
            text_x = screen_padding+container_padding_horz

            # Draw Icon
            icon = Image.open("icon/"+icons[idx]+".png")
            icon = self.resizeImage(icon, self.info_icon_size, self.info_icon_size)
            img.paste(icon, (text_x,text_y))

            text_x += 30

            # Draw MMSI
            text = vals[idx]
            tx_w,tx_h = self.getTextSize(self.hanken_bold_20,text)
            draw.text((text_x,text_y), k, self.BLUE, font=self.hanken_bold_20)
            draw.text((self.width-screen_padding-container_padding_horz-tx_w,text_y), text, self.BLUE, font=self.hanken_bold_20)

            text_x = screen_padding+container_padding_horz
            text_y += 30

            draw.line([(text_x,text_y),(self.width-text_x,text_y)], fill=self.BLUE, width=2)

            text_y += 35

        img = img.convert("RGB")
        img = img.rotate(90,expand=1)

        self.inky.set_image(img)
        self.inky.show()