# weapon.py - 무기 3종 (볼펜, 전공 서적, 커피)
#
# 모든 무기는 같은 모양의 함수 2개를 가짐:
#   update(now, player_pos, enemies, attack_mult) -> 이번에 죽인 적 목록
#   draw(screen, offset)                          -> 무기 그리기
# 그래서 main.py에서는 무기 종류를 신경 쓰지 않고 똑같이 부를 수 있음.
import random

import pygame
from settings import (
    PEN_INTERVAL, PEN_MIN_INTERVAL, PEN_DAMAGE, PEN_MAX_COUNT, PEN_RANGE,
    BULLET_SPEED, BULLET_LIFETIME,
    BOOK_DAMAGE, BOOK_RADIUS, BOOK_MAX_RADIUS, BOOK_MAX_COUNT,
    BOOK_ROTATE_SPEED, BOOK_HIT_SIZE, BOOK_HIT_COOLDOWN,
    COFFEE_INTERVAL, COFFEE_DAMAGE, COFFEE_RADIUS, COFFEE_RANGE, COFFEE_EFFECT_TIME,
)


def enemies_in_range(pos, enemies, max_range):
    """pos에서 max_range 안에 있는 적들을 가까운 순서로"""
    near = [e for e in enemies if pos.distance_to(e.pos) <= max_range]
    near.sort(key=lambda e: pos.distance_squared_to(e.pos))
    return near


# ------------------------------------------------------------------
# 볼펜 투사체: 가장 가까운 적에게 발사 (기본 무기)
# ------------------------------------------------------------------
class Bullet(pygame.sprite.Sprite):
    """날아가는 총알. 정해진 시간이 지나면 사라짐."""

    def __init__(self, pos, direction, damage, now):
        super().__init__()
        self.image = pygame.Surface((4, 4))
        self.image.fill((240, 220, 80))
        self.pos = pygame.Vector2(pos)
        self.velocity = direction.normalize() * BULLET_SPEED
        self.rect = self.image.get_rect(center=self.pos)
        self.damage = damage
        self.spawn_time = now

    def update(self, now):
        self.pos += self.velocity
        self.rect.center = self.pos
        if now - self.spawn_time > BULLET_LIFETIME:
            self.kill()


class Pen:
    name = "볼펜"

    def __init__(self):
        self.count = 1                 # 한 번에 쏘는 총알 수
        self.interval = PEN_INTERVAL   # 공격 간격
        self.last_shot = 0
        self.bullets = pygame.sprite.Group()

    def update(self, now, player_pos, enemies, attack_mult):
        self.bullets.update(now)

        if now - self.last_shot >= self.interval / attack_mult:
            targets = enemies_in_range(player_pos, enemies, PEN_RANGE)
            if targets:
                # 가까운 적부터 한 발씩. 적이 총알 수보다 적으면 다시 처음부터
                for i in range(self.count):
                    target = targets[i % len(targets)]
                    direction = target.pos - player_pos
                    if direction.length() > 0:
                        self.bullets.add(Bullet(player_pos, direction, PEN_DAMAGE, now))
                self.last_shot = now

        # 총알 ↔ 적: 총알은 사라지고, 적은 데미지를 받음
        killed = []
        hits = pygame.sprite.groupcollide(self.bullets, enemies, True, False)
        for bullet, hit_enemies in hits.items():
            for enemy in hit_enemies:
                if enemy.alive() and enemy.take_damage(bullet.damage):
                    killed.append(enemy)
        return killed

    def draw(self, screen, offset):
        for bullet in self.bullets:
            screen.blit(bullet.image, pygame.Vector2(bullet.rect.topleft) - offset)

    # 레벨업 강화
    def can_add_count(self):
        return self.count < PEN_MAX_COUNT

    def add_count(self):
        self.count += 1

    def can_speed_up(self):
        return self.interval > PEN_MIN_INTERVAL

    def speed_up(self):
        self.interval = max(PEN_MIN_INTERVAL, self.interval * 0.8)


# ------------------------------------------------------------------
# 전공 서적: 플레이어 주변을 빙글빙글 돌며 닿는 적을 공격
# ------------------------------------------------------------------
class Book:
    name = "전공 서적"

    def __init__(self):
        self.count = 1
        self.radius = BOOK_RADIUS
        self.positions = []   # 책들의 현재 위치 (그리기용)
        self.last_hit = {}    # 적 -> 그 적을 마지막으로 때린 시각

    def update(self, now, player_pos, enemies, attack_mult):
        # 책 위치 계산: 시간에 따라 각도가 커짐 -> 회전. 책끼리는 같은 간격으로 벌어짐
        base_angle = now * BOOK_ROTATE_SPEED
        self.positions = [
            player_pos + pygame.Vector2(self.radius, 0).rotate(base_angle + 360 * i / self.count)
            for i in range(self.count)
        ]

        killed = []
        cooldown = BOOK_HIT_COOLDOWN / attack_mult
        for enemy in list(enemies):
            if now - self.last_hit.get(enemy, -cooldown) < cooldown:
                continue  # 이 적은 방금 맞았으니 잠깐 쉼
            for book_pos in self.positions:
                if enemy.pos.distance_to(book_pos) < BOOK_HIT_SIZE:
                    self.last_hit[enemy] = now
                    if enemy.take_damage(BOOK_DAMAGE):
                        killed.append(enemy)
                    break

        # 죽은 적은 기록에서 지움 (기록이 계속 쌓이지 않게)
        self.last_hit = {e: t for e, t in self.last_hit.items() if e.alive()}
        return killed

    def draw(self, screen, offset):
        for pos in self.positions:
            rect = pygame.Rect(0, 0, 6, 7)
            rect.center = pos - offset
            pygame.draw.rect(screen, (60, 90, 200), rect)
            pygame.draw.line(screen, (230, 230, 230), (rect.left + 1, rect.top + 1), (rect.left + 1, rect.bottom - 2))

    # 레벨업 강화
    def can_add_count(self):
        return self.count < BOOK_MAX_COUNT

    def add_count(self):
        self.count += 1

    def can_widen(self):
        return self.radius < BOOK_MAX_RADIUS

    def widen(self):
        self.radius += 8


# ------------------------------------------------------------------
# 커피 폭발: 일정 시간마다 무작위 적 위치에서 펑! 주변 적 모두 데미지
# ------------------------------------------------------------------
class Coffee:
    name = "커피"

    def __init__(self):
        self.radius = COFFEE_RADIUS
        self.damage = COFFEE_DAMAGE
        self.last_shot = 0
        self.explosions = []  # (폭발 위치, 그림이 사라질 시각)

    def update(self, now, player_pos, enemies, attack_mult):
        killed = []
        if now - self.last_shot >= COFFEE_INTERVAL / attack_mult:
            candidates = enemies_in_range(player_pos, enemies, COFFEE_RANGE)
            if candidates:
                center = pygame.Vector2(random.choice(candidates).pos)
                for enemy in list(enemies):
                    if enemy.pos.distance_to(center) <= self.radius:
                        if enemy.take_damage(self.damage):
                            killed.append(enemy)
                self.explosions.append((center, now + COFFEE_EFFECT_TIME))
                self.last_shot = now

        # 시간이 다 된 폭발 그림은 지움
        self.explosions = [(pos, end) for pos, end in self.explosions if end > now]
        return killed

    def draw(self, screen, offset):
        r = int(self.radius)
        for center, _ in self.explosions:
            circle = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)  # 반투명 원
            pygame.draw.circle(circle, (190, 120, 60, 130), (r, r), r)
            pygame.draw.circle(circle, (240, 200, 150, 220), (r, r), r, 1)
            screen.blit(circle, center - offset - pygame.Vector2(r, r))

    # 레벨업 강화
    def widen(self):
        self.radius += 6

    def strengthen(self):
        self.damage += 10
