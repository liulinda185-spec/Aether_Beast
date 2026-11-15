# -*- coding: utf-8 -*-
"""把 final_out.json 的难度阶梯与四打法存活率打印出来，作为 engine 的对照基准。"""
import json
import os

P = (r"C:\Users\yingg\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode"
     r"\workspace\.sessions\38453088985749506\agents\m_0cweTgepC1G\calc\final_out.json")
print("读取：", P, os.path.exists(P))

d = json.load(open(P, encoding="utf-8"))
print("顶层键：", list(d.keys()))

lad = d.get("difficulty_ladder", {})
print("\n难度阶梯（两层展开）：")
for k, v in lad.items():
    print(f"  {k}")
    if isinstance(v, dict):
        for kk, vv in v.items():
            if isinstance(vv, dict):
                print(f"     {kk}:")
                for k3, v3 in vv.items():
                    print(f"        {k3} = {v3}")
            elif isinstance(vv, list):
                print(f"     {kk}: list len={len(vv)} 首={vv[0] if vv else None}")
            else:
                print(f"     {kk} = {vv}")

rep = d.get("representative", {})
print("\n代表局（打法 → 摘要）：")
for name, v in rep.items():
    if isinstance(v, dict):
        print(f"  {name}: keys={list(v.keys())}")
        for kk, vv in v.items():
            if not isinstance(vv, list):
                print(f"     {kk} = {vv}")
        rec = v.get("rec")
        if rec:
            print(f"     rec 长度={len(rec)}，首={rec[0]}，末={rec[-1]}")
