# -*- coding: utf-8 -*-
"""
幻兽星河 · 世界生成器 v0.1
=========================
只做一件事：证明「母题库 + 种子」能不能产出值得探索的世界。
原则（与 GDD 一致）：
  · 叙事层自由生成：名字 / 形貌 / 钩子 / 场景 / 开场
  · 数值层不生成：六维初值固定 50（已验证包络），难度只取自 {18,15,12} 三档
  · 同种子必同世界：使用与 JS 版完全相同的 mulberry32
"""
import json
import sys

DB_PATH = r"D:\aether-beast-game\tools\worldgen\idea_db.json"
OUT_JSON = r"D:\aether-beast-game\tools\worldgen\worlds_100.json"
OUT_MD = r"D:\aether-beast-game\docs\生成器样本-v0.1.md"

DIMS = ["环境", "和平", "自由", "平等", "繁荣", "文化"]
ISSUE_DIM = {"环境": 1, "战争": 2, "自由与秩序": 3, "平等": 4, "能源": 5, "文化": 6}
BIOME_AFFINITY = {
    "潮汐林": ["幽林", "深海"], "熔脊": ["赤炎", "晶岩"], "浮空礁": ["星云", "苍穹"],
    "沉城": ["深海", "晶岩"], "霜原": ["苍穹", "晶岩"], "孢海": ["幽林"],
    "铁砧荒原": ["赤炎", "晶岩"], "星港废墟": ["星云", "苍穹"],
}
DIFF = {18: "第一颗 星尘海（教学）", 15: "第二颗 灰烬带（正片）", 12: "第三颗 坍缩区（末关）"}
# 骨架×生境：一个能浮起水面的东西不该出生在雪原上。这是第三根相容轴。
# 每个生境必须至少容纳 8 种骨架，否则该生境凑不满一局的 8 场遭遇（脚本开头会断言）。
BIOME_BODIES = {
    "潮汐林": ["鲸", "鹿", "蛇", "藤", "菌", "蜂", "鱼群", "象", "龟", "灯虫", "树", "章鱼"],
    "熔脊": ["隼", "蛇", "甲", "菌", "鸦", "龟", "藤", "象"],
    "浮空礁": ["鹿", "隼", "甲", "龟", "马", "蜂", "鸦", "灯虫"],
    "沉城": ["鲸", "蛇", "甲", "藤", "菌", "鱼群", "鸦", "龟", "灯虫", "章鱼"],
    "霜原": ["鹿", "隼", "蜂", "象", "鸦", "树", "马", "甲"],
    "孢海": ["鹿", "蛇", "藤", "菌", "蜂", "象", "龟", "灯虫", "树"],
    "铁砧荒原": ["鹿", "隼", "蛇", "甲", "象", "鸦", "树", "马"],
    "星港废墟": ["隼", "甲", "鸦", "灯虫", "马", "蛇", "龟", "树"],
}
MAX_SAME_BEHAVIOR = 2  # 单世界内同一行为最多两只：否则 8 场遭遇会变成同一场打四遍
MIN_BEHAVIOR_KINDS = 5
TICKS = 16
ENCOUNTER_TICKS = [2, 4, 6, 8, 10, 12, 14, 16]


def behavior_dims(b):
    """该行为的三条动作一共能触到哪几个维度（1–6）。"""
    out = set()
    for a in b["actions"]:
        for k in a["dims"]:
            out.add(DIMS.index(k) + 1)
    return out


# ---------- 与 JS 逐位一致的 mulberry32 ----------
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
            i = int(self.r() * len(pool)) % len(pool)
            out.append(pool.pop(i))
        return out


def gen_world(db, seed):
    rng = RNG(seed)
    biome = rng.pick(db["biomes"])
    issue = (db["issues"][[i["word"] for i in db["issues"]].index(biome["issue"])]
             if rng.r() < 0.6 else rng.pick(db["issues"]))
    d = 18 if rng.r() < 0.30 else (15 if rng.r() < 0.68 else 12)
    state = rng.pick(db["world_states"])

    issue_faction = next(f for f in db["factions"] if f["word"] != "" and f["dim"] == issue["dim"])
    others = [f for f in db["factions"] if f["word"] != issue_faction["word"]]
    factions = [issue_faction] + rng.sample(others, 2)

    beasts = []
    used_triple, used_body, used_motif = set(), set(), set()
    issue_behaviors = [b for b in db["behaviors"] if issue["dim"] in behavior_dims(b)]
    beh_count = {b["word"]: 0 for b in db["behaviors"]}
    tries = 0
    while len(beasts) < 8 and tries < 600:
        tries += 1
        cand_body = [b["word"] for b in db["bodies"]
                     if b["word"] not in used_body and b["word"] in BIOME_BODIES[biome["word"]]]
        if not cand_body:
            break
        body_word = rng.pick(cand_body)
        # 行为必须容得下这个骨架（树不会堆巢，鲸不会焚界）
        cand_beh = [b for b in db["behaviors"]
                    if body_word in b["bodies"] and beh_count[b["word"]] < MAX_SAME_BEHAVIOR]
        if not cand_beh:
            continue
        # 主议题覆盖 60% / 支线 40%（与 GDD §05 周目节奏同口径）
        avail_issue = [b for b in cand_beh if b in issue_behaviors]
        beh = rng.pick(avail_issue) if (rng.r() < 0.60 and avail_issue) else rng.pick(cand_beh)
        # 元素必须在行为允许之列；优先本生境同源，其次外来者（外来者是叙事燃料）
        native = [e for e in BIOME_AFFINITY[biome["word"]] if e in beh["allowed_elements"]]
        if native and rng.r() < 0.70:
            want = rng.pick(native)
            element = next(e for e in db["elements"] if e["word"] == want)
        else:
            legal = [e for e in db["elements"] if e["word"] in beh["allowed_elements"]]
            if not legal:
                continue
            element = rng.pick(legal)
        motif = rng.pick([m for m in db["motifs"] if m["word"] not in used_motif])
        body = next(b for b in db["bodies"] if b["word"] == body_word)
        key = (body["word"], element["word"], motif["word"])
        if key in used_triple:
            continue
        used_triple.add(key)
        used_body.add(body["word"])
        used_motif.add(motif["word"])
        beh_count[beh["word"]] = beh_count.get(beh["word"], 0) + 1
        beasts.append({
            "name": f"{motif['word']}{element['word']}{body['word']}",
            "body": body["word"], "element": element["word"],
            "motif": motif["word"], "behavior": beh["word"],
            "measure": body["measure"],
            "shape": f"{body['shape']}；{element['tone']}",
            "hook": motif["clause"],
            "scene": beh["scene"],
            "affinity": element["word"] in BIOME_AFFINITY[biome["word"]],
            "actions": [{"text": a["text"], "dims": a["dims"]} for a in beh["actions"]],
        })
    return {
        "seed": seed,
        "id": None,
        "name": f"{state}{biome['word']}",
        "biome": biome["word"], "biome_scene": biome["scene"],
        "issue": issue["word"], "issue_dim": issue["dim"], "issue_line": issue["line"],
        "difficulty": {"D": d, "label": DIFF[d]},
        "factions": [{"name": f["word"], "stance": f["stance"]} for f in factions],
        "beasts": beasts,
        "ticks": TICKS, "encounter_ticks": ENCOUNTER_TICKS,
        "opening": f"{biome['scene']}。{issue['line']}",
    }


# ---------- 质量闸门 ----------
def validate(w):
    f = []
    if len(w["beasts"]) != 8:
        f.append(f"兽数 {len(w['beasts'])} ≠ 8")
    triples = {(b["body"], b["element"], b["motif"]) for b in w["beasts"]}
    if len(triples) != 8:
        f.append("三元组重复")
    for b in w["beasts"]:
        for a in b["actions"]:
            pos = [v for v in a["dims"].values() if v > 0]
            neg = [v for v in a["dims"].values() if v < 0]
            if len(pos) != 1 or len(neg) != 1:
                f.append(f"{b['name']} 动作「{a['text']}」不是一升一降")
    related = 0
    for b in w["beasts"]:
        touched = set()
        for a in b["actions"]:
            for k in a["dims"]:
                touched.add(DIMS.index(k) + 1)
        if w["issue_dim"] in touched:
            related += 1
    if related < 3:
        f.append(f"与主议题相关的兽只有 {related} 只（需 ≥3）")
    aff = sum(1 for b in w["beasts"] if b["affinity"])
    if aff < 4:
        f.append(f"生境亲和兽只有 {aff} 只（需 ≥4）")
    bh = {}
    for b in w["beasts"]:
        bh[b["behavior"]] = bh.get(b["behavior"], 0) + 1
    if max(bh.values()) > MAX_SAME_BEHAVIOR:
        f.append(f"同一行为出现 {max(bh.values())} 次（上限 {MAX_SAME_BEHAVIOR}）")
    if len(bh) < MIN_BEHAVIOR_KINDS:
        f.append(f"行为种类只有 {len(bh)} 种（需 ≥{MIN_BEHAVIOR_KINDS}）")
    return f


def assert_db(db):
    """母题库自检：任何生境凑不满 8 种骨架，都会让那个生境永远生成失败。"""
    body_words = {b["word"] for b in db["bodies"]}
    bad = []
    for biome, words in BIOME_BODIES.items():
        missing = [w for w in words if w not in body_words]
        if missing:
            bad.append(f"{biome} 引用了不存在的骨架 {missing}")
        if len(words) < 8:
            bad.append(f"{biome} 只有 {len(words)} 种骨架（需 ≥8）")
    if bad:
        raise SystemExit("母题库自检失败：\n  " + "\n  ".join(bad))


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    seed0 = int(sys.argv[2]) if len(sys.argv) > 2 else 20261111
    db = json.load(open(DB_PATH, encoding="utf-8"))
    assert_db(db)

    worlds, fails = [], []
    rerolls = 0
    for i in range(n):
        base = seed0 + i * 7919
        chosen, used_seed, last_bad = None, base, []
        for k in range(6):
            cand = gen_world(db, base + k * 13)
            bad = validate(cand)
            if not bad:
                chosen, used_seed, rerolls = cand, base + k * 13, rerolls + k
                break
            last_bad = bad
        if chosen is None:
            chosen, used_seed = cand, base + 5 * 13
            fails.append((f"W{i + 1:04d}", last_bad))
        chosen["id"] = f"W{i + 1:04d}"
        chosen["seed_used"] = used_seed
        worlds.append(chosen)

    json.dump({"seed0": seed0, "count": n, "worlds": worlds},
              open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ---------- 统计 ----------
    names = [b["name"] for w in worlds for b in w["beasts"]]
    uniq_names = len(set(names))
    act_texts = {a["text"] for w in worlds for b in w["beasts"] for a in b["actions"]}
    biomes = {}
    issues = {}
    diffs = {}
    for w in worlds:
        biomes[w["biome"]] = biomes.get(w["biome"], 0) + 1
        issues[w["issue"]] = issues.get(w["issue"], 0) + 1
        diffs[w["difficulty"]["D"]] = diffs.get(w["difficulty"]["D"], 0) + 1
    print(f"生成 {n} 个世界 / {n * 8} 只兽（种子 {seed0}）")
    print(f"  兽名唯一：{uniq_names}/{n * 8} = {uniq_names / (n * 8) * 100:.1f}%")
    print(f"  动作文本唯一：{len(act_texts)} 种（每世界 8 兽 × 3 动作 = 24 次，共 {n * 24} 次调用）")
    kinds = [len({b['behavior'] for b in w['beasts']}) for w in worlds]
    used_beh = {}
    for w in worlds:
        for b in w["beasts"]:
            used_beh[b["behavior"]] = used_beh.get(b["behavior"], 0) + 1
    print(f"  单世界行为种类：平均 {sum(kinds) / len(kinds):.1f}／最少 {min(kinds)}／最多 {max(kinds)}")
    print(f"  行为库覆盖：{len(used_beh)}/{len(db['behaviors'])} 条被用到，"
          f"最少 {min(used_beh.values())} 次、最多 {max(used_beh.values())} 次")
    unused = [b['word'] for b in db['behaviors'] if b['word'] not in used_beh]
    if unused:
        print(f"  从未出现的行有：{unused}")
    print(f"  生境分布：{biomes}")
    print(f"  议题分布：{issues}")
    print(f"  难度分布：{diffs}")
    print(f"  闸门失败世界：{len(fails)}/{n}　重掷次数：{rerolls}（平均 {rerolls / n:.2f} 次/世界）")
    for wid, bad in fails[:5]:
        print(f"    {wid}: {bad}")

    # ---------- 可读样本 ----------
    lines = [
        "# 生成器样本 v0.1　·　5 个自动生成的世界",
        "",
        f"> 种子 `{seed0}`，共生成 {n} 个世界，这里抽 5 个全文列出。完整数据见 `tools/worldgen/worlds_100.json`。",
        "> 母题库 `tools/worldgen/idea_db.json` 是手写核："
        f"{len(db['bodies'])} 骨架 / {len(db['elements'])} 元素 / {len(db['behaviors'])} 行为 / "
        f"{len(db['motifs'])} 母题 / {len(db['biomes'])} 生境 / {len(db['issues'])} 议题 / "
        f"{len(db['factions'])} 势力；每世界同一行为 ≤{MAX_SAME_BEHAVIOR} 只、行为种类 ≥{MIN_BEHAVIOR_KINDS}。",
        "",
        "**读这份文件的方法**：只看一件事——你有没有想对其中某只兽做点什么。想，就说明这条循环成立；都觉得无所谓，就说明母题库太小。数字是验证过的，感觉没有。",
        "",
    ]
    for w in worlds[:5]:
        lines += [
            f"## {w['id']}　{w['name']}",
            "",
            f"- 生境：**{w['biome']}** —— {w['biome_scene']}",
            f"- 主议题：**{w['issue']}**（维度 {w['issue_dim']}）—— {w['issue_line']}",
            f"- 难度：D = {w['difficulty']['D']}（{w['difficulty']['label']}）　一局 {w['ticks']} 刻，第 "
            f"{'、'.join(str(t) for t in w['encounter_ticks'])} 刻各一次遭遇",
            f"- 势力：{ ' / '.join(f['name'] for f in w['factions']) }",
            "",
            f"> {w['opening']}",
            "",
        ]
        for i, b in enumerate(w["beasts"], 1):
            lines.append(f"**{i}. {b['name']}**（{b['behavior']}　{b['measure']}）")
            lines.append(f"　{b['shape']}。")
            lines.append(f"　{b['scene']}")
            lines.append(f"　*{b['hook']}*")
            for j, a in enumerate(b["actions"]):
                dd = "　".join(f"{k} {'+' if v > 0 else '−'}{abs(v)}" for k, v in a["dims"].items())
                lines.append(f"　　{'①②③'[j]} {a['text']}　→　{dd}")
            lines.append("")
        lines.append("---")
        lines.append("")

    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"\n样本写到 {OUT_MD}")


if __name__ == "__main__":
    main()
