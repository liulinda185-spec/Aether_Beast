/**
 * 垂直切片 · 六条验收（A1–A6）
 * 运行：node tools/slice/test_engine.js
 * 全部用真实数据，不写死期望值以外的东西。
 */
"use strict";

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..");
const E = require(path.join(ROOT, "engine.js"));

const WORLD_JSON = path.join(ROOT, "tools", "worldgen", "worlds_100.json");
const BEAST_JSON = path.join(ROOT, "tools", "beastgen", "beast_db.json");

let pass = 0, fail = 0;
const lines = [];
function check(id, name, ok, detail) {
  lines.push(`${ok ? "PASS" : "FAIL"}  ${id}  ${name}${detail ? "　" + detail : ""}`);
  if (ok) pass++; else fail++;
}

// ---------------------------------------------------------------- A1 同种子同局
(function A1() {
  const a = E.runCardGame(20261111, "spread", 12, 16);
  const b = E.runCardGame(20261111, "spread", 12, 16);
  const same = JSON.stringify(a) === JSON.stringify(b);
  check("A1", "同种子必同局", same, `两局混沌 ${a.chaos} / ${b.chaos}，刻数 ${a.turn}`);
  // 逐刻序列比较（浮点严格相等）
  const da = a.log.map(x => `${x.tick}:${x.balance}:${x.chaos}`).join("|");
  const db = b.log.map(x => `${x.tick}:${x.balance}:${x.chaos}`).join("|");
  check("A1b", "逐刻序列完全一致", da === db, da === db ? "16 刻序列逐项相同" : "序列有差异");
})();

// ---------------------------------------------------------------- A2 与配平表读数一致
(function A2() {
  const SAMPLES = [
    { name: "健康均衡", dims: [50, 50, 50, 50, 50, 50], exBal: 100, exSigma: 0 },
    { name: "失衡独裁", dims: [100, 100, 0, 100, 100, 100], exBal: 6.8, exSigma: 37.3 },
    { name: "失序繁荣", dims: [40, 45, 95, 35, 90, 30], exBal: 34.0, exSigma: 26.4 },
    { name: "全员崩坏", dims: [10, 10, 10, 10, 10, 10], exBal: 100, exSigma: 0 }
  ];
  let worst = 0, rows = [];
  for (const s of SAMPLES) {
    const sg = E.sigma(s.dims), bal = E.balance(s.dims);
    const dBal = Math.abs(bal - s.exBal), dSg = Math.abs(sg - s.exSigma);
    worst = Math.max(worst, dBal, dSg);
    rows.push(`${s.name}: σ=${sg.toFixed(2)}(期望${s.exSigma}) 均衡度=${bal.toFixed(1)}(期望${s.exBal})`);
  }
  check("A2", "四个世界样本读数与 GDD/配平表一致（≤0.1）", worst <= 0.1,
        rows.join("；") + `　最大偏差 ${worst.toFixed(2)}`);
})();

// ---------------------------------------------------------------- A3 三种死法
(function A3() {
  // 1) 混沌终焉：除子 5，乱选
  const g = E.runCardGame(777001, "random", 5, 16);
  check("A3a", "混沌终焉可触发", g.why === "混沌终焉", `第 ${g.turn} 刻，${g.why}，混沌 ${g.chaos}`);

  // 2) 文明崩塌：给定 100/100/0/100/100/100，不施加任何变动
  const st = E.createState({ div: 15 });
  st.dims = [100, 100, 0, 100, 100, 100];
  let whyB = null, tickB = 0;
  for (let i = 0; i < 16; i++) {
    E.settle(st, { v: [0, 0, 0, 0, 0, 0] });
    if (st.died) { whyB = st.why; tickB = st.tick; break; }
  }
  check("A3b", "文明崩塌可触发", whyB === "文明崩塌", `第 ${tickB} 刻，${whyB}，混沌 ${st.chaos.toFixed(1)}`);

  // 3) 灰烬：六维全 10（均衡度 100，所以不能被误判成"平衡得好"）
  const st2 = E.createState({ div: 15 });
  st2.dims = [10, 10, 10, 10, 10, 10];
  let whyC = null, tickC = 0;
  for (let i = 0; i < 16; i++) {
    E.settle(st2, { v: [0, 0, 0, 0, 0, 0] });
    if (st2.died) { whyC = st2.why; tickC = st2.tick; break; }
  }
  check("A3c", "灰烬可触发（且不被均衡度误判）", whyC === "灰烬",
        `第 ${tickC} 刻，${whyC}，混沌 ${st2.chaos.toFixed(1)}，均衡度 ${E.balance(st2.dims).toFixed(1)}`);
})();

// ---------------------------------------------------------------- A4 能力合法
(function A4() {
  const db = JSON.parse(fs.readFileSync(BEAST_JSON, "utf8"));
  const cat = db.catalog || [];
  const ids = new Set(cat.map(c => c.id));
  const badDir = cat.filter(c => c.up_dim === c.down_dim);
  const badMag = cat.filter(c => c.mag < 3 || c.mag > 9);
  check("A4", "144 形状可实例化、一升一降、量级 3–9",
        cat.length === 144 && ids.size === 144 && !badDir.length && !badMag.length,
        `形状 ${cat.length}，唯一 ${ids.size}，方向异常 ${badDir.length}，量级异常 ${badMag.length}`);

  // 能力真的能结算：拿一条重档能力打到干净状态上，六维必须一动一静
  const ab = cat.find(c => c.cost === "占 1 刻，混沌 +2" && c.target === "一个村");
  const st = E.createState({ div: 15 });
  const before = st.dims.slice();
  E.applyAbility(st, ab);
  const up = E.DIMS.indexOf(ab.up_dim), dn = E.DIMS.indexOf(ab.down_dim);
  const okApply = (st.dims[up] - before[up]) === ab.mag && (before[dn] - st.dims[dn]) === ab.mag;
  check("A4b", "能力结算方向正确（+mag / −mag）", okApply,
        `${ab.id}：${ab.up_dim} ${before[up]}→${st.dims[up]}，${ab.down_dim} ${before[dn]}→${st.dims[dn]}`);
})();

// ---------------------------------------------------------------- A5 素材可达（霜原）
(function A5() {
  const worlds = JSON.parse(fs.readFileSync(WORLD_JSON, "utf8")).worlds;
  const db = JSON.parse(fs.readFileSync(BEAST_JSON, "utf8"));
  const mats = db.materials || [];
  const BODY_FORM = {
    "鲸": ["鳍", "鳞", "膜"], "鹿": ["骨", "胫"], "隼": ["羽", "脊"], "蛇": ["鳞", "膜"],
    "甲": ["甲", "壳"], "藤": ["丝", "绒"], "菌": ["伞", "绒"], "蜂": ["绒", "丝"],
    "鱼群": ["鳞", "膜"], "象": ["胫", "骨"], "鸦": ["羽", "骨"], "龟": ["壳", "甲"],
    "灯虫": ["灯", "丝"], "树": ["骨", "核"], "章鱼": ["丝", "膜"], "马": ["胫", "脊"]
  };
  function cands(beast) {
    const fams = BODY_FORM[beast.body] || [];
    const strict = mats.filter(m => fams.includes(m.form) && m.element === beast.element);
    if (strict.length) return strict;
    const sameEl = mats.filter(m => m.element === beast.element);
    if (sameEl.length) return sameEl;
    return mats.filter(m => fams.includes(m.form));
  }
  const world = worlds.find(w => w.biome === "霜原");
  const rng = new E.RNG(world.seed_used);
  const got = world.beasts.map(b => {
    const c = cands(b).slice().sort((x, y) => x.word.localeCompare(y.word));
    return c[rng.int(c.length)].word;
  });
  const distinct = [...new Set(got)];
  check("A5", "霜原 8 只兽可采到 ≥3 件素材", distinct.length >= 3,
        `${world.name}：${got.join("、")} → 去重 ${distinct.length} 件`);
})();

// ---------------------------------------------------------------- A6 存活率同档
(function A6() {
  // 参考值来自 calc/final_out.json（第三世 坍缩区 div=12，每组 2000 局）
  const REF = { random: 0.039, greedy: 0.051, spread: 0.812, steward: 0.915 };
  const N = 2000, DIV = 12;
  const got = {}, rows = [];
  let worst = 0;
  for (const pol of ["random", "greedy", "spread", " steward".trim()]) {
    let surv = 0;
    for (let i = 0; i < N; i++) {
      const r = E.runCardGame(900000 + i * 7919, pol, DIV, 16);
      if (!r.died) surv++;
    }
    got[pol] = surv / N;
    const d = Math.abs(got[pol] - REF[pol]);
    worst = Math.max(worst, d);
    rows.push(`${pol} ${(got[pol] * 100).toFixed(1)}% vs ${(REF[pol] * 100).toFixed(1)}% (差 ${(d * 100).toFixed(1)}pt)`);
  }
  check("A6", "四打法存活率与配平表同档（≤3pt）", worst <= 0.03,
        `div=12，每组 ${N} 局：` + rows.join("；"));
})();

// ---------------------------------------------------------------- 汇总
console.log(lines.join("\n"));
console.log(`\n通过 ${pass} 项，失败 ${fail} 项`);
process.exit(fail ? 1 : 0);
