class InputProcessor:
    def __init__(self, processor:any):
        self.processor: any = processor
        self.prev_key: int = None

    def get_key(self) -> int:
        new_key: int = self.processor.get_key()
        if new_key != self.prev_key:
            self.prev_key = new_key
            return new_key
        
        return None