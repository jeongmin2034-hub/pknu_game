# item.py - 아이템 (경험치 보석, 회복 등)
import pygame


class Item(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((4, 4))
        self.image.fill((80, 160, 240))
        self.pos = pygame.Vector2(x, y)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        # TODO: 플레이어가 가까우면 끌려오기 등
        pass
