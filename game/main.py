# main.py - 게임의 중심. 다른 파일을 불러와서 게임을 돌림
#
# 게임 흐름: 10분 동안 버팀 (3분, 7분에 중간보스) -> 10분에 최종 보스 "기말고사" 등장
#            -> 기말고사를 쓰러뜨리면 클리어
#
# 시간은 pygame.time.get_ticks()(실제 시계) 대신 game_time을 씀.
# game_time은 게임이 진행 중일 때만 흐르기 때문에, 레벨업 창이 떠 있는 동안
# 타이머·버프·무기 쿨타임이 모두 같이 멈춤.
#
# 파일 구성
#   settings.py  숫자 모음 (밸런스 조절)       campus.py  맵 그리기
#   player.py    플레이어, 패시브              sprites.py 도트 그림
#   enemy.py     적, 보스                      sound.py   효과음, 배경음악
#   weapon.py    무기 8종, 진화, 시너지        ui.py      화면 정보, 시작/끝 화면
#   item.py      경험치 보석, 버프, 보물상자   levelup.py 레벨업 선택지, 보물상자 열기
#
# 화면(state): title(시작 화면) -> playing(게임) -> gameover / clear
#              ESC를 누르면 pause(일시정지), 메뉴에서 settings(설정: 소리, 전체화면)
#              F11: 전체화면
import math
import random

import pygame
from settings import (
    WIDTH,
    HEIGHT,
    WINDOW_W,
    WINDOW_H,
    FPS,
    BG_COLOR,
    GAME_DURATION,
    START_MINUTE,
    DIFFICULTIES,
    DEFAULT_DIFFICULTY,
    SPAWN_INTERVAL,
    SPAWN_BASE,
    SPAWN_PER_MINUTE,
    ENEMY_HP_GROWTH,
    SPAWN_DISTANCE,
    RECYCLE_DISTANCE,
    MAX_ENEMIES,
    SWARM_CHANCE,
    STUCK_DISTANCE,
    RUSH_CHANCE,
    RUSH_SIZE,
    ENEMY_TYPES,
    BOSS_SCHEDULE,
    FINAL_BOSS,
    GEM_COLLECT_DISTANCE,
    MAX_GEMS,
    REROLL_COUNT,
    LEVELUP_BLAST_RADIUS,
    LEVELUP_BLAST_POWER,
    LEVELUP_SHIELD_TIME,
    ITEMS,
    ITEM_SPAWN_INTERVAL,
    ITEM_SPAWN_MIN_DISTANCE,
    ITEM_SPAWN_MAX_DISTANCE,
    MEAL_HEAL,
    SYNERGIES,
)
from player import Player
from enemy import Enemy, Hazard
from weapon import Pen, active_synergies
from item import ExpGem, BuffItem, Chest
import campus
import levelup
import sound
import ui
import vfx


# 메뉴 항목들
TITLE_MENU = ["게임 시작", "난이도", "설정", "프로그램 종료"]
PAUSE_MENU = ["계속하기", "효과 설명", "설정", "현재 게임 종료"]
SETTINGS_MENU = ["효과음", "배경음악", "전체화면", "뒤로"]
VOLUME_KINDS = ["sfx", "bgm"]  # 소리 설정 메뉴의 0번, 1번 항목이 조절하는 볼륨
VOLUME_STEP = 0.1


def toggle_fullscreen(fullscreen):
    """전체화면 <-> 창 화면 바꾸기. 바뀐 뒤의 상태(True = 전체화면)를 돌려줌.
    전체화면을 못 쓰는 환경이면 아무 일도 안 하고 원래 상태 그대로"""
    try:
        pygame.display.toggle_fullscreen()
        return not fullscreen
    except pygame.error:
        return fullscreen


# ------------------------------------------------------------------
# 메뉴 조작
# ------------------------------------------------------------------
def read_menu_event(event, index, count):
    """메뉴에서 키보드·마우스 입력 읽기.
    돌려주는 값: (선택된 번호, 결정했는지, 좌우 방향 -1/0/1)
      위아래(W/S): 선택 이동    Enter/Space/클릭: 결정    좌우(A/D): 볼륨 조절
      마우스로 항목의 왼쪽 절반을 누르면 -1, 오른쪽 절반을 누르면 +1"""
    pressed, side = False, 0
    if event.type == pygame.KEYDOWN:
        if event.key in (pygame.K_UP, pygame.K_w):
            index = (index - 1) % count
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            index = (index + 1) % count
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            pressed = True
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            side = -1
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            side = 1
    elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
        mouse = ui.mouse_to_ui(event.pos)
        for i, rect in enumerate(ui.get_menu_rects(count)):
            if rect.collidepoint(mouse):
                index = i
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pressed = True
                    side = -1 if mouse[0] < rect.centerx else 1
    return index, pressed, side


# ------------------------------------------------------------------
# 위치 도우미
# ------------------------------------------------------------------
def random_point_around(center, distance, play_area):
    """center에서 distance만큼 떨어진 무작위 위치. 맵 안쪽이면서 건물이 아닌 곳이 나올 때까지
    여러 번 다시 뽑고, 그래도 안 되면 center 쪽으로 당겨서 빈 곳을 찾음"""
    for _ in range(30):
        angle = random.uniform(0, math.tau)
        pos = center + pygame.Vector2(distance, 0).rotate_rad(angle)
        if play_area.collidepoint(pos) and not campus.is_blocked(pos.x, pos.y):
            return pos
    pos.x = max(play_area.left, min(play_area.right - 1, pos.x))
    pos.y = max(play_area.top, min(play_area.bottom - 1, pos.y))
    return campus.free_point(pos, center)


# ------------------------------------------------------------------
# 적 생성 / 난이도
# ------------------------------------------------------------------
def get_hp_multiplier(minutes):
    """적 체력 = 기본 x 1.2^경과 분 (1분마다 1.2배씩 계속 늘어남)"""
    return ENEMY_HP_GROWTH ** minutes


def make_enemy(x, y, kind, hp_mult, hard):
    """적 한 마리 만들기. hard = 난이도 배율 (체력과 공격력에 곱함)"""
    enemy = Enemy(x, y, kind, hp_mult * hard)
    enemy.damage *= hard
    return enemy


def spawn_wave(player_pos, minutes, count, play_area, hard):
    """화면 밖에 적 count마리를 생성해서 목록으로 돌려줌.
    가끔은 리포트 무리가 한쪽에서 한꺼번에 몰려옴"""
    hp_mult = get_hp_multiplier(minutes)
    kinds = [
        kind
        for kind, info in ENEMY_TYPES.items()
        if info["from_minute"] is not None and minutes >= info["from_minute"] and "rush" not in info
    ]
    wave = []
    if "report" in kinds and random.random() < SWARM_CHANCE:
        center = random_point_around(player_pos, SPAWN_DISTANCE, play_area)
        for _ in range(max(count, random.randint(5, 8))):
            pos = center + (random.uniform(-30, 30), random.uniform(-30, 30))
            wave.append(make_enemy(pos.x, pos.y, "report", hp_mult, hard))
    else:
        for _ in range(count):
            pos = random_point_around(player_pos, SPAWN_DISTANCE, play_area)
            wave.append(make_enemy(pos.x, pos.y, random.choice(kinds), hp_mult, hard))
    return wave


def spawn_rush(player_pos, minutes, play_area, hard):
    """돌진 무리: 빠른 적 8마리가 한곳에 뭉쳐서, 지금 플레이어 위치를 향해 일직선으로 돌진.
    방향은 생성 순간에 정해지므로 옆으로 비키면 피할 수 있음"""
    kinds = [
        kind
        for kind, info in ENEMY_TYPES.items()
        if "rush" in info and minutes >= info["from_minute"]
    ]
    if not kinds:
        return []
    kind = random.choice(kinds)
    center = random_point_around(player_pos, SPAWN_DISTANCE, play_area)
    direction = (player_pos - center).normalize()
    rush = []
    for _ in range(RUSH_SIZE):
        pos = center + (random.uniform(-25, 25), random.uniform(-25, 25))
        enemy = make_enemy(pos.x, pos.y, kind, get_hp_multiplier(minutes), hard)
        enemy.rush_dir = direction
        rush.append(enemy)
    return rush


def recycle_far_enemies(enemies, player_pos, play_area, now):
    """1초마다: 플레이어에게서 너무 멀어진 적, 건물에 걸려 1초 동안 거의 못 움직인 적은
    화면 밖 가까운 곳으로 다시 데려옴. 돌진하는 적은 지나가 버린 것이므로 없앰"""
    for enemy in list(enemies):
        if enemy.is_boss:
            continue
        far = enemy.pos.distance_to(player_pos) > RECYCLE_DISTANCE
        stuck = enemy.pos.distance_to(enemy.last_pos) < STUCK_DISTANCE and not enemy.is_waiting(now, player_pos)
        stuck = stuck and enemy.pos.distance_to(player_pos) > 40  # 플레이어에게 붙어 있는 건 걸린 게 아님
        if far and enemy.rush_dir is not None:
            enemy.kill()
        elif far or stuck:
            enemy.pos = random_point_around(player_pos, SPAWN_DISTANCE, play_area)
        enemy.last_pos = pygame.Vector2(enemy.pos)


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
    # SCALED: 전체화면으로 바꿔도 게임 화면(1280x720)을 모니터 크기에 맞게 알아서 늘려 줌
    window = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.SCALED)
    sharp = pygame.Surface((WIDTH * 2, HEIGHT * 2))  # 도트가 고르게 보이도록 2배로 키운 뒤 창 크기로 줄임
    fullscreen = False
    pygame.display.set_caption("부경대 서바이벌")
    screen = pygame.Surface((WIDTH, HEIGHT))  # 작은 화면에 그린 뒤 확대
    clock = pygame.time.Clock()
    sound.init()
    sound.start_bgm()
    ui.init()
    map_surface, play_area, map_labels = campus.load_map()

    running = True
    restart = True  # True면 게임을 처음 상태로 다시 세팅
    start_state = "title"  # 다시 세팅한 뒤 어느 화면으로 갈지 ("title" 또는 "playing")
    menu_index = 0         # 메뉴에서 지금 선택된 항목 번호
    difficulty = DEFAULT_DIFFICULTY  # 선택한 난이도 번호 (다시 시작해도 유지)
    settings_from = "title"   # 설정을 어디서 열었는지 (뒤로 가면 여기로)
    pause_from = "playing"    # 일시정지를 어느 상태에서 눌렀는지 (계속하면 여기로)
    while running:
        dt = clock.tick(FPS)  # 지난 프레임부터 흐른 시간 (ms)

        # 0. 새 게임 세팅 (처음 시작할 때와 R로 재시작할 때)
        if restart:
            sound.play_bgm("normal")
            player = Player(*(campus.start or play_area.center))
            weapons = {"pen": Pen()}  # 처음엔 볼펜만. 레벨업으로 최대 6개까지
            enemies = pygame.sprite.Group()
            enemy_bullets = pygame.sprite.Group()  # 교수님 질문이 던지는 물음표
            gems = pygame.sprite.Group()
            items = pygame.sprite.Group()
            bosses = []                # 지금까지 나온 보스들
            # 다음에 나올 보스 번호 (테스트로 중간부터 시작하면 지나간 보스는 건너뜀)
            next_boss = len([m for m, _ in BOSS_SCHEDULE if m < START_MINUTE])
            vfx.clear()
            banners = []               # 화면 가운데 큰 알림 (진화, 시너지)
            seen_evolved = set()       # 이미 알려 준 진화 무기
            game_time = int(START_MINUTE * 60000)
            last_spawn = game_time
            last_item_spawn = game_time
            kills = 0
            rerolls = REROLL_COUNT
            won = False                # 최종 보스를 잡았는지
            chest_gained = []          # 방금 연 보물상자에서 나온 강화들
            # "title" / "settings" / "playing" / "pause" / "levelup" / "chest" / "gameover" / "clear"
            state = start_state
            menu_index = 0
            options = []  # 레벨업 선택지
            message = ""  # 화면 위에 잠깐 뜨는 글자 (아이템, 보스 등장)
            message_color = ui.YELLOW
            message_end = 0
            restart = False

        now = game_time

        # 1. 이벤트 처리
        chosen = None  # 레벨업에서 고른 번호 (0, 1, 2)
        for event in pygame.event.get():
            escape = event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            if event.type == pygame.QUIT:
                running = False

            # F11: 전체화면 켜기/끄기 (어느 화면에서든)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                fullscreen = toggle_fullscreen(fullscreen)

            # 시작 화면: 게임 시작 / 소리 설정 / 프로그램 종료
            elif state == "title":
                menu_index, pressed, side = read_menu_event(event, menu_index, len(TITLE_MENU))
                if pressed and menu_index == 0:
                    state = "playing"
                elif menu_index == 1 and (pressed or side != 0):
                    # 난이도 바꾸기: Enter는 다음 난이도, A/D나 좌우 클릭은 그 방향으로
                    difficulty = (difficulty + (side or 1)) % len(DIFFICULTIES)
                elif pressed and menu_index == 2:
                    state, settings_from, menu_index = "settings", "title", 0
                elif pressed and menu_index == 3:
                    running = False

            # 일시정지: 계속하기 / 효과 설명 / 소리 설정 / 현재 게임 종료
            elif state == "pause":
                menu_index, pressed, _ = read_menu_event(event, menu_index, len(PAUSE_MENU))
                if escape or (pressed and menu_index == 0):
                    state = pause_from
                elif pressed and menu_index == 1:
                    state, info_from = "info", "pause"
                elif pressed and menu_index == 2:
                    state, settings_from, menu_index = "settings", "pause", 0
                elif pressed and menu_index == 3:
                    restart, start_state = True, "title"  # 시작 화면으로

            # 보스 소개: 아무 키나 클릭으로 닫기 (바로 넘어가지 않게 0.8초 기다림)
            elif state == "bossintro":
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN) \
                        and pygame.time.get_ticks() - intro_start > 800:
                    state = "playing"
                    message, message_color, message_end = f"{intro_boss.name} 등장!", ui.RED, now + 2000

            # 효과 설명 (진화·시너지): Tab / ESC / Enter / 클릭으로 닫기
            elif state == "info":
                if (event.type == pygame.KEYDOWN and event.key in (pygame.K_TAB, pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE)) \
                        or event.type == pygame.MOUSEBUTTONDOWN:
                    state = info_from

            # 게임 중 Tab: 효과 설명 열기 (게임은 멈춤)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB and state in ("playing", "levelup", "chest"):
                state, info_from = "info", state

            # 설정: 효과음 / 배경음악 볼륨, 전체화면, 뒤로
            elif state == "settings":
                menu_index, pressed, side = read_menu_event(event, menu_index, len(SETTINGS_MENU))
                if escape or (pressed and menu_index == 3):
                    state = settings_from
                    menu_index = 2  # 돌아가면 "설정" 항목이 선택된 채로 (시작 화면, 일시정지 모두 3번째)
                elif pressed and menu_index == 2:
                    fullscreen = toggle_fullscreen(fullscreen)
                elif side != 0 and menu_index < 2:
                    kind = VOLUME_KINDS[menu_index]
                    sound.set_volume(kind, sound.volume[kind] + side * VOLUME_STEP)
                    sound.play("gem")  # 바뀐 크기를 바로 들어볼 수 있게

            # 게임 중 ESC: 일시정지 (레벨업·보물상자 창에서도 가능)
            elif escape and state in ("playing", "levelup", "chest"):
                pause_from, state, menu_index = state, "pause", 0
            # 끝난 화면 ESC: 시작 화면으로
            elif escape:
                restart, start_state = True, "title"

            elif event.type == pygame.KEYDOWN:
                if state == "chest":
                    state = "playing"
                elif event.key == pygame.K_r and state in ("gameover", "clear"):
                    restart, start_state = True, "playing"
                elif state == "levelup" and event.key == pygame.K_r and rerolls > 0:
                    rerolls -= 1  # 선택지 다시 뽑기
                    options = levelup.get_options(player, weapons)
                elif state == "levelup" and event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    chosen = event.key - pygame.K_1
            elif event.type == pygame.MOUSEBUTTONDOWN and state == "levelup":
                mouse = ui.mouse_to_ui(event.pos)
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
                # 레벨업 넉백: 주변 적을 밀어내고 잠깐 무적
                for enemy in enemies:
                    if enemy.pos.distance_to(player.pos) <= LEVELUP_BLAST_RADIUS:
                        enemy.push(player.pos, LEVELUP_BLAST_POWER)
                player.shield_until = now + LEVELUP_SHIELD_TIME
                vfx.levelup(player.pos, LEVELUP_BLAST_RADIUS)

        # 시너지 확인: 새로 켜진 시너지가 있으면 화면에 알림
        synergies = active_synergies(weapons)
        for key in synergies - player.synergies:
            info = SYNERGIES[key]
            banners.append({"kind": "synergy", "title": f"시너지 발동: {info['name']}", "desc": info["desc"],
                            "icons": [f"icon_{w}" for w in info["weapons"]], "start": now})
            vfx.synergy(player.pos, (130, 230, 140))
            sound.play("levelup")
        player.synergies = synergies
        # 진화 확인: 새로 진화한 무기가 있으면 큰 연출
        for key, weapon in weapons.items():
            if weapon.evolved and key not in seen_evolved:
                seen_evolved.add(key)
                banners.append({"kind": "evolve", "title": f"{weapon.evo_name} 진화!", "desc": weapon.evo_desc,
                                "icons": [f"icon_{key}"], "start": now})
                vfx.evolve(player.pos)
                sound.play("chest")
        banners = [b for b in banners if now - b["start"] < ui.BANNER_TIME]

        # 2. 업데이트 (게임 중일 때만 움직임)
        if state == "playing":
            game_time += dt
            now = game_time
            minutes = min(now, GAME_DURATION) / 60000  # 난이도는 10분에서 멈춤
            hard = DIFFICULTIES[difficulty][1]  # 난이도 배율: 적의 체력·공격력·생성 수에 곱함
            final_boss_alive = any(b.kind == FINAL_BOSS and b.alive() for b in bosses)

            # 적 생성: 1초마다 (4.5 + 경과 분)마리. 최종 보스전에서는 절반
            if now - last_spawn >= SPAWN_INTERVAL:
                last_spawn = now
                recycle_far_enemies(enemies, player.pos, play_area, now)
                amount = (SPAWN_BASE + int(minutes) * SPAWN_PER_MINUTE) * hard
                if final_boss_alive:
                    amount = 0   # 최종 보스전은 1대1
                # 4.5마리처럼 소수면: 4마리 + 절반 확률로 1마리 더
                count = int(amount) + (random.random() < amount % 1)
                count = min(count, MAX_ENEMIES - len(enemies))
                if count > 0:
                    enemies.add(spawn_wave(player.pos, minutes, count, play_area, hard))
                if random.random() < RUSH_CHANCE and not final_boss_alive:
                    enemies.add(spawn_rush(player.pos, minutes, play_area, hard))

            # 보스 등장 (3분, 7분 중간보스 / 10분 최종 보스)
            if next_boss < len(BOSS_SCHEDULE) and now / 60000 >= BOSS_SCHEDULE[next_boss][0]:
                kind = BOSS_SCHEDULE[next_boss][1]
                pos = random_point_around(player.pos, 250, play_area)
                boss = make_enemy(pos.x, pos.y, kind, player.level, hard)  # 보스 체력은 플레이어 레벨에 비례
                if kind == "lunch_line":
                    enemies.add(reversed(boss.make_followers()))   # 줄 선 학생들 (뒤쪽부터 넣어야 머리가 맨 위에 그려짐)
                if kind == FINAL_BOSS:
                    # 최종 보스전: 필드의 몹이 모두 사라지고 1대1. 보스는 하늘에서 떨어짐
                    for enemy in list(enemies):
                        vfx.death(enemy.pos, enemy.kind)
                        enemy.kill()
                    enemy_bullets.empty()
                    boss.pos = player.pos + pygame.Vector2(0, -120)
                    boss.start_entrance(now)
                    sound.play_bgm("boss")
                enemies.add(boss)
                bosses.append(boss)
                next_boss += 1
                sound.play("boss")
                # 보스 소개 화면 (게임 멈춤, 0.8초 뒤부터 아무 키나 누르면 시작)
                state, intro_boss, intro_start = "bossintro", boss, pygame.time.get_ticks()

            # 버프 아이템 생성 (30초마다)
            if now - last_item_spawn >= ITEM_SPAWN_INTERVAL:
                items.add(spawn_item(player.pos, play_area))
                last_item_spawn = now

            player.update(now, dt, play_area)
            enemies.update(player.pos, now, enemy_bullets)
            vfx.update(now)
            if "overcharge" in player.synergies:   # 과충전: 느려진 적에게 전기가 지지직
                for enemy in enemies:
                    if now < enemy.slow_until and random.random() < 0.15:
                        vfx.zap(enemy.pos)
            enemy_bullets.update(now)
            for boss in bosses:
                if boss.landed:          # 착지 소리
                    boss.landed = False
                    sound.play("explosion")
                if boss.raged and boss.alive():   # 분노한 보스는 계속 불꽃이 피어오름
                    for _ in range(2):
                        vfx.rage_aura(boss.rect.center, boss.rect.width)
                if boss.just_raged:
                    boss.just_raged = False
                    vfx.rage(boss.pos)
                    sound.play("boss")
                    message, message_color, message_end = f"{boss.name} 분노! 공격이 빨라진다", ui.RED, now + 3000

            # 무기 공격 -> 죽은 적 처리
            for weapon in list(weapons.values()):
                for enemy in weapon.update(now, player, enemies):
                    kills += 1
                    sound.play("kill")
                    if enemy.is_boss:
                        vfx.boss_death(enemy.pos)
                    else:
                        vfx.death(enemy.pos, enemy.kind)
                    # 경험치 보석 (너무 많으면 새로 안 만들고 기존 보석에 합침)
                    if len(gems) < MAX_GEMS:
                        spot = campus.free_point(enemy.pos, player.pos)  # 건물 위에서 죽었으면 보석은 건물 밖에
                        gems.add(ExpGem(spot.x, spot.y, enemy.xp))
                    else:
                        random.choice(gems.sprites()).value += enemy.xp
                    # 팀플 무임승차자: 죽으면 작은 적 2마리로 분열
                    split = ENEMY_TYPES[enemy.kind].get("split_into")
                    if split:
                        for dx in (-6, 6):
                            enemies.add(make_enemy(enemy.pos.x + dx, enemy.pos.y, split, get_hp_multiplier(minutes), hard))
                    # 보스: 최종 보스면 클리어, 중간보스면 보물상자
                    if enemy.kind == FINAL_BOSS:
                        won = True
                    elif enemy.is_boss:
                        spot = campus.free_point(enemy.pos, player.pos)  # 보스가 건물 위에서 죽었으면 밖으로
                        items.add(Chest(spot.x, spot.y))
                        message, message_color, message_end = f"{enemy.name} 격파! 성적표를 주워라", ui.YELLOW, now + 3000

            # 경험치 보석 줍기
            gems.update(player.pos, player.pickup_radius())
            for gem in list(gems):
                if player.pos.distance_to(gem.pos) < GEM_COLLECT_DISTANCE:
                    player.gain_xp(gem.value, now)
                    vfx.gem(gem.pos, (150, 215, 255))
                    gem.kill()
                    sound.play("gem")

            # 버프 아이템 / 보물상자 줍기
            for item in pygame.sprite.spritecollide(player, items, True):
                vfx.pickup(item.rect.center)
                if item.kind == "chest":
                    chest_gained = levelup.open_chest(player, weapons)
                    state = "chest"
                    sound.play("chest")
                else:
                    apply_item(item.kind, player, gems, now)
                    info = ITEMS[item.kind]
                    message, message_color, message_end = f"{info['name']}!  {info['desc']}", ui.YELLOW, now + 2000
                    sound.play("item")

            # 적, 물음표 ↔ 플레이어: 닿으면 플레이어가 데미지를 받음
            enemy_hit = next((e for e in pygame.sprite.spritecollide(player, enemies, False) if e.height < 20), None)
            if enemy_hit and player.take_damage(enemy_hit.damage, now):
                sound.play("hurt")
                vfx.hurt(player.pos)
            for bullet in list(enemy_bullets):
                if isinstance(bullet, Hazard):   # 바닥 폭발은 원 안에 있을 때만
                    if not bullet.hits(player.pos):
                        continue
                    bullet.active = False        # 한 번만 맞음
                elif not player.rect.colliderect(bullet.rect):
                    continue
                else:
                    bullet.kill()
                if player.take_damage(bullet.damage, now):
                    sound.play("hurt")

            # 게임 끝 / 레벨업 판정
            if player.is_dead():
                state = "gameover"
                sound.play("gameover")
            elif won:
                state = "clear"
                sound.play("clear")
            elif state == "playing" and player.can_level_up():
                state = "levelup"
                options = levelup.get_options(player, weapons)
                sound.play("levelup")

        # 3. 그리기 - 게임 화면 (작은 screen에 그림)
        offset = get_camera_offset(player.pos, map_surface.get_size()) + vfx.shake_offset()
        screen.fill(BG_COLOR)
        screen.blit(map_surface, (0, 0), pygame.Rect(offset, (WIDTH, HEIGHT)))  # 맵에서 보이는 부분만
        for item in items:
            item.draw(screen, offset, now)
        for enemy in enemies:   # 보스 돌진 경고선 (적보다 먼저 = 바닥에 깔림)
            if enemy.telegraph:
                vfx.draw_warning(screen, offset, *enemy.telegraph, now)
            if enemy.height > 0:   # 공중에 뜬 보스의 그림자 (높을수록 작게)
                w = enemy.rect.width * max(0.3, 1 - enemy.height / 500)
                shadow = pygame.Rect(0, 0, w, w * 0.35)
                shadow.center = enemy.pos - offset + (0, enemy.rect.height * 0.4)
                pygame.draw.ellipse(screen, (20, 20, 30), shadow)
        # 건물 뒤에 있는 캐릭터는 먼저 그리고, 건물 그림(지붕·벽)을 덮은 뒤, 건물 앞 캐릭터를 그림
        behind_sprites = []
        for group in (gems, enemies, enemy_bullets):
            for sprite in group:
                if campus.is_behind(sprite.rect.centerx, sprite.rect.bottom):
                    behind_sprites.append(sprite)
                else:
                    draw_sprite(screen, sprite, offset)
        player_behind = campus.is_behind(player.rect.centerx, player.rect.bottom)
        if campus.building_layer:
            for sprite in behind_sprites:
                draw_sprite(screen, sprite, offset)
            screen.blit(campus.building_layer, (0, 0), pygame.Rect(offset, (WIDTH, HEIGHT)))
        else:
            for sprite in behind_sprites:
                draw_sprite(screen, sprite, offset)

        # 무적(학생증, 레벨업 직후)이면 플레이어 주변에 파란 원
        if player.has_buff("student_id", now) or now < player.shield_until:
            pygame.draw.circle(screen, ITEMS["student_id"]["color"], player.pos - offset, player.rect.height * 0.8, 1)
        # 맞은 직후에는 깜빡이게 (0.1초마다 보였다 안 보였다)
        if not (player.is_blinking(now) and (now // 100) % 2 == 0):
            if player_behind and campus.building_layer:
                ghost = player.image.copy()
                ghost.set_alpha(110)   # 건물 뒤에서도 위치를 알 수 있게 반투명으로 비침
                screen.blit(ghost, pygame.Vector2(player.rect.topleft) - offset)
            else:
                draw_sprite(screen, player, offset)
        for weapon in weapons.values():
            weapon.draw(screen, offset, now)
        vfx.draw(screen, offset)
        if any(b.kind == FINAL_BOSS and b.alive() for b in bosses):
            vfx.draw_vignette(screen, now)   # 최종 보스전: 화면 가장자리가 붉게 뜀

        ui.draw_player_hp(screen, player, offset)

        pygame.transform.scale(screen, sharp.get_size(), sharp)
        pygame.transform.smoothscale(sharp, window.get_size(), window)

        # 4. 그리기 - UI (확대된 window에 직접 그림)
        if state == "playing":
            alive_bosses = [b for b in bosses if b.alive()]
            ui.draw_map_labels(window, map_labels, offset)
            ui.draw_hud(window, player, weapons, kills, game_time, alive_bosses[-1] if alive_bosses else None, now)
            if now < message_end:
                ui.draw_text(window, "normal", message, ui.UI_W // 2, 24, "midtop", message_color)
            for banner in banners[-1:]:   # 가장 최근 알림 하나만
                ui.draw_banner(window, banner, now)
        else:
            ui.draw_dark_overlay(window)
            if state == "title":
                ui.draw_title(window)
                menu_items = list(TITLE_MENU)
                menu_items[1] = f"난이도: {DIFFICULTIES[difficulty][0]}"
                ui.draw_menu(window, menu_items, menu_index)
            elif state == "info":
                ui.draw_info(window, weapons, player)
            elif state == "bossintro":
                ui.draw_boss_intro(window, intro_boss, pygame.time.get_ticks() - intro_start)
            elif state == "pause":
                ui.draw_text(window, "big", "일시정지", ui.UI_W // 2, 40, "midtop", ui.YELLOW)
                ui.draw_menu(window, PAUSE_MENU, menu_index)
            elif state == "settings":
                ui.draw_text(window, "big", "설정", ui.UI_W // 2, 40, "midtop", ui.YELLOW)
                menu_items = list(SETTINGS_MENU)
                menu_items[2] = "전체화면: 켜짐" if fullscreen else "전체화면: 꺼짐"
                ui.draw_menu(window, menu_items, menu_index, [sound.volume["sfx"], sound.volume["bgm"], None, None])
            elif state == "levelup":
                ui.draw_levelup(window, options, rerolls)
            elif state == "chest":
                ui.draw_chest(window, chest_gained)
            else:
                ui.draw_end(window, state, game_time, kills, player.level, DIFFICULTIES[difficulty][0])

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
