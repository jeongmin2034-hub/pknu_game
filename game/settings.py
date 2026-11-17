# settings.py - 모든 파일이 같이 쓰는 숫자 모음 (밸런스 조절은 여기서)
# 시간 단위는 전부 밀리초(ms). 1000 = 1초

# 화면
WIDTH, HEIGHT = 960, 540   # 게임 내부 해상도 = 한 화면에 보이는 맵 넓이 (클수록 높은 곳에서 내려다본 느낌)
WINDOW_W, WINDOW_H = 1280, 720   # 실제 창 크기
SCALE = WINDOW_W / WIDTH   # 게임 화면이 창에서 몇 배로 보이는지
FPS = 60
FONT_NAME = "malgungothic" # 한글이 나오는 글꼴 (윈도우 맑은 고딕)

# 게임 진행
GAME_DURATION = 10 * 60 * 1000   # 10분 뒤 최종 보스 등장. 보스를 잡아야 클리어
# 난이도: (이름, 배율). 배율은 적의 체력·공격력·생성 수에 곱해짐 (1.0 = 아래 적 설정값 그대로)
DIFFICULTIES = [("쉬움", 0.6), ("보통", 0.8), ("어려움", 1.1)]
DEFAULT_DIFFICULTY = 1     # 처음 선택되어 있는 난이도 번호 (0 = 쉬움, 1 = 보통, 2 = 어려움)
START_MINUTE = 0           # 테스트용: 몇 분부터 시작할지 (최종 보스 확인하려면 9.9로)

# 맵 (부경대 대연캠퍼스)
#   assets/images/map.png 가 있으면 그 그림(실제 캠퍼스 맵)을 쓰고, 없으면 campus.py가 맵을 그림
#   아래 크기는 campus.py가 그리는 맵에만 적용됨
MAP_WIDTH, MAP_HEIGHT = 3840, 2880
MAP_BORDER = 64            # 맵 가장자리 건물 구역 두께 (플레이어는 못 들어감)

# 소리
#   처음 켰을 때의 기본값. 게임 안 "소리 설정"에서 바꾸면 volume.json에 저장됨
SOUND_VOLUME = 0.5         # 효과음 0.0 ~ 1.0
BGM_VOLUME = 0.3           # 배경음악

# 플레이어
PLAYER_SPEED = 2
PLAYER_SIZE = 1            # 플레이어 그림 크기 배율
PLAYER_MAX_HP = 100
INVINCIBLE_TIME = 500      # 맞은 뒤 무적 시간 - 한 번에 여러 번 맞는 것 방지

# 경험치 / 레벨업
XP_BASE = 5                # 다음 레벨까지 필요한 경험치 = 5 + 3 x 레벨 + 0.12 x 레벨²
XP_PER_LEVEL = 3
XP_GROWTH = 0.12           # 레벨이 높을수록 필요 경험치가 점점 더 많이 늘어남
GEM_PICKUP_RADIUS = 30     # 이 거리 안의 경험치 보석은 플레이어에게 끌려옴
GEM_COLLECT_DISTANCE = 6   # 이 거리까지 오면 획득
GEM_SPEED = 4
MAX_GEMS = 300             # 보석이 이보다 많아지면 새로 안 만들고 기존 보석에 합침
REROLL_COUNT = 3           # 한 판에 레벨업 선택지를 다시 뽑을 수 있는 횟수
LEVELUP_BLAST_RADIUS = 100 # 레벨업하면 이 거리 안의 적을 밀어냄
LEVELUP_BLAST_POWER = 8
LEVELUP_SHIELD_TIME = 1000 # 레벨업 직후 무적 시간
MAX_WEAPONS = 6
MAX_PASSIVES = 6
EVOLVE_LEVEL = 7           # 무기가 이 레벨이 되면 진화 가능
WEAPON_BONUS_DAMAGE = 0.1  # 옵션을 다 찍은 무기는 레벨업마다 데미지 +10% (강화 한계 없음)
KNOCKBACK_RATE = 0.5       # 모든 무기 넉백에 곱하는 배율

# 적 생성 / 난이도
#   1초마다 (4.5 + 경과 분)마리 생성 -> 느리지만 많이 (4.5마리 = 4마리 또는 5마리)
#   적 체력 = 기본 체력 x 1.2^경과 분 -> 1분마다 1.2배씩 계속 늘어남 (3분 1.7배, 5분 2.5배, 10분 6.2배)
#   보스 체력 = 기본 체력 x 등장 순간의 플레이어 레벨
SPAWN_INTERVAL = 1000
SPAWN_BASE = 4.5
SPAWN_PER_MINUTE = 1
ENEMY_HP_GROWTH = 1.2
SPAWN_DISTANCE = 600       # 플레이어로부터 이 거리에서 생성 (화면 밖)
RECYCLE_DISTANCE = 900     # 이보다 멀어진 적은 플레이어 근처로 다시 데려옴
STUCK_DISTANCE = 4         # 1초 동안 이만큼도 못 움직인 적은 건물에 걸린 것으로 보고 다시 데려옴
MAX_ENEMIES = 400          # 동시에 존재할 수 있는 최대 적 수
SWARM_CHANCE = 0.2         # 리포트 무리가 한쪽에서 몰려올 확률
RUSH_CHANCE = 0.5          # 1초마다 갈매기 돌진 무리가 나올 확률 (6분부터)
RUSH_SIZE = 8              # 돌진 무리 한 번에 몇 마리
KNOCKBACK_DECAY = 0.85     # 넉백으로 밀리는 힘이 매 프레임 줄어드는 비율

# 적 종류. "from_minute" 분부터 나오기 시작 (그 전 적들도 계속 나옴)
#   from_minute가 None이면 평소에는 안 나옴 (보스, 분열로 생기는 적)
#   weight: 넉백을 받는 정도 (1 = 그대로, 0.5 = 절반, 0 = 안 밀림)
ENEMY_TYPES = {
    "homework":   {"name": "과제",     "from_minute": 0, "hp": 12, "speed": 0.42, "damage": 5,  "xp": 1, "weight": 1},
    "report":     {"name": "길고양이",   "from_minute": 1, "hp": 8.4,  "speed": 0.5,  "damage": 4,  "xp": 1, "weight": 1.2},
    "alarm":      {"name": "알람시계", "from_minute": 2, "hp": 16.8, "speed": 0.45, "damage": 8,  "xp": 2, "weight": 1},
    "exam":       {"name": "시험지",   "from_minute": 4, "hp": 72, "speed": 0.32, "damage": 10, "xp": 4, "weight": 0.5},
    "freerider":  {"name": "팀플 무임승차자", "from_minute": 5, "hp": 30, "speed": 0.45, "damage": 7, "xp": 2, "weight": 1,
                   "split_into": "freerider_mini"},
    # 갈매기: 8마리가 뭉쳐서, 생성 순간의 플레이어 위치로 일직선 돌진 ("rush")
    "attendance": {"name": "갈매기",   "from_minute": 6, "hp": 12, "speed": 2.2,  "damage": 8,  "xp": 2, "weight": 1, "rush": True},
    "question":   {"name": "교수님 질문", "from_minute": 8, "hp": 26.4, "speed": 0.4, "damage": 6, "xp": 3, "weight": 1},
    "freerider_mini": {"name": "무임승차자", "from_minute": None, "hp": 9.6, "speed": 0.7, "damage": 4, "xp": 1, "weight": 1},
    # 보스: hp는 "플레이어 레벨 1당" 체력
    "team_project": {"name": "조별과제", "from_minute": None, "boss": True, "hp": 62.5,"speed": 0.7, "damage": 15, "xp": 20, "weight": 0},
    "lunch_line":   {"name": "학식 대기줄", "from_minute": None, "boss": True, "hp": 75, "speed": 0.9, "damage": 18, "xp": 30, "weight": 0},
    "lunch_body":   {"name": "줄 선 학생", "from_minute": None, "hp": 1,   "speed": 0.9, "damage": 12, "xp": 3, "weight": 0},
    "midterm":      {"name": "중간고사", "from_minute": None, "boss": True, "hp": 100,  "speed": 0.8, "damage": 20, "xp": 40, "weight": 0},
    "final_exam":   {"name": "기말고사", "from_minute": None, "boss": True, "hp": 220,  "speed": 1.0, "damage": 35, "xp": 0,  "weight": 0},
}

# 보스 등장 시각 (분, 종류). 중간보스는 보물상자를 떨어뜨리고, 최종 보스를 잡으면 클리어
BOSS_SCHEDULE = [(3, "team_project"), (5, "lunch_line"), (7, "midterm"), (10, "final_exam")]
FINAL_BOSS = "final_exam"

# 보스 등장 화면에 나오는 설명 (한 줄 소개, 공격 패턴, 공략 팁)
BOSS_INFO = {
    "team_project": {"title": "3분 중간보스", "intro": "아무도 안 하는 조별과제가 혼자 걸어온다",
                     "attacks": ["과제 종이 3장을 부채꼴로 던짐"],
                     "tip": "종이 사이 틈으로 옆으로 피하기"},
    "lunch_line":   {"title": "5분 중간보스", "intro": "배고픔에 미친 학생들이 줄지어 몰려온다",
                     "attacks": ["빨간 경고선을 따라 돌진", "줄 선 학생들이 젓가락을 던짐"],
                     "tip": "맨 앞 머리를 노리기 (몸통은 데미지 40%만)"},
    "midterm":      {"title": "7분 중간보스", "intro": "벼락치기로는 이길 수 없는 중간고사",
                     "attacks": ["C 학점 8발을 사방으로 뿌림", "빨간 경고선을 따라 돌진"],
                     "tip": "경고선 밖으로 비켜서고, C 학점 사이로 빠져나가기"},
    "final_exam":   {"title": "최종 보스", "intro": "모든 몹이 물러났다. 종강을 건 1대1 결투",
                     "attacks": ["점프 착지: 빨간 원에 떨어지며 사방으로 F 발사",
                                 "3연속 돌진 (경고선)", "F 학점 회오리 탄막",
                                 "빨간펜 폭격 (빨간 원이 차오르면 폭발)", "F 학점 부채꼴 발사"],
                     "tip": "체력이 절반 아래면 분노해서 더 빨라짐! 빨간 표시 밖으로"},
}

# 중간보스 패턴 (너무 어렵지 않게: 투사체는 느리게, 돌진은 경로를 미리 빨갛게 보여 줌)
#   "fan":    플레이어 쪽으로 부채꼴 3발 (조별과제: 과제 종이)
#   "ring":   사방으로 8발 (중간고사: C 학점)
#   "charge": 빨간 경고선 1초 -> 그 선을 따라 돌진
BOSS_PATTERNS = {
    "team_project": {"actions": ["fan"], "interval": 4500},
    "lunch_line":   {"actions": ["charge"], "interval": 6000},
    "midterm":      {"actions": ["ring", "charge"], "interval": 3500},
    "final_exam":   {"actions": ["jump", "fan", "charge3", "spiral", "rain"], "interval": 2400},
}
FINAL_RAGE_HP = 0.5            # 기말고사: 체력이 이 비율 아래로 내려가면 분노
FINAL_RAGE_SPEEDUP = 0.6       # 분노하면 패턴 간격에 곱함
FINAL_BULLET_SPEED = 1.6       # 기말고사 F 탄 속도 (다른 보스 1.0)
FINAL_BULLET_DAMAGE = 16
FINAL_ENTER_TIME = 1600        # 기말고사가 하늘에서 떨어지는 시간 (ms)
JUMP_TIME = 1100               # 점프해서 착지할 때까지 시간 (빨간 원이 이 동안 보임)
JUMP_RADIUS = 60               # 착지 충격 범위
JUMP_DAMAGE = 30
SPIRAL_TIME = 3000             # 회오리 탄막 지속 시간
RAIN_RADIUS = 40               # 빨간펜 폭격 원 크기
RAIN_DAMAGE = 22
BOSS_BULLET_SPEED = 1.0        # 보스 투사체 속도 (플레이어 이동 속도의 절반)
BOSS_BULLET_DAMAGE = 10
BOSS_BULLET_LIFETIME = 6000
CHARGE_WARN_TIME = 1000        # 돌진 전 경고선이 보이는 시간 (ms)
CHARGE_DISTANCE = 240          # 돌진 거리
CHARGE_SPEED = 3.2
CHARGE_REST_TIME = 700         # 돌진 뒤 잠깐 쉬는 시간

# 학식 대기줄: 머리 뒤로 학생들이 줄줄이 따라옴
LUNCH_FOLLOWERS = 11           # 몸통(줄 선 학생) 수
LUNCH_GAP = 14                 # 학생 사이 간격 (픽셀)
LUNCH_ZOMBIE_HP = 6             # 떨어져 나간 학생의 체력 (시간 배율이 곱해짐)
LUNCH_BODY_DAMAGE_RATE = 0.4   # 몸통을 때리면 데미지의 40%가 머리 체력에서 깎임
LUNCH_CHOPSTICK_INTERVAL = 5000  # 학생 한 명이 젓가락을 던지는 간격 (학생마다 시간을 어긋나게)
LUNCH_CHOPSTICK_DAMAGE = 6

# 알람시계: 가까워지면 잠깐 멈췄다가 돌진
ALARM_RANGE = 100
ALARM_READY_TIME = 500
ALARM_DASH_TIME = 600
ALARM_REST_TIME = 1500
ALARM_DASH_SPEED = 2.4

# 교수님 질문: 멀리서 물음표를 던짐
QUESTION_RANGE = 150
QUESTION_INTERVAL = 2500
QUESTION_BULLET_SPEED = 1.5
QUESTION_BULLET_DAMAGE = 8
QUESTION_BULLET_LIFETIME = 4000

# ------------------------------------------------------------------
# 무기 (8종). 여기는 처음 얻었을 때(Lv1)의 값
# 무기별 강화 옵션과 넉백은 weapon.py의 각 무기에 있음
# ------------------------------------------------------------------
# 볼펜: 가장 가까운 적에게 발사 (기본 무기)
PEN_INTERVAL = 800
PEN_DAMAGE = 15
PEN_RANGE = 260            # 이 거리 안의 적만 노림
BULLET_SPEED = 5
BULLET_LIFETIME = 1500
INK_RADIUS = 18            # 만년필: 맞은 자리 주변에 잉크가 튀는 범위

# 전공서적: 플레이어 주변을 회전
BOOK_DAMAGE = 12
BOOK_RADIUS = 50           # 회전 반경
BOOK_ROTATE_SPEED = 0.18   # 1ms마다 도는 각도 (0.18 -> 2초에 한 바퀴)
BOOK_HIT_SIZE = 8          # 책과 적이 이 거리 안이면 맞음
BOOK_HIT_COOLDOWN = 300    # 같은 적을 다시 때리기까지 시간
BOOK_STORM_INTERVAL = 4000 # 백과사전: 페이지 폭풍 간격
BOOK_STORM_TIME = 1000     # 페이지 폭풍: 책이 퍼졌다 돌아오는 시간
BOOK_STORM_REACH = 2.5     # 페이지 폭풍: 가장 멀리 퍼질 때 반경 배율

# 신라면: 바라보는 방향으로 화염 방사
RAMEN_TICK = 150           # 이 간격으로 화염 안의 적에게 데미지
RAMEN_DAMAGE = 4
RAMEN_LENGTH = 60
RAMEN_ANGLE = 28           # 화염이 퍼지는 각도 (도)
FIRE_TIME = 3000           # 바닥에 남는 불의 지속 시간
FIRE_TICK = 300
FIRE_DAMAGE = 3
FIRE_RADIUS = 16

# 커피: 무작위 적 위치에 범위 폭발
COFFEE_INTERVAL = 3000
COFFEE_DAMAGE = 15
COFFEE_RADIUS = 26
COFFEE_RANGE = 240         # 이 거리 안의 적 중에서 무작위로 고름
COFFEE_EFFECT_TIME = 300   # 폭발 그림이 보이는 시간

# 보조배터리: 하늘에서 번개
BATTERY_INTERVAL = 1200
BATTERY_DAMAGE = 18
BATTERY_RADIUS = 14
BATTERY_RANGE = 240
CHAIN_RANGE = 70           # 전기가 옆의 적에게 튀는 거리

# 형광펜: 일직선 레이저
HIGHLIGHTER_INTERVAL = 2000
HIGHLIGHTER_DAMAGE = 14
HIGHLIGHTER_LENGTH = 150
HIGHLIGHTER_WIDTH = 8
HIGHLIGHTER_EFFECT_TIME = 250

# 식판: 던지면 돌아오는 부메랑
TRAY_INTERVAL = 2200
TRAY_DAMAGE = 12
TRAY_RANGE = 100           # 날아가는 거리
TRAY_SPEED = 3
TRAY_HIT_SIZE = 10

# 충전 케이블: 좌우로 번갈아 휘두르는 채찍
CABLE_INTERVAL = 1300
CABLE_DAMAGE = 14
CABLE_LENGTH = 150
CABLE_HEIGHT = 36
CABLE_EFFECT_TIME = 150
CABLE_STUN_TIME = 400      # 고압 멀티탭: 전기 맞은 적이 멈추는 시간

SLOW_TIME = 2000           # 과충전 시너지: 느려지는 시간

# 시너지: 두 무기를 모두 Lv3 이상으로 올리면 자동 발동
SYNERGY_LEVEL = 3
SYNERGIES = {
    "morning":    {"name": "얼큰한 모닝커피", "weapons": ("ramen", "coffee"),      "desc": "폭발 자리에 불 장판"},
    "overcharge": {"name": "과충전",          "weapons": ("battery", "cable"),     "desc": "맞은 적 2초간 느려짐, 번개에서 전기가 1마리 튐"},
    "notes":      {"name": "필기 세트",       "weapons": ("pen", "highlighter"),   "desc": "볼펜 관통 +1, 형광펜 쿨타임 -20%"},
    "rush":       {"name": "학식 러시",       "weapons": ("book", "tray"),         "desc": "전공서적·식판 넉백 +50%"},
}

# 패시브 (5종): 플레이어 자신에 대한 강화. 한 레벨에 "per"만큼 효과가 커짐
#   (무기에 대한 강화는 weapon.py의 무기별 options에 있음)
PASSIVES = {
    "speed":    {"name": "이동 속도",     "desc": "이동 속도 +8%",         "per": 0.08, "max": 5},
    "maxhp":    {"name": "최대 HP",       "desc": "최대 HP +20",           "per": 20,   "max": 5},
    "regen":    {"name": "HP 재생",       "desc": "초당 HP +0.3",          "per": 0.3,  "max": 5},
    "armor":    {"name": "방어력",        "desc": "받는 피해 -1",          "per": 1,    "max": 5},
    "magnet":   {"name": "흡수 범위",     "desc": "경험치 흡수 거리 +25%", "per": 0.25, "max": 5},
}

# 버프 아이템 - 30초마다 1개 생성
ITEM_SPAWN_INTERVAL = 30 * 1000
ITEM_SPAWN_MIN_DISTANCE = 120   # 플레이어로부터 이 거리 ~
ITEM_SPAWN_MAX_DISTANCE = 520   # 이 거리 사이에 생성
ITEMS = {
    "americano":   {"name": "아메리카노",    "desc": "이동 속도 +30%",        "duration": 15000, "color": (140, 90, 50)},
    "energy":      {"name": "에너지 드링크", "desc": "공격 속도 +50%",        "duration": 15000, "color": (60, 220, 220)},
    "meal":        {"name": "학식",          "desc": "HP 30 회복",            "duration": 0,     "color": (245, 245, 245)},
    "scholarship": {"name": "장학금",        "desc": "경험치 2배",            "duration": 20000, "color": (250, 210, 40)},
    "student_id":  {"name": "학생증",        "desc": "무적",                  "duration": 5000,  "color": (80, 140, 250)},
    "magnet":      {"name": "자석",          "desc": "경험치 보석 전부 흡수", "duration": 0,     "color": (230, 60, 140)},
}
AMERICANO_SPEED_BONUS = 0.3
ENERGY_ATTACK_BONUS = 0.5
MEAL_HEAL = 30
SCHOLARSHIP_XP_MULTIPLIER = 2

# 보물상자 (중간보스가 떨어뜨림): 강화 개수와 확률(%)
CHEST_COUNTS = [2, 3, 5]
CHEST_CHANCES = [60, 30, 10]

# 배경 (맵 바깥)
BG_COLOR = (30, 30, 40)
