# enemy.py - 적 (플레이어를 향해 다가옴), 보스, 적이 쏘는 물음표
import math
import random

import pygame
from settings import (
    BOSS_PATTERNS, BOSS_BULLET_SPEED, BOSS_BULLET_DAMAGE, BOSS_BULLET_LIFETIME,
    CHARGE_WARN_TIME, CHARGE_DISTANCE, CHARGE_SPEED, CHARGE_REST_TIME,
    LUNCH_FOLLOWERS, LUNCH_GAP, LUNCH_ZOMBIE_HP,
    FINAL_RAGE_HP, FINAL_ENTER_TIME, JUMP_TIME, JUMP_RADIUS, JUMP_DAMAGE, SPIRAL_TIME,
    RAIN_RADIUS, RAIN_DAMAGE, FINAL_RAGE_SPEEDUP, FINAL_BULLET_SPEED, FINAL_BULLET_DAMAGE,
    LUNCH_BODY_DAMAGE_RATE, LUNCH_CHOPSTICK_INTERVAL, LUNCH_CHOPSTICK_DAMAGE,
    ENEMY_TYPES,
    KNOCKBACK_DECAY,
    ALARM_RANGE, ALARM_READY_TIME, ALARM_DASH_TIME, ALARM_REST_TIME, ALARM_DASH_SPEED,
    QUESTION_RANGE, QUESTION_INTERVAL, QUESTION_BULLET_SPEED,
    QUESTION_BULLET_DAMAGE, QUESTION_BULLET_LIFETIME,
)
import campus
import sprites
import vfx

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
    if kind == "lunch_line":
        return sprites.load_file("lunch_head")
    if kind == "lunch_body":
        return sprites.load_file("lunch_body_1")
    if kind == "final_exam" and sprites.load_file("final_exam"):
        return sprites.load_file("final_exam")
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
        self.is_boss = info.get("boss", False)
        # 보스는 계속 맞아서 늘 번쩍이므로 살짝만 밝아지게 (모습이 하얗게 묻히지 않게)
        self.flash_frames = [sprites.white_flash(frame, 45 if self.is_boss else 110) for frame in self.frames]
        self.image = self.frames[0]
        self.pos = pygame.Vector2(x, y)
        self.rect = self.image.get_rect(center=(x, y))

        self.hp_multiplier = hp_multiplier
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

        # 중간보스 패턴
        self.next_action = 0       # 다음 패턴 시각 (처음 나올 땐 3초 뒤)
        self.action_index = 0
        self.charge_dir = None     # 돌진 방향
        self.telegraph = None      # 돌진 경고선 (시작점, 끝점, 굵기) - main.py가 빨갛게 그림

        # 학식 대기줄: 머리는 지나온 길(trail)을 기억하고, 몸통은 그 길을 따라감
        self.trail = []
        self.followers = []
        self.leader = None         # 몸통이면 머리
        self.slot = 0              # 몸통이면 몇 번째 학생인지
        self.immune = False        # 줄에 붙어 있는 몸통은 맞아도 안 다침 (식판 방패)

        # 기말고사
        self.height = 0            # 공중에 뜬 높이 (점프, 등장). 높이 떠 있으면 안 맞고 안 부딪힘
        self.raged = False         # 체력 절반 아래에서 분노
        self.just_raged = False    # 방금 분노했는지 (main.py가 알림 띄우고 False로 바꿈)
        self.landed = False        # 방금 착지했는지 (main.py가 화면 흔들기)
        self.charges_left = 0
        self.spin = 0

    def update(self, player_pos, now, bullets):
        if self.leader is not None:   # 학식 대기줄 몸통: 머리가 지나온 길을 그대로 따라감
            self.follow()
            if now >= self.next_action:   # 젓가락 던지기 (학생마다 시간이 어긋나 있음)
                if self.next_action and player_pos != self.pos:
                    bullets.add(EnemyBullet(self.pos, player_pos - self.pos, now, "chopstick"))
                self.next_action = now + LUNCH_CHOPSTICK_INTERVAL
            return
        if self.next_action == 0:
            self.next_action = now + 3000
        if self.kind in BOSS_PATTERNS and self.boss_pattern(player_pos, now, bullets):
            self.after_move()
            return
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
        self.after_move()

    def after_move(self):
        self.rect.center = (self.pos.x, self.pos.y - self.height)
        if self.kind == "lunch_line":
            self.remember_trail()
        flashing = pygame.time.get_ticks() - self.last_hit < FLASH_TIME
        frame = (pygame.time.get_ticks() // 180) % len(self.frames)
        self.image = self.flash_frames[frame] if flashing else self.frames[frame]

    # ------------------------------------------------------------------
    # 중간보스 패턴
    # ------------------------------------------------------------------
    def boss_pattern(self, player_pos, now, bullets):
        """패턴 진행. 이번 프레임 움직임을 여기서 처리했으면 True"""
        info = BOSS_PATTERNS[self.kind]
        if self.mode == "enter":                      # 기말고사 등장: 하늘에서 떨어짐
            left = max(0, self.mode_end - now) / FINAL_ENTER_TIME
            self.height = 420 * left * left
            if now >= self.mode_end:
                self.height = 0
                self.mode, self.mode_end = "rest", now + 1200
                self.next_action = now + 2500
                self.landed = True
                vfx.final_landing(self.pos)
            return True
        if self.mode == "jump":                       # 점프: 포물선을 그리며 표시된 원으로 날아감
            t = min(1, 1 - (self.mode_end - now) / JUMP_TIME)
            self.pos = self.jump_from.lerp(self.jump_to, t)
            self.height = math.sin(t * math.pi) * 110
            if t >= 1:
                self.height = 0
                self.landed = True
                vfx.slam(self.pos)
                ring = 22 if self.raged else 16
                for i in range(ring):                        # 착지하면서 사방으로 F
                    bullets.add(EnemyBullet(self.pos, pygame.Vector2(1, 0).rotate(i * 360 / ring + self.spin), now, "grade_f"))
                if self.raged:                               # 분노: 착지 직후 플레이어 쪽으로 3발 더
                    for angle in (-12, 0, 12):
                        bullets.add(EnemyBullet(self.pos, (player_pos - self.pos or pygame.Vector2(1, 0)).rotate(angle), now, "grade_f"))
                self.spin += 15
                self.mode, self.mode_end = "rest", now + 600
            return True
        if self.mode == "spiral":                     # 회오리 탄막: 제자리에서 돌며 F를 뿌림
            if now >= self.shot_time:
                arms = 4 if self.raged else 3
                for k in range(arms):
                    bullets.add(EnemyBullet(self.pos, pygame.Vector2(1, 0).rotate(self.spin + k * 360 / arms), now, "grade_f"))
                self.spin += 14
                self.shot_time = now + (95 if self.raged else 115)
            if now >= self.mode_end:
                self.mode, self.mode_end = "rest", now + 400
            return True
        if self.mode == "warn":                       # 경고선 보여 주는 중 (제자리)
            if now >= self.mode_end:
                self.mode, self.mode_end = "charge", now + CHARGE_DISTANCE / CHARGE_SPEED * 1000 / 60
                self.telegraph = None
            return True
        if self.mode == "charge":                     # 경고선을 따라 돌진
            self.walk(self.charge_dir * CHARGE_SPEED * (1.3 if self.kind == "final_exam" else 1))
            if now >= self.mode_end:
                if self.charges_left > 0:              # 3연속 돌진: 다시 조준
                    self.charges_left -= 1
                    self.aim_charge(player_pos, now, 500)
                else:
                    self.mode, self.mode_end = "rest", now + CHARGE_REST_TIME
            return True
        if self.mode == "rest":                       # 돌진 뒤 잠깐 숨 고르기
            if now >= self.mode_end:
                self.mode = "walk"
            return True
        if self.kind == "final_exam" and not self.raged and self.hp < self.max_hp * FINAL_RAGE_HP:
            self.raged = self.just_raged = True        # 분노: 빨갛게 변하고 더 빨라짐
            rage_image = sprites.load_file("final_exam_rage")   # 분노 모습: 검붉게 타고 용암 균열, 불타는 눈
            self.frames = [rage_image] if rage_image else [sprites.tinted(f, (255, 90, 80)) for f in self.frames]
            self.flash_frames = [sprites.white_flash(frame, 45) for frame in self.frames]
            self.speed *= 1.3
        if now < self.next_action:
            return False
        action = info["actions"][self.action_index % len(info["actions"])]
        self.action_index += 1
        self.next_action = now + info["interval"] * (FINAL_RAGE_SPEEDUP if self.raged else 1)
        to_player = player_pos - self.pos
        if to_player.length() == 0:
            to_player = pygame.Vector2(1, 0)
        if action == "charge":
            self.aim_charge(player_pos, now, CHARGE_WARN_TIME)
            return True
        if action == "charge3":
            self.charges_left = 3 if self.raged else 2      # 분노하면 4연속
            self.aim_charge(player_pos, now, 750)
            return True
        if action == "jump":
            self.jump_from, self.jump_to = pygame.Vector2(self.pos), pygame.Vector2(player_pos)
            self.mode, self.mode_end = "jump", now + JUMP_TIME
            bullets.add(Hazard(self.jump_to, JUMP_RADIUS, now, JUMP_TIME, JUMP_DAMAGE))
            return True
        if action == "spiral":
            self.mode, self.mode_end, self.shot_time = "spiral", now + SPIRAL_TIME, now
            return True
        if action == "rain":                          # 빨간펜 폭격: 플레이어 주변에 원이 차오르다 폭발
            count = 11 if self.raged else 8
            spots = [pygame.Vector2(player_pos)] + [
                player_pos + pygame.Vector2(random.uniform(40, 130), 0).rotate(random.uniform(0, 360))
                for _ in range(count - 1)]
            for i, spot in enumerate(spots):
                bullets.add(Hazard(spot, RAIN_RADIUS, now, 900 + i * 110, RAIN_DAMAGE))
            return False
        if action == "fan" and self.kind == "final_exam":   # F 부채꼴 (분노하면 7발)
            spread = range(-60, 61, 15) if self.raged else range(-45, 46, 15)   # 9발 / 7발
            for volley in range(2):   # 두 번 연속 (두 번째는 살짝 엇갈리게)
                for angle in spread:
                    bullet = EnemyBullet(self.pos, to_player.rotate(angle + volley * 7.5), now, "grade_f")
                    bullet.pos -= bullet.velocity * volley * 14     # 두 번째 줄은 뒤에서 따라옴
                    bullets.add(bullet)
            return False
        if action == "fan":                           # 플레이어 쪽 부채꼴 3발
            for angle in (-20, 0, 20):
                bullets.add(EnemyBullet(self.pos, to_player.rotate(angle), now, "boss_paper"))
        elif action == "ring":                        # 사방 8발 (플레이어 쪽부터)
            for i in range(8):
                bullets.add(EnemyBullet(self.pos, to_player.rotate(i * 45), now, "grade_c"))
        return False

    def aim_charge(self, player_pos, now, warn_time):
        """플레이어 쪽으로 돌진 경고선을 그리고 warn_time 뒤에 돌진"""
        to_player = player_pos - self.pos
        self.charge_dir = to_player.normalize() if to_player.length() else pygame.Vector2(1, 0)
        self.mode, self.mode_end = "warn", now + warn_time
        width = self.rect.width * 0.8
        self.telegraph = (pygame.Vector2(self.pos), self.pos + self.charge_dir * CHARGE_DISTANCE, width)

    def start_entrance(self, now):
        """기말고사 등장 연출 시작 (하늘에서 쿵)"""
        self.mode, self.mode_end, self.height = "enter", now + FINAL_ENTER_TIME, 420
        self.next_action = now + 99999

    # ------------------------------------------------------------------
    # 학식 대기줄
    # ------------------------------------------------------------------
    def make_followers(self):
        """머리 뒤에 줄 설 학생들을 만들어서 돌려줌 (main.py가 적 목록에 넣음)"""
        self.trail = [pygame.Vector2(self.pos) for _ in range((LUNCH_FOLLOWERS + 1) * LUNCH_GAP // 2)]
        for i in range(LUNCH_FOLLOWERS):
            body = Enemy(self.pos.x, self.pos.y, "lunch_body", self.hp_multiplier)
            body.damage = self.damage * 0.7
            image = sprites.load_file(f"lunch_body_{i % 4 + 1}")
            body.frames, body.flash_frames = [image], [sprites.white_flash(image)]
            body.image = image
            body.leader, body.slot, body.immune = self, i + 1, True
            body.next_action = 1 + 3000 + i * LUNCH_CHOPSTICK_INTERVAL // LUNCH_FOLLOWERS
            body.is_boss = True      # 줄에 붙어 있는 동안은 건물 통과, 멀어져도 다시 데려오지 않음
            self.followers.append(body)
        return self.followers

    def remember_trail(self):
        """머리가 2픽셀 움직일 때마다 위치를 기록 (몸통 간격이 속도와 상관없이 일정하게)"""
        last = self.trail[-1] if self.trail else pygame.Vector2(self.pos)
        distance = last.distance_to(self.pos)
        steps = int(distance // 2)
        for i in range(1, steps + 1):
            self.trail.append(last.lerp(self.pos, i * 2 / distance))
        limit = (LUNCH_FOLLOWERS + 1) * LUNCH_GAP // 2
        del self.trail[:-limit]

    def follow(self):
        index = len(self.leader.trail) - 1 - self.slot * LUNCH_GAP // 2
        self.pos = pygame.Vector2(self.leader.trail[max(0, index)])
        self.rect.center = self.pos
        flashing = pygame.time.get_ticks() - self.last_hit < FLASH_TIME
        self.image = self.flash_frames[0] if flashing else self.frames[0]

    def detach(self):
        """줄에서 떨어져 나와 일반 몹이 됨"""
        self.leader, self.immune, self.is_boss = None, False, False
        self.max_hp = self.hp = LUNCH_ZOMBIE_HP * self.hp_multiplier
        self.weight = 0.6

    def drop_followers(self):
        """머리 체력이 줄어든 만큼 맨 뒤 학생부터 떨어져 나감"""
        should_stay = math.ceil(max(0, self.hp) / self.max_hp * LUNCH_FOLLOWERS)
        while len(self.followers) > should_stay:
            self.followers.pop().detach()

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
        if self.height > 20:   # 공중에 떠 있으면 안 맞음
            return False
        if self.immune:
            # 줄에 붙은 몸통: 데미지의 일부만 머리 체력에서 깎임 (마지막 한 방은 머리를 때려야 함)
            self.last_hit = pygame.time.get_ticks()
            head = self.leader
            head.hp = max(1, head.hp - amount * LUNCH_BODY_DAMAGE_RATE)
            head.drop_followers()
            return False
        self.hp -= amount
        if self.kind == "lunch_line":
            self.drop_followers()
        self.last_hit = pygame.time.get_ticks()
        if from_pos is not None:
            self.push(from_pos, knockback)
        if self.hp <= 0:
            self.kill()
            return True
        return False


class EnemyBullet(pygame.sprite.Sprite):
    """교수님 질문이 던지는 물음표. 플레이어가 맞으면 데미지"""

    def __init__(self, pos, direction, now, kind="qmark"):
        """kind: "qmark"(교수님 질문), "boss_paper"(조별과제), "grade_c"(중간고사)"""
        super().__init__()
        if kind == "qmark":
            self.image = sprites.with_outline(sprites.load("qmark", sprites.QMARK), (60, 30, 90))
            speed, self.damage, self.lifetime = QUESTION_BULLET_SPEED, QUESTION_BULLET_DAMAGE, QUESTION_BULLET_LIFETIME
        else:
            self.image = sprites.load_file(kind)
            speed, self.damage, self.lifetime = BOSS_BULLET_SPEED, BOSS_BULLET_DAMAGE, BOSS_BULLET_LIFETIME
            if kind == "grade_f":     # 기말고사 F: 더 빠르고 아픔
                speed, self.damage = FINAL_BULLET_SPEED, FINAL_BULLET_DAMAGE
            if kind == "chopstick":   # 젓가락은 날아가는 방향으로 돌려서 그림
                self.image = pygame.transform.rotate(self.image, -math.degrees(math.atan2(direction.y, direction.x)))
                self.damage = LUNCH_CHOPSTICK_DAMAGE
        self.pos = pygame.Vector2(pos)
        self.velocity = direction.normalize() * speed
        self.rect = self.image.get_rect(center=self.pos)
        self.spawn_time = now

    def update(self, now):
        self.pos += self.velocity
        self.rect.center = self.pos
        if now - self.spawn_time > self.lifetime:
            self.kill()


class Hazard(pygame.sprite.Sprite):
    """바닥 위험 표시: 빨간 원이 점점 차오르다가 폭발. 폭발하는 순간에만 데미지 (active)"""

    def __init__(self, pos, radius, now, delay, damage):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.radius = radius
        self.start, self.boom = now, now + delay
        self.damage = damage
        self.active = False
        self.image = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, now):
        if now >= self.boom + 120:
            self.kill()
            return
        if now >= self.boom and not self.active:
            self.active = True
            vfx.red_blast(self.pos, self.radius)
        self.image.fill((0, 0, 0, 0))
        c = self.image.get_width() // 2
        if not self.active:
            t = (now - self.start) / max(1, self.boom - self.start)      # 0 -> 1 차오름
            pygame.draw.circle(self.image, (220, 30, 40, 60), (c, c), self.radius)
            pygame.draw.circle(self.image, (240, 50, 50, 150), (c, c), max(1, int(self.radius * t)))
            pygame.draw.circle(self.image, (255, 110, 110, 230), (c, c), self.radius, 2)

    def hits(self, player_pos):
        return self.active and self.pos.distance_to(player_pos) <= self.radius + 6
