# weapon.py - 무기 8종
#   볼펜, 전공서적, 신라면, 커피, 보조배터리, 형광펜, 식판, 충전 케이블
#
# 모든 무기는 같은 모양의 함수 2개를 가짐:
#   update(now, player, enemies) -> 이번에 죽인 적 목록
#   draw(screen, offset, now)    -> 무기 그리기
# 그래서 main.py에서는 무기 종류를 신경 쓰지 않고 똑같이 부를 수 있음.
#
# 무기 레벨: 처음 얻으면 Lv1, 강화할 때마다 +1 (최대 Lv10). Lv7부터 "진화" 가능
# 각 무기의 options = 그 무기만의 강화 옵션들: (설명, 바꿀 값 이름, 더할 양, 최대 횟수)
# 레벨업 때 옵션 중 하나가 무작위로 카드에 나오고, 고르면 그 무기에만 적용됨
import math
import random

import pygame
from settings import (
    PEN_INTERVAL, PEN_DAMAGE, PEN_RANGE, BULLET_SPEED, BULLET_LIFETIME, INK_RADIUS,
    BOOK_DAMAGE, BOOK_RADIUS, BOOK_ROTATE_SPEED, BOOK_HIT_SIZE, BOOK_HIT_COOLDOWN,
    RAMEN_TICK, RAMEN_DAMAGE, RAMEN_LENGTH, RAMEN_ANGLE,
    FIRE_TIME, FIRE_TICK, FIRE_DAMAGE, FIRE_RADIUS,
    COFFEE_INTERVAL, COFFEE_DAMAGE, COFFEE_RADIUS, COFFEE_RANGE, COFFEE_EFFECT_TIME,
    BATTERY_INTERVAL, BATTERY_DAMAGE, BATTERY_RADIUS, BATTERY_RANGE, CHAIN_RANGE,
    HIGHLIGHTER_INTERVAL, HIGHLIGHTER_DAMAGE, HIGHLIGHTER_LENGTH, HIGHLIGHTER_WIDTH,
    HIGHLIGHTER_EFFECT_TIME,
    TRAY_INTERVAL, TRAY_DAMAGE, TRAY_RANGE, TRAY_SPEED, TRAY_HIT_SIZE,
    CABLE_INTERVAL, CABLE_DAMAGE, CABLE_LENGTH, CABLE_HEIGHT, CABLE_EFFECT_TIME,
    SLOW_TIME, SYNERGIES, SYNERGY_LEVEL, EVOLVE_LEVEL, MAX_WEAPON_LEVEL,
)
import sound
import sprites
import vfx


# ------------------------------------------------------------------
# 같이 쓰는 도우미
# ------------------------------------------------------------------
def enemies_in_range(pos, enemies, max_range):
    """pos에서 max_range 안에 있는 적들을 가까운 순서로"""
    near = [e for e in enemies if pos.distance_to(e.pos) <= max_range]
    near.sort(key=lambda e: pos.distance_squared_to(e.pos))
    return near


def aim_at(start, target):
    """start에서 target을 향하는 방향 (길이 1). 완전히 겹쳐 있으면 오른쪽"""
    direction = target - start
    if direction.length() == 0:
        return pygame.Vector2(1, 0)
    return direction.normalize()


def hit(enemy, damage, killed, knockback=0, from_pos=None):
    """적 한 마리를 때림. 죽었으면 killed에 추가"""
    if not enemy.alive():
        return
    sound.play("hit")
    vfx.hit(enemy.pos)
    if enemy.take_damage(damage, knockback, from_pos):
        killed.append(enemy)


def slow(enemy, now, player):
    """과충전 시너지가 켜져 있으면 적을 느리게"""
    if "overcharge" in player.synergies:
        enemy.slow_until = now + SLOW_TIME


def draw_circle(screen, color, center, radius, width=0):
    """반투명 원 그리기. color는 (빨강, 초록, 파랑, 투명도)"""
    r = max(1, int(radius))
    circle = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    pygame.draw.circle(circle, color, (r, r), r, width)
    screen.blit(circle, pygame.Vector2(center) - (r, r))


_scaled = {}


def fx(name, size):
    """이펙트 도트 그림을 size(정수 픽셀) 크기로 (한 번 만든 크기는 저장)"""
    size = max(4, int(size))
    key = (name, size)
    if key not in _scaled:
        image = sprites.load_file(name)
        w, h = image.get_size()
        _scaled[key] = pygame.transform.scale(image, (size, round(size * h / w)))
    return _scaled[key]


def active_synergies(weapons):
    """지금 켜져 있는 시너지 이름들. 두 무기가 모두 Lv3 이상이면 발동"""
    result = set()
    for key, info in SYNERGIES.items():
        a, b = info["weapons"]
        if a in weapons and b in weapons:
            if weapons[a].level >= SYNERGY_LEVEL and weapons[b].level >= SYNERGY_LEVEL:
                result.add(key)
    return result


class Weapon:
    """모든 무기의 공통 부분 (레벨, 강화 옵션, 진화, 쿨타임)"""
    name = ""
    desc = ""          # 새 무기로 나올 때 설명
    evo_name = ""      # 진화했을 때 이름
    evo_desc = ""
    knockback = 0
    options = []       # (설명, 바꿀 값 이름, 더할 양, 최대 횟수)

    def __init__(self):
        self.level = 1
        self.evolved = False
        self.last_shot = 0
        self.taken = {}  # 옵션 번호 -> 지금까지 고른 횟수

    def title(self):
        return self.evo_name if self.evolved else self.name

    def available_options(self):
        """아직 더 올릴 수 있는 옵션 번호들"""
        if self.level >= MAX_WEAPON_LEVEL:
            return []
        return [i for i, option in enumerate(self.options) if self.taken.get(i, 0) < option[3]]

    def take_option(self, index):
        """옵션 하나를 적용: 그 값에 정해진 양을 더하고 레벨 +1"""
        _, attr, amount, _ = self.options[index]
        setattr(self, attr, getattr(self, attr) + amount)
        self.taken[index] = self.taken.get(index, 0) + 1
        self.level += 1

    def can_evolve(self):
        return self.level >= EVOLVE_LEVEL and not self.evolved

    def evolve(self):
        self.evolved = True

    def shine(self, pos, count=2):
        """진화한 무기는 공격할 때 금빛 반짝이가 같이 튐"""
        if self.evolved:
            vfx.gold(pos, count)

    def cooled(self, now, player, interval):
        """쿨타임이 끝났으면 True (에너지 드링크를 먹으면 쿨타임이 짧아짐)"""
        return now - self.last_shot >= interval * player.cooldown_mult(now)


class FirePatches:
    """바닥에 남는 불 (불닭볶음면, 얼큰한 모닝커피 시너지). 안에 있는 적은 계속 데미지"""

    def __init__(self):
        self.patches = []   # (위치, 꺼지는 시각)
        self.last_tick = 0

    def add(self, pos, now):
        self.patches.append((pygame.Vector2(pos), now + FIRE_TIME))

    def update(self, now, enemies, killed):
        self.patches = [(pos, end) for pos, end in self.patches if end > now]
        for pos, _ in self.patches:
            if random.random() < 0.25:
                vfx.fire_spark(pos)
        if self.patches and now - self.last_tick >= FIRE_TICK:
            self.last_tick = now
            for enemy in list(enemies):
                for pos, _ in self.patches:
                    if enemy.pos.distance_to(pos) <= FIRE_RADIUS:
                        hit(enemy, FIRE_DAMAGE, killed)
                        break

    def draw(self, screen, offset, now):
        flicker = 1 + 0.15 * math.sin(now / 60)  # 불이 일렁이게
        for pos, _ in self.patches:
            draw_circle(screen, (240, 110, 40, 60), pos - offset, FIRE_RADIUS * flicker)
            image = fx("fx_flame", FIRE_RADIUS * 0.9 * flicker)
            for dx, dy in ((-0.4, 0.1), (0.4, 0.15), (0, -0.25)):
                spot = pos - offset + (dx * FIRE_RADIUS, dy * FIRE_RADIUS)
                screen.blit(image, image.get_rect(midbottom=spot))


# ------------------------------------------------------------------
# 1. 볼펜: 가장 가까운 적에게 발사 (기본 무기)  ->  만년필
# ------------------------------------------------------------------
class Bullet(pygame.sprite.Sprite):
    """날아가는 총알. 정해진 시간이 지나면 사라짐."""

    def __init__(self, pos, direction, damage, pierce, now):
        super().__init__()
        self.image = sprites.load("bullet", sprites.BULLET)
        self.pos = pygame.Vector2(pos)
        self.velocity = direction * BULLET_SPEED
        self.rect = self.image.get_rect(center=self.pos)
        self.damage = damage
        self.pierce = pierce      # 몇 마리까지 뚫고 지나가는지
        self.hit_enemies = set()  # 이미 맞힌 적 (같은 적을 두 번 안 때리게)
        self.spawn_time = now

    def update(self, now):
        self.pos += self.velocity
        self.rect.center = self.pos
        if now - self.spawn_time > BULLET_LIFETIME:
            self.kill()


class Pen(Weapon):
    name = "볼펜"
    desc = "가까운 적에게 발사"
    evo_name = "만년필"
    evo_desc = "적을 관통하고 잉크가 튐"
    options = [
        ("발사 수 +1", "count", 1, 3),
        ("공격 간격 -0.12초", "interval", -120, 3),
        ("데미지 +6", "damage", 6, 4),
        ("넉백 +1.5", "knockback", 1.5, 2),
        ("관통 +1", "pierce", 1, 2),
    ]

    def __init__(self):
        super().__init__()
        self.count = 1
        self.interval = PEN_INTERVAL
        self.damage = PEN_DAMAGE
        self.knockback = 1.5
        self.pierce = 0
        self.bullets = pygame.sprite.Group()
        self.splashes = []  # 만년필 잉크 (위치, 사라질 시각)
        self.notes = False

    def update(self, now, player, enemies):
        self.bullets.update(now)
        self.notes = "notes" in player.synergies   # 필기 세트면 총알 꼬리가 형광색

        if self.cooled(now, player, self.interval):
            targets = enemies_in_range(player.pos, enemies, PEN_RANGE)
            if targets:
                pierce = self.pierce + (1 if "notes" in player.synergies else 0)
                if self.evolved:
                    pierce = 999
                # 가까운 적부터 한 발씩. 적이 총알 수보다 적으면 다시 처음부터
                for i in range(self.count):
                    direction = aim_at(player.pos, targets[i % len(targets)].pos)
                    self.bullets.add(Bullet(player.pos, direction, self.damage, pierce, now))
                    vfx.muzzle(player.pos + direction * 6, direction)
                    self.shine(player.pos + direction * 6)
                self.last_shot = now
                sound.play("shoot")

        # 총알 ↔ 적
        killed = []
        hits = pygame.sprite.groupcollide(self.bullets, enemies, False, False)
        for bullet, hit_enemies in hits.items():
            for enemy in hit_enemies:
                if enemy in bullet.hit_enemies or not bullet.alive():
                    continue
                bullet.hit_enemies.add(enemy)
                hit(enemy, bullet.damage, killed, self.knockback, bullet.pos - bullet.velocity * 10)
                if self.evolved:  # 잉크가 튀어 주변 적도 절반 데미지
                    self.splashes.append((pygame.Vector2(enemy.pos), now + 150))
                    vfx.ink(enemy.pos)
                    for other in enemies_in_range(enemy.pos, enemies, INK_RADIUS):
                        if other is not enemy:
                            hit(other, bullet.damage * 0.5, killed)
                if len(bullet.hit_enemies) > bullet.pierce:
                    bullet.kill()
        self.splashes = [(pos, end) for pos, end in self.splashes if end > now]
        return killed

    def draw(self, screen, offset, now):
        for bullet in self.bullets:
            # 꼬리: 지나온 자리에 점점 작아지는 잉크 점
            for k, size in ((1, 3), (2, 2), (3, 1)):
                tail = bullet.pos - bullet.velocity * k * 0.8 - offset
                color = (240, 236, 80) if self.notes else (90, 130, 220)
                screen.fill(color, (round(tail.x) - size // 2, round(tail.y) - size // 2, size, size))
            screen.blit(bullet.image, pygame.Vector2(bullet.rect.topleft) - offset)


# ------------------------------------------------------------------
# 2. 전공서적: 플레이어 주변을 빙글빙글 돌며 공격  ->  백과사전
# ------------------------------------------------------------------
class Book(Weapon):
    name = "전공서적"
    desc = "주변을 회전하며 공격"
    evo_name = "백과사전"
    evo_desc = "책 크기 2배, 도는 범위 1.5배"
    options = [
        ("책 개수 +1", "count", 1, 3),
        ("회전 속도 +20%", "rotate_speed", BOOK_ROTATE_SPEED * 0.2, 3),
        ("데미지 +6", "damage", 6, 4),
        ("넉백 +2", "knockback", 2, 2),
        ("책 크기 +25%", "size", 0.25, 2),
    ]

    def __init__(self):
        super().__init__()
        self.count = 1
        self.rotate_speed = BOOK_ROTATE_SPEED
        self.damage = BOOK_DAMAGE
        self.knockback = 6
        self.size = 1
        self.angle = 0
        self.last_update = 0
        self.positions = []   # 책들의 현재 위치 (그리기용)
        self.last_hit = {}    # 적 -> 그 적을 마지막으로 때린 시각

    def scale(self):
        return self.size * (2 if self.evolved else 1)

    def update(self, now, player, enemies):
        # 책 위치 계산: 시간에 따라 각도가 커짐 -> 회전. 책끼리는 같은 간격으로 벌어짐
        self.angle += (now - self.last_update) * self.rotate_speed
        self.last_update = now
        radius = BOOK_RADIUS * (1.5 if self.evolved else 1)
        self.positions = [
            player.pos + pygame.Vector2(radius, 0).rotate(self.angle + 360 * i / self.count)
            for i in range(self.count)
        ]

        killed = []
        for book_pos in self.positions:
            if self.evolved and random.random() < 0.12:
                vfx.gold(book_pos, 1)
        knockback = self.knockback * (1.5 if "rush" in player.synergies else 1)
        cooldown = BOOK_HIT_COOLDOWN * player.cooldown_mult(now)
        for enemy in list(enemies):
            if now - self.last_hit.get(enemy, -cooldown) < cooldown:
                continue  # 이 적은 방금 맞았으니 잠깐 쉼
            for book_pos in self.positions:
                if enemy.pos.distance_to(book_pos) < BOOK_HIT_SIZE * self.scale() + enemy.rect.width / 2:
                    self.last_hit[enemy] = now
                    hit(enemy, self.damage, killed, knockback, player.pos)
                    if "rush" in player.synergies:
                        vfx.dust(enemy.pos)
                    break

        # 죽은 적은 기록에서 지움 (기록이 계속 쌓이지 않게)
        self.last_hit = {e: t for e, t in self.last_hit.items() if e.alive()}
        return killed

    def draw(self, screen, offset, now):
        image = sprites.load("book", sprites.BOOK)
        size = (round(image.get_width() * self.scale()), round(image.get_height() * self.scale()))
        image = pygame.transform.scale(image, size)
        light = vfx.glow_image(image.get_width(), (40, 60, 120) if not self.evolved else (90, 70, 20))
        for pos in self.positions:
            screen.blit(light, light.get_rect(center=pos - offset), special_flags=pygame.BLEND_RGB_ADD)
            screen.blit(image, image.get_rect(center=pos - offset))


# ------------------------------------------------------------------
# 3. 신라면: 바라보는 방향으로 화염 방사  ->  불닭볶음면
# ------------------------------------------------------------------
class Ramen(Weapon):
    name = "신라면"
    desc = "움직이는 방향으로 화염 방사"
    evo_name = "불닭볶음면"
    evo_desc = "화염이 길어지고 바닥에 불이 남음"
    options = [
        ("데미지 +2", "damage", 2, 4),
        ("화염 길이 +15", "length", 15, 3),
        ("화염 폭 +8도", "angle", 8, 2),
        ("타격 간격 -0.02초", "tick", -20, 2),
        ("넉백 +1", "knockback", 1, 2),
    ]

    def __init__(self):
        super().__init__()
        self.damage = RAMEN_DAMAGE
        self.length = RAMEN_LENGTH
        self.angle = RAMEN_ANGLE
        self.tick = RAMEN_TICK
        self.knockback = 0
        self.origin = pygame.Vector2(0, 0)
        self.aim = pygame.Vector2(1, 0)
        self.reach = self.length
        self.fires = FirePatches()
        self.last_fire = 0

    def update(self, now, player, enemies):
        killed = []
        self.origin = pygame.Vector2(player.pos)
        self.aim = pygame.Vector2(player.aim)
        self.reach = self.length * (1.5 if self.evolved else 1)
        for _ in range(2):
            vfx.ember(self.origin + self.aim * 8, self.aim)
        if random.random() < 0.3:
            self.shine(self.origin + self.aim * self.reach * random.uniform(0.3, 1), 1)

        if self.cooled(now, player, self.tick):
            self.last_shot = now
            min_dot = math.cos(math.radians(self.angle))
            for enemy in list(enemies):
                to_enemy = enemy.pos - player.pos
                distance = to_enemy.length()
                # 화염 길이 안에 있고, 바라보는 방향과 각도가 가까우면 맞음
                if 0 < distance <= self.reach and to_enemy.dot(self.aim) / distance >= min_dot:
                    hit(enemy, self.damage, killed, self.knockback, player.pos)

        if self.evolved and now - self.last_fire >= 400:
            self.fires.add(player.pos + self.aim * self.reach * 0.7, now)
            self.last_fire = now
        self.fires.update(now, enemies, killed)
        return killed

    def draw(self, screen, offset, now):
        self.fires.draw(screen, offset, now)
        # 화염: 플레이어에서 멀어질수록 커지는 원 여러 개 (조금씩 흔들림)
        start = self.origin - offset
        side = self.aim.rotate(90)
        spread = math.tan(math.radians(self.angle)) * 0.45
        for i in range(1, 7):
            t = i / 6
            wobble = math.sin(now / 40 + i * 1.7) * 3 * t
            center = start + self.aim * self.reach * t + side * wobble
            radius = 3 + self.reach * spread * t
            image = fx("fx_flame", radius * 1.8)
            screen.blit(image, image.get_rect(center=center))


# ------------------------------------------------------------------
# 4. 커피: 무작위 적 위치에서 펑! 주변 적 모두 데미지  ->  콜드브루
# ------------------------------------------------------------------
class Coffee(Weapon):
    name = "커피"
    desc = "3초마다 적 위치에 폭발"
    evo_name = "콜드브루"
    evo_desc = "폭발 뒤 작은 폭발이 연쇄로 터짐"
    options = [
        ("폭발 범위 +8", "radius", 8, 3),
        ("데미지 +10", "damage", 10, 4),
        ("공격 간격 -0.4초", "interval", -400, 3),
        ("폭발 수 +1", "count", 1, 2),
        ("넉백 +1.5", "knockback", 1.5, 2),
    ]

    def __init__(self):
        super().__init__()
        self.radius = COFFEE_RADIUS
        self.damage = COFFEE_DAMAGE
        self.interval = COFFEE_INTERVAL
        self.count = 1
        self.knockback = 3.5
        self.pending = []     # 조금 뒤에 터질 연쇄 폭발 (터질 시각, 위치)
        self.explosions = []  # 그리기용 (위치, 반지름, 그림이 사라질 시각)
        self.fires = FirePatches()

    def explode(self, center, scale, now, player, enemies, killed):
        """center에서 폭발. scale: 크기와 데미지 배율 (연쇄 폭발은 0.6)"""
        radius = self.radius * scale
        for enemy in enemies_in_range(center, enemies, radius):
            hit(enemy, self.damage * scale, killed, self.knockback, center)
        self.explosions.append((center, radius, now + COFFEE_EFFECT_TIME))
        vfx.coffee(center, radius)
        self.shine(center, 4)
        if "morning" in player.synergies and scale == 1:
            self.fires.add(center, now)
        sound.play("explosion")

    def update(self, now, player, enemies):
        killed = []
        if self.cooled(now, player, self.interval):
            candidates = enemies_in_range(player.pos, enemies, COFFEE_RANGE)
            for target in random.sample(candidates, min(self.count, len(candidates))):
                center = pygame.Vector2(target.pos)
                self.explode(center, 1, now, player, enemies, killed)
                if self.evolved:  # 0.2초 간격으로 주변에서 작은 폭발 3번
                    for i in range(3):
                        spot = center + pygame.Vector2(random.uniform(20, 45), 0).rotate(random.uniform(0, 360))
                        self.pending.append((now + 200 * (i + 1), spot))
                self.last_shot = now

        for time, spot in self.pending:
            if time <= now:
                self.explode(spot, 0.6, now, player, enemies, killed)
        self.pending = [(time, spot) for time, spot in self.pending if time > now]

        self.fires.update(now, enemies, killed)
        self.explosions = [e for e in self.explosions if e[2] > now]
        return killed

    def draw(self, screen, offset, now):
        self.fires.draw(screen, offset, now)
        for center, radius, end in self.explosions:
            t = 1 - (end - now) / COFFEE_EFFECT_TIME          # 0 -> 1
            image = fx("fx_coffee", radius * 2 * (0.7 + 0.4 * t))
            image.set_alpha(int(255 * (1 - t * 0.8)))         # 점점 흐려짐
            screen.blit(image, image.get_rect(center=center - offset))


# ------------------------------------------------------------------
# 5. 보조배터리: 하늘에서 번개가 떨어짐  ->  벼락치기
# ------------------------------------------------------------------
class Battery(Weapon):
    name = "보조배터리"
    desc = "무작위 적에게 번개"
    evo_name = "벼락치기"
    evo_desc = "번개 +2, 옆의 적에게 전기가 튐"
    options = [
        ("번개 수 +1", "count", 1, 3),
        ("데미지 +8", "damage", 8, 4),
        ("공격 간격 -0.2초", "interval", -200, 3),
        ("번개 범위 +6", "radius", 6, 2),
        ("넉백 +1.5", "knockback", 1.5, 2),
    ]

    def __init__(self):
        super().__init__()
        self.count = 1
        self.damage = BATTERY_DAMAGE
        self.interval = BATTERY_INTERVAL
        self.radius = BATTERY_RADIUS
        self.knockback = 1.5
        self.bolts = []   # 그리기용 (떨어진 위치, 사라질 시각)
        self.sparks = []  # 그리기용: 옆으로 튄 전기 (시작, 끝, 사라질 시각)

    def update(self, now, player, enemies):
        killed = []
        if self.cooled(now, player, self.interval):
            candidates = enemies_in_range(player.pos, enemies, BATTERY_RANGE)
            if candidates:
                count = self.count + (2 if self.evolved else 0)
                for target in random.sample(candidates, min(count, len(candidates))):
                    center = pygame.Vector2(target.pos)
                    self.bolts.append((center, now + 150))
                    vfx.lightning(center, self.radius)
                    self.shine(center, 3)
                    for enemy in enemies_in_range(center, enemies, self.radius):
                        slow(enemy, now, player)
                        hit(enemy, self.damage, killed, self.knockback, center)
                    if self.evolved:  # 가까운 적 2마리에게 전기가 튐 (절반 데미지)
                        for enemy in enemies_in_range(center, enemies, CHAIN_RANGE)[:2]:
                            self.sparks.append((center, pygame.Vector2(enemy.pos), now + 150))
                            slow(enemy, now, player)
                            hit(enemy, self.damage * 0.5, killed)
                self.last_shot = now
                sound.play("thunder")

        self.bolts = [b for b in self.bolts if b[1] > now]
        self.sparks = [s for s in self.sparks if s[2] > now]
        return killed

    def draw(self, screen, offset, now):
        for center, _ in self.bolts:
            # 화면 위에서부터 지그재그로 내려오는 번개
            end = center - offset
            points = [(end.x + random.randint(-6, 6), y) for y in range(0, max(1, int(end.y)), 24)]
            points.append(end)
            if len(points) >= 2:
                pygame.draw.lines(screen, (120, 90, 20), False, points, 5)    # 어두운 테두리 (잔디 위에서도 잘 보이게)
                pygame.draw.lines(screen, (255, 226, 80), False, points, 3)
                pygame.draw.lines(screen, (255, 255, 255), False, points, 1)
            image = fx("fx_bolt", 18)
            screen.blit(image, image.get_rect(midbottom=end + (0, 4)))
        for start, end, _ in self.sparks:
            pygame.draw.line(screen, (150, 220, 255), start - offset, end - offset, 1)


# ------------------------------------------------------------------
# 6. 형광펜: 가까운 적 방향으로 일직선 레이저  ->  레이저 포인터
# ------------------------------------------------------------------
class Highlighter(Weapon):
    name = "형광펜"
    desc = "일직선 레이저"
    evo_name = "레이저 포인터"
    evo_desc = "훨씬 길고 굵은 레이저"
    options = [
        ("데미지 +6", "damage", 6, 4),
        ("레이저 길이 +40", "length", 40, 3),
        ("공격 간격 -0.3초", "interval", -300, 3),
        ("레이저 굵기 +4", "width", 4, 3),
        ("레이저 수 +1", "count", 1, 2),
        ("넉백 +2", "knockback", 2, 2),
    ]

    def __init__(self):
        super().__init__()
        self.damage = HIGHLIGHTER_DAMAGE
        self.length = HIGHLIGHTER_LENGTH
        self.width = HIGHLIGHTER_WIDTH
        self.interval = HIGHLIGHTER_INTERVAL
        self.count = 1
        self.knockback = 0
        self.beams = []  # 그리기용 (시작, 끝, 굵기, 사라질 시각)

    def update(self, now, player, enemies):
        killed = []
        interval = self.interval * (0.8 if "notes" in player.synergies else 1)
        if self.cooled(now, player, interval):
            targets = enemies_in_range(player.pos, enemies, PEN_RANGE)
            length = 700 if self.evolved else self.length
            width = self.width * (2 if self.evolved else 1)
            damage = self.damage * (1.5 if self.evolved else 1)
            start = pygame.Vector2(player.pos)
            # 가까운 적부터 레이저 수만큼, 각각 그 적 방향으로 쏨
            for target in targets[:self.count]:
                direction = aim_at(start, target.pos)
                for enemy in list(enemies):
                    to_enemy = enemy.pos - start
                    along = to_enemy.dot(direction)          # 레이저 방향으로 얼마나 떨어져 있나
                    across = abs(to_enemy.cross(direction))  # 레이저에서 옆으로 얼마나 벗어났나
                    if 0 <= along <= length and across <= width / 2 + enemy.rect.width / 2:
                        hit(enemy, damage, killed, self.knockback, start)
                self.beams.append((start, start + direction * length, width, now + HIGHLIGHTER_EFFECT_TIME))
                vfx.beam_end(start + direction * min(length, 250), (255, 120, 120) if self.evolved else (255, 245, 120))
                self.shine(start + direction * 20, 3)
                if "notes" in player.synergies:
                    vfx.glitter_line(start, start + direction * min(length, 300), (230, 255, 90))
            if targets:
                self.last_shot = now
                sound.play("laser")

        self.beams = [b for b in self.beams if b[3] > now]
        return killed

    def draw(self, screen, offset, now):
        color = (255, 80, 80) if self.evolved else (250, 240, 80)
        edge = (150, 30, 40) if self.evolved else (150, 130, 20)
        for start, end, width, finish in self.beams:
            t = max(0, (finish - now) / HIGHLIGHTER_EFFECT_TIME)   # 1 -> 0 (점점 가늘어짐)
            w = max(1, int(width * (0.4 + 0.6 * t)))
            a, b = start - offset, end - offset
            pygame.draw.line(screen, edge, a, b, w + 2)
            pygame.draw.line(screen, color, a, b, w)
            pygame.draw.line(screen, (255, 255, 240), a, b, max(1, w // 3))


# ------------------------------------------------------------------
# 7. 식판: 던지면 돌아오는 부메랑  ->  급식차
# ------------------------------------------------------------------
class Tray(Weapon):
    name = "식판"
    desc = "던지면 돌아오는 부메랑"
    evo_name = "급식차"
    evo_desc = "크기 2배, 돌아올 때도 공격"
    options = [
        ("데미지 +6", "damage", 6, 4),
        ("식판 개수 +1", "count", 1, 3),
        ("날아가는 거리 +30", "range", 30, 3),
        ("공격 간격 -0.3초", "interval", -300, 3),
        ("식판 크기 +25%", "size", 0.25, 2),
        ("넉백 +1.5", "knockback", 1.5, 2),
    ]

    def __init__(self):
        super().__init__()
        self.count = 1
        self.damage = TRAY_DAMAGE
        self.range = TRAY_RANGE
        self.interval = TRAY_INTERVAL
        self.size = 1
        self.knockback = 3.5
        self.flying = []  # 날아다니는 식판들. 각각 {"pos", "dir", "moved", "back", "hit"}

    def scale(self):
        return self.size * (2 if self.evolved else 1)

    def trail(self):
        for tray in self.flying:
            vfx.tray_trail(tray["pos"])
            self.shine(tray["pos"], 1)


    def update(self, now, player, enemies):
        killed = []
        if self.cooled(now, player, self.interval):
            targets = enemies_in_range(player.pos, enemies, PEN_RANGE)
            if targets:
                for i in range(self.count):
                    direction = aim_at(player.pos, targets[i % len(targets)].pos)
                    self.flying.append({
                        "pos": pygame.Vector2(player.pos), "dir": direction,
                        "moved": 0, "back": False, "hit": set(),
                    })
                self.last_shot = now

        knockback = self.knockback * (1.5 if "rush" in player.synergies else 1)
        for tray in self.flying:
            if not tray["back"]:
                tray["pos"] += tray["dir"] * TRAY_SPEED
                tray["moved"] += TRAY_SPEED
                if tray["moved"] >= self.range:
                    tray["back"] = True
                    tray["hit"] = set()  # 돌아올 때 다시 맞힐 수 있게 (급식차만)
            else:
                to_player = player.pos - tray["pos"]
                if to_player.length() <= TRAY_SPEED * 2:
                    tray["done"] = True
                    continue
                tray["pos"] += to_player.normalize() * TRAY_SPEED * 1.5

            if tray["back"] and not self.evolved:
                continue  # 식판은 날아갈 때만 공격
            for enemy in enemies_in_range(tray["pos"], enemies, TRAY_HIT_SIZE * self.scale()):
                if enemy not in tray["hit"]:
                    tray["hit"].add(enemy)
                    hit(enemy, self.damage, killed, knockback, player.pos)
                    if "rush" in player.synergies:
                        vfx.dust(enemy.pos)

        self.flying = [t for t in self.flying if "done" not in t]
        if now // 32 % 2 == 0:
            self.trail()
        return killed

    def draw(self, screen, offset, now):
        image = sprites.load("tray", sprites.TRAY)
        size = (round(image.get_width() * self.scale()), round(image.get_height() * self.scale()))
        image = pygame.transform.rotate(pygame.transform.scale(image, size), (now // 60 % 4) * 90)  # 빙글빙글
        for tray in self.flying:
            screen.blit(image, image.get_rect(center=tray["pos"] - offset))


# ------------------------------------------------------------------
# 8. 충전 케이블: 좌우로 번갈아 휘두르는 채찍  ->  고압 멀티탭
# ------------------------------------------------------------------
class Cable(Weapon):
    name = "충전 케이블"
    desc = "좌우로 휘두르는 채찍"
    evo_name = "고압 멀티탭"
    evo_desc = "맞은 적 주변 3마리에게 전기 연쇄"
    options = [
        ("데미지 +6", "damage", 6, 4),
        ("케이블 길이 +20", "length", 20, 3),
        ("공격 간격 -0.2초", "interval", -200, 3),
        ("넉백 +2", "knockback", 2, 2),
        ("케이블 폭 +10", "height", 10, 2),
        ("양쪽 동시 공격", "both", 1, 1),
    ]

    def __init__(self):
        super().__init__()
        self.damage = CABLE_DAMAGE
        self.length = CABLE_LENGTH
        self.interval = CABLE_INTERVAL
        self.height = CABLE_HEIGHT
        self.knockback = 6
        self.both = 0      # 1이면 좌우를 동시에 침
        self.side = 1      # 1 = 오른쪽, -1 = 왼쪽 (칠 때마다 바뀜)
        self.whips = []    # 그리기용 (시작, 끝, 사라질 시각)
        self.sparks = []   # 그리기용: 전기 연쇄 (시작, 끝, 사라질 시각)

    def update(self, now, player, enemies):
        killed = []
        if self.cooled(now, player, self.interval):
            first = None
            for side in ((1, -1) if self.both else (self.side,)):
                # 플레이어 옆의 네모 구역 안에 있는 적이 맞음
                area = pygame.Rect(0, 0, self.length, self.height)
                if side == 1:
                    area.midleft = player.pos
                else:
                    area.midright = player.pos
                for enemy in list(enemies):
                    if area.collidepoint(enemy.pos):
                        first = first or enemy
                        slow(enemy, now, player)
                        hit(enemy, self.damage, killed, self.knockback, player.pos)
                end = player.pos + pygame.Vector2(self.length * side, 0)
                self.whips.append((pygame.Vector2(player.pos), end, now + CABLE_EFFECT_TIME))
                vfx.whip_tip(end, self.evolved)
                self.shine(end, 3)
            if self.evolved and first:  # 처음 맞은 적 주변 3마리에게 전기 (60% 데미지)
                for enemy in enemies_in_range(first.pos, enemies, CHAIN_RANGE + 30)[:3]:
                    self.sparks.append((pygame.Vector2(first.pos), pygame.Vector2(enemy.pos), now + 150))
                    slow(enemy, now, player)
                    hit(enemy, self.damage * 0.6, killed)
            self.side = -self.side
            self.last_shot = now
            sound.play("whip")

        self.whips = [w for w in self.whips if w[2] > now]
        self.sparks = [s for s in self.sparks if s[2] > now]
        return killed

    def draw(self, screen, offset, now):
        color = (150, 220, 255) if self.evolved else (245, 245, 250)
        for start, end, finish in self.whips:
            t = max(0, (finish - now) / CABLE_EFFECT_TIME)   # 1 -> 0
            # 휘어진 선: 가운데가 위로 볼록한 곡선을 점 8개로
            a, b = start - offset, end - offset
            bend = pygame.Vector2(0, -10 - 6 * t)
            points = [a + (b - a) * (i / 7) + bend * (4 * (i / 7) * (1 - i / 7)) for i in range(8)]
            width = max(1, round(3 * t))
            pygame.draw.lines(screen, (40, 44, 60), False, points, width + 2)
            pygame.draw.lines(screen, color, False, points, width)
            pygame.draw.circle(screen, (200, 204, 214), points[-1], 2 + width)
        for start, end, _ in self.sparks:
            pygame.draw.line(screen, (60, 120, 200), start - offset, end - offset, 3)
            pygame.draw.line(screen, (200, 240, 255), start - offset, end - offset, 1)


# 무기 이름 -> 클래스 (레벨업에서 새 무기를 줄 때 씀)
WEAPON_CLASSES = {
    "pen": Pen,
    "book": Book,
    "ramen": Ramen,
    "coffee": Coffee,
    "battery": Battery,
    "highlighter": Highlighter,
    "tray": Tray,
    "cable": Cable,
}
