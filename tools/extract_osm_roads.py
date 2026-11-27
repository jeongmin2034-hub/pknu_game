# extract_osm_roads.py - OSM 원본(campus_raw.json)에서 길만 뽑아 map_src/osm_roads.json 으로 저장
# 길끼리 공유하는 교차점(노드) 번호를 그대로 남겨서, 맵을 만들 때 길이 끊기지 않게 함
# 실행: python tools/extract_osm_roads.py <campus_raw.json 경로>
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = sys.argv[1]
els = json.load(open(RAW, encoding="utf-8"))["elements"]

# campus_data.py 와 같은 투영 (캠퍼스 경계 중심 기준, 4.863도 회전)
way = [e for e in els if e["type"] == "way" and e["id"] == 480816518][0]
bg = way["geometry"][:-1]
LAT0 = (min(p["lat"] for p in bg) + max(p["lat"] for p in bg)) / 2
LON0 = (min(p["lon"] for p in bg) + max(p["lon"] for p in bg)) / 2
phi = math.radians(LAT0)
MY = 111132.92 - 559.82 * math.cos(2 * phi) + 1.175 * math.cos(4 * phi)
MX = 111412.84 * math.cos(phi) - 93.5 * math.cos(3 * phi)
CT, ST = math.cos(math.radians(4.863)), math.sin(math.radians(4.863))


def rot(lat, lon):
    x, y = (lon - LON0) * MX, -(lat - LAT0) * MY
    return x * CT - y * ST, x * ST + y * CT


B = [rot(p["lat"], p["lon"]) for p in bg]
OX, OY = min(x for x, _ in B) - 50, min(y for _, y in B) - 50

KIND = {"trunk": ("major", 16), "trunk_link": ("major", 7), "secondary": ("major", 12),
        "secondary_link": ("major", 7), "residential": ("street", 7), "unclassified": ("street", 7),
        "service": ("campus", 5), "pedestrian": ("path", 6), "footway": ("path", 3),
        "path": ("path", 3), "steps": ("steps", 3)}

nodes, ways = {}, []
for e in els:
    t = e.get("tags", {})
    if e["type"] != "way" or t.get("highway") not in KIND or t.get("area") == "yes":
        continue
    if t.get("footway") in ("sidewalk", "crossing"):   # 차도 옆 인도·횡단보도는 차도에 포함
        continue
    kind, w = KIND[t["highway"]]
    for nid, p in zip(e["nodes"], e["geometry"]):
        x, y = rot(p["lat"], p["lon"])
        nodes[nid] = (round(x - OX, 2), round(y - OY, 2))
    ways.append({"kind": kind, "w": w, "nodes": e["nodes"], "name": t.get("name", "")})

out = os.path.join(HERE, "map_src", "osm_roads.json")
json.dump({"source": "OpenStreetMap (ODbL)", "nodes": nodes, "ways": ways}, open(out, "w", encoding="utf-8"))
print("길", len(ways), "개, 점", len(nodes), "개 ->", out)
