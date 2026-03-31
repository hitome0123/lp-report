# 图表数据Schema

## Chart 1: 美国AI加速器芯片市场规模（2022-2026E）

```json
{
  "type": "bar+line",
  "x_axis": ["2022", "2023", "2024", "2025E", "2026E"],
  "bar_data": [6, 27, 49, 67, 84],
  "bar_unit": "$B",
  "bar_color": "#0096A9",
  "line_data": [null, 350, 81, 37, 25],
  "line_unit": "%",
  "line_color": "#6ECEB2",
  "source": "Bloomberg Intelligence, Silicon Analysts, NVIDIA财报交叉验证",
  "note": "口径: AI加速器(GPU/TPU/ASIC), 美国占全球~42%"
}
```

## Chart 2: Cerebras融资历程（2016-2026）

```json
{
  "type": "bar+line",
  "x_axis": ["A轮 2016", "B轮 2016", "C轮 2017", "D轮 2018", "E轮 2019", "F轮 2021", "G轮 2025", "H轮 2026"],
  "bar_data": [27, 25, 62, 84, 272, 250, 1100, 1000],
  "bar_unit": "$M",
  "bar_color": "#0096A9",
  "line_data": [null, null, null, 1.7, 2.4, 4.0, 8.1, 23.0],
  "line_unit": "$B",
  "line_color": "#6ECEB2",
  "source": "SEC S-1, Crunchbase, 各轮官方公告"
}
```

## 渲染规则

| 规则 | 说明 |
|------|------|
| 柱顶标签 | 柱顶上方，深蓝色(#003D6B)，大柱13px加粗 |
| 折线标签 | 数据点下方，薄荷绿(#6ECEB2)，白底药片 |
| 图例 | 底部居中，20×14色块，13px加粗黑字 |
| Y轴 | 隐藏（数字已在标签上） |
| 柱形 | 圆角顶部(3,3,0,0)，宽度45-52% |
| Tooltip | 白底，悬停触发，显示详细数值 |
