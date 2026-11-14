# settings.py - 모든 파일이 같이 쓰는 숫자 모음 (밸런스 조절은 여기서)

# 화면
WIDTH, HEIGHT = 320, 180   # 게임 내부 해상도 (픽셀아트용 작은 화면)
SCALE = 4                  # 실제 창 크기 = 내부 해상도 x SCALE
FPS = 60

# 플레이어
PLAYER_SPEED = 2

# 적
ENEMY_SPEED = 1
SPAWN_INTERVAL = 800       # 적 생성 간격 (밀리초)
SPAWN_DISTANCE = 200       # 플레이어로부터 이 거리에서 생성 (화면 밖)
MAX_ENEMIES = 60           # 동시에 존재할 수 있는 최대 적 수

# 무기 (자동 공격)
ATTACK_INTERVAL = 500      # 공격 간격 (밀리초)
ATTACK_RANGE = 150         # 이 거리 안의 적만 노림
BULLET_SPEED = 4
BULLET_LIFETIME = 1500     # 총알이 사라지기까지 시간 (밀리초)

# 배경
BG_COLOR = (30, 30, 40)
GRID_COLOR = (45, 45, 60)
GRID_SIZE = 32
