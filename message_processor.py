import paho.mqtt.client as mqtt
from pyais.stream import TagBlockQueue
from pyais.queue import NMEAQueue
import json
import logging

class MessageProcessor:
    def __init__(self, mqtt_addr, mqtt_port, mqtt_topic):
        self.logger = logging.getLogger(__name__)

        self.mqtt_addr = mqtt_addr
        self.mqtt_port = mqtt_port
        self.mqtt_topic = mqtt_topic
        self.on_message = None

        tbq = TagBlockQueue()
        self.message_queue = NMEAQueue(tbq=tbq)

        self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
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
        if not callable(self.on_message):
            raise TypeError("on_message must be set to a callback function")

        self.message_queue.put_line(msg.payload)
        
        while True:
            ais_message = self.message_queue.get_or_none()
            if not ais_message:
                break

            decoded_sentence = ais_message.decode().asdict()
                
            for key, value in decoded_sentence.items():
                if isinstance(value, bytes):
                    decoded_sentence[key] = value.decode('utf-8', errors='ignore')
                
            self.on_message(json.dumps(decoded_sentence))