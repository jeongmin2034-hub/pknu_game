# sound.py - 효과음과 배경음악
#
# 소리 파일 없이도 되도록, 파이썬으로 "삐-" 하는 소리를 직접 만들어서 씀 (8비트 게임 느낌).
# assets/sounds/<이름>.wav (또는 .ogg) 파일이 있으면 그 파일을 대신 씀.
#   이름: shoot, hit, kill, gem, item, levelup, hurt, explosion, boss, gameover, clear,
#         thunder, laser, whip, chest
#
# 배경음악도 파이썬으로 만든 짧은 8비트 곡을 반복 재생함.
# assets/sounds/bgm.ogg (또는 .mp3, .wav) 파일을 넣으면 그 곡을 대신 틂.
#
# 사용법:  import sound  ->  sound.init() 한 번  ->  sound.play("shoot")
import array
import json
import math
import os
import random
import sys

import pygame
from settings import SOUND_VOLUME, BGM_VOLUME

SOUND_DIR = os.path.join(os.path.dirname(__file__), "assets", "sounds")
# 볼륨 설정을 저장해 두는 파일.
# 실행파일(.exe)로 돌릴 때는 코드가 임시 폴더에 풀리므로, exe 옆에 저장해야 다음에도 남아 있음
if getattr(sys, "frozen", False):
    VOLUME_FILE = os.path.join(os.path.dirname(sys.executable), "volume.json")
else:
    VOLUME_FILE = os.path.join(os.path.dirname(__file__), "volume.json")

# 지금 볼륨 (0.0 ~ 1.0). "sfx" = 효과음, "bgm" = 배경음악
volume = {"sfx": SOUND_VOLUME, "bgm": BGM_VOLUME}
RATE = 44100

_sounds = {}
_last_played = {}  # 같은 소리가 너무 겹쳐서 시끄럽지 않게, 마지막으로 낸 시각 기록

# 같은 소리를 다시 내려면 최소 이만큼(ms) 기다림
MIN_GAP = {"shoot": 60, "hit": 50, "kill": 40, "gem": 50, "explosion": 80, "thunder": 80}


def tone(freq_start, freq_end, duration, wave="square", volume=0.3):
    """freq_start에서 freq_end로 음이 변하는 소리. 점점 작아짐.
    wave: "square"(삐-), "sine"(부드러움), "noise"(치익-)"""
    count = int(RATE * duration)
    samples = array.array("h")
    phase = 0.0
    for i in range(count):
        t = i / count
        phase += (freq_start + (freq_end - freq_start) * t) / RATE
        if wave == "square":
            v = 1.0 if phase % 1 < 0.5 else -1.0
        elif wave == "sine":
            v = math.sin(phase * math.tau)
        else:
            v = random.uniform(-1, 1)
        value = int(v * (1 - t) * volume * 32767)
        samples.append(value)  # 왼쪽
        samples.append(value)  # 오른쪽
    return samples


def melody(notes, note_time, wave="square", volume=0.2):
    """여러 음을 이어 붙이기 (레벨업, 클리어 같은 짧은 멜로디)"""
    samples = array.array("h")
    for freq in notes:
        samples.extend(tone(freq, freq, note_time, wave, volume))
    return samples


def make_all():
    """만들어 쓰는 소리 목록. 숫자를 바꿔서 소리를 조절할 수 있음."""
    return {
        "shoot": tone(900, 600, 0.05, "square", 0.08),
        "hit": tone(0, 0, 0.04, "noise", 0.08),
        "kill": tone(500, 150, 0.08, "square", 0.12),
        "gem": tone(1200, 1700, 0.05, "sine", 0.15),
        "item": tone(660, 1320, 0.18, "sine", 0.3),
        "levelup": melody([523, 659, 784, 1047], 0.08),
        "hurt": tone(220, 70, 0.15, "square", 0.22),
        "explosion": tone(0, 0, 0.3, "noise", 0.25),
        "boss": melody([110, 0, 110, 0, 82], 0.15, "square", 0.3),
        "gameover": melody([392, 330, 262, 196], 0.18),
        "clear": melody([523, 659, 784, 1047, 0, 1047, 1319], 0.1),
        "thunder": tone(1800, 200, 0.12, "noise", 0.2),
        "laser": tone(1500, 900, 0.12, "square", 0.1),
        "whip": tone(300, 900, 0.06, "noise", 0.15),
        "chest": melody([784, 988, 1175, 1568, 1175, 1568], 0.09),
    }


# 배경음악 악보: 음 높이(Hz), 0은 쉼표. 한 칸 = 8분음표. 4마디를 반복
A2, C3, D3, E3, F3, G3 = 110, 131, 147, 165, 175, 196
A4, B4, C5, D5, E5, G5, A5 = 440, 494, 523, 587, 659, 784, 880
BGM_MELODY = [
    A4, 0, C5, E5, A5, 0, E5, C5,   D5, 0, E5, D5, C5, 0, B4, 0,
    C5, 0, E5, G5, E5, 0, C5, E5,   D5, C5, B4, C5, A4, 0, 0, 0,
    A4, 0, C5, E5, A5, 0, G5, E5,   D5, 0, E5, G5, A5, 0, G5, 0,
    E5, 0, D5, C5, D5, 0, B4, D5,   C5, B4, A4, B4, A4, 0, 0, 0,
]
BGM_BASS = [A2, A2, F3, F3, C3, C3, G3, E3, A2, A2, D3, D3, F3, G3, A2, A2]  # 한 칸 = 2분음표
BGM_NOTE_TIME = 0.2  # 8분음표 하나의 길이 (초)


def make_bgm():
    """멜로디(삐-)와 베이스(부드러운 소리)를 섞어서 한 곡으로"""
    melody_part = array.array("h")
    for freq in BGM_MELODY:
        volume = 0.12 if freq else 0  # 쉼표는 소리 없이
        melody_part.extend(tone(freq, freq, BGM_NOTE_TIME, "square", volume))
    bass_part = array.array("h")
    for freq in BGM_BASS:
        bass_part.extend(tone(freq, freq, BGM_NOTE_TIME * 4, "sine", 0.3))
    return array.array("h", [a + b for a, b in zip(melody_part, bass_part)])


def start_bgm():
    """배경음악을 끝없이 반복 재생 (sound.init() 다음에 한 번)"""
    if not pygame.mixer.get_init():
        return
    for ext in (".ogg", ".mp3", ".wav"):
        path = os.path.join(SOUND_DIR, "bgm" + ext)
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume["bgm"])
            pygame.mixer.music.play(-1)
            return
    bgm = pygame.mixer.Sound(buffer=make_bgm())
    bgm.set_volume(volume["bgm"])
    bgm.play(-1)
    _sounds["bgm"] = bgm  # 지워지지 않게 보관


def load_volume():
    """지난번에 저장한 볼륨 설정 불러오기 (파일이 없거나 이상하면 기본값 그대로)"""
    try:
        with open(VOLUME_FILE, encoding="utf-8") as f:
            saved = json.load(f)
        for kind in volume:
            volume[kind] = max(0, min(1, float(saved[kind])))
    except (OSError, ValueError, KeyError, TypeError):
        pass


def set_volume(kind, value):
    """볼륨 바꾸기. kind: "sfx"(효과음) 또는 "bgm"(배경음악), value: 0.0 ~ 1.0
    바로 적용하고 파일에 저장해서 다음에 켤 때도 유지됨"""
    volume[kind] = max(0, min(1, round(value, 2)))
    for name, sound in _sounds.items():
        sound.set_volume(volume["bgm"] if name == "bgm" else volume["sfx"])
    if pygame.mixer.get_init():
        pygame.mixer.music.set_volume(volume["bgm"])
    try:
        with open(VOLUME_FILE, "w", encoding="utf-8") as f:
            json.dump(volume, f)
    except OSError:
        pass


def init():
    """소리 준비. 스피커가 없는 등 소리를 못 내는 환경이면 조용히 넘어감."""
    load_volume()
    try:
        pygame.mixer.quit()  # 만든 소리와 같은 형식(44100Hz, 16비트, 스테레오)으로 다시 켬
        pygame.mixer.init(RATE, -16, 2, 512)
    except pygame.error:
        return
    for name, samples in make_all().items():
        sound = None
        for ext in (".wav", ".ogg"):
            path = os.path.join(SOUND_DIR, name + ext)
            if os.path.exists(path):
                sound = pygame.mixer.Sound(path)
                break
        if sound is None:
            sound = pygame.mixer.Sound(buffer=samples)
        sound.set_volume(volume["sfx"])
        _sounds[name] = sound


def play(name):
    sound = _sounds.get(name)
    if sound is None:
        return
    now = pygame.time.get_ticks()
    if now - _last_played.get(name, -10**9) < MIN_GAP.get(name, 0):
        return
    _last_played[name] = now
    sound.play()
