# -*- coding: utf-8 -*-
"""把行为库从 10 扩到 24。只跑一次；可重复运行（按 word 去重，不会重复追加）。"""
import json

P = r"D:\aether-beast-game\tools\worldgen\idea_db.json"

NEW = [
    {"word": "引潮", "bodies": ["鲸", "龟", "鱼群", "章鱼", "蛇"], "allowed_elements": ["深海", "苍穹"],
     "scene": "它把水往上引，一天一次；沿岸的井跟着涨，上游的井跟着干。",
     "actions": [
         {"text": "让它继续引潮，沿岸的田归它灌", "dims": {"环境": 7, "平等": -6}},
         {"text": "筑坝挡潮，把水位钉住", "dims": {"繁荣": 6, "环境": -7}},
         {"text": "迁走下游的村，水位让给它", "dims": {"平等": 5, "文化": -6}}]},

    {"word": "落尘", "bodies": ["甲", "象", "马", "鹿", "树"], "allowed_elements": ["晶岩", "赤炎"],
     "scene": "它走过的地方落一层灰，灰里带着肥，也带着毒。",
     "actions": [
         {"text": "收集落尘做肥料", "dims": {"繁荣": 7, "环境": -6}},
         {"text": "赶它离开农田", "dims": {"环境": 6, "繁荣": -7}},
         {"text": "把落尘当神迹供奉", "dims": {"文化": 7, "平等": -5}}]},

    {"word": "开路", "bodies": ["象", "甲", "蛇", "隼", "马"], "allowed_elements": ["晶岩", "赤炎"],
     "scene": "它在山脊上磨出一道口子，一次比一次宽。",
     "actions": [
         {"text": "让开口子通商", "dims": {"繁荣": 8, "环境": -7}},
         {"text": "把它堵回去", "dims": {"环境": 6, "繁荣": -8}},
         {"text": "把口子定为朝圣道", "dims": {"文化": 6, "自由": -4}}]},

    {"word": "结网", "bodies": ["蜂", "菌", "章鱼", "藤", "灯虫"], "allowed_elements": ["幽林", "星云"],
     "scene": "它在两个定居点之间织了一片能走的网，网会旧，它不会补。",
     "actions": [
         {"text": "让人走网，不问去向", "dims": {"自由": 7, "和平": -5}},
         {"text": "剪断网，恢复关卡", "dims": {"和平": 6, "自由": -7}},
         {"text": "收费过网，网归公", "dims": {"繁荣": 6, "平等": -7}}]},

    {"word": "引路", "bodies": ["鸦", "灯虫", "龟", "隼", "鲸"], "allowed_elements": ["星云", "苍穹"],
     "scene": "它带迷路的人走出去，只带它愿意带的。",
     "actions": [
         {"text": "把引路做成公共系统", "dims": {"平等": 7, "繁荣": -4}},
         {"text": "只给买得起的人引", "dims": {"繁荣": 7, "平等": -8}},
         {"text": "禁止它带外人进来", "dims": {"和平": 6, "自由": -7}}]},

    {"word": "埋种", "bodies": ["树", "菌", "藤", "龟", "甲"], "allowed_elements": ["幽林", "晶岩"],
     "scene": "它把种子埋得很深，几十年后才长出来，没人知道埋在哪。",
     "actions": [
         {"text": "等它长，把这块地划为林地", "dims": {"环境": 8, "繁荣": -7}},
         {"text": "挖出来卖", "dims": {"繁荣": 8, "环境": -8}},
         {"text": "把埋种地划为祖产", "dims": {"文化": 7, "自由": -5}}]},

    {"word": "蚀骨", "bodies": ["菌", "藤", "章鱼", "蛇", "龟"], "allowed_elements": ["幽林", "深海"],
     "scene": "它啃旧墙，一天一寸，墙上的字先没。",
     "actions": [
         {"text": "让它蚀完，清出地基", "dims": {"繁荣": 7, "文化": -8}},
         {"text": "封锁旧城区", "dims": {"文化": 7, "繁荣": -7}},
         {"text": "抢救性拓印", "dims": {"文化": 6, "平等": -4}}]},

    {"word": "鸣雷", "bodies": ["隼", "鲸", "马", "象", "鸦"], "allowed_elements": ["苍穹", "赤炎"],
     "scene": "它一叫，云就聚，雷落在它选的地方。",
     "actions": [
         {"text": "让它只劈荒野", "dims": {"环境": 6, "自由": -4}},
         {"text": "引雷入网做能源", "dims": {"繁荣": 8, "环境": -6}},
         {"text": "驱离它", "dims": {"和平": 6, "文化": -7}}]},

    {"word": "引泉", "bodies": ["龟", "蛇", "鲸", "章鱼", "树"], "allowed_elements": ["深海", "晶岩"],
     "scene": "它踩过的地方会出水，踩得越多，水越少。",
     "actions": [
         {"text": "让泉供全村", "dims": {"平等": 7, "环境": -5}},
         {"text": "封泉独占", "dims": {"繁荣": 7, "平等": -8}},
         {"text": "按老规矩分水", "dims": {"文化": 6, "繁荣": -5}}]},

    {"word": "拾遗", "bodies": ["鸦", "蜂", "灯虫", "章鱼", "马"], "allowed_elements": ["星云", "幽林"],
     "scene": "它捡所有人丢掉的东西，堆在一个地方，越堆越高。",
     "actions": [
         {"text": "设回收站交给它管", "dims": {"环境": 7, "繁荣": -5}},
         {"text": "烧掉那一堆", "dims": {"繁荣": 6, "环境": -8}},
         {"text": "把堆做成纪念馆", "dims": {"文化": 7, "自由": -5}}]},

    {"word": "断桥", "bodies": ["象", "甲", "鹿", "马", "鲸"], "allowed_elements": ["赤炎", "苍穹"],
     "scene": "它每年拆一次河上那座桥，拆得很准。",
     "actions": [
         {"text": "每年重修，成本照付", "dims": {"繁荣": 6, "环境": -6}},
         {"text": "不修了，改摆渡", "dims": {"平等": 6, "繁荣": -6}},
         {"text": "把村子迁到对岸", "dims": {"和平": 6, "文化": -6}}]},

    {"word": "守灯", "bodies": ["灯虫", "鸦", "龟", "树", "隼"], "allowed_elements": ["星云", "赤炎"],
     "scene": "它守着一盏灯，船靠这盏灯认路；它已经守了三百年。",
     "actions": [
         {"text": "让它继续守", "dims": {"和平": 6, "自由": -5}},
         {"text": "改成自动灯塔，让它退下来", "dims": {"繁荣": 7, "文化": -7}},
         {"text": "把守灯人封圣", "dims": {"文化": 8, "平等": -5}}]},

    {"word": "分巢", "bodies": ["蜂", "甲", "菌", "灯虫", "鸦"], "allowed_elements": ["幽林", "晶岩"],
     "scene": "它的巢一年分一次，分出来的都往城里搬。",
     "actions": [
         {"text": "给它划地盘", "dims": {"环境": 6, "繁荣": -6}},
         {"text": "灭巢", "dims": {"繁荣": 6, "环境": -8}},
         {"text": "登记为城市的一部分", "dims": {"平等": 8, "和平": -6}}]},

    {"word": "蜕忆", "bodies": ["章鱼", "龟", "鲸", "树", "鸦"], "allowed_elements": ["星云", "深海"],
     "scene": "它忘事，忘得很干净，旁边的人也跟着忘。",
     "actions": [
         {"text": "让它忘，人也不记得旧仇", "dims": {"和平": 8, "文化": -8}},
         {"text": "隔绝它，别让人靠近", "dims": {"文化": 6, "自由": -7}},
         {"text": "把忘掉的事写下来", "dims": {"文化": 7, "平等": -4}}]},
]

db = json.load(open(P, encoding="utf-8"))
have = {b["word"] for b in db["behaviors"]}
added = 0
for b in NEW:
    if b["word"] in have:
        continue
    db["behaviors"].append(b)
    added += 1

db["meta"]["rules"].append("行为之间必须一升一降：每个选项恰好一个维度上、一个维度下")

open(P, "w", encoding="utf-8").write(json.dumps(db, ensure_ascii=False, indent=2))

print(f"新增 {added} 条行为，现有 {len(db['behaviors'])} 条，选项 {len(db['behaviors']) * 3} 个")

# ---- 立即自检：每个行为必须恰好一升一降；骨架词必须存在 ----
body_words = {b["word"] for b in db["bodies"]}
el_words = {e["word"] for e in db["elements"]}
errs = []
for b in db["behaviors"]:
    for a in b["actions"]:
        pos = [k for k, v in a["dims"].items() if v > 0]
        neg = [k for k, v in a["dims"].items() if v < 0]
        if len(pos) != 1 or len(neg) != 1:
            errs.append(f"{b['word']}/{a['text']} 不是一升一降：{a['dims']}")
    miss = [w for w in b["bodies"] if w not in body_words]
    if miss:
        errs.append(f"{b['word']} 引用了不存在的骨架 {miss}")
    bad_el = [e for e in b["allowed_elements"] if e not in el_words]
    if bad_el:
        errs.append(f"{b['word']} 引用了不存在的元素 {bad_el}")
print("自检：" + ("通过" if not errs else "失败"))
for e in errs:
    print("  " + e)
