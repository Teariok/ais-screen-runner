from inky.auto import auto

class InkyRenderer:
    def __init__(self):
        self.inky = auto(ask_user=True, verbose=False)

        self.height = self.inky.width
        self.width = self.inky.height
        return

    def render(self, img):
        img = img.rotate(90,expand=1)

        self.inky.set_image(img)
        self.inky.show()
