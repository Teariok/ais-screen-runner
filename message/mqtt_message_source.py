import paho.mqtt.client as mqtt
import logging

class MQTTMessageSource:
    def __init__(self, mqtt_addr:str, mqtt_port:int, mqtt_topic:str):
        self.logger:logging.Logger = logging.getLogger(__name__)

        self.mqtt_addr:str = mqtt_addr
        self.mqtt_port:int = mqtt_port
        self.mqtt_topic:str = mqtt_topic

        self.mqttc:mqtt.Client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqttc.on_connect = self.__on_connected
        self.mqttc.on_message = self.__on_message

        self.handle_message = None

    def __on_connected(self, client, userdata, flags, reason_code, properties):
        self.logger.info(f"Connected with result code {reason_code}")
        client.subscribe(self.mqtt_topic)

    def __on_message(self, client, userdata, msg):
        if msg.topic.startswith("/sensor"):
            self.handle_message(msg.payload)

    def begin_processing(self):
        self.logger.info(f"Connect to {self.mqtt_addr}:{self.mqtt_port}")
        self.mqttc.connect(self.mqtt_addr, self.mqtt_port, 60)
        self.mqttc.loop_forever()