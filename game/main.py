# main.py - 게임의 중심. 다른 파일을 불러와서 게임을 돌림
# 1주차: 핵심 루프 (이동, 적 생성·추적, 자동 공격, 충돌, 10분 타이머)
# 2주차: 경험치와 레벨업 선택창, 무기 2종 추가, 버프 아이템 6종, 시간별 난이도
# 3주차: UI(HP·경험치바, 타이머), 도트 스프라이트와 부경대 맵, 효과음, 보스
#
# 시간은 pygame.time.get_ticks()(실제 시계) 대신 game_time을 씀.
# game_time은 게임이 진행 중일 때만 흐르기 때문에, 레벨업 창이 떠 있는 동안
# 타이머·버프·무기 쿨타임이 모두 같이 멈춤.
#
# 파일 구성
#   settings.py  숫자 모음 (밸런스 조절)     campus.py  맵 그리기
#   player.py    플레이어                    sprites.py 도트 그림
#   enemy.py     적, 보스                    sound.py   효과음
#   weapon.py    무기 3종                    ui.py      화면 정보, 시작/끝 화면
#   item.py      경험치 보석, 버프 아이템    levelup.py 레벨업 선택지
import math
import random

import pygame
from settings import (
    WIDTH,
    HEIGHT,
    SCALE,
    FPS,
    BG_COLOR,
    GAME_DURATION,
    START_MINUTE,
    SPAWN_INTERVAL_START,
    SPAWN_INTERVAL_MIN,
    SPAWN_INTERVAL_DECREASE,
    ENEMY_HP_GROWTH,
    SPAWN_DISTANCE,
    MAX_ENEMIES,
    ENEMY_TYPES,
    BOSS_KIND,
    BOSS_MINUTE,
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
import campus
import levelup
import sound
import ui


# ------------------------------------------------------------------
# 위치 도우미
# ------------------------------------------------------------------
def random_point_around(center, distance, play_area):
    """center에서 distance만큼 떨어진 무작위 위치. 맵 안쪽이 나올 때까지 몇 번 다시 뽑고,
    그래도 안 되면 맵 안쪽으로 끌어당김"""
    for _ in range(10):
        angle = random.uniform(0, math.tau)
        pos = center + pygame.Vector2(distance, 0).rotate_rad(angle)
        if play_area.collidepoint(pos):
            return pos
    pos.x = max(play_area.left, min(play_area.right - 1, pos.x))
    pos.y = max(play_area.top, min(play_area.bottom - 1, pos.y))
    return pos


# ------------------------------------------------------------------
# 난이도 (계획서 4번)
# ------------------------------------------------------------------
def get_spawn_interval(minutes):
    """생성 간격 = max(0.3초, 1.5초 - 0.12초 x 경과 분)"""
    return max(
        SPAWN_INTERVAL_MIN, SPAWN_INTERVAL_START - SPAWN_INTERVAL_DECREASE * minutes
    )


def get_hp_multiplier(minutes):
    """적 체력 = 기본 x (1 + 0.15 x 경과 분)"""
    return 1 + ENEMY_HP_GROWTH * minutes


def spawn_enemy(player_pos, minutes, play_area):
    """플레이어 주변 화면 밖에, 지금 시간에 나올 수 있는 적 중 하나를 생성"""
    kinds = [
        kind
        for kind, info in ENEMY_TYPES.items()
        if info["from_minute"] is not None and minutes >= info["from_minute"]
    ]
    pos = random_point_around(player_pos, SPAWN_DISTANCE, play_area)
    return Enemy(pos.x, pos.y, random.choice(kinds), get_hp_multiplier(minutes))


def spawn_boss(player_pos, minutes, play_area):
    pos = random_point_around(player_pos, 150, play_area)
    return Enemy(pos.x, pos.y, BOSS_KIND, get_hp_multiplier(minutes))


# ------------------------------------------------------------------
# 버프 아이템
# ------------------------------------------------------------------
def spawn_item(player_pos, play_area):
    """플레이어 근처 무작위 위치에 무작위 버프 아이템 생성"""
    distance = random.uniform(ITEM_SPAWN_MIN_DISTANCE, ITEM_SPAWN_MAX_DISTANCE)
    pos = random_point_around(player_pos, distance, play_area)
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
def get_camera_offset(player_pos, map_size):
    """플레이어가 화면 가운데 오도록 하되, 맵 바깥은 안 보이게"""
    map_w, map_h = map_size
    x = round(player_pos.x - WIDTH / 2)
    y = round(player_pos.y - HEIGHT / 2)
    return pygame.Vector2(
        max(0, min(map_w - WIDTH, x)),
        max(0, min(map_h - HEIGHT, y)),
    )


def draw_sprite(screen, sprite, offset):
    """월드 좌표의 스프라이트를 카메라 기준으로 그리기"""
    screen.blit(sprite.image, pygame.Vector2(sprite.rect.topleft) - offset)


# ------------------------------------------------------------------
# 게임
# ------------------------------------------------------------------
def main():
    pygame.init()
    window = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE))
    pygame.display.set_caption("부경대 서바이벌")
    screen = pygame.Surface((WIDTH, HEIGHT))  # 작은 화면에 그린 뒤 확대
    clock = pygame.time.Clock()
    sound.init()
    ui.init()
    map_surface, play_area, map_labels = campus.load_map()

    running = True
    restart = True  # True면 게임을 처음 상태로 다시 세팅
    first_game = True
    while running:
        dt = clock.tick(FPS)  # 지난 프레임부터 흐른 시간 (ms)

        # 0. 새 게임 세팅 (처음 시작할 때와 R로 재시작할 때)
        if restart:
            player = Player(*play_area.center)
            weapons = {"pen": Pen()}  # 처음엔 볼펜만. 레벨업으로 "book", "coffee" 추가
            enemies = pygame.sprite.Group()
            gems = pygame.sprite.Group()
            items = pygame.sprite.Group()
            boss = None
            game_time = START_MINUTE * 60000
            last_spawn = game_time
            last_item_spawn = game_time
            kills = 0
            # "title" / "playing" / "levelup" / "gameover" / "clear"
            state = "title" if first_game else "playing"
            options = []  # 레벨업 선택지
            message = ""  # 화면 위에 잠깐 뜨는 글자 (아이템, 보스 등장)
            message_color = ui.YELLOW
            message_end = 0
            restart = False
            first_game = False

        # 1. 이벤트 처리
        chosen = None  # 레벨업에서 고른 번호 (0, 1, 2)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif state == "title":
                    state = "playing"
                elif event.key == pygame.K_r and state in ("gameover", "clear"):
                    restart = True
                elif state == "levelup" and event.key in (
                    pygame.K_1,
                    pygame.K_2,
                    pygame.K_3,
                ):
                    chosen = event.key - pygame.K_1
            elif event.type == pygame.MOUSEBUTTONDOWN and state == "levelup":
                mouse = (event.pos[0] // SCALE, event.pos[1] // SCALE)  # 창 좌표 -> 게임 좌표
                for i, rect in enumerate(ui.get_option_rects(len(options))):
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
                enemies.add(spawn_enemy(player.pos, minutes, play_area))
                last_spawn = now

            # 보스 등장 (한 번만)
            if boss is None and minutes >= BOSS_MINUTE:
                boss = spawn_boss(player.pos, minutes, play_area)
                enemies.add(boss)
                message, message_color, message_end = "기말고사 등장!", ui.RED, now + 3000
                sound.play("boss")

            # 버프 아이템 생성 (30초마다)
            if now - last_item_spawn >= ITEM_SPAWN_INTERVAL:
                items.add(spawn_item(player.pos, play_area))
                last_item_spawn = now

            player.update(now, play_area)
            enemies.update(player.pos)

            # 무기 공격 -> 죽은 적 자리에 경험치 보석
            attack_mult = player.attack_speed_multiplier(now)
            for weapon in weapons.values():
                for enemy in weapon.update(now, player.pos, enemies, attack_mult):
                    kills += 1
                    gems.add(ExpGem(enemy.pos.x, enemy.pos.y, enemy.xp))
                    sound.play("kill")
                    if enemy is boss:
                        message, message_color, message_end = "기말고사 격파!", ui.YELLOW, now + 3000

            # 경험치 보석 줍기
            gems.update(player.pos)
            for gem in list(gems):
                if player.pos.distance_to(gem.pos) < GEM_COLLECT_DISTANCE:
                    player.gain_xp(gem.value, now)
                    gem.kill()
                    sound.play("gem")

            # 버프 아이템 줍기
            for item in pygame.sprite.spritecollide(player, items, True):
                apply_item(item.kind, player, gems, now)
                info = ITEMS[item.kind]
                message, message_color, message_end = f"{info['name']}!  {info['desc']}", ui.YELLOW, now + 2000
                sound.play("item")

            # 적 ↔ 플레이어: 닿으면 플레이어가 데미지를 받음
            enemy_hit = pygame.sprite.spritecollideany(player, enemies)
            if enemy_hit and player.take_damage(enemy_hit.damage, now):
                sound.play("hurt")

            # 게임 끝 / 레벨업 판정
            if player.is_dead():
                state = "gameover"
                sound.play("gameover")
            elif game_time >= GAME_DURATION:
                state = "clear"
                sound.play("clear")
            elif player.can_level_up():
                state = "levelup"
                options = levelup.get_options(player, weapons)
                sound.play("levelup")

        now = game_time

        # 3. 그리기 - 게임 화면 (작은 screen에 그림)
        offset = get_camera_offset(player.pos, map_surface.get_size())
        screen.fill(BG_COLOR)
        screen.blit(map_surface, (0, 0), pygame.Rect(offset, (WIDTH, HEIGHT)))  # 맵에서 보이는 부분만
        for item in items:
            item.draw(screen, offset, now)
        for gem in gems:
            draw_sprite(screen, gem, offset)
        for enemy in enemies:
            draw_sprite(screen, enemy, offset)

        # 학생증 무적이면 플레이어 주변에 파란 원
        if player.has_buff("student_id", now):
            pygame.draw.circle(screen, ITEMS["student_id"]["color"], player.pos - offset, 9, 1)
        # 맞은 직후에는 깜빡이게 (0.1초마다 보였다 안 보였다)
        if not (player.is_blinking(now) and (now // 100) % 2 == 0):
            draw_sprite(screen, player, offset)
        for weapon in weapons.values():
            weapon.draw(screen, offset)
        ui.draw_player_hp(screen, player, offset)

        if state == "playing":
            ui.draw_hud_screen(screen, player, boss, now)
        else:
            ui.draw_dark_overlay(screen)
        if state == "levelup":
            ui.draw_levelup_screen(screen, options)

        pygame.transform.scale(screen, window.get_size(), window)

        # 4. 그리기 - 글자 (확대된 window에 직접 그림)
        if state == "playing":
            ui.draw_map_labels(window, map_labels, offset)
            ui.draw_hud_text(window, player, kills, game_time, boss, now)
            if now < message_end:
                ui.draw_text(window, "normal", message, WIDTH // 2, 24, "midtop", message_color)
        elif state == "title":
            ui.draw_title_text(window, pygame.time.get_ticks())
        elif state == "levelup":
            ui.draw_levelup_text(window, options)
        else:
            ui.draw_end_text(window, state, game_time, kills, player.level)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
