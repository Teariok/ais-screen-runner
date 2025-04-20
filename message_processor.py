import json
import logging

from pyais.queue import NMEAQueue
from pyais.stream import TagBlockQueue


class MessageProcessor:
    def __init__(self, message_source:any, message_handler:any):
        self.logger:logging.Logger = logging.getLogger(__name__)

        self.message_handler:any = message_handler

        self.source = message_source
        self.source.handle_message = self.__handle_message

        tbq:TagBlockQueue = TagBlockQueue()
        self.message_queue:NMEAQueue = NMEAQueue(tbq=tbq)

    def begin_processing(self):
        self.source.begin_processing()

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