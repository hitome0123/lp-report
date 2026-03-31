# ECharts PitchBook Theme — 完整配色+排版规范

## 配色板（从PitchBook 2025大中华区报告截图精确提取）

```javascript
const PB = {
  colors: {
    primary:    '#0096A9',  // 青蓝（主色，几乎所有主柱/主线）
    darkBlue:   '#003D6B',  // 深蓝（B2B/软件/深色堆叠层）
    mint:       '#6ECEB2',  // 薄荷绿（折线/浅色堆叠层）
    lightBlue:  '#B8D8E8',  // 浅蓝（次要堆叠层）
    yellowGreen:'#C4D600',  // 黄绿（能源/B2C）
    orange:     '#F47B20',  // 橙色（强调色）
    gold:       '#E8B84B',  // 金黄
    gray:       '#7C878E',  // 灰色（次要类别）
    lightCyan:  '#A5C8D0',  // 浅青（生物科技）
    tan:        '#D4A574',  // 浅棕（媒体）
    silver:     '#BCC5C9',  // 银灰（其他）
  },
  text:       '#333333',   // 正文色
  subText:    '#999999',   // 来源标注色
  gridLine:   '#E8E8E8',   // 网格线色
  bg:         '#FFFFFF',   // 白底
  fontFamily: "'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
};
```

## 堆叠柱状图配色序列（11色）

```javascript
const STACK_COLORS = [
  '#003D6B',  // 1. 深蓝
  '#0096A9',  // 2. 青蓝
  '#6ECEB2',  // 3. 薄荷绿
  '#B8D8E8',  // 4. 浅蓝
  '#C4D600',  // 5. 黄绿
  '#F47B20',  // 6. 橙色
  '#E8B84B',  // 7. 金黄
  '#7C878E',  // 8. 灰色
  '#A5C8D0',  // 9. 浅青
  '#D4A574',  // 10. 浅棕
  '#BCC5C9',  // 11. 银灰
];
```

## 通用轴样式

```javascript
// 有网格线的Y轴
const pbAxisStyle = {
  axisLine:  { show: false },
  axisTick:  { show: false },
  splitLine: { lineStyle: { color: '#E8E8E8', type: 'solid' } },
  axisLabel: { color: '#333', fontSize: 11, fontFamily: PB.fontFamily },
};

// 无网格线的轴（X轴、右Y轴）
const pbAxisStyleNoSplit = {
  ...pbAxisStyle,
  splitLine: { show: false },
};
```

## 图例配置

```javascript
// PitchBook图例始终在右侧竖排
const pbLegend = {
  orient: 'vertical',
  right: 0,
  top: 40,
  itemWidth: 12,
  itemHeight: 12,
  textStyle: { fontSize: 10, color: '#333', fontFamily: PB.fontFamily },
};
```

## 柱状图样式

```javascript
// 主色柱
{
  type: 'bar',
  barWidth: '50%',          // 柱宽占间距60-70%
  itemStyle: { color: '#0096A9' },  // 无圆角、无边框
  label: {
    show: true,
    position: 'top',        // 数据标签在柱顶上方
    formatter: (p) => '$' + p.value,
    fontSize: 10,
    color: '#333',
  },
}
```

## 折线样式

```javascript
// 薄荷绿折线
{
  type: 'line',
  lineStyle: { color: '#6ECEB2', width: 2.5 },
  itemStyle: { color: '#6ECEB2', borderWidth: 0 },
  symbolSize: 8,
  symbol: 'circle',         // 实心圆点标记
  label: {
    show: true,
    position: 'top',
    fontSize: 10,
    color: '#6ECEB2',
    fontWeight: 'bold',
  },
}
```

## 雷达图样式

```javascript
{
  radar: {
    shape: 'polygon',
    radius: '60%',
    center: ['40%', '55%'],  // 偏左，右侧留给图例
    axisName: { color: '#333', fontSize: 11 },
    splitArea: {
      areaStyle: { color: ['#fff', '#F7FAFB', '#fff', '#F7FAFB', '#fff'] }
    },
    splitLine: { lineStyle: { color: '#E8E8E8' } },
    axisLine:  { lineStyle: { color: '#E8E8E8' } },
  }
}
```

## Tooltip样式

```javascript
{
  tooltip: {
    trigger: 'axis',
    backgroundColor: '#fff',
    borderColor: '#E8E8E8',
    textStyle: { color: '#333', fontSize: 11, fontFamily: PB.fontFamily },
  }
}
```

## HTML表格CSS

```css
.pb-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}
.pb-table thead th {
  background: #0096A9;     /* 青蓝表头 */
  color: #fff;
  font-weight: 500;
  padding: 10px 12px;
}
.pb-table thead th:not(:first-child) {
  text-align: right;       /* 数字列右对齐 */
}
.pb-table tbody td {
  padding: 9px 12px;
  border-bottom: 1px solid #E8E8E8;
}
.pb-table tbody tr:nth-child(even) {
  background: #F7FAFB;    /* 隔行浅灰 */
}
/* Cerebras高亮行 */
.pb-table tbody tr.highlight {
  background: #EDF5F7 !important;
}
```

## 页面排版CSS

```css
.page {
  width: 210mm;            /* A4宽 */
  min-height: 297mm;       /* A4高 */
  padding: 48px 56px;      /* 充足内边距 */
  background: #fff;
  page-break-after: always;
}

.page-header {
  border-bottom: 3px solid #0096A9;  /* Logo下方青蓝线 */
  padding-bottom: 16px;
  margin-bottom: 36px;
}

.section-title-lg {
  font-size: 48px;
  font-weight: 900;
  color: #333;
}

.two-col {
  column-count: 2;
  column-gap: 32px;
  font-size: 11px;
  line-height: 1.8;
}

.chart-source {
  font-size: 9px;
  color: #999;
  text-align: right;
  /* 格式: 资料来源: PitchBook · 地域: xxx · 截至xxx */
}
```

## CDN依赖

```html
<!-- ECharts -->
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>

<!-- 中文字体 -->
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&display=swap" rel="stylesheet">
```
