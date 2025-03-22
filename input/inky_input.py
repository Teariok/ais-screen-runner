import gpiod
import gpiodevice
from gpiod.line import Bias, Direction, Edge

class InkyInput:
    def __init__(self):
        buttons = [5, 6, 16, 24]
        line_settings = gpiod.LineSettings(direction=Direction.INPUT, bias=Bias.PULL_UP, edge_detection=Edge.FALLING)
        chip = gpiodevice.find_chip_by_platform()
        self.offsets = [chip.line_offset_from_id(id) for id in buttons]
        line_config = dict.fromkeys(self.offsets, line_settings)
        self.request = chip.request_lines(consumer="inky7-buttons", config=line_config)

    def get_key(self):
        events = self.request.read_edge_events()
        if len(events) > 0:
            index = self.offsets.index(events[-1].line_offset)
            if index >= 0 and index < 4:
                return index
        
        return None