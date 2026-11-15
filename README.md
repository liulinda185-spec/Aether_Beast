# Aether Beast · 幻兽星河

A turn-based **civilisation balance** game. Six dimensions — Environment, Peace, Freedom, Equality, Prosperity, Culture — drift each tick; every choice raises one and lowers another; imbalance turns into chaos, and chaos ends the run.

> 一句话：六维文明在每一次选择里一升一降，失衡累积成混沌，混沌终局。神兽不是战斗单位，是**你干预世界的那只手**。

**Play right now** · 直接开玩

| Version | Offline | Online (GitHub Pages) |
|---|---|---|
| 中文 | [`slice/index.html`](slice/index.html) | [slice/](https://liulinda185-spec.github.io/Aether_Beast/slice/index.html) |
| English | [`slice/index-en.html`](slice/index-en.html) | [slice/index-en.html](https://liulinda185-spec.github.io/Aether_Beast/slice/index-en.html) |

No server, no build, no dependencies — double-click the file, or open the online link once Pages is enabled (root serves a two-button landing page). Add `?auto=2` to skip straight to an ending screen.

---

## What is this

This repository is the build log of a game that changed direction mid-way, and the change is visible in the artefacts.

**v0.1** was a card-game balance model: 16 rounds, three sources of pressure, a difficulty ladder, four player archetypes simulated 2000 runs each. That produced a GDD, a nine-sheet balance workbook, and four charts.

**v0.2** pivoted to open-world exploration: worlds and creatures come out of an idea database plus a seed, and the player's own beast is generated from **keywords**. Two rules survived the pivot:

- Keywords may never touch numbers directly. Keywords pick *materials*; materials carry *verbs*; verbs are grammatical and their numbers are fixed in advance. A keyword system that writes stats destroys reproducibility, offline cost, and the balance envelope at the same time.
- A material is only obtained by **observing** the creature that carries it — observation costs one of the eight free ticks, so a full collection run means never moving.

The playable slice in `slice/` is the result: **one world (a frost steppe), 8 creatures, 1 generated beast with 3 material slots, 16 ticks (8 encounters + 8 free ticks)**.

---

## The numbers are the design

Six dimensions start at 50. Balance is a function of spread, not of level:

```
μ = mean(six dims)          σ = population std (divided by 6)
Balance = clamp(100 − 2.5σ, 0, 100)
chaos growth = ( (100−Balance)/15 + (50−μ)/15 + issuePressure ) × (1 + chaos/100)²
```

Three ways to die, checked in this order: `chaos ≥ 100` → `Balance < 28` for 6 consecutive ticks → `μ < 20` for 6 consecutive ticks.

The third one exists because of a real hole: a world with **all six dimensions at 10** has perfect balance (σ = 0, Balance = 100). Balanced readings, dead civilisation. The decay term and the ash check close it — and the test suite asserts exactly that case.

### Verification (all runnable)

`node tools/slice/test_engine.js` → **10/10**

| # | Claim | Measured |
|---|---|---|
| A1 | Same seed ⇒ same run | two runs: chaos 57.7 / 57.7, 16-tick sequence identical |
| A2 | Readings match GDD (≤0.1) | max deviation **0.09** |
| A3 | All three deaths reachable | chaos end at tick 8 · collapse at 6 · ash at 6 |
| A3c | Ash ≠ balanced | all-dims-10 world: Balance **100.0**, still judged ash |
| A4 | 144 ability shapes legal | 144 unique, 0 direction errors, 0 magnitude errors |
| A5 | Frost steppe harvest | 8 creatures → 8 distinct materials |
| A6 | Survival rates match the workbook (≤3pt) | max deviation **2.9pt** over 4 archetypes × 2000 runs |

`node tools/slice/test_slice_logic.js [en]` → **6/6**, both languages. Cross-language check: 300 random runs in Chinese and in English produce **the identical distribution** (chaos-end 128 / survived 172) — proof the translation carries no mechanical drift.

---

## Architecture

```
engine.js              254 lines, zero dependencies, Node + browser, mulberry32 PRNG
                       all rules live here; the UI never recomputes a number
slice/logic.js         16-tick state machine: free ticks vs encounters, observation,
                       material→verb→ability pipeline, light-tier "no tick spent"
slice/data.js          generated · one world + 20 materials + grammar + 5 keyword presets
slice/data-en.js       generated · same via a translation table with a leftover-CJK gate
slice/index.html       playable UI (Canvas 2D), Chinese
slice/index-en.html    playable UI, English — same engine and logic, different data
tools/worldgen/        idea database + world generator (24 behaviours, 16 bodies, 8 biomes)
tools/beastgen/        keyword → materials → verbs → 144 ability shapes
tools/slice/           data builders + the two test suites above
docs/                  GDD, nine-sheet balance workbook, design reports, charts
```

Design rule worth stating: **mechanical values are never translated.** In the English build, `strength`, dimension names and verb keys stay as the original tokens — only display strings go through `data.ui`. A first attempt that translated the light/medium/heavy tokens broke the light tier and the heavy-tier chaos penalty without raising a single error.

---

## Run it, rebuild it

```bash
# play
open slice/index.html          # or double-click

# verify
node tools/slice/test_engine.js
node tools/slice/test_slice_logic.js
node tools/slice/test_slice_logic.js en

# regenerate data (needs python)
python tools/slice/build_slice_data.py
python tools/slice/build_slice_data_en.py
```

---

## Design documents

| Document | What it holds |
|---|---|
| [GDD (v0.1)](docs/GDD-幻兽星河-v0.1.md) | six dimensions, three pressure sources, morality as background drift, still-water ending |
| [Balance workbook](docs/数值配平表-幻兽星河-v0.1.xlsx) | 9 sheets: parameters, balance curve, chaos timeline, card pool, pacing, endings, difficulty ladder, beast grammar |
| [Open-world generator report](docs/v0.2-开放世界-方向与生成器验证.md) | why the generator lives outside the engine, and the four compatibility axes it took to stop producing contradictions |
| [Beast grammar](docs/v0.2-神兽生成方案.md) | keyword → material → verb chain, 144 shapes, why keywords cannot write numbers |
| [Slice spec](docs/v0.2-垂直切片规格.md) | the 16-tick scope and the six acceptance criteria |
| [Verification report](docs/切片验收报告.md) | the measured numbers, plus the four defects the tests and the screenshots actually caught |

Charts: [k=2.5 balance curve](docs/img/图1_失衡系数对比.png) · [chaos acceleration](docs/img/图2_混沌加速曲线.png) · [world samples](docs/img/图3_世界样本雷达.png) · [four archetypes](docs/img/图4_四种玩法混沌轨迹.png) · [slice screenshot](docs/img/图5_切片界面.png) · [English slice](docs/img/fig6_slice_en.png)

---

## The older prototype

[`legacy/3d-collect.html`](legacy/3d-collect.html) is an earlier, unrelated build: a Three.js 3D creature-collecting game (five biomes, 15 crystals, 8 shadow beasts, one evolution choice). It still runs and it is kept because it is a different game, not a worse one. WASD / arrows to move, drag to look.

The v0.2 direction is the one in `slice/`, and the root `index.html` is a two-button landing page between the two.

---

## Status

Playable slice — done. Not done: 24 behaviours → 60, 20 materials → 36 (the 20 fill only 20 of the 36 element×form cells, so 58% of drops currently match by element only), still-water ending proven reachable, sub-species suffixes for duplicate creature names.
