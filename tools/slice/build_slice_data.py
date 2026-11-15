# -*- coding: utf-8 -*-
"""生成 slice/data.js：一个霜原世界 + 母题库 + 素材 + 5 个关键词预设。
原则：界面只做渲染与操作，所有生成逻辑仍留在 python 端的单一来源里。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "beastgen"))

from beastgen import MATERIALS, VERBS, TARGETS, STRENGTHS, COST, RNG, gen_beast  # noqa: E402
import drops  # noqa: E402

WORLDS = os.path.join(ROOT, "tools", "worldgen", "worlds_100.json")
IDEA = os.path.join(ROOT, "tools", "worldgen", "idea_db.json")
OUT = os.path.join(ROOT, "slice", "data.js")

# 界面文案（逻辑层不硬编码中文，统一从这里取，英文版另有一份）
UI_ZH = {
    "abilityText": "{form}{verb}·{target}·{strength}",
    "verbs": {v: v for v in ["洞察", "安抚", "催生", "固守", "迁徙", "结契", "撕裂", "献祭"]},
    "targets": {t: t for t in ["一只兽", "一群兽", "一个村", "一片地", "一季", "自己"]},
    "strengths": {"轻": "轻", "中": "中", "重": "重"},
    "cost": {"轻": "不占刻（每局 3 次）", "中": "占 1 刻", "重": "占 1 刻，混沌 +2"},
    "forms": {f: f for f in ["骨", "羽", "甲", "鳞", "丝", "膜", "核", "绒", "脊",
                             "睫", "灯", "筋", "砂", "髓", "胫", "鳍", "伞", "壳"]},
    "move": "移动一格（推进 1 刻）",
    "moveLog": "第 {t} 刻 · 移动到 {name}",
    "observe": "观察「{name}」（推进 1 刻，可采到 {drop}）",
    "observeLog": "第 {t} 刻 · 观察 {name} → 采到 {drop}（替换第 {i} 槽）",
    "light": "微调 {text}（剩余 {n} 次）",
    "lightLog": "第 {t} 刻 · 微调 {text}（不占刻，剩余 {n}）",
    "abilityLog": "第 {t} 刻 · 用 {text}（{up} +{mag} / {down} −{mag}）",
    "optionLog": "第 {t} 刻 · 遭遇 {name} → {text}",
    "cause": {"混沌终焉": "混沌终焉", "文明崩塌": "文明崩塌", "灰烬": "灰烬", "存活": "存活"},
    "dims": {"环境": "环境", "和平": "和平", "自由": "自由",
             "平等": "平等", "繁荣": "繁荣", "文化": "文化"},
}


def main():
    worlds = json.load(open(WORLDS, encoding="utf-8"))["worlds"]
    idea = json.load(open(IDEA, encoding="utf-8"))
    world = next(w for w in worlds if w["biome"] == "霜原")

    all_mats = drops.mats()
    behaviors = {b["word"]: b["actions"] for b in idea["behaviors"]}

    beasts = []
    for i, b in enumerate(world["beasts"]):
        beh = behaviors.get(b["behavior"])
        if not beh:
            raise SystemExit(f"行为缺失：{b['behavior']}")
        beasts.append({
            "name": b["name"], "element": b["element"], "body": b["body"],
            "behavior": b["behavior"], "measure": b["measure"],
            "shape": b["shape"], "hook": b["hook"],
            "drop": drops.drop(b, world["seed_used"], i, all_mats),
            "actions": beh,
        })

    # 5 组关键词预设：全部由 beastgen 现算，界面不重算
    # 统一字段名：python 侧是 up_dim/down_dim，引擎与界面按 upDim/downDim 读，两份都写
    presets = []
    for kws in (["霜", "骨", "守"], ["星", "夜", "静"], ["火", "噬", "断"], ["海", "眠", "抚"], ["苔"]):
        b = gen_beast(kws, drops.mats(), RNG(20261111 + len(presets)))
        eq = []
        for a in b["equipped"]:
            a = dict(a)
            a["upDim"] = a.get("up_dim")
            a["downDim"] = a.get("down_dim")
            eq.append(a)
        presets.append({
            "keywords": kws, "name": b["name"], "slots": b["slots"],
            "verbs": b["verbs"], "equipped": eq,
            "poolSize": b["ability_count"],
        })

    data = {
        "seed": world["seed_used"],
        "world": {
            "name": world["name"], "biome": world["biome"], "biomeScene": world["biome_scene"],
            "issue": world["issue"], "issueDim": world["issue_dim"], "issueLine": world["issue_line"],
            "opening": world["opening"], "D": world["difficulty"]["D"],
            "DLabel": world["difficulty"]["label"], "factions": world["factions"],
            "encounterTicks": world["encounter_ticks"], "ticks": world["ticks"],
            "beasts": beasts,
        },
        "materials": [{"word": w, "element": e, "form": f, "verbs": v, "trait": t}
                      for w, e, f, v, t in MATERIALS],
        "grammar": {
            "verbs": VERBS,
            "targets": [{"word": t["word"], "mult": t["mult"]} for t in TARGETS],
            "strengths": STRENGTHS,
            "cost": COST,
        },
        "presets": presets,
        "ui": UI_ZH,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=1)
    open(OUT, "w", encoding="utf-8").write("/* 自动生成，勿手改：tools/slice/build_slice_data.py */\n"
                                          "window.SLICE_DATA = " + payload + ";\n")
    print(f"写入 {OUT}（{len(payload)} 字节）")
    print(f"世界：{world['name']}　D={world['difficulty']['D']}　议题={world['issue']}")
    for b in beasts:
        print(f"  {b['name']}（{b['element']}/{b['body']}/{b['behavior']}）→ 掉落 {b['drop']}")
    for p in presets:
        print(f"  预设 {p['keywords']} → {p['name']}（{'+'.join(p['slots'])}，装 {len(p['equipped'])}）")


if __name__ == "__main__":
    main()
