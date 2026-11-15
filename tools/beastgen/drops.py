# -*- coding: utf-8 -*-
"""
观察掉落 v0.1
=============
规则（按你的决定）：素材不是打完自动给，必须花一刻"观察"那只兽才掉。
所以素材变成有成本的资源 —— 16 刻 = 8 个遭遇刻（必选）+ 8 个自由刻（移动/观察/微调）。
观察一只兽 = 1 个自由刻。走完 8 只兽基本不可能，现实是每世界 3–5 件。

本脚本只回答三件事：
  1. 每世界能给多少素材（全观察 / 现实 4 只）
  2. 20 件素材是否都能在世界里被采到（不能有"写了但永远采不到"的素材）
  3. 采到的素材能撑出几个方向（这决定你会不会造出一只窄兽）
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from beastgen import MATERIALS, RNG, VERBS  # noqa: E402

WORLDS = r"D:\aether-beast-game\tools\worldgen\worlds_100.json"

# 骨架 → 它身上能取下来的形态（第四根轴在掉落侧的另一半：鲸身上取不出毛）
BODY_FORM = {
    "鲸": ["鳍", "鳞", "膜"], "鹿": ["骨", "胫"], "隼": ["羽", "脊"], "蛇": ["鳞", "膜"],
    "甲": ["甲", "壳"], "藤": ["丝", "绒"], "菌": ["伞", "绒"], "蜂": ["绒", "丝"],
    "鱼群": ["鳞", "膜"], "象": ["胫", "骨"], "鸦": ["羽", "骨"], "龟": ["壳", "甲"],
    "灯虫": ["灯", "丝"], "树": ["骨", "核"], "章鱼": ["丝", "膜"], "马": ["胫", "脊"],
}


def mats():
    return [{"word": w, "element": e, "form": f, "verbs": v, "trait": t}
            for w, e, f, v, t in MATERIALS]


def candidates(beast, all_mats):
    """先看骨架能取下什么形态，再要求元素对得上。
    只按元素找会让星云鸦掉出"膜"——同元素不等于同物种身上有的东西。"""
    fams = BODY_FORM.get(beast["body"], [])
    strict = [m for m in all_mats if m["form"] in fams and m["element"] == beast["element"]]
    if strict:
        return strict, "形态+元素"
    same_el = [m for m in all_mats if m["element"] == beast["element"]]
    if same_el:
        return same_el, "仅元素"
    same_fm = [m for m in all_mats if m["form"] in fams]
    return (same_fm or all_mats), "仅形态"


FALLBACK = {"形态+元素": 0, "仅元素": 0, "仅形态": 0}


def drop(beast, world_seed, idx, all_mats):
    cands, kind = candidates(beast, all_mats)
    FALLBACK[kind] += 1
    rng = RNG((world_seed * 31 + idx * 17) & 0xFFFFFFFF)
    cands = sorted(cands, key=lambda m: m["word"])
    return rng.pick(cands)["word"]


def main():
    data = json.load(open(WORLDS, encoding="utf-8"))
    worlds = data["worlds"]
    all_mats = mats()

    full, real = [], []
    providers = {m["word"]: 0 for m in all_mats}
    sample_rows = []

    for w in worlds:
        seed = w["seed_used"]
        got = [drop(b, seed, i, all_mats) for i, b in enumerate(w["beasts"])]
        full.append(len(set(got)))
        # 现实：8 个自由刻里一半要花在移动上，能观察 4 只
        real.append(len(set(got[:4])))
        for g in set(got):
            providers[g] += 1
        if len(sample_rows) < 3:
            sample_rows.append((w["name"], w["biome"],
                                [(b["name"], b["element"], b["body"], g)
                                 for b, g in zip(w["beasts"], got)]))

    print(f"观察全部 8 只 → 每世界可得不同素材：平均 {sum(full) / len(full):.1f}，"
          f"最少 {min(full)}，最多 {max(full)}")
    print(f"现实只观察 4 只 → 每世界可得：平均 {sum(real) / len(real):.1f}，"
          f"最少 {min(real)}，最多 {max(real)}")
    never = [k for k, v in providers.items() if v == 0]
    rare = sorted([(v, k) for k, v in providers.items()])[:5]
    print(f"素材可达性：{len(all_mats) - len(never)}/{len(all_mats)} 件能采到"
          + (f"；永远采不到：{never}" if never else ""))
    print(f"候选集来源（800 次掉落）：{FALLBACK}")
    print(f"最稀有的 5 件（出现在多少世界）：{[(k, v) for v, k in rare]}")

    # 窄兽判据：采到的素材带出几个不同的"升维方向"
    up_of = {v["word"]: v["up"] for v in VERBS}
    mat_verbs = {m["word"]: m["verbs"] for m in all_mats}
    dirs = []
    for w in worlds:
        seed = w["seed_used"]
        got = list(dict.fromkeys(drop(b, seed, i, all_mats) for i, b in enumerate(w["beasts"][:4])))
        vs = [v for g in got for v in mat_verbs[g]]
        dirs.append(len({up_of[v] for v in vs}))
    print(f"现实采集（4 件素材）→ 可用升维方向数：平均 {sum(dirs) / len(dirs):.1f}，"
          f"最少 {min(dirs)}，最多 {max(dirs)}；≤2 个方向的世界占 "
          f"{sum(1 for d in dirs if d <= 2) / len(dirs) * 100:.0f}%")

    for name, biome, rows in sample_rows:
        print(f"\n{name}（{biome}）")
        for bn, el, bd, g in rows[:4]:
            print(f"  观察 {bn}（{el}/{bd}）→ {g}")


if __name__ == "__main__":
    main()
