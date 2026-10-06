/**
 * 用 citeproc-js（Zotero 内部使用的同一引用引擎）与 Zotero 样式仓库的
 * GB/T 7714-2015 (numeric) 样式，把 CSL-JSON 渲染成文末参考文献表。
 *
 * 双语处理：GB/T 7714-2015 要求中文文献用「等」、西文文献用「et al.」。
 * CSL 一个文档只能挂一种 locale，故用 en-US 渲染全表，再对含中日韩字符的
 * 条目把 et al. 回写成「等」。这是唯一的人工后处理，其余字段全部由引擎产出。
 *
 * 输入：results/references_csl.json
 *        tools/china-national-standard-gb-t-7714-2015-numeric.csl
 *        tools/locales-en-US.xml
 * 输出：results/references_gbt7714.json
 *
 * 用法：cd tools && node render_bibliography.mjs
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import CSL from 'citeproc';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');

const cslJson = JSON.parse(readFileSync(join(root, 'results/references_csl.json'), 'utf8'));
const styleXml = readFileSync(join(here, 'china-national-standard-gb-t-7714-2015-numeric.csl'), 'utf8');
const localeXml = readFileSync(join(here, 'locales-en-US.xml'), 'utf8');

const byId = new Map(cslJson.items.map((it) => [String(it.id), it]));

const sys = {
  retrieveLocale: () => localeXml,
  retrieveItem: (id) => byId.get(String(id)),
};

const engine = new CSL.Engine(sys, styleXml, 'en-US');
engine.setOutputFormat('html');
engine.updateItems(cslJson.items.map((it) => String(it.id)));
const [, entries] = engine.makeBibliography();

const unescapeHtml = (s) => s
  .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d)))
  .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
  .replace(/&quot;/g, '"').replace(/&nbsp;/g, ' ');

const BY_INDEX = cslJson.items;

/** 判断是否为中文条目：看作者与标题，不看渲染结果（渲染结果含样式的「版」字） */
const isChineseEntry = (item) => {
  const names = (item.author || []).map((a) => a.literal || a.family || '').join('');
  return /[\u3000-\u9fff]/.test(names + (item.title || ''));
};

/** 去掉 citeproc 的外层 div 与编号栏，只取正文（编号由顺序编码制自行给出）。 */
function bodyOf(html) {
  let s = unescapeHtml(html).trim();
  s = s.replace(/^\s*<div class="csl-entry">\s*/i, '').replace(/\s*<\/div>\s*$/i, '');
  const m = s.match(/<div class="csl-right-inline">([\s\S]*?)<\/div>/);
  if (m) s = m[1];
  s = s.replace(/<div class="csl-left-margin">[\s\S]*?<\/div>/g, '');
  s = s.replace(/<\/?div[^>]*>/g, '');
  return s.trim();
}

/** 纯文本化：保留斜体/上下标信息，供 DOCX 富文本使用。 */
function toPlain(html) {
  return unescapeHtml(html.replace(/<[^>]+>/g, ''))
    .replace(/\s+/g, ' ')
    .replace(/\s+([,.;:])/g, '$1')
    .trim();
}

const out = entries.map((html, i) => {
  let bodyHtml = bodyOf(html);
  let text = toPlain(bodyHtml);
  if (isChineseEntry(BY_INDEX[i])) {
    // 中文条目：西文 locale 的 et al. 回写为「等.」（GB/T 7714 要求）
    bodyHtml = bodyHtml.replace(/et al\./g, '等.');
    text = text.replace(/et al\./g, '等.');
  } else {
    // 西文条目：样式内置的「版」改为「ed.」（GB/T 7714 对西文文献的书写习惯）
    bodyHtml = bodyHtml.replace(/(\d+(?:st|nd|rd|th))\s*版\.?/g, '$1 ed.');
    text = text.replace(/(\d+(?:st|nd|rd|th))\s*版\.?/g, '$1 ed.');
  }
  return { n: i + 1, html: bodyHtml, text };
});

const payload = {
  engine: 'citeproc-js',
  styleTitle: 'China National Standard GB/T 7714-2015 (numeric)',
  styleSource: 'https://www.zotero.org/styles/china-national-standard-gb-t-7714-2015-numeric',
  styleFile: 'tools/china-national-standard-gb-t-7714-2015-numeric.csl',
  locale: 'en-US（中文条目 et al. -> 等.；西文条目「版」-> ed.）',
  csl: 'results/references_csl.json',
  note: '条目由 Zotero 库（results/references_authoritative.json）经 citeproc-js 渲染，格式与 Zotero 输出一致',
  entries: out,
};
writeFileSync(join(root, 'results/references_gbt7714.json'),
  JSON.stringify(payload, null, 2), 'utf8');

console.log(`rendered ${out.length} entries -> results/references_gbt7714.json\n`);
for (const e of out) console.log(`[${e.n}] ${e.text}\n`);
