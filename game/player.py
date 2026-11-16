# player.py - 플레이어
import pygame
from settings import (
    PLAYER_SPEED,
    PLAYER_SIZE,
    PLAYER_MAX_HP,
    INVINCIBLE_TIME,
    XP_BASE,
    XP_PER_LEVEL,
    GEM_PICKUP_RADIUS,
    AMERICANO_SPEED_BONUS,
    ENERGY_ATTACK_BONUS,
    SCHOLARSHIP_XP_MULTIPLIER,
    PASSIVES,
)
import campus
import sprites


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # 걷는 그림 2장 (오른쪽 보기) + 좌우 뒤집은 그림 (왼쪽 보기)
        right = [sprites.load("player_1", sprites.PLAYER_1), sprites.load("player_2", sprites.PLAYER_2)]
        size = (round(right[0].get_width() * PLAYER_SIZE), round(right[0].get_height() * PLAYER_SIZE))
        right = [pygame.transform.scale(img, size) for img in right]
        left = [pygame.transform.flip(img, True, False) for img in right]
        self.frames = {1: right, -1: left}
        self.facing = 1    # 1 = 오른쪽, -1 = 왼쪽
        self.aim = pygame.Vector2(1, 0)  # 마지막으로 움직인 방향 (신라면 화염 방향)
        self.moving = False
        self.image = right[0]
        self.pos = pygame.Vector2(x, y)
        self.rect = self.image.get_rect(center=(x, y))

        self.max_hp = PLAYER_MAX_HP
        self.hp = PLAYER_MAX_HP
        self.last_hit = -INVINCIBLE_TIME  # 마지막으로 맞은 시각 (시작하자마자 맞을 수 있게)
        self.shield_until = 0             # 이 시각까지 무적 (레벨업 직후)

        self.level = 1
        self.xp = 0
        self.buffs = {}      # 버프 이름 -> 버프가 끝나는 시각. 예: {"americano": 25000}
        self.passives = {}   # 패시브 이름 -> 레벨. 예: {"might": 2}
        self.synergies = set()  # 지금 켜져 있는 시너지 이름들 (main.py가 채움)

    def update(self, now, dt, play_area):
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(
            (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a]),
            (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w]),
        )
        speed = PLAYER_SPEED * (1 + self.bonus("speed"))
        if self.has_buff("americano", now):
            speed *= 1 + AMERICANO_SPEED_BONUS
        self.moving = direction.length() > 0
        if self.moving:
            self.aim = direction.normalize()
            campus.move(self.pos, self.aim * speed)  # 건물은 못 지나감
            if direction.x != 0:
                self.facing = 1 if direction.x > 0 else -1

        # 맵 밖(건물 구역)으로 못 나가게
        self.pos.x = max(play_area.left, min(play_area.right, self.pos.x))
        self.pos.y = max(play_area.top, min(play_area.bottom, self.pos.y))

        # HP 재생 패시브
        self.heal(self.bonus("regen") * dt / 1000)

        # 움직이는 중이면 0.15초마다 그림을 바꿔서 걷는 것처럼
        frame = (now // 150) % 2 if self.moving else 0
        self.image = self.frames[self.facing][frame]
        self.rect = self.image.get_rect(center=self.pos)

    # ---------- 패시브 ----------
    def bonus(self, key):
        """패시브 효과 크기 = 레벨 x 레벨당 효과. 예: 공격력 Lv3 -> 0.3"""
        return self.passives.get(key, 0) * PASSIVES[key]["per"]

    def add_passive(self, key):
        self.passives[key] = self.passives.get(key, 0) + 1
        if key == "maxhp":
            self.max_hp += PASSIVES[key]["per"]
            self.hp += PASSIVES[key]["per"]

    def cooldown_mult(self, now):
        """무기 쿨타임에 곱하는 값. 에너지 드링크를 먹으면 작아짐 (더 빨리 공격)"""
        if self.has_buff("energy", now):
            return 1 / (1 + ENERGY_ATTACK_BONUS)
        return 1

    def pickup_radius(self):
        return GEM_PICKUP_RADIUS * (1 + self.bonus("magnet"))

    # ---------- 버프 ----------
    def add_buff(self, name, duration, now):
        self.buffs[name] = now + duration

    def has_buff(self, name, now):
        return self.buffs.get(name, 0) > now

    # ---------- 체력 ----------
    def is_blinking(self, now):
        """맞은 직후 잠깐 동안 깜빡이며 무적"""
        return now - self.last_hit < INVINCIBLE_TIME

    def is_invincible(self, now):
        return self.is_blinking(now) or self.has_buff("student_id", now) or now < self.shield_until

    def take_damage(self, amount, now):
        """데미지를 받음. 무적 중이면 무시. 실제로 맞았으면 True"""
        if self.is_invincible(now):
            return False
        amount = max(1, amount - self.bonus("armor"))  # 방어력 (최소 1은 받음)
        self.hp = max(0, self.hp - amount)
        self.last_hit = now
        return True

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def is_dead(self):
        return self.hp <= 0

    # ---------- 경험치 / 레벨 ----------
    def xp_needed(self):
        return XP_BASE + XP_PER_LEVEL * self.level

    def gain_xp(self, amount, now):
        if self.has_buff("scholarship", now):
            amount *= SCHOLARSHIP_XP_MULTIPLIER
        self.xp += amount

    def can_level_up(self):
        return self.xp >= self.xp_needed()

    def level_up(self):
        self.xp -= self.xp_needed()
        self.level += 1
