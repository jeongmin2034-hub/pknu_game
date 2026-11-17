# vfx.py - 이펙트 모음 (파티클, 빛, 퍼지는 고리)
#
# 다른 파일에서는 "무슨 일이 일어났는지"만 알려 주면 됨. 예) vfx.death(적 위치, 적 종류)
# 그러면 여기서 작은 조각(파티클)들을 만들고, 매 프레임 움직이고 그려 줌.
#
# 게임하는 데 방해되지 않게:
#   - 대부분 0.1~0.4초 안에 사라짐
#   - 파티클은 최대 MAX_PARTICLES개까지만 (넘으면 새로 안 만듦)
#   - 시간은 game_time 기준이라 일시정지·레벨업 화면에서는 이펙트도 멈춤
import math
import random

import pygame

MAX_PARTICLES = 450

now = 0            # 지금 시각 (update에서 매 프레임 바꿈)
particles = []     # [x, y, 속도x, 속도y, 시작 시각, 끝 시각, 색, 크기, 중력, 빛나는지]
rings = []         # [x, y, 시작 시각, 끝 시각, 시작 반지름, 끝 반지름, 색, 굵기]
glows = []         # [x, y, 시작 시각, 끝 시각, 반지름, 색]  (번쩍이는 빛)

# 적이 죽을 때 튀는 조각 색
DEATH_COLORS = {
    "homework": (245, 245, 240),
    "report": (240, 150, 60),       # 길고양이
    "alarm": (226, 64, 64),
    "exam": (246, 234, 198),
    "freerider": (92, 194, 112),
    "freerider_mini": (92, 194, 112),
    "attendance": (235, 238, 245),  # 갈매기
    "question": (156, 90, 210),
}

_glow_cache = {}


def glow_image(radius, color):
    """가운데가 밝고 바깥으로 갈수록 흐려지는 동그란 빛 (더하기 방식으로 그림)"""
    radius = max(2, int(radius))
    key = (radius, color)
    if key not in _glow_cache:
        image = pygame.Surface((radius * 2, radius * 2))
        for i in range(radius, 0, -1):
            t = 1 - i / radius   # 바깥 0 ~ 가운데 1
            c = tuple(int(v * t * t) for v in color)
            pygame.draw.circle(image, c, (radius, radius), i)
        _glow_cache[key] = image
    return _glow_cache[key]


def clear():
    particles.clear()
    rings.clear()
    glows.clear()


# ------------------------------------------------------------------
# 기본 재료
# ------------------------------------------------------------------
def add(pos, velocity, life, color, size=2, gravity=0.0, light=False):
    if len(particles) >= MAX_PARTICLES:
        return
    particles.append([pos[0], pos[1], velocity[0], velocity[1], now, now + life, color, size, gravity, light])


def burst(pos, count, color, speed=1.5, life=300, size=2, gravity=0.0, light=False, spread=360, direction=0):
    """pos에서 사방(또는 direction 방향 spread도 안)으로 조각을 흩뿌림"""
    for _ in range(count):
        angle = math.radians(direction + random.uniform(-spread / 2, spread / 2))
        s = speed * random.uniform(0.4, 1.0)
        add(pos, (math.cos(angle) * s, math.sin(angle) * s), life * random.uniform(0.6, 1.0),
            color, size, gravity, light)


def ring(pos, r0, r1, life, color, width=2):
    rings.append([pos[0], pos[1], now, now + life, r0, r1, color, width])


def flash(pos, radius, life, color):
    glows.append([pos[0], pos[1], now, now + life, radius, color])


# ------------------------------------------------------------------
# 상황별 이펙트 (다른 파일에서 부르는 것들)
# ------------------------------------------------------------------
def hit(pos):
    """적이 맞았을 때: 작은 불꽃 2개 (파티클이 많을 땐 생략해서 죽는 이펙트 자리를 남겨 둠)"""
    if len(particles) > MAX_PARTICLES * 0.6:
        return
    burst(pos, 2, (255, 244, 200), speed=1.6, life=140, size=1)


def death(pos, kind):
    """적이 죽었을 때: 하얀 연기 + 적 색깔 조각"""
    color = DEATH_COLORS.get(kind, (240, 240, 240))
    burst(pos, 4, (230, 232, 236), speed=0.7, life=260, size=3)
    burst(pos, 4, color, speed=1.8, life=320, size=2, gravity=0.06)


def boss_death(pos):
    flash(pos, 70, 400, (255, 220, 120))
    ring(pos, 10, 120, 500, (255, 230, 140), 3)
    burst(pos, 40, (255, 210, 90), speed=3.5, life=700, size=3, gravity=0.04, light=True)


def gem(pos, color):
    """경험치를 먹었을 때: 반짝"""
    burst(pos, 3, color, speed=1.0, life=220, size=1, light=True)


def hurt(pos):
    """플레이어가 맞았을 때"""
    burst(pos, 6, (255, 80, 80), speed=1.8, life=260, size=2)


def levelup(pos, radius):
    """레벨업 넉백: 금빛 고리 두 겹 + 반짝이"""
    flash(pos, 40, 300, (255, 230, 120))
    ring(pos, 6, radius, 350, (255, 240, 160), 3)
    ring(pos, 4, radius * 0.6, 300, (255, 255, 255), 1)
    burst(pos, 18, (255, 226, 110), speed=2.6, life=450, size=2, light=True)


def pickup(pos):
    """버프 아이템·보물상자를 주웠을 때"""
    ring(pos, 4, 30, 300, (255, 255, 255), 2)
    burst(pos, 10, (255, 250, 200), speed=1.6, life=350, size=2, light=True)


# 무기별
def muzzle(pos, direction):
    """볼펜 발사: 앞쪽으로 작은 잉크 방울"""
    angle = math.degrees(math.atan2(direction.y, direction.x))
    burst(pos, 2, (110, 150, 230), speed=1.4, life=120, size=1, spread=40, direction=angle)


def ink(pos):
    """만년필 잉크 튐"""
    ring(pos, 2, 16, 200, (60, 90, 180), 2)
    burst(pos, 6, (50, 80, 170), speed=1.6, life=260, size=2, gravity=0.05)


def ember(pos, direction):
    """신라면 불씨: 화염 방향으로 날아가며 위로 살짝 뜸"""
    angle = math.degrees(math.atan2(direction.y, direction.x))
    color = random.choice(((255, 200, 70), (255, 140, 40), (240, 80, 30)))
    burst(pos, 1, color, speed=2.4, life=300, size=2, gravity=-0.03, spread=50, direction=angle, light=True)


def coffee(pos, radius):
    """커피 폭발: 갈색 방울 + 크림색 고리"""
    ring(pos, radius * 0.3, radius, 260, (240, 214, 170), 2)
    burst(pos, 10, (120, 74, 42), speed=2.6, life=380, size=2, gravity=0.08)
    burst(pos, 4, (246, 230, 200), speed=1.2, life=300, size=2)


def lightning(pos, radius):
    """번개가 떨어진 자리: 번쩍 + 전기 불꽃"""
    flash(pos, radius * 1.6, 180, (180, 200, 255))
    ring(pos, 4, radius, 200, (210, 230, 255), 2)
    burst(pos, 6, (170, 220, 255), speed=2.4, life=220, size=1, light=True)


def beam_end(pos, color):
    """레이저 끝 불꽃"""
    burst(pos, 4, color, speed=1.8, life=200, size=1, light=True)


def whip_tip(pos, electric):
    """케이블 끝 불꽃"""
    color = (150, 220, 255) if electric else (240, 240, 250)
    burst(pos, 4, color, speed=1.8, life=200, size=1, light=electric)


def tray_trail(pos):
    """식판이 지나간 자리"""
    add((pos[0] + random.uniform(-3, 3), pos[1] + random.uniform(-3, 3)), (0, 0), 160, (220, 224, 234), 2)


# ------------------------------------------------------------------
# 매 프레임
# ------------------------------------------------------------------
def update(time):
    global now
    now = time
    particles[:] = [p for p in particles if p[5] > now]
    rings[:] = [r for r in rings if r[3] > now]
    glows[:] = [g for g in glows if g[3] > now]
    for p in particles:
        p[0] += p[2]
        p[1] += p[3]
        p[2] *= 0.93     # 공기 저항
        p[3] = p[3] * 0.93 + p[8]


def draw(screen, offset):
    ox, oy = offset
    for x, y, start, end, radius, color in glows:
        t = (now - start) / (end - start)
        image = glow_image(radius * (1 - 0.3 * t), tuple(int(c * (1 - t)) for c in color))
        screen.blit(image, image.get_rect(center=(x - ox, y - oy)), special_flags=pygame.BLEND_RGB_ADD)
    for x, y, start, end, r0, r1, color, width in rings:
        t = (now - start) / (end - start)
        radius = r0 + (r1 - r0) * (1 - (1 - t) ** 2)   # 처음엔 빠르게, 나중엔 천천히 퍼짐
        w = max(1, round(width * (1 - t)))
        pygame.draw.circle(screen, color, (x - ox, y - oy), max(1, radius), w)
    for x, y, _, _, start, end, color, size, _, light in particles:
        t = (now - start) / (end - start)
        s = max(1, round(size * (1 - t * 0.6)))
        if light:
            image = glow_image(s + 2, tuple(int(c * (1 - t)) for c in color))
            screen.blit(image, image.get_rect(center=(x - ox, y - oy)), special_flags=pygame.BLEND_RGB_ADD)
        screen.fill(color, (round(x - ox) - s // 2, round(y - oy) - s // 2, s, s))


# ------------------------------------------------------------------
# 진화 / 시너지
# ------------------------------------------------------------------
GOLD = (255, 214, 90)


def evolve(pos):
    """무기 진화 순간: 금빛 기둥 + 큰 고리 두 겹 + 번쩍"""
    flash(pos, 90, 600, (255, 210, 110))
    ring(pos, 8, 110, 600, GOLD, 4)
    ring(pos, 4, 70, 450, (255, 255, 255), 2)
    for _ in range(36):   # 땅에서 위로 솟는 금빛 기둥
        x = pos[0] + random.uniform(-14, 14)
        add((x, pos[1] + random.uniform(-4, 8)), (random.uniform(-0.2, 0.2), random.uniform(-4.5, -2)),
            random.uniform(400, 800), random.choice((GOLD, (255, 250, 210))), 2, -0.02, True)
    burst(pos, 24, GOLD, speed=3.2, life=600, size=2, light=True)


def synergy(pos, color):
    """시너지 발동 순간"""
    flash(pos, 60, 450, color)
    ring(pos, 6, 90, 500, color, 3)
    burst(pos, 20, color, speed=2.6, life=500, size=2, light=True)


def gold(pos, count=2):
    """진화한 무기가 공격할 때 같이 튀는 금빛 반짝이"""
    if len(particles) > MAX_PARTICLES * 0.7:
        return
    burst(pos, count, GOLD, speed=1.4, life=260, size=1, light=True)


def zap(pos):
    """과충전: 느려진 적 몸에서 지지직"""
    add((pos[0] + random.uniform(-5, 5), pos[1] + random.uniform(-6, 4)),
        (random.uniform(-0.8, 0.8), random.uniform(-0.8, 0.8)), 120, (140, 210, 255), 1, 0, True)


def dust(pos):
    """학식 러시: 넉백된 적 발밑 흙먼지"""
    if len(particles) > MAX_PARTICLES * 0.6:
        return
    burst((pos[0], pos[1] + 4), 2, (196, 178, 150), speed=0.9, life=300, size=3)


def glitter_line(start, end, color):
    """필기 세트: 레이저를 따라 형광 가루"""
    for i in range(8):
        t = random.random()
        p = (start[0] + (end[0] - start[0]) * t, start[1] + (end[1] - start[1]) * t)
        add(p, (random.uniform(-0.4, 0.4), random.uniform(-0.6, 0.1)), 300, color, 1, 0, True)


def fire_spark(pos):
    """바닥 불에서 튀어 오르는 불씨"""
    color = random.choice(((255, 200, 70), (255, 140, 40)))
    add((pos[0] + random.uniform(-14, 14), pos[1] + random.uniform(-8, 8)),
        (random.uniform(-0.3, 0.3), random.uniform(-1.6, -0.6)), 380, color, 2, 0, True)


def draw_warning(screen, offset, start, end, width, time):
    """보스 돌진 경고: 돌진할 길을 빨간 띠로 보여 주고, 화살표가 진행 방향으로 흘러감"""
    a, b = pygame.Vector2(start) - offset, pygame.Vector2(end) - offset
    direction = b - a
    if direction.length() == 0:
        return
    forward = direction.normalize()
    side = pygame.Vector2(-forward.y, forward.x) * width / 2
    left, top = min(a.x, b.x) - width, min(a.y, b.y) - width
    size = (int(abs(b.x - a.x) + width * 2) + 2, int(abs(b.y - a.y) + width * 2) + 2)
    layer = pygame.Surface(size, pygame.SRCALPHA)
    corner = pygame.Vector2(left, top)
    band = [p - corner for p in (a + side, b + side, b - side, a - side)]
    pulse = 70 + 40 * math.sin(time / 80)          # 깜빡깜빡
    pygame.draw.polygon(layer, (230, 40, 40, int(pulse)), band)
    pygame.draw.polygon(layer, (255, 90, 90, 220), band, 2)
    # 진행 방향 화살표 (>)
    length = direction.length()
    for k in range(4):
        d = (time / 6 + k * length / 4) % length
        tip = a + forward * d - corner
        wing = forward * -8
        pygame.draw.lines(layer, (255, 200, 200, 230), False,
                          [tip + wing + side * 0.6, tip, tip + wing - side * 0.6], 2)
    screen.blit(layer, corner)



# ------------------------------------------------------------------
# 기말고사 (최종 보스)
# ------------------------------------------------------------------
_shake = [0, 0, 0]   # [세기, 시작, 끝]
_vignette = {}


def shake(power, time):
    """화면 흔들기"""
    _shake[:] = [power, now, now + time]


def shake_offset():
    power, start, end = _shake
    if now >= end:
        return pygame.Vector2(0, 0)
    p = power * (end - now) / (end - start)
    return pygame.Vector2(random.uniform(-p, p), random.uniform(-p, p))


def final_landing(pos):
    """기말고사가 하늘에서 떨어져 착지: 화면 번쩍 + 충격파 세 겹 + 파편"""
    shake(9, 900)
    flash(pos, 160, 700, (255, 80, 60))
    for r1, life, color, width in ((260, 700, (255, 70, 60), 5), (180, 550, (255, 200, 120), 3), (110, 420, (255, 255, 255), 2)):
        ring(pos, 10, r1, life, color, width)
    burst(pos, 50, (120, 96, 80), speed=4.5, life=800, size=3, gravity=0.12)      # 흙 파편
    burst(pos, 30, (255, 90, 60), speed=3.5, life=700, size=2, light=True)       # 불똥
    burst(pos, 20, (240, 230, 200), speed=2.2, life=600, size=4)                 # 종이 조각


def slam(pos):
    """점프 착지"""
    shake(5, 350)
    flash(pos, 70, 300, (255, 120, 80))
    ring(pos, 8, 70, 380, (255, 160, 120), 3)
    burst(pos, 18, (130, 104, 84), speed=3, life=450, size=3, gravity=0.1)


def red_blast(pos, radius):
    """빨간펜 폭격 폭발"""
    flash(pos, radius * 1.4, 220, (255, 60, 50))
    ring(pos, radius * 0.4, radius, 220, (255, 120, 110), 3)
    burst(pos, 8, (220, 30, 40), speed=2.4, life=320, size=2, gravity=0.06)


def rage(pos):
    """기말고사 분노: 크게 번쩍 + 불기둥 + 충격파"""
    shake(10, 1000)
    flash(pos, 180, 900, (255, 60, 20))
    for r1, life, color, width in ((240, 800, (255, 60, 30), 5), (160, 650, (255, 170, 60), 3)):
        ring(pos, 10, r1, life, color, width)
    for _ in range(50):   # 위로 솟는 불기둥
        x = pos[0] + random.uniform(-30, 30)
        add((x, pos[1] + random.uniform(0, 20)), (random.uniform(-0.3, 0.3), random.uniform(-5, -2)),
            random.uniform(500, 900), random.choice(((255, 80, 20), (255, 170, 40), (255, 230, 120))), 3, -0.02, True)
    burst(pos, 30, (40, 20, 20), speed=3.5, life=800, size=3, gravity=0.08)   # 검은 재


def rage_aura(pos, width):
    """분노한 기말고사 주변에 계속 피어오르는 불꽃"""
    if len(particles) > MAX_PARTICLES * 0.7:
        return
    x = pos[0] + random.uniform(-width / 2, width / 2)
    color = random.choice(((255, 90, 20), (255, 160, 40), (220, 40, 30)))
    add((x, pos[1] + random.uniform(-10, 30)), (random.uniform(-0.3, 0.3), random.uniform(-2.2, -0.8)),
        random.uniform(300, 600), color, random.choice((2, 3)), -0.01, True)


def draw_vignette(screen, time):
    """최종 보스전: 화면 가장자리에 붉은 기운이 맥박처럼 뛰는 효과"""
    size = screen.get_size()
    if size not in _vignette:
        w, h = size
        layer = pygame.Surface(size, pygame.SRCALPHA)
        for i in range(40):
            alpha = int(150 * (1 - i / 40) ** 2)
            pygame.draw.rect(layer, (150, 0, 10, alpha), (i * 2, i * 2, w - i * 4, h - i * 4), 2)
        _vignette[size] = layer
    layer = _vignette[size]
    layer.set_alpha(int(130 + 50 * math.sin(time / 300)))
    screen.blit(layer, (0, 0))
