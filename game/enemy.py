# enemy.py - 적 (플레이어를 향해 다가옴), 보스, 적이 쏘는 물음표
import pygame
from settings import (
    ENEMY_TYPES,
    KNOCKBACK_DECAY,
    ALARM_RANGE, ALARM_READY_TIME, ALARM_DASH_TIME, ALARM_REST_TIME, ALARM_DASH_SPEED,
    QUESTION_RANGE, QUESTION_INTERVAL, QUESTION_BULLET_SPEED,
    QUESTION_BULLET_DAMAGE, QUESTION_BULLET_LIFETIME,
)
import campus
import sprites

FLASH_TIME = 80  # 맞았을 때 하얗게 번쩍이는 시간 (ms)


def get_enemy_image(kind):
    if kind == "homework":
        return sprites.load(kind, sprites.HOMEWORK)
    if kind == "report":
        return sprites.load(kind, sprites.REPORT)
    if kind == "alarm":
        return sprites.load(kind, sprites.ALARM)
    if kind == "exam":
        return sprites.load(kind, sprites.EXAM)
    if kind == "freerider":
        return sprites.load(kind, sprites.PLAYER_1, {"B": (80, 160, 90), "W": (80, 160, 90), "H": (110, 110, 120)})
    if kind == "freerider_mini":
        return sprites.load(kind, sprites.FREERIDER_MINI)
    if kind == "attendance":
        return sprites.load(kind, sprites.ATTENDANCE)
    if kind == "question":
        return sprites.load(kind, sprites.QUESTION)
    # 보스는 작은 그림을 크게 키워서 씀
    if kind == "team_project":
        return sprites.load_big(kind, sprites.REPORT, 4)
    if kind == "midterm":
        return sprites.load_big(kind, sprites.EXAM, 4)
    return sprites.boss_image()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, kind, hp_multiplier=1):
        """kind: settings.ENEMY_TYPES의 이름 (예: "homework")
        hp_multiplier: 시간이 지날수록 커지는 체력 배율"""
        super().__init__()
        info = ENEMY_TYPES[kind]
        self.kind = kind
        self.name = info["name"]
        self.frames = [get_enemy_image(kind)]
        second = sprites.load_file(kind + "_2")   # 두 번째 그림이 있으면 번갈아 보여줌 (날갯짓, 걷기)
        if second:
            self.frames.append(second)
        self.flash_frames = [sprites.white_flash(frame) for frame in self.frames]
        self.image = self.frames[0]
        self.pos = pygame.Vector2(x, y)
        self.rect = self.image.get_rect(center=(x, y))

        self.max_hp = info["hp"] * hp_multiplier
        self.hp = self.max_hp
        self.speed = info["speed"]
        self.damage = info["damage"]
        self.xp = info["xp"]          # 죽을 때 떨어뜨리는 경험치
        self.weight = info["weight"]  # 넉백을 받는 정도
        self.is_boss = info.get("boss", False)
        self.last_hit = -FLASH_TIME

        self.knock = pygame.Vector2(0, 0)  # 넉백으로 밀리는 속도
        self.stun_until = 0   # 이 시각까지 기절 (못 움직임)
        self.slow_until = 0   # 이 시각까지 느려짐
        self.mode = "walk"    # 알람시계: "walk" -> "ready" -> "dash" -> "rest"
        self.mode_end = 0
        self.last_shot = 0    # 교수님 질문: 마지막으로 물음표를 던진 시각
        self.rush_dir = None  # 출석부: 돌진 방향 (main.py가 생성할 때 정해 줌)
        self.last_pos = pygame.Vector2(x, y)  # 1초 전 위치 (건물에 걸려 못 움직이는지 확인용)

    def update(self, player_pos, now, bullets):
        # 넉백: 밀리는 힘이 점점 줄어듦
        self.walk(self.knock)
        self.knock *= KNOCKBACK_DECAY

        to_player = player_pos - self.pos
        distance = to_player.length()
        if self.rush_dir is not None:
            # 돌진: 플레이어를 따라가지 않고 정해진 방향으로 직진
            if now >= self.stun_until:
                self.walk(self.rush_dir * self.speed * (0.5 if now < self.slow_until else 1))
        elif now >= self.stun_until and distance > 0:
            speed = self.speed
            if self.kind == "alarm":
                speed = self.alarm_speed(now, distance)
            elif self.kind == "question" and distance < QUESTION_RANGE:
                speed = 0  # 가까이 오지 않고 멀리서 물음표를 던짐
                if now - self.last_shot >= QUESTION_INTERVAL:
                    bullets.add(EnemyBullet(self.pos, to_player, now))
                    self.last_shot = now
            if now < self.slow_until:
                speed *= 0.5
            self.walk(to_player.normalize() * speed)
        self.rect.center = self.pos

        flashing = pygame.time.get_ticks() - self.last_hit < FLASH_TIME
        frame = (pygame.time.get_ticks() // 180) % len(self.frames)
        self.image = self.flash_frames[frame] if flashing else self.frames[frame]

    def walk(self, step):
        """step만큼 이동. 건물은 못 지나감 (보스와 돌진하는 출석부는 건물 위로 지나감).
        움직였으면 True"""
        if self.is_boss or self.rush_dir is not None:
            self.pos += step
            return True
        return campus.move(self.pos, step)

    def is_waiting(self, now, player_pos):
        """일부러 멈춰 있는 중인지 (기절, 알람시계 준비, 교수님 질문이 멀리서 쏘는 중)"""
        if now < self.stun_until or self.mode == "ready":
            return True
        return self.kind == "question" and self.pos.distance_to(player_pos) < QUESTION_RANGE

    def alarm_speed(self, now, distance):
        """알람시계: 가까워지면 잠깐 멈췄다가(ready) 돌진(dash)하고 쉼(rest)"""
        if self.mode == "walk" and distance < ALARM_RANGE:
            self.mode, self.mode_end = "ready", now + ALARM_READY_TIME
        elif self.mode == "ready" and now >= self.mode_end:
            self.mode, self.mode_end = "dash", now + ALARM_DASH_TIME
        elif self.mode == "dash" and now >= self.mode_end:
            self.mode, self.mode_end = "rest", now + ALARM_REST_TIME
        elif self.mode == "rest" and now >= self.mode_end:
            self.mode = "walk"

        if self.mode == "ready":
            return 0
        if self.mode == "dash":
            return ALARM_DASH_SPEED
        return self.speed

    def push(self, from_pos, power):
        """from_pos 반대 방향으로 밀려남 (넉백)"""
        direction = self.pos - from_pos
        if power > 0 and direction.length() > 0:
            self.knock += direction.normalize() * power * self.weight

    def take_damage(self, amount, knockback=0, from_pos=None):
        """데미지를 받고, 체력이 0 이하가 되면 죽었다고 알려줌 (True 반환)"""
        self.hp -= amount
        self.last_hit = pygame.time.get_ticks()
        if from_pos is not None:
            self.push(from_pos, knockback)
        if self.hp <= 0:
            self.kill()
            return True
        return False


class EnemyBullet(pygame.sprite.Sprite):
    """교수님 질문이 던지는 물음표. 플레이어가 맞으면 데미지"""

    def __init__(self, pos, direction, now):
        super().__init__()
        self.image = sprites.with_outline(sprites.load("qmark", sprites.QMARK), (60, 30, 90))
        self.pos = pygame.Vector2(pos)
        self.velocity = direction.normalize() * QUESTION_BULLET_SPEED
        self.rect = self.image.get_rect(center=self.pos)
        self.damage = QUESTION_BULLET_DAMAGE
        self.spawn_time = now

    def update(self, now):
        self.pos += self.velocity
        self.rect.center = self.pos
        if now - self.spawn_time > QUESTION_BULLET_LIFETIME:
            self.kill()
