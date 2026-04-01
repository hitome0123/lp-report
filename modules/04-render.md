# Phase 4 — 图表渲染与PDF生成

## 目标
将报告文字 + 图表数据渲染为7页HTML报告，并转换为PDF。

## ECharts图表配置

### Chart 1: 美国AI加速器市场规模（2022-2026E）
- 类型: 柱状图 + 折线图（双轴）
- 柱形: 市场规模 $B — 颜色 #0096A9
- 折线: YoY增速 % — 颜色 #6ECEB2
- 数据: [6, 27, 49, 67, 84] / [null, 350%, 81%, 37%, 25%]
- 柱顶标金额（深蓝），折线标百分比（薄荷绿下方）

### Chart 2: Cerebras融资历程（2016-2026）
- 类型: 柱状图 + 折线图（双轴）
- 柱形: 融资金额 $M — 颜色 #0096A9
- 折线: 投后估值 $B — 颜色 #6ECEB2
- 数据: [27,25,62,84,272,250,1100,1000] / [null,null,null,1.7,2.4,4.0,8.1,23.0]

### 通用样式
- 图例: 底部居中，20×14色块，13px加粗黑字
- Y轴: 隐藏（数字在标签上）
- 网格线: 无
- Tooltip: 白底，悬停显示详情

## PDF生成方案

### 方案A: Puppeteer逐页截图（推荐）
```javascript
// 核心: viewport 794×1123 @ 2x → 逐个.page截图 → 拼成PDF
await page.setViewport({ width: 794, height: 1123, deviceScaleFactor: 2 });
// 每个 .page div 单独截图，保证不串页
```

### 方案B: reportlab代码绘制（备选）
- `scripts/generate_pdf.py` — 纯Python绘制PDF
- 优点: 不依赖浏览器
- 缺点: 样式和HTML不完全一致

## 输出
- `report/report.html` — 7页交互式报告
- `report/report.pdf` — 7页A4 PDF（210×297mm）

