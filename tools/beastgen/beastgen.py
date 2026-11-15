# -*- coding: utf-8 -*-
"""
幻兽星河 · 神兽生成器 v0.1
=========================
玩家用关键词生成自己的神兽：关键词 → 素材库选材 → 素材给能力动词 → 动词×作用域×强度 = 能力表。

三条硬原则（与已验证的数值层一致）：
  · 素材层自由：名字/形貌/手感随便长，不碰数值
  · 能力层文法化：8 个动词 × 6 个作用域 × 3 个强度 = 144 种"形状"，文本全部唯一
  · 数值层不许发明：每个能力恰好一升一降，量级只从 {4,6,8} 出发按作用域缩放，封顶 12
"""
import json
import os

OUT_JSON = r"D:\aether-beast-game\tools\beastgen\beast_db.json"
OUT_BUILDS = r"D:\aether-beast-game\tools\beastgen\builds_200.json"

DIMS = ["环境", "和平", "自由", "平等", "繁荣", "文化"]
ELEM_SHORT = {"星云": "星", "赤炎": "炎", "苍穹": "穹", "深海": "渊", "晶岩": "晶", "幽林": "林"}

# ---- 能力文法：动词定方向（一升一降），作用域定量级，强度定档 ----
VERBS = [
    {"word": "洞察", "up": "自由", "down": "和平", "why": "看清真相，秩序就松了"},
    {"word": "安抚", "up": "和平", "down": "自由", "why": "摁住冲突，也摁住了别的"},
    {"word": "催生", "up": "繁荣", "down": "环境", "why": "长得快，是因为透支"},
    {"word": "固守", "up": "文化", "down": "繁荣", "why": "保住了旧物，也就挡住了新事"},
    {"word": "迁徙", "up": "平等", "down": "文化", "why": "人流动了，地方就淡了"},
    {"word": "结契", "up": "和平", "down": "平等", "why": "订盟的人安全，没订的人不平"},
    {"word": "撕裂", "up": "平等", "down": "环境", "why": "打破既有分配，也砸坏地基"},
    {"word": "献祭", "up": "环境", "down": "平等", "why": "让土地休养，代价有人扛"},
]

TARGETS = [
    {"word": "一只兽", "mult": 1.0}, {"word": "一群兽", "mult": 1.15},
    {"word": "一个村", "mult": 1.1}, {"word": "一片地", "mult": 1.15},
    {"word": "一季", "mult": 1.1}, {"word": "自己", "mult": 0.8},
]
STRENGTHS = [{"word": "轻", "base": 4}, {"word": "中", "base": 6}, {"word": "重", "base": 8}]
# 三档必须各有代价，否则轻档没人装（纯更弱）。代价就是它存在的理由。
COST = {"轻": "不占刻（每局 3 次）", "中": "占 1 刻", "重": "占 1 刻，混沌 +2"}
MAG_CAP = 9  # 神兽能力不许超过事件卡量级（卡是 4–9）。超过就不是"神兽强"，是"平衡系统失效"

# ---- 素材库：20 件，每件带 1 个元素、1 个形态、2 个能力动词、1 条手感 ----
MATERIALS = [
    ("霜骨", "晶岩", "骨", ["洞察", "固守"], "在零下也不裂"),
    ("霜羽", "苍穹", "羽", ["迁徙", "洞察"], "落地比身体重"),
    ("霜甲", "晶岩", "甲", ["固守", "献祭"], "壳上刻着年轮"),
    ("烬鳞", "赤炎", "鳞", ["撕裂", "迁徙"], "碰过的东西会暖"),
    ("星丝", "星云", "丝", ["结契", "洞察"], "夜里有亮点在走"),
    ("潮膜", "深海", "膜", ["安抚", "迁徙"], "一直湿着"),
    ("晶核", "晶岩", "核", ["固守", "催生"], "碎了会长回去"),
    ("苔绒", "幽林", "绒", ["催生", "安抚"], "走过留痕，第二天才见"),
    ("雷脊", "苍穹", "脊", ["撕裂", "催生"], "雨前会低下来"),
    ("盐睫", "深海", "睫", ["洞察", "安抚"], "睁着也不流泪"),
    ("骨灯", "赤炎", "灯", ["洞察", "结契"], "烧三百年不灭"),
    ("雾筋", "星云", "筋", ["迁徙", "献祭"], "拉着它就飘起来"),
    ("灰绒", "赤炎", "绒", ["催生", "献祭"], "越拍越热"),
    ("火砂", "赤炎", "砂", ["撕裂", "催生"], "踩出火星就熄"),
    ("空髓", "星云", "髓", ["洞察", "结契"], "空的地方会自己长"),
    ("铁胫", "晶岩", "胫", ["固守", "迁徙"], "走一步地就记得"),
    ("云鳍", "苍穹", "鳍", ["迁徙", "安抚"], "游在云里"),
    ("菌伞", "幽林", "伞", ["催生", "献祭"], "撑开就下雨"),
    ("缠丝", "幽林", "丝", ["结契", "撕裂"], "系上就解不开"),
    ("眠壳", "深海", "壳", ["安抚", "献祭"], "睡着的比醒着的多"),
]

# 关键词归一：玩家不会只打"晶岩"，会打"石头""冰""夜里"，也会打气质词和动作词。
# 后一组直接指到能力动词上（score 会拿动词做匹配），否则玩家打的字会被静默丢掉。
SYNONYM = {"火": "赤炎", "炎": "赤炎", "冰": "霜", "雪": "霜", "寒": "霜", "海": "深海",
           "潮": "深海", "水": "深海", "夜": "星云", "星": "星云", "空": "星云",
           "石": "晶岩", "岩": "晶岩", "晶": "晶岩", "云": "苍穹", "天": "苍穹",
           "风": "苍穹", "雷": "苍穹", "林": "幽林", "苔": "幽林", "木": "幽林",
           "守": "固守", "藏": "固守", "镇": "固守", "噬": "撕裂", "猎": "撕裂",
           "断": "撕裂", "杀": "撕裂", "跑": "迁徙", "迁": "迁徙", "游": "迁徙",
           "静": "安抚", "眠": "安抚", "和": "安抚", "契": "结契", "盟": "结契",
           "魂": "结契", "缚": "结契", "祭": "献祭", "舍": "献祭", "烧": "催生",
           "生": "催生", "长": "催生", "歌": "洞察", "吟": "洞察", "看": "洞察"}


def mulberry32(seed):
    a = seed & 0xFFFFFFFF
    while True:
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = a
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        inner = ((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF
        t = (t ^ ((t + inner) & 0xFFFFFFFF)) & 0xFFFFFFFF
        yield ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296


class RNG:
    def __init__(self, seed):
        self.g = mulberry32(seed)

    def r(self):
        return next(self.g)

    def pick(self, seq):
        return seq[int(self.r() * len(seq)) % len(seq)]

    def sample(self, seq, n):
        pool = list(seq)
        out = []
        for _ in range(n):
            if not pool:
                break
            out.append(pool.pop(int(self.r() * len(pool)) % len(pool)))
        return out


def build_catalog():
    """144 种能力形状：文本唯一，数值全部由文法推出。"""
    cat = []
    for v in VERBS:
        for t in TARGETS:
            for s in STRENGTHS:
                mag = int(round(s["base"] * t["mult"]))
                mag = max(3, min(MAG_CAP, mag))
                up = v["up"]
                eff = {"up": mag, "down": mag}
                cat.append({
                    "id": f"{v['word']}·{t['word']}·{s['word']}",
                    "verb": v["word"], "target": t["word"], "strength": s["word"],
                    "up_dim": up, "down_dim": v["down"], "mag": mag,
                    "cost": COST[s["word"]],
                    "self_target": t["word"] == "自己",
                })
    return cat


def materials_as_records():
    recs = []
    for word, el, form, verbs, trait in MATERIALS:
        recs.append({"word": word, "element": el, "form": form,
                     "verbs": verbs, "trait": trait})
    return recs


def normalize(keyword):
    k = keyword.strip()
    return SYNONYM.get(k, k)


def score(mat, kws):
    hay = [mat["word"], mat["element"], mat["form"], mat["trait"]] + mat["verbs"]
    s = 0
    for k in kws:
        if k in mat["word"] or k in mat["form"] or k in mat["verbs"]:
            s += 2
        elif k in mat["element"] or k in mat["trait"]:
            s += 1
    return s


def equip(abilities, n=4, issue_dim=None):
    """能力池不是给玩家全用的。一局只装 4 个，配比固定 2 重 / 1 中 / 1 轻。
    轻档之所以存在，是因为它不占刻——它是"把偏到 58 的那一维拧回 50"的手，不是弱化版的重。"""
    quota_tbl = {4: [("重", 2), ("中", 1), ("轻", 1)], 3: [("重", 1), ("中", 1), ("轻", 1)],
                 2: [("重", 1), ("中", 1)], 1: [("重", 1)]}
    quota = quota_tbl.get(n, [("重", max(1, n // 2)), ("中", 1)])
    picked, used_up, used_tg = [], set(), set()

    def best(st, need_issue=False, allow_reuse=False):
        cands = [a for a in abilities
                 if a["strength"] == st and (allow_reuse or a["up_dim"] not in used_up)
                 and (not need_issue or a["up_dim"] == issue_dim or a["down_dim"] == issue_dim)]
        cands.sort(key=lambda a: (-a["mag"], a["id"]))
        for a in cands:  # 先挑作用域没重复过的
            if a["target"] not in used_tg:
                return a
        return cands[0] if cands else None

    for st, count in quota:
        for _ in range(count):
            if len(picked) >= n:
                break
            a = best(st, need_issue=(st == "重" and issue_dim is not None and not picked),
                     allow_reuse=(st == "轻"))
            if a is None:
                a = best(st) or next((x for x in sorted(abilities, key=lambda x: -x["mag"])
                                      if x not in picked), None)
            if a is None:
                break
            picked.append(a)
            used_up.add(a["up_dim"])
            used_tg.add(a["target"])
    for a in sorted(abilities, key=lambda a: -a["mag"]):  # 兜底补齐
        if len(picked) >= n:
            break
        if a not in picked:
            picked.append(a)
    return picked[:n]


def gen_beast(keywords, mats, rng, slots_n=3, equip_n=4):
    kws = [normalize(k) for k in keywords if k.strip()]
    scored = [(score(m, kws), i, m) for i, m in enumerate(mats)]
    scored.sort(key=lambda x: (-x[0], x[1]))
    hit = [m for s, _, m in scored if s > 0]
    slots = hit[:slots_n]
    shortage = slots_n - len(slots)
    if shortage > 0:
        rest = [m for m in mats if m not in slots]
        slots += rng.sample(rest, shortage)

    verbs = []
    for m in slots:
        for v in m["verbs"]:
            if v not in verbs:
                verbs.append(v)

    # 槽位数随可用方向数走：2 个动词的窄构筑只能装 3 个，3 个以上的装满 4 个。
    # 硬塞 4 个的结果是同一维度出现两次，玩家看到的是"两个一样的按钮"。
    dims_avail = len({v["up"] for v in VERBS if v["word"] in verbs})
    n_slots = min(equip_n, max(2, dims_avail))

    name = ELEM_SHORT[slots[0]["element"]] + slots[0]["form"] + slots[1]["form"] + "兽"
    abilities = []
    for v in VERBS:
        if v["word"] not in verbs:
            continue
        for t in TARGETS:
            for s in STRENGTHS:
                mag = max(3, min(MAG_CAP, int(round(s["base"] * t["mult"]))))
                abilities.append({
                    "id": f"{v['word']}·{t['word']}·{s['word']}",
                    "text": f"{slots[0]['form']}{v['word']}·{t['word']}·{s['word']}",
                    "verb": v["word"], "target": t["word"],
                    "strength": s["word"],
                    "up_dim": v["up"], "down_dim": v["down"], "mag": mag,
                    "cost": COST[s["word"]],
                    "self_target": t["word"] == "自己",
                })
    return {
        "keywords": keywords, "name": name, "slots": [m["word"] for m in slots],
        "elements": [m["element"] for m in slots],
        "verbs": verbs,
        "ability_count": len(abilities),
        "matched": len(hit),
        "slots_n": n_slots,
        "pool": abilities,
        "equipped": equip(abilities, n_slots),
    }


def main():
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    rng = RNG(20261111)
    mats = materials_as_records()
    cat = build_catalog()

    # ---- 自检 1：144 种形状，文本必须唯一 ----
    ids = [c["id"] for c in cat]
    assert len(set(ids)) == len(ids) == 144, f"能力形状重复：{len(ids)} vs {len(set(ids))}"
    # ---- 自检 2：一升一降，量级在 3..12 ----
    for c in cat:
        assert c["up_dim"] != c["down_dim"], c["id"]
        assert 3 <= c["mag"] <= MAG_CAP, c["id"]
    # ---- 自检 3：素材动词必须全在动词表里；每个动词至少 2 件素材能承接 ----
    vwords = {v["word"] for v in VERBS}
    cover = {v["word"]: 0 for v in VERBS}
    for m in mats:
        for v in m["verbs"]:
            assert v in vwords, f"{m['word']} 引用了不存在的动词 {v}"
            cover[v] += 1
    thin = [k for k, n in cover.items() if n < 2]
    assert not thin, f"这些动词没有足够素材承接：{thin}"

    # ---- 200 组关键词，模拟玩家乱输 ----
    pool = ["霜", "星", "火", "海", "骨", "羽", "甲", "丝", "苔", "灯", "雷", "沙",
            "晶", "云", "风", "盐", "睡", "守", "迁", "猎", "烧", "歌", "生", "契",
            "断", "夜", "石", "潮", "空", "铁", "魂", "静", "跑", "藏", "噬", "吟"]
    builds = []
    for i in range(200):
        n = 1 + int(rng.r() * 3)  # 玩家会给 1~3 个词
        kws = rng.sample(pool, n)
        builds.append(gen_beast(kws, mats, rng))

    counts = [b["ability_count"] for b in builds]
    matched0 = [b for b in builds if b["matched"] == 0]
    all_texts = {a["text"] for b in builds for a in b["pool"]}
    verb_sets = {tuple(b["verbs"]) for b in builds}
    slot_sets = {tuple(b["slots"]) for b in builds}

    data = {
        "seed": 20261111,
        "grammar": {"verbs": VERBS, "targets": TARGETS, "strengths": STRENGTHS},
        "catalog": cat,
        "materials": mats,
        "builds": builds,
    }
    open(OUT_JSON, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2))
    open(OUT_BUILDS, "w", encoding="utf-8").write(
        json.dumps(builds, ensure_ascii=False, indent=2))

    print(f"能力形状：{len(cat)} 种（全部文本唯一、一升一降、量级 3–{MAG_CAP}，与事件卡同量级）")
    print(f"素材：{len(mats)} 件；动词承接数：{cover}")
    slots_n_dist = {}
    for b in builds:
        slots_n_dist[len(b["equipped"])] = slots_n_dist.get(len(b["equipped"]), 0) + 1
    print(f"200 组关键词 → 能力池：平均 {sum(counts) / len(counts):.1f}，"
          f"最少 {min(counts)}，最多 {max(counts)}")
    print(f"实际装备数分布：{slots_n_dist}（槽位随可用方向数走）")
    print(f"素材槽组合：{len(slot_sets)} 种／动词组合：{len(verb_sets)} 种")
    print(f"出现的不同能力文本：{len(all_texts)} 种（玩法形状只有 144 种，其余是皮肤）")
    print(f"一个词都没匹配上的构建：{len(matched0)}/200 = {len(matched0) / 2:.0f}%")
    dimcov = [len({a['up_dim'] for a in b['equipped']}) for b in builds]
    tgcov = [len({a['target'] for a in b['equipped']}) for b in builds]
    heavy = sum(1 for b in builds for a in b["equipped"] if a["mag"] >= 6)
    st = {}
    for b in builds:
        for a in b["equipped"]:
            st[a["strength"]] = st.get(a["strength"], 0) + 1
    print(f"装备的 4 个能力：覆盖维度平均 {sum(dimcov) / len(dimcov):.1f}/4，"
          f"作用域平均 {sum(tgcov) / len(tgcov):.1f}/4；"
          f"中/重占 {heavy / (len(builds) * 4) * 100:.0f}%，强度分布 {st}")
    print(f"\n样例构建：")
    for b in builds[:6]:
        print(f"  关键词 {b['keywords']} → {b['name']}"
              f"（{'+'.join(b['slots'])}，池 {b['ability_count']} 条 → 装 4 条）")
        for a in b["equipped"]:
            print(f"      {a['text']}　{a['up_dim']} +{a['mag']}　{a['down_dim']} −{a['mag']}")
    print(f"\n写到 {OUT_JSON}")


if __name__ == "__main__":
    main()
