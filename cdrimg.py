from math import sqrt
from sys import argv
import os.path
from PIL import Image
from numpy import array

from lib import SafePixelGetter

DEBUG = False


def check_input():
    usage_msg = open("lib/USAGE.txt").read()

    if len(argv) not in range(4, 6):
        print(usage_msg)
        return False

    # Make sure option is valid
    if argv[2] not in ["encode", "decode"]:
        print("Error: invalid option")
        print(usage_msg)
        return False

    elif argv[2] == "encode":
        if len(argv) < 5:
            print("Error: no output file specified")
            print(usage_msg)
            return False

    # Make sure the input file exists
    if not os.path.isfile(argv[1]):
        print("Error: Given file does not exist.")
        print(usage_msg)
        return False

    return True


def rgb_dist(c1, c2):
    if not c1 or not c2:
        return 999
    dr_sq = (c2[0] - c1[0]) ** 2
    dg_sq = (c2[1] - c1[1]) ** 2
    db_sq = (c2[2] - c1[2]) ** 2
    return sqrt(dr_sq + dg_sq + db_sq)


def main(argv):
    if not DEBUG:
        if not check_input():
            return
    else:
        argv.append("decode")
        argv.append("output.cdr")

    if argv[2] == "encode":
        encode(argv[1], argv[3], argv[4])

    elif argv[2] == "decode":
        argv.append(50)
        decode(argv[1], argv[3])


def encode(path, compression_level, output_path):

    try:
        compression_level = int(compression_level)
        assert(compression_level in range(-1, 443))
    except:
        print("Compression level must be a positive integer less than 442!")

    image = Image.open(path)
    pil_pixels = image.load()
    pixels = SafePixelGetter.Pixels(pil_pixels)
    width = image.size[0]
    height = image.size[1]
    rgb = []

    threshold = compression_level
    flags = []
    compressed_data = []

    for x in range(width):
        flags.append([False] * height)

    for x in range(width):
        for y in range(height):
            if flags[x][y]:
                continue

            current_rgb = pixels.get(x, y)

            r = current_rgb[0]
            g = current_rgb[1]
            b = current_rgb[2]

            horizontal_extent = 0
            vertical_extent = 0

            # Determine maximum horizontal extent
            while True:
                next_rgb = pixels.get(x + horizontal_extent + 1, y)

                if not next_rgb:
                    break

                else:
                    # Check if the neighbouring pixel is the same
                    # if next_rgb == current_rgb:
                    if rgb_dist(next_rgb, current_rgb) <= threshold:
                        flags[x + horizontal_extent + 1][y] = True
                        horizontal_extent += 1
                    else:
                        break

            # Determine maximum vertical extent
            while True:
                next_rgb = pixels.get(x, y + vertical_extent + 1)

                # if next_rgb != current_rgb:
                if rgb_dist(next_rgb, current_rgb) > threshold:
                    break

                else:
                    # Check if the entire row up to the horizontal extent is the same
                    row_same = True
                    for i in range(horizontal_extent):
                        if pixels.get(x + i, y + vertical_extent + 1) != current_rgb:
                            row_same = False
                            break
                        else:
                            flags[x + i][y + vertical_extent] = True
                    if row_same:
                        vertical_extent += 1
                    else:
                        break

            compressed_data.append(
                (x, y, horizontal_extent, vertical_extent, current_rgb[0], current_rgb[1], current_rgb[2]))

            nr = r
            ng = g
            nb = b

            rgb.append((nr, ng, nb))

    flattened_compressed_data = list(array(compressed_data).flat)
    byte_data = bytearray(0)

    # Assign the first four bytes to the width and height of the image
    width_b = width.to_bytes(2, "big")
    height_b = height.to_bytes(2, "big")
    byte_data += (width_b + height_b)

    i = 0
    # for i in range(0, len(flattened_compressed_data)):
    while i < len(flattened_compressed_data):
        data_type = i % 7

        # Data type is 2-byte value
        if data_type in range(0, 4):
            val = int(flattened_compressed_data[i]).to_bytes(2, "big")
            byte_data += val

        # Data type is single-byte value
        else:
            byte_data.append(flattened_compressed_data[i])

        i += 1

    '''
    Format of bytes:
    First to second byte = image width
    Third to fourth byte = image height
    Subsequent bytes are in groups of 11:
    1-2 byte = x coordinate
    3-4 byte = y coordinate
    5-6 byte = width of rect
    7-8 byte = height of rect
    9, 10, 11 bytes = rgb
    '''

    f = open(output_path+".cdr", "wb")
    f.write(byte_data)
    f.close()

    # Debug output image
    '''new_image = Image.new("RGB", (width, height), 0)
    new_image.putdata(rgb)
    new_image.save("output.png")'''


def decode(path, output_path):
    f = open(path, "rb")
    byte_data = bytearray(f.read())

    width = 256 * byte_data[0] + byte_data[1]
    height = 256 * byte_data[2] + byte_data[3]
    rgb = []

    for rows in range(height):
        rgb.append([(0, 0, 0)] * width)

    # Reconstruct RGB data from CDR data
    for i in range(4, len(byte_data), 11):
        x = 256 * byte_data[i] + byte_data[i + 1]
        y = 256 * byte_data[i + 2] + byte_data[i + 3]
        w = 256 * byte_data[i + 4] + byte_data[i + 5]
        h = 256 * byte_data[i + 6] + byte_data[i + 7]
        r = byte_data[i + 8]
        g = byte_data[i + 9]
        b = byte_data[i + 10]

        for vertical_extent in range(h + 1):
            for horizontal_extent in range(w + 1):
                rgb[y + vertical_extent][x + horizontal_extent] = (r, g, b)

    flattened_rgb = list(array(rgb).flat)
    flattened_rgb = [tuple(flattened_rgb[i:i + 3]) for i in range(0, len(flattened_rgb), 3)]

    new_image = Image.new("RGB", (width, height), 0)
    new_image.putdata(flattened_rgb)
    new_image.save(output_path+".png")


if __name__ == '__main__':
    main(argv)
