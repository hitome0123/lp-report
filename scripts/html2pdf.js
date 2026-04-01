#!/usr/bin/env node
/**
 * HTML → PDF 像素级精确转换
 * 方案：逐个 .page div 截图 → 拼成 PDF
 * 保证和浏览器显示一模一样
 */
const puppeteer = require('puppeteer');
const path = require('path');

const URL = process.argv[2] || 'http://localhost:5010/report';
const OUT = process.argv[3] || path.join(__dirname, 'report.pdf');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: process.platform === 'darwin'
      ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
      : '/usr/bin/google-chrome-stable',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();

  // A4 at 2x for清晰度: 210mm=794px, 297mm=1123px
  const scale = 2;
  const pageW = 794;
  const pageH = 1123;
  await page.setViewport({ width: pageW, height: pageH, deviceScaleFactor: scale });

  await page.goto(URL, { waitUntil: 'networkidle0', timeout: 30000 });
  // 等 ECharts 渲染
  await new Promise(r => setTimeout(r, 3000));

  // 获取所有 .page 元素
  const pageCount = await page.$$eval('.page', els => els.length);
  console.log(`Found ${pageCount} pages`);

  // 逐页截图
  const screenshots = [];
  for (let i = 0; i < pageCount; i++) {
    const clip = await page.$eval(`.page:nth-child(${i + 1})`, el => {
      const r = el.getBoundingClientRect();
      return { x: r.x, y: r.y, width: r.width, height: r.height };
    });
    const buf = await page.screenshot({
      type: 'png',
      clip: { x: clip.x, y: clip.y, width: clip.width, height: clip.height },
      captureBeyondViewport: true,
    });
    screenshots.push(buf);
    console.log(`  Page ${i + 1}/${pageCount} captured`);
  }

  // 用 Puppeteer 生成空白 PDF，每页嵌入截图
  const pdfPage = await browser.newPage();
  // 构建一个临时 HTML，每张截图一页
  const imagesHtml = screenshots.map((buf, i) => {
    const b64 = buf.toString('base64');
    return `<div class="pdf-page"><img src="data:image/png;base64,${b64}" /></div>`;
  }).join('\n');

  const html = `<!DOCTYPE html>
<html><head><style>
  @page { size: 210mm 297mm; margin: 0; }
  * { margin: 0; padding: 0; }
  body { background: #fff; }
  .pdf-page { width: 210mm; height: 297mm; page-break-after: always; overflow: hidden; }
  .pdf-page:last-child { page-break-after: auto; }
  .pdf-page img { width: 210mm; height: 297mm; display: block; }
</style></head><body>${imagesHtml}</body></html>`;

  await pdfPage.setContent(html, { waitUntil: 'networkidle0' });
  await pdfPage.pdf({
    path: OUT,
    format: 'A4',
    printBackground: true,
    preferCSSPageSize: true,
    margin: { top: 0, bottom: 0, left: 0, right: 0 },
  });

  console.log(`PDF saved: ${OUT} (${pageCount} pages)`);
  await browser.close();
})();

