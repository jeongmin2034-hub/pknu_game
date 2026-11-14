# enemy.py - 적 (플레이어를 향해 다가옴)
import pygame
from settings import ENEMY_TYPES


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, kind, hp_multiplier=1):
        """kind: settings.ENEMY_TYPES의 이름 (예: "homework")
        hp_multiplier: 시간이 지날수록 커지는 체력 배율"""
        super().__init__()
        info = ENEMY_TYPES[kind]
        self.kind = kind
        self.image = pygame.Surface((info["size"], info["size"]))
        self.image.fill(info["color"])
        self.pos = pygame.Vector2(x, y)
        self.rect = self.image.get_rect(center=(x, y))

        self.hp = info["hp"] * hp_multiplier
        self.speed = info["speed"]
        self.damage = info["damage"]
        self.xp = info["xp"]  # 죽을 때 떨어뜨리는 경험치

    def update(self, player_pos):
        direction = player_pos - self.pos
        if direction.length() > 0:
            self.pos += direction.normalize() * self.speed
        self.rect.center = self.pos

    def take_damage(self, amount):
        """데미지를 받고, 체력이 0 이하가 되면 죽었다고 알려줌 (True 반환)"""
        self.hp -= amount
        if self.hp <= 0:
            self.kill()
            return True
        return False
