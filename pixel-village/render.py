"""Render a top-down (3/4 view) pixel-art medieval village: 5 peasants at work.

The world is drawn at 640x330 pixels; a 480x270 camera pans across it and each
frame is scaled 4x (nearest neighbour) to 1920x1080.
Usage: python3 render.py <frames_dir>
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

WW, WH = 640, 330          # world size
VW, VH, SCALE = 480, 270, 4
FPS, DUR = 24, 10
N = FPS * DUR

OUT = (34, 26, 24)
GRASS = [(74, 100, 36), (94, 122, 44), (116, 144, 54), (142, 166, 68)]
DIRT = [(108, 74, 44), (136, 96, 58), (162, 120, 74), (184, 142, 90)]
STONE = [(86, 84, 80), (126, 120, 108), (164, 156, 136), (200, 192, 166)]
WALL = [(126, 108, 80), (170, 150, 108), (206, 188, 140), (226, 212, 168)]
WOOD = [(72, 46, 28), (106, 70, 40), (142, 96, 54), (178, 130, 74)]
PLASTER = [(196, 178, 140), (226, 212, 174)]
SLATE = [(36, 56, 62), (52, 80, 86), (70, 104, 108), (94, 132, 132)]
LEAF = [(36, 66, 30), (54, 92, 38), (76, 122, 46), (108, 152, 62)]
SKIN = [(228, 170, 126), (196, 136, 98)]
IRON = [(64, 66, 76), (104, 108, 120), (160, 166, 178), (210, 214, 222)]
FIRE = [(255, 236, 140), (255, 176, 60), (232, 100, 36)]
WATER = [(34, 70, 84), (54, 104, 120), (120, 170, 180)]
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16


def ease(p):
    p = min(1, max(0, p))
    return p * p * (3 - 2 * p)


def noise(w, h, cells, seed):
    rng = np.random.default_rng(seed)
    small = Image.fromarray((rng.random((cells[1], cells[0])) * 255).astype(np.uint8))
    return np.asarray(small.resize((w, h), Image.BICUBIC), dtype=float) / 255


def dither(field, palette):
    """Map a 0..1 field onto a palette with ordered (Bayer) dithering."""
    h, w = field.shape
    th = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w]
    idx = np.clip((field * len(palette) + th - 0.5).astype(int), 0, len(palette) - 1)
    return np.array(palette, dtype=np.uint8)[idx]


def layer(w=WW, h=WH):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def outlined(img, color=OUT):
    a = img.getchannel("A").point(lambda v: 255 if v else 0)
    grown = a.filter(ImageFilter.MaxFilter(3))
    out = Image.new("RGBA", img.size, color + (255,))
    out.putalpha(grown)
    out.alpha_composite(img)
    return out


def shadow(world, box, alpha=70):
    lay, d = layer(world.width, world.height)
    d.ellipse(box, fill=(20, 30, 14, alpha))
    world.alpha_composite(lay)


# ------------------------------------------------------------------ ground
def ground():
    g = noise(WW, WH, (22, 12), 1) * 0.75 + noise(WW, WH, (80, 42), 2) * 0.25
    img = Image.fromarray(dither(g * 0.9 + 0.05, GRASS)).convert("RGBA")

    # roads: an L/T shaped dirt track with organic edges
    mask = Image.new("L", (WW, WH), 0)
    md = ImageDraw.Draw(mask)
    md.rectangle([140, 0, 166, WH], fill=255)
    md.rectangle([140, 205, WW, 230], fill=255)
    md.ellipse([128, 192, 180, 244], fill=255)
    # worn yard ground around the house and the workyard
    md.ellipse([240, 180, 380, 240], fill=255)
    md.ellipse([186, 236, 330, 312], fill=200)
    md.ellipse([400, 160, 540, 230], fill=255)
    md.ellipse([440, 232, 600, 312], fill=180)
    m = np.asarray(mask.filter(ImageFilter.GaussianBlur(3)), dtype=float) / 255
    m = m + (noise(WW, WH, (90, 50), 3) - 0.5) * 0.5
    road = m > 0.5
    edge = road & ~(np.asarray(Image.fromarray((road * 255).astype(np.uint8))
                               .filter(ImageFilter.MinFilter(3))) > 0)
    dirt = dither(noise(WW, WH, (60, 30), 4) * 0.7 + 0.25, DIRT)
    arr = np.asarray(img).copy()
    arr[road, :3] = dirt[road]
    arr[edge, :3] = DIRT[0]
    img = Image.fromarray(arr)
    d = ImageDraw.Draw(img)

    rnd = random.Random(5)
    # wheel ruts
    for ry in (212, 223):
        for x in range(170, WW):
            d.point((x, ry + round(math.sin(x / 17) * 1.2)), fill=DIRT[0])
    for ry in (147, 159):
        for y in range(0, 196):
            d.point((ry + round(math.sin(y / 15) * 1.2), y), fill=DIRT[0])
    # pebbles
    for _ in range(120):
        x, y = rnd.randrange(WW), rnd.randrange(WH)
        if road[y, x]:
            d.point((x, y), fill=STONE[2])
            d.point((x, y + 1), fill=STONE[0])
    # grass tufts and flowers
    for _ in range(900):
        x, y = rnd.randrange(2, WW - 2), rnd.randrange(3, WH)
        if road[y, x] or road[y - 2, x]:
            continue
        d.point((x - 1, y - 1), fill=GRASS[3])
        d.point((x, y - 2), fill=GRASS[3])
        d.point((x + 1, y - 1), fill=GRASS[2])
        d.point((x, y), fill=GRASS[0])
    for _ in range(90):
        x, y = rnd.randrange(WW), rnd.randrange(WH)
        if not road[y, x]:
            d.point((x, y), fill=rnd.choice([(240, 236, 200), (248, 214, 90), (220, 120, 140)]))
    return img


# ------------------------------------------------------------------ props
def wall_h(world, x0, x1, y):
    lay, d = layer()
    d.rectangle([x0, y - 1, x1 - 1, y + 9], fill=WALL[0])
    for x in range(x0, x1, 10):
        j = (x // 10) % 2
        d.rectangle([x, y - j, x + 9, y + 3 - j], fill=WALL[3])
        d.rectangle([x, y + 4 - j, x + 9, y + 9], fill=WALL[1])
        d.line([x + 1, y + 4 - j, x + 8, y + 4 - j], fill=WALL[2])
        d.rectangle([x, y - j, x + 9, y + 9], outline=OUT)
    world.alpha_composite(lay)


def wall_v(world, x, y0, y1):
    lay, d = layer()
    d.rectangle([x, y0, x + 10, y1 + 2], fill=WALL[0])
    for y in range(y0, y1, 7):
        j = (y // 7) % 2
        d.rectangle([x + j, y, x + 9 + j, y + 4], fill=WALL[3])
        d.rectangle([x + j, y + 5, x + 9 + j, y + 9], fill=WALL[1])
        d.rectangle([x + j, y, x + 9 + j, y + 9], outline=OUT)
    world.alpha_composite(lay)


def house(world):
    shadow(world, [256, 160, 384, 206], 80)
    lay, d = layer()
    # roof slopes: ridge runs away from the camera
    A, B, L1, L2, R1, R2 = (310, 100), (310, 38), (250, 146), (250, 84), (370, 146), (370, 84)
    for poly, base in [((A, B, L2, L1), 3), ((A, B, R2, R1), 1)]:
        sl, sd = layer()
        sd.rectangle([0, 0, WW, WH], fill=SLATE[base])
        for k, cx in enumerate(range(252, 370, 6)):
            sd.line([cx, 0, cx, WH], fill=SLATE[0])
            for cy in range(30 + (k % 2) * 3, 150, 6):
                sd.line([cx + 1, cy, cx + 5, cy], fill=SLATE[max(0, base - 1)])
                sd.point((cx + 2, cy + 1), fill=SLATE[min(3, base + 1) if base == 3 else 2])
        pm = Image.new("L", (WW, WH), 0)
        ImageDraw.Draw(pm).polygon(poly, fill=255)
        lay.paste(sl, (0, 0), pm)
    # chimney
    d.rectangle([336, 26, 352, 72], fill=STONE[2])
    for cy in range(30, 72, 5):
        d.line([336, cy, 352, cy], fill=STONE[1])
        for cx in range(338 + (cy // 5 % 2) * 3, 352, 6):
            d.point((cx, cy - 2), fill=STONE[1])
    d.rectangle([346, 26, 352, 72], fill=STONE[1])
    d.rectangle([334, 22, 354, 27], fill=STONE[3])
    d.rectangle([339, 23, 349, 26], fill=OUT)
    # gable front
    d.polygon([(262, 146), (310, 108), (358, 146)], fill=PLASTER[1])
    d.line([310, 108, 310, 146], fill=WOOD[1], width=2)
    d.line([272, 146, 310, 118], fill=WOOD[1], width=2)
    d.line([348, 146, 310, 118], fill=WOOD[1], width=2)
    d.rectangle([304, 124, 316, 134], fill=WOOD[0])
    d.rectangle([306, 126, 314, 132], fill=(60, 50, 70))
    d.line([A, L1], fill=WOOD[2], width=4)
    d.line([A, R1], fill=WOOD[1], width=4)
    d.line([A[0], A[1] - 1, L1[0], L1[1] - 1], fill=WOOD[3])
    # facade
    d.rectangle([262, 146, 358, 190], fill=PLASTER[1])
    d.rectangle([262, 146, 266, 190], fill=WOOD[1])
    d.rectangle([354, 146, 358, 190], fill=WOOD[1])
    d.rectangle([262, 146, 358, 149], fill=WOOD[2])
    d.rectangle([262, 166, 358, 168], fill=WOOD[1])
    for bx in (284, 336):
        d.line([bx, 149, bx, 182], fill=WOOD[1], width=2)
    d.line([266, 166, 284, 150], fill=WOOD[1], width=2)
    d.line([354, 166, 336, 150], fill=WOOD[1], width=2)
    for x in range(262, 359, 8):
        d.rectangle([x, 182, x + 7, 190], fill=STONE[2], outline=STONE[0])
    # door with arch, hinges and ring
    d.rectangle([298, 158, 322, 190], fill=WOOD[0])
    d.pieslice([298, 150, 322, 168], 180, 360, fill=WOOD[0])
    d.rectangle([301, 160, 319, 190], fill=WOOD[2])
    d.pieslice([301, 153, 319, 167], 180, 360, fill=WOOD[2])
    for px in (305, 310, 315):
        d.line([px, 158, px, 190], fill=WOOD[1])
    for hy in (166, 180):
        d.line([301, hy, 309, hy], fill=IRON[0], width=2)
    d.ellipse([313, 172, 317, 176], outline=IRON[1])
    # windows with shutters
    for wx in (270, 340):
        d.rectangle([wx - 3, 154, wx, 166], fill=SLATE[2])
        d.rectangle([wx + 11, 154, wx + 14, 166], fill=SLATE[2])
        d.rectangle([wx, 154, wx + 11, 166], fill=(48, 44, 56))
        d.line([wx + 5, 154, wx + 5, 166], fill=WOOD[1])
        d.line([wx, 160, wx + 11, 160], fill=WOOD[1])
        d.point((wx + 2, 156), fill=(200, 210, 220))
        d.rectangle([wx - 1, 167, wx + 12, 169], fill=WOOD[2])
        for fx in range(wx, wx + 12, 3):
            d.point((fx, 166), fill=(220, 90, 90) if fx % 2 else (240, 220, 120))
    # steps
    d.rectangle([294, 190, 326, 196], fill=STONE[3])
    d.rectangle([294, 194, 326, 197], fill=STONE[1])
    d.rectangle([290, 197, 330, 203], fill=STONE[2])
    d.rectangle([290, 201, 330, 204], fill=STONE[0])
    world.alpha_composite(outlined(lay))


def barrel(d, x, y):
    d.rectangle([x - 6, y - 14, x + 6, y], fill=WOOD[2])
    d.rectangle([x + 2, y - 14, x + 6, y], fill=WOOD[1])
    d.rectangle([x - 6, y - 12, x + 6, y - 11], fill=IRON[1])
    d.rectangle([x - 6, y - 4, x + 6, y - 3], fill=IRON[1])
    d.ellipse([x - 6, y - 18, x + 6, y - 11], fill=WOOD[3])
    d.ellipse([x - 4, y - 17, x + 4, y - 12], fill=WOOD[2])


def crate(d, x, y):
    d.rectangle([x - 8, y - 14, x + 8, y - 9], fill=WOOD[3])
    d.rectangle([x - 8, y - 9, x + 8, y], fill=WOOD[2])
    d.line([x - 8, y - 9, x + 8, y], fill=WOOD[1], width=2)
    d.rectangle([x - 8, y - 9, x + 8, y], outline=WOOD[1])


def woodpile(world):
    shadow(world, [196, 270, 256, 292])
    lay, d = layer()
    d.rectangle([194, 246, 248, 286], fill=WOOD[1])
    for row in range(4):
        for col in range(6):
            cx, cy = 199 + col * 9 + (row % 2) * 4, 252 + row * 9
            if cx > 244:
                continue
            d.ellipse([cx - 5, cy - 5, cx + 4, cy + 4], fill=WOOD[1])
            d.ellipse([cx - 4, cy - 4, cx + 3, cy + 3], fill=WOOD[3])
            d.ellipse([cx - 2, cy - 2, cx + 1, cy + 1], outline=WOOD[2])
    for px in (194, 248):
        d.rectangle([px - 1, 240, px + 2, 288], fill=WOOD[2])
    world.alpha_composite(outlined(lay))


def stump(d, x, y, w=8):
    d.rectangle([x - w, y - 4, x + w, y + 4], fill=WOOD[1])
    d.rectangle([x + w // 2, y - 4, x + w, y + 4], fill=WOOD[0])
    d.ellipse([x - w, y - 8, x + w, y], fill=WOOD[3])
    d.ellipse([x - w + 3, y - 6, x + w - 3, y - 2], outline=WOOD[2])


def furnace(world):
    shadow(world, [462, 158, 528, 186], 90)
    lay, d = layer()
    cx, top, base = 490, 112, 174
    for y in range(top, base):
        hw = round(8 + (y - top) / (base - top) * 14)
        row = (y - top) // 5
        for x in range(cx - hw, cx + hw + 1):
            rel = (x - cx) / max(1, hw)
            shade = 3 if rel < -0.5 else 2 if rel < 0.3 else 1
            col = STONE[shade]
            if (y - top) % 5 == 0 or (x - cx + row * 3) % 8 == 0:
                col = STONE[max(0, shade - 1)]
            d.point((x, y), fill=col)
    d.ellipse([cx - 10, top - 4, cx + 10, top + 4], fill=STONE[3])
    d.ellipse([cx - 6, top - 2, cx + 6, top + 2], fill=OUT)
    d.rectangle([cx - 8, 156, cx + 8, base], fill=(40, 20, 16))
    d.pieslice([cx - 8, 150, cx + 8, 162], 180, 360, fill=(40, 20, 16))
    world.alpha_composite(outlined(lay))


def anvil(world):
    shadow(world, [424, 188, 452, 198])
    lay, d = layer()
    stump(d, 437, 192, 7)
    d.rectangle([430, 178, 446, 182], fill=IRON[2])
    d.rectangle([432, 182, 444, 186], fill=IRON[0])
    d.polygon([(430, 178), (423, 179), (430, 182)], fill=IRON[2])
    d.line([431, 178, 445, 178], fill=IRON[3])
    barrel(d, 456, 196)
    d.ellipse([451, 180, 461, 185], fill=WATER[1])
    world.alpha_composite(outlined(lay))


def well(world):
    shadow(world, [574, 258, 622, 282], 80)
    lay, d = layer()
    cx, cy = 596, 262
    d.ellipse([cx - 17, cy - 8, cx + 17, cy + 14], fill=STONE[1])
    d.rectangle([cx - 17, cy + 2, cx + 17, cy + 6], fill=STONE[1])
    d.ellipse([cx - 17, cy - 12, cx + 17, cy + 8], fill=STONE[3])
    for a in range(0, 360, 30):
        r = math.radians(a)
        d.point((cx + round(15 * math.cos(r)), cy - 2 + round(9 * math.sin(r))), fill=STONE[1])
    d.ellipse([cx - 11, cy - 8, cx + 11, cy + 4], fill=WATER[0])
    d.ellipse([cx - 9, cy - 6, cx + 7, cy + 2], fill=WATER[1])
    d.line([cx - 5, cy - 4, cx - 1, cy - 4], fill=WATER[2])
    for px in (cx - 19, cx + 17):
        d.rectangle([px, cy - 30, px + 2, cy + 6], fill=WOOD[2])
    d.rectangle([cx - 21, cy - 32, cx + 21, cy - 29], fill=WOOD[3])
    d.line([cx, cy - 29, cx, cy - 14], fill=(206, 190, 150))
    d.rectangle([cx - 3, cy - 14, cx + 3, cy - 9], fill=WOOD[2])
    world.alpha_composite(outlined(lay))


def stonepile(world):
    shadow(world, [516, 286, 568, 306])
    lay, d = layer()
    d.rectangle([518, 288, 564, 300], fill=WOOD[2])
    for x in range(518, 564, 8):
        d.line([x, 288, x, 300], fill=WOOD[1])
    rnd = random.Random(9)
    for _ in range(14):
        x, y = rnd.randrange(522, 558), rnd.randrange(274, 292)
        r = rnd.randrange(4, 7)
        d.ellipse([x - r, y - r + 1, x + r, y + r], fill=STONE[0], outline=OUT)
        d.ellipse([x - r + 1, y - r + 1, x + r - 2, y + r - 3], fill=STONE[1])
        d.ellipse([x - r + 2, y - r + 1, x + 1, y - 1], fill=STONE[2])
    world.alpha_composite(outlined(lay))


def workbench(world):
    shadow(world, [466, 252, 516, 270])
    lay, d = layer()
    d.rectangle([468, 244, 512, 252], fill=WOOD[3])
    d.rectangle([468, 252, 512, 256], fill=WOOD[1])
    for lx in (470, 508):
        d.rectangle([lx, 256, lx + 3, 266], fill=WOOD[1])
    d.rectangle([476, 242, 488, 245], fill=IRON[2])        # saw
    d.rectangle([496, 240, 500, 246], fill=IRON[1])        # tongs
    world.alpha_composite(outlined(lay))


def field(world):
    lay, d = layer()
    d.rectangle([16, 248, 126, 318], fill=DIRT[1])
    for row, y in enumerate(range(252, 316, 9)):
        d.rectangle([20, y, 122, y + 5], fill=DIRT[0])
        d.line([20, y, 122, y], fill=DIRT[2])
        for x in range(24, 120, 9):
            if row < 3 or x > 70:
                d.ellipse([x - 3, y - 3, x + 3, y + 2], fill=LEAF[2])
                d.ellipse([x - 2, y - 2, x + 1, y], fill=LEAF[3])
            else:
                d.point((x, y - 1), fill=LEAF[3])
                d.point((x + 1, y - 2), fill=LEAF[2])
    for x in range(14, 130, 12):
        for y in (244, 318):
            d.rectangle([x, y - 6, x + 2, y + 1], fill=WOOD[2])
    for y in (244, 318):
        d.line([14, y - 4, 128, y - 4], fill=WOOD[3], width=2)
    world.alpha_composite(outlined(lay))


def tree_parts(cx, cy, r, seed):
    """Return (trunk layer, canopy layer) for a round deciduous tree."""
    rnd = random.Random(seed)
    tr, td = layer()
    td.rectangle([cx - 4, cy + r - 10, cx + 4, cy + r + 10], fill=WOOD[1])
    td.rectangle([cx - 4, cy + r - 10, cx - 2, cy + r + 10], fill=WOOD[2])
    td.polygon([(cx - 8, cy + r + 10), (cx, cy + r + 4), (cx + 8, cy + r + 10)], fill=WOOD[1])
    cl, cd = layer()
    blobs = [(cx + rnd.randint(-r // 2, r // 2), cy + rnd.randint(-r // 2, r // 3), rnd.randint(r // 2, r * 2 // 3))
             for _ in range(9)]
    for bx, by, br in blobs:
        cd.ellipse([bx - br, by - br, bx + br, by + br], fill=LEAF[1])
    for bx, by, br in blobs:
        cd.ellipse([bx - br + 2, by - br + 1, bx + br - 4, by + br - 5], fill=LEAF[2])
    for bx, by, br in blobs:
        cd.ellipse([bx - br // 2 - 2, by - br // 2 - 2, bx, by - 1], fill=LEAF[3])
    for _ in range(r * 6):
        x, y = cx + rnd.randint(-r, r), cy + rnd.randint(-r, r)
        if 0 <= x < WW and 0 <= y < WH and cl.getpixel((x, y))[3]:
            cd.point((x, y), fill=rnd.choice([LEAF[0], LEAF[1], LEAF[3]]))
    return outlined(tr), outlined(cl)


def bush(d, x, y, rnd):
    for _ in range(5):
        bx, by, br = x + rnd.randint(-6, 6), y + rnd.randint(-4, 2), rnd.randint(4, 7)
        d.ellipse([bx - br, by - br, bx + br, by + br], fill=LEAF[1])
        d.ellipse([bx - br + 1, by - br, bx + br - 3, by + br - 4], fill=LEAF[2])
        d.point((bx - 2, by - br + 2), fill=LEAF[3])


def build_world():
    world = ground()
    field(world)
    wall_h(world, 186, 252, 112)
    wall_h(world, 372, 462, 112)
    wall_v(world, 180, 112, 196)
    wall_v(world, 180, 238, 312)
    house(world)
    lay, d = layer()
    barrel(d, 244, 190)
    barrel(d, 254, 196)
    crate(d, 372, 198)
    crate(d, 380, 190)
    rnd = random.Random(3)
    for bx, by in [(112, 196), (528, 112), (196, 140), (622, 220), (40, 220), (420, 116)]:
        bush(d, bx, by, rnd)
    # signpost
    d.rectangle([126, 176, 128, 200], fill=WOOD[1])
    d.polygon([(114, 178), (134, 178), (138, 182), (134, 186), (114, 186)], fill=WOOD[3])
    world.alpha_composite(outlined(lay))
    furnace(world)
    anvil(world)
    woodpile(world)
    lay, d = layer()
    stump(d, 296, 274)
    for lx, ly in [(312, 286), (318, 290), (308, 292)]:
        d.rectangle([lx - 4, ly - 3, lx + 4, ly + 1], fill=WOOD[3])
        d.rectangle([lx - 4, ly - 3, lx - 2, ly + 1], fill=WOOD[1])
    world.alpha_composite(outlined(lay))
    workbench(world)
    stonepile(world)
    well(world)
    wall_h(world, 186, 292, 312)
    wall_h(world, 330, 432, 312)

    canopy = Image.new("RGBA", (WW, WH), (0, 0, 0, 0))
    trunks = []
    for cx, cy, r, seed in [(392, 256, 26, 1), (60, 70, 24, 2), (214, 52, 20, 3),
                            (596, 60, 26, 4), (40, 150, 18, 5), (620, 318, 22, 6)]:
        shadow(world, [cx - r + 6, cy + r - 2, cx + r + 10, cy + r + 14], 80)
        t, c = tree_parts(cx, cy, r, seed)
        trunks.append((cy + r + 10, t))
        canopy.alpha_composite(c)
    return world, canopy, trunks


# ------------------------------------------------------------------ characters
FARMER = dict(hair=(110, 70, 40), tunic=(150, 104, 62), pants=(84, 70, 56), hat=True)
WOODCUTTER = dict(hair=(70, 44, 30), tunic=(66, 108, 62), pants=(110, 84, 56), hood=(54, 86, 52))
SMITH = dict(hair=(48, 34, 30), tunic=(122, 100, 88), pants=(70, 60, 58), apron=(96, 62, 40), beard=True)
MAIDEN = dict(hair=(176, 92, 48), tunic=(156, 64, 64), pants=(156, 64, 64), dress=True,
              kerchief=(236, 228, 208), apron=(228, 218, 196))
CHILD = dict(hair=(232, 196, 104), tunic=(76, 108, 168), pants=(98, 78, 58), kid=True)

CW, CH, OX, OY = 72, 64, 36, 54


def person(look, facing, arm, tool=None, walk=None):
    img, d = layer(CW, CH)
    k = 0.8 if look.get("kid") else 1.0
    fy = OY
    lh, bh, hh, hw = round(6 * k), round(9 * k), round(12 * k), round(12 * k)
    btop, htop = fy - lh - bh, fy - lh - bh - hh
    t, tdk = look["tunic"], tuple(max(0, c - 34) for c in look["tunic"])
    a = math.sin(walk * 2 * math.pi) if walk is not None else 0
    lo = (round(a * 1.6), round(-a * 1.6))
    # back arm
    d.rectangle([OX - 7, btop + 1, OX - 5, btop + bh - 3], fill=tdk)
    if look.get("dress"):
        for i, lx in enumerate((OX - 3, OX + 1)):
            d.rectangle([lx + lo[i], fy - 2, lx + lo[i] + 2, fy], fill=OUT)
        d.polygon([(OX - 5, btop), (OX + 4, btop), (OX + 7, fy - 2), (OX - 8, fy - 2)], fill=t)
        d.polygon([(OX + 1, btop), (OX + 4, btop), (OX + 7, fy - 2), (OX + 2, fy - 2)], fill=tdk)
        d.rectangle([OX - 2, btop + 4, OX + 3, fy - 4], fill=look["apron"])
    else:
        for i, lx in enumerate((OX - 4, OX + 1)):
            lift = 1 if (walk is not None and (a > 0) == (i == 0)) else 0
            d.rectangle([lx + lo[i], fy - lh, lx + lo[i] + 2, fy - lift], fill=look["pants"])
            d.rectangle([lx + lo[i], fy - 1 - lift, lx + lo[i] + 3, fy - lift], fill=WOOD[0])
        d.rectangle([OX - 5, btop, OX + 4, fy - lh], fill=t)
        d.rectangle([OX + 2, btop, OX + 4, fy - lh], fill=tdk)
        d.line([OX - 5, fy - lh - 2, OX + 4, fy - lh - 2], fill=WOOD[1])
        d.point((OX, fy - lh - 2), fill=(220, 190, 90))
        if look.get("apron"):
            d.rectangle([OX - 3, btop + 2, OX + 3, fy - lh + 1], fill=look["apron"])
    # head
    d.rectangle([OX - hw // 2, htop, OX + hw // 2 - 1, btop], fill=SKIN[0])
    d.rectangle([OX + hw // 2 - 3, htop + 2, OX + hw // 2 - 1, btop], fill=SKIN[1])
    for px, py in [(OX - hw // 2, htop), (OX + hw // 2 - 1, htop)]:
        d.point((px, py), fill=(0, 0, 0, 0))
    d.rectangle([OX - hw // 2, htop, OX + hw // 2 - 1, htop + 3], fill=look["hair"])
    d.rectangle([OX - hw // 2, htop, OX - hw // 2 + 2, htop + hh - 4], fill=look["hair"])
    if look.get("dress"):
        d.rectangle([OX - hw // 2 - 1, htop + 2, OX - hw // 2 + 1, btop + 6], fill=look["hair"])
    ey = htop + hh // 2 + 1
    d.rectangle([OX, ey, OX, ey + 1], fill=OUT)
    d.rectangle([OX + 3, ey, OX + 3, ey + 1], fill=OUT)
    d.point((OX + 4, ey + 3), fill=(214, 120, 110))
    if look.get("beard"):
        d.rectangle([OX - 2, ey + 2, OX + 5, btop + 2], fill=look["hair"])
        d.line([OX, ey + 3, OX + 3, ey + 3], fill=SKIN[1])
    if look.get("hat"):
        d.ellipse([OX - 10, htop - 3, OX + 9, htop + 3], fill=(220, 186, 96))
        d.rectangle([OX - 5, htop - 7, OX + 4, htop], fill=(206, 170, 82))
        d.line([OX - 5, htop - 1, OX + 4, htop - 1], fill=(160, 60, 50))
    if look.get("hood"):
        c = look["hood"]
        d.rectangle([OX - hw // 2 - 1, htop - 2, OX + hw // 2, htop + 2], fill=c)
        d.rectangle([OX - hw // 2 - 1, htop - 2, OX - hw // 2 + 2, btop + 1], fill=c)
        d.polygon([(OX - hw // 2 - 1, htop - 2), (OX - hw // 2 - 5, htop + 4), (OX - hw // 2, htop + 4)], fill=c)
    if look.get("kerchief"):
        c = look["kerchief"]
        d.rectangle([OX - hw // 2, htop - 1, OX + hw // 2 - 1, htop + 2], fill=c)
        d.point((OX - hw // 2 - 1, htop + 3), fill=c)
    # front arm + tool
    sx, sy = OX + 2, btop + 2
    r = math.radians(arm)
    ux, uy = math.cos(r), math.sin(r)
    al = 6 * k
    hx, hy = sx + ux * al, sy + uy * al
    if tool == "hoe":
        ex, ey2 = hx + ux * 14, hy + uy * 14
        d.line([hx - ux * 3, hy - uy * 3, ex, ey2], fill=WOOD[3], width=2)
        d.line([ex, ey2, ex - uy * 5, ey2 + ux * 5], fill=IRON[2], width=3)
    elif tool == "axe":
        ex, ey2 = hx + ux * 10, hy + uy * 10
        d.line([hx - ux * 2, hy - uy * 2, ex, ey2], fill=WOOD[3], width=2)
        px, py = -uy, ux
        d.polygon([(ex - px * 2, ey2 - py * 2), (ex + px * 3 + ux * 2, ey2 + py * 3 + uy * 2),
                   (ex + px * 3 - ux * 3, ey2 + py * 3 - uy * 3)], fill=IRON[2])
        d.line([ex + px * 3 + ux * 2, ey2 + py * 3 + uy * 2, ex + px * 3 - ux * 3, ey2 + py * 3 - uy * 3],
               fill=IRON[3])
    elif tool == "hammer":
        ex, ey2 = hx + ux * 8, hy + uy * 8
        d.line([hx, hy, ex, ey2], fill=WOOD[3], width=2)
        px, py = -uy, ux
        d.line([ex - px * 3, ey2 - py * 3, ex + px * 3, ey2 + py * 3], fill=IRON[1], width=4)
    elif tool == "bucket":
        d.rectangle([hx - 4, hy + 2, hx + 4, hy + 10], fill=WOOD[2])
        d.rectangle([hx + 1, hy + 2, hx + 4, hy + 10], fill=WOOD[1])
        d.line([hx - 4, hy + 4, hx + 4, hy + 4], fill=IRON[1])
        d.line([hx - 4, hy + 8, hx + 4, hy + 8], fill=IRON[1])
        d.line([hx - 3, hy + 2, hx + 3, hy + 2], fill=WATER[2])
        d.arc([hx - 4, hy - 1, hx + 4, hy + 5], 180, 360, fill=IRON[0])
    d.line([sx, sy, hx, hy], fill=t, width=3)
    d.rectangle([round(hx) - 1, round(hy) - 1, round(hx) + 1, round(hy) + 1], fill=SKIN[0])
    if facing < 0:
        img = ImageOps.mirror(img)
    return outlined(img)


def chicken(t, facing, peck=False):
    img, d = layer(16, 16)
    bob = int(t * 10) % 2
    p = 2 if peck and int(t * 3) % 2 else 0
    d.ellipse([3, 6 - bob, 11, 12 - bob], fill=(244, 240, 228))
    d.ellipse([3, 9 - bob, 9, 12 - bob], fill=(214, 206, 190))
    d.rectangle([9, 4 - bob + p, 12, 8 - bob + p], fill=(244, 240, 228))
    d.rectangle([10, 3 - bob + p, 11, 3 - bob + p], fill=(220, 50, 50))
    d.point((13, 6 - bob + p), fill=(250, 170, 40))
    d.point((11, 5 - bob + p), fill=OUT)
    d.rectangle([2, 5 - bob, 4, 7 - bob], fill=(230, 226, 214))
    leg = int(t * 12) % 2
    d.line([6 + leg, 12, 6 + leg, 14], fill=(250, 170, 40))
    d.line([8 - leg, 12, 8 - leg, 14], fill=(250, 170, 40))
    if facing < 0:
        img = ImageOps.mirror(img)
    return outlined(img)


def swing(p, rise, up, down):
    if p < rise:
        return down + (up - down) * ease(p / rise)
    return up + (down - up) * min(1, (p - rise) / 0.15)


# ------------------------------------------------------------------ frame
def puff(d, x, y, r, a):
    d.ellipse([x - r, y - r, x + r, y + r], fill=(150, 146, 140, a))
    d.ellipse([x - r + 1, y - r, x + r - 1, y + r - 2], fill=(214, 210, 204, a))
    d.ellipse([x - r + 2, y - r + 1, x, y - 1], fill=(240, 238, 232, a))


def frame(world, canopy, trunks, i, font):
    t = i / FPS
    img = world.copy()
    fx, fd = layer()

    # forge fire, glow and smoke
    for k in range(12):
        x = 482 + (k * 5 + int(t * 18)) % 17
        h = 3 + (k * 7 + int(t * 22)) % 6
        fd.line([x, 173, x, 173 - h], fill=FIRE[(k + int(t * 12)) % 3])
    glow, gd = layer()
    gl = 60 + round(20 * math.sin(t * 9))
    gd.ellipse([466, 168, 514, 192], fill=(255, 150, 50, gl))
    img.alpha_composite(glow)
    for n, (cx, cy) in enumerate([(344, 20), (490, 106)]):
        for k in range(8):
            age = (t * 0.45 + k / 8 + n * 0.3) % 1
            sx = cx + round(math.sin(age * 6 + k) * 2 + age * 18)
            sy = cy - round(age * 44)
            puff(fd, sx, sy, 2 + round(age * 4), round(230 * (1 - age ** 2)))

    sprites = []

    # 1. farmer hoeing the cabbage field
    p = (t / 1.3) % 1
    sprites.append((300, 80, 300, person(FARMER, 1, swing(p, 0.6, -75, 48), "hoe")))
    if 0.68 < p < 0.98:
        q = (p - 0.68) / 0.3
        for k, (vx, vy) in enumerate([(-5, -7), (4, -8), (8, -4), (-2, -9)]):
            fd.point((98 + round(vx * q * 1.6), 304 + round(vy * q * 1.6 + 14 * q * q)), fill=DIRT[0])

    # 2. woodcutter at the chopping block
    p = (t / 1.1 + 0.3) % 1
    sprites.append((274, 283, 274, person(WOODCUTTER, 1, swing(p, 0.62, -130, 38), "axe")))
    if 0.72 < p < 0.98:
        q = (p - 0.72) / 0.26
        for k, (vx, vy) in enumerate([(-6, -7), (6, -8), (9, -3), (-3, -9), (3, -10)]):
            fd.rectangle([298 + round(vx * q * 2), 266 + round(vy * q * 2 + 18 * q * q),
                          299 + round(vx * q * 2), 266 + round(vy * q * 2 + 18 * q * q)], fill=WOOD[3])

    # 3. blacksmith hammering at the anvil
    p = (t / 0.7) % 1
    sprites.append((188, 423, 188, person(SMITH, 1, swing(p, 0.6, -105, 22), "hammer")))
    if 0.72 < p < 1:
        q = (p - 0.72) / 0.28
        rr = random.Random(int(t / 0.7))
        for k in range(9):
            ang = rr.uniform(-3.0, -0.2)
            dist = rr.uniform(5, 14) * q
            fd.point((438 + round(math.cos(ang) * dist), 177 + round(math.sin(ang) * dist + 8 * q * q)),
                     fill=FIRE[k % 2])

    # 4. maiden carrying water along the road toward the well
    mx = round(220 + 345 * (t / DUR))
    sprites.append((222, mx, 222, person(MAIDEN, 1, 82, "bucket", walk=t * 1.8)))

    # 5. child chasing a chicken around the big tree
    th = t * 1.3
    kx, ky = 392 + 38 * math.cos(th), 290 + 12 * math.sin(th)
    cx, cy = 392 + 38 * math.cos(th + 0.75), 290 + 12 * math.sin(th + 0.75)
    kf = -1 if math.sin(th) > 0 else 1
    cf = -1 if math.sin(th + 0.75) > 0 else 1
    sprites.append((ky, round(kx), round(ky), person(CHILD, kf, -30 + 60 * math.sin(t * 14), walk=t * 3.5)))
    sprites.append((cy, round(cx), round(cy), ("chicken", chicken(t, cf))))
    sprites.append((248, 540, 248, ("chicken", chicken(t, -1, peck=True))))
    for base, trunk in trunks:
        sprites.append((base, None, None, trunk))

    for _, x, y, spr in sorted(sprites, key=lambda s: s[0]):
        if x is None:
            img.alpha_composite(spr)
        elif isinstance(spr, tuple):
            shadow(img, [x - 6, y - 2, x + 6, y + 2], 70)
            img.alpha_composite(spr[1], (x - 8, y - 14))
        else:
            shadow(img, [x - 8, y - 3, x + 8, y + 2], 80)
            img.alpha_composite(spr, (x - OX, y - OY))
    img.alpha_composite(fx)
    img.alpha_composite(canopy)

    # butterflies
    bd = ImageDraw.Draw(img)
    for n, (bx0, by0) in enumerate([(240, 150), (520, 200), (90, 230)]):
        bx = bx0 + 30 * math.sin(t * 0.7 + n * 2) + 12 * math.sin(t * 2.1 + n)
        by = by0 + 14 * math.sin(t * 1.1 + n) + 4 * math.sin(t * 5 + n)
        wing = int(t * 10 + n) % 2
        col = [(250, 244, 220), (250, 210, 90), (170, 200, 250)][n]
        bd.point((round(bx) - 1, round(by) - wing), fill=col)
        bd.point((round(bx) + 1, round(by) - wing), fill=col)
        bd.point((round(bx), round(by)), fill=OUT)

    # slow camera pan across the village
    pp = ease(t / DUR)
    cam_x, cam_y = round(160 * pp), round(30 + 30 * pp)
    view = img.crop((cam_x, cam_y, cam_x + VW, cam_y + VH)).convert("RGB")
    if t < 4.4:
        s = ease(t / 0.6) if t < 3.8 else 1 - ease((t - 3.8) / 0.6)
        banner(view, font, "Village Life", round(-30 + 38 * s), "five peasants at work")
    if t > 8.4:
        banner(view, font, "Anno Domini 1347", round(-30 + 38 * ease((t - 8.4) / 0.6)))
    return view.resize((VW * SCALE, VH * SCALE), Image.NEAREST)


def banner(img, font, text, y, sub=None):
    small = Image.new("RGBA", (120, 12), (0, 0, 0, 0))
    ImageDraw.Draw(small).text((0, 0), text, font=font, fill=(236, 228, 210, 255))
    tw = round(ImageDraw.Draw(small).textlength(text, font=font)) * 2
    big = small.resize((240, 24), Image.NEAREST)
    w = tw + 40
    x = (VW - w) // 2
    d = ImageDraw.Draw(img)
    d.rectangle([x, y, x + w, y + 26], fill=OUT)
    d.rectangle([x + 1, y + 1, x + w - 1, y + 25], fill=(64, 70, 86))
    d.line([x + 2, y + 2, x + w - 2, y + 2], fill=(132, 140, 156))
    d.line([x + 2, y + 24, x + w - 2, y + 24], fill=(38, 42, 54))
    for ex in (x - 6, x + w - 2):
        d.polygon([(ex, y + 4), (ex + 8, y + 2), (ex + 8, y + 24), (ex, y + 22)], fill=(150, 116, 60), outline=OUT)
        d.line([ex + 2, y + 6, ex + 2, y + 20], fill=(214, 180, 100))
    sh = Image.new("RGBA", big.size, OUT + (255,))
    sh.putalpha(big.getchannel("A"))
    img.paste(sh, (x + 21, y + 3), sh)
    img.paste(big, (x + 20, y + 2), big)
    if sub:
        sw = d.textlength(sub, font=font)
        sx = round((VW - sw) / 2)
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            d.text((sx + ox, y + 30 + oy), sub, font=font, fill=OUT)
        d.text((sx, y + 30), sub, font=font, fill=(240, 226, 180))


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    font = ImageFont.load_default_imagefont()
    world, canopy, trunks = build_world()
    for i in range(N):
        frame(world, canopy, trunks, i, font).save(os.path.join(out, f"f{i:04d}.png"))


if __name__ == "__main__":
    main()
