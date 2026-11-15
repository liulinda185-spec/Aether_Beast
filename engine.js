/**
 * 幻兽星河 · engine.js v0.1
 * 纯函数引擎：无 DOM、无渲染、无依赖。Node 可直接 require，浏览器挂 global.ABEngine。
 *
 * 数值权威来自 GDD §3.2/§3.3 与 final_calc.py，本文件不重新发明任何常数。
 * 随机数用 mulberry32，与 worldgen / beastgen 同一个算法，保证同种子同局。
 */
(function (global) {
  "use strict";

  var DIMS = ["环境", "和平", "自由", "平等", "繁荣", "文化"];

  var PARAM = {
    INIT: 50,        // 六维初值
    K: 2.5,          // 均衡度系数
    D: 15,           // 混沌除子
    CHAOS_MAX: 100,
    TH_BAL: 28,      // 崩塌阈值
    TH_MU: 20,       // 灰烬：六维均值阈值
    TH_STREAK: 6,    // 连续刻数
    TURNS: 16,
    P0: 1.0, P_MAX: 3.0, P_UP: 0.3, P_DOWN: 1.2,   // 议题压力
    GE_DIFF: 25, GE_DRIFT: 0.6,                      // 善恶背景漂移
    GE_VEC: [0.6, 0.0, -0.6, 0.6, -0.6, 0.0]
  };

  // ---------------- 随机 ----------------
  function mulberry32(seed) {
    var a = seed >>> 0;
    return {
      next: function () {
        a = (a + 0x6D2B79F5) >>> 0;
        var t = a;
        t = ((t ^ (t >>> 15)) * (t | 1)) >>> 0;
        var inner = ((t ^ (t >>> 7)) * (t | 61)) >>> 0;
        t = (t ^ ((t + inner) >>> 0)) >>> 0;
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
      }
    };
  }

  function RNG(seed) {
    this.g = mulberry32(seed);
  }
  RNG.prototype.r = function () { return this.g.next(); };
  RNG.prototype.int = function (n) { return Math.floor(this.r() * n) % n; };
  RNG.prototype.uniform = function (lo, hi) { return lo + (hi - lo) * this.r(); };
  RNG.prototype.pick = function (arr) { return arr[this.int(arr.length)]; };
  RNG.prototype.sample = function (arr, n) {
    var pool = arr.slice(), out = [];
    for (var i = 0; i < n && pool.length; i++) out.push(pool.splice(this.int(pool.length), 1)[0]);
    return out;
  };

  // ---------------- 数值 ----------------
  function sigma(d) {
    var m = 0, i;
    for (i = 0; i < 6; i++) m += d[i];
    m /= 6;
    var v = 0;
    for (i = 0; i < 6; i++) v += (d[i] - m) * (d[i] - m);
    return Math.sqrt(v / 6);           // 总体标准差，除以 6
  }
  function balance(d) { return Math.max(0, Math.min(100, 100 - PARAM.K * sigma(d))); }
  function mean6(d) {
    var m = 0; for (var i = 0; i < 6; i++) m += d[i];
    return m / 6;
  }
  function clampDims(d) {
    for (var i = 0; i < 6; i++) d[i] = Math.max(0, Math.min(100, d[i]));
    return d;
  }

  // ---------------- 事件卡（与 final_calc.py 的 make_card 同分布） ----------------
  function makeCard(rng) {
    var issueDim = rng.int(6), opts = [], k, o, gain, cost, d;
    for (k = 0; k < 3; k++) {
      gain = rng.sample([0, 1, 2, 3, 4, 5], 2);
      cost = rng.sample([0, 1, 2, 3, 4, 5].filter(function (x) { return gain.indexOf(x) < 0; }), 2);
      o = { v: [0, 0, 0, 0, 0, 0], g: 0, e: 0, solve: gain.indexOf(issueDim) >= 0 };
      for (d = 0; d < 2; d++) {
        o.v[gain[d]] = rng.uniform(8, 14);
        o.v[cost[d]] = -rng.uniform(5, 11);
      }
      if (cost.indexOf(2) >= 0 || cost.indexOf(5) >= 0) o.e += rng.uniform(2, 5);
      if (cost.indexOf(0) >= 0 || cost.indexOf(3) >= 0) o.e += rng.uniform(1, 3);
      if (gain.indexOf(0) >= 0 || gain.indexOf(3) >= 0 || gain.indexOf(5) >= 0) o.g += rng.uniform(2, 5);
      if (cost.indexOf(4) >= 0) o.g += rng.uniform(1, 3);
      opts.push(o);
    }
    return opts;
  }

  // ---------------- 状态 ----------------
  function createState(opt) {
    opt = opt || {};
    return {
      dims: [PARAM.INIT, PARAM.INIT, PARAM.INIT, PARAM.INIT, PARAM.INIT, PARAM.INIT],
      chaos: 0,
      issue: PARAM.P0,
      good: 0,
      evil: 0,
      streakBal: 0,
      streakMu: 0,
      tick: 0,
      div: opt.div || PARAM.D,
      died: false,
      why: null,
      log: []
    };
  }

  /** 只算不写：给 UI 或验收脚本读当前读数 */
  function derived(st) {
    var b = balance(st.dims), m = mean6(st.dims);
    var loss = Math.max(0, (100 - b) / st.div);
    var decay = Math.max(0, (50 - m) / st.div);
    var rate = loss + decay + st.issue;
    var grow = rate * Math.pow(1 + st.chaos / 100, 2.0);
    return { sigma: sigma(st.dims), balance: b, mu: m, loss: loss, decay: decay,
             rate: rate, grow: grow };
  }

  /** 一步结算：六维/善恶/议题 → 混沌增长 → 死法判定。所有行动都走这里。
   *  opts.advance=false 用于"不占刻"的行动（轻档微调）：仍算混沌与死法，但不推进刻数。 */
  function settle(st, delta, opts) {
    var i;
    var advance = !opts || opts.advance !== false;
    // 1) 六维与善恶
    if (delta && delta.v) for (i = 0; i < 6; i++) st.dims[i] += delta.v[i];
    if (delta && delta.g) st.good = Math.min(100, st.good + delta.g);
    if (delta && delta.e) st.evil = Math.min(100, st.evil + delta.e);
    clampDims(st.dims);

    // 2) 善恶背景漂移（已锁定的第 2 项决策）
    var diff = st.good - st.evil;
    if (Math.abs(diff) >= PARAM.GE_DIFF) {
      var sign = diff > 0 ? 1 : -1;
      for (i = 0; i < 6; i++) st.dims[i] += PARAM.GE_VEC[i] * sign * PARAM.GE_DRIFT;
      clampDims(st.dims);
    }

    // 3) 议题压力：处置则回落，其余任何"过了这一课还没处理"的行动都让压力自己往上顶
    if (delta && typeof delta.solve === "boolean") {
      st.issue = Math.max(0, Math.min(PARAM.P_MAX,
        st.issue + (delta.solve ? -PARAM.P_DOWN : PARAM.P_UP)));
    } else if (advance) {
      st.issue = Math.min(PARAM.P_MAX, st.issue + PARAM.P_UP);
    }

    // 4) 混沌
    var d = derived(st);
    st.chaos += d.grow;
    if (advance) st.tick += 1;

    // 5) 死法（优先级：混沌终焉 → 文明崩塌 → 灰烬）
    st.streakBal = d.balance < PARAM.TH_BAL ? st.streakBal + 1 : Math.max(0, st.streakBal - 1);
    st.streakMu = d.mu < PARAM.TH_MU ? st.streakMu + 1 : Math.max(0, st.streakMu - 1);

    var why = null;
    if (st.chaos >= PARAM.CHAOS_MAX) why = "混沌终焉";
    else if (st.streakBal >= PARAM.TH_STREAK) why = "文明崩塌";
    else if (st.streakMu >= PARAM.TH_STREAK) why = "灰烬";

    st.log.push({ tick: st.tick, balance: +d.balance.toFixed(1), mu: +d.mu.toFixed(1),
                  chaos: +Math.min(st.chaos, 100).toFixed(1), issue: +st.issue.toFixed(2),
                  why: why });
    if (why) { st.died = true; st.why = why; }
    return st;
  }

  // ---------------- 神兽能力 ----------------
  /**
   * 能力结算。作用域"自己"= 自省：善恶各向 50 回归，代价照付（降维减半）。
   * 其余作用域：升维 +mag，降维 -mag，封顶由 beastgen 保证（3–9）。
   */
  function applyAbility(st, ab, opts) {
    // 兼容两处字段名：beastgen 的构建用 upDim/downDim，catalog 用 up_dim/down_dim
    var upDim = ab.upDim || ab.up_dim;
    var downDim = ab.downDim || ab.down_dim;
    var delta = { v: [0, 0, 0, 0, 0, 0], g: 0, e: 0 };
    var ui = DIMS.indexOf(upDim), di = DIMS.indexOf(downDim);
    if (ab.target === "自己") {
      var back = Math.min(ab.mag, Math.abs(st.good - 50), Math.abs(st.evil - 50));
      delta.g = st.good < 50 ? back : -back;
      delta.e = st.evil < 50 ? back : -back;
      if (di >= 0) delta.v[di] = -Math.floor(ab.mag / 2);
    } else {
      if (ui >= 0) delta.v[ui] = ab.mag;
      if (di >= 0) delta.v[di] = -ab.mag;
    }
    // 用 strength 判重档（cost 是给人读的文案，可能是别的语言）
    if (ab.strength === "重" || ab.cost === "重") st.chaos += 2;
    return settle(st, delta, opts);
  }

  // ---------------- 卡牌模式（验收 A6 用，机制与 final_calc.py 一致） ----------------
  function scorePolicy(policy, st, o) {
    var nd = clampDims([0, 1, 2, 3, 4, 5].map(function (i) { return st.dims[i] + o.v[i]; }));
    if (policy === "greedy") {
      var sum = 0; for (var i = 0; i < 6; i++) sum += nd[i];
      return -sum;                                    // 取总产出最大
    }
    if (policy === "spread") return sigma(nd);        // 取离散最小
    if (policy === "steward") {
      return 0.5 * sigma(nd)
        + 0.15 * Math.abs((st.good + o.g) - (st.evil + o.e))
        + (o.solve ? -1.2 : 1.2);
    }
    return 0;
  }

  function runCardGame(seed, policy, div, turns) {
    var rng = new RNG(seed), st = createState({ div: div });
    turns = turns || PARAM.TURNS;
    for (var t = 0; t < turns; t++) {
      var opts = makeCard(rng), i;
      if (policy === "random") i = rng.int(3);
      else {
        var best = 0, bs = scorePolicy(policy, st, opts[0]);
        for (i = 1; i < 3; i++) {
          var s = scorePolicy(policy, st, opts[i]);
          if (s < bs) { bs = s; best = i; }
        }
        i = best;
      }
      var o = opts[i];
      settle(st, { v: o.v, g: o.g, e: o.e, solve: o.solve });
      if (st.died) break;
    }
    return { died: st.died, why: st.why || "存活", turn: st.tick,
             chaos: +Math.min(st.chaos, 100).toFixed(1), log: st.log };
  }

  // ---------------- 世界模式（垂直切片用） ----------------
  /**
   * 世界兽的选项：{dims:{环境:+8,自由:-6}}，由 idea_db 的 behavior actions 提供。
   * 观察：花 1 个自由刻换 1 件素材（掉落在 drops.js 里算，引擎只记账）。
   */
  function applyBeastOption(st, action) {
    var delta = { v: [0, 0, 0, 0, 0, 0], solve: true };
    Object.keys(action.dims || {}).forEach(function (k) {
      var i = DIMS.indexOf(k);
      if (i >= 0) delta.v[i] = action.dims[k];
    });
    return settle(st, delta);
  }

  var API = {
    DIMS: DIMS, PARAM: PARAM, RNG: RNG,
    sigma: sigma, balance: balance, mean6: mean6,
    createState: createState, derived: derived, settle: settle,
    makeCard: makeCard, applyAbility: applyAbility,
    applyBeastOption: applyBeastOption, runCardGame: runCardGame
  };

  if (typeof module !== "undefined" && module.exports) module.exports = API;
  global.ABEngine = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
