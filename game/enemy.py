# enemy.py - 적 (플레이어를 향해 다가옴)
import pygame
from settings import ENEMY_TYPES
import sprites

FLASH_TIME = 80  # 맞았을 때 하얗게 번쩍이는 시간 (ms)

# 적 종류 -> 글자 그림
ENEMY_GRIDS = {
    "homework": sprites.HOMEWORK,
    "exam": sprites.EXAM,
    "attendance": sprites.ATTENDANCE,
}


def get_enemy_image(kind):
    if kind in ENEMY_GRIDS:
        return sprites.load(kind, ENEMY_GRIDS[kind])
    if kind == "final_exam":
        return sprites.boss_image()
    # 그림이 없는 적은 settings의 색깔 네모로
    info = ENEMY_TYPES[kind]
    surface = pygame.Surface((info["size"], info["size"]))
    surface.fill(info["color"])
    return surface


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, kind, hp_multiplier=1):
        """kind: settings.ENEMY_TYPES의 이름 (예: "homework")
        hp_multiplier: 시간이 지날수록 커지는 체력 배율"""
        super().__init__()
        info = ENEMY_TYPES[kind]
        self.kind = kind
        self.normal_image = get_enemy_image(kind)
        self.flash_image = sprites.white_flash(self.normal_image)
        self.image = self.normal_image
        self.pos = pygame.Vector2(x, y)
        self.rect = self.image.get_rect(center=(x, y))

        self.max_hp = info["hp"] * hp_multiplier
        self.hp = self.max_hp
        self.speed = info["speed"]
        self.damage = info["damage"]
        self.xp = info["xp"]  # 죽을 때 떨어뜨리는 경험치
        self.is_boss = info["from_minute"] is None
        self.last_hit = -FLASH_TIME

    def update(self, player_pos):
        direction = player_pos - self.pos
        if direction.length() > 0:
            self.pos += direction.normalize() * self.speed
        self.rect.center = self.pos

        flashing = pygame.time.get_ticks() - self.last_hit < FLASH_TIME
        self.image = self.flash_image if flashing else self.normal_image

    def take_damage(self, amount):
        """데미지를 받고, 체력이 0 이하가 되면 죽었다고 알려줌 (True 반환)"""
        self.hp -= amount
        self.last_hit = pygame.time.get_ticks()
        if self.hp <= 0:
            self.kill()
            return True
        return False
