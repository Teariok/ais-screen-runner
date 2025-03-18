#!/usr/bin/env python3

from dotenv import dotenv_values
from message_processor import MessageProcessor
from ship_tracker import ShipTracker
from screen import Screen
from renderer.image_renderer import ImageRenderer
from renderer.inky_renderer import InkyRenderer
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

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler('ais.log'),logging.StreamHandler()])

if not os.path.exists(".env"):
    logger.critical(".env file does not exist!")
    os._exit(-1)

config = dotenv_values(".env")

no_screen = True
if no_screen:
    screen = Screen(config["IMG_DIR"],ImageRenderer("output.jpg"))
else:
    screen = Screen(config["IMG_DIR"],InkyRenderer())

ais_message_queue = Queue()
vessel_update_queue = Queue()

mpt = Thread(target=begin_message_processing)
mpt.start()

stt = Thread(target=begin_ship_tracking)
stt.start()

while True:
    msg = vessel_update_queue.get()
    if msg != None and msg[0] == "zone":
        ship = msg[1]
        zone_prev = msg[2]

        logger.info(f"{ship['name']} changed zone from {zone_prev} to {ship.get('zone','None')}")
        
        if ship.get("zone", None) != None:
            screen.displayShip(ship)