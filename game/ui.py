# ui.py - 화면에 보이는 정보들 (HP·경험치바, 타이머, 레벨업 창, 시작/끝 화면)
#
# UI는 전부 확대가 끝난 실제 창(window)에 그림 (글자가 선명하게 보이도록).
# 좌표는 "UI 칸" 기준: 화면 전체가 가로 320칸 x 세로 180칸, 1칸 = 창의 4픽셀.
# 게임 해상도(settings.WIDTH)를 바꿔도 UI 크기는 그대로임.
import math

import pygame
from settings import WIDTH, HEIGHT, SCALE, WINDOW_W, FONT_NAME, GAME_DURATION, ITEMS, PASSIVES, SYNERGIES
import sprites

UI_W, UI_H = 320, 180
U = WINDOW_W // UI_W   # UI 1칸이 창에서 몇 픽셀인지 (4)

TEXT_COLOR = (235, 235, 235)
YELLOW = (250, 220, 90)
RED = (240, 90, 90)
GRAY = (170, 170, 190)
GREEN = (120, 220, 140)

XP_COLOR = (90, 170, 250)
HP_COLOR = (220, 60, 60)
BOSS_COLOR = (200, 70, 200)

XP_BAR = pygame.Rect(0, 0, UI_W, 3)
HP_BAR = pygame.Rect(4, 7, 64, 5)
BOSS_BAR = pygame.Rect(UI_W // 2 - 70, UI_H - 10, 140, 5)

fonts = {}


def init():
    """글꼴 준비 (pygame.init() 다음에 한 번)"""
    fonts["tiny"] = pygame.font.SysFont(FONT_NAME, 5 * U)
    fonts["small"] = pygame.font.SysFont(FONT_NAME, 6 * U)
    fonts["normal"] = pygame.font.SysFont(FONT_NAME, 7 * U)
    fonts["timer"] = pygame.font.SysFont(FONT_NAME, 9 * U, bold=True)
    fonts["big"] = pygame.font.SysFont(FONT_NAME, 12 * U, bold=True)
    fonts["title"] = pygame.font.SysFont(FONT_NAME, 18 * U, bold=True)


# ------------------------------------------------------------------
# 기본 도구
# ------------------------------------------------------------------
def to_window(rect):
    """UI 칸 기준 네모 -> 창 픽셀 기준 네모"""
    return pygame.Rect(rect.x * U, rect.y * U, rect.width * U, rect.height * U)


def mouse_to_ui(pos):
    """마우스 위치(창 픽셀) -> UI 칸"""
    return pos[0] // U, pos[1] // U


def draw_text(window, size, text, x, y, anchor="topleft", color=TEXT_COLOR):
    """글자 그리기. 뒤에 검은 그림자를 깔아서 어떤 배경에서도 잘 보이게.
    size: "tiny" / "small" / "normal" / "timer" / "big" / "title"
    anchor: "topleft", "midtop", "topright", "center" 등"""
    font = fonts[size]
    pos = {anchor: (x * U, y * U)}
    shadow = font.render(text, True, (0, 0, 0))
    window.blit(shadow, shadow.get_rect(**pos).move(2, 2))
    text_surface = font.render(text, True, color)
    window.blit(text_surface, text_surface.get_rect(**pos))


def draw_bar(surface, rect, ratio, color):
    """채워지는 막대 (HP, 경험치 등). ratio: 0.0 ~ 1.0. rect는 그리는 곳의 픽셀 기준"""
    ratio = max(0, min(1, ratio))
    pygame.draw.rect(surface, (15, 15, 20), rect.inflate(4, 4))   # 테두리
    surface.fill((50, 50, 60), rect)                              # 빈 부분
    filled = pygame.Rect(rect.left, rect.top, round(rect.width * ratio), rect.height)
    surface.fill(color, filled)
    light = tuple(min(255, c + 60) for c in color)                # 윗줄을 밝게 -> 입체감
    surface.fill(light, (filled.left, filled.top, filled.width, max(1, rect.height // 4)))


def draw_dark_overlay(window, alpha=150):
    """게임 화면을 어둡게 덮기 (레벨업/시작/끝 화면 뒤)"""
    dark = pygame.Surface(window.get_size(), pygame.SRCALPHA)
    dark.fill((0, 0, 0, alpha))
    window.blit(dark, (0, 0))


def format_time(ms):
    """밀리초를 '분:초' 글자로 바꾸기 (예: 600000 -> '10:00')"""
    seconds = int(max(0, ms)) // 1000
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def active_buffs(player, now):
    return [(kind, end) for kind, end in player.buffs.items() if end > now]


# ------------------------------------------------------------------
# 게임 중 정보 (HUD)
# ------------------------------------------------------------------
def draw_hud(window, player, weapons, kills, game_time, boss, now):
    # 막대
    draw_bar(window, to_window(XP_BAR), player.xp / player.xp_needed(), XP_COLOR)
    draw_bar(window, to_window(HP_BAR), player.hp / player.max_hp, HP_COLOR)
    draw_text(window, "small", f"{math.ceil(player.hp)}/{player.max_hp}", HP_BAR.right + 4, HP_BAR.top - 2)
    draw_text(window, "normal", f"Lv {player.level}", 4, 14)

    # 타이머: 10분이 지나면 0에서 멈추고 최종 보스전
    if game_time < GAME_DURATION:
        draw_text(window, "timer", format_time(GAME_DURATION - game_time), UI_W // 2, 5, "midtop")
    else:
        draw_text(window, "timer", "기말고사를 쓰러뜨려라!", UI_W // 2, 5, "midtop", RED)
    draw_text(window, "normal", f"처치 {kills}", UI_W - 4, 5, "topright")

    # 가진 무기 (오른쪽 위): 진화한 무기는 노란색
    y = 16
    for weapon in weapons.values():
        if weapon.evolved:
            draw_text(window, "tiny", weapon.evo_name, UI_W - 4, y, "topright", YELLOW)
        else:
            draw_text(window, "tiny", f"{weapon.name} Lv{weapon.level}", UI_W - 4, y, "topright")
        y += 6
    # 가진 패시브
    y += 2
    for key, level in player.passives.items():
        draw_text(window, "tiny", f"{PASSIVES[key]['name']} Lv{level}", UI_W - 4, y, "topright", GRAY)
        y += 6
    # 켜진 시너지
    y += 2
    for key in sorted(player.synergies):
        draw_text(window, "tiny", SYNERGIES[key]["name"], UI_W - 4, y, "topright", GREEN)
        y += 6

    # 켜져 있는 버프 (왼쪽 아래부터 위로): 아이콘 + 남은 시간
    y = UI_H - 12
    for kind, end in active_buffs(player, now):
        icon = pygame.transform.scale(sprites.load(kind, sprites.ITEM_GRIDS[kind]), (8 * U, 8 * U))
        window.blit(icon, (4 * U, y * U))
        seconds = math.ceil((end - now) / 1000)
        draw_text(window, "small", f"{ITEMS[kind]['name']} {seconds}초", 15, y, color=ITEMS[kind]["color"])
        y -= 11

    # 보스 체력
    if boss is not None:
        draw_bar(window, to_window(BOSS_BAR), boss.hp / boss.max_hp, BOSS_COLOR)
        draw_text(window, "small", boss.name, UI_W // 2, BOSS_BAR.top - 1, "midbottom", BOSS_COLOR)


def draw_player_hp(screen, player, offset):
    """플레이어 발밑의 작은 HP 막대 (다쳤을 때만). 이것만 게임 화면(screen)에 그림"""
    if player.hp < player.max_hp:
        rect = pygame.Rect(0, 0, 12, 2)
        rect.midtop = (player.pos.x - offset.x, player.rect.bottom - offset.y + 2)
        pygame.draw.rect(screen, (15, 15, 20), rect.inflate(2, 2))
        screen.fill((50, 50, 60), rect)
        screen.fill(HP_COLOR, (rect.left, rect.top, round(rect.width * player.hp / player.max_hp), rect.height))


def draw_map_labels(window, labels, offset):
    """건물 이름표. 맵 위의 위치(게임 화면 픽셀)를 UI 칸으로 바꿔서 그림"""
    for text, (x, y) in labels:
        sx, sy = x - offset.x, y - offset.y
        if -80 < sx < WIDTH + 80 and -20 < sy < HEIGHT + 20:
            draw_text(window, "small", text, sx * SCALE / U, sy * SCALE / U, "center", (255, 250, 220))


# ------------------------------------------------------------------
# 레벨업 창
# ------------------------------------------------------------------
def get_option_rects(count):
    """레벨업 선택지 상자 위치들 (UI 칸 기준)"""
    box_w, box_h, gap = 92, 72, 8
    left = (UI_W - (box_w * count + gap * (count - 1))) // 2
    return [pygame.Rect(left + i * (box_w + gap), 58, box_w, box_h) for i in range(count)]


# 카드 색: (배경, 테두리, 꼬리표 글자)
CARD_STYLE = {
    "weapon": ((28, 42, 72), (90, 170, 255), "무기"),
    "passive": ((26, 58, 42), (110, 210, 120), "패시브"),
    "gold": ((90, 70, 20), YELLOW, "진화"),
}
_icons = {}


def card_icon(name):
    """카드에 띄울 아이콘 (16x16 도트를 창에서 48x48로)"""
    if name not in _icons:
        image = sprites.load_file(name) if name else None
        _icons[name] = pygame.transform.scale(image, (image.get_width() * 3, image.get_height() * 3)) if image else None
    return _icons[name]


def draw_levelup(window, options, rerolls):
    draw_text(window, "big", "레벨 업!", UI_W // 2, 24, "midtop", YELLOW)
    draw_text(window, "small", "1, 2, 3 키 또는 클릭으로 선택", UI_W // 2, 42, "midtop")
    for i, (option, rect) in enumerate(zip(options, get_option_rects(len(options)))):
        style = "gold" if option["gold"] else option.get("kind", "weapon")
        background, border, tag = CARD_STYLE[style]
        box = to_window(rect)
        pygame.draw.rect(window, background, box, border_radius=8)
        pygame.draw.rect(window, border, box, 6 if style == "gold" else 4, border_radius=8)
        # 왼쪽 위: 무기/패시브/진화 꼬리표, 오른쪽 위: 번호
        draw_text(window, "tiny", tag, rect.left + 5, rect.top + 4, "topleft", border)
        draw_text(window, "small", f"[{i + 1}]", rect.right - 5, rect.top + 3, "topright", YELLOW)
        icon = card_icon(option.get("icon"))
        if icon:
            center = (box.centerx, box.top + 18 * U)
            pygame.draw.circle(window, tuple(min(255, c + 25) for c in background), center, 8 * U)
            window.blit(icon, icon.get_rect(center=center))
        draw_text(window, "small", option["title"], rect.centerx, rect.top + 31, "midtop",
                  YELLOW if option["gold"] else TEXT_COLOR)
        draw_text(window, "tiny", option["desc"], rect.centerx, rect.top + 46, "midtop", GRAY)
        if option.get("hint"):
            draw_text(window, "tiny", option["hint"], rect.centerx, rect.bottom - 11, "midtop", (230, 200, 110))
    if rerolls > 0:
        draw_text(window, "small", f"R: 다시 뽑기 (남은 횟수 {rerolls})", UI_W // 2, 136, "midtop")
    else:
        draw_text(window, "small", "다시 뽑기 횟수를 모두 사용함", UI_W // 2, 136, "midtop", GRAY)
    draw_text(window, "tiny", "Tab: 진화·시너지 설명 보기", UI_W // 2, 148, "midtop", GRAY)


def small_icon(name, size):
    """설명 화면용 작은 아이콘"""
    key = (name, size)
    if key not in _icons:
        image = sprites.load_file(name)
        _icons[key] = pygame.transform.scale(image, (size, size)) if image else None
    return _icons[key]


def draw_info(window, weapons, player):
    """Tab: 진화·시너지 설명. 왼쪽은 무기 8종의 진화, 오른쪽은 시너지 4종"""
    from weapon import WEAPON_CLASSES   # ui.py가 먼저 불려도 문제없게 여기서 가져옴
    from settings import SYNERGY_LEVEL, EVOLVE_LEVEL
    panel = pygame.Surface(window.get_size(), pygame.SRCALPHA)
    panel.fill((10, 12, 24, 170))   # 글씨가 잘 보이게 한 번 더 어둡게
    window.blit(panel, (0, 0))
    draw_text(window, "big", "진화 · 시너지", UI_W // 2, 6, "midtop", YELLOW)
    # 왼쪽: 진화
    draw_text(window, "small", f"무기 진화 (Lv{EVOLVE_LEVEL}부터)", 10, 24, "topleft", (90, 170, 255))
    y = 34
    for key, weapon_class in WEAPON_CLASSES.items():
        weapon = weapons.get(key)
        icon = small_icon(f"icon_{key}", 8 * U)
        if icon:
            window.blit(icon, (10 * U, y * U))
        if weapon is None:
            status, color = "없음", GRAY
        elif weapon.evolved:
            status, color = "진화 완료", YELLOW
        elif weapon.can_evolve():
            status, color = "진화 가능!", YELLOW
        else:
            status, color = f"Lv{weapon.level}", TEXT_COLOR
        draw_text(window, "tiny", f"{weapon_class.name} → {weapon_class.evo_name}", 21, y - 1, "topleft",
                  TEXT_COLOR if weapon else GRAY)
        draw_text(window, "tiny", weapon_class.evo_desc, 21, y + 5, "topleft", GRAY)
        draw_text(window, "tiny", status, 156, y - 1, "topright", color)
        y += 16
    # 오른쪽: 시너지
    draw_text(window, "small", f"시너지 (두 무기 모두 Lv{SYNERGY_LEVEL} 이상)", 166, 24, "topleft", GREEN)
    y = 34
    for key, info in SYNERGIES.items():
        on = key in player.synergies
        a, b = info["weapons"]
        for i, w in enumerate((a, b)):
            icon = small_icon(f"icon_{w}", 8 * U)
            if icon:
                window.blit(icon, ((166 + i * 10) * U, y * U))
        draw_text(window, "small", info["name"], 189, y - 1, "topleft", GREEN if on else TEXT_COLOR)
        draw_text(window, "tiny", "켜짐" if on else "꺼짐", 310, y - 1, "topright", GREEN if on else GRAY)
        names = f"{WEAPON_CLASSES[a].name} + {WEAPON_CLASSES[b].name}"
        draw_text(window, "tiny", names, 189, y + 6, "topleft", GRAY)
        draw_text(window, "tiny", info["desc"], 189, y + 12, "topleft", (230, 200, 110))
        y += 30
    draw_text(window, "tiny", "Tab / ESC / Enter: 닫기", UI_W // 2, 172, "midtop", GRAY)


def draw_boss_intro(window, boss, elapsed):
    """보스 등장 화면: 왼쪽에 보스 그림, 오른쪽에 이름·소개·공격 패턴·공략 팁"""
    from settings import BOSS_INFO
    info = BOSS_INFO.get(boss.kind, {"title": "보스", "intro": "", "attacks": [], "tip": ""})
    t = min(1, elapsed / 250)                       # 0.25초 동안 위에서 미끄러져 내려옴
    drop = int((1 - t) * 20)
    panel = pygame.Rect(30, 32 - drop, 260, 112)
    box = to_window(panel)
    pygame.draw.rect(window, (30, 16, 22), box, border_radius=10)
    pygame.draw.rect(window, RED, box, 5, border_radius=10)
    # 위쪽 띠: WARNING
    band = pygame.Rect(box.left, box.top, box.width, 12 * U)
    pygame.draw.rect(window, (150, 24, 32), band, border_top_left_radius=10, border_top_right_radius=10)
    blink = (elapsed // 300) % 2 == 0
    draw_text(window, "small", f"⚠ {info['title']} 등장 ⚠", UI_W // 2, panel.top + 2, "midtop",
              YELLOW if blink else (255, 255, 255))
    # 보스 그림 (크게)
    image = boss.frames[0]
    scale = min(56 * U / image.get_width(), 64 * U / image.get_height())
    big = pygame.transform.scale(image, (int(image.get_width() * scale), int(image.get_height() * scale)))
    center = (box.left + 38 * U, box.top + 60 * U)
    pygame.draw.circle(window, (70, 26, 34), center, 32 * U)
    window.blit(big, big.get_rect(center=center))
    # 글
    x = panel.left + 78
    draw_text(window, "big", boss.name, x, panel.top + 16, "topleft", RED)
    draw_text(window, "tiny", info["intro"], x, panel.top + 32, "topleft", GRAY)
    draw_text(window, "small", "공격 패턴", x, panel.top + 44, "topleft", YELLOW)
    y = panel.top + 54
    for attack in info["attacks"]:
        draw_text(window, "tiny", f"• {attack}", x + 2, y, "topleft")
        y += 8
    draw_text(window, "small", "공략", x, y + 3, "topleft", GREEN)
    draw_text(window, "tiny", info["tip"], x + 2, y + 13, "topleft")
    if elapsed > 800:
        draw_text(window, "small", "아무 키나 누르면 시작", UI_W // 2, panel.bottom + 6, "midtop",
                  TEXT_COLOR if blink else GRAY)


BANNER_TIME = 2200   # 진화·시너지 알림이 떠 있는 시간 (ms)


def draw_banner(window, banner, now):
    """진화: 금빛 아이콘이 커지며 등장 / 시너지: 두 무기 아이콘이 양쪽에서 날아와 합쳐짐"""
    t = (now - banner["start"]) / BANNER_TIME          # 0 -> 1
    color = YELLOW if banner["kind"] == "evolve" else GREEN
    cx, cy = WINDOW_W // 2, 34 * U
    pop = min(1, t / 0.12)                              # 처음 0.26초 동안 튀어나옴
    light_color = (120, 90, 20) if banner["kind"] == "evolve" else (40, 110, 50)
    radius = int(26 * U * (0.6 + 0.4 * pop))
    glow = pygame.Surface((radius * 2, radius * 2))
    for i in range(radius, 0, -2):
        k = (1 - i / radius) ** 2
        pygame.draw.circle(glow, tuple(int(c * k) for c in light_color), (radius, radius), i)
    window.blit(glow, glow.get_rect(center=(cx, cy)), special_flags=pygame.BLEND_RGB_ADD)   # 뒤에 은은한 빛
    icons = [card_icon(name) for name in banner["icons"]]
    if banner["kind"] == "synergy" and len(icons) == 2:
        slide = min(1, t / 0.3)
        gap = int((60 - 34 * slide) * U)                 # 양쪽에서 가운데로
        for icon, side in zip(icons, (-1, 1)):
            if icon:
                window.blit(icon, icon.get_rect(center=(cx + side * gap // 2, cy)))
        if slide >= 1:
            draw_text(window, "big", "+", UI_W // 2, 34, "center", GREEN)
    elif icons and icons[0]:
        size = int(icons[0].get_width() * (0.5 + 0.8 * pop))
        icon = pygame.transform.scale(icons[0], (size, size))
        window.blit(icon, icon.get_rect(center=(cx, cy)))
    draw_text(window, "big", banner["title"], UI_W // 2, 48, "midtop", color)
    draw_text(window, "small", banner["desc"], UI_W // 2, 64, "midtop")


def draw_chest(window, gained):
    """보물상자를 열었을 때: 강화된 것들 목록"""
    draw_text(window, "big", "A+ 성적표!", UI_W // 2, 30, "midtop", YELLOW)
    draw_text(window, "small", f"강화 {len(gained)}개 획득", UI_W // 2, 48, "midtop")
    y = 64
    for title in gained:
        draw_text(window, "normal", title, UI_W // 2, y, "midtop", YELLOW if title.startswith("진화") else TEXT_COLOR)
        y += 12
    draw_text(window, "small", "아무 키나 눌러 계속", UI_W // 2, y + 8, "midtop", GRAY)


# ------------------------------------------------------------------
# 시작 화면 / 끝 화면
# ------------------------------------------------------------------
def draw_title(window):
    draw_text(window, "title", "부경대 서바이벌", UI_W // 2, 22, "midtop", YELLOW)
    draw_text(window, "normal", "10분을 버티고, 마지막에 나오는 기말고사를 쓰러뜨려라!", UI_W // 2, 52, "midtop")
    draw_text(window, "tiny", "WASD / 방향키: 이동    공격: 자동    Tab: 진화·시너지 설명    ESC: 일시정지    F11: 전체화면", UI_W // 2, 173, "midtop", GRAY)


# ------------------------------------------------------------------
# 메뉴 (시작 화면, 일시정지, 소리 설정이 같이 씀)
# ------------------------------------------------------------------
def get_menu_rects(count):
    """메뉴 항목 상자 위치들 (UI 칸 기준). 화면 가운데에 세로로 나열"""
    box_w, box_h, gap = 130, 20, 5
    if count > 3:  # 항목이 많으면 조금 낮은 상자로
        box_h, gap = 18, 4
    return [pygame.Rect((UI_W - box_w) // 2, 76 + i * (box_h + gap), box_w, box_h) for i in range(count)]


def draw_menu(window, items, selected, values=None):
    """메뉴 그리기. selected번 항목은 노란 테두리.
    values: 항목별 볼륨(0.0~1.0) 목록. None이 아닌 항목은 이름 옆에 볼륨 막대를 그림"""
    for i, (text, rect) in enumerate(zip(items, get_menu_rects(len(items)))):
        box = to_window(rect)
        pygame.draw.rect(window, (70, 70, 100) if i == selected else (40, 40, 60), box)
        pygame.draw.rect(window, YELLOW if i == selected else GRAY, box, 4 if i == selected else 2)
        color = YELLOW if i == selected else TEXT_COLOR
        value = values[i] if values else None
        if value is None:
            draw_text(window, "normal", text, rect.centerx, rect.centery, "center", color)
        else:
            draw_text(window, "small", text, rect.left + 6, rect.centery, "midleft", color)
            bar = pygame.Rect(rect.left + 44, rect.centery - 2, 56, 4)
            draw_bar(window, to_window(bar), value, XP_COLOR)
            draw_text(window, "small", f"{round(value * 100)}%", rect.right - 5, rect.centery, "midright", color)
    if values:
        draw_text(window, "tiny", "볼륨: A / D 또는 ← → (막대 왼쪽·오른쪽 클릭도 가능)      F11: 전체화면", UI_W // 2, 166, "midtop", GRAY)
    else:
        y = 166 if len(items) > 3 else 150
        draw_text(window, "tiny", "W / S: 이동    Enter: 선택    마우스 클릭도 가능", UI_W // 2, y, "midtop", GRAY)


def draw_end(window, state, game_time, kills, level, difficulty):
    if state == "gameover":
        draw_text(window, "big", "게임 오버", UI_W // 2, 56, "midtop", RED)
        summary = f"생존 시간 {format_time(game_time)}    처치 {kills}    레벨 {level}"
    else:
        draw_text(window, "big", "클리어!", UI_W // 2, 56, "midtop", YELLOW)
        summary = f"기말고사 격파!    걸린 시간 {format_time(game_time)}    처치 {kills}    레벨 {level}"
    draw_text(window, "normal", summary, UI_W // 2, 82, "midtop")
    draw_text(window, "small", f"난이도: {difficulty}", UI_W // 2, 96, "midtop", GRAY)
    draw_text(window, "normal", "R: 다시 시작      ESC: 시작 화면으로", UI_W // 2, 112, "midtop", GRAY)
