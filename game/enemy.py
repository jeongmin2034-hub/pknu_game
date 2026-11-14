# enemy.py - 적 (플레이어를 향해 다가옴)
import pygame
from settings import ENEMY_SPEED, ENEMY_HP


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill((200, 50, 50))
        self.pos = pygame.Vector2(x, y)
        self.rect = self.image.get_rect(center=(x, y))
        self.hp = ENEMY_HP

    def update(self, player_pos):
        direction = player_pos - self.pos
        if direction.length() > 0:
            self.pos += direction.normalize() * ENEMY_SPEED
        self.rect.center = self.pos

    def take_damage(self, amount):
        """데미지를 받고, 체력이 0 이하가 되면 죽었다고 알려줌 (True 반환)"""
        self.hp -= amount
        if self.hp <= 0:
            self.kill()
            return True
        return False
