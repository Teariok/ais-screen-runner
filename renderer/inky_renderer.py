from inky.auto import auto

class InkyRenderer:
    def __init__(self):
        self.inky = auto(ask_user=True, verbose=False)

        self.height = self.inky.height
        self.width = self.inky.width
        return

    def render(self, img):
        img = img.rotate(90,expand=1)

        self.inky.set_image(img)
        self.inky.show()
