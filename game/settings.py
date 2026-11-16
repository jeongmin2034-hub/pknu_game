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
XP_BASE = 5                # 다음 레벨까지 필요한 경험치 = 5 + 3 x 현재 레벨
XP_PER_LEVEL = 3
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
MAX_WEAPON_LEVEL = 10      # 무기 강화 한계

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
    "homework":   {"name": "과제",     "from_minute": 0, "hp": 10, "speed": 0.42, "damage": 5,  "xp": 1, "weight": 1},
    "report":     {"name": "길고양이",   "from_minute": 1, "hp": 7,  "speed": 0.5,  "damage": 4,  "xp": 1, "weight": 1.2},
    "alarm":      {"name": "알람시계", "from_minute": 2, "hp": 14, "speed": 0.45, "damage": 8,  "xp": 2, "weight": 1},
    "exam":       {"name": "시험지",   "from_minute": 4, "hp": 60, "speed": 0.32, "damage": 10, "xp": 4, "weight": 0.5},
    "freerider":  {"name": "팀플 무임승차자", "from_minute": 5, "hp": 25, "speed": 0.45, "damage": 7, "xp": 2, "weight": 1,
                   "split_into": "freerider_mini"},
    # 갈매기: 8마리가 뭉쳐서, 생성 순간의 플레이어 위치로 일직선 돌진 ("rush")
    "attendance": {"name": "갈매기",   "from_minute": 6, "hp": 10, "speed": 2.2,  "damage": 8,  "xp": 2, "weight": 1, "rush": True},
    "question":   {"name": "교수님 질문", "from_minute": 8, "hp": 22, "speed": 0.4, "damage": 6, "xp": 3, "weight": 1},
    "freerider_mini": {"name": "무임승차자", "from_minute": None, "hp": 8, "speed": 0.7, "damage": 4, "xp": 1, "weight": 1},
    # 보스: hp는 "플레이어 레벨 1당" 체력
    "team_project": {"name": "조별과제", "from_minute": None, "boss": True, "hp": 25,  "speed": 0.7, "damage": 15, "xp": 20, "weight": 0},
    "midterm":      {"name": "중간고사", "from_minute": None, "boss": True, "hp": 40,  "speed": 0.8, "damage": 20, "xp": 40, "weight": 0},
    "final_exam":   {"name": "기말고사", "from_minute": None, "boss": True, "hp": 60,  "speed": 0.9, "damage": 25, "xp": 0,  "weight": 0},
}

# 보스 등장 시각 (분, 종류). 중간보스는 보물상자를 떨어뜨리고, 최종 보스를 잡으면 클리어
BOSS_SCHEDULE = [(3, "team_project"), (7, "midterm"), (10, "final_exam")]
FINAL_BOSS = "final_exam"

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
BOOK_DAMAGE = 8
BOOK_RADIUS = 34           # 회전 반경
BOOK_ROTATE_SPEED = 0.18   # 1ms마다 도는 각도 (0.18 -> 2초에 한 바퀴)
BOOK_HIT_SIZE = 8          # 책과 적이 이 거리 안이면 맞음
BOOK_HIT_COOLDOWN = 500    # 같은 적을 다시 때리기까지 시간

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
CABLE_LENGTH = 70
CABLE_HEIGHT = 24
CABLE_EFFECT_TIME = 150

SLOW_TIME = 2000           # 과충전 시너지: 느려지는 시간

# 시너지: 두 무기를 모두 Lv3 이상으로 올리면 자동 발동
SYNERGY_LEVEL = 3
SYNERGIES = {
    "morning":    {"name": "얼큰한 모닝커피", "weapons": ("ramen", "coffee"),      "desc": "폭발 자리에 불 장판"},
    "overcharge": {"name": "과충전",          "weapons": ("battery", "cable"),     "desc": "맞은 적 2초간 느려짐"},
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
