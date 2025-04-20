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

    MAX_BLOCK_SIZE = 32
    READ_INTERVAL = 0.05
    ERROR_WAIT_TIME = 0.01

    def __init__(self):
        self.logger:logging.Logger = logging.getLogger(__name__)
        self.bus = SMBus(1)
        self.handle_message = None

    def read_byte(self, addr):
        self.bus.write_byte(self.DEVICE_ADDR, addr)
        return self.bus.read_byte(self.DEVICE_ADDR)
    
    def read_block(self, size: int) -> str:
        buff = bytearray()
        while size > 0:
            buff_size = min(size, self.MAX_BLOCK_SIZE)
            block = self.bus.read_i2c_block_data(self.DEVICE_ADDR, self.MESSAGE_BUFF_ADDR, buff_size)
            buff.extend(block)
            size -= buff_size
        return bytes(buff)

    def log_device_info(self):
        device_type = self.read_byte(self.DEVICE_TYPE_ADDR)
        version_major = self.read_byte(self.FIRMWARE_MAJOR_ADDR)
        version_minor = self.read_byte(self.FIRMWARE_MINOR_ADDR)
        self.logger.info(f"dAISy device ID: 0x{device_type:02X}, firmware v{version_major}.{version_minor}")

    def begin_processing(self):
        self.log_device_info()

        if self.handle_message is None:
            self.logger.critical("Cannot begin message processing with no message handler")
            return

        self.bus.write_byte(self.DEVICE_ADDR, self.MESSAGE_BUFF_ADDR)
        message = b""

        while True:
            try:
                high = self.read_byte(self.BYTES_AVAIL_H_ADDR)
                low = self.read_byte(self.BYTES_AVAIL_L_ADDR)
                available = (high << 8) | low

                if available == 0:
                    time.sleep(self.READ_INTERVAL)
                    continue

                self.logger.debug(f"Bytes available: {available}")
                message += self.read_block(available)

                while b"\r\n" in message:
                    complete, _, remainder = message.partition(b"\r\n")
                    self.logger.info(f"MSG: {complete}")
                    self.handle_message(complete)
                    message = remainder

            except OSError as ex:
                self.logger.warning(f"Error reading from I2C: {ex}")
                time.sleep(self.ERROR_WAIT_TIME)