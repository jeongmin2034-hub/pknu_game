# campus.py - 부경대 대연캠퍼스 맵 그리기
#
# 실제 캠퍼스 배치를 그대로 옮긴 건 아니고, "캠퍼스 느낌"으로 그린 맵.
#   - 가운데 광장(분수), 십자 모양 길, 오른쪽 아래 운동장
#   - 가장자리에는 건물들 (플레이어는 건물 구역에 못 들어감)
#   - 아래쪽 가운데가 정문
#
# assets/images/map.png 가 있으면 이 맵 대신 그 그림을 씀.
# (그 경우에도 가장자리 MAP_BORDER 만큼은 못 들어가는 구역)
import os
import random

import pygame
from settings import MAP_WIDTH, MAP_HEIGHT, MAP_BORDER

MAP_IMAGE = os.path.join(os.path.dirname(__file__), "assets", "images", "map.png")

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
    if os.path.exists(MAP_IMAGE):
        surface = pygame.image.load(MAP_IMAGE).convert()
        labels = []
    else:
        surface, labels = draw_campus()
    w, h = surface.get_size()
    play_area = pygame.Rect(MAP_BORDER, MAP_BORDER, w - 2 * MAP_BORDER, h - 2 * MAP_BORDER)
    return surface, play_area, labels


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

    # 2. 길: 가로 큰길 + 세로 큰길(정문까지) + 운동장 가는 길
    roads = [
        pygame.Rect(b, cy - 20, w - 2 * b, 40),
        pygame.Rect(cx - 20, b, 40, h - b),  # 아래로 정문까지 이어짐
        pygame.Rect(cx + 20, cy + 150, 380, 24),
    ]
    for road in roads:
        draw_road(s, road)

    # 3. 가운데 광장과 분수
    pygame.draw.circle(s, ROAD, (cx, cy), 60)
    pygame.draw.circle(s, STONE, (cx, cy), 26)
    pygame.draw.circle(s, WATER, (cx, cy), 21)
    pygame.draw.circle(s, (150, 200, 240), (cx, cy), 6)

    # 4. 운동장 (오른쪽 아래)
    field = pygame.Rect(cx + 140, cy + 190, 380, 210)
    pygame.draw.rect(s, TRACK, field, border_radius=100)
    inner = field.inflate(-36, -36)
    pygame.draw.rect(s, FIELD, inner, border_radius=80)
    pygame.draw.rect(s, LINE, inner.inflate(-60, -30), 1)
    pygame.draw.line(s, LINE, (inner.centerx, inner.top + 15), (inner.centerx, inner.bottom - 15))
    pygame.draw.circle(s, LINE, inner.center, 18, 1)
    labels.append(("운동장", (field.centerx, field.top - 8)))

    # 5. 가장자리 울타리(생울타리) - 여기부터는 못 들어감
    pygame.draw.rect(s, HEDGE, (b - 4, b - 4, w - 2 * b + 8, h - 2 * b + 8), 4)

    # 6. 가장자리 건물들
    buildings = [
        # (x, y, 너비, 높이, 이름)  이름이 ""이면 이름표 없음
        (90, 6, 260, b - 14, "중앙도서관"),
        (cx - 150, 6, 300, b - 14, "대학본관"),
        (w - 350, 6, 260, b - 14, ""),
        (6, 120, b - 14, 280, "학생회관"),
        (6, h - 400, b - 14, 280, ""),
        (w - b + 8, 120, b - 14, 300, ""),
        (w - b + 8, h - 420, b - 14, 300, ""),
        (90, h - b + 8, 300, b - 14, ""),
        (w - 390, h - b + 8, 300, b - 14, ""),
    ]
    for x, y, bw, bh, name in buildings:
        draw_building(s, pygame.Rect(x, y, bw, bh))
        if name:
            labels.append((name, (x + bw // 2, y + bh // 2)))

    # 정문 (아래 가운데) - 기둥 두 개
    gate_y = h - b + 4
    for gx in (cx - 34, cx + 26):
        s.fill(STONE, (gx, gate_y, 8, b - 8))
        s.fill(WALL_SHADE, (gx, gate_y + b - 14, 8, 6))
    labels.append(("정문", (cx, h - b // 2)))

    # 7. 나무 (길, 광장, 운동장 위에는 안 심음)
    blocked = roads + [field.inflate(20, 20), pygame.Rect(cx - 70, cy - 70, 140, 140)]
    planted = 0
    while planted < 140:
        x = rng.randrange(b + 10, w - b - 10)
        y = rng.randrange(b + 10, h - b - 10)
        if any(r.inflate(16, 16).collidepoint(x, y) for r in blocked):
            continue
        draw_tree(s, x, y)
        planted += 1

    # 8. 큰길 옆 벤치
    for x in range(b + 60, w - b - 60, 140):
        if abs(x - cx) > 80:
            s.fill((120, 80, 50), (x, cy - 28, 14, 4))
            s.fill((120, 80, 50), (x, cy + 24, 14, 4))

    return s, labels


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
