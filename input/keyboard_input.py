import keyboard

class KeyboardInput:
    def get_key(self) -> int|None:
        keys: list[str] = ['1','2','3','4']

        for k in keys:
            if keyboard.is_pressed(k):
                return keys.index(k)
        
        return None