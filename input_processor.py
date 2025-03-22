class InputProcessor:
    def __init__(self, processor):
        self.processor = processor
        self.prev_key = None

    def get_key(self):
        new_key = self.processor.get_key()
        if new_key != self.prev_key:
            self.prev_key = new_key
            return new_key
        
        return None