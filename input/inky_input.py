import logging

import gpiod
import gpiodevice
from gpiod.line import Bias, Direction, Edge


class InkyInput:
    def __init__(self):
        self.logger: logging.Logger = logging.getLogger(__name__)

        buttons: list[int] = [24, 16, 6, 5]
        line_settings: any = gpiod.LineSettings(direction=Direction.INPUT, bias=Bias.PULL_UP, edge_detection=Edge.FALLING)
        chip: any = gpiodevice.find_chip_by_platform()
        self.offsets: list[any] = [chip.line_offset_from_id(id) for id in buttons]
        line_config: dict[any, any] = dict.fromkeys(self.offsets, line_settings)
        self.request: any = chip.request_lines(consumer="inky7-buttons", config=line_config)

    def get_key(self) -> int|None:
        events: any = self.request.read_edge_events()
        if len(events) > 0:
            try:
                index: int = self.offsets.index(events[-1].line_offset)
                if index >= 0 and index < 4:
                    return index
            except ValueError as e:
                self.logger.exception("Button read exception", exc_info=e)

        return None