# settings.py - 모든 파일이 같이 쓰는 숫자 모음 (밸런스 조절은 여기서)
# 시간 단위는 전부 밀리초(ms). 1000 = 1초

# 화면
WIDTH, HEIGHT = 320, 180   # 게임 내부 해상도 (픽셀아트용 작은 화면)
SCALE = 4                  # 실제 창 크기 = 내부 해상도 x SCALE
FPS = 60
FONT_NAME = "malgungothic" # 한글이 나오는 글꼴 (윈도우 맑은 고딕)

# 게임 진행
GAME_DURATION = 10 * 60 * 1000   # 10분 버티면 클리어
START_MINUTE = 0           # 테스트용: 몇 분부터 시작할지 (보스 확인하려면 9로)

# 맵 (부경대 대연캠퍼스)
#   assets/images/map.png 가 있으면 그 그림을 쓰고, 없으면 campus.py가 맵을 그림
MAP_WIDTH, MAP_HEIGHT = 1280, 960
MAP_BORDER = 64            # 맵 가장자리 건물 구역 두께 (플레이어는 못 들어감)

# 효과음
SOUND_VOLUME = 0.5         # 0.0 ~ 1.0

# 플레이어
PLAYER_SPEED = 2
PLAYER_MAX_HP = 100
INVINCIBLE_TIME = 500      # 맞은 뒤 무적 시간 - 한 번에 여러 번 맞는 것 방지

# 경험치 / 레벨업
XP_PER_LEVEL = 5           # 다음 레벨까지 필요한 경험치 = 5 x 현재 레벨
GEM_PICKUP_RADIUS = 24     # 이 거리 안의 경험치 보석은 플레이어에게 끌려옴
GEM_COLLECT_DISTANCE = 6   # 이 거리까지 오면 획득
GEM_SPEED = 3

# 적 / 난이도 (계획서 4번)
#   생성 간격 = max(0.3초, 1.5초 - 0.12초 x 경과 분)
#   적 체력   = 기본 체력 x (1 + 0.15 x 경과 분)
SPAWN_INTERVAL_START = 1500
SPAWN_INTERVAL_MIN = 300
SPAWN_INTERVAL_DECREASE = 120   # 1분마다 줄어드는 양
ENEMY_HP_GROWTH = 0.15          # 1분마다 늘어나는 체력 비율
SPAWN_DISTANCE = 200       # 플레이어로부터 이 거리에서 생성 (화면 밖)
MAX_ENEMIES = 150          # 동시에 존재할 수 있는 최대 적 수

# 적 종류. "from_minute" 분부터 나오기 시작 (그 전 적들도 계속 나옴)
ENEMY_TYPES = {
    "homework":   {"name": "과제",   "from_minute": 0, "hp": 10, "speed": 0.6, "damage": 5,  "xp": 1, "size": 8, "color": (200, 70, 70)},
    "exam":       {"name": "시험지", "from_minute": 3, "hp": 20, "speed": 0.9, "damage": 10, "xp": 2, "size": 9, "color": (230, 150, 60)},
    "attendance": {"name": "출석부", "from_minute": 6, "hp": 8,  "speed": 1.4, "damage": 8,  "xp": 2, "size": 7, "color": (170, 80, 210)},
    # 보스: from_minute가 None이면 평소에는 안 나오고, BOSS_MINUTE에 한 번만 나옴
    "final_exam": {"name": "기말고사", "from_minute": None, "hp": 600, "speed": 0.45, "damage": 25, "xp": 30, "size": 24, "color": (240, 230, 200)},
}

# 보스 (기말고사)
BOSS_KIND = "final_exam"
BOSS_MINUTE = 9            # 9분에 등장

# 무기 1: 볼펜 투사체 (기본 무기) - 가장 가까운 적에게 발사
PEN_INTERVAL = 1000        # 공격 간격 - 계획서: 1초마다 발사
PEN_MIN_INTERVAL = 300     # 공격 속도 강화의 한계
PEN_DAMAGE = 10
PEN_MAX_COUNT = 5          # 발사 수 강화의 한계
PEN_RANGE = 150            # 이 거리 안의 적만 노림
BULLET_SPEED = 4
BULLET_LIFETIME = 1500     # 총알이 사라지기까지 시간

# 무기 2: 전공 서적 - 플레이어 주변을 회전
BOOK_DAMAGE = 8
BOOK_RADIUS = 24           # 회전 반경
BOOK_MAX_RADIUS = 56
BOOK_MAX_COUNT = 6
BOOK_ROTATE_SPEED = 0.18   # 1ms마다 도는 각도 (0.18 -> 2초에 한 바퀴)
BOOK_HIT_SIZE = 7          # 책과 적이 이 거리 안이면 맞음
BOOK_HIT_COOLDOWN = 500    # 같은 적을 다시 때리기까지 시간

# 무기 3: 커피 폭발 - 무작위 적 위치에 범위 공격
COFFEE_INTERVAL = 3000     # 계획서: 3초마다
COFFEE_DAMAGE = 15
COFFEE_RADIUS = 20
COFFEE_RANGE = 150         # 이 거리 안의 적 중에서 무작위로 고름
COFFEE_EFFECT_TIME = 300   # 폭발 그림이 보이는 시간

# 버프 아이템 (계획서 3번) - 30초마다 1개 생성
ITEM_SPAWN_INTERVAL = 30 * 1000
ITEM_SPAWN_MIN_DISTANCE = 60    # 플레이어로부터 이 거리 ~
ITEM_SPAWN_MAX_DISTANCE = 160   # 이 거리 사이에 생성
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

# 배경 (맵 바깥)
BG_COLOR = (30, 30, 40)
