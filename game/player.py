# player.py - 플레이어
import pygame
from settings import (
    PLAYER_SPEED,
    PLAYER_MAX_HP,
    INVINCIBLE_TIME,
    XP_PER_LEVEL,
    AMERICANO_SPEED_BONUS,
    ENERGY_ATTACK_BONUS,
    SCHOLARSHIP_XP_MULTIPLIER,
)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill((80, 200, 120))
        self.pos = pygame.Vector2(x, y)
        self.rect = self.image.get_rect(center=(x, y))

        self.speed = PLAYER_SPEED
        self.max_hp = PLAYER_MAX_HP
        self.hp = PLAYER_MAX_HP
        self.last_hit = -INVINCIBLE_TIME  # 마지막으로 맞은 시각 (시작하자마자 맞을 수 있게)

        self.level = 1
        self.xp = 0
        self.buffs = {}  # 버프 이름 -> 버프가 끝나는 시각. 예: {"americano": 25000}

    def update(self, now):
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(
            (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a]),
            (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w]),
        )
        speed = self.speed
        if self.has_buff("americano", now):
            speed *= 1 + AMERICANO_SPEED_BONUS
        if direction.length() > 0:
            self.pos += direction.normalize() * speed
        self.rect.center = self.pos

    # ---------- 버프 ----------
    def add_buff(self, name, duration, now):
        self.buffs[name] = now + duration

    def has_buff(self, name, now):
        return self.buffs.get(name, 0) > now

    def attack_speed_multiplier(self, now):
        """에너지 드링크를 먹으면 1.5 (무기가 1.5배 빨리 공격)"""
        if self.has_buff("energy", now):
            return 1 + ENERGY_ATTACK_BONUS
        return 1

    # ---------- 체력 ----------
    def is_blinking(self, now):
        """맞은 직후 잠깐 동안 깜빡이며 무적"""
        return now - self.last_hit < INVINCIBLE_TIME

    def is_invincible(self, now):
        return self.is_blinking(now) or self.has_buff("student_id", now)

    def take_damage(self, amount, now):
        """데미지를 받음. 무적 중이면 무시."""
        if self.is_invincible(now):
            return
        self.hp = max(0, self.hp - amount)
        self.last_hit = now

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def is_dead(self):
        return self.hp <= 0

    # ---------- 경험치 / 레벨 ----------
    def xp_needed(self):
        return XP_PER_LEVEL * self.level

    def gain_xp(self, amount, now):
        if self.has_buff("scholarship", now):
            amount *= SCHOLARSHIP_XP_MULTIPLIER
        self.xp += amount

    def can_level_up(self):
        return self.xp >= self.xp_needed()

    def level_up(self):
        self.xp -= self.xp_needed()
        self.level += 1

    # ---------- 레벨업 강화 ----------
    def increase_max_hp(self):
        self.max_hp += 20
        self.hp += 20

    def increase_speed(self):
        self.speed *= 1.1
