# levelup.py - 레벨업할 때 고를 수 있는 강화 목록 만들기
import random

from weapon import Book, Coffee


def get_options(player, weapons):
    """지금 고를 수 있는 강화들 중에서 무작위 3개를 돌려줌.
    각 강화는 {"title": 제목, "desc": 설명, "apply": 고르면 실행할 함수}"""
    options = []

    def add(title, desc, apply):
        options.append({"title": title, "desc": desc, "apply": apply})

    def give_weapon(key, weapon_class):
        def apply():
            weapons[key] = weapon_class()
        return apply

    # 볼펜 (처음부터 가지고 있음)
    pen = weapons["pen"]
    if pen.can_add_count():
        add("볼펜 발사 수 +1", f"한 번에 {pen.count} → {pen.count + 1}발", pen.add_count)
    if pen.can_speed_up():
        add("볼펜 공격 속도 +20%", "더 자주 발사", pen.speed_up)

    # 전공 서적
    if "book" not in weapons:
        add("새 무기: 전공 서적", "주변을 회전하며 공격", give_weapon("book", Book))
    else:
        book = weapons["book"]
        if book.can_add_count():
            add("전공 서적 개수 +1", f"책 {book.count} → {book.count + 1}권", book.add_count)
        if book.can_widen():
            add("전공 서적 회전 반경 +", "더 넓게 회전", book.widen)

    # 커피
    if "coffee" not in weapons:
        add("새 무기: 커피 폭발", "3초마다 적 위치에 폭발", give_weapon("coffee", Coffee))
    else:
        coffee = weapons["coffee"]
        add("커피 폭발 범위 +", "더 넓게 터짐", coffee.widen)
        add("커피 폭발 데미지 +10", f"데미지 {coffee.damage} → {coffee.damage + 10}", coffee.strengthen)

    # 플레이어
    add("최대 HP +20", "HP도 20 회복", player.increase_max_hp)
    add("이동 속도 +10%", "더 빠르게 이동", player.increase_speed)

    return random.sample(options, min(3, len(options)))
