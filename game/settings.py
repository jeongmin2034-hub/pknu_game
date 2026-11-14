# settings.py - 모든 파일이 같이 쓰는 숫자 모음 (밸런스 조절은 여기서)

# 화면
WIDTH, HEIGHT = 320, 180   # 게임 내부 해상도 (픽셀아트용 작은 화면)
SCALE = 4                  # 실제 창 크기 = 내부 해상도 x SCALE
FPS = 60

# 게임 진행
GAME_DURATION = 10 * 60 * 1000   # 10분 버티면 클리어 (밀리초)

# 플레이어
PLAYER_SPEED = 2
PLAYER_MAX_HP = 100
INVINCIBLE_TIME = 500      # 맞은 뒤 무적 시간 (밀리초) - 한 번에 여러 번 맞는 것 방지

# 적
ENEMY_SPEED = 1
ENEMY_HP = 10              # 적 기본 체력
ENEMY_DAMAGE = 10          # 적에게 닿았을 때 받는 데미지
SPAWN_INTERVAL = 800       # 적 생성 간격 (밀리초)
SPAWN_DISTANCE = 200       # 플레이어로부터 이 거리에서 생성 (화면 밖)
MAX_ENEMIES = 60           # 동시에 존재할 수 있는 최대 적 수

# 무기 (자동 공격)
ATTACK_INTERVAL = 1000     # 공격 간격 (밀리초) - 계획서: 1초마다 발사
BULLET_DAMAGE = 10         # 총알 한 발 데미지
ATTACK_RANGE = 150         # 이 거리 안의 적만 노림
BULLET_SPEED = 4
BULLET_LIFETIME = 1500     # 총알이 사라지기까지 시간 (밀리초)

# 배경
BG_COLOR = (30, 30, 40)
GRID_COLOR = (45, 45, 60)
GRID_SIZE = 32
