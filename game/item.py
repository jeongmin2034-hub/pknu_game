# item.py - 줍는 것들 (경험치 보석, 버프 아이템, 보물상자)
import math

import pygame
from settings import GEM_SPEED
import sprites


def gem_image(value):
    """경험치가 클수록 다른 색 보석: 1 = 파랑, 2~4 = 초록, 5 이상 = 빨강"""
    if value >= 5:
        return sprites.load("gem_big", sprites.GEM, {"C": (230, 70, 80), "A": (255, 200, 200)})
    if value >= 2:
        return sprites.load("gem_mid", sprites.GEM, {"C": (80, 210, 120), "A": (210, 255, 220)})
    return sprites.load("gem", sprites.GEM)


class ExpGem(pygame.sprite.Sprite):
    """적이 죽으면 떨어지는 경험치 보석. 가까이 가면 플레이어에게 끌려옴."""

    def __init__(self, x, y, value):
        super().__init__()
        self.image = gem_image(value)
        self.pos = pygame.Vector2(x, y)
        self.rect = self.image.get_rect(center=(x, y))
        self.value = value
        self.attracted = False  # True면 거리와 상관없이 플레이어에게 날아옴 (자석)

    def update(self, player_pos, pickup_radius):
        to_player = player_pos - self.pos
        distance = to_player.length()
        if distance < pickup_radius:
            self.attracted = True
        if self.attracted and distance > 0:
            self.pos += to_player.normalize() * min(GEM_SPEED, distance)
        self.rect.center = self.pos


def item_image(kind):
    """버프 아이템 그림 + 흰 테두리 (잔디 위에서 잘 보이게)"""
    return sprites.with_outline(sprites.load(kind, sprites.ITEM_GRIDS[kind]), (255, 255, 255))


class BuffItem(pygame.sprite.Sprite):
    """맵에 생기는 버프 아이템. kind는 settings.ITEMS의 이름 (예: "americano")"""

    def __init__(self, x, y, kind):
        super().__init__()
        self.kind = kind
        self.image = item_image(kind)
        self.pos = pygame.Vector2(x, y)
        self.rect = self.image.get_rect(center=(x, y))

    def draw(self, screen, offset, now):
        """둥실둥실 위아래로 떠 있게 그림 (줍는 판정 위치는 그대로)"""
        bob = round(math.sin(now / 250) * 1.5)
        screen.blit(self.image, pygame.Vector2(self.rect.topleft) - offset + (0, bob))


class Chest(BuffItem):
    """중간보스가 떨어뜨리는 보물상자 (A+ 성적표). 주우면 강화 여러 개"""

    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.kind = "chest"
        self.image = sprites.with_outline(sprites.load("chest", sprites.CHEST), (255, 255, 255))
        self.pos = pygame.Vector2(x, y)
        self.rect = self.image.get_rect(center=(x, y))
