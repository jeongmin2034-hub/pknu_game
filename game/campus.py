# campus.py - 부경대 대연캠퍼스 맵 그리기
#
# 실제 캠퍼스 배치를 그대로 옮긴 건 아니고, "캠퍼스 느낌"으로 그린 맵.
#   - 가운데 광장(분수), 바둑판 모양 길, 운동장·농구장·연못·주차장·잔디광장
#   - 가장자리에는 건물들 (플레이어는 건물 구역에 못 들어감)
#   - 아래쪽 가운데가 정문
#
# assets/images/map.png 가 있으면 이 맵 대신 그 그림을 씀. (실제 부경대 대연캠퍼스 맵)
#   map_block.png   : 충돌 지도. 그림의 1픽셀 = 맵의 8x8 칸. 불투명한 픽셀 = 막힌 칸 (건물, 캠퍼스 밖)
#   map_labels.json : 건물 이름표 위치와 시작 위치
import json
import os
import random

import pygame
from settings import MAP_WIDTH, MAP_HEIGHT, MAP_BORDER

IMAGE_DIR = os.path.join(os.path.dirname(__file__), "assets", "images")
MAP_IMAGE = os.path.join(IMAGE_DIR, "map.png")
BLOCK_IMAGE = os.path.join(IMAGE_DIR, "map_block.png")
LABEL_FILE = os.path.join(IMAGE_DIR, "map_labels.json")
BUILDING_IMAGE = os.path.join(IMAGE_DIR, "map_bld.png")
SILHOUETTE_IMAGE = os.path.join(IMAGE_DIR, "map_sil.png")

BLOCK_CELL = 8      # 충돌 지도 한 칸의 크기 (픽셀)
block_mask = None   # 충돌 지도 (없으면 None -> 건물 충돌 없음)
start = None        # 플레이어 시작 위치 (없으면 맵 한가운데)
building_layer = None  # 건물 그림 (지붕·벽만 있는 투명 그림. 캐릭터 위에 덮어 그림)
silhouette = None      # 건물 그림이 덮는 칸 (캐릭터가 건물 뒤에 있는지 확인용)

GRASS = (92, 150, 72)
GRASS_DARK = (78, 132, 62)
GRASS_LIGHT = (110, 168, 84)
ROAD = (196, 186, 164)
ROAD_LINE = (176, 166, 146)
HEDGE = (52, 100, 50)
WALL = (205, 200, 190)
WALL_SHADE = (165, 160, 152)
ROOF = (130, 135, 150)
WINDOW = (85, 125, 170)
TRACK = (175, 85, 65)
FIELD = (70, 150, 80)
LINE = (240, 240, 240)
STONE = (175, 175, 180)
WATER = (80, 150, 220)


def load_map():
    """(맵 그림, 플레이 가능 구역, 건물 이름표 목록)을 돌려줌.
    이름표는 (글자, 월드 좌표) 목록"""
    global block_mask, start, building_layer, silhouette
    if not os.path.exists(MAP_IMAGE):
        surface, labels = draw_campus()
        w, h = surface.get_size()
        play_area = pygame.Rect(MAP_BORDER, MAP_BORDER, w - 2 * MAP_BORDER, h - 2 * MAP_BORDER)
        return surface, play_area, labels

    surface = pygame.image.load(MAP_IMAGE).convert()
    labels = []
    if os.path.exists(LABEL_FILE):
        with open(LABEL_FILE, encoding="utf-8") as f:
            data = json.load(f)
        labels = [(text, tuple(pos)) for text, pos in data["labels"]]
        start = tuple(data["start"])
    if os.path.exists(BLOCK_IMAGE):
        block_mask = pygame.mask.from_surface(pygame.image.load(BLOCK_IMAGE).convert_alpha())
    if os.path.exists(BUILDING_IMAGE) and os.path.exists(SILHOUETTE_IMAGE):
        building_layer = pygame.image.load(BUILDING_IMAGE).convert_alpha()
        silhouette = pygame.mask.from_surface(pygame.image.load(SILHOUETTE_IMAGE).convert_alpha())
    play_area = surface.get_rect().inflate(-16, -16)
    return surface, play_area, labels


def is_blocked(x, y):
    """맵의 (x, y)가 막힌 곳(건물, 캠퍼스 밖)인지"""
    if block_mask is None:
        return False
    cx, cy = int(x) // BLOCK_CELL, int(y) // BLOCK_CELL
    w, h = block_mask.get_size()
    if not (0 <= cx < w and 0 <= cy < h):
        return True
    return block_mask.get_at((cx, cy)) == 1


def is_behind(x, y):
    """(x, y)에 서 있는 캐릭터가 건물 뒤에 가려지는 자리인지 (지붕·벽 그림 안쪽)"""
    if silhouette is None:
        return False
    cx, cy = int(x) // BLOCK_CELL, int(y) // BLOCK_CELL
    w, h = silhouette.get_size()
    return 0 <= cx < w and 0 <= cy < h and silhouette.get_at((cx, cy)) == 1


def move(pos, step):
    """pos를 step만큼 옮기되 벽은 못 지나감. 가로·세로를 따로 확인해서
    비스듬히 부딪히면 벽을 따라 미끄러지듯 움직임. 실제로 움직였으면 True"""
    moved = False
    if step.x != 0 and not is_blocked(pos.x + step.x, pos.y):
        pos.x += step.x
        moved = True
    if step.y != 0 and not is_blocked(pos.x, pos.y + step.y):
        pos.y += step.y
        moved = True
    return moved


def free_point(pos, toward):
    """pos가 막힌 곳이면 toward 쪽으로 조금씩 옮겨서 처음 나오는 빈 곳을 돌려줌"""
    point = pygame.Vector2(pos)
    direction = pygame.Vector2(toward) - point
    steps = int(direction.length() // BLOCK_CELL)
    for _ in range(steps):
        if not is_blocked(point.x, point.y):
            break
        point += direction.normalize() * BLOCK_CELL
    return point


def draw_campus():
    rng = random.Random(7)  # 숫자를 고정하면 매번 같은 맵이 나옴
    w, h, b = MAP_WIDTH, MAP_HEIGHT, MAP_BORDER
    cx, cy = w // 2, h // 2
    s = pygame.Surface((w, h))
    labels = []

    # 1. 잔디 (점을 흩뿌려서 질감)
    s.fill(GRASS)
    for _ in range(w * h // 40):
        s.set_at((rng.randrange(w), rng.randrange(h)), rng.choice((GRASS_DARK, GRASS_LIGHT)))

    # 2. 길: 가로 3줄 + 세로 3줄 (가운데 세로 길은 정문까지)
    road_xs = [w // 4, cx, w * 3 // 4]
    road_ys = [h // 4, cy, h * 3 // 4]
    roads = [pygame.Rect(b, y - 20, w - 2 * b, 40) for y in road_ys]
    roads += [pygame.Rect(x - 20, b, 40, h - 2 * b) for x in road_xs]
    roads.append(pygame.Rect(cx - 20, h - b, 40, b))  # 정문으로 나가는 길
    for road in roads:
        draw_road(s, road)

    # 3. 길이 만나는 곳마다 작은 광장, 한가운데는 큰 광장과 분수
    for x in road_xs:
        for y in road_ys:
            pygame.draw.circle(s, ROAD, (x, y), 44)
    pygame.draw.circle(s, ROAD, (cx, cy), 90)
    pygame.draw.circle(s, STONE, (cx, cy), 34)
    pygame.draw.circle(s, WATER, (cx, cy), 28)
    pygame.draw.circle(s, (150, 200, 240), (cx, cy), 8)
    labels.append(("중앙광장", (cx, cy - 60)))

    # 4. 길 사이 잔디 구역에 놓는 것들 (전부 그림일 뿐, 지나다닐 수 있음)
    field = pygame.Rect(0, 0, 560, 300)        # 대운동장 (오른쪽 아래)
    field.center = (w * 7 // 8 - 20, h * 7 // 8 - 20)
    draw_field(s, field)
    labels.append(("대운동장", (field.centerx, field.top - 10)))

    court = pygame.Rect(0, 0, 300, 180)        # 농구장 (왼쪽 아래)
    court.center = (w // 8 + 30, h * 5 // 8)
    draw_court(s, court)
    labels.append(("농구장", (court.centerx, court.top - 10)))

    pond = pygame.Rect(0, 0, 320, 200)         # 연못 (왼쪽 위)
    pond.center = (w * 3 // 8, h * 3 // 8)
    pygame.draw.ellipse(s, STONE, pond.inflate(12, 12))
    pygame.draw.ellipse(s, WATER, pond)
    pygame.draw.ellipse(s, (120, 180, 235), pond.inflate(-120, -90))
    labels.append(("연못", (pond.centerx, pond.top - 14)))

    parking = pygame.Rect(0, 0, 360, 200)      # 주차장 (오른쪽 위)
    parking.center = (w * 5 // 8, h // 8 + 20)
    draw_parking(s, parking, rng)
    labels.append(("주차장", (parking.centerx, parking.top - 10)))

    lawn = pygame.Rect(0, 0, 380, 260)         # 잔디광장 (가운데 오른쪽)
    lawn.center = (w * 5 // 8, h * 5 // 8)
    pygame.draw.rect(s, GRASS_LIGHT, lawn, border_radius=30)
    pygame.draw.rect(s, HEDGE, lawn, 3, border_radius=30)
    labels.append(("잔디광장", lawn.center))

    # 5. 가장자리 울타리(생울타리) - 여기부터는 못 들어감
    pygame.draw.rect(s, HEDGE, (b - 4, b - 4, w - 2 * b + 8, h - 2 * b + 8), 4)

    # 6. 가장자리 건물들: 네 변을 따라 줄지어 세움
    top_names = ["중앙도서관", "", "대학본관", "", "공학관", "", "자연과학관", ""]
    side_names = ["학생회관", "", "인문관", "", "체육관", ""]
    for i, x in enumerate(range(90, w - 400, 460)):
        draw_building(s, pygame.Rect(x, 6, 340, b - 14))
        if top_names[i % len(top_names)]:
            labels.append((top_names[i % len(top_names)], (x + 170, b // 2)))
        if abs(x + 170 - cx) > 260:  # 아래쪽은 정문 자리를 비워 둠
            draw_building(s, pygame.Rect(x, h - b + 8, 340, b - 14))
    for i, y in enumerate(range(110, h - 420, 450)):
        draw_building(s, pygame.Rect(6, y, b - 14, 340))
        draw_building(s, pygame.Rect(w - b + 8, y, b - 14, 340))
        if side_names[i % len(side_names)]:
            labels.append((side_names[i % len(side_names)], (b // 2 + 30, y + 170)))

    # 정문 (아래 가운데) - 기둥 두 개
    gate_y = h - b + 4
    for gx in (cx - 34, cx + 26):
        s.fill(STONE, (gx, gate_y, 8, b - 8))
        s.fill(WALL_SHADE, (gx, gate_y + b - 14, 8, 6))
    labels.append(("정문", (cx, h - b // 2)))

    # 7. 나무 (길, 광장, 운동장 같은 곳 위에는 안 심음)
    blocked = roads + [field, court, pond, parking, lawn, pygame.Rect(cx - 100, cy - 100, 200, 200)]
    blocked += [pygame.Rect(x - 50, y - 50, 100, 100) for x in road_xs for y in road_ys]
    planted = 0
    while planted < 1100:
        x = rng.randrange(b + 10, w - b - 10)
        y = rng.randrange(b + 10, h - b - 10)
        if any(r.inflate(24, 24).collidepoint(x, y) for r in blocked):
            continue
        draw_tree(s, x, y)
        planted += 1

    # 8. 가로 길 옆 벤치
    for y in road_ys:
        for x in range(b + 60, w - b - 60, 160):
            if all(abs(x - rx) > 70 for rx in road_xs):
                s.fill((120, 80, 50), (x, y - 28, 14, 4))
                s.fill((120, 80, 50), (x, y + 24, 14, 4))

    return s, labels


def draw_field(s, field):
    """육상 트랙 + 축구장"""
    pygame.draw.rect(s, TRACK, field, border_radius=140)
    inner = field.inflate(-44, -44)
    pygame.draw.rect(s, FIELD, inner, border_radius=110)
    pygame.draw.rect(s, LINE, inner.inflate(-90, -40), 1)
    pygame.draw.line(s, LINE, (inner.centerx, inner.top + 20), (inner.centerx, inner.bottom - 20))
    pygame.draw.circle(s, LINE, inner.center, 26, 1)


def draw_court(s, court):
    """농구장 2면"""
    pygame.draw.rect(s, (70, 110, 150), court)
    for half in (pygame.Rect(court.left + 8, court.top + 8, court.width // 2 - 12, court.height - 16),
                 pygame.Rect(court.centerx + 4, court.top + 8, court.width // 2 - 12, court.height - 16)):
        pygame.draw.rect(s, (200, 120, 70), half)
        pygame.draw.rect(s, LINE, half, 1)
        pygame.draw.line(s, LINE, half.midtop, half.midbottom)
        pygame.draw.circle(s, LINE, half.center, 14, 1)


def draw_parking(s, parking, rng):
    """주차장: 아스팔트 + 주차선 + 자동차 몇 대"""
    s.fill((95, 98, 105), parking)
    car_colors = [(200, 60, 60), (60, 90, 180), (230, 230, 230), (40, 40, 50), (220, 190, 60)]
    for row_y in (parking.top + 8, parking.bottom - 48):
        for x in range(parking.left + 10, parking.right - 24, 26):
            pygame.draw.line(s, LINE, (x, row_y), (x, row_y + 40))
            if rng.random() < 0.6:
                car = pygame.Rect(x + 5, row_y + 5, 16, 30)
                pygame.draw.rect(s, rng.choice(car_colors), car, border_radius=3)
                s.fill((150, 190, 220), (car.left + 2, car.top + 5, 12, 6))


def draw_road(s, rect):
    """보도블록 길"""
    s.fill(ROAD, rect)
    for x in range(rect.left, rect.right, 8):
        pygame.draw.line(s, ROAD_LINE, (x, rect.top), (x, rect.bottom - 1))
    for y in range(rect.top, rect.bottom, 8):
        pygame.draw.line(s, ROAD_LINE, (rect.left, y), (rect.right - 1, y))


def draw_building(s, rect):
    """위에서 내려다본 건물: 옥상 + 창문 + 그림자"""
    s.fill((60, 90, 55), rect.move(3, 3))          # 그림자
    s.fill(WALL, rect)
    s.fill(ROOF, rect.inflate(-6, -6))             # 옥상
    pygame.draw.rect(s, WALL_SHADE, rect, 1)
    # 옥상 위 창문(채광창) 줄
    inner = rect.inflate(-14, -14)
    for x in range(inner.left, inner.right - 3, 9):
        for y in range(inner.top, inner.bottom - 3, 9):
            s.fill(WINDOW, (x, y, 4, 4))


def draw_tree(s, x, y):
    pygame.draw.ellipse(s, (60, 100, 50), (x - 6, y + 3, 13, 5))   # 그림자
    s.fill((110, 75, 45), (x - 1, y, 2, 5))                         # 줄기
    pygame.draw.circle(s, (45, 110, 55), (x, y - 2), 6)            # 잎
    pygame.draw.circle(s, (70, 145, 70), (x - 2, y - 4), 3)        # 밝은 잎
