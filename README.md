# Aether Beast — 以太兽 3D

**Aether Beast is a browser-based, AI-ready creature-adventure game where you create your own beast, explore a procedurally generated 3D wilderness of five biomes, gather Ether Shards, and make an evolution choice that reshapes the rest of your run.**

> 一句话简介：创造一个属于你的兽，在每次随机重编的 3D 荒野里收集以太结晶、躲开影兽，并在旅途中做一次真正改变战局的进化抉择。

## 玩法

- 开局选择兽的元素（火 / 水 / 风 / 地 / 影）
- 在 3D 开放地形中奔跑，收集 **15 个以太结晶**
- 每张地图随机生成 5 个生物群系：翠色野原、熔岩裂隙、镜水低地、古木深林、暮色夹缝
- 躲避 8 只游荡追击的影兽，被撞会损失生命
- 收集到第 8 个结晶时触发**进化三选一**：烈阳之心 / 疾风之羽 / 磐石之核，选择会真实改变后续体验
- 生命归零或集满结晶结束一局

## 操作

| 设备 | 操作 |
|---|---|
| 桌面 | WASD / 方向键移动，鼠标拖拽转视角 |
| 手机 | 左侧滑动移动（虚拟摇杆），右侧滑动转视角 |

## 技术

- 纯静态单文件 HTML + Three.js（CDN 加载），无需后端
- 地形、群系布局、结晶与敌人分布由程序种子生成，每次开局不同
- 代码中预留了 AI 生成接口（场景文案 / 兽故事），后续可接入 LLM

## 部署到 GitHub Pages（5 步）

1. 打开 [github.com](https://github.com)，新建一个仓库（如 `aether-beast`），勾选 **Public**
2. 本文件夹里的 `index.html` 和 `README.md` 就是这个仓库的全部内容——直接上传这两个文件
   - GitHub 网页端：仓库页面 → **Add file → Upload files** → 拖入两个文件 → Commit
3. 进入仓库 **Settings → Pages**
4. **Source** 选 `Deploy from a branch`，Branch 选 `main` / `master`，目录选 `/ (root)`，点 **Save**
5. 等 1–2 分钟，你的游戏就会出现在 `https://<你的用户名>.github.io/aether-beast/`

## 本地试玩

直接双击打开 `index.html` 即可（无需安装任何东西）。

## 版本

- v0.2 — 生物群系地貌 + 进化三选一（当前）
- v0.1 — 2D 文字三选一切片（已归档）
