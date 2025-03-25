import math
import os

from PIL import Image

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

class ScreenBase():
    WHITE:str="#FFFFFF"
    BLACK:str="#000000"
    RED:str="#FF0000"
    GREEN:str="#00FF00"
    BLUE:str="#0000FF"
    YELLOW:str="#FFFF00"

    _LARGE_ICON_SIZE:int = 40
    _SMALL_ICON_SIZE:int = 24

    def __init__(self, img_dir: str, renderer: any, dark_mode: bool = False):
        self.img_dir: str = img_dir
        self._dark_mode: bool = dark_mode

        self.renderer: any = renderer

        self.height: int = self.renderer.width
        self.width: int = self.renderer.height

        self.active: bool = False

        self.icons: dict[str,Image.Image] = {}

    def _load_icon(self, key:str, filename:str, size:int):
        icon:Image.Image = Image.open(os.path.join("icon", filename))
        self.icons[key] = self._resize_image(icon, size, size)

    def set_active(self, active:bool):
        self.active = active
        if self.active:
            self._render_screen(True)

    def set_mode(self, dark_mode:bool):
        if self._dark_mode != dark_mode:
            self._dark_mode = dark_mode
            if self.active:
                self._render_screen(True)

    def _get_text_size(self, font:Image.TrueTypeFont, text:str) -> tuple[int,int]:
        _, _, right, bottom = font.getbbox(text)
        return (right, bottom)
    
    def _get_vessel_type(self, value:int) -> str:
        if value is None:
            return "Unknown"

        vessel_type: str = VESSEL_TYPES.get(value)

        if vessel_type:
            return vessel_type

        base_cat: int = math.floor(value / 10) * 10
        vessel_type = VESSEL_TYPES.get(base_cat)

        if vessel_type is None:
            return "Reserved"

        sub_cat: int = value % 10
        sub_cat_type: int = VESSEL_SUBCATS.get(sub_cat)

        if sub_cat_type:
            return f"{vessel_type} - {sub_cat_type}"

        return vessel_type

    def _resize_image(self, pic:Image.Image, max_width:int, max_height:int) -> Image.Image:
        original_width, original_height = pic.size

        width_ratio: float = max_width / original_width
        height_ratio: float = max_height / original_height

        scale_factor: float = min(width_ratio, height_ratio)

        new_width: int = int(original_width * scale_factor)
        new_height: int = int(original_height * scale_factor)

        return pic.resize((new_width, new_height), Image.LANCZOS)
    
    def _render_screen(self, force:bool = False):
        pass