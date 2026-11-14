# player.py - 플레이어
import pygame
from settings import PLAYER_SPEED


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill((80, 200, 120))
        self.pos = pygame.Vector2(x, y)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(
            (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a]),
            (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w]),
        )
        if direction.length() > 0:
            self.pos += direction.normalize() * PLAYER_SPEED
        self.rect.center = self.pos
