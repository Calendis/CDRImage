class Pixels():
    def __init__(self, PIL_pixel_access):
        self.pixels = PIL_pixel_access

    def get(self, x, y):
        r = 0
        g = 0
        b = 0

        try:
            r = self.pixels[x, y][0]
            g = self.pixels[x, y][1]
            b = self.pixels[x, y][2]

        except IndexError:
            return False

        return r, g, b
