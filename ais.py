#!/usr/bin/env python3

import json
import logging
import os
import time
from queue import Queue
from threading import Thread

from dotenv import dotenv_values

from input.keyboard_input import KeyboardInput
from input_processor import InputProcessor
from message_processor import MessageProcessor
from renderer.image_renderer import ImageRenderer
from renderer.inky_renderer import InkyRenderer
from screen.ship_map_screen import ShipMapScreen
from screen.ship_table_screen import ShipTableScreen
from screen.ship_zone_screen import ShipZoneScreen
from screen_manager import ScreenManager
from ship_tracker import ShipTracker


def begin_message_processing():
    try:
        message_processor:MessageProcessor = MessageProcessor(env["MQTT_ADDR"], int(env["MQTT_PORT"]), env["MQTT_AIS_TOPIC"], ais_message_queue)
        message_processor.begin_processing()
    except Exception as ex:
        logger.exception("Message Processing Exception", exc_info=ex)

def begin_ship_tracking():
    try:
        # Init the tracker to keep a record of vessels we've seen
        ship_tracker:ShipTracker = ShipTracker(int(env["MAX_DYN_SIZE"]), env["DB_NAME"], ais_message_queue, vessel_update_queue)

        # Set the notification zones up from the env
        zones:list[dict[str,any]] = prefs.get("ZONES",[])
        for zone in zones:
            ship_tracker.add_zone((zone["name"], zone["lat"], zone["lon"], zone["radius"]))

        ship_tracker.begin_processing()
    except Exception as ex:
        logger.exception("Ship Tracking Exception", exc_info=ex)

def begin_screen_updates(no_screen:bool = True):
    try:
        renderer:ImageRenderer|InkyRenderer = ImageRenderer("output.jpg") if no_screen else InkyRenderer()
        screens:list[ShipZoneScreen|ShipTableScreen|ShipMapScreen] = [
            ShipZoneScreen(env["IMG_DIR"], renderer),
            ShipTableScreen(env["IMG_DIR"], renderer),
            ShipMapScreen(env["IMG_DIR"], renderer, env["MAPBOX_API_KEY"], prefs.get("MAP_BOUNDS", []), prefs.get("MAPBOX_LIGHT_STYLE",""), prefs.get("MAPBOX_DARK_STYLE","")),
        ]

        screen_manager:ScreenManager = ScreenManager(screens, vessel_update_queue)
        screen_manager.begin_processing()
    except Exception as ex:
        logger.exception("Screen Update Exception", exc_info=ex)

logger:logging.Logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler('ais.log'),logging.StreamHandler()])

if not os.path.exists(".env"):
    logger.critical(".env file does not exist!")
    os._exit(-1)

env:dict[str,str|None] = dotenv_values(".env")
prefs:dict[str,any] = {}

if os.path.exists("user_prefs.json"):
    with open("user_prefs.json") as prefs_file:
        prefs = json.load(prefs_file)

ais_message_queue:Queue = Queue()
vessel_update_queue:Queue = Queue()

msg_proc_thread:Thread = Thread(target=begin_message_processing)
msg_proc_thread.start()

ship_track_thread:Thread = Thread(target=begin_ship_tracking)
ship_track_thread.start()

screen_update_thread:Thread = Thread(target=begin_screen_updates, args=[False])
screen_update_thread.start()

input_processor:InputProcessor = InputProcessor(KeyboardInput())

while True:
    key_val: int = input_processor.get_key()
    if key_val == 3:
        vessel_update_queue.put(("mode",))
    elif key_val is not None:
        vessel_update_queue.put(("screen",key_val))

    time.sleep(0.5)