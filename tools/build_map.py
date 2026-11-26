# build_map.py - 실제 부경대 대연캠퍼스 맵 만들기 (게임 밖에서 한 번만 돌리는 도구)
#
# 실제 캠퍼스 모양을 따르되, 건물·운동장 같은 오브젝트는 크기 그대로 두고
# 사이 간격만 STRETCH배로 넓힘 (잔디·길·광장은 같이 늘어나서 빈자리를 채움)
# 나무는 겹치지 않게 간격을 두고 솎아냄
#
# 재료 (tools/map_src/)
#   campus_data.py        : OpenStreetMap 건물 바닥 모양, 길, 잔디·숲, 나무, 명소
#   building_registry.json: 건축물대장(국토교통부 API) 건물별 지상 층수
#   satellite.jpg         : 위성사진 (지붕 색)
#   sprites_env.py        : 나무·소품·바닥 타일·창문 도트 그림
# 결과 (game/assets/images/): map.png, map_bld.png, map_sil.png, map_block.png, map_labels.json
#
# 실행: python tools/build_map.py
import json
import math
import os
import random
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "map_src")
OUT = os.path.join(HERE, "..", "game", "assets", "images")
sys.path.insert(0, SRC)
import campus_data as cd
import sprites_env as env

STRETCH = 1.35    # 오브젝트 사이 간격을 몇 배로 넓힐지
B = 2             # 그릴 때 1 m = 2 픽셀
ZOOM = 2          # 다 그린 뒤 2배 확대 -> 게임에서 1 m = 4 픽셀
CELL = 8          # 게임 충돌 칸 (확대 후 픽셀)
FLOOR_H = 5       # 한 층 벽 높이 (픽셀)
TREE_GAP = {"cherry": 11, "ginkgo": 11, "quince": 0, "green": 22, "pine": 20, "bush": 30}   # 나무 사이 최소 간격 (m)
PROP_GAP = 30     # 벤치·가로등 사이 최소 간격 (m)

pygame.display.init()
pygame.display.set_mode((1, 1))
W, H = int(cd.WORLD_W * STRETCH * B), int(cd.WORLD_H * STRETCH * B)
rng = random.Random(45)


# ------------------------------------------------------------------
# 좌표: 실제 위치(m) -> 넓힌 위치 -> 그림 픽셀
# ------------------------------------------------------------------
def T(x, y):
    """실제 위치(m) -> 넓힌 위치의 픽셀"""
    return (x * STRETCH * B, y * STRETCH * B)


def px(pts):
    """모양째 넓힘 (잔디, 길, 광장, 경계)"""
    return [T(x, y) for x, y in pts]


def px_fixed(pts):
    """크기는 그대로, 위치만 옮김 (건물, 운동장, 코트)"""
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    nx, ny = T(cx, cy)
    return [(nx + (x - cx) * B, ny + (y - cy) * B) for x, y in pts]


# ------------------------------------------------------------------
# 반듯하게 펴기
# ------------------------------------------------------------------
def simplify(pts, tol):
    """더글러스-포커: 거의 일직선인 중간 점들은 지움"""
    if len(pts) < 3:
        return list(pts)
    (ax, ay), (bx, by) = pts[0], pts[-1]
    L = math.hypot(bx - ax, by - ay) or 1
    far, idx = 0, 0
    for k in range(1, len(pts) - 1):
        d = abs((bx - ax) * (ay - pts[k][1]) - (ax - pts[k][0]) * (by - ay)) / L
        if d > far:
            far, idx = d, k
    if far < tol:
        return [pts[0], pts[-1]]
    return simplify(pts[:idx + 1], tol)[:-1] + simplify(pts[idx:], tol)


def square_up(pts, closed, ratio=0.2):
    """거의 가로/세로인 변은 딱 가로/세로로 (양 끝점을 평균 위치로 맞춤)"""
    pts = [list(p) for p in pts]
    n = len(pts)
    for _ in range(3):
        for i in range(n if closed else n - 1):
            a, b = pts[i], pts[(i + 1) % n]
            dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
            if dy <= dx * ratio:
                a[1] = b[1] = (a[1] + b[1]) / 2
            elif dx <= dy * ratio:
                a[0] = b[0] = (a[0] + b[0]) / 2
    return [tuple(p) for p in pts]


def neat_line(pts, tol=4):
    return square_up(simplify(pts, tol), False)


def neat_ring(pts, tol=2):
    if len(pts) < 5:
        return square_up(pts, True)
    far = max(range(len(pts)), key=lambda k: math.hypot(pts[k][0] - pts[0][0], pts[k][1] - pts[0][1]))
    ring = simplify(pts[:far + 1], tol)[:-1] + simplify(pts[far:] + [pts[0]], tol)[:-1]
    return square_up(ring, True) if len(ring) >= 3 else pts


def tint(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])


def mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def in_poly(x, y, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def polygon_area(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))) / 2


def thin(items, gap_of):
    """가까이 붙은 것들은 하나만 남김. items: (x, y, 종류)"""
    kept = []
    for x, y, kind in items:
        gap = gap_of(kind)
        if all(math.hypot(x - a, y - b) >= max(gap, g2) for a, b, g2 in kept):
            kept.append((x, y, gap))
    return [(x, y) for x, y, _ in kept], kept


def load_sprites():
    img = {}
    for name, rows in env.SPRITES.items():
        s = pygame.Surface((len(rows[0]), len(rows)), pygame.SRCALPHA)
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch != ".":
                    s.set_at((x, y), env.PAL[ch])
        img[name] = s
    return img


IMG = load_sprites()

ROUND_AREAS = ("track", "pitch")     # 원래 둥근 것은 그대로
cd.BOUNDARY = neat_ring(cd.BOUNDARY, 4)
for _b in cd.BUILDINGS:
    if len(_b["poly"]) >= 3:
        _b["poly"] = neat_ring(_b["poly"], 1.5)
for _a in cd.AREAS:
    if len(_a["poly"]) >= 3 and _a["kind"] not in ROUND_AREAS:
        _a["poly"] = neat_ring(_a["poly"], 3)


for _r in cd.ROADS:
    _r["pts"] = neat_line(_r["pts"], 4 if _r["kind"] in ("path", "steps") else 3)


def tiled(names):
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    r = random.Random(len(names[0]))
    for y in range(0, H, 16):
        for x in range(0, W, 16):
            s.blit(IMG[r.choice(names)], (x, y))
    return s


def paint(ground, draw_fn, names):
    """draw_fn이 흰색으로 그린 모양 안에만 타일 깔기"""
    mask = pygame.Surface((W, H), pygame.SRCALPHA)
    draw_fn(mask, (255, 255, 255, 255))
    tex = tiled(names)
    tex.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    ground.blit(tex, (0, 0))


def draw_line_wide(surf, color, pts, width):
    """둥근 끝의 굵은 꺾은선 (pts는 픽셀)"""
    r = max(1, width / 2)
    for a, b in zip(pts, pts[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 0.01:
            continue
        nx, ny = -dy / L * r, dx / L * r
        pygame.draw.polygon(surf, color, [(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny),
                                          (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)])
    for p in pts:
        pygame.draw.circle(surf, color, p, r)


# ------------------------------------------------------------------
# 1. 건축물대장 층수 + 위성사진 지붕 색
# ------------------------------------------------------------------
def load_registry():
    with open(os.path.join(SRC, "building_registry.json"), encoding="utf-8") as f:
        rows = json.load(f)["rows"]
    floors = {}
    for row in rows:
        floors[row[0].split("(")[0].replace(" ", "").replace("부경대학교", "")] = row[1]
    alias = {"수산과학관": "수산과학1관", "부산행복기숙사": "부산행복연합기숙사",
             "부경컨벤션홀": "컨벤션홀", "LMO격리사육동": "해양수산LMO격리사육동"}
    return floors, alias


SAT_EXTENT = (14371283.44, 14372410.96, 4181602.52, 4182568.97)   # 위성사진 범위 (웹 메르카토르 m)
GEO = {"lat0": 35.1338621, "lon0": 129.1055009, "ox": -444.6908, "oy": -395.3099, "theta": 4.863}
SAT = pygame.image.load(os.path.join(SRC, "satellite.jpg"))


def sat_color(wx, wy):
    """실제 위치(m)의 위성사진 색"""
    phi = math.radians(GEO["lat0"])
    my = 111132.92 - 559.82 * math.cos(2 * phi) + 1.175 * math.cos(4 * phi)
    mx = 111412.84 * math.cos(phi) - 93.5 * math.cos(3 * phi)
    t = math.radians(GEO["theta"])
    x, y = wx + GEO["ox"], wy + GEO["oy"]
    lat = GEO["lat0"] - (-x * math.sin(t) + y * math.cos(t)) / my
    lon = GEO["lon0"] + (x * math.cos(t) + y * math.sin(t)) / mx
    R = 6378137
    X = R * math.radians(lon)
    Y = R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    x0, x1, y0, y1 = SAT_EXTENT
    w, h = SAT.get_size()
    sx, sy = (X - x0) / (x1 - x0) * w, (y1 - Y) / (y1 - y0) * h
    if 0 <= sx < w and 0 <= sy < h:
        return SAT.get_at((int(sx), int(sy)))[:3]
    return None


def roof_from_satellite(poly, fallback):
    """건물 바닥 안 위성사진 색의 중간값 -> 조금 밝고 진하게"""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    samples = []
    for x in range(int(min(xs)) + 2, int(max(xs)) - 1, 2):
        for y in range(int(min(ys)) + 2, int(max(ys)) - 1, 2):
            if in_poly(x, y, poly):
                c = sat_color(x, y)
                if c and sum(c) > 150:
                    samples.append(c)
    if len(samples) < 12:
        return fallback
    med = [sorted(c[i] for c in samples)[len(samples) // 2] for i in range(3)]
    avg = sum(med) / 3
    return mix(tint([avg + (v - avg) * 1.6 for v in med], 1.15), fallback, 0.3)


# ------------------------------------------------------------------
# 2. 바닥
# ------------------------------------------------------------------
AREA_TILE = {
    "grass": ["tile_grass_0", "tile_grass_1", "tile_grass_2"], "park": ["tile_grass_0", "tile_grass_1"],
    "wood": ["tile_wood"], "plaza": ["tile_plaza"], "pitch": ["tile_pitch"], "track": ["tile_track"],
    "court": ["tile_court"], "parking": ["tile_parking"], "water": ["tile_water_0"], "pond": ["tile_water_0"],
    "sand": ["tile_sand"], "playground": ["tile_sand"], "construction": ["tile_construction"],
    "city": ["tile_city"],
}
FIXED_AREAS = ("pitch", "track", "court", "pond")    # 크기 그대로 두는 구역
ROAD_TILE = {"major": "tile_street", "street": "tile_street", "campus": "tile_campus",
             "path": "tile_path", "steps": "tile_plaza"}


def area_poly(area):
    if area["kind"] in FIXED_AREAS:
        return px_fixed(area["poly"])
    return px(area["poly"])


def draw_ground():
    g = pygame.Surface((W, H))
    g.blit(tiled(["tile_city"]), (0, 0))
    boundary = px(cd.BOUNDARY)
    paint(g, lambda s, c: pygame.draw.polygon(s, c, boundary), AREA_TILE["grass"])

    for kind in ("major", "street"):
        roads = [r for r in cd.ROADS if r["kind"] == kind]
        paint(g, lambda s, c: [draw_line_wide(s, c, px(r["pts"]), r["w"] * B * 1.2) for r in roads],
              [ROAD_TILE[kind]])
    for area in cd.AREAS:
        if len(area["poly"]) < 3:
            continue
        poly = area_poly(area)
        paint(g, lambda s, c: pygame.draw.polygon(s, c, poly), AREA_TILE.get(area["kind"], ["tile_grass_0"]))
        edge = {"wood": (47, 111, 63), "pond": (44, 156, 152), "water": (44, 156, 152), "track": (255, 255, 255),
                "parking": (143, 155, 179), "plaza": (201, 211, 224)}.get(area["kind"])
        if edge:
            pygame.draw.polygon(g, edge, poly, 1)
        if area["kind"] == "pitch":
            draw_pitch_lines(g, poly)
        if area["kind"] == "court":
            pygame.draw.polygon(g, (238, 244, 251), poly, 1)
    for kind in ("campus", "path", "steps"):
        roads = [r for r in cd.ROADS if r["kind"] == kind]
        paint(g, lambda s, c: [draw_line_wide(s, c, px(r["pts"]), max(2.5, r["w"]) * B * 1.15) for r in roads],
              [ROAD_TILE[kind]])
    for r in cd.ROADS:
        if r["kind"] == "major" and r["w"] >= 10:
            dashes(g, px(r["pts"]), (255, 216, 74))

    pygame.draw.polygon(g, (47, 111, 63), boundary, 3)     # 캠퍼스 생울타리
    pygame.draw.polygon(g, (79, 158, 69), boundary, 1)

    for _ in range(1500):      # 잔디 위 꽃
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        if in_poly(x, y, boundary):
            c = g.get_at((int(x), int(y)))
            if c.g > c.r + 30 and c.g > c.b + 30:
                g.blit(IMG[rng.choice(["flower_0", "flower_1", "flower_2", "flower_3"])], (x, y))
    return g


def dashes(surf, pts, color):
    on = True
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L // 6))
        for i in range(n):
            if on:
                p = (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
                q = (a[0] + (b[0] - a[0]) * (i + 0.5) / n, a[1] + (b[1] - a[1]) * (i + 0.5) / n)
                pygame.draw.line(surf, color, p, q)
            on = not on


def draw_pitch_lines(g, poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    r = pygame.Rect(min(xs) + 4, min(ys) + 4, max(xs) - min(xs) - 8, max(ys) - min(ys) - 8)
    if r.w < 30 or r.h < 30:
        return
    white = (238, 244, 251)
    pygame.draw.rect(g, white, r, 1)
    if r.h > r.w:
        pygame.draw.line(g, white, (r.left, r.centery), (r.right, r.centery))
        box = pygame.Rect(0, 0, r.w * 0.5, r.h * 0.14)
        for y in (r.top, r.bottom - box.h):
            box.midtop = (r.centerx, y)
            pygame.draw.rect(g, white, box, 1)
    else:
        pygame.draw.line(g, white, (r.centerx, r.top), (r.centerx, r.bottom))
    pygame.draw.circle(g, white, r.center, min(r.w, r.h) * 0.12, 1)


# ------------------------------------------------------------------
# 3. 건물 (남쪽 벽 + 위로 올린 지붕)
# ------------------------------------------------------------------
def wall_height(levels, campus):
    h = FLOOR_H * min(levels, 6) + 2 * max(0, levels - 6)
    if not campus:
        h = min(h, 34)
    return int(min(64, h + 2))


def make_building(b, pts):
    """건물 한 채 그림. (그림, 왼쪽 위 위치, 바닥 다각형(픽셀), 벽 높이, 지붕 가운데)"""
    n = len(pts)
    if sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n)) < 0:
        pts = pts[::-1]
    campus = b["campus"]
    h = wall_height(b["levels"], campus)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, y0 = int(min(xs)) - 2, int(min(ys)) - h - 2
    w, hh = int(max(xs)) - x0 + 3, int(max(ys)) - y0 + 3
    surf = pygame.Surface((w, hh), pygame.SRCALPHA)
    loc = [(x - x0, y - y0) for x, y in pts]
    wall, roof, style = b["wall"], b["roof"], b["style"]

    edges = []
    for i in range(n):
        a, c = loc[i], loc[(i + 1) % n]
        if c[0] - a[0] < -0.5:          # 남쪽을 향한 변
            edges.append((max(a[1], c[1]), c, a))
    edges.sort(key=lambda e: e[0])
    longest = None
    for _, l, r in edges:
        nx = (l[1] - r[1]) / math.hypot(r[0] - l[0], r[1] - l[1])
        col = tint(wall, 1.0 - 0.24 * nx)
        pygame.draw.polygon(surf, col, (l, r, (r[0], r[1] - h), (l[0], l[1] - h)))
        if campus:
            wall_detail(surf, l, r, h, col, style)
        else:
            for yy in range(int(l[1]) - 4, int(l[1]) - h + 2, 5):
                pygame.draw.line(surf, tint(col, 0.8), (l[0] + 1, yy), (r[0] - 1, yy))
        pygame.draw.line(surf, tint(col, 0.65), (l[0], l[1] - 1), (r[0], r[1] - 1))
        if longest is None or r[0] - l[0] > longest[0]:
            longest = (r[0] - l[0], l, r)
    if campus and longest and longest[0] >= 18:
        _, l, r = longest
        door = IMG["door_big" if longest[0] >= 70 else "door"]
        mx = (l[0] + r[0]) / 2
        my = l[1] + (r[1] - l[1]) * (mx - l[0]) / (r[0] - l[0])
        surf.blit(door, (int(mx - door.get_width() / 2), int(my) - door.get_height()))

    rp = [(x, y - h) for x, y in loc]
    pygame.draw.polygon(surf, tint(roof, 1.2), rp)
    tmp = pygame.Surface((w, hh), pygame.SRCALPHA)
    pygame.draw.polygon(tmp, (255, 255, 255), rp)
    rmask = pygame.mask.from_surface(tmp, 1)
    inner = rmask
    for off in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        inner = inner.overlap_mask(rmask, off)
    top = inner.to_surface(setcolor=roof + (255,), unsetcolor=(0, 0, 0, 0))
    if campus:
        for yy in range(3, hh, 6):
            pygame.draw.line(top, tint(roof, 0.92), (0, yy), (w, yy))
        top = inner.to_surface(setsurface=top, unsetcolor=(0, 0, 0, 0))
    surf.blit(top, (0, 0))
    pygame.draw.polygon(surf, tint(roof, 0.6), rp, 1)
    count = inner.count()
    if campus and count > 900:
        for _ in range(min(5, count // 1400 + 1)):
            for _try in range(20):
                u = IMG[rng.choice(["roof_unit_0", "roof_unit_1", "roof_unit_2"])]
                ux, uy = rng.randrange(3, max(4, w - 11)), rng.randrange(3, max(4, hh - 9))
                if all(0 <= ux + dx < w and 0 <= uy + dy < hh and inner.get_at((ux + dx, uy + dy))
                       for dx in (-2, 10) for dy in (-2, 8)):
                    surf.blit(u, (ux, uy))
                    break
    cx, cy = inner.centroid() if count else (w / 2, hh / 2)
    return surf, (x0, y0), pts, h, (x0 + cx, y0 + cy)


def wall_detail(surf, l, r, h, col, style):
    x_l, x_r = int(math.ceil(l[0])), int(math.floor(r[0]))
    width = x_r - x_l
    if width < 4:
        return
    slope = (r[1] - l[1]) / (r[0] - l[0])
    if style == "glass":
        g = IMG["win_glass"]
        for i in range(width // 6):
            x = x_l + (width - width // 6 * 6) // 2 + i * 6
            by = int(l[1] + slope * (x + 3 - l[0]))
            for k in range(max(1, (h - 2) // 6)):
                surf.blit(g, (x, by - (k + 1) * 6))
        return
    if style == "metal":
        for x in range(x_l + 2, x_r, 3):
            by = int(l[1] + slope * (x - l[0]))
            pygame.draw.line(surf, tint(col, 0.88), (x, by - h + 1), (x, by - 1))
        return
    win = IMG["win_b" if style == "concrete" else "win_a"]
    rows = max(1, (h - 2) // FLOOR_H)
    cols = (width - 2) // 7
    start = x_l + (width - (cols * 7 - 3)) // 2
    for i in range(cols):
        x = start + i * 7
        by = int(l[1] + slope * (x + 2 - l[0]))
        for k in range(rows):
            surf.blit(win, (x, by - k * FLOOR_H - 6))


# ------------------------------------------------------------------
# 4. 나무·소품·조형물 (솎아서 듬성듬성)
# ------------------------------------------------------------------
TREE_NAMES = {"cherry": ["tree_cherry_0", "tree_cherry_1", "tree_cherry_2"], "ginkgo": ["tree_ginkgo_0", "tree_ginkgo_1"],
              "green": ["tree_green_0", "tree_green_1", "tree_green_2"], "pine": ["tree_pine_0", "tree_pine_1"],
              "bush": ["bush_0", "bush_1"], "quince": ["tree_quince"]}
LANDMARK_SPRITE = {"백경탑": "monument", "웅비탑": "monument", "부경고사우루스": "statue_dino",
                   "실러캔스": "statue_fish", "한어울터": "fountain_0"}


def collect_statics():
    """(정렬 y, 그림, 발 위치 픽셀) 목록"""
    out = []
    # 벚꽃·은행·모과 먼저 (명소 나무가 솎아질 때 살아남게)
    order = {"quince": 0, "cherry": 1, "ginkgo": 1, "pine": 2, "green": 3, "bush": 4}
    trees = sorted(cd.TREES, key=lambda t: order.get(t[2], 5))
    kept = []
    for x, y, kind in trees:
        gap = TREE_GAP.get(kind, 20)
        if all(math.hypot(x - a, y - b) * STRETCH >= max(gap, g2) * 0.9 for a, b, g2 in kept):
            kept.append((x, y, gap))
            name = rng.choice(TREE_NAMES.get(kind, TREE_NAMES["green"]))
            fx, fy = T(x, y)
            out.append((fy, IMG[name], (fx, fy)))
    props = []
    for x, y, kind in cd.PROPS:
        if kind in ("bench", "lamp", "vending", "busstop", "flag", "sign"):
            if all(math.hypot(x - a, y - b) * STRETCH >= PROP_GAP for a, b in props):
                props.append((x, y))
                fx, fy = T(x, y)
                out.append((fy, IMG[kind], (fx, fy)))
    for lm in cd.LANDMARKS:
        name = LANDMARK_SPRITE.get(lm["name"])
        if name:
            fx, fy = T(lm["x"], lm["y"])
            out.append((fy, IMG[name], (fx, fy)))
    for gate in cd.GATES:
        if gate["name"] == "정문":
            for d in (-9, 9):
                fx, fy = T(gate["x"], gate["y"] + d)
                out.append((fy, IMG["gate_pillar"], (fx, fy)))
    return out, len(kept)


# ------------------------------------------------------------------
# 5. 전부 합치기
# ------------------------------------------------------------------
def main():
    floors, alias = load_registry()
    changed = []
    for b in cd.BUILDINGS:
        if not b["campus"]:
            continue
        key = alias.get(b["name"], b["name"]).replace(" ", "")
        if key in floors and floors[key] != b["levels"]:
            changed.append("%s %d->%d층" % (b["name"], b["levels"], floors[key]))
            b["levels"] = floors[key]
        b["roof"] = roof_from_satellite(b["poly"], b["roof"])
    print("건축물대장으로 고친 층수:", ", ".join(changed))

    ground = draw_ground()
    over = pygame.Surface((W, H), pygame.SRCALPHA)
    sil = pygame.Surface((W, H), pygame.SRCALPHA)
    block = pygame.Surface((W, H), pygame.SRCALPHA)
    blk = (0, 0, 0, 255)

    pygame.draw.rect(block, blk, block.get_rect())               # 캠퍼스 밖은 막힘
    pygame.draw.polygon(block, (0, 0, 0, 0), px(cd.BOUNDARY))
    for a in cd.AREAS:
        if a["kind"] in ("pond", "water") and len(a["poly"]) >= 3:
            pygame.draw.polygon(block, blk, area_poly(a))
    for lm in cd.LANDMARKS:
        if lm["name"] in LANDMARK_SPRITE:
            pygame.draw.circle(block, blk, T(lm["x"], lm["y"]), 4 * B)

    drawn, labels = [], []
    for b in cd.BUILDINGS:
        if len(b["poly"]) < 3:
            continue
        foot = px_fixed(b["poly"])
        surf, pos, foot, h, center = make_building(b, foot)
        drawn.append((max(p[1] for p in foot), "bld", (surf, pos, foot, h)))
        pygame.draw.polygon(block, blk, foot)
        if b["campus"] and b["name"] and polygon_area(b["poly"]) > 250:
            labels.append([b["name"], [round(center[0] * ZOOM), round(center[1] * ZOOM)]])

    shadow = pygame.Surface((W, H), pygame.SRCALPHA)       # 건물 그림자 (오른쪽 아래)
    for _, kind, (surf, pos, foot, h) in drawn:
        off = h * 0.45
        for a, b in zip(foot, foot[1:] + foot[:1]):
            pygame.draw.polygon(shadow, (20, 40, 30, 255),
                                [a, b, (b[0] + off, b[1] + off * 0.25), (a[0] + off, a[1] + off * 0.25)])
        pygame.draw.polygon(shadow, (20, 40, 30, 255), [(x + off, y + off * 0.25) for x, y in foot])
    shadow.set_alpha(80)
    ground.blit(shadow, (0, 0))

    statics, tree_count = collect_statics()
    print("나무", tree_count, "그루 (원래", len(cd.TREES), "그루)")
    for y, img, (fx, fy) in statics:
        drawn.append((y, "spr", (img, (fx, fy))))
        if img.get_height() > 20:
            r = pygame.Rect(0, 0, img.get_width() * 0.7, 5)
            r.center = (fx + 2, fy)
            pygame.draw.ellipse(ground, tint(ground.get_at((int(fx) % W, int(fy) % H)), 0.72), r)

    drawn.sort(key=lambda d: d[0])
    for _, kind, data in drawn:
        if kind == "bld":
            surf, pos, foot, _ = data
            over.blit(surf, pos)
            sil.blit(pygame.mask.from_surface(surf, 1).to_surface(setcolor=(255, 255, 255, 255),
                                                                 unsetcolor=(0, 0, 0, 0)), pos)
        else:
            img, (fx, fy) = data
            over.blit(img, (fx - img.get_width() // 2, fy - img.get_height() + 1))
    for _, kind, data in drawn:      # 건물 바닥 자리는 "뒤"가 아님
        if kind == "bld":
            pygame.draw.polygon(sil, (0, 0, 0, 0), data[2])

    for lm in cd.LANDMARKS:          # 명소 이름표
        if lm["kind"] == "building" or lm["name"] in ("골드정원", "생활밀착형 숲", "허공에의 드로잉"):
            continue
        fx, fy = T(lm["x"], lm["y"] - 6)
        labels.append([lm["name"], [round(fx * ZOOM), round(fy * ZOOM)]])

    save(ground, over, sil, block, labels)


def save(ground, over, sil, block, labels):
    os.makedirs(OUT, exist_ok=True)
    big = (W * ZOOM, H * ZOOM)
    pygame.image.save(pygame.transform.scale(ground, big), os.path.join(OUT, "map.png"))
    pygame.image.save(pygame.transform.scale(over, big), os.path.join(OUT, "map_bld.png"))
    cells = (big[0] // CELL, big[1] // CELL)
    for surf, name, cut in ((sil, "map_sil.png", 140), (block, "map_block.png", 110)):
        small = pygame.transform.smoothscale(surf, cells)
        out = pygame.Surface(cells, pygame.SRCALPHA)
        for y in range(cells[1]):
            for x in range(cells[0]):
                if small.get_at((x, y)).a >= cut:
                    out.set_at((x, y), (0, 0, 0, 255))
        pygame.image.save(out, os.path.join(OUT, name))
    sx, sy = T(*cd.START)
    with open(os.path.join(OUT, "map_labels.json"), "w", encoding="utf-8") as f:
        json.dump({"cell": CELL, "start": [round(sx * ZOOM), round(sy * ZOOM)], "labels": labels},
                  f, ensure_ascii=False)
    print("맵 크기:", big, "/ 이름표", len(labels), "개")


if __name__ == "__main__":
    main()
