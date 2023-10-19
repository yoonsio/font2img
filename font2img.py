import os, sys, argparse
from fontforge import *
from PIL import Image, ImageChops

# define cli arguments
parser = argparse.ArgumentParser(description='fontforge font render script')

# font file as positional argument
parser.add_argument('font', help='font file name')

# initial font rendering resolution
parser.add_argument('-r', '--resolution', type=int, default=1000, help='font render size')

# final image size - font-specific configuration
# roughly 1000 for alpha, 500 for numeric
parser.add_argument('-s', '--size', type=int, default=500, help='final image size')

parser.add_argument('-o', '--out', default='tmp', help='output directory')

# type of characters to include
parser.add_argument('-u', '--upper', type=bool, default=False, action=argparse.BooleanOptionalAction, help='include upper-case letters')
parser.add_argument('-l', '--lower', type=bool, default=False, action=argparse.BooleanOptionalAction, help='include lower-case letters')
parser.add_argument('-n', '--number', type=bool, default=False, action=argparse.BooleanOptionalAction, help='include numeric values')

# character filter in regex
parser.add_argument('-f', '--filter', help='regex filter for characters')

args = parser.parse_args()

# set up global variables from config
font_file = args.font
resolution = args.resolution
final_size = args.size
inc_upper = args.upper
inc_lower = args.lower
inc_num = args.number
out_dir = args.out
char_filter = args.filter

# create output directory if does not exists
if not os.path.exists(out_dir):
    os.mkdir(out_dir)

print('''
================================
RENDERING OPTIONS:
    FONT:         {}
    RESOLUTION:   {}
    SIZE:         {}
    UPPER_CASE:   {}
    LOWER_CASE:   {}
    NUMERIC:      {}
    OUTDIR:       {}
================================
'''.format(
    font_file,
    resolution,
    final_size,
    inc_upper,
    inc_lower,
    inc_num,
    out_dir
))

numMap = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
}

# 'A' = 65
# '0' = 48

# start processing glyphs

font = fontforge.open(font_file)
for glyph in font:

    ch = font[glyph]
    gname = ch.glyphname

    if not ch.isWorthOutputting():
        continue

    name = gname

    # determine if char is a numeric value
    if 'numr' in gname:
        if not inc_num:
            continue
        tokens = gname.split(".")
        # ignore special style (eg. ss02)
        if len(tokens) > 2:
            continue
        name = numMap[tokens[0]]

    # determine if char is lower/upper letter
    elif len(gname) == 1:
        if gname.islower() and not inc_lower:
            continue
        if gname.isupper() and not inc_upper:
            continue
    else:
        continue

    # export image file
    fname = "{}/{}.png".format(out_dir, name)
    ch.export(fname, pixelsize=resolution)
    print("exporting {}".format(fname))

    # open image with PIL for post-processing
    img = Image.open(fname)

    # convert image to RGB
    img = img.convert('RGB')

    # determine bounding box
    bg = Image.new(img.mode, img.size, img.getpixel((0,0)))
    diff = ImageChops.difference(img, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if not bbox:
        sys.exit('ERROR determining bounding box')

    # crop to bounding box
    img = img.crop(bbox)

    # increase canvas size to final size
    w, h = img.size
    r = final_size
    squareImg = Image.new('RGB', (r, r), (255, 255, 255))
    hoffset = int((r - w) / 2)
    voffset = int((r - h) / 2)
    squareImg.paste(img, (hoffset, voffset, w+hoffset, h+voffset))

    # save image
    squareImg.save(fname)

