# -*- coding: utf-8 -*-
"""由 slice/data.js 生成 slice/data-en.js（英文版数据）。
做法：所有中文串集中在这张表里，逐字段替换；生成后扫描是否还残留中日韩字符，
残留即报错退出——不做"部分翻译"的半成品。
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(ROOT, "slice", "data.js")
OUT = os.path.join(ROOT, "slice", "data-en.js")

# ---------- 词汇表 ----------
ELEM = {"星云": "Nebula", "晶岩": "Crystal", "赤炎": "Ember", "苍穹": "Sky",
        "深海": "Deepsea", "幽林": "Gloomwood"}
BODY = {"鸦": "Crow", "甲": "Shell", "马": "Horse", "树": "Tree",
        "隼": "Falcon", "鹿": "Deer", "蜂": "Swarm", "象": "Elephant"}
BEHAVIOR = {"守灯": "Lampkeeping", "寄居": "Squatting", "焚界": "Border-burning",
            "埋种": "Seeding", "吟唱": "Chanting", "落尘": "Dustfalling",
            "结网": "Weaving", "鸣雷": "Thunder-call"}
DIM = {"环境": "Environment", "和平": "Peace", "自由": "Freedom",
       "平等": "Equality", "繁荣": "Prosperity", "文化": "Culture"}
VERB = {"洞察": "Insight", "安抚": "Sooth", "催生": "Quickening", "固守": "Ward",
        "迁徙": "Migration", "结契": "Pact", "撕裂": "Tear", "献祭": "Offering"}
TARGET = {"一只兽": "One Beast", "一群兽": "One Herd", "一个村": "One Village",
          "一片地": "One Tract", "一季": "One Season", "自己": "Self"}
STRENGTH = {"轻": "Light", "中": "Medium", "重": "Heavy"}
COST = {"轻": "no tick (3 per run)", "中": "1 tick", "重": "1 tick, chaos +2"}

BEAST = {
    "守誓星云鸦": "Oathkeeper Nebula Crow",
    "祭祀晶岩甲": "Votive Crystal Shell",
    "流亡赤炎马": "Exile Ember Horse",
    "记忆晶岩树": "Remembering Crystal Tree",
    "回声苍穹隼": "Echo Sky Falcon",
    "边界晶岩鹿": "Borderline Crystal Deer",
    "债星云蜂": "Debt Nebula Swarm",
    "复生苍穹象": "Revived Sky Elephant",
}

MAT = {
    "霜骨": "Frostbone", "霜羽": "Frostfeather", "霜甲": "Frostplate",
    "烬鳞": "Emberscale", "星丝": "Starthread", "潮膜": "Tidesheen",
    "晶核": "Crystalcore", "苔绒": "Mossdown", "雷脊": "Thunderspine",
    "盐睫": "Saltlash", "骨灯": "Bonelamp", "雾筋": "Mistwire",
    "灰绒": "Ashdown", "火砂": "Embersand", "空髓": "Hollowmarrow",
    "铁胫": "Ironstave", "云鳍": "Cloudfin", "菌伞": "Raincap",
    "缠丝": "Coilthread", "眠壳": "Sleepshell",
}
FORM = {"骨": "Bone", "羽": "Feather", "甲": "Plate", "鳞": "Scale", "丝": "Thread",
        "膜": "Sheen", "核": "Core", "绒": "Down", "脊": "Spine", "睫": "Lash",
        "灯": "Lamp", "筋": "Wire", "砂": "Sand", "髓": "Marrow", "胫": "Stave",
        "鳍": "Fin", "伞": "Cap", "壳": "Shell"}

TEXT = {
    # world
    "正在退潮的霜原": "The Ebbing Frostlands",
    "霜原": "Frost Steppe",
    "雪线一年往下压一层，村子跟着往下搬一次": "Each year the snowline presses one layer lower, and the village moves down with it.",
    "能源": "Energy",
    "灯亮着的代价，写在没人住的那一区。": "The price of lamplight is written in the district nobody lives in.",
    "第二颗 灰烬带（正片）": "World 2 · Ash Belt (main run)",
    "雪线一年往下压一层，村子跟着往下搬一次。灯亮着的代价，写在没人住的那一区。":
        "Each year the snowline presses one layer lower, and the village moves down with it. The price of lamplight is written in the district nobody lives in.",
    "星轨财团": "Stellar Track Consortium",
    "把这片星区当资产，且从不隐瞒这一点": "Treats this sector as an asset, and never hides the fact.",
    "联盟政府": "Alliance Government",
    "承认自己无能为力，但坚持秩序比效率重要": "Admits it is powerless, yet insists order outranks efficiency.",
    "平民议会": "Civic Assembly",
    "刚拿到席位，第一次发现席位不附带权力": "Just won its seats, and found that seats come without power.",
    # shapes
    "会学人说话，但只说它记得的那几句；暗紫，体内有缓慢旋转的亮点，夜里看得见它在动":
        "Mimics human speech, but only the few phrases it remembers; dark violet, with slow-rotating lights inside — at night you can see it move.",
    "壳上刻着它出生那年的雨量，一年一道；半透明白，撞击时发出玻璃声，碎了会长回去":
        "Its shell is carved with the rainfall of the year it was born, one groove a year; translucent white, rings like glass when struck, and regrows when broken.",
    "跑起来时地面会记得，路被踩出来后就一直在；橘红，靠近时影子会先变热，再看才见光":
        "The ground remembers it running: once a path is stamped out it stays; orange-red, and as you near it the shadow heats before you see the light.",
    "站得比谁都久，动得比谁都慢，倒下的那天最响；半透明白，撞击时发出玻璃声，碎了会长回去":
        "Stands longer than anything, moves slower than anything, is loudest on the day it falls; translucent white, rings like glass when struck, regrows when broken.",
    "翅膀收起来时像一把折起的伞，落地的声音比身体重；铁灰蓝，边缘带着雷声，雨前会低下来":
        "Folded wings look like a closed umbrella; its landing sounds heavier than its body; iron-grey blue, thunder on the edges, drops lower before rain.",
    "角每年换一次，旧角留在原地不带走；半透明白，撞击时发出玻璃声，碎了会长回去":
        "Its antlers turn over once a year and the old pair is left where it stood; translucent white, rings like glass when struck, regrows when broken.",
    "一整群只有一个意志，分开就都停住；暗紫，体内有缓慢旋转的亮点，夜里看得见它在动":
        "The whole swarm runs on a single will and freezes when split; dark violet, with slow-rotating lights inside.",
    "记得所有走过的路，走的时候比谁都慢；铁灰蓝，边缘带着雷声，雨前会低下来":
        "Remembers every road it has walked, and walks slower than anything; iron-grey blue, thunder on the edges, drops lower before rain.",
    # hooks
    "它守的东西，已经不在了。": "What it keeps watch over is already gone.",
    "它被供奉，也被害怕，两件事同时发生。": "It is worshipped and feared, both at once.",
    "它是从别的地方来的，那地方已经不在了。": "It came from somewhere else, and that place is gone.",
    "它记住的事，比这片土地更久。": "What it remembers outlasts this land.",
    "它发出的声音，总比它自己晚到一步。": "Its voice always arrives a step behind it.",
    "它只在这条线以内活动，线是它自己画的。": "It moves inside one line, and drew that line itself.",
    "它欠着什么，没人知道是谁的。": "It owes something, and nobody knows to whom.",
    "它死过一次。第二次不太一样。": "It has died once. The second time is not the same.",
    # options（24）
    "让它继续守": "Let it keep watch",
    "改成自动灯塔，让它退下来": "Swap in an automated lighthouse and retire it",
    "把守灯人封圣": "Canonize the lampkeeper",
    "清空废墟，赶走它们": "Clear the ruins and drive them out",
    "共存，把废墟划成保护区": "Coexist: make the ruins a preserve",
    "登记居民，给它们户籍": "Register them as residents",
    "让它烧完，让界线彻底消失": "Let it burn out and erase the border",
    "在火头前重修工事，把界钉住": "Rebuild the works ahead of the fire and pin the border",
    "撤离沿线居民，地不要了": "Evacuate the borderlands and abandon the ground",
    "等它长，把这块地划为林地": "Let it grow; zone the land as forest",
    "挖出来卖": "Dig it up and sell it",
    "把埋种地划为祖产": "Declare the seedbed ancestral land",
    "录下吟唱，做成全城广播": "Record the chant and broadcast it citywide",
    "禁声，宵禁到天亮": "Silence it; curfew until dawn",
    "学着唱，让居民跟着唱": "Learn the song and teach it to the residents",
    "收集落尘做肥料": "Collect the dustfall as fertilizer",
    "赶它离开农田": "Drive it off the farmland",
    "把落尘当神迹供奉": "Worship the dustfall as a miracle",
    "让人走网，不问去向": "Let people cross the web, ask nothing",
    "剪断网，恢复关卡": "Cut the web and restore the checkpoints",
    "收费过网，网归公": "Charge tolls; the web becomes public",
    "让它只劈荒野": "Make it strike only the wilds",
    "引雷入网做能源": "Channel the lightning into the grid",
    "驱离它": "Drive it off",
    # material traits（20）
    "在零下也不裂": "does not crack even below zero",
    "落地比身体重": "lands heavier than its own body",
    "壳上刻着年轮": "carries growth rings on the shell",
    "碰过的东西会暖": "whatever it touches turns warm",
    "夜里有亮点在走": "lights travel through it at night",
    "一直湿着": "never dries out",
    "碎了会长回去": "regrows after it breaks",
    "走过留痕，第二天才见": "leaves marks visible only the next day",
    "雨前会低下来": "drops low before rain",
    "睁着也不流泪": "stays open without tears",
    "烧三百年不灭": "burns for three hundred years",
    "拉着它就飘起来": "pull it and you rise",
    "越拍越热": "the more you beat it, the hotter it gets",
    "踩出火星就熄": "sparks when stepped on, then goes out",
    "空的地方会自己长": "emptiness grows itself back",
    "走一步地就记得": "the ground remembers every step",
    "游在云里": "swims in cloud",
    "撑开就下雨": "opens up and it rains",
    "系上就解不开": "once tied, it will not come undone",
    "睡着的比醒着的多": "more of it is asleep than awake",
    # verb rationale
    "看清真相，秩序就松了": "Truth surfaces, and order loosens",
    "摁住冲突，也摁住了别的": "Hold down conflict, and everything else with it",
    "长得快，是因为透支": "It grows fast because it is overdrawn",
    "保住了旧物，也就挡住了新事": "Keep the old safe, and block the new",
    "人流动了，地方就淡了": "People move, and the place fades",
    "订盟的人安全，没订的人不平": "The sworn are safe; the unsworn are not",
    "打破既有分配，也砸坏地基": "Break the old allocation, and the foundation with it",
    "让土地休养，代价有人扛": "Give the land rest; someone carries the cost",
    # preset names
    "晶骨甲兽": "Frostbone Warden",
    "星丝膜兽": "Starthread Sheen",
    "炎鳞砂兽": "Emberscale Sand",
    "渊膜睫兽": "Abyss Sheen Lash",
    "林绒伞兽": "Grove Down Cap",
    # keywords
    "霜": "frost", "骨": "bone", "守": "ward", "星": "star", "夜": "night",
    "静": "still", "火": "fire", "噬": "devour", "断": "sever", "海": "sea",
    "眠": "sleep", "抚": "soothe", "苔": "moss",
}

UI_EN = {
    "abilityText": "{form} {verb} · {target} · {strength}",
    "verbs": {k: v for k, v in VERB.items()},
    "targets": {k: v for k, v in TARGET.items()},
    "strengths": {k: v for k, v in STRENGTH.items()},
    "cost": {k: v for k, v in COST.items()},
    "forms": {k: v for k, v in FORM.items()},
    "move": "Move one node (advances 1 tick)",
    "moveLog": "Tick {t} · moved to {name}",
    "observe": "Observe “{name}” (advances 1 tick, drops {drop})",
    "observeLog": "Tick {t} · observed {name} → got {drop} (replaced slot {i})",
    "light": "Trim {text} ({n} left this run)",
    "lightLog": "Tick {t} · trimmed {text} (no tick spent, {n} left)",
    "abilityLog": "Tick {t} · used {text} ({up} +{mag} / {down} −{mag})",
    "optionLog": "Tick {t} · encounter {name} → {text}",
    "cause": {"混沌终焉": "Cosmic Collapse", "文明崩塌": "Civic Collapse",
              "灰烬": "Ash End", "存活": "Survived"},
    "dims": DIM,
}
UI_EN["cost"] = COST

CJK = re.compile(r"[\u3400-\u9fff]")


def tr(v, where):
    if v is None or not isinstance(v, str):
        return v
    if v in TEXT:
        return TEXT[v]
    if v in ELEM:
        return ELEM[v]
    raise SystemExit(f"[未翻译] {where}：{v}")


def tr_list(vs, where):
    return [tr(v, where) for v in vs]


def ability_text(preset, a):
    """素材形态 + 动词 + 目标 + 强度，例如 Bone Ward · One Village · Heavy"""
    return (f"{preset['_form']} {VERB[a['verb']]} · {TARGET[a['target']]} · {STRENGTH[a['strength']]}")


def main():
    raw = open(SRC, encoding="utf-8").read()
    payload = raw[raw.index("{"): raw.rindex(";")]
    data = json.loads(payload)

    w = data["world"]
    w["name"] = tr(w["name"], "world.name")
    w["biome"] = tr(w["biome"], "world.biome")
    w["biomeScene"] = tr(w["biomeScene"], "world.biomeScene")
    w["issue"] = tr(w["issue"], "world.issue")
    w["issueLine"] = tr(w["issueLine"], "world.issueLine")
    w["opening"] = tr(w["opening"], "world.opening")
    w["DLabel"] = tr(w["DLabel"], "world.DLabel")
    for f in w["factions"]:
        f["name"] = tr(f["name"], "faction.name")
        f["stance"] = tr(f["stance"], "faction.stance")

    for b in w["beasts"]:
        b["name"] = BEAST[b["name"]]
        b["element"] = ELEM[b["element"]]
        b["body"] = BODY[b["body"]]
        b["behavior"] = BEHAVIOR[b["behavior"]]
        b["measure"] = ""
        b["shape"] = tr(b["shape"], "beast.shape")
        b["hook"] = tr(b["hook"], "beast.hook")
        b["drop"] = MAT[b["drop"]]
        for a in b["actions"]:
            a["text"] = tr(a["text"], "beast.action")
            # dims 的键保持中文：引擎与逻辑层靠它定位维度，界面按 ui.dims 显示

    for m in data["materials"]:
        m["word"] = MAT[m["word"]]
        m["element"] = ELEM[m["element"]]
        m["form"] = FORM[m["form"]]
        m["trait"] = tr(m["trait"], "material.trait")
        # verbs 保持中文：它是能力池的机制键，界面靠 ui.verbs 显示

    # grammar 整体保持中文：动词/目标/强度/代价都是机制键，展示全部走 ui.*
    g = data["grammar"]

    for p in data["presets"]:
        # 此时 slots 还是中文，先取首件素材的形态做能力名前缀，再翻译
        p["_form"] = FORM[MAT_FORM(p["slots"][0])]
        p["name"] = tr(p["name"], "preset.name")
        p["keywords"] = tr_list(p["keywords"], "preset.keywords")
        p["slots"] = [MAT[s] for s in p["slots"]]
        p["verbs"] = [VERB[v] for v in p["verbs"]]
        for a in p["equipped"]:
            a["text"] = ability_text(p, a)
            a["id"] = a["text"]
            a["cost"] = COST[a["strength"]]   # 展示用；机制判档靠 strength 中文键
            # strength / verb / target / up_dim / down_dim 保持中文：机制键
        p.pop("_form")

    data["ui"] = UI_EN

    # ---- 残留检查：机制键按设计保留中文，只查"人眼会看到"的字段 ----
    SKIP_KEYS = {"up_dim", "down_dim", "upDim", "downDim", "strength", "verbs",
                 "verb", "target", "grammar", "seed"}
    SKIP_PATHS = ("/materials", "/presets")

    def walk(node, path=""):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in SKIP_KEYS:
                    continue
                # 素材与预设里的 verbs/strength 等是机制键，整块跳过人工检查
                if path.split("/")[-1] in ("equipped",) and k in ("strength",):
                    continue
                yield from walk(v, path + "/" + str(k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from walk(v, path + f"[{i}]")
        elif isinstance(node, str) and CJK.search(node):
            yield path, node

    left = list(walk(data))

    payload_en = json.dumps(data, ensure_ascii=False, indent=1)
    open(OUT, "w", encoding="utf-8").write(
        "/* auto-generated, do not edit: tools/slice/build_slice_data_en.py */\n"
        "window.SLICE_DATA_EN = " + payload_en + ";\n")

    print(f"写入 {OUT}（{len(payload_en)} 字节）")
    if left:
        print(f"残留中文 {len(left)} 处：")
        for p, s in left[:20]:
            print("  ", p, s)
        raise SystemExit(1)
    print("残留中文检查：0 处（dims 键与 up_dim/down_dim 按设计保留中文）")


def MAT_FORM(zh_word):
    """素材名 → 形态（取 beastgen 的 MATERIALS 定义，保证与生成器一致）"""
    import sys
    sys_path = os.path.join(ROOT, "tools", "beastgen")
    if sys_path not in sys.path:
        sys.path.insert(0, sys_path)
    from beastgen import MATERIALS
    for w, e, f, v, t in MATERIALS:
        if w == zh_word:
            return f
    raise SystemExit(f"素材不存在：{zh_word}")


if __name__ == "__main__":
    main()
