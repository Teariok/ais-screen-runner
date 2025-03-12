class ImageRenderer:
    def __init__(self, name, width = 800, height = 480):
        self.img_name = name
        self.height = height
        self.width = width

    def render(self, img):
        img.save(self.img_name)