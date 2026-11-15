/**
 * 静态检查 slice/index.html：内联脚本语法 + 引用的文件是否存在。
 * 运行：node tools/slice/check_html.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..", "..");
const target = process.argv[2] || "index.html";
const HTML = path.join(ROOT, "slice", target);
const html = fs.readFileSync(HTML, "utf8");
console.log(`检查 ${target}`);

// 内联脚本：最后一个不含 src 的 <script> 块
const blocks = [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]);
let ok = true;
blocks.forEach((src, i) => {
  try { new vm.Script(src, { filename: `inline-${i}.js` }); }
  catch (e) { ok = false; console.log(`FAIL  内联脚本 ${i} 语法错误：${e.message}`); }
});
if (ok) console.log(`PASS  内联脚本语法（${blocks.length} 块，${blocks.reduce((a,b)=>a+b.length,0)} 字节）`);

// 引用文件
const refs = [...html.matchAll(/<script[^>]*\bsrc="([^"]+)"/g)].map(m => m[1]);
let allExist = true;
for (const r of refs) {
  const p = path.resolve(path.dirname(HTML), r);
  const exists = fs.existsSync(p);
  if (!exists) allExist = false;
  console.log(`${exists ? "PASS" : "FAIL"}  引用 ${r} → ${p}`);
}
console.log(allExist ? "\n静态检查通过（未做视觉验证）" : "\n静态检查失败");
process.exit((ok && allExist) ? 0 : 1);
