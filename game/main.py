# main.py - 게임의 중심. 다른 파일을 불러와서 게임을 돌림
# 1주차
import math
import random

import pygame
from settings import (
    WIDTH,
    HEIGHT,
    SCALE,
    FPS,
    BG_COLOR,
    GRID_COLOR,
    GRID_SIZE,
    SPAWN_INTERVAL,
    SPAWN_DISTANCE,
    MAX_ENEMIES,
)
from player import Player
from enemy import Enemy
from weapon import Weapon


def spawn_enemy(player_pos):
    """플레이어 주변 화면 밖 랜덤한 위치에 적 생성"""
    angle = random.uniform(0, math.tau)
    pos = player_pos + pygame.Vector2(SPAWN_DISTANCE, 0).rotate_rad(angle)
    return Enemy(pos.x, pos.y)


def get_camera_offset(player_pos):
    """플레이어가 화면 가운데 오도록 하는 카메라 위치"""
    return pygame.Vector2(
        round(player_pos.x - WIDTH / 2), round(player_pos.y - HEIGHT / 2)
    )


def draw_grid(screen, offset):
    """움직이는 게 보이도록 바닥에 격자 그리기"""
    for x in range(-int(offset.x) % GRID_SIZE, WIDTH, GRID_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT))
    for y in range(-int(offset.y) % GRID_SIZE, HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y))


def draw_sprite(screen, sprite, offset):
    """월드 좌표의 스프라이트를 카메라 기준으로 그리기"""
    screen.blit(sprite.image, pygame.Vector2(sprite.rect.topleft) - offset)


def main():
    pygame.init()
    window = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE))
    pygame.display.set_caption("My Game")
    screen = pygame.Surface((WIDTH, HEIGHT))  # 작은 화면에 그린 뒤 확대
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 16)

    player = Player(0, 0)
    weapon = Weapon()
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()

    last_spawn = 0
    kills = 0

    running = True
    while running:
        clock.tick(FPS)
        now = pygame.time.get_ticks()

        # 1. 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # 2. 업데이트
        if now - last_spawn >= SPAWN_INTERVAL and len(enemies) < MAX_ENEMIES:
            enemies.add(spawn_enemy(player.pos))
            last_spawn = now

        player.update()
        enemies.update(player.pos)
        weapon.update(player.pos, enemies, bullets)
        bullets.update()

        # 총알과 적이 닿으면 둘 다 제거
        hits = pygame.sprite.groupcollide(bullets, enemies, True, True)
        kills += sum(len(hit_enemies) for hit_enemies in hits.values())

        # 3. 그리기 (카메라 적용)
        offset = get_camera_offset(player.pos)
        screen.fill(BG_COLOR)
        draw_grid(screen, offset)
        for enemy in enemies:
            draw_sprite(screen, enemy, offset)
        for bullet in bullets:
            draw_sprite(screen, bullet, offset)
        draw_sprite(screen, player, offset)

        screen.blit(font.render(f"Kills: {kills}", False, (230, 230, 230)), (4, 4))

        pygame.transform.scale(screen, window.get_size(), window)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
