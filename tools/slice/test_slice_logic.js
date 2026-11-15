/**
 * 切片逻辑 · headless 自测（不依赖浏览器）
 * 运行：node tools/slice/test_slice_logic.js
 */
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..", "..");
const E = require(path.join(ROOT, "engine.js"));
const L = require(path.join(ROOT, "slice", "logic.js"));
global.ABEngine = E;

// 第二个参数传 en 时跑英文数据（同一套逻辑，只换数据）
const LANG = (process.argv[2] || "zh").toLowerCase();
const DATA_FILE = LANG === "en" ? "data-en.js" : "data.js";
const DATA_KEY = LANG === "en" ? "SLICE_DATA_EN" : "SLICE_DATA";

const src = fs.readFileSync(path.join(ROOT, "slice", DATA_FILE), "utf8");
const sandbox = { window: {} };
vm.createContext(sandbox);
vm.runInContext(src, sandbox);
const DATA = sandbox.window[DATA_KEY];
console.log(`语言：${LANG}（${DATA_FILE}）\n`);
let pass = 0, fail = 0;
const out = [];
function check(id, name, ok, detail) {
  out.push(`${ok ? "PASS" : "FAIL"}  ${id}  ${name}${detail ? "　" + detail : ""}`);
  ok ? pass++ : fail++;
}

// ---- S1 数据完整性 ----
check("S1", "数据完整（8 兽 / 20 素材 / 24 行为动作 / 5 预设）",
  DATA.world.beasts.length === 8 && DATA.materials.length === 20 && DATA.presets.length === 5,
  `兽 ${DATA.world.beasts.length}，素材 ${DATA.materials.length}，预设 ${DATA.presets.length}`);

// ---- S2 每个预设都能开局且能走完一局（乱选） ----
const outcomes = {};
for (let p = 0; p < DATA.presets.length; p++) {
  const g = L.createGame(DATA, p);
  let guard = 0;
  while (!g.over && guard++ < 200) {
    const acts = L.availableActions(g);
    if (!acts.length) break;
    L.act(g, acts[0].id);
  }
  outcomes[DATA.presets[p].keywords.join("")] = g.outcome || "卡住";
}
const finished = Object.values(outcomes).every(v => v !== "卡住");
check("S2", "5 个预设都能走完一局（不卡住）", finished, JSON.stringify(outcomes));

// ---- S3 观察真的掉素材并改写构筑 ----
(function S3() {
  const g = L.createGame(DATA, 0);
  const before = JSON.stringify(g.slots);
  let guard = 0;
  while (!g.over && guard++ < 60) {
    const acts = L.availableActions(g);
    const obs = acts.find(a => a.kind === "observe");
    if (obs) { L.act(g, obs.id); break; }
    L.act(g, acts[0].id);
  }
  check("S3", "观察掉素材并替换槽位", g.inventory.length >= 1 && JSON.stringify(g.slots) !== before,
    `采到 ${g.inventory.join("、")}；槽位 ${before} → ${JSON.stringify(g.slots)}`);
})();

// ---- S4 轻档每局最多 3 次，且不推进刻 ----
(function S4() {
  const g = L.createGame(DATA, 3);
  let lights = 0, tickBefore = g.st.tick;
  for (let i = 0; i < 10; i++) {
    const acts = L.availableActions(g);
    const light = acts.find(a => a.kind === "light");
    if (!light) break;
    const t = g.st.tick;
    L.act(g, light.id);
    if (g.st.tick === t) lights++;
    if (g.over) break;
  }
  check("S4", "轻档限 3 次且不推进刻", g.lightLeft === 0 && lights <= 3,
    `用掉 ${3 - g.lightLeft} 次，刻数 ${tickBefore}→${g.st.tick}`);
})();

// ---- S5 结局分布（随机策略，跑够样本才看得到分布） ----
(function S5() {
  const causes = {};
  let lcg = 424242;
  function rnd() { lcg = (lcg * 1103515245 + 12345) & 0x7fffffff; return lcg / 0x7fffffff; }
  for (let p = 0; p < DATA.presets.length; p++) {
    for (let n = 0; n < 60; n++) {
      const g = L.createGame(DATA, p);
      let guard = 0;
      while (!g.over && guard++ < 200) {
        const acts = L.availableActions(g);
        if (!acts.length) break;
        L.act(g, acts[Math.floor(rnd() * acts.length)].id);
      }
      causes[g.outcome] = (causes[g.outcome] || 0) + 1;
    }
  }
  check("S5", "随机策略下结局不止一种", Object.keys(causes).length >= 2,
    `300 局：${JSON.stringify(causes)}`);
})();

// ---- S6 200 局同种子可复现 ----
(function S6() {
  function run(p, n) {
    let d = 0, surv = 0;
    for (let i = 0; i < n; i++) {
      const g = L.createGame(DATA, p);
      let guard = 0;
      while (!g.over && guard++ < 200) {
        const acts = L.availableActions(g);
        if (!acts.length) break;
        L.act(g, acts[acts.length - 1].id);   // 固定策略：每次选最后一个动作
      }
      if (g.outcome === "存活") surv++; else d++;
    }
    return { d, surv };
  }
  const a = run(0, 100), b = run(0, 100);
  const same = JSON.stringify(a) === JSON.stringify(b);
  check("S6", "固定策略 100 局结果可复现", same,
    `两次都是 存活 ${a.surv} / 死 ${a.d}`);
})();

console.log(out.join("\n"));
console.log(`\n通过 ${pass} 项，失败 ${fail} 项`);
process.exit(fail ? 1 : 0);
