# levelup.py - 레벨업 선택지, 보물상자
import random

from settings import PASSIVES, EVOLVE_LEVEL, MAX_WEAPONS, MAX_PASSIVES, CHEST_COUNTS, CHEST_CHANCES
from weapon import WEAPON_CLASSES


def get_pool(player, weapons):
    """지금 고를 수 있는 모든 강화 목록.
    각 강화는 {"title": 제목, "desc": 설명, "apply": 고르면 실행할 함수,
               "gold": 진화인지, "owned": 이미 가진 것의 강화인지}"""
    pool = []

    def add(title, desc, apply, gold=False, owned=True, kind="weapon", icon=None, hint=""):
        # kind: "weapon"(무기) / "passive"(패시브) -> 카드 테두리 색, icon: 카드에 띄울 그림 이름
        # hint: 카드 아래쪽 작은 안내 (예: "Lv7에 진화: 만년필")
        pool.append({"title": title, "desc": desc, "apply": apply, "gold": gold, "owned": owned,
                     "kind": kind, "icon": icon, "hint": hint})

    def give_weapon(key):
        def apply():
            weapons[key] = WEAPON_CLASSES[key]()
        return apply

    def give_passive(key):
        return lambda: player.add_passive(key)

    def take_option(weapon, index):
        return lambda: weapon.take_option(index)

    # 무기: 가진 무기는 그 무기의 옵션 중 하나(무작위)와 진화, 없는 무기는 새로 얻기 (자리가 있을 때만)
    for key, weapon_class in WEAPON_CLASSES.items():
        if key in weapons:
            weapon = weapons[key]
            if weapon.can_evolve():
                add(f"진화: {weapon.evo_name}", weapon.evo_desc, weapon.evolve, gold=True, icon=f"icon_{key}")
            choices = weapon.available_options()
            if choices:
                index = random.choice(choices)
                hint = "" if weapon.evolved else f"Lv{EVOLVE_LEVEL}에 진화: {weapon.evo_name}"
                add(f"{weapon.title()} Lv{weapon.level + 1}", weapon.option_text(index), take_option(weapon, index),
                    icon=f"icon_{key}", hint=hint)
        elif len(weapons) < MAX_WEAPONS:
            add(f"새 무기: {weapon_class.name}", weapon_class.desc, give_weapon(key), owned=False, icon=f"icon_{key}",
                hint=f"Lv{EVOLVE_LEVEL}에 진화: {weapon_class.evo_name}")

    # 패시브
    for key, info in PASSIVES.items():
        level = player.passives.get(key, 0)
        if 0 < level < info["max"]:
            add(f"{info['name']} Lv{level + 1}", info["desc"], give_passive(key), kind="passive", icon=f"icon_{key}")
        elif level == 0 and len(player.passives) < MAX_PASSIVES:
            add(f"새 패시브: {info['name']}", info["desc"], give_passive(key), owned=False,
                kind="passive", icon=f"icon_{key}")

    return pool


def get_options(player, weapons):
    """레벨업 선택지 3개. 진화가 가능하면 반드시 포함하고, 나머지는 무작위"""
    pool = get_pool(player, weapons)
    evolves = [option for option in pool if option["gold"]]
    others = [option for option in pool if not option["gold"]]
    random.shuffle(others)
    options = (evolves + others)[:3]
    if not options:  # 전부 최대까지 강화했으면 회복
        options = [{"title": "HP 30 회복", "desc": "더 강화할 것이 없음",
                    "apply": lambda: player.heal(30), "gold": False, "owned": True,
                    "kind": "passive", "icon": "icon_maxhp"}]
    return options


def open_chest(player, weapons):
    """보물상자: 가진 무기·패시브를 2~5개 자동 강화 (진화가 가능하면 진화 먼저).
    강화한 것들의 제목 목록을 돌려줌"""
    count = random.choices(CHEST_COUNTS, CHEST_CHANCES)[0]
    gained = []
    for _ in range(count):
        pool = [option for option in get_pool(player, weapons) if option["owned"]]
        if not pool:
            break
        evolves = [option for option in pool if option["gold"]]
        option = evolves[0] if evolves else random.choice(pool)
        option["apply"]()
        gained.append(option["title"])
    if not gained:
        player.heal(player.max_hp)
        gained.append("HP 전부 회복")
    return gained
