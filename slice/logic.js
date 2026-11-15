/**
 * 切片逻辑层 · 16 刻状态机
 * 只做规则，不做渲染。Node 可 require（headless 200 局自测），浏览器挂 global.SliceLogic。
 *
 * 刻结构：奇数刻 = 自由刻（移动 / 观察 / 中重档能力，各占 1 刻；轻档随时可用不占刻，每局 3 次）
 *         偶数刻 = 遭遇刻（从 8 只世界兽里按顺序抽一只，必选一个选项）
 */
(function (global) {
  "use strict";

  var E = (typeof require === "function" && typeof module !== "undefined")
    ? require("../engine.js") : global.ABEngine;

  var DIMS = E.DIMS;

  /** 文案模板：中英两份数据各带一套 ui，逻辑层不写死任何一种语言 */
  function fmt(tpl, kv) {
    return String(tpl).replace(/\{(\w+)\}/g, function (m, k) {
      return kv[k] !== undefined ? kv[k] : m;
    });
  }
  function ui(g) { return g.data.ui || {}; }

  function clampMag(x) { return Math.max(3, Math.min(9, Math.round(x))); }

  /** 由 3 件素材重建能力池与装备（与 beastgen.py 的规则一致）
   *  机制值（动词/强度/维度）始终用中文做键，只有展示文案走 data.ui 的翻译。 */
  function rebuildBeast(data, slots) {
    var U = data.ui || {};
    var byWord = {};
    data.materials.forEach(function (m) { byWord[m.word] = m; });
    var mats = slots.map(function (w) { return byWord[w]; }).filter(Boolean);
    var verbs = [];
    mats.forEach(function (m) {
      m.verbs.forEach(function (v) { if (verbs.indexOf(v) < 0) verbs.push(v); });
    });

    var g = data.grammar, pool = [], firstForm = mats[0] ? mats[0].form : "";
    g.verbs.forEach(function (v) {
      if (verbs.indexOf(v.word) < 0) return;
      g.targets.forEach(function (t) {
        g.strengths.forEach(function (s) {
          var mag = clampMag(s.base * t.mult);
          pool.push({
            id: v.word + "·" + t.word + "·" + s.word,
            text: fmt(U.abilityText || "{verb}·{target}·{strength}", {
              form: (U.forms && U.forms[firstForm]) || firstForm,
              verb: (U.verbs && U.verbs[v.word]) || v.word,
              target: (U.targets && U.targets[t.word]) || t.word,
              strength: (U.strengths && U.strengths[s.word]) || s.word
            }),
            verb: v.word, target: t.word, strength: s.word,
            upDim: v.up, downDim: v.down, mag: mag,
            cost: (U.cost && U.cost[s.word]) || g.cost[s.word]
          });
        });
      });
    });

    var dirs = {};
    verbs.forEach(function (v) {
      var def = g.verbs.filter(function (x) { return x.word === v; })[0];
      if (def) dirs[def.up] = 1;
    });
    var dirCount = Object.keys(dirs).length;
    var nSlots = Math.min(4, Math.max(2, dirCount));
    return { verbs: verbs, pool: pool, equipped: equip(pool, nSlots), dirCount: dirCount };
  }

  /** 装备配比：2 重 / 1 中 / 1 轻；重、中必须换方向，轻档允许同维微调 */
  function equip(pool, n) {
    var quota = { 4: [["重", 2], ["中", 1], ["轻", 1]],
                  3: [["重", 1], ["中", 1], ["轻", 1]],
                  2: [["重", 1], ["中", 1]] }[n] || [["重", 1]];
    var picked = [], usedUp = {}, usedTg = {};

    function best(st, allowReuse) {
      var c = pool.filter(function (a) {
        return a.strength === st && (allowReuse || !usedUp[a.upDim]);
      }).sort(function (x, y) { return (y.mag - x.mag) || (x.id < y.id ? -1 : 1); });
      var fresh = c.filter(function (a) { return !usedTg[a.target]; });
      return fresh.length ? fresh[0] : (c[0] || null);
    }

    quota.forEach(function (pair) {
      for (var i = 0; i < pair[1]; i++) {
        if (picked.length >= n) return;
        var a = best(pair[0], pair[0] === "轻");
        if (!a) a = pool.filter(function (x) { return picked.indexOf(x) < 0; })[0];
        if (a) { picked.push(a); usedUp[a.upDim] = 1; usedTg[a.target] = 1; }
      }
    });
    return picked.slice(0, n);
  }

  function createGame(data, presetIndex) {
    var preset = data.presets[presetIndex || 0];
    var beast = rebuildBeast(data, preset.slots);
    var st = E.createState({ div: data.world.D });
    return {
      data: data,
      preset: preset,
      st: st,
      slots: preset.slots.slice(),
      beast: beast,
      inventory: [],
      observed: [],
      pos: 0,
      lightLeft: 3,
      over: false,
      outcome: null,
      log: []
    };
  }

  function currentEncounter(g) {
    var next = g.st.tick + 1;
    if (next > g.data.world.ticks) return null;
    if (next % 2 !== 0) return null;
    return g.data.world.beasts[next / 2 - 1] || null;
  }

  function availableActions(g) {
    if (g.over) return [];
    var next = g.st.tick + 1, out = [], i;
    var enc = currentEncounter(g);

    if (enc) {
      enc.actions.forEach(function (a, idx) {
        out.push({ id: "option:" + idx, kind: "option", label: a.text });
      });
    } else {
      var U = ui(g);
      out.push({ id: "move", kind: "move", label: U.move });
      var cur = g.data.world.beasts[g.pos];
      if (g.observed.indexOf(g.pos) < 0) {
        out.push({ id: "observe", kind: "observe",
                   label: fmt(U.observe, { name: cur.name, drop: cur.drop }) });
      }
      g.beast.equipped.forEach(function (a, idx) {
        if (a.strength !== "轻") {
          out.push({ id: "ability:" + idx, kind: "ability", label: a.text + "（" + a.cost + "）" });
        }
      });
    }

    // 轻档随时可用，不占刻，每局 3 次
    if (g.lightLeft > 0) {
      g.beast.equipped.forEach(function (a, idx) {
        if (a.strength === "轻") {
          out.push({ id: "light:" + idx, kind: "light",
                     label: fmt(ui(g).light, { text: a.text, n: g.lightLeft }) });
        }
      });
    }
    return out;
  }

  function touchesIssue(g, dims) {
    var k = DIMS[g.data.world.issueDim - 1];
    return !!(dims && Object.prototype.hasOwnProperty.call(dims, k));
  }

  function act(g, id) {
    if (g.over) return g;
    var parts = id.split(":"), idx = parseInt(parts[1], 10);

    if (parts[0] === "option") {
      var enc = currentEncounter(g);
      var a = enc.actions[idx];
      E.applyBeastOption(g.st, { dims: a.dims, solve: touchesIssue(g, a.dims) });
      g.log.push(fmt(ui(g).optionLog, { t: g.st.tick, name: enc.name, text: a.text }));

    } else if (parts[0] === "move") {
      g.pos = (g.pos + 1) % g.data.world.beasts.length;
      E.settle(g.st, { v: [0, 0, 0, 0, 0, 0] });
      g.log.push(fmt(ui(g).moveLog, { t: g.st.tick, name: g.data.world.beasts[g.pos].name }));

    } else if (parts[0] === "observe") {
      if (g.observed.indexOf(g.pos) < 0) {
        var cur = g.data.world.beasts[g.pos];
        g.observed.push(g.pos);
        g.inventory.push(cur.drop);
        // 换掉"去掉后方向损失最少"的那一槽
        var bestSlot = 0, bestDirs = -1;
        for (var i = 0; i < 3; i++) {
          var trial = g.slots.slice(); trial[i] = cur.drop;
          var d = rebuildBeast(g.data, trial).dirCount;
          if (d > bestDirs) { bestDirs = d; bestSlot = i; }
        }
        g.slots[bestSlot] = cur.drop;
        g.beast = rebuildBeast(g.data, g.slots);
        E.settle(g.st, { v: [0, 0, 0, 0, 0, 0] });
        g.log.push(fmt(ui(g).observeLog, {
          t: g.st.tick, name: cur.name, drop: cur.drop, i: bestSlot + 1 }));
      }

    } else if (parts[0] === "ability") {
      var ab = g.beast.equipped[idx];
      E.applyAbility(g.st, ab);
      var D = ui(g).dims || {};
      g.log.push(fmt(ui(g).abilityLog, { t: g.st.tick, text: ab.text,
        up: D[ab.upDim] || ab.upDim, mag: ab.mag,
        down: D[ab.downDim] || ab.downDim }));

    } else if (parts[0] === "light") {
      if (g.lightLeft > 0) {
        var la = g.beast.equipped[idx];
        E.applyAbility(g.st, la, { advance: false });
        g.lightLeft -= 1;
        g.log.push(fmt(ui(g).lightLog, { t: g.st.tick, text: la.text, n: g.lightLeft }));
      }
    }

    if (g.st.died) { g.over = true; g.outcome = g.st.why; }
    else if (g.st.tick >= g.data.world.ticks) { g.over = true; g.outcome = "存活"; }
    return g;
  }

  var API = { createGame: createGame, availableActions: availableActions, act: act,
              currentEncounter: currentEncounter, rebuildBeast: rebuildBeast, equip: equip };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  global.SliceLogic = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
