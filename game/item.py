# item.py - 줍는 것들 (경험치 보석, 버프 아이템)
import pygame
from settings import ITEMS, GEM_PICKUP_RADIUS, GEM_SPEED


class ExpGem(pygame.sprite.Sprite):
    """적이 죽으면 떨어지는 경험치 보석. 가까이 가면 플레이어에게 끌려옴."""

    def __init__(self, x, y, value):
        super().__init__()
        self.image = pygame.Surface((4, 4))
        self.image.fill((80, 160, 240))
        self.pos = pygame.Vector2(x, y)
        self.rect = self.image.get_rect(center=(x, y))
        self.value = value
        self.attracted = False  # True면 거리와 상관없이 플레이어에게 날아옴 (자석)

    def update(self, player_pos):
        to_player = player_pos - self.pos
        distance = to_player.length()
        if distance < GEM_PICKUP_RADIUS:
            self.attracted = True
        if self.attracted and distance > 0:
            self.pos += to_player.normalize() * min(GEM_SPEED, distance)
        self.rect.center = self.pos


class BuffItem(pygame.sprite.Sprite):
    """맵에 생기는 버프 아이템. kind는 settings.ITEMS의 이름 (예: "americano")"""

    def __init__(self, x, y, kind):
        super().__init__()
        self.kind = kind
        self.image = pygame.Surface((7, 7))
        self.image.fill((255, 255, 255))                          # 흰 테두리
        self.image.fill(ITEMS[kind]["color"], pygame.Rect(1, 1, 5, 5))  # 안쪽 색
        self.pos = pygame.Vector2(x, y)
        self.rect = self.image.get_rect(center=(x, y))
