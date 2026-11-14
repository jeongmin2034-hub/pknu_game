# main.py - 게임의 중심. 다른 파일을 불러와서 게임을 돌림
# 1주차: 핵심 루프 (이동, 적 생성·추적, 자동 공격, 충돌, 10분 타이머)
# 2주차: 경험치와 레벨업 선택창, 무기 2종 추가, 버프 아이템 6종, 시간별 난이도
#
# 시간은 pygame.time.get_ticks()(실제 시계) 대신 game_time을 씀.
# game_time은 게임이 진행 중일 때만 흐르기 때문에, 레벨업 창이 떠 있는 동안
# 타이머·버프·무기 쿨타임이 모두 같이 멈춤.
import math
import random

import pygame
from settings import (
    WIDTH,
    HEIGHT,
    SCALE,
    FPS,
    FONT_NAME,
    BG_COLOR,
    GRID_COLOR,
    GRID_SIZE,
    GAME_DURATION,
    SPAWN_INTERVAL_START,
    SPAWN_INTERVAL_MIN,
    SPAWN_INTERVAL_DECREASE,
    ENEMY_HP_GROWTH,
    SPAWN_DISTANCE,
    MAX_ENEMIES,
    ENEMY_TYPES,
    GEM_COLLECT_DISTANCE,
    ITEMS,
    ITEM_SPAWN_INTERVAL,
    ITEM_SPAWN_MIN_DISTANCE,
    ITEM_SPAWN_MAX_DISTANCE,
    MEAL_HEAL,
)
from player import Player
from enemy import Enemy
from weapon import Pen
from item import ExpGem, BuffItem
import levelup

TEXT_COLOR = (230, 230, 230)
YELLOW = (250, 220, 90)


# ------------------------------------------------------------------
# 난이도 (계획서 4번)
# ------------------------------------------------------------------
def get_spawn_interval(minutes):
    """생성 간격 = max(0.3초, 1.5초 - 0.12초 x 경과 분)"""
    return max(
        SPAWN_INTERVAL_MIN, SPAWN_INTERVAL_START - SPAWN_INTERVAL_DECREASE * minutes
    )


def spawn_enemy(player_pos, minutes):
    """플레이어 주변 화면 밖에, 지금 시간에 나올 수 있는 적 중 하나를 생성"""
    kinds = [k for k, info in ENEMY_TYPES.items() if minutes >= info["from_minute"]]
    hp_multiplier = (
        1 + ENEMY_HP_GROWTH * minutes
    )  # 적 체력 = 기본 x (1 + 0.15 x 경과 분)
    angle = random.uniform(0, math.tau)
    pos = player_pos + pygame.Vector2(SPAWN_DISTANCE, 0).rotate_rad(angle)
    return Enemy(pos.x, pos.y, random.choice(kinds), hp_multiplier)


# ------------------------------------------------------------------
# 버프 아이템
# ------------------------------------------------------------------
def spawn_item(player_pos):
    """플레이어 근처 무작위 위치에 무작위 버프 아이템 생성"""
    angle = random.uniform(0, math.tau)
    distance = random.uniform(ITEM_SPAWN_MIN_DISTANCE, ITEM_SPAWN_MAX_DISTANCE)
    pos = player_pos + pygame.Vector2(distance, 0).rotate_rad(angle)
    return BuffItem(pos.x, pos.y, random.choice(list(ITEMS)))


def apply_item(kind, player, gems, now):
    """주운 아이템의 효과 적용"""
    if kind == "meal":
        player.heal(MEAL_HEAL)
    elif kind == "magnet":
        for gem in gems:
            gem.attracted = True  # 맵의 보석 전부 플레이어에게 날아옴
    else:
        player.add_buff(kind, ITEMS[kind]["duration"], now)


# ------------------------------------------------------------------
# 그리기 도우미
# ------------------------------------------------------------------
def get_camera_offset(player_pos):
    """플레이어가 화면 가운데 오도록 하는 카메라 위치"""
    return pygame.Vector2(
        round(player_pos.x - WIDTH / 2), round(player_pos.y - HEIGHT / 2)
    )


def draw_grid(screen, offset):
    """움직이는 게 보이도록 바닥에 격자 그리기"""
    for x in range(-int(offset.x) % GRID_SIZE, WIDTH, GRID_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT))
    for y in range(-int(offset.y) % GRID_SIZE, HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y))


def draw_sprite(screen, sprite, offset):
    """월드 좌표의 스프라이트를 카메라 기준으로 그리기"""
    screen.blit(sprite.image, pygame.Vector2(sprite.rect.topleft) - offset)


def draw_dark_overlay(screen):
    """게임 화면을 어둡게 덮기 (레벨업/게임 끝 화면 뒤)"""
    dark = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dark.fill((0, 0, 0, 150))
    screen.blit(dark, (0, 0))


def draw_text(window, font, text, x, y, anchor="topleft", color=TEXT_COLOR):
    """글자는 확대된 창(window)에 직접 그림 -> 작은 화면에서 키우는 것보다 한글이 선명함.
    x, y는 게임 화면(320x180) 기준 좌표. anchor: "topleft", "midtop", "topright" 등"""
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect(**{anchor: (x * SCALE, y * SCALE)})
    window.blit(text_surface, rect)


def format_time(ms):
    """밀리초를 '분:초' 글자로 바꾸기 (예: 600000 -> '10:00')"""
    seconds = int(max(0, ms)) // 1000
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def get_option_rects(count):
    """레벨업 선택지 상자 위치들 (게임 화면 기준)"""
    box_w, box_h, gap = 92, 60, 8
    left = (WIDTH - (box_w * count + gap * (count - 1))) // 2
    return [
        pygame.Rect(left + i * (box_w + gap), 62, box_w, box_h) for i in range(count)
    ]


# ------------------------------------------------------------------
# 게임
# ------------------------------------------------------------------
def main():
    pygame.init()
    window = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE))
    pygame.display.set_caption("부경대 서바이벌")
    screen = pygame.Surface((WIDTH, HEIGHT))  # 작은 화면에 그린 뒤 확대
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(FONT_NAME, 7 * SCALE)
    small_font = pygame.font.SysFont(FONT_NAME, 6 * SCALE)
    big_font = pygame.font.SysFont(FONT_NAME, 12 * SCALE, bold=True)

    running = True
    restart = True  # True면 게임을 처음 상태로 다시 세팅
    while running:
        dt = clock.tick(FPS)  # 지난 프레임부터 흐른 시간 (ms)

        # 0. 새 게임 세팅 (처음 시작할 때와 R로 재시작할 때)
        if restart:
            player = Player(0, 0)
            weapons = {"pen": Pen()}  # 처음엔 볼펜만. 레벨업으로 "book", "coffee" 추가
            enemies = pygame.sprite.Group()
            gems = pygame.sprite.Group()
            items = pygame.sprite.Group()
            game_time = 0
            last_spawn = 0
            last_item_spawn = 0
            kills = 0
            state = "playing"  # "playing" / "levelup" / "gameover" / "clear"
            options = []  # 레벨업 선택지
            message = ""  # 아이템 주웠을 때 잠깐 뜨는 글자
            message_end = 0
            restart = False

        # 1. 이벤트 처리
        chosen = None  # 레벨업에서 고른 번호 (0, 1, 2)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r and state in ("gameover", "clear"):
                    restart = True
                elif state == "levelup" and event.key in (
                    pygame.K_1,
                    pygame.K_2,
                    pygame.K_3,
                ):
                    chosen = event.key - pygame.K_1
            elif event.type == pygame.MOUSEBUTTONDOWN and state == "levelup":
                mouse = (
                    event.pos[0] // SCALE,
                    event.pos[1] // SCALE,
                )  # 창 좌표 -> 게임 좌표
                for i, rect in enumerate(get_option_rects(len(options))):
                    if rect.collidepoint(mouse):
                        chosen = i

        # 레벨업 선택 처리
        if chosen is not None and chosen < len(options):
            options[chosen]["apply"]()
            player.level_up()
            if player.can_level_up():  # 경험치가 많이 남았으면 한 번 더
                options = levelup.get_options(player, weapons)
            else:
                state = "playing"

        # 2. 업데이트 (게임 중일 때만 움직임)
        if state == "playing":
            game_time += dt
            now = game_time
            minutes = now / 60000

            # 적 생성 (시간이 지날수록 자주)
            if (
                now - last_spawn >= get_spawn_interval(minutes)
                and len(enemies) < MAX_ENEMIES
            ):
                enemies.add(spawn_enemy(player.pos, minutes))
                last_spawn = now

            # 버프 아이템 생성 (30초마다)
            if now - last_item_spawn >= ITEM_SPAWN_INTERVAL:
                items.add(spawn_item(player.pos))
                last_item_spawn = now

            player.update(now)
            enemies.update(player.pos)

            # 무기 공격 -> 죽은 적 자리에 경험치 보석
            attack_mult = player.attack_speed_multiplier(now)
            for weapon in weapons.values():
                for enemy in weapon.update(now, player.pos, enemies, attack_mult):
                    kills += 1
                    gems.add(ExpGem(enemy.pos.x, enemy.pos.y, enemy.xp))

            # 경험치 보석 줍기
            gems.update(player.pos)
            for gem in list(gems):
                if player.pos.distance_to(gem.pos) < GEM_COLLECT_DISTANCE:
                    player.gain_xp(gem.value, now)
                    gem.kill()

            # 버프 아이템 줍기
            for item in pygame.sprite.spritecollide(player, items, True):
                apply_item(item.kind, player, gems, now)
                info = ITEMS[item.kind]
                message = f"{info['name']}!  {info['desc']}"
                message_end = now + 2000

            # 적 ↔ 플레이어: 닿으면 플레이어가 데미지를 받음
            enemy_hit = pygame.sprite.spritecollideany(player, enemies)
            if enemy_hit:
                player.take_damage(enemy_hit.damage, now)

            # 게임 끝 / 레벨업 판정
            if player.is_dead():
                state = "gameover"
            elif game_time >= GAME_DURATION:
                state = "clear"
            elif player.can_level_up():
                state = "levelup"
                options = levelup.get_options(player, weapons)

        now = game_time

        # 3. 그리기 - 게임 화면 (작은 screen에 그림)
        offset = get_camera_offset(player.pos)
        screen.fill(BG_COLOR)
        draw_grid(screen, offset)
        for item in items:
            draw_sprite(screen, item, offset)
        for gem in gems:
            draw_sprite(screen, gem, offset)
        for enemy in enemies:
            draw_sprite(screen, enemy, offset)
        for weapon in weapons.values():
            weapon.draw(screen, offset)

        # 학생증 무적이면 플레이어 주변에 파란 원
        if player.has_buff("student_id", now):
            pygame.draw.circle(
                screen, ITEMS["student_id"]["color"], player.pos - offset, 8, 1
            )
        # 맞은 직후에는 깜빡이게 (0.1초마다 보였다 안 보였다)
        if not (player.is_blinking(now) and (now // 100) % 2 == 0):
            draw_sprite(screen, player, offset)

        option_rects = get_option_rects(len(options))
        if state != "playing":
            draw_dark_overlay(screen)
        if state == "levelup":
            for rect in option_rects:
                pygame.draw.rect(screen, (40, 40, 60), rect)
                pygame.draw.rect(screen, YELLOW, rect, 1)

        pygame.transform.scale(screen, window.get_size(), window)

        # 4. 그리기 - 글자 (확대된 window에 직접 그림)
        draw_text(window, font, f"HP {player.hp}/{player.max_hp}", 4, 3)
        draw_text(
            window,
            font,
            f"Lv {player.level}   XP {player.xp}/{player.xp_needed()}",
            4,
            12,
        )
        draw_text(
            window,
            font,
            format_time(GAME_DURATION - game_time),
            WIDTH // 2,
            3,
            "midtop",
        )
        draw_text(window, font, f"처치 {kills}", WIDTH - 4, 3, "topright")

        # 켜져 있는 버프와 남은 시간 (왼쪽 아래)
        y = HEIGHT - 10
        for kind, end in player.buffs.items():
            if end > now:
                draw_text(
                    window,
                    small_font,
                    f"{ITEMS[kind]['name']} {math.ceil((end - now) / 1000)}초",
                    4,
                    y,
                    color=ITEMS[kind]["color"],
                )
                y -= 8

        if now < message_end:
            draw_text(window, font, message, WIDTH // 2, 28, "midtop", YELLOW)

        if state == "levelup":
            draw_text(window, big_font, "레벨 업!", WIDTH // 2, 30, "midtop", YELLOW)
            draw_text(
                window,
                small_font,
                "1, 2, 3 키 또는 클릭으로 선택",
                WIDTH // 2,
                46,
                "midtop",
            )
            for i, (option, rect) in enumerate(zip(options, option_rects)):
                draw_text(
                    window,
                    small_font,
                    f"[{i + 1}]",
                    rect.centerx,
                    rect.top + 6,
                    "midtop",
                    YELLOW,
                )
                draw_text(
                    window,
                    small_font,
                    option["title"],
                    rect.centerx,
                    rect.top + 20,
                    "midtop",
                )
                draw_text(
                    window,
                    small_font,
                    option["desc"],
                    rect.centerx,
                    rect.top + 36,
                    "midtop",
                    (170, 170, 190),
                )
        elif state == "gameover":
            draw_text(
                window, big_font, "게임 오버", WIDTH // 2, 60, "midtop", (240, 90, 90)
            )
            draw_text(
                window,
                font,
                f"생존 시간 {format_time(game_time)}   처치 {kills}   레벨 {player.level}",
                WIDTH // 2,
                84,
                "midtop",
            )
            draw_text(
                window, font, "R: 다시 시작    ESC: 종료", WIDTH // 2, 104, "midtop"
            )
        elif state == "clear":
            draw_text(window, big_font, "클리어!", WIDTH // 2, 60, "midtop", YELLOW)
            draw_text(
                window,
                font,
                f"10분 생존 성공   처치 {kills}   레벨 {player.level}",
                WIDTH // 2,
                84,
                "midtop",
            )
            draw_text(
                window, font, "R: 다시 시작    ESC: 종료", WIDTH // 2, 104, "midtop"
            )

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
