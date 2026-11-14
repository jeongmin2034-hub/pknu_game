# main.py - 게임의 중심. 다른 파일을 불러와서 게임을 돌림
# 1주차: 핵심 루프 (이동, 적 생성·추적, 자동 공격, 충돌, 10분 타이머)
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
    GAME_DURATION,
    ENEMY_DAMAGE,
    BULLET_DAMAGE,
)
from player import Player
from enemy import Enemy
from weapon import Weapon

TEXT_COLOR = (230, 230, 230)


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


def format_time(ms):
    """밀리초를 '분:초' 글자로 바꾸기 (예: 600000 -> '10:00')"""
    seconds = max(0, ms) // 1000
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def draw_center_text(screen, font, lines):
    """화면 가운데에 여러 줄 글자 그리기 (게임오버/클리어 화면용)"""
    total_height = len(lines) * 14
    y = HEIGHT // 2 - total_height // 2
    for line in lines:
        text = font.render(line, False, TEXT_COLOR)
        screen.blit(text, text.get_rect(midtop=(WIDTH // 2, y)))
        y += 14


def main():
    pygame.init()
    window = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE))
    pygame.display.set_caption("My Game")
    screen = pygame.Surface((WIDTH, HEIGHT))  # 작은 화면에 그린 뒤 확대
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 16)

    running = True
    restart = True  # True면 게임을 처음 상태로 다시 세팅
    while running:
        clock.tick(FPS)
        now = pygame.time.get_ticks()

        # 0. 새 게임 세팅 (처음 시작할 때와 R로 재시작할 때)
        if restart:
            player = Player(0, 0)
            weapon = Weapon()
            enemies = pygame.sprite.Group()
            bullets = pygame.sprite.Group()
            last_spawn = now
            kills = 0
            start_time = now
            state = "playing"  # "playing" / "gameover" / "clear"
            restart = False

        # 1. 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r and state != "playing":
                    restart = True

        # 2. 업데이트 (게임 중일 때만 움직임)
        if state == "playing":
            elapsed = now - start_time

            if now - last_spawn >= SPAWN_INTERVAL and len(enemies) < MAX_ENEMIES:
                enemies.add(spawn_enemy(player.pos))
                last_spawn = now

            player.update()
            enemies.update(player.pos)
            weapon.update(player.pos, enemies, bullets)
            bullets.update()

            # 총알 ↔ 적: 총알은 사라지고, 적은 데미지를 받음
            hits = pygame.sprite.groupcollide(bullets, enemies, True, False)
            for hit_enemies in hits.values():
                for enemy in hit_enemies:
                    if enemy.take_damage(BULLET_DAMAGE):
                        kills += 1

            # 적 ↔ 플레이어: 닿으면 플레이어가 데미지를 받음
            if pygame.sprite.spritecollideany(player, enemies):
                player.take_damage(ENEMY_DAMAGE, now)

            # 게임 끝 판정
            if player.is_dead():
                state = "gameover"
                end_elapsed = elapsed
            elif elapsed >= GAME_DURATION:
                state = "clear"
                end_elapsed = GAME_DURATION

        # 3. 그리기 (카메라 적용)
        offset = get_camera_offset(player.pos)
        screen.fill(BG_COLOR)
        draw_grid(screen, offset)
        for enemy in enemies:
            draw_sprite(screen, enemy, offset)
        for bullet in bullets:
            draw_sprite(screen, bullet, offset)

        # 무적 중에는 깜빡이게 (0.1초마다 보였다 안 보였다)
        if not (player.is_invincible(now) and (now // 100) % 2 == 0):
            draw_sprite(screen, player, offset)

        # 화면 위 정보 (HP, 남은 시간, 처치 수)
        shown_elapsed = elapsed if state == "playing" else end_elapsed
        screen.blit(font.render(f"HP: {player.hp}/{player.max_hp}", False, TEXT_COLOR), (4, 4))
        timer_text = font.render(format_time(GAME_DURATION - shown_elapsed), False, TEXT_COLOR)
        screen.blit(timer_text, timer_text.get_rect(midtop=(WIDTH // 2, 4)))
        kills_text = font.render(f"Kills: {kills}", False, TEXT_COLOR)
        screen.blit(kills_text, kills_text.get_rect(topright=(WIDTH - 4, 4)))

        # 게임 끝 화면
        if state == "gameover":
            draw_center_text(screen, font, [
                "GAME OVER",
                f"Survived {format_time(end_elapsed)}  /  Kills {kills}",
                "R: Restart   ESC: Quit",
            ])
        elif state == "clear":
            draw_center_text(screen, font, [
                "CLEAR!",
                f"Kills {kills}",
                "R: Restart   ESC: Quit",
            ])

        pygame.transform.scale(screen, window.get_size(), window)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
