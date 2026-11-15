# -*- coding: utf-8 -*-
"""把三处带强设定前提的场景改成与地点无关（霜原上不该有船）。只跑一次，可重入。"""
import json

P = r"D:\aether-beast-game\tools\worldgen\idea_db.json"
db = json.load(open(P, encoding="utf-8"))

FIX = {
    "它守着一盏灯，船靠这盏灯认路；它已经守了三百年。":
        "它守着一盏灯，夜里赶路的人靠它认方向；它已经守了三百年。",
    "它每年拆一次河上那座桥，拆得很准。":
        "它每年拆一次那条唯一能过去的通道，拆得很准。",
    "它把水往上引，一天一次；沿岸的井跟着涨，上游的井跟着干。":
        "它把水往上引，一天一次；低处的井跟着涨，高处的井跟着干。",
}

n = 0
for b in db["behaviors"]:
    if b["scene"] in FIX:
        b["scene"] = FIX[b["scene"]]
        n += 1

open(P, "w", encoding="utf-8").write(json.dumps(db, ensure_ascii=False, indent=2))
print(f"改写 {n} 条场景（应为 3）")
for b in db["behaviors"]:
    if b["word"] in ("守灯", "断桥", "引潮"):
        print(f"  {b['word']}: {b['scene']}")
