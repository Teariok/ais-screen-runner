#!/usr/bin/env python3

import json
from dotenv import dotenv_values
from input.inky_input import InkyInput
from input_processor import InputProcessor
from input.keyboard_input import KeyboardInput
from message_processor import MessageProcessor
from screen.ship_map_screen import ShipMapScreen
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
    message_processor = MessageProcessor(env["MQTT_ADDR"], int(env["MQTT_PORT"]), env["MQTT_AIS_TOPIC"], ais_message_queue)
    message_processor.begin_processing()

def begin_ship_tracking():
    # Init the tracker to keep a record of vessels we've seen
    ship_tracker = ShipTracker(int(env["MAX_DYN_SIZE"]), env["DB_NAME"], ais_message_queue, vessel_update_queue)

    # Set the notification zones up from the env
    zones = prefs.get("ZONES",[])
    for zone in zones:
        ship_tracker.add_zone((zone["name"], zone["lat"], zone["lon"], zone["radius"]))

    ship_tracker.begin_processing()

def begin_screen_updates(no_screen = True):
    renderer = ImageRenderer("output.jpg") if no_screen else InkyRenderer()
    screens = [
        ShipZoneScreen(env["IMG_DIR"], renderer),
        ShipTableScreen(env["IMG_DIR"], renderer),
        ShipMapScreen(env["IMG_DIR"], renderer, env["MAPBOX_API_KEY"], prefs.get("MAP_BOUNDS", []), prefs.get("MAPBOX_LIGHT_STYLE",""), prefs.get("MAPBOX_DARK_STYLE","")),
    ]

    screen_manager = ScreenManager(screens, vessel_update_queue)
    screen_manager.begin_processing()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler('ais.log'),logging.StreamHandler()])

if not os.path.exists(".env"):
    logger.critical(".env file does not exist!")
    os._exit(-1)

env = dotenv_values(".env")
prefs = {}

if os.path.exists("user_prefs.json"):
    with open("user_prefs.json") as prefs_file:
        prefs = json.load(prefs_file)

ais_message_queue = Queue()
vessel_update_queue = Queue()

msg_proc_thread = Thread(target=begin_message_processing)
msg_proc_thread.start()

ship_track_thread = Thread(target=begin_ship_tracking)
ship_track_thread.start()

screen_update_thread = Thread(target=begin_screen_updates, args=[False])
screen_update_thread.start()

input_processor = InputProcessor(InkyInput()) #KeyboardInput())

while True:
    key_val = input_processor.get_key()
    if key_val == 3:
        vessel_update_queue.put(("mode",))
    elif key_val != None:
        vessel_update_queue.put(("screen",key_val))

    #time.sleep(0.5)