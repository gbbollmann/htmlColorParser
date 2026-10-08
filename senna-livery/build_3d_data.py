"""Builds the data the 3D viewer needs from the 2D renders:
  3d/car-outline.json   outer polygons of the lower body and the greenhouse (image px, y down)
  3d/body-texture.jpg   livery render with edge colours dilated outward + dark patches for wells/underside
  3d/wheel.png          circular crop of the tyre/rim photo
Pure numpy + PIL, no OpenCV."""
import json, numpy as np
from PIL import Image, ImageFilter

BASE = 'assets/car-base.png'
LIVERY = 'carta-senna-livery-transparent.png'
W, H = 2828, 808
WHEELS = [(555, 578), (2260, 578)]
TIRE_R, WELL_R = 230, 244
BELT_Y, GH_X0, GH_X1 = 252, 950, 2250

alpha = np.array(Image.open(BASE).convert('RGBA'))[:, :, 3]
sil = alpha > 128
yy, xx = np.mgrid[0:H, 0:W]
wells = np.zeros_like(sil)
for cx, cy in WHEELS:
    wells |= (xx - cx) ** 2 + (yy - cy) ** 2 <= WELL_R ** 2
green = sil & (yy < BELT_Y) & (xx >= GH_X0) & (xx <= GH_X1)
lower = sil & ~green & ~wells

def trace(mask, seed):
    """Moore-neighbour outer boundary trace, 8-connected, starting at the topmost pixel of column seed."""
    ys = np.where(mask[:, seed])[0]
    sy, sx = int(ys.min()), seed
    pad = np.zeros((H + 2, W + 2), bool); pad[1:-1, 1:-1] = mask
    sy += 1; sx += 1
    nbr = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]  # clockwise from N
    pts = [(sx, sy)]
    cur = (sx, sy); back = 6  # we "came from" the west... start scanning from NW
    start_dir = None
    while True:
        found = False
        for k in range(8):
            d = (back + 1 + k) % 8
            ny, nx = cur[1] + nbr[d][0], cur[0] + nbr[d][1]
            if pad[ny, nx]:
                if cur == (sx, sy) and start_dir is None: start_dir = d
                elif cur == (sx, sy) and d == start_dir and len(pts) > 2:
                    return [(x - 1, y - 1) for x, y in pts]
                cur = (nx, ny); pts.append(cur); back = (d + 4) % 8; found = True
                break
        if not found: return [(x - 1, y - 1) for x, y in pts]
        if len(pts) > 200000: raise RuntimeError('trace runaway')

def rdp(pts, eps):
    pts = np.array(pts, float)
    def rec(i, j):
        if j <= i + 1: return [i]
        a, b = pts[i], pts[j]
        ab = b - a; n = np.hypot(*ab)
        rel = pts[i + 1:j] - a
        d = np.abs(ab[0] * rel[:, 1] - ab[1] * rel[:, 0]) / n if n else np.hypot(rel[:, 0], rel[:, 1])
        k = int(np.argmax(d))
        if d[k] > eps: return rec(i, i + 1 + k) + rec(i + 1 + k, j)
        return [i]
    idx = rec(0, len(pts) - 1) + [len(pts) - 1]
    return pts[idx].round(1).tolist()

out = {}
for name, mask, seed in [('lower', lower, 600), ('greenhouse', green, 1400)]:
    raw = trace(mask, seed)
    poly = rdp(raw, 1.8)
    print(name, 'raw', len(raw), 'simplified', len(poly))
    out[name] = poly
out['wheels'] = [{'x': cx, 'y': cy, 'r': TIRE_R} for cx, cy in WHEELS]
out['wellR'] = WELL_R; out['belt'] = BELT_Y; out['size'] = [W, H]
json.dump(out, open('3d/car-outline.json', 'w'))

# Texture: dilate opaque colours outward so edge samples never hit transparent pixels.
def dilated(path):
    im = Image.open(path).convert('RGBA')
    rgba = np.array(im).astype(np.float32) / 255
    rgb, a = rgba[:, :, :3], rgba[:, :, 3:4]
    cur_rgb, cur_a = rgb * a, a.copy()
    for _ in range(14):
        br = np.array(Image.fromarray((np.dstack([cur_rgb, cur_a]) * 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(2))).astype(np.float32) / 255
        nb_rgb, nb_a = br[:, :, :3], br[:, :, 3:4]
        fill = (cur_a < 0.02) & (nb_a > 0.001)
        cur_rgb = np.where(fill, nb_rgb / np.maximum(nb_a, 1e-4), cur_rgb)
        cur_a = np.where(fill, 1.0, cur_a)
    tex = np.where(cur_a > 0.02, cur_rgb / np.maximum(cur_a, 1e-4), 0.08)
    return (np.clip(tex, 0, 1) * 255).astype(np.uint8)
# Top half: the livery as seen from the right. Bottom half: same layout with lettering mirrored
# in place, which is what the left side of the car must show. Both are sampled by x position.
top = dilated(LIVERY); bottom = dilated(LIVERY.replace('.png', '-mirror.png'))
tex = np.vstack([top, bottom])
tex[0:24, 0:24] = (26, 26, 26)  # dark patch sampled by wheel wells and the underside
Image.fromarray(tex).save('3d/body-texture.jpg', quality=92)
# Walls (hood, roof, nose, tail) sample along the outline; a softened copy hides pixel-level edge noise.
walls = np.array(Image.fromarray(tex).filter(ImageFilter.GaussianBlur(7)))
walls[0:24, 0:24] = (26, 26, 26)
Image.fromarray(walls).save('3d/body-texture-walls.jpg', quality=90)

# Wheel face: circular crop of the front tyre.
cx, cy = WHEELS[0]
crop = Image.open(BASE).convert('RGBA').crop((cx - TIRE_R, cy - TIRE_R, cx + TIRE_R, cy + TIRE_R))
n = crop.size[0]; g = np.mgrid[0:n, 0:n]; r2 = (g[0] - n / 2 + .5) ** 2 + (g[1] - n / 2 + .5) ** 2
m = (np.clip((n / 2 - 1 - np.sqrt(r2)) + 1, 0, 1) * 255).astype(np.uint8)
crop.putalpha(Image.fromarray(m)); crop.save('3d/wheel.png')
print('done')
