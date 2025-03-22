import keyboard

class KeyboardInput:
    def get_key(self):
        if keyboard.is_pressed('1'):
            return 0
        elif keyboard.is_pressed('2'):
            return 1
        elif keyboard.is_pressed('3'):
            return 2
        elif keyboard.is_pressed('4'):
            return 3
        
        return None