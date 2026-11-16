# sprites.py - 도트 그림 모음
#
# 그림을 글자로 그려 둠. 글자 하나 = 픽셀 하나, "." = 투명
# 각 글자가 어떤 색인지는 아래 PALETTE에 있음.
#
# assets/images/<이름>.png 파일이 있으면 글자 그림 대신 그 파일을 씀.
# 예) assets/images/player.png 를 넣으면 플레이어 그림이 바뀜
import os

import pygame

IMAGE_DIR = os.path.join(os.path.dirname(__file__), "assets", "images")

PALETTE = {
    "K": (30, 30, 40),      # 검정 (눈, 신발)
    "W": (245, 245, 240),   # 흰색 (종이)
    "E": (240, 228, 190),   # 누런 종이
    "G": (150, 160, 185),   # 회색 (줄)
    "V": (200, 200, 210),   # 은색
    "S": (240, 200, 160),   # 피부
    "H": (70, 45, 35),      # 머리카락
    "B": (40, 70, 150),     # 남색 (부경대 파랑)
    "L": (60, 60, 85),      # 바지
    "R": (215, 55, 55),     # 빨강
    "Y": (250, 210, 60),    # 노랑
    "O": (230, 140, 50),    # 주황
    "P": (140, 75, 190),    # 보라
    "M": (125, 80, 50),     # 커피색
    "T": (70, 200, 210),    # 청록 (캔)
    "C": (90, 170, 250),    # 하늘색 (보석)
    "A": (200, 235, 255),   # 아주 밝은 하늘색 (반짝임)
    "Q": (80, 200, 120),    # 초록
}

# ---------------- 플레이어 (걷는 동작 2장) ----------------
PLAYER_1 = [
    "..HHHH..",
    ".HHHHHH.",
    ".HSSSSH.",
    ".SSKSKS.",
    "..SSSS..",
    ".BBWWBB.",
    "SBBBBBBS",
    ".BBBBBB.",
    "..LL.LL.",
    "..KK.KK.",
]
PLAYER_2 = PLAYER_1[:8] + [
    ".LL..LL.",
    ".KK..KK.",
]

# ---------------- 적 ----------------
HOMEWORK = [   # 과제: 흰 종이
    "WWWWWV..",
    "WWWWWVV.",
    "WKWWKWWW",
    "WWWWWWWW",
    "WGGGGGGW",
    "WWWWWWWW",
    "WGGGGGWW",
    "WWWWWWWW",
]
EXAM = [       # 시험지: 누런 종이 + 빨간 채점
    "EEEEEEEEE",
    "ERRREEEEE",
    "EREREKEKE",
    "ERRREEEEE",
    "EEEEEEEEE",
    "EGGGGGGGE",
    "EEEEEEERE",
    "EGGRGGRGE",
    "EEEERREEE",
]
ATTENDANCE = [ # 출석부: 보라색 공책
    "PPPPPPW",
    "PYYYYPW",
    "PKPPKPW",
    "PPPPPPW",
    "PPPPPPW",
    "PPPPPPW",
    "PPPPPPW",
]

REPORT = [     # 리포트: 겹쳐진 종이 (조별과제 보스는 이 그림을 4배로)
    ".WWWWWW",
    "WWWWWWG",
    "WKWWKWG",
    "WWWWWWG",
    "WRRRRWG",
    "WWWWWWG",
    "WGGGGWG",
    "WWWWWW.",
]
ALARM = [      # 알람시계
    "V.RRRR.V",
    ".RRRRRR.",
    "RWWKWWWR",
    "RWWKWWWR",
    "RWWKKKWR",
    "RWWWWWWR",
    ".RRRRRR.",
    ".K....K.",
]
FREERIDER_MINI = [  # 무임승차자가 죽으면 나오는 작은 적
    ".HHHH.",
    ".SKSK.",
    ".SSSS.",
    "QQQQQQ",
    ".QQQQ.",
    ".L..L.",
]
QUESTION = [   # 교수님 질문: 물음표 말풍선
    ".PPPPPP.",
    "PPWWWWPP",
    "PPPPPWPP",
    "PPPPWWPP",
    "PPPWWPPP",
    "PPPPPPPP",
    "PPPWWPPP",
    ".PPPPPP.",
    "..PP....",
]
QMARK = [      # 교수님 질문이 던지는 물음표
    ".YYY.",
    "Y...Y",
    "...Y.",
    "..Y..",
    ".....",
    "..Y..",
]

# ---------------- 무기 ----------------
TRAY = [       # 식판
    "VVVVVVVV",
    "VWWVOOOV",
    "VWWVOOOV",
    "VVVVVVVV",
    "VQQVRRRV",
    "VVVVVVVV",
]
BULLET = [     # 볼펜 잉크
    ".BB.",
    "BCCB",
    "BCCB",
    ".BB.",
]
BOOK = [       # 전공 서적
    "BBBBBW",
    "BYYYBW",
    "BBBBBW",
    "BBBBBW",
    "BBYBBW",
    "BBBBBW",
    "BBBBBW",
]

# ---------------- 경험치 보석 ----------------
GEM = [
    "..C..",
    ".CAC.",
    "CCACC",
    ".CCC.",
    "..C..",
]

# ---------------- 보물상자 (A+ 성적표) ----------------
CHEST = [
    "YYYYYYYYYY",
    "YWWWWWWWWY",
    "YWWRWWWWWY",
    "YWRWRWWRWY",
    "YWRRRWRRRY",
    "YWRWRWWRWY",
    "YWWWWWWWWY",
    "YWGGGGGGWY",
    "YYYYYYYYYY",
]

# ---------------- 버프 아이템 ----------------
ITEM_GRIDS = {
    "americano": [
        "..KKKK..",
        ".KKKKKK.",
        "..WWWW..",
        "..MMMM..",
        "..MMMM..",
        "..WWWW..",
        "...WW...",
        "........",
    ],
    "energy": [
        "..VVVV..",
        "..TTTT..",
        "..TYTT..",
        "..TYYT..",
        "..TTYT..",
        "..TTTT..",
        "..VVVV..",
        "........",
    ],
    "meal": [
        "........",
        "..WWWW..",
        ".WWWWWW.",
        "OOOOOOOO",
        ".OOOOOO.",
        "..OOOO..",
        "........",
        "........",
    ],
    "scholarship": [
        "..YYYY..",
        ".YOOOOY.",
        "YOYOOYOY",
        "YOYOOYOY",
        "YOOYYOOY",
        ".YOOOOY.",
        "..YYYY..",
        "........",
    ],
    "student_id": [
        "........",
        "BBBBBBBB",
        "WSSWGGGW",
        "WSSWWWWW",
        "WKKWGGWW",
        "WWWWWWWW",
        "........",
        "........",
    ],
    "magnet": [
        "VV....VV",
        "RR....RR",
        "RR....RR",
        "RR....RR",
        "RRR..RRR",
        ".RRRRRR.",
        "..RRRR..",
        "........",
    ],
}

_cache = {}


def from_grid(grid, recolor=None):
    """글자 그림 -> pygame 그림. recolor로 색을 바꿀 수 있음 (예: {"C": (255,0,0)})"""
    colors = dict(PALETTE)
    if recolor:
        colors.update(recolor)
    surface = pygame.Surface((len(grid[0]), len(grid)), pygame.SRCALPHA)
    for y, row in enumerate(grid):
        for x, char in enumerate(row):
            if char != ".":
                surface.set_at((x, y), colors[char])
    return surface


def load(name, grid, recolor=None):
    """assets/images/<name>.png 가 있으면 그걸, 없으면 글자 그림을 씀 (한 번 만든 건 저장해 둠)"""
    if name not in _cache:
        path = os.path.join(IMAGE_DIR, name + ".png")
        if os.path.exists(path):
            _cache[name] = pygame.image.load(path).convert_alpha()
        else:
            _cache[name] = from_grid(grid, recolor)
    return _cache[name]


def load_file(name):
    """assets/images/<name>.png 가 있으면 그 그림, 없으면 None"""
    if name not in _cache:
        path = os.path.join(IMAGE_DIR, name + ".png")
        _cache[name] = pygame.image.load(path).convert_alpha() if os.path.exists(path) else None
    return _cache[name]


def load_big(name, grid, times):
    """글자 그림을 times배로 키운 그림 (보스, 진화 무기)"""
    if name not in _cache:
        path = os.path.join(IMAGE_DIR, name + ".png")
        if os.path.exists(path):
            _cache[name] = pygame.image.load(path).convert_alpha()
        else:
            small = from_grid(grid)
            size = (small.get_width() * times, small.get_height() * times)
            _cache[name] = pygame.transform.scale(small, size)
    return _cache[name]


def with_outline(surface, color):
    """그림 둘레에 1픽셀 테두리 (아이템이 잔디 위에서 잘 보이게)"""
    w, h = surface.get_size()
    result = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
    silhouette = pygame.mask.from_surface(surface).to_surface(
        setcolor=color, unsetcolor=(0, 0, 0, 0)
    )
    for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2)):
        result.blit(silhouette, (dx, dy))
    result.blit(surface, (1, 1))
    return result


def white_flash(surface):
    """맞았을 때 잠깐 보여줄 밝은 그림 (모양은 그대로, 색만 환하게)"""
    bright = surface.copy()
    bright.fill((110, 110, 110), special_flags=pygame.BLEND_RGB_ADD)
    return bright


def boss_image():
    """기말고사 보스 (48x48) - 커서 글자 그림 대신 도형으로 그린 뒤 2배로 키움"""
    if "final_exam" in _cache:
        return _cache["final_exam"]
    path = os.path.join(IMAGE_DIR, "final_exam.png")
    if os.path.exists(path):
        _cache["final_exam"] = pygame.image.load(path).convert_alpha()
        return _cache["final_exam"]

    s = pygame.Surface((24, 24), pygame.SRCALPHA)
    paper, line, red, dark = PALETTE["E"], PALETTE["G"], PALETTE["R"], PALETTE["K"]
    pygame.draw.rect(s, dark, (0, 0, 24, 24))                  # 테두리
    pygame.draw.rect(s, paper, (1, 1, 22, 22))                 # 종이
    pygame.draw.polygon(s, (190, 180, 150), [(17, 1), (22, 1), (22, 6)])  # 접힌 귀퉁이
    pygame.draw.line(s, dark, (4, 4), (9, 6))                  # 화난 눈썹
    pygame.draw.line(s, dark, (19, 4), (14, 6))
    s.fill(dark, (6, 7, 2, 2))                                 # 눈
    s.fill(dark, (16, 7, 2, 2))
    s.fill(red, (5, 11, 2, 9))                                 # 빨간 F
    s.fill(red, (5, 11, 7, 2))
    s.fill(red, (5, 15, 5, 2))
    for y in (13, 16, 19):                                     # 답안 줄
        pygame.draw.line(s, line, (14, y), (20, y))
    _cache["final_exam"] = pygame.transform.scale(s, (48, 48))  # 최종 보스라 2배로
    return _cache["final_exam"]
