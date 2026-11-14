# weapon.py - 무기 / 투사체
import pygame
from settings import ATTACK_INTERVAL, ATTACK_RANGE, BULLET_SPEED, BULLET_LIFETIME


class Bullet(pygame.sprite.Sprite):
    """날아가는 총알. 정해진 시간이 지나면 사라짐."""

    def __init__(self, pos, direction):
        super().__init__()
        self.image = pygame.Surface((4, 4))
        self.image.fill((240, 220, 80))
        self.pos = pygame.Vector2(pos)
        self.velocity = direction.normalize() * BULLET_SPEED
        self.rect = self.image.get_rect(center=self.pos)
        self.spawn_time = pygame.time.get_ticks()

    def update(self):
        self.pos += self.velocity
        self.rect.center = self.pos
        if pygame.time.get_ticks() - self.spawn_time > BULLET_LIFETIME:
            self.kill()


class Weapon:
    """일정 간격마다 가장 가까운 적에게 자동으로 총알을 쏨."""

    def __init__(self):
        self.last_shot = 0

    def find_nearest(self, player_pos, enemies):
        nearest = min(enemies, key=lambda e: player_pos.distance_squared_to(e.pos), default=None)
        if nearest is None or player_pos.distance_to(nearest.pos) > ATTACK_RANGE:
            return None
        return nearest

    def update(self, player_pos, enemies, bullets):
        now = pygame.time.get_ticks()
        if now - self.last_shot < ATTACK_INTERVAL:
            return

        target = self.find_nearest(player_pos, enemies)
        if target is None:
            return

        direction = target.pos - player_pos
        if direction.length() == 0:
            return

        bullets.add(Bullet(player_pos, direction))
        self.last_shot = now
