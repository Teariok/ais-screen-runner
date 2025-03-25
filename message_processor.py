import json
import logging

import paho.mqtt.client as mqtt
from pyais.queue import NMEAQueue
from pyais.stream import TagBlockQueue


class MessageProcessor:
    def __init__(self, mqtt_addr:str, mqtt_port:int, mqtt_topic:str, message_handler:any):
        self.logger:logging.Logger = logging.getLogger(__name__)

        self.mqtt_addr:str = mqtt_addr
        self.mqtt_port:int = mqtt_port
        self.mqtt_topic:str = mqtt_topic
        self.message_handler:any = message_handler

        tbq:TagBlockQueue = TagBlockQueue()
        self.message_queue:NMEAQueue = NMEAQueue(tbq=tbq)

        self.mqttc:mqtt.Client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqttc.on_connect = self.__on_connected
        self.mqttc.on_message = self.__on_message

    def begin_processing(self):
        self.logger.info(f"Connect to {self.mqtt_addr}:{self.mqtt_port}")
        self.mqttc.connect(self.mqtt_addr, self.mqtt_port, 60)
        self.mqttc.loop_forever()

    def __on_connected(self, client, userdata, flags, reason_code, properties):
        self.logger.info(f"Connected with result code {reason_code}")
        client.subscribe(self.mqtt_topic)

    def __on_message(self, client, userdata, msg):
        if msg.topic.startswith("/sensor"):
            self.__handle_message(msg)

    def __handle_message(self, msg):
        if self.message_handler is None:
            raise TypeError("Message handler must be set to a callback function")

        # Use the message queue to help with handling multipart messages
        self.message_queue.put_line(msg.payload)
        
        while True:
            ais_message = self.message_queue.get_or_none()
            if not ais_message:
                break

            decoded_sentence:dict[str,any] = ais_message.decode().asdict()
            
            for key, value in decoded_sentence.items():
                if isinstance(value, bytes):
                    decoded_sentence[key] = value.decode('utf-8', errors='ignore')
                
            self.message_handler.put(json.dumps(decoded_sentence))