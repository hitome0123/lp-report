#!/usr/bin/env python3
"""
LP投后汇报报告 - Cerebras System
生成7页A4 PDF报告（reportlab + matplotlib）
"""

import os
import tempfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
pdfmetrics.registerFont(TTFont('Songti', '/System/Library/Fonts/Supplemental/Songti.ttc', subfontIndex=0))
# Use STHeiti for bold-ish Chinese
pdfmetrics.registerFont(TTFont('STHeiti', '/System/Library/Fonts/STHeiti Medium.ttc', subfontIndex=0))

FONT_CN = 'Songti'
FONT_CN_BOLD = 'STHeiti'
FONT_EN = 'Helvetica'
FONT_EN_BOLD = 'Helvetica-Bold'

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
C_PRIMARY = HexColor('#0096A9')
C_DARK = HexColor('#003D6B')
C_MINT = HexColor('#6ECEB2')
C_HIGHLIGHT_BG = HexColor('#F0F9FA')
C_ROW_ALT = HexColor('#F7FAFB')
C_WHITE = white
C_BLACK = black
C_GREEN = HexColor('#2E7D32')
C_ORANGE = HexColor('#E65100')
C_YELLOW = HexColor('#F9A825')
C_LIGHT_BLUE_BG = HexColor('#E0F4F7')

W, H = A4  # 595.27, 841.89
MARGIN_L = 45
MARGIN_R = 45
MARGIN_T = 60
MARGIN_B = 50
CONTENT_W = W - MARGIN_L - MARGIN_R

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
def make_style(name, fontName=FONT_CN, fontSize=10, leading=14, textColor=C_BLACK,
               alignment=TA_LEFT, spaceAfter=0, spaceBefore=0, firstLineIndent=0,
               leftIndent=0, rightIndent=0):
    return ParagraphStyle(
        name=name, fontName=fontName, fontSize=fontSize, leading=leading,
        textColor=textColor, alignment=alignment, spaceAfter=spaceAfter,
        spaceBefore=spaceBefore, firstLineIndent=firstLineIndent,
        leftIndent=leftIndent, rightIndent=rightIndent,
        wordWrap='CJK',
    )

S_TITLE_BIG = make_style('TitleBig', FONT_CN_BOLD, 22, 30, C_DARK, TA_LEFT)
S_SUBTITLE = make_style('Subtitle', FONT_CN, 11, 16, HexColor('#555555'), TA_LEFT)
S_META = make_style('Meta', FONT_CN, 8, 12, HexColor('#888888'), TA_LEFT)
S_SECTION_TITLE = make_style('SectionTitle', FONT_CN_BOLD, 15, 22, C_DARK, TA_LEFT, spaceAfter=6)
S_SUBSECTION = make_style('Subsection', FONT_CN_BOLD, 11, 16, C_DARK, TA_LEFT, spaceAfter=4, spaceBefore=6)
S_BODY = make_style('Body', FONT_CN, 9, 14, C_BLACK, TA_LEFT)
S_BODY_SMALL = make_style('BodySmall', FONT_CN, 8, 12, C_BLACK, TA_LEFT)
S_BODY_TINY = make_style('BodyTiny', FONT_CN, 7.5, 11, C_BLACK, TA_LEFT)
S_TABLE_HEADER = make_style('TH', FONT_CN_BOLD, 8, 11, C_WHITE, TA_CENTER)
S_TABLE_CELL = make_style('TC', FONT_CN, 7.5, 10.5, C_BLACK, TA_CENTER)
S_TABLE_CELL_L = make_style('TCL', FONT_CN, 7.5, 10.5, C_BLACK, TA_LEFT)
S_TOC_ITEM = make_style('TOC', FONT_CN, 11, 20, C_BLACK, TA_LEFT, leftIndent=20)
S_PAGE_TITLE = make_style('PageTitle', FONT_CN_BOLD, 9, 12, HexColor('#666666'), TA_LEFT)
S_FOOTER = make_style('Footer', FONT_CN, 7, 10, HexColor('#999999'), TA_CENTER)
S_HIGHLIGHT_TEXT = make_style('HLText', FONT_CN, 8.5, 13, C_BLACK, TA_LEFT, leftIndent=10)
S_CARD_TITLE = make_style('CardTitle', FONT_CN_BOLD, 9, 13, C_DARK, TA_LEFT)
S_CARD_BODY = make_style('CardBody', FONT_CN, 7.5, 11, C_BLACK, TA_LEFT)

# ---------------------------------------------------------------------------
# Custom Flowables
# ---------------------------------------------------------------------------
class ColorBar(Flowable):
    """Horizontal colored bar."""
    def __init__(self, width, height, color):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.color = color

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)


class HighlightBox(Flowable):
    """Box with left blue border and light bg."""
    def __init__(self, content_paragraphs, width, border_color=C_PRIMARY,
                 bg_color=C_HIGHLIGHT_BG, padding=8, border_width=3):
        Flowable.__init__(self)
        self.content_paragraphs = content_paragraphs
        self.box_width = width
        self.border_color = border_color
        self.bg_color = bg_color
        self.padding = padding
        self.border_width = border_width
        # Calculate height
        self._calc_height()

    def _calc_height(self):
        total = self.padding * 2
        for p in self.content_paragraphs:
            pw, ph = p.wrap(self.box_width - self.padding * 2 - self.border_width - 4, 1000)
            total += ph + 2
        self.height = total

    def wrap(self, availWidth, availHeight):
        self._calc_height()
        return (self.box_width, self.height)

    def draw(self):
        c = self.canv
        # Background
        c.setFillColor(self.bg_color)
        c.rect(0, 0, self.box_width, self.height, fill=1, stroke=0)
        # Left border
        c.setFillColor(self.border_color)
        c.rect(0, 0, self.border_width, self.height, fill=1, stroke=0)
        # Content
        y = self.height - self.padding
        for p in self.content_paragraphs:
            pw, ph = p.wrap(self.box_width - self.padding * 2 - self.border_width - 4, 1000)
            p.drawOn(c, self.border_width + self.padding, y - ph)
            y -= ph + 2


class ThesisCard(Flowable):
    """A bordered card for investment thesis."""
    def __init__(self, title, tag_text, tag_color, lines, width, card_height=None):
        Flowable.__init__(self)
        self.title = title
        self.tag_text = tag_text
        self.tag_color = tag_color
        self.lines = lines
        self.box_width = width
        self.card_height = card_height
        self._calc_height()

    def _calc_height(self):
        if self.card_height:
            self.height = self.card_height
            return
        h = 10  # top padding
        h += 14  # title line
        for line in self.lines:
            p = Paragraph(line, S_CARD_BODY)
            pw, ph = p.wrap(self.box_width - 20, 1000)
            h += ph + 1
        h += 8  # bottom padding
        self.height = max(h, 60)

    def wrap(self, availWidth, availHeight):
        return (self.box_width, self.height)

    def draw(self):
        c = self.canv
        # Border
        c.setStrokeColor(HexColor('#DDDDDD'))
        c.setLineWidth(0.5)
        c.roundRect(0, 0, self.box_width, self.height, 3, fill=0, stroke=1)
        # Top color bar
        c.setFillColor(self.tag_color)
        c.rect(0, self.height - 3, self.box_width, 3, fill=1, stroke=0)
        # Title + tag
        y = self.height - 16
        c.setFont(FONT_CN_BOLD, 8.5)
        c.setFillColor(C_DARK)
        c.drawString(8, y, self.title)
        # Tag
        tag_w = len(self.tag_text) * 9 + 12
        c.setFillColor(self.tag_color)
        c.roundRect(self.box_width - tag_w - 8, y - 2, tag_w, 14, 2, fill=1, stroke=0)
        c.setFillColor(C_WHITE)
        c.setFont(FONT_CN_BOLD, 7)
        c.drawCentredString(self.box_width - tag_w / 2 - 8, y + 1, self.tag_text)
        # Body lines
        y -= 16
        for line in self.lines:
            p = Paragraph(line, S_CARD_BODY)
            pw, ph = p.wrap(self.box_width - 20, 1000)
            if y - ph < 4:
                break
            p.drawOn(c, 10, y - ph)
            y -= ph + 1


class InfoBlock(Flowable):
    """A small info block for 2x2 grid."""
    def __init__(self, title, body_lines, width, height):
        Flowable.__init__(self)
        self.title = title
        self.body_lines = body_lines
        self.block_width = width
        self.height = height

    def wrap(self, availWidth, availHeight):
        return (self.block_width, self.height)

    def draw(self):
        c = self.canv
        c.setFillColor(C_HIGHLIGHT_BG)
        c.roundRect(0, 0, self.block_width, self.height, 3, fill=1, stroke=0)
        c.setFillColor(C_PRIMARY)
        c.rect(0, 0, 3, self.height, fill=1, stroke=0)
        y = self.height - 14
        c.setFont(FONT_CN_BOLD, 8.5)
        c.setFillColor(C_DARK)
        c.drawString(10, y, self.title)
        y -= 14
        for line in self.body_lines:
            p = Paragraph(line, make_style('ib', FONT_CN, 7, 10, C_BLACK, TA_LEFT))
            pw, ph = p.wrap(self.block_width - 20, 1000)
            if y - ph < 2:
                break
            p.drawOn(c, 10, y - ph)
            y -= ph + 1


# ---------------------------------------------------------------------------
# Chart Generation (matplotlib)
# ---------------------------------------------------------------------------
def make_market_chart(tmp_dir):
    """P4: US AI Accelerator Market bar chart."""
    fig, ax = plt.subplots(figsize=(6.5, 2.8))
    years = ['2022', '2023', '2024', '2025E', '2026E']
    values = [6, 27, 49, 67, 84]
    bars = ax.bar(years, values, color='#0096A9', width=0.55, edgecolor='none')
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                f'${val}B', ha='center', va='bottom', fontsize=10, fontweight='bold', color='#003D6B')
    ax.set_ylabel('Market Size ($B)', fontsize=9, color='#555555')
    ax.set_title('US AI Accelerator Chip Market', fontsize=11, fontweight='bold',
                 color='#003D6B', pad=10)
    ax.set_ylim(0, 100)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#CCCCCC')
    ax.spines['bottom'].set_color('#CCCCCC')
    ax.tick_params(colors='#555555', labelsize=9)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'${int(x)}B'))
    plt.tight_layout()
    path = os.path.join(tmp_dir, 'market_chart.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return path


def make_funding_chart(tmp_dir):
    """P5: Funding history bar+line chart."""
    fig, ax1 = plt.subplots(figsize=(6.5, 3.0))
    rounds = ['A\n2016', 'B\n2016', 'C\n2017', 'D\n2018', 'E\n2019', 'F\n2021', 'G\n2025', 'H\n2026']
    amounts = [27, 25, 62, 84, 272, 250, 1100, 1000]
    x = np.arange(len(rounds))
    bars = ax1.bar(x, amounts, color='#0096A9', width=0.5, edgecolor='none', label='Funding ($M)')
    for bar, val in zip(bars, amounts):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 15,
                 f'${val}M', ha='center', va='bottom', fontsize=7, color='#003D6B', fontweight='bold')
    ax1.set_ylabel('Funding Amount ($M)', fontsize=8, color='#555555')
    ax1.set_ylim(0, 1350)
    ax1.set_xticks(x)
    ax1.set_xticklabels(rounds, fontsize=7)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_color('#CCCCCC')
    ax1.spines['bottom'].set_color('#CCCCCC')
    ax1.tick_params(colors='#555555', labelsize=8)

    # Valuation line (from D round)
    ax2 = ax1.twinx()
    val_x = [3, 4, 5, 6, 7]
    val_y = [1.7, 2.4, 4.0, 8.1, 23.0]
    ax2.plot(val_x, val_y, color='#6ECEB2', marker='o', linewidth=2.5, markersize=6, label='Valuation ($B)')
    for xi, yi in zip(val_x, val_y):
        ax2.annotate(f'${yi}B', (xi, yi), textcoords='offset points', xytext=(0, 10),
                     ha='center', fontsize=7, color='#2E7D32', fontweight='bold')
    ax2.set_ylabel('Valuation ($B)', fontsize=8, color='#6ECEB2')
    ax2.set_ylim(0, 30)
    ax2.spines['top'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    ax2.spines['right'].set_color('#6ECEB2')
    ax2.tick_params(axis='y', colors='#6ECEB2', labelsize=8)

    ax1.set_title('Cerebras Systems Funding History', fontsize=11, fontweight='bold',
                  color='#003D6B', pad=10)
    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=7, framealpha=0.8)
    plt.tight_layout()
    path = os.path.join(tmp_dir, 'funding_chart.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Table helper
# ---------------------------------------------------------------------------
def make_table(headers, rows, col_widths, highlight_row=None):
    """Create a styled table."""
    header_paras = [Paragraph(h, S_TABLE_HEADER) for h in headers]
    data = [header_paras]
    for i, row in enumerate(rows):
        style = S_TABLE_CELL_L if len(row) > 0 else S_TABLE_CELL
        data.append([Paragraph(str(c), S_TABLE_CELL) for c in row])

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), C_WHITE),
        ('FONTNAME', (0, 0), (-1, 0), FONT_CN_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.4, HexColor('#DDDDDD')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]
    # Alternate row colors
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), C_ROW_ALT))
    # Highlight specific row
    if highlight_row is not None:
        style_cmds.append(('BACKGROUND', (0, highlight_row), (-1, highlight_row), C_LIGHT_BLUE_BG))
    t.setStyle(TableStyle(style_cmds))
    return t


# ---------------------------------------------------------------------------
# Page Template (header/footer)
# ---------------------------------------------------------------------------
page_num = [0]

def page_template(canvas, doc):
    page_num[0] += 1
    pn = page_num[0]
    canvas.saveState()
    # Header line
    canvas.setStrokeColor(C_PRIMARY)
    canvas.setLineWidth(0.6)
    canvas.line(MARGIN_L, H - 38, W - MARGIN_R, H - 38)
    canvas.setFont(FONT_CN, 7)
    canvas.setFillColor(HexColor('#888888'))
    canvas.drawString(MARGIN_L, H - 34, 'LP投后汇报报告-芯片行业：Cerebras System（2026.03）')
    # Footer
    canvas.setFont(FONT_CN, 7)
    canvas.setFillColor(HexColor('#999999'))
    canvas.drawCentredString(W / 2, 28, f'{pn}/7')
    canvas.drawRightString(W - MARGIN_R, 28, '仅供基金LP内部参考')
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Build Pages
# ---------------------------------------------------------------------------
def build_pdf():
    tmp_dir = tempfile.mkdtemp()
    market_chart_path = make_market_chart(tmp_dir)
    funding_chart_path = make_funding_chart(tmp_dir)

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'report.pdf')
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=MARGIN_L, rightMargin=MARGIN_R,
        topMargin=MARGIN_T, bottomMargin=MARGIN_B,
    )

    story = []

    # =====================================================================
    # PAGE 1: Cover + Portfolio Table
    # =====================================================================
    story.append(ColorBar(CONTENT_W, 4 * mm, C_PRIMARY))
    story.append(Spacer(1, 20))
    story.append(Paragraph('LP投后汇报报告', S_TITLE_BIG))
    story.append(Paragraph('芯片行业：Cerebras System', make_style('t2', FONT_CN_BOLD, 20, 28, C_DARK)))
    story.append(Spacer(1, 8))
    story.append(Paragraph('Compute-centric Picks & Shovels · AI算力赛道投后管理',
                           make_style('sub', FONT_CN, 11, 16, HexColor('#666666'))))
    story.append(Spacer(1, 16))

    meta_lines = [
        '报告日期：2026年3月  |  投资策略：AI Infra Picks & Shovels（算力基建）',
        '数据来源：公司财务/公开市场/行业研究  |  密级：基金LP内部',
    ]
    for m in meta_lines:
        story.append(Paragraph(m, S_META))
    story.append(Spacer(1, 20))

    # Portfolio table
    story.append(Paragraph('基金芯片赛道投资组合一览', make_style('pt', FONT_CN_BOLD, 12, 18, C_DARK, spaceAfter=6)))
    portfolio_headers = ['公司', '赛道定位', '投资逻辑', '当前状态']
    portfolio_rows = [
        ['Groq', 'AI推理芯片（LPU）', '已商业化，推理需求爆发', '运营中'],
        ['Cerebras Systems', 'AI训练+推理芯片（WSE）', '训练侧+有收入+有风险', '预计Q2 2026 IPO'],
        ['Photonium', '光子计算芯片', '下一代范式（高风险高回报）', '早期研发'],
    ]
    cw = [CONTENT_W * 0.18, CONTENT_W * 0.25, CONTENT_W * 0.32, CONTENT_W * 0.25]
    t = make_table(portfolio_headers, portfolio_rows, cw, highlight_row=2)
    story.append(t)
    story.append(Spacer(1, 16))

    # Strategy box
    strategy_paras = [
        Paragraph('<b>组合策略说明（Barbell Strategy）</b>',
                  make_style('sb', FONT_CN_BOLD, 9, 13, C_DARK)),
        Paragraph('采用哑铃策略：一端配置已验证的商业化公司（Groq），一端配置前沿范式（Photonium），'
                  '中间核心仓位押注技术领先+可商业化的Cerebras Systems。',
                  make_style('sb2', FONT_CN, 8.5, 13, C_BLACK)),
        Paragraph('三家公司覆盖训练+推理+下一代计算的完整AI芯片赛道，形成风险对冲组合。',
                  make_style('sb3', FONT_CN, 8.5, 13, C_BLACK)),
    ]
    story.append(HighlightBox(strategy_paras, CONTENT_W))

    story.append(PageBreak())

    # =====================================================================
    # PAGE 2: Table of Contents
    # =====================================================================
    story.append(Spacer(1, 30))
    story.append(Paragraph('目录', make_style('toc_title', FONT_CN_BOLD, 22, 30, C_DARK, TA_LEFT, spaceAfter=20)))
    story.append(ColorBar(CONTENT_W, 1.5, C_PRIMARY))
    story.append(Spacer(1, 20))

    toc_items = [
        ('基金芯片赛道投资组合一览', '1'),
        ('一、投资概况与投资逻辑兑现', '3'),
        ('二、核心经营数据与行业环境', '4'),
        ('三、融资历程与IPO进展', '5'),
        ('四、风险监控与投后管理', '6'),
        ('五、投资结论与关键数据速览', '7'),
    ]
    for title, page in toc_items:
        dots = '·' * (60 - len(title))
        story.append(Paragraph(f'{title} {dots} {page}', S_TOC_ITEM))

    story.append(PageBreak())

    # =====================================================================
    # PAGE 3: Investment Overview & Thesis Tracking
    # =====================================================================
    story.append(Paragraph('一、投资概况与投资逻辑兑现', S_SECTION_TITLE))
    story.append(ColorBar(CONTENT_W, 1.5, C_PRIMARY))
    story.append(Spacer(1, 8))

    overview_paras = [
        Paragraph('<b>投资概况</b>', make_style('ov1', FONT_CN_BOLD, 9, 13, C_DARK)),
        Paragraph('投资时间：2023年底/2024年初  |  轮次：Pre-IPO late stage  |  最新估值：$23B',
                  make_style('ov2', FONT_CN, 8.5, 12, C_BLACK)),
        Paragraph('Cerebras Systems是全球唯一量产wafer-scale芯片的公司，WSE-3单芯片集成4万亿晶体管，'
                  '在大模型训练效率上相比NVIDIA GPU集群具有架构级优势。',
                  make_style('ov3', FONT_CN, 8.5, 12, C_BLACK)),
    ]
    story.append(HighlightBox(overview_paras, CONTENT_W))
    story.append(Spacer(1, 8))

    story.append(Paragraph('三大投资逻辑兑现追踪', S_SUBSECTION))
    story.append(Spacer(1, 4))

    card_w = CONTENT_W
    card_h = 95

    # Thesis 1
    t1_lines = [
        '<b>投前判断：</b>AI基础设施（算力/芯片/数据中心）确定性远高于应用层，是"卖水人"逻辑。',
        '<b>投后验证：</b>2024年全球AI芯片市场达$490亿（+86%），NVIDIA数据中心收入$115B（+142%）。'
        'AI Infra投资逻辑完全兑现，且超过投前预期。',
    ]
    story.append(ThesisCard('逻辑一：赛道确定性（AI Infra > 应用层）', '超预期', C_GREEN, t1_lines, card_w, card_h))
    story.append(Spacer(1, 5))

    # Thesis 2
    t2_lines = [
        '<b>投前判断：</b>Wafer-scale是GPU之外的范式级技术路径，具备颠覆潜力。',
        '<b>投后验证：</b>WSE-3性能领先，但市场仍由NVIDIA主导（80%+ 份额）。'
        'Cerebras在推理市场找到差异化切入点，技术优势在逐步转化为商业优势。',
    ]
    story.append(ThesisCard('逻辑二：技术范式级机会（非GPU路径）', '符合预期', C_ORANGE, t2_lines, card_w, card_h))
    story.append(Spacer(1, 5))

    # Thesis 3
    t3_lines = [
        '<b>投前判断：</b>公司有收入、有客户、技术可量产，具备IPO退出路径。',
        '<b>投后验证：</b>H1 2024收入$136.4M（+1474%），但客户集中度高（G42占83%）。'
        '2025年新增多家客户，集中度问题正在修复。预计Q2 2026 IPO。',
    ]
    story.append(ThesisCard('逻辑三：可商业化+可存活', '已修复', C_YELLOW, t3_lines, card_w, card_h))
    story.append(Spacer(1, 8))

    # Highlight box
    bright_paras = [
        Paragraph('<b>超预期亮点</b>', make_style('bp1', FONT_CN_BOLD, 9, 13, C_DARK)),
        Paragraph('· Cerebras推理速度达到NVIDIA方案的20倍以上（Llama 3.1 70B: 2,100 tokens/s vs ~100 tokens/s）',
                  make_style('bp2', FONT_CN, 8, 12, C_BLACK)),
        Paragraph('· 推理市场为公司打开了第二增长曲线，不再仅依赖训练侧收入',
                  make_style('bp3', FONT_CN, 8, 12, C_BLACK)),
    ]
    story.append(HighlightBox(bright_paras, CONTENT_W))

    story.append(PageBreak())

    # =====================================================================
    # PAGE 4: Core Business Data & Industry
    # =====================================================================
    story.append(Paragraph('二、核心经营数据与行业环境', S_SECTION_TITLE))
    story.append(ColorBar(CONTENT_W, 1.5, C_PRIMARY))
    story.append(Spacer(1, 6))

    biz_paras = [
        Paragraph('<b>经营验证</b>', make_style('bz1', FONT_CN_BOLD, 9, 13, C_DARK)),
        Paragraph('H1 2024收入$136.4M（同比+1474%），全年预估约$272M。'
                  '净亏损$66.6M（收窄），现金储备充裕。',
                  make_style('bz2', FONT_CN, 8.5, 12, C_BLACK)),
    ]
    story.append(HighlightBox(biz_paras, CONTENT_W))
    story.append(Spacer(1, 8))

    story.append(Paragraph('AI芯片核心企业对比', S_SUBSECTION))
    comp_headers = ['公司', '市值/估值', '最新年收入', '收入增速', 'P/S', '退出状态']
    comp_rows = [
        ['NVIDIA', '$2.8T', '$130.5B', '+114%', '~21x', '已上市'],
        ['AMD', '$197B', '$25.8B', '+14%', '~8x', '已上市'],
        ['Cerebras', '$23B (估值)', '~$272M (预估)', '+1474%', '~85x', '预计Q2 IPO'],
        ['Graphcore', '被ARM收购', '<$10M', 'N/A', 'N/A', '已退出'],
    ]
    cw2 = [CONTENT_W * 0.14, CONTENT_W * 0.17, CONTENT_W * 0.19, CONTENT_W * 0.14, CONTENT_W * 0.12, CONTENT_W * 0.24]
    story.append(make_table(comp_headers, comp_rows, cw2, highlight_row=3))
    story.append(Spacer(1, 10))

    # Market chart
    story.append(Paragraph('美国AI加速器芯片市场规模', S_SUBSECTION))
    story.append(Image(market_chart_path, width=CONTENT_W, height=180))
    story.append(Spacer(1, 8))

    meaning_paras = [
        Paragraph('<b>对本笔投资的意义</b>', make_style('mn1', FONT_CN_BOLD, 9, 13, C_DARK)),
        Paragraph('AI芯片市场从2022年$6B增长到2026E $84B（CAGR 93%），市场空间足够大。'
                  'Cerebras即使只拿到1%份额，也意味着$840M收入，支撑$23B估值合理性。',
                  make_style('mn2', FONT_CN, 8.5, 12, C_BLACK)),
    ]
    story.append(HighlightBox(meaning_paras, CONTENT_W))

    story.append(PageBreak())

    # =====================================================================
    # PAGE 5: Funding & IPO
    # =====================================================================
    story.append(Paragraph('三、融资历程与IPO进展', S_SECTION_TITLE))
    story.append(ColorBar(CONTENT_W, 1.5, C_PRIMARY))
    story.append(Spacer(1, 6))

    # Funding chart
    story.append(Image(funding_chart_path, width=CONTENT_W, height=190))
    story.append(Spacer(1, 6))

    # IPO Timeline
    story.append(Paragraph('IPO进程关键节点', S_SUBSECTION))
    ipo_headers = ['时间', '事件', '状态']
    ipo_rows = [
        ['2024.08', '秘密提交S-1招股书', '已完成'],
        ['2024.11', '公开S-1文件，披露财务数据', '已完成'],
        ['2025.01', 'SEC审核反馈，修订文件', '已完成'],
        ['2025.06', '完成G轮$1.1B融资（估值$8.1B）', '已完成'],
        ['2026.02', 'H轮$1B融资（估值$23B），IPO前最后一轮', '已完成'],
        ['Q2 2026', '预计NYSE/NASDAQ上市', '进行中'],
    ]
    cw3 = [CONTENT_W * 0.15, CONTENT_W * 0.55, CONTENT_W * 0.30]
    story.append(make_table(ipo_headers, ipo_rows, cw3))
    story.append(Spacer(1, 8))

    # Tech comparison
    story.append(Paragraph('核心技术参数对比', S_SUBSECTION))
    tech_headers = ['参数', 'NVIDIA H100', 'NVIDIA B200', 'AMD MI300X', 'Cerebras WSE-3']
    tech_rows = [
        ['晶体管数', '800亿', '2080亿', '1530亿', '4万亿'],
        ['制程', 'TSMC 4nm', 'TSMC 4nm', 'TSMC 5/6nm', 'TSMC 5nm'],
        ['片上内存', '80GB HBM3', '192GB HBM3e', '192GB HBM3', '44GB SRAM'],
        ['内存带宽', '3.35TB/s', '8TB/s', '5.3TB/s', '21PB/s'],
        ['功耗', '700W', '1000W', '750W', '23kW(系统)'],
        ['推理速度*', '~100 tok/s', '~200 tok/s', '~90 tok/s', '2,100 tok/s'],
    ]
    cw4 = [CONTENT_W * 0.16, CONTENT_W * 0.19, CONTENT_W * 0.19, CONTENT_W * 0.19, CONTENT_W * 0.27]
    t5 = make_table(tech_headers, tech_rows, cw4)
    story.append(t5)
    story.append(Spacer(1, 4))
    story.append(Paragraph('*推理速度：Llama 3.1 70B模型单用户输出速度，供参考', S_META))

    story.append(PageBreak())

    # =====================================================================
    # PAGE 6: Risk Monitoring & Post-Investment
    # =====================================================================
    story.append(Paragraph('四、风险监控与投后管理', S_SECTION_TITLE))
    story.append(ColorBar(CONTENT_W, 1.5, C_PRIMARY))
    story.append(Spacer(1, 8))

    # Risk matrix
    story.append(Paragraph('核心风险监控矩阵', S_SUBSECTION))
    risk_headers = ['风险项', '监控措施', '改善情况', '残余风险']
    risk_rows = [
        ['客户集中度\n（G42占83%收入）',
         '季度跟踪客户结构\n关注新客户签约',
         '2025年新增Mayo Clinic、\nDell等客户，Q4占比\n降至约60%',
         '中等：需持续\n观察去集中化进展'],
        ['NVIDIA竞争压力\n（B200/GB300迭代）',
         '跟踪NVIDIA产品周期\n对比Cerebras技术迭代',
         'WSE-3推理速度20x领先\n但训练侧仍需证明',
         '中高：NVIDIA生态\n壁垒仍在'],
        ['IPO时间窗口\n不确定性',
         '跟踪SEC审核进度\n监控市场IPO窗口',
         'H轮$23B估值获认可\n市场环境偏好AI标的',
         '低：Q2 2026\n预期明确'],
    ]
    cw5 = [CONTENT_W * 0.22, CONTENT_W * 0.26, CONTENT_W * 0.28, CONTENT_W * 0.24]
    story.append(make_table(risk_headers, risk_rows, cw5))
    story.append(Spacer(1, 12))

    # Post-investment management
    story.append(Paragraph('投后管理措施', S_SUBSECTION))
    story.append(Spacer(1, 6))

    block_w = (CONTENT_W - 10) / 2
    block_h = 85

    b1 = InfoBlock('跟踪频率与创始人关系', [
        '· 季度深度沟通（CEO Andrew Feldman）',
        '· 建立6年+长期信任关系',
        '· 每月书面进展更新',
        '· 关键节点实时同步',
    ], block_w, block_h)

    b2 = InfoBlock('产业资源赋能', [
        '· 对接基金LP中的产业方资源',
        '· 组织AI芯片赛道创始人交流',
        '· 协助打通资本市场网络',
        '· IPO路演战略咨询支持',
    ], block_w, block_h)

    b3 = InfoBlock('客户拓展支持', [
        '· 协助对接G42等中东客户',
        '· 利用LP网络推荐企业客户',
        '· 背书效应助力商务拓展',
        '· 推动政府/国防客户接触',
    ], block_w, block_h)

    b4 = InfoBlock('投后核心进展', [
        '· 技术：WSE-3发布，推理速度20x NVIDIA',
        '· 商业：H1收入$136.4M（+1474%）',
        '· 融资：H轮$1B，估值$23B',
        '· IPO：预计Q2 2026上市',
    ], block_w, block_h)

    # 2x2 grid using Table
    grid_data = [[b1, b2], [b3, b4]]
    grid = Table(grid_data, colWidths=[block_w + 5, block_w + 5], rowHeights=[block_h + 6, block_h + 6])
    grid.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(grid)

    story.append(PageBreak())

    # =====================================================================
    # PAGE 7: Conclusion & Key Metrics
    # =====================================================================
    story.append(Paragraph('五、投资结论与关键数据速览', S_SECTION_TITLE))
    story.append(ColorBar(CONTENT_W, 1.5, C_PRIMARY))
    story.append(Spacer(1, 8))

    # Conclusion box
    conclusion_paras = [
        Paragraph('<b>投资结论</b>', make_style('cc1', FONT_CN_BOLD, 10, 15, C_DARK)),
        Paragraph('<b>三大逻辑兑现：</b>赛道确定性超预期（AI芯片市场+86%），技术范式符合预期（WSE-3领先但需持续证明），'
                  '商业化逻辑已修复（客户集中度问题正在改善）。',
                  make_style('cc2', FONT_CN, 8.5, 13, C_BLACK)),
        Paragraph('<b>退出展望：</b>预计Q2 2026 IPO，以$23B估值上市。IPO后根据锁定期和市场情况制定分批退出策略，'
                  '预期回报倍数可观。',
                  make_style('cc3', FONT_CN, 8.5, 13, C_BLACK)),
        Paragraph('<b>持续关注：</b>①客户集中度去化进展 ②NVIDIA B200/GB300竞品压力 ③IPO定价与市场反应 '
                  '④推理业务增长速度。',
                  make_style('cc4', FONT_CN, 8.5, 13, C_BLACK)),
    ]
    story.append(HighlightBox(conclusion_paras, CONTENT_W))
    story.append(Spacer(1, 10))

    # Key metrics table
    story.append(Paragraph('关键数据速览', S_SUBSECTION))
    kpi_headers = ['指标', '数据']
    kpi_rows = [
        ['投资时间', '2023年底/2024年初'],
        ['投资轮次', 'Pre-IPO late stage'],
        ['最新估值', '$23B（H轮，2026.02）'],
        ['累计融资额', '~$2.82B（A-H轮）'],
        ['H1 2024收入', '$136.4M（同比+1474%）'],
        ['全年预估收入', '~$272M'],
        ['P/S倍数', '~85x（基于预估收入）'],
        ['最大合约', 'G42 $1.43B（已执行$272M）'],
        ['IPO计划', '预计Q2 2026 NYSE/NASDAQ'],
        ['AI芯片市场', '2024年$490亿，CAGR 93%'],
        ['WSE-3晶体管', '4万亿（H100的50倍）'],
        ['推理速度', '2,100 tok/s（NVIDIA 20倍）'],
        ['投资逻辑兑现度', '3/3逻辑均已兑现或修复'],
    ]
    cw6 = [CONTENT_W * 0.35, CONTENT_W * 0.65]
    story.append(make_table(kpi_headers, kpi_rows, cw6))
    story.append(Spacer(1, 10))

    # Follow-up plan
    plan_paras = [
        Paragraph('<b>基金后续规划</b>', make_style('fp1', FONT_CN_BOLD, 9, 13, C_DARK)),
        Paragraph('· <b>IPO退出：</b>制定分批退出策略，IPO后锁定期内评估市场反应，分3-4批次逐步减持',
                  make_style('fp2', FONT_CN, 8.5, 12, C_BLACK)),
        Paragraph('· <b>持续赋能：</b>IPO前继续提供产业资源对接和资本市场支持，助力上市成功',
                  make_style('fp3', FONT_CN, 8.5, 12, C_BLACK)),
        Paragraph('· <b>风险监控：</b>保持季度深度跟踪，重点关注客户去集中化和NVIDIA竞品迭代',
                  make_style('fp4', FONT_CN, 8.5, 12, C_BLACK)),
        Paragraph('· <b>赛道布局：</b>基于Cerebras投后经验，持续关注Groq商业化进展和Photonium技术突破',
                  make_style('fp5', FONT_CN, 8.5, 12, C_BLACK)),
    ]
    story.append(HighlightBox(plan_paras, CONTENT_W))

    # Build
    doc.build(story, onFirstPage=page_template, onLaterPages=page_template)
    print(f'PDF generated: {output_path}')
    return output_path


if __name__ == '__main__':
    build_pdf()
