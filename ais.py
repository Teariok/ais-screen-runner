#!/usr/bin/env python3

import json
from dotenv import dotenv_values
from message_processor import MessageProcessor
from ship_tracker import ShipTracker
from screen import Screen
from renderer.image_renderer import ImageRenderer
from renderer.inky_renderer import InkyRenderer
import logging
import os

def handle_ship_message(msg):
    try:
        data = json.loads(msg)
    except json.JSONDecodeError as e:
        logger.exception(f"Error decoding JSON", exc_info=e)
        return

    ship_tracker.update_vessel(data)

def handle_zone_change(ship,zone_prev):
    logger.info(f"{ship['name']} changed zone from {zone_prev} to {ship.get('zone','None')}")
    if ship.get("zone", None) != None:
        screen.displayShip(ship)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler('ais.log'),logging.StreamHandler()])

if not os.path.exists(".env"):
    logger.critical(".env file does not exist!")
    os._exit(-1)

config = dotenv_values(".env")

# Init the tracker to keep a record of vessels we've seen
ship_tracker = ShipTracker(int(config["MAX_DYN_SIZE"]), config["DB_NAME"])
ship_tracker.on_zone_change = handle_zone_change

# Set the notification zones up from the env
zones = config.get("ZONES","").strip('()').split('),(')
for zone in zones:
    parts = zone.split(',')
    ship_tracker.add_zone((parts[0].strip(), float(parts[1]), float(parts[2]), float(parts[3])))

no_screen = False
if no_screen:
    screen = Screen(config["IMG_DIR"],ImageRenderer("output.jpg"))
else:
    screen = Screen(config["IMG_DIR"],InkyRenderer())

message_processor = MessageProcessor(config["MQTT_ADDR"], int(config["MQTT_PORT"]), config["MQTT_AIS_TOPIC"])
message_processor.on_message = handle_ship_message
message_processor.begin_processing()