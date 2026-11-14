# ui.py - 화면에 보이는 정보들 (HP·경험치바, 타이머, 레벨업 창, 시작/끝 화면)
#
# 그리는 곳이 두 군데:
#   screen (320x180 작은 화면) -> 막대, 상자, 아이콘 같은 도트 그림
#   window (확대된 실제 창)    -> 글자 (한글이 선명하게 보이도록)
# 좌표는 둘 다 작은 화면(320x180) 기준으로 넘기면 됨.
import math

import pygame
from settings import WIDTH, HEIGHT, SCALE, FONT_NAME, GAME_DURATION, ITEMS
import sprites

TEXT_COLOR = (235, 235, 235)
YELLOW = (250, 220, 90)
RED = (240, 90, 90)
GRAY = (170, 170, 190)

XP_COLOR = (90, 170, 250)
HP_COLOR = (220, 60, 60)
BOSS_COLOR = (200, 70, 200)

XP_BAR = pygame.Rect(0, 0, WIDTH, 4)
HP_BAR = pygame.Rect(4, 8, 64, 5)
BOSS_BAR = pygame.Rect(WIDTH // 2 - 70, HEIGHT - 10, 140, 5)

fonts = {}


def init():
    """글꼴 준비 (pygame.init() 다음에 한 번)"""
    fonts["small"] = pygame.font.SysFont(FONT_NAME, 6 * SCALE)
    fonts["normal"] = pygame.font.SysFont(FONT_NAME, 7 * SCALE)
    fonts["timer"] = pygame.font.SysFont(FONT_NAME, 9 * SCALE, bold=True)
    fonts["big"] = pygame.font.SysFont(FONT_NAME, 12 * SCALE, bold=True)
    fonts["title"] = pygame.font.SysFont(FONT_NAME, 18 * SCALE, bold=True)


# ------------------------------------------------------------------
# 기본 도구
# ------------------------------------------------------------------
def draw_text(window, size, text, x, y, anchor="topleft", color=TEXT_COLOR):
    """window에 글자 그리기. 뒤에 검은 그림자를 깔아서 어떤 배경에서도 잘 보이게.
    size: "small" / "normal" / "timer" / "big" / "title"
    anchor: "topleft", "midtop", "topright", "center" 등"""
    font = fonts[size]
    pos = {anchor: (x * SCALE, y * SCALE)}
    shadow = font.render(text, True, (0, 0, 0))
    window.blit(shadow, shadow.get_rect(**pos).move(2, 2))
    text_surface = font.render(text, True, color)
    window.blit(text_surface, text_surface.get_rect(**pos))


def draw_bar(screen, rect, ratio, color):
    """채워지는 막대 (HP, 경험치 등). ratio: 0.0 ~ 1.0"""
    ratio = max(0, min(1, ratio))
    pygame.draw.rect(screen, (15, 15, 20), rect.inflate(2, 2))    # 테두리
    screen.fill((50, 50, 60), rect)                               # 빈 부분
    filled = pygame.Rect(rect.left, rect.top, round(rect.width * ratio), rect.height)
    screen.fill(color, filled)
    light = tuple(min(255, c + 60) for c in color)                # 윗줄을 밝게 -> 입체감
    screen.fill(light, (filled.left, filled.top, filled.width, 1))


def draw_dark_overlay(screen, alpha=150):
    """게임 화면을 어둡게 덮기 (레벨업/시작/끝 화면 뒤)"""
    dark = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dark.fill((0, 0, 0, alpha))
    screen.blit(dark, (0, 0))


def format_time(ms):
    """밀리초를 '분:초' 글자로 바꾸기 (예: 600000 -> '10:00')"""
    seconds = int(max(0, ms)) // 1000
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def active_buffs(player, now):
    return [(kind, end) for kind, end in player.buffs.items() if end > now]


# ------------------------------------------------------------------
# 게임 중 정보 (HUD)
# ------------------------------------------------------------------
def draw_hud_screen(screen, player, boss, now):
    """막대와 아이콘 (작은 screen에)"""
    draw_bar(screen, XP_BAR, player.xp / player.xp_needed(), XP_COLOR)
    draw_bar(screen, HP_BAR, player.hp / player.max_hp, HP_COLOR)

    # 켜져 있는 버프 아이콘 (왼쪽 아래부터 위로)
    y = HEIGHT - 12
    for kind, _ in active_buffs(player, now):
        screen.blit(sprites.load(kind, sprites.ITEM_GRIDS[kind]), (4, y))
        y -= 11

    if boss is not None and boss.alive():
        draw_bar(screen, BOSS_BAR, boss.hp / boss.max_hp, BOSS_COLOR)


def draw_hud_text(window, player, kills, game_time, boss, now):
    """글자 (확대된 window에)"""
    draw_text(window, "small", f"{math.ceil(player.hp)}/{player.max_hp}", HP_BAR.right + 4, HP_BAR.top - 2)
    draw_text(window, "normal", f"Lv {player.level}", 4, 15)
    draw_text(window, "timer", format_time(GAME_DURATION - game_time), WIDTH // 2, 5, "midtop")
    draw_text(window, "normal", f"처치 {kills}", WIDTH - 4, 6, "topright")

    y = HEIGHT - 12
    for kind, end in active_buffs(player, now):
        seconds = math.ceil((end - now) / 1000)
        draw_text(window, "small", f"{ITEMS[kind]['name']} {seconds}초", 15, y, color=ITEMS[kind]["color"])
        y -= 11

    if boss is not None and boss.alive():
        draw_text(window, "small", "기말고사", WIDTH // 2, BOSS_BAR.top - 1, "midbottom", BOSS_COLOR)


def draw_player_hp(screen, player, offset):
    """플레이어 발밑의 작은 HP 막대 (다쳤을 때만)"""
    if player.hp < player.max_hp:
        rect = pygame.Rect(0, 0, 12, 2)
        rect.midtop = (player.pos.x - offset.x, player.rect.bottom - offset.y + 2)
        draw_bar(screen, rect, player.hp / player.max_hp, HP_COLOR)


def draw_map_labels(window, labels, offset):
    """건물 이름표"""
    for text, (x, y) in labels:
        sx, sy = x - offset.x, y - offset.y
        if -60 < sx < WIDTH + 60 and -20 < sy < HEIGHT + 20:
            draw_text(window, "small", text, sx, sy, "center", (255, 250, 220))


# ------------------------------------------------------------------
# 레벨업 창
# ------------------------------------------------------------------
def get_option_rects(count):
    """레벨업 선택지 상자 위치들 (게임 화면 기준)"""
    box_w, box_h, gap = 92, 60, 8
    left = (WIDTH - (box_w * count + gap * (count - 1))) // 2
    return [pygame.Rect(left + i * (box_w + gap), 62, box_w, box_h) for i in range(count)]


def draw_levelup_screen(screen, options):
    for rect in get_option_rects(len(options)):
        pygame.draw.rect(screen, (40, 40, 60), rect)
        pygame.draw.rect(screen, YELLOW, rect, 1)


def draw_levelup_text(window, options):
    draw_text(window, "big", "레벨 업!", WIDTH // 2, 30, "midtop", YELLOW)
    draw_text(window, "small", "1, 2, 3 키 또는 클릭으로 선택", WIDTH // 2, 46, "midtop")
    for i, (option, rect) in enumerate(zip(options, get_option_rects(len(options)))):
        draw_text(window, "small", f"[{i + 1}]", rect.centerx, rect.top + 6, "midtop", YELLOW)
        draw_text(window, "small", option["title"], rect.centerx, rect.top + 20, "midtop")
        draw_text(window, "small", option["desc"], rect.centerx, rect.top + 36, "midtop", GRAY)


# ------------------------------------------------------------------
# 시작 화면 / 끝 화면
# ------------------------------------------------------------------
def draw_title_text(window, real_time):
    draw_text(window, "title", "부경대 서바이벌", WIDTH // 2, 36, "midtop", YELLOW)
    draw_text(window, "normal", "몰려오는 과제와 시험을 피해 10분 동안 살아남아라!", WIDTH // 2, 70, "midtop")
    draw_text(window, "small", "WASD / 방향키: 이동      공격: 자동", WIDTH // 2, 96, "midtop", GRAY)
    draw_text(window, "small", "레벨업하면 강화를 고르고, 맵의 버프 아이템을 주워라", WIDTH // 2, 106, "midtop", GRAY)
    if (real_time // 500) % 2 == 0:  # 깜빡깜빡
        draw_text(window, "normal", "아무 키나 눌러 시작", WIDTH // 2, 132, "midtop")


def draw_end_text(window, state, game_time, kills, level):
    if state == "gameover":
        draw_text(window, "big", "게임 오버", WIDTH // 2, 56, "midtop", RED)
        summary = f"생존 시간 {format_time(game_time)}    처치 {kills}    레벨 {level}"
    else:
        draw_text(window, "big", "클리어!", WIDTH // 2, 56, "midtop", YELLOW)
        summary = f"10분 생존 성공!    처치 {kills}    레벨 {level}"
    draw_text(window, "normal", summary, WIDTH // 2, 82, "midtop")
    draw_text(window, "normal", "R: 다시 시작      ESC: 종료", WIDTH // 2, 104, "midtop", GRAY)
