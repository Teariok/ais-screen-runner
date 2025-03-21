#!/usr/bin/env python3

from dotenv import dotenv_values
from input_processor import InputProcessor
from input.keyboard_input import KeyboardInput
from message_processor import MessageProcessor
from ship_tracker import ShipTracker
from screen_manager import ScreenManager
from renderer.image_renderer import ImageRenderer
from renderer.inky_renderer import InkyRenderer
from screen.ship_zone_screen import ShipZoneScreen
from screen.ship_table_screen import ShipTableScreen
import logging
import os
from queue import Queue
from threading import Thread

def begin_message_processing():
    message_processor = MessageProcessor(config["MQTT_ADDR"], int(config["MQTT_PORT"]), config["MQTT_AIS_TOPIC"], ais_message_queue)
    message_processor.begin_processing()

def begin_ship_tracking():
    # Init the tracker to keep a record of vessels we've seen
    ship_tracker = ShipTracker(int(config["MAX_DYN_SIZE"]), config["DB_NAME"], ais_message_queue, vessel_update_queue)

    # Set the notification zones up from the env
    zones = config.get("ZONES","").strip('()').split('),(')
    for zone in zones:
        parts = zone.split(',')
        ship_tracker.add_zone((parts[0].strip(), float(parts[1]), float(parts[2]), float(parts[3])))

    ship_tracker.begin_processing()

def begin_screen_updates(no_screen = True):
    renderer = ImageRenderer("output.jpg") if no_screen else InkyRenderer()
    screens = [
        ShipTableScreen(config["IMG_DIR"], renderer),
        ShipZoneScreen(config["IMG_DIR"], renderer)
    ]
    screen_manager = ScreenManager(screens, vessel_update_queue)

    screen_manager.begin_processing()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler('ais.log'),logging.StreamHandler()])

if not os.path.exists(".env"):
    logger.critical(".env file does not exist!")
    os._exit(-1)

config = dotenv_values(".env")

ais_message_queue = Queue()
vessel_update_queue = Queue()

mpt = Thread(target=begin_message_processing)
mpt.start()

stt = Thread(target=begin_ship_tracking)
stt.start()

sut = Thread(target=begin_screen_updates)
sut.start()

input_processor = InputProcessor(KeyboardInput())

while True:
    key_val = input_processor.get_key()
    if key_val == 3:
        vessel_update_queue.put(("mode",))
    elif key_val != None:
        vessel_update_queue.put(("screen",key_val))

    #time.sleep(0.5)