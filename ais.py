#!/usr/bin/env python3

import paho.mqtt.client as mqtt
from pyais.stream import TagBlockQueue
from pyais.queue import NMEAQueue
import json
import filter
import shipdata
import screen
import argparse
from renderer.image_renderer import ImageRenderer
from renderer.inky_renderer import InkyRenderer
from dotenv import dotenv_values

def on_connect(client, userdata, flags, reason_code, properties):
        print(f"Connected with result code {reason_code}")
        client.subscribe(config.MQTT_AIS_TOPIC)

def on_message(client, userdata, msg):
        if msg.topic.startswith("/sensor"):
                handle_sensor_message(msg)

def handle_sensor_message(msg):
        queue.put_line(msg.payload)
        
        while True:
                ais_message = queue.get_or_none()
                if not ais_message:
                        break

                decoded_sentence = ais_message.decode().asdict()
                
                for key, value in decoded_sentence.items():
                        if isinstance(value, bytes):
                                decoded_sentence[key] = value.decode('utf-8', errors='ignore')
                
                handle_ship_message(json.dumps(decoded_sentence))

def handle_ship_message(msg):
        try:
                data = json.loads(msg)
        except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                return

        mmsi = data["mmsi"]

        if len(str(mmsi)) < 9:
                print("MMSI is not a ship. Skip update.")
                return

        message_type = data["msg_type"]

        last_pos = shipData.getLastKnownPosition(mmsi)

        shipData.updateShipDynamicData(data)
        ship = shipData.updateStaticShipData(data, message_type == 5)

        if ship == None:
                print("Ship Update Error")
                return
        
        log = "Ship: " + ship["name"] + " (" + str(mmsi) + ")."

        if message_type <= 4 or message_type == 18:
                log += "\t\tPos: "+str(data["lat"])+","+str(data["lon"])
                if shipFilter.isInZone(data["lat"],data["lon"]):
                        log += "\t\tIn Zone. Prev Pos: "+str(last_pos)
                        if last_pos == None or not shipFilter.isInZone(last_pos[0],last_pos[1]):
                                log += "\t\tZone Entry. Update Screen"
                                shipScreen.displayShip(ship)
                        else:
                                log += "\t\tAlready in Zone."
                else:
                        log += "\t\tNot in Zone"
        
        print(log)

config = dotenv_values(".env")
print(config)

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-noscreen', action='store_const', const=True)
args = arg_parser.parse_args()

tbq = TagBlockQueue()
queue = NMEAQueue(tbq=tbq)

shipFilter = filter.ShipFilter()
#for zone in config.ZONES:
#        shipFilter.addZone(zone)

shipData = shipdata.ShipData(config.DB_NAME,config.IMG_DIR,config.MAX_DYN_SIZE)
shipData.initTables()

renderer = ImageRenderer("output.jpg") if args.noscreen else InkyRenderer()
shipScreen = screen.Screen(config.IMG_DIR,renderer)

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.connect(config.MQTT_ADDR, config.MQTT_PORT, 60)
mqttc.loop_forever()
