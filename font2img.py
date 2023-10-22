import os, sys, argparse, pprint
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
parser.add_argument('-s', '--size', type=int, default=0, help='final image size')

parser.add_argument('-o', '--out', default='tmp', help='output directory')

parser.add_argument('-b', '--bounding-box', type=bool, default=False, action=argparse.BooleanOptionalAction, help='process bounding box resize')

# type of characters to include
parser.add_argument('-u', '--upper', type=bool, default=False, action=argparse.BooleanOptionalAction, help='include upper-case letters')
parser.add_argument('-l', '--lower', type=bool, default=False, action=argparse.BooleanOptionalAction, help='include lower-case letters')
parser.add_argument('-n', '--number', type=bool, default=False, action=argparse.BooleanOptionalAction, help='include numeric values')

parser.add_argument('--unicode', default='', help='comma-separated unicode range (eg 0x30-0x39,0x41-0x5a)')

args = parser.parse_args()

# set up global variables from config
font_file = args.font
out_dir = args.out
resolution = args.resolution
final_size = args.size
do_bbox = args.bounding_box
inc_upper = args.upper
inc_lower = args.lower
inc_num = args.number
unicode = args.unicode

# create output directory if does not exists
if not os.path.exists(out_dir):
    os.mkdir(out_dir)

# delete everything in output directory
os.system('rm -rf {}/*'.format(out_dir))

print('''
================================
RENDERING OPTIONS:
   FONT:         {}
    RESOLUTION:   {}
    SIZE:         {}
    UNICODE:      {}
    UPPER_CASE:   {}
    LOWER_CASE:   {}
    NUMERIC:      {}
    OUTDIR:       {}
================================
'''.format(
    font_file,
    resolution,
    final_size,
    unicode,
    inc_upper,
    inc_lower,
    inc_num,
    out_dir
))

num_map = {
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

# create map of all unicodes to parse
# number            0x30 - 0x39
# upper             0x41 - 0x5a
# lower             0x61 - 0x7a
# fw number         0xff10 - 0xff19
# fw upper          0xff21 - 0xff3a
# fw lower          0xff41 - 0xff5a
# tick tri outline  0x25b3
# tick tri solid    0x25b2
# tick straight     0x2503
# unit m/s          0x33a7
# unit cal          0x3388
# unit kcal         0x3398
# unit am           0x33c2
# unit pm           0x33d8
# special bg kor    0x3266

# construct unicode based on the args
if inc_upper:
    unicode += ',0x41-0x5a'
if inc_lower:
    unicode += ',0x61-0x7a'
if inc_num:
    unicode += ',0x30-0x39'


# parse unicode argument
def parse_unicode(u):
    ulist = {}
    if u == '':
        return ulist
    u = u.replace(" ", "")
    tokens = u.split(",")
    for t in tokens:
        if t == "":
            continue
        rv = t.split("-")
        if len(rv) > 2:
            sys.exit("invalid unicode argument {}".format(u))
        elif len(rv) == 1:
            ulist[int(rv[0], 16)] = t
        else:
            start = int(rv[0], 16)
            end = int(rv[1], 16)
            for x in range(start, end+1, 1):
                ulist[x] = t
    return ulist

# parse unicode into lookup table
udict = parse_unicode(unicode)

print(udict)

font = fontforge.open(font_file)
for glyph in font:

    ch = font[glyph]

    # filter out valid unicodes
    if not ch.isWorthOutputting():
        continue

    if ch.unicode not in udict:
        continue

    # remove all extensions from the name
    name = ch.glyphname.split(".")[0]

    # rename if maps to a number
    if name in num_map:
        name = num_map[name]

    # export image file
    fname = "{}/{}.png".format(out_dir, name)
    ch.export(fname, pixelsize=resolution)
    print("exporting {}".format(fname))

    # open image with PIL for post-processing
    img = Image.open(fname)

    # convert image to RGB
    img = img.convert('RGB')

    # determine bounding box
    if do_bbox:
        bg = Image.new(img.mode, img.size, img.getpixel((0,0)))
        diff = ImageChops.difference(img, bg)
        diff = ImageChops.add(diff, diff, 2.0, -100)
        bbox = diff.getbbox()
        if not bbox:
            sys.exit('ERROR determining bounding box')
        # crop to bounding box
        img = img.crop(bbox)

    w, h = img.size

    # increase size to fixed canvas size
    if final_size != 0:
        r = final_size
    else:
        r = max(w, h)

    squareImg = Image.new('RGB', (r, r), (255, 255, 255))
    hoffset = int((r - w) / 2)
    voffset = int((r - h) / 2)
    squareImg.paste(img, (hoffset, voffset, w+hoffset, h+voffset))

    # save image
    squareImg.save(fname)

