from smbus2 import SMBus
import time
import logging

class DaisyMessageSource:
    DEVICE_ADDR = 0x33

    DEVICE_TYPE_ADDR = 0x00
    FIRMWARE_MAJOR_ADDR = 0x01
    FIRMWARE_MINOR_ADDR = 0x02
    BYTES_AVAIL_H_ADDR = 0xFD
    BYTES_AVAIL_L_ADDR = 0xFE
    MESSAGE_BUFF_ADDR = 0xFF

    def __init__(self):
        self.logger:logging.Logger = logging.getLogger(__name__)
        self.bus = SMBus(1)
        self.handle_message = None

    def read_byte(self, addr):
        self.bus.write_byte(self.DEVICE_ADDR, addr)
        return self.bus.read_byte(self.DEVICE_ADDR)

    def begin_processing(self):
        if self.handle_message is None:
            self.logger.critical("Cannot begin message processing with no message handler")
            return

        self.bus.write_byte(self.DEVICE_ADDR, self.MESSAGE_BUFF_ADDR)
        message = ""

        while True:
            try:
                high = self.read_byte(self.BYTES_AVAIL_H_ADDR)
                low = self.read_byte(self.BYTES_AVAIL_L_ADDR)
                available = (high << 8) | low

                if available == 0:
                    time.sleep(0.05)
                    continue

                data = self.bus.read_block_data(self.DEVICE_ADDR, self.MESSAGE_BUFF_ADDR, available)
                message += bytes(data).decode('utf-8')

                while "\r\n" in message:
                    complete, _, remainder = message.partition("\r\n")
                    self.handle_message(complete.strip())
                    message = remainder

            except OSError as ex:
                self.logger.warning(f"Error reading from I2C: {ex}")
                time.sleep(0.1)