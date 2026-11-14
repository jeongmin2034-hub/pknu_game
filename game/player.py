# player.py - 플레이어
import pygame
from settings import PLAYER_SPEED, PLAYER_MAX_HP, INVINCIBLE_TIME


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill((80, 200, 120))
        self.pos = pygame.Vector2(x, y)
        self.rect = self.image.get_rect(center=(x, y))

        self.max_hp = PLAYER_MAX_HP
        self.hp = PLAYER_MAX_HP
        self.last_hit = -INVINCIBLE_TIME  # 마지막으로 맞은 시각 (시작하자마자 맞을 수 있게)

    def update(self):
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(
            (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a]),
            (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w]),
        )
        if direction.length() > 0:
            self.pos += direction.normalize() * PLAYER_SPEED
        self.rect.center = self.pos

    def is_invincible(self, now):
        """맞은 직후 잠깐 동안은 무적"""
        return now - self.last_hit < INVINCIBLE_TIME

    def take_damage(self, amount, now):
        """데미지를 받음. 무적 중이면 무시."""
        if self.is_invincible(now):
            return
        self.hp = max(0, self.hp - amount)
        self.last_hit = now

    def is_dead(self):
        return self.hp <= 0
