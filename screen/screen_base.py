from PIL import Image
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

class ScreenBase():
    WHITE="#FFFFFF"
    BLACK="#000000"
    RED="#FF0000"
    GREEN="#00FF00"
    BLUE="#0000FF"
    YELLOW="#FFFF00"

    _LARGE_ICON_SIZE = 40
    _SMALL_ICON_SIZE = 24

    def __init__(self, img_dir, renderer, dark_mode = False):
        self.img_dir = img_dir
        self._dark_mode = dark_mode

        self.renderer = renderer

        self.height = self.renderer.width
        self.width = self.renderer.height

        self.active = False

        self.icons = {}

    def _load_icon(self, key, filename, size):
        icon = Image.open(os.path.join("icon", filename))
        self.icons[key] = self._resize_image(icon, size, size)

    def set_active(self, active):
        self.active = active
        if self.active:
            self._render_screen(True)

    def set_mode(self, dark_mode):
        if self._dark_mode != dark_mode:
            self._dark_mode = dark_mode
            if self.active:
                self._render_screen(True)

    def _get_text_size(self, font, text):
        _, _, right, bottom = font.getbbox(text)
        return (right, bottom)
    
    def _get_vessel_type(self, value):
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

    def _resize_image(self, pic, max_width, max_height):
        original_width, original_height = pic.size

        width_ratio = max_width / original_width
        height_ratio = max_height / original_height

        scale_factor = min(width_ratio, height_ratio)

        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)

        return pic.resize((new_width, new_height), Image.LANCZOS)
    
    def _render_screen(self, force = False):
        pass