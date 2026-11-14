# enemy.py - 적 (플레이어를 향해 다가옴)
import pygame
from settings import ENEMY_SPEED


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill((200, 50, 50))
        self.pos = pygame.Vector2(x, y)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, player_pos):
        direction = player_pos - self.pos
        if direction.length() > 0:
            self.pos += direction.normalize() * ENEMY_SPEED
        self.rect.center = self.pos
