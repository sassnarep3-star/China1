/* Headless render check for the China1 site.
 *
 *   cd scripts && npm i jsdom && node render_check.js
 *
 * Loads every page over HTTP, executes its scripts, and fails if a page throws,
 * leaves its data container empty, or leaks a literal "undefined" into the DOM.
 * Requires a static server:  python3 -m http.server 8080 --bind 0.0.0.0
 * (jsdom is a dev-only dependency and is not committed.)
 */
const { JSDOM, VirtualConsole } = require("jsdom");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const BASE = process.env.BASE || "http://127.0.0.1:8080/";
const EXPECT = {
  "index.html": "mini-table", "channels.html": "channels-table",
  "costs.html": "costs-table", "us-tax.html": "forms-table",
  "prohibited.html": "prohibited-list", "flagged.html": "unverified",
  "sources.html": "sources-cn"
};

(async () => {
  const pages = fs.readdirSync(ROOT).filter(f => f.endsWith(".html")).sort();
  if (!pages.length) {
    console.error("No .html pages found under " + ROOT + " — refusing a vacuous pass.");
    process.exit(1);
  }
  let fail = 0;
  for (const p of pages) {
    const errs = [];
    const vc = new VirtualConsole();
    vc.on("jsdomError", e => errs.push("jsdomError: " + e.message));
    const dom = await JSDOM.fromFile(path.join(ROOT, p), {
      runScripts: "dangerously", resources: "usable",
      virtualConsole: vc, url: BASE + p
    });
    await new Promise(r => setTimeout(r, 400));
    const d = dom.window.document;
    if (EXPECT[p]) {
      const el = d.getElementById(EXPECT[p]);
      if (!el || !el.querySelectorAll("tr, .panel").length)
        errs.push("container " + EXPECT[p] + " rendered empty");
    }
    if (/undefined/.test(d.body.innerHTML)) errs.push("literal 'undefined' in DOM");
    if (!d.querySelector(".site-nav a")) errs.push("no navigation rendered");
    if (errs.length) fail++;
    console.log((errs.length ? "FAIL  " : " ok   ") + p.padEnd(18) +
      " rows=" + d.querySelectorAll("tbody tr").length +
      " sourceLinks=" + d.querySelectorAll("a.src[href]").length);
    errs.forEach(e => console.log("        ! " + e));
    dom.window.close();
  }
  console.log(fail ? "\n" + fail + " page(s) failed" : "\nAll pages render with no JS errors.");
  process.exit(fail ? 1 : 0);
})();
