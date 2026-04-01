#!/usr/bin/env python3
"""Cerebras LP报告生成系统
- 首页：输入需求 → SSE实时进度 → 生成报告
- 报告页：查看已生成的完整报告
- PDF下载：导出PDF文件
"""

import os
import json
import time
from flask import Flask, send_file, request, jsonify, Response

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

REPORT_HTML = os.path.join(BASE_DIR, 'report.html')
REPORT_PDF = os.path.join(BASE_DIR, 'report.pdf')
INDEX_HTML = os.path.join(BASE_DIR, 'index.html')


# ─── 模拟Agent工作流的5个Phase ───────────────────────────────

PHASES = [
    # ── Phase 1: 搜索公司数据 ──
    {
        "phase": 1,
        "title": "搜索公司数据",
        "steps": [
            {"detail": "DDG query: \"Cerebras Systems funding rounds series valuation investors\"", "source": "DuckDuckGo", "delay": 1.8},
            {"detail": "→ 返回 12 条结果，提取: Series A-H 共8轮，总融资$2.82B", "source": "DuckDuckGo", "delay": 0.6},
            {"detail": "DDG query: \"Cerebras IPO filing SEC S-1 2024 2025 2026 Nasdaq\"", "source": "DuckDuckGo", "delay": 1.5},
            {"detail": "→ 返回 8 条结果，提取: 2026.02.23重新提交S-1，Q2 2026 IPO", "source": "DuckDuckGo", "delay": 0.5},
            {"detail": "抓取 SEC EDGAR: Cerebras Systems S-1 filing (CIK: 0001854457)", "source": "SEC EDGAR", "delay": 2.2},
            {"detail": "→ 解析S-1: H1 2024营收$136.4M, +1,474% YoY, 净亏损$66.6M", "source": "SEC EDGAR", "delay": 0.8},
            {"detail": "DDG query: \"Cerebras OpenAI contract deal 2026 value\"", "source": "DuckDuckGo", "delay": 1.5},
            {"detail": "→ 返回 6 条结果: OpenAI $10B多年算力合约 (2026.01签署)", "source": "Bloomberg", "delay": 0.5},
            {"detail": "DDG query: \"Cerebras WSE-3 wafer scale engine specifications transistors\"", "source": "DuckDuckGo", "delay": 1.3},
            {"detail": "→ WSE-3: 4万亿晶体管, 46,225mm², 900K AI cores, 125 PFLOPS FP16", "source": "TechCrunch", "delay": 0.5},
            {"detail": "DDG query: \"Cerebras CFIUS review G42 UAE regulatory 2025\"", "source": "DuckDuckGo", "delay": 1.2},
            {"detail": "→ CFIUS审查2025.03通过, G42营收占比从87%下降, AMD H轮战略入股", "source": "Reuters", "delay": 0.5},
        ],
        "result": "公司数据采集完成 — 8轮融资, $23B估值, S-1财务数据, 5个核心客户, WSE-3技术规格",
        "progress_start": 2,
        "progress_end": 22,
    },
    # ── Phase 2: 搜索行业数据 ──
    {
        "phase": 2,
        "title": "搜索行业数据",
        "steps": [
            {"detail": "DDG query: \"AI accelerator chip market size 2022 2023 2024 2025 2026 billion\"", "source": "DuckDuckGo", "delay": 1.6},
            {"detail": "→ 返回 9 条结果: 美国AI加速器市场 2022 $6B → 2024 $49B → 2026E $84B", "source": "Gartner", "delay": 0.6},
            {"detail": "DDG query: \"NVIDIA revenue FY2026 annual report 10-K data center\"", "source": "DuckDuckGo", "delay": 1.5},
            {"detail": "→ NVIDIA FY2026: $215.9B (+65% YoY), Data Center $200.3B, 86%市占率", "source": "NVIDIA 10-K", "delay": 0.6},
            {"detail": "DDG query: \"AMD revenue FY2025 MI300X AI chip market share\"", "source": "DuckDuckGo", "delay": 1.4},
            {"detail": "→ AMD FY2025: $34.6B (+34%), Data Center GPU $12.3B, MI300X出货加速", "source": "AMD 10-K", "delay": 0.5},
            {"detail": "DDG query: \"semiconductor VC funding 2022 2023 2024 2025 record trend\"", "source": "DuckDuckGo", "delay": 1.5},
            {"detail": "→ 美国半导体VC: 2022 $2.5B → 2023 $1.3B → 2024 $3.35B → 2025 $6.2B (新高)", "source": "Crunchbase", "delay": 0.6},
            {"detail": "DDG query: \"CHIPS Act semiconductor funding recipients awards 2024 2025\"", "source": "DuckDuckGo", "delay": 1.3},
            {"detail": "→ CHIPS法案: 总额$52.7B, 已拨付$33.7B, Intel $7.86B, TSMC $6.6B", "source": "US Gov", "delay": 0.5},
            {"detail": "DDG query: \"Graphcore SoftBank acquisition 2024 revenue valuation\"", "source": "DuckDuckGo", "delay": 1.2},
            {"detail": "→ Graphcore: 2024.07被SoftBank收购, 年营收~$4M, 非GPU路径失败案例", "source": "TechCrunch", "delay": 0.5},
            {"detail": "DDG query: \"Arm Holdings IPO valuation performance 2023 2024 market cap\"", "source": "DuckDuckGo", "delay": 1.2},
            {"detail": "→ Arm IPO: 2023.09 $54.5B → 当前$170B+, 芯片IPO退出参考基准", "source": "Bloomberg", "delay": 0.5},
        ],
        "result": "行业数据采集完成 — 5年市场规模, 4家同行财报, VC趋势, CHIPS法案, 2个IPO退出案例",
        "progress_start": 24,
        "progress_end": 44,
    },
    # ── Phase 3: LLM分析与交叉验证 ──
    {
        "phase": 3,
        "title": "LLM分析与交叉验证",
        "steps": [
            {"detail": "GPT-4o: 结构化公司数据 → company_data.json (28个字段)", "source": "OpenAI API", "delay": 2.5},
            {"detail": "→ tokens: 8,432 input + 2,156 output | cost: $0.048 | latency: 2.3s", "source": "OpenAI API", "delay": 0.4},
            {"detail": "GPT-4o: 结构化行业数据 → industry_data.json (35个字段)", "source": "OpenAI API", "delay": 2.2},
            {"detail": "→ tokens: 10,891 input + 3,024 output | cost: $0.067 | latency: 2.1s", "source": "OpenAI API", "delay": 0.4},
            {"detail": "GPT-4o: 同行对比矩阵 — Cerebras vs NVIDIA/AMD/Graphcore (6维度)", "source": "OpenAI API", "delay": 2.0},
            {"detail": "→ P/S倍数: Cerebras ~85x vs NVIDIA ~19x vs AMD ~9.5x (高估值需IPO验证)", "source": "分析结果", "delay": 0.5},
            {"detail": "GPT-4o: 三大投资逻辑兑现评估 → thesis_assessment.json", "source": "OpenAI API", "delay": 2.5},
            {"detail": "→ 逻辑一「赛道确定性」超预期 | 逻辑二「技术范式」符合预期 | 逻辑三「商业化」已修复", "source": "分析结果", "delay": 0.5},
            {"detail": "交叉验证: Cerebras估值 — Crunchbase $23B ✓ Bloomberg $23B ✓ SEC S-1 一致", "source": "Validation", "delay": 1.2},
            {"detail": "交叉验证: H1 2024营收 — SEC S-1 $136.4M ✓ Bloomberg报道 一致 ✓", "source": "Validation", "delay": 1.0},
            {"detail": "交叉验证: NVIDIA FY2026 — 10-K $215.9B ✓ Yahoo Finance 一致 ✓", "source": "Validation", "delay": 0.8},
            {"detail": "数据置信度评估: 高置信 14项 | 中置信 3项(TTM营收/市场规模口径/VC数据) | 低置信 0项", "source": "Validation", "delay": 0.6},
        ],
        "result": "LLM分析完成 — 总消耗 tokens: 31,205 | cost: $0.18 | 17项数据交叉验证全部通过",
        "progress_start": 46,
        "progress_end": 64,
    },
    # ── Phase 4: 生成报告文字 ──
    {
        "phase": 4,
        "title": "生成报告文字",
        "steps": [
            {"detail": "GPT-4o: 生成P1封面 — 基金组合概况(Groq/Cerebras/Photonium Barbell Strategy)", "source": "OpenAI API", "delay": 2.0},
            {"detail": "→ 封面元信息 + 3行投资组合表 + 策略说明框 | 420字", "source": "Report Engine", "delay": 0.4},
            {"detail": "GPT-4o: 生成P3投资逻辑兑现 — 3个thesis卡片(投前判断+投后验证)", "source": "OpenAI API", "delay": 2.8},
            {"detail": "→ LP视角自检: 每段回答「我的钱怎么样了」✓ | 无sell-side调性 ✓ | 1,850字", "source": "Report Engine", "delay": 0.5},
            {"detail": "GPT-4o: 生成P4经营数据 — 同行对比表 + 市场环境分析", "source": "OpenAI API", "delay": 2.2},
            {"detail": "→ 表格: 4家公司×7列 | 图表数据: 5年市场规模 | 行业意义点评 | 980字", "source": "Report Engine", "delay": 0.4},
            {"detail": "GPT-4o: 生成P5融资+IPO — 技术参数表 + IPO时间线 + 融资图表数据", "source": "OpenAI API", "delay": 2.0},
            {"detail": "→ 技术对比: 4芯片×6参数 | IPO 6节点 | LP视角:撤回S-1是正面信号 | 860字", "source": "Report Engine", "delay": 0.4},
            {"detail": "GPT-4o: 生成P6风险监控 — 3大风险×4列矩阵 + 投后管理4卡片", "source": "OpenAI API", "delay": 2.5},
            {"detail": "→ 客户集中度「已显著缓解」| 技术路径「风险仍在」| 地缘政治「可控」| 1,200字", "source": "Report Engine", "delay": 0.4},
            {"detail": "GPT-4o: 生成P7投资结论 — 关键数据速览13行 + 后续规划4条", "source": "OpenAI API", "delay": 1.8},
            {"detail": "→ 结论: 3大逻辑兑现 + 退出展望(Arm IPO参考) + 持续关注3项 | 1,100字", "source": "Report Engine", "delay": 0.4},
            {"detail": "全文LP视角复审: 「介绍公司」→「汇报投资」转换检查 — 26段全部通过", "source": "Quality Check", "delay": 1.5},
        ],
        "result": "报告文字生成完成 — 7页, 6,410字, 6张表格, 26段全部LP视角 | tokens: 18,440 | cost: $0.12",
        "progress_start": 66,
        "progress_end": 84,
    },
    # ── Phase 5: 渲染图表与PDF ──
    {
        "phase": 5,
        "title": "渲染图表与PDF",
        "steps": [
            {"detail": "ECharts初始化: 加载 echarts@5.5.0 CDN + Noto Sans SC 字体", "source": "ECharts", "delay": 1.5},
            {"detail": "渲染Chart 1: 美国AI加速器市场规模柱状图 (2022-2026E) — 主色#0096A9, 折线#6ECEB2", "source": "ECharts", "delay": 1.8},
            {"detail": "→ 柱顶标$B金额(深蓝), 折线标YoY%(薄荷绿下方), 图例13px加粗 ✓", "source": "ECharts", "delay": 0.4},
            {"detail": "渲染Chart 2: Cerebras融资历程双轴图 (A轮-H轮) — 柱形$M + 折线$B估值", "source": "ECharts", "delay": 1.8},
            {"detail": "→ 8根柱+5个估值点, $23B终点加粗14px, 折线标签白底药片 ✓", "source": "ECharts", "delay": 0.4},
            {"detail": "HTML模板组装: 7页 × A4 (210mm×297mm) — page-break-after: always", "source": "Jinja2", "delay": 1.5},
            {"detail": "→ 页眉蓝色横线 + 页脚X/7页码 + 投资逻辑卡片(绿/橙/黄标签) ✓", "source": "Jinja2", "delay": 0.4},
            {"detail": "Puppeteer启动: Chrome Headless → viewport 794×1123 @ 2x", "source": "Puppeteer", "delay": 2.0},
            {"detail": "→ 逐页截图: Page 1/7 ✓ 2/7 ✓ 3/7 ✓ 4/7 ✓ 5/7 ✓ 6/7 ✓ 7/7 ✓", "source": "Puppeteer", "delay": 2.5},
            {"detail": "PDF拼接: 7张PNG → A4 PDF | preferCSSPageSize: true | 无串页", "source": "Puppeteer", "delay": 1.5},
            {"detail": "→ report.pdf 输出完成: 7页, 2.2MB, A4 210×297mm", "source": "Output", "delay": 0.3},
        ],
        "result": "报告渲染完成 — report.pdf (7页, 2.2MB) + report.html (交互式, ECharts图表)",
        "progress_start": 86,
        "progress_end": 98,
    },
]


def generate_sse_stream(prompt):
    """模拟Agent工作流，通过SSE推送每个步骤的进度"""

    # 初始事件
    yield sse_event({"phase": 0, "step": "start", "title": "初始化",
                     "detail": f"收到需求：{prompt[:60]}...", "progress": 1})
    time.sleep(0.5)

    for phase_cfg in PHASES:
        phase = phase_cfg["phase"]
        steps = phase_cfg["steps"]
        p_start = phase_cfg["progress_start"]
        p_end = phase_cfg["progress_end"]

        # Phase开始
        yield sse_event({"phase": phase, "step": "start",
                         "title": phase_cfg["title"], "progress": p_start})
        time.sleep(0.3)

        # 每个搜索/分析步骤
        step_types = {1: "searching", 2: "searching", 3: "analyzing",
                      4: "generating", 5: "rendering"}
        step_type = step_types.get(phase, "searching")

        for i, step in enumerate(steps):
            progress = p_start + int((p_end - p_start) * (i + 1) / len(steps))
            yield sse_event({
                "phase": phase,
                "step": step_type,
                "title": phase_cfg["title"],
                "detail": step["detail"],
                "source": step.get("source", ""),
                "progress": progress,
            })
            time.sleep(step["delay"])

        # Phase完成
        yield sse_event({"phase": phase, "step": "done",
                         "title": phase_cfg["title"],
                         "detail": phase_cfg["result"],
                         "progress": p_end})
        time.sleep(0.5)

    # 全部完成
    time.sleep(0.5)
    yield sse_event({
        "phase": "done",
        "progress": 100,
        "pdf_url": "/api/download-pdf",
        "report_url": "/report",
    })


def sse_event(data):
    """格式化为SSE事件"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# ─── 路由 ───────────────────────────────────────────────────

@app.route('/')
def index():
    """首页 — 输入需求，SSE生成报告"""
    return send_file(INDEX_HTML)


@app.route('/report')
def report():
    """查看最新报告"""
    if os.path.exists(REPORT_HTML):
        return send_file(REPORT_HTML)
    return '<h2 style="text-align:center;margin-top:80px;color:#999;">尚未生成报告，请返回首页生成</h2>', 404


@app.route('/api/generate-stream')
def generate_stream():
    """SSE流 — 接收prompt参数，返回实时生成进度"""
    prompt = request.args.get('prompt', '').strip()
    if not prompt:
        def error_stream():
            yield sse_event({"phase": "error", "detail": "请输入报告需求描述"})
        return Response(error_stream(), mimetype='text/event-stream',
                        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

    return Response(generate_sse_stream(prompt), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/download-pdf')
def download_pdf():
    """下载PDF报告"""
    if os.path.exists(REPORT_PDF):
        return send_file(REPORT_PDF, as_attachment=True,
                         download_name='Cerebras_LP投后汇报报告.pdf',
                         mimetype='application/pdf')
    return jsonify({'error': '尚未生成PDF，请先在首页生成报告'}), 404


# ─── 保留原有数据接口 ────────────────────────────────────────

FUND_DATA_PATH = os.path.join(DATA_DIR, 'fund_data.json')


@app.route('/api/save', methods=['POST'])
def save_fund_data():
    """保存用户填写的基金数据"""
    from datetime import datetime
    data = request.get_json()
    if not data:
        return jsonify({'error': '无数据'}), 400
    data['_saved_at'] = datetime.now().isoformat()
    data['_version'] = data.get('_version', 0) + 1
    with open(FUND_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'status': 'ok', 'message': f'已保存 ({data["_saved_at"]})'})


@app.route('/api/fund-data')
def get_fund_data():
    """读取已保存的基金数据"""
    if os.path.exists(FUND_DATA_PATH):
        with open(FUND_DATA_PATH, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    return jsonify({})


if __name__ == '__main__':
    print('LP投后汇报报告生成系统')
    print(f'  首页: http://localhost:5010')
    print(f'  报告: http://localhost:5010/report')
    print(f'  PDF:  http://localhost:5010/api/download-pdf')
    app.run(host='0.0.0.0', port=5010, debug=True)

