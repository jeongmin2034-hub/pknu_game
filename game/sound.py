# sound.py - 효과음
#
# 소리 파일 없이도 되도록, 파이썬으로 "삐-" 하는 소리를 직접 만들어서 씀 (8비트 게임 느낌).
# assets/sounds/<이름>.wav (또는 .ogg) 파일이 있으면 그 파일을 대신 씀.
#   이름: shoot, hit, kill, gem, item, levelup, hurt, explosion, boss, gameover, clear
#
# 사용법:  import sound  ->  sound.init() 한 번  ->  sound.play("shoot")
import array
import math
import os
import random

import pygame
from settings import SOUND_VOLUME

SOUND_DIR = os.path.join(os.path.dirname(__file__), "assets", "sounds")
RATE = 44100

_sounds = {}
_last_played = {}  # 같은 소리가 너무 겹쳐서 시끄럽지 않게, 마지막으로 낸 시각 기록

# 같은 소리를 다시 내려면 최소 이만큼(ms) 기다림
MIN_GAP = {"shoot": 60, "hit": 50, "kill": 40, "gem": 50}


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
    }


def init():
    """소리 준비. 스피커가 없는 등 소리를 못 내는 환경이면 조용히 넘어감."""
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
        sound.set_volume(SOUND_VOLUME)
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
