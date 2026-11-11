#!/usr/bin/env node
/*
 * Render canonical project-site pages in headless Chromium at phone, tablet and
 * desktop sizes. The temporary server models a GitHub Pages /China1/ base path.
 * No source pages or user information are requested by the browser.
 */
'use strict';

const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');

// The bundled Chromium includes Amazon Linux runtime libraries; this instructs
// the package to extract them as well on minimal environments such as CI.
if (!process.env.AWS_EXECUTION_ENV) process.env.AWS_EXECUTION_ENV = 'AWS_Lambda_nodejs22.x';
const puppeteer = require('puppeteer-core');
const chromium = require('@sparticuz/chromium');

const root = path.resolve(__dirname, '..');
const base = '/China1/';
const pages = ['index.html', ...fs.readdirSync(path.join(root, 'guide'))
  .filter(name => name.endsWith('.html')).sort().map(name => `guide/${name}`)];
const widths = [320, 360, 390, 768, 1280];
const issues = [];
const observations = [];

function logError(location, message) { issues.push(`${location}: ${message}`); }

const server = http.createServer((req, res) => {
  let pathname;
  try { pathname = decodeURIComponent(new URL(req.url, 'http://local.test').pathname); }
  catch { res.writeHead(400).end('Bad URL'); return; }
  if (!pathname.startsWith(base)) { res.writeHead(404).end('Not found'); return; }
  const relative = pathname.slice(base.length) || 'index.html';
  const filename = path.resolve(root, relative);
  if (!filename.startsWith(root + path.sep)) { res.writeHead(403).end('Forbidden'); return; }
  fs.readFile(filename, (error, contents) => {
    if (error) { res.writeHead(404).end('Not found'); return; }
    const ext = path.extname(filename).toLowerCase();
    const type = {'.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
      '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8'}[ext] || 'application/octet-stream';
    res.writeHead(200, {'content-type': type, 'cache-control': 'no-store'}).end(contents);
  });
});

async function run() {
  await new Promise(resolve => server.listen(0, '0.0.0.0', resolve));
  const origin = `http://127.0.0.1:${server.address().port}${base}`;
  let browser;
  let runs = 0;
  try {
    browser = await puppeteer.launch({
      executablePath: await chromium.executablePath(),
      args: chromium.args,
      headless: true,
    });
    const version = await browser.version();
    const tab = await browser.newPage();
    tab.on('pageerror', error => logError(tab.url(), `uncaught script error: ${error.message}`));
    for (const width of widths) {
      await tab.setViewport({width, height: 900, deviceScaleFactor: 1});
      for (const name of pages) {
        const location = `${name} @ ${width}px`;
        let response;
        try {
          response = await tab.goto(origin + name, {waitUntil: 'load', timeout: 30000});
          if (!response || response.status() !== 200) {
            logError(location, `HTTP ${response ? response.status() : 'no response'}`);
            continue;
          }
          const metrics = await tab.evaluate(() => {
            for (const el of document.querySelectorAll('details')) el.open = true;
            const nameless = [...document.querySelectorAll('a[href]')].filter(a => {
              return !a.textContent.trim() && !a.getAttribute('aria-label') &&
                !a.getAttribute('title') && !a.querySelector('img[alt]:not([alt=""])');
            }).length;
            const missingAlt = [...document.images].filter(img => !img.hasAttribute('alt')).length;
            const clippedTables = [...document.querySelectorAll('table')].filter(table => {
              const box = table.getBoundingClientRect();
              if (box.right <= innerWidth + 1 && box.left >= -1) return false;
              for (let parent = table.parentElement; parent; parent = parent.parentElement) {
                const overflow = getComputedStyle(parent).overflowX;
                if ((overflow === 'auto' || overflow === 'scroll') && parent.scrollWidth > parent.clientWidth) return false;
              }
              return true;
            }).length;
            const smallTargets = [...document.querySelectorAll('nav a')].filter(a => {
              const r = a.getBoundingClientRect();
              return r.width < 24 || r.height < 24;
            }).length;
            return {
              width: innerWidth, docWidth: document.documentElement.scrollWidth,
              lang: document.documentElement.lang, title: document.title,
              viewport: !!document.querySelector('meta[name="viewport"]'),
              headings: document.querySelectorAll('h1').length,
              mains: document.querySelectorAll('main').length,
              navigation: document.querySelectorAll('nav').length,
              nameless, missingAlt, clippedTables, smallTargets,
              details: document.querySelectorAll('details').length,
            };
          });
          if (metrics.width !== width) logError(location, `expected viewport ${width}, got ${metrics.width}`);
          if (metrics.docWidth > width + 1) logError(location, `page overflows horizontally (${metrics.docWidth}px)`);
          if (!metrics.lang || !metrics.title || !metrics.viewport) logError(location, 'missing language, title or viewport metadata');
          if (metrics.headings !== 1 || metrics.mains !== 1 || !metrics.navigation) {
            logError(location, `landmarks: h1=${metrics.headings}, main=${metrics.mains}, nav=${metrics.navigation}`);
          }
          if (metrics.nameless) logError(location, `${metrics.nameless} links lack an accessible name`);
          if (metrics.missingAlt) logError(location, `${metrics.missingAlt} images lack alt attributes`);
          if (metrics.clippedTables) logError(location, `${metrics.clippedTables} tables overflow without a scroll container`);
          if (metrics.smallTargets) observations.push(`${location}: ${metrics.smallTargets} nav links under 24px in one dimension`);
          if (metrics.details) {
            const toggled = await tab.evaluate(() => {
              const details = document.querySelector('details');
              details.open = false;
              return !!details.querySelector('summary');
            });
            if (!toggled) logError(location, 'details element has no summary');
            else {
              await tab.click('details summary');
              if (!await tab.$eval('details', element => element.open)) logError(location, 'details summary did not open');
            }
          }
          if (process.env.QA_SCREENSHOTS === '1' && name === 'index.html' && (width === 360 || width === 1280)) {
            const out = path.join(__dirname, 'artifacts');
            fs.mkdirSync(out, {recursive: true});
            await tab.screenshot({path: path.join(out, `landing-${width}.png`), fullPage: false});
          }
          runs++;
        } catch (error) {
          logError(location, `navigation/rendering failed: ${error.message}`);
        }
      }
    }
    console.log(`Browser: ${version}`);
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
  for (const observation of observations.slice(0, 30)) console.log('REVIEW:', observation);
  if (issues.length) {
    for (const issue of issues.slice(0, 60)) console.error('FAIL:', issue);
    console.error(`FAIL: ${issues.length} rendering issues across ${runs} successful page loads`);
    process.exitCode = 1;
  } else {
    console.log(`PASS: ${pages.length} canonical pages × ${widths.length} widths = ${runs} real-browser renders; ` +
      `no page-level overflow, uncontained tables, missing landmarks or nameless links. ${observations.length} observations.`);
  }
}

run().catch(error => { console.error(error); server.close(); process.exitCode = 1; });
