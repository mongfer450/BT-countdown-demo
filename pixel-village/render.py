"""Render a pixel-art medieval village scene: 5 peasants going about their day.

Draws each frame at 320x180, then scales 4x (nearest neighbour) to 1280x720.
Usage: python3 render.py <frames_dir>
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

W, H, SCALE = 320, 180, 4
FPS, DUR = 24, 10
N = FPS * DUR

SKY = [(92, 156, 228), (116, 176, 238), (146, 198, 246), (182, 220, 250)]
SUN = (255, 236, 130)
HILL_FAR, HILL_NEAR = (98, 146, 110), (76, 130, 80)
GRASS, GRASS_D, GRASS_L = (100, 170, 74), (78, 144, 60), (132, 194, 92)
DIRT, DIRT_D = (178, 136, 88), (146, 106, 66)
SOIL, SOIL_D, CROP = (120, 82, 52), (96, 64, 40), (90, 178, 70)
PLASTER, TIMBER = (234, 216, 174), (102, 64, 38)
THATCH, THATCH_D = (216, 172, 74), (176, 134, 52)
STONE, STONE_D = (152, 152, 164), (112, 112, 128)
WOOD, WOOD_D = (140, 92, 52), (102, 66, 38)
IRON, IRON_D = (170, 176, 186), (70, 72, 82)
SKIN, EYE = (242, 194, 150), (40, 30, 30)
WHITE, BLACK = (250, 250, 240), (24, 20, 24)
FIRE = [(255, 220, 90), (255, 160, 50), (230, 90, 40)]


def ease(p):
    return p * p * (3 - 2 * p)


# ---------------------------------------------------------------- background
def tree(d, x, y):
    d.rectangle([x - 1, y - 10, x + 1, y], fill=WOOD_D)
    for cx, cy, r, col in [(x, y - 16, 7, (58, 118, 56)), (x - 5, y - 12, 5, (58, 118, 56)),
                           (x + 5, y - 12, 5, (58, 118, 56)), (x - 1, y - 18, 4, (84, 146, 68)),
                           (x + 3, y - 14, 3, (84, 146, 68))]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)


def house(d, x, base, w, hw, rh, chimney_dx):
    top = base - hw
    d.rectangle([x + chimney_dx, top - rh + 2, x + chimney_dx + 4, top - 2], fill=STONE_D)
    d.rectangle([x, top, x + w, base], fill=PLASTER)
    d.rectangle([x, top, x + w, base], outline=TIMBER)
    d.line([x, top + hw // 2, x + w, top + hw // 2], fill=TIMBER)
    for bx in range(x + 8, x + w - 4, 10):
        d.line([bx, top, bx, base], fill=TIMBER)
        d.line([bx - 8, top + hw // 2, bx, top], fill=TIMBER)
    d.polygon([(x - 4, top + 1), (x + w + 4, top + 1), (x + w // 2, top - rh)], fill=THATCH)
    for i in range(2, rh, 3):
        half = (w // 2 + 4) * i // rh
        d.line([x + w // 2 - half, top - rh + i, x + w // 2 + half, top - rh + i], fill=THATCH_D)
    dx = x + w // 2 - 3
    d.rectangle([dx, base - 9, dx + 6, base], fill=WOOD_D)
    d.point((dx + 5, base - 4), fill=IRON)
    for wx in (x + 4, x + w - 10):
        d.rectangle([wx, top + 3, wx + 5, top + 7], fill=(70, 54, 44))
        d.line([wx + 2, top + 3, wx + 2, top + 7], fill=TIMBER)
    return (x + chimney_dx + 2, top - rh + 1)


def background():
    rnd = random.Random(7)
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        for x in range(W):
            b = min(len(SKY) - 1, (y + ((x + y) % 2) * 3) // 24)
            px[x, y] = SKY[b]
    d = ImageDraw.Draw(img)
    d.ellipse([34, 14, 50, 30], fill=SUN)
    d.ellipse([30, 10, 54, 34], outline=(255, 246, 190))

    for x in range(W):
        h = int(80 + 6 * math.sin(x / 23) + 4 * math.sin(x / 9 + 1))
        d.line([x, h, x, 110], fill=HILL_FAR)
    # castle on the far hill
    cs, cd = (168, 168, 182), (130, 130, 148)
    d.rectangle([242, 58, 278, 78], fill=cs)
    d.rectangle([254, 44, 266, 58], fill=cs)
    for tx in (238, 274):
        d.rectangle([tx, 50, tx + 8, 78], fill=cd)
        for cx in range(tx, tx + 9, 3):
            d.rectangle([cx, 48, cx + 1, 49], fill=cd)
    for cx in range(242, 279, 3):
        d.rectangle([cx, 56, cx + 1, 57], fill=cs)
    for cx in range(254, 267, 3):
        d.rectangle([cx, 42, cx + 1, 43], fill=cs)
    d.rectangle([258, 70, 262, 78], fill=(60, 50, 50))
    for wx, wy in [(241, 58), (277, 58), (259, 49), (248, 64), (270, 64)]:
        d.rectangle([wx, wy, wx + 1, wy + 2], fill=(60, 60, 80))
    d.line([260, 34, 260, 42], fill=WOOD_D)

    for x in range(W):
        h = int(94 + 5 * math.sin(x / 31 + 2) + 3 * math.sin(x / 13))
        d.line([x, h, x, 110], fill=HILL_NEAR)

    d.rectangle([0, 104, W, H], fill=GRASS)
    for _ in range(700):
        x, y = rnd.randrange(W), rnd.randrange(104, H)
        d.point((x, y), fill=rnd.choice([GRASS_D, GRASS_D, GRASS_L]))
    # dirt path
    for x in range(W):
        top = 136 + int(1.2 * math.sin(x / 7))
        d.line([x, top, x, 147 + int(1.2 * math.sin(x / 9 + 2))], fill=DIRT)
    for _ in range(140):
        d.point((rnd.randrange(W), rnd.randrange(138, 146)), fill=DIRT_D)
    # ploughed field
    d.rectangle([8, 152, 112, 176], fill=SOIL)
    for ry in range(154, 176, 4):
        d.line([10, ry, 110, ry], fill=SOIL_D)
        for cx in range(12, 110, 5):
            if cx < 70 or ry > 165:
                d.point((cx, ry - 1), fill=CROP)
                d.point((cx + 1, ry - 2), fill=CROP)
    d.rectangle([8, 152, 112, 176], outline=WOOD_D)

    tree(d, 96, 112)
    tree(d, 306, 114)
    tree(d, 6, 118)
    chimneys = [house(d, 18, 114, 44, 20, 16, 30), house(d, 116, 114, 36, 18, 14, 6)]

    # forge shed
    d.rectangle([222, 102, 294, 126], fill=STONE_D)
    for by in range(104, 126, 4):
        for bx in range(222 + (by % 8), 294, 8):
            d.line([bx, by, bx + 5, by], fill=STONE)
    d.polygon([(216, 104), (300, 104), (290, 92), (226, 92)], fill=WOOD)
    for rx in range(228, 290, 6):
        d.line([rx, 93, rx - 2, 103], fill=WOOD_D)
    for postx in (220, 296):
        d.rectangle([postx - 1, 104, postx + 1, 128], fill=WOOD_D)
    d.rectangle([228, 112, 244, 126], fill=STONE)          # hearth
    d.rectangle([232, 82, 238, 112], fill=STONE)           # forge chimney
    d.rectangle([258, 124, 260, 130], fill=WOOD_D)         # anvil stump
    d.rectangle([254, 120, 266, 123], fill=IRON_D)         # anvil
    d.rectangle([252, 120, 254, 121], fill=IRON_D)
    chimneys.append((235, 80))

    # woodpile and chopping block
    for i, (lx, ly) in enumerate([(176, 132), (182, 132), (179, 128)]):
        d.ellipse([lx - 3, ly - 3, lx + 3, ly + 3], fill=WOOD)
        d.ellipse([lx - 1, ly - 1, lx + 1, ly + 1], fill=(200, 160, 100))
    d.rectangle([203, 129, 209, 135], fill=WOOD)
    d.line([203, 129, 209, 129], fill=(200, 160, 100))
    return img, chimneys


# ---------------------------------------------------------------- sprites
def peasant(d, x, y, look, facing=1, walk=None, arm=80, tool=None, small=False):
    leg_h, body_h = (2, 4) if small else (3, 6)
    if walk is None:
        offs = (0, 0)
    else:
        a = math.sin(walk * 2 * math.pi)
        offs = (round(a * 1.4), round(-a * 1.4))
    btop = y - leg_h - body_h
    if look.get("dress"):
        for i, lx in enumerate((x - 2, x + 1)):
            d.point((lx + offs[i], y - 1), fill=BLACK)
        d.polygon([(x - 3, btop), (x + 2, btop), (x + 3, y - 2), (x - 4, y - 2)], fill=look["tunic"])
        d.line([x - 2, btop + 2, x + 1, btop + 2], fill=look.get("apron", look["tunic"]))
        if look.get("apron"):
            d.rectangle([x - 1 + facing, btop + 2, x + facing, y - 3], fill=look["apron"])
    else:
        for i, lx in enumerate((x - 2, x + 1)):
            d.rectangle([lx + offs[i], y - leg_h, lx + offs[i], y - 1], fill=look["legs"])
            d.point((lx + offs[i], y - 1), fill=BLACK)
        d.rectangle([x - 3, btop, x + 2, y - leg_h - 1], fill=look["tunic"])
        d.line([x - 3, btop + body_h - 2, x + 2, btop + body_h - 2], fill=look.get("belt", WOOD_D))
        if look.get("apron"):
            d.rectangle([x - 1 + facing, btop + 1, x + facing, y - leg_h], fill=look["apron"])

    htop = btop - 4
    d.rectangle([x - 2, htop, x + 1, btop - 1], fill=SKIN)
    d.line([x - 2, htop, x + 1, htop], fill=look["hair"])
    back = x - 2 if facing > 0 else x + 1
    d.line([back, htop, back, htop + 2], fill=look["hair"])
    if look.get("hood"):
        d.line([x - 3, htop - 1, x + 2, htop - 1], fill=look["hood"])
        d.line([x - 2, htop - 2, x + 1, htop - 2], fill=look["hood"])
        d.line([back - facing, htop - 1, back - facing, htop + 3], fill=look["hood"])
    if look.get("hat"):
        d.line([x - 4, htop - 1, x + 3, htop - 1], fill=look["hat"])
        d.line([x - 2, htop - 3, x + 1, htop - 2], fill=look["hat"])
        d.rectangle([x - 2, htop - 3, x + 1, htop - 2], fill=look["hat"])
    d.point((x if facing > 0 else x - 1, htop + 2), fill=EYE)

    sx, sy = (x if facing > 0 else x - 1), btop + 1
    rad = math.radians(arm)
    ln = 3 if small else 4
    hx, hy = sx + round(ln * math.cos(rad)) * facing, sy + round(ln * math.sin(rad))
    d.line([sx, sy, hx, hy], fill=look["tunic"])
    ux, uy = math.cos(rad) * facing, math.sin(rad)
    if tool == "hoe":
        ex, ey = hx + ux * 7, hy + uy * 7
        d.line([hx - ux * 4, hy - uy * 4, ex, ey], fill=WOOD)
        px_, py_ = -uy * facing, ux * facing
        d.line([ex, ey, ex + 3 * facing * abs(px_) * 0 + px_ * 0, ey + 3], fill=IRON)
    elif tool == "axe":
        ex, ey = hx + ux * 6, hy + uy * 6
        d.line([hx - ux, hy - uy, ex, ey], fill=WOOD)
        d.rectangle([round(ex) - 1, round(ey) - 1, round(ex) + 1, round(ey) + 1], fill=IRON)
        d.point((round(ex + ux * 2), round(ey + uy * 2)), fill=WHITE)
    elif tool == "hammer":
        ex, ey = hx + ux * 4, hy + uy * 4
        d.line([hx, hy, ex, ey], fill=WOOD)
        d.rectangle([round(ex) - 1, round(ey) - 1, round(ex) + 1, round(ey)], fill=IRON_D)
    elif tool == "bucket":
        d.rectangle([hx - 1, hy + 1, hx + 2, hy + 4], fill=WOOD)
        d.line([hx - 1, hy + 2, hx + 2, hy + 2], fill=IRON_D)
        d.line([hx, hy + 1, hx + 1, hy + 1], fill=(80, 140, 220))
    d.point((hx, hy), fill=SKIN)


def chicken(d, x, y, facing, t):
    bob = int((t * 12) % 2)
    d.rectangle([x - 2, y - 4 - bob, x + 1, y - 2 - bob], fill=WHITE)
    hx = x + 2 if facing > 0 else x - 3
    d.point((hx, y - 5 - bob), fill=WHITE)
    d.point((hx, y - 6 - bob), fill=(220, 50, 50))
    d.point((hx + facing, y - 5 - bob), fill=(250, 170, 40))
    d.point((x - 3 * facing if facing > 0 else x + 2, y - 4 - bob), fill=(220, 220, 210))
    leg = int(t * 12) % 2
    d.point((x - 1 + leg, y - 1), fill=(250, 170, 40))
    d.point((x - leg, y - 1), fill=(250, 170, 40))


def well(d):
    d.rectangle([166, 124, 182, 134], fill=STONE)
    for by in (126, 130):
        for bx in range(166 + (by % 4), 182, 5):
            d.line([bx, by, bx + 3, by], fill=STONE_D)
    d.line([166, 124, 182, 124], fill=STONE_D)
    for postx in (167, 181):
        d.line([postx, 110, postx, 124], fill=WOOD_D)
    d.polygon([(163, 112), (185, 112), (174, 104)], fill=THATCH)
    d.line([168, 113, 180, 113], fill=WOOD_D)
    d.line([174, 113, 174, 119], fill=(200, 190, 160))
    d.rectangle([173, 119, 175, 121], fill=WOOD)


# ---------------------------------------------------------------- scene
FARMER = dict(hair=(110, 70, 40), tunic=(150, 110, 70), legs=(90, 80, 60), hat=(214, 180, 90))
WOODCUTTER = dict(hair=(60, 40, 30), tunic=(70, 120, 70), legs=(110, 90, 60), hood=(60, 96, 60))
SMITH = dict(hair=(30, 25, 25), tunic=(110, 90, 80), legs=(70, 60, 60), apron=(90, 60, 40))
MAIDEN = dict(hair=(200, 120, 60), tunic=(160, 70, 70), dress=True, hood=(236, 230, 210), apron=(230, 222, 200))
CHILD = dict(hair=(230, 200, 110), tunic=(80, 110, 170), legs=(100, 80, 60))


def swing(p, rise, up, down):
    """Tool swing cycle: slow raise for `rise` of the cycle, fast strike after."""
    if p < rise:
        return down + (up - down) * ease(p / rise)
    s = min(1, (p - rise) / 0.15)
    return up + (down - up) * s


def frame(bg, chimneys, i, font):
    t = i / FPS
    img = bg.copy()
    d = ImageDraw.Draw(img)

    # drifting clouds and birds
    for cx0, cy, spd in [(40, 20, 4), (170, 34, 2.5), (290, 14, 3.2)]:
        cx = (cx0 + t * spd) % (W + 60) - 30
        for ox, oy, r in [(0, 0, 6), (7, -3, 7), (14, 0, 6), (7, 2, 5)]:
            d.ellipse([cx + ox - r, cy + oy - r, cx + ox + r, cy + oy + r // 2], fill=WHITE)
    for bx0, by in [(0, 40), (12, 46), (-10, 44)]:
        bx = (bx0 + t * 18) % (W + 40) - 20
        flap = 1 if int(t * 6 + bx0) % 2 else -1
        by2 = by + round(2 * math.sin(t * 2 + bx0))
        d.point((bx, by2), fill=BLACK)
        d.point((bx - 1, by2 + flap), fill=BLACK)
        d.point((bx + 1, by2 + flap), fill=BLACK)

    # castle flag
    for k in range(5):
        fy = 35 + round(math.sin(t * 6 - k * 0.9))
        d.line([261 + k, fy, 261 + k, fy + 3], fill=(210, 40, 50))

    # chimney smoke
    for n, (cx, cy) in enumerate(chimneys):
        for k in range(7):
            age = (t * 0.6 + k / 7 + n * 0.13) % 1
            sx = cx + round(math.sin(age * 5 + n + k) * 2 + age * 8)
            sy = cy - 2 - round(age * 26)
            r = 1 + round(age * 2)
            g = 170 + round(age * 60)
            d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(g, g, g + 6))

    # forge fire
    for k in range(10):
        fx = 230 + (k * 7 + int(t * 20)) % 13
        fh = 2 + (k * 13 + int(t * 24)) % 4
        d.line([fx, 113, fx, 113 - fh], fill=FIRE[(k + int(t * 10)) % 3])
    d.rectangle([228, 113, 244, 114], fill=FIRE[2])

    sprites = []
    # 1. farmer hoeing the field
    p = (t / 1.3) % 1
    sprites.append((168, lambda: peasant(d, 76, 168, FARMER, 1, None, swing(p, 0.6, -60, 70), "hoe")))
    if 0.7 < p < 0.95:
        for k in range(4):
            q = (p - 0.7) / 0.25
            d.point((86 + k * 2 - 3, 170 - round(q * (3 + k) * (1 - q) * 3)), fill=SOIL_D)

    # 2. woodcutter at the chopping block
    p = (t / 1.1 + 0.3) % 1
    sprites.append((134, lambda: peasant(d, 198, 135, WOODCUTTER, 1, None, swing(p, 0.62, -120, 40), "axe")))
    if 0.72 < p < 0.98:
        q = (p - 0.72) / 0.26
        for k, (vx, vy) in enumerate([(-4, -6), (5, -7), (7, -3), (-2, -8)]):
            d.point((206 + round(vx * q * 2), 128 + round(vy * q * 2 + 14 * q * q)), fill=(214, 176, 112))

    # 3. blacksmith at the anvil
    p = (t / 0.7) % 1
    sprites.append((130, lambda: peasant(d, 250, 130, SMITH, 1, None, swing(p, 0.6, -90, 15), "hammer")))
    if 0.72 < p < 1:
        q = (p - 0.72) / 0.28
        rr = random.Random(int(t / 0.7))
        for k in range(6):
            ang = rr.uniform(-2.8, -0.3)
            dist = rr.uniform(4, 10) * q
            d.point((257 + round(math.cos(ang) * dist), 119 + round(math.sin(ang) * dist + 6 * q * q)),
                    fill=FIRE[k % 2])

    # 4. maiden carrying water along the path
    cyc = (t / 8) % 1
    tri = cyc * 2 if cyc < 0.5 else 2 - cyc * 2
    mx = round(36 + 112 * ease(tri))
    mf = 1 if cyc < 0.5 else -1
    sprites.append((145, lambda: peasant(d, mx, 145, MAIDEN, mf, t * 2.2, 80, "bucket")))

    # 5. child chasing a chicken around the well
    th = t * 1.5
    kx, ky = round(174 + 26 * math.cos(th)), round(140 + 8 * math.sin(th))
    hx_, hy_ = round(174 + 26 * math.cos(th + 0.7)), round(140 + 8 * math.sin(th + 0.7))
    kf = -1 if math.sin(th) > 0 else 1
    hf = -1 if math.sin(th + 0.7) > 0 else 1
    sprites.append((ky, lambda: peasant(d, kx, ky, CHILD, kf, t * 4, -40 + 50 * math.sin(t * 16), None, small=True)))
    sprites.append((hy_, lambda: chicken(d, hx_, hy_, hf, t)))
    sprites.append((134.5, lambda: well(d)))

    for _, fn in sorted(sprites, key=lambda s: s[0]):
        fn()

    # title card, slides in then out
    if t < 4.2:
        slide = min(1, t / 0.6) if t < 3.6 else 1 - (t - 3.6) / 0.6
        title_overlay(img, font, round(-40 + 46 * ease(max(0, slide))))
    if t > 8.6:
        title_overlay(img, font, None, sub_only="~ Anno Domini 1347 ~")
    return img.resize((W * SCALE, H * SCALE), Image.NEAREST)


def title_overlay(img, font, y, sub_only=None):
    if sub_only:
        lay = Image.new("RGBA", (W, 16), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        tw = ld.textlength(sub_only, font=font)
        ld.text(((W - tw) // 2 + 1, 3), sub_only, font=font, fill=(40, 24, 10, 255))
        ld.text(((W - tw) // 2, 2), sub_only, font=font, fill=(255, 236, 160, 255))
        img.paste(lay, (0, 6), lay)
        return
    text = "VILLAGE LIFE"
    small = Image.new("RGBA", (80, 12), (0, 0, 0, 0))
    sd = ImageDraw.Draw(small)
    sd.text((0, 0), text, font=font, fill=(255, 236, 160, 255))
    big = small.resize((160, 24), Image.NEAREST)
    shadow = Image.new("RGBA", big.size, (60, 34, 14, 255))
    shadow.putalpha(big.getchannel("A"))
    bx = (W - 146) // 2
    plate = ImageDraw.Draw(img)
    plate.rectangle([bx - 8, y - 4, bx + 152, y + 32], fill=(92, 58, 32), outline=(52, 30, 16))
    plate.rectangle([bx - 6, y - 2, bx + 150, y + 30], outline=(200, 150, 80))
    img.paste(shadow, (bx + 2, y + 2), shadow)
    img.paste(big, (bx, y), big)
    sub = "five peasants at work"
    tw = plate.textlength(sub, font=font)
    plate.text(((W - tw) // 2, y + 20), sub, font=font, fill=(240, 220, 180))


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    font = ImageFont.load_default_imagefont()
    bg, chimneys = background()
    for i in range(N):
        frame(bg, chimneys, i, font).save(os.path.join(out, f"f{i:04d}.png"))


if __name__ == "__main__":
    main()
