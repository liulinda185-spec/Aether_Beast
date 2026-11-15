# -*- coding: utf-8 -*-
"""给每条行为补上骨架白名单（第四根相容轴），并收紧焚界的元素。只跑一次。"""
import json

P = r"D:\aether-beast-game\tools\worldgen\idea_db.json"
db = json.load(open(P, encoding="utf-8"))

BODIES = {
    "迁徙": ["鲸", "鹿", "象", "马", "隼", "鱼群", "龟", "鸦"],
    "筑巢": ["蜂", "鸦", "隼", "甲", "灯虫", "龟", "蛇", "菌"],
    "共生": ["藤", "菌", "蜂", "灯虫", "章鱼", "龟", "树", "蛇"],
    "捕食": ["隼", "蛇", "鸦", "章鱼", "甲", "鲸", "象", "马"],
    "守墓": ["甲", "鸦", "蛇", "龟", "树", "菌", "蜂", "灯虫"],
    "吟唱": ["鲸", "鸦", "蜂", "灯虫", "章鱼", "龟", "树", "隼"],
    "寄居": ["蜂", "甲", "鸦", "灯虫", "菌", "藤", "蛇", "章鱼", "龟"],
    "耕云": ["蜂", "灯虫", "鸦", "隼", "章鱼", "菌", "藤"],
    "蜕壳": ["蛇", "甲", "龟", "菌", "灯虫", "藤", "章鱼"],
    "焚界": ["蛇", "隼", "甲", "象", "马", "鸦", "鹿"],
}

for b in db["behaviors"]:
    b["bodies"] = BODIES[b["word"]]
    if b["word"] == "焚界":
        b["allowed_elements"] = ["赤炎"]   # 晶体不会烧；能烧的只有赤炎

db["meta"]["rules"].append("同一只兽必须同时通过四根相容轴：元素×行为、骨架×行为、骨架×生境、元素×生境")

open(P, "w", encoding="utf-8").write(json.dumps(db, ensure_ascii=False, indent=2))
print("patched", len(db["behaviors"]), "behaviors")
for b in db["behaviors"]:
    print(f"  {b['word']}: {len(b['bodies'])} 骨架 / 元素 {b['allowed_elements']}")
