"""Build index.html from tools/page.html: draw the figures, write the video transcript, fill the placeholders.

Usage: python tools/build_page.py
Reads tools/page.html, tools/narration.json and assets/video/chapters.json. Writes index.html at the site root.
Every figure has its English and Japanese labels side by side; the page shows one language at a time.
The counts in Figures 5 and 6 and every number in a label are the paper's (Maeda 2026, version 1.0).
Figures 1, 2 and 4, and the shape of the curve in Figure 4, are drawings.
"""
import html
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
W = 640  # width of every figure in SVG units


def esc(s):
    return html.escape(s, quote=True)


def t2(x, y, en, ja, cls="", anchor="start"):
    """One label in two languages: two text elements at the same place."""
    a = "" if anchor == "start" else f' text-anchor="{anchor}"'
    c = f' class="{cls}"' if cls else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}"{a}{c} data-l="en" lang="en">{en}</text>'
            f'<text x="{x:.1f}" y="{y:.1f}"{a}{c} data-l="ja" lang="ja">{ja}</text>')


def tip(en, ja):
    """Hover text. site.js swaps it when the language changes."""
    return f'<title data-en="{esc(en)}" data-ja="{esc(ja)}">{esc(en)}</title>'


def figure(num, h, body, cap_en, cap_ja, aria_en, aria_ja):
    return (f'<figure class="fig">\n<div class="fig-scroll"><svg viewBox="0 0 {W} {h}" role="img" '
            f'aria-label="{esc(aria_en)}" data-aria-en="{esc(aria_en)}" data-aria-ja="{esc(aria_ja)}">'
            f'{body}</svg></div>\n<figcaption><span data-l="en" lang="en"><span class="fignum">Figure {num}.</span>'
            f'{cap_en}</span><span data-l="ja" lang="ja"><span class="fignum">図 {num}</span>'
            f'{cap_ja}</span></figcaption>\n</figure>')


# ---------------------------------------------------------------- Figure 1: the Sun as a lens

def fig_lens():
    y, sx = 128, 170
    s = []
    s.append(f'<path class="axis-faint" d="M24,{y} H620"/>')
    # rays from the far planet, bent at the Sun, crossing the axis farther away the farther out they pass
    for b, fx in ((26, 330), (34, 385), (42, 440), (50, 495)):
        for sgn in (-1, 1):
            y0 = y + sgn * b
            x1 = min(fx + 70, 600)
            y1 = y0 + (y - y0) * (x1 - sx) / (fx - sx)
            s.append(f'<path class="ray" d="M48,{y0} H{sx} L{x1:.1f},{y1:.1f}"/>')
    s.append(f'<path class="focal" d="M330,{y} H618"/>')
    s.append(f'<circle class="sun" cx="{sx}" cy="{y}" r="16"/>')
    s.append(t2(sx, y + 74, "Sun", "太陽", "ink", "middle"))
    s.append(f'<circle class="planet dot" cx="34" cy="38" r="9"/>')
    s.append(t2(50, 34, "a planet of another star", "ほかの恒星の惑星", "ink"))
    s.append(t2(50, 50, "(very far away, to the left)", "(ずっと左の、とても遠く)", "small"))
    s.append(t2(sx + 16, y - 62, "light is bent near the Sun", "太陽のそばで光が曲がる", "", "start"))
    s.append(f'<rect class="tel" x="532" y="{y - 7}" width="40" height="14" rx="2"/>')
    s.append(f'<rect class="tel" x="528" y="{y - 10}" width="6" height="20" rx="1"/>')
    s.append(t2(552, y - 20, "telescope", "望遠鏡", "ink", "middle"))
    s.append(t2(470, y + 40, "the light comes together along this line", "光はこの線に沿って集まる", "", "middle"))
    s.append(t2(470, y + 58, "(650 AU from the Sun in the paper's baseline)", "(論文の基本の設定では太陽から 650 天文単位)",
                "small", "middle"))
    return figure(
        1, 236, "".join(s),
        "The Sun as a lens (a drawing, not to scale). Light from a far planet passes the Sun and is bent by its gravity. "
        "Far beyond the planets, the bent light comes together. A telescope there could collect it.",
        "レンズとしての太陽(縮尺は正しくない絵)。遠い惑星からの光は太陽のそばを通り、重力で曲がります。"
        "惑星たちよりずっと遠くで、曲がった光は集まります。そこに置いた望遠鏡が、その光を集めます。",
        "Drawing: light rays from a far planet pass above and below the Sun, bend, and meet along a line far behind "
        "the Sun, where a telescope sits.",
        "図: 遠い惑星からの光が太陽の上下を通って曲がり、太陽のはるか後ろの線の上で集まる。そこに望遠鏡がある。")


# ---------------------------------------------------------------- Figure 2: scanning and the blur

def fig_scan():
    s = []
    n, c, x0, y0 = 8, 26, 30, 30
    me = (3, 4)
    for i in range(n):
        for j in range(n):
            cls = "cell-me" if (i, j) == me else "cell"
            s.append(f'<rect class="{cls}" x="{x0 + j * c}" y="{y0 + i * c}" width="{c}" height="{c}"/>')
    cx, cy = x0 + me[1] * c + c / 2, y0 + me[0] * c + c / 2
    for i, j in ((0, 0), (0, 7), (1, 1), (2, 6), (5, 0), (5, 7), (7, 0), (7, 6), (7, 7), (3, 6), (0, 2), (6, 2)):
        px, py = x0 + j * c + c / 2, y0 + i * c + c / 2
        s.append(f'<path class="blur" d="M{px:.1f},{py:.1f} L{cx:.1f},{cy:.1f}"/>')
    s.append(f'<circle class="scope" cx="{cx}" cy="{cy}" r="8"/>')
    s.append(t2(x0 + n * c / 2, y0 + n * c + 22, "image of the planet", "惑星の像", "ink", "middle"))
    s.append(t2(x0 + n * c / 2, y0 + n * c + 39, "128 × 128 pixels (8 × 8 drawn)", "128 × 128 画素(8 × 8 を描いた)",
                "small", "middle"))
    tx = 270
    s.append(f'<path class="leader" d="M{cx + 10},{cy} H{tx - 8}"/>')
    s.append(t2(tx, 66, "At each step, the telescope gets:", "1 歩ごとに、望遠鏡は次を受けます。", "ink bold"))
    s.append(f'<rect class="cell-me" x="{tx}" y="84" width="14" height="14"/>')
    s.append(t2(tx + 22, 96, "the light of its own pixel", "自分の画素の光", "ink"))
    s.append(f'<rect class="cell" x="{tx}" y="110" width="14" height="14"/>')
    s.append(t2(tx + 22, 122, "a faint blur from all the other pixels", "ほかの全ての画素からの、淡くぼやけた光", "ink"))
    s.append(t2(tx, 160, "So the data are a mix.", "そのため、データは混ざっています。", ""))
    s.append(t2(tx, 180, "A computation takes the mix apart.", "計算で、混ざりを解きます。", ""))
    s.append(t2(tx, 214, "1 pixel = 99.5 km on the planet", "1 画素 = 惑星の上の 99.5 km", "ink"))
    return figure(
        2, 280, "".join(s),
        "How the picture is made (a drawing). The telescope moves across the image of the planet, one step for each "
        "pixel. At each step it gets the light of its own pixel and a faint blur from all the other pixels.",
        "写真の作り方(絵)。望遠鏡は、惑星の像の上を 1 画素ごとに 1 歩ずつ動きます。1 歩ごとに、自分の画素の光と、"
        "ほかの全ての画素からの淡くぼやけた光を受けます。",
        "Drawing: an 8 by 8 grid stands for the 128 by 128 pixel image. One pixel is bright; lines from other pixels "
        "lead to it. Text: one pixel is 99.5 km on the planet.",
        "図: 8×8 の格子が 128×128 画素の像を表す。一つの画素が明るく、ほかの画素から線が集まる。1 画素は惑星の上の 99.5 km。")


# ---------------------------------------------------------------- Figure 3: which barrier, scale by scale

def ring_x(k, x0=60, x1=600):
    return x0 + math.log2(k) / 6 * (x1 - x0)


def fig_scale():
    s = []
    ya, yb = 132, 92
    s.append(f'<path class="axis" d="M{ring_x(1) - 12},{ya} H{ring_x(64) + 12}"/>')
    for k in (1, 2, 4, 8, 16, 32, 64):
        x = ring_x(k)
        s.append(f'<path class="axis" d="M{x:.1f},{ya - 5} v10"/>')
        s.append(f'<text x="{x:.1f}" y="{ya + 20}" text-anchor="middle" class="small">{k}</text>')
    s.append(t2(ring_x(8), ya + 38, "ring k (each step to the right halves the size of the pattern)",
                "環 k(右へ一つ進むごとに、模様の大きさが半分)", "small", "middle"))
    segs = [(1, 4, "seg-cld", "clouds", "雲"), (8, 16, "seg-und", "undetermined", "未定"),
            (32, 64, "seg-cor", "corona noise", "コロナの雑音")]
    for a, b, cls, en, ja in segs:
        xa, xb = ring_x(a) - 8, ring_x(b) + 8
        s.append(f'<path class="{cls}" d="M{xa:.1f},{yb} H{xb:.1f}"/>')
        s.append(t2((xa + xb) / 2, yb - 14, en, ja, "ink bold", "middle"))
    s.append(t2(ring_x(2), yb - 32, "about 1,600 km and larger", "約 1600 km 以上", "small", "middle"))
    s.append(t2(ring_x(45), yb - 32, "200 km and smaller", "200 km 以下", "small", "middle"))
    x11 = ring_x(11)
    s.append(f'<g>{tip("Ring 11: no information in one setting of the shape of the Sun's gravity (sin²β = 0.3)", "環 11: 太陽の重力の形のある設定(sin²β = 0.3)では、情報が無い")}'
             f'<path class="j2" d="M{x11:.1f},{ya - 26} v52"/><path class="j2x" d="M{x11 - 6:.1f},{ya - 6} l12,12 m0,-12 l-12,12"/></g>')
    s.append(t2(x11 + 8, ya + 62, "ring 11: no information in one setting", "環 11: ある設定では情報が無い", "small j2t"))
    s.append(t2(x11 + 8, ya + 78, "(shape of the Sun's gravity)", "(太陽の重力の形)", "small j2t"))
    return figure(
        3, 222, "".join(s),
        "Which barrier causes the largest loss of information, size by size, in the model. Clouds lead for the widest "
        "patterns, the noise from the corona for the finest. In between (rings 8 and 16) the order changes with the "
        "settings. Numbers from the paper; the conditions are those of the paper's Figure 2.",
        "モデルの中で、情報を最も多く失わせる壁を、大きさごとに示します。いちばん広い模様では雲、いちばん細かい模様では"
        "コロナの雑音です。その間(環 8 と 16)では、順番が設定によって入れ替わります。数は論文のもので、条件は論文の図 2 のものです。",
        "Scale of pattern sizes, ring 1 to 64. Rings 1 to 4 (about 1,600 km and larger): clouds. Rings 8 and 16: "
        "undetermined. Rings 32 and 64 (200 km and smaller): corona noise. Ring 11: no information in one setting of "
        "the shape of the Sun's gravity.",
        "模様の大きさの目盛り、環 1〜64。環 1〜4(約 1600 km 以上): 雲。環 8 と 16: 未定。環 32 と 64(200 km 以下): "
        "コロナの雑音。環 11: 太陽の重力の形のある設定では情報が無い。")


# ---------------------------------------------------------------- Figure 4: the gap and two rules

def fig_gap():
    s = []
    x0, x1, y0, y1 = 70, 610, 236, 40

    def X(k):
        return x0 + math.log2(k) / 6 * (x1 - x0)

    def Y(v):
        return y0 + (math.log10(v) + 1) / 2 * (y1 - y0)

    s.append(f'<rect class="band" x="{X(6.5):.1f}" y="{y1}" width="{X(12.5) - X(6.5):.1f}" height="{y0 - y1}"/>')
    s.append(t2((X(6.5) + X(12.5)) / 2, y1 - 8, "910 – 531 km", "910〜531 km", "ink bold", "middle"))
    s.append(f'<path class="axis" d="M{x0 - 8},{y0} H{x1 + 8} M{x0 - 8},{y0} V{y1}"/>')
    s.append(f'<path class="rline" d="M{x0 - 8},{Y(1):.1f} H{x1 + 8}"/>')
    s.append(t2(x1 + 6, Y(1) - 6, "signal = error", "信号 = 誤差", "small halo", "end"))
    s.append(t2(x0 - 14, (y0 + y1) / 2, "signal ÷ error", "信号 ÷ 誤差", "small", "middle").replace(
        '<text ', f'<text transform="rotate(-90 {x0 - 14} {(y0 + y1) / 2})" '))
    s.append(t2(x0, y0 + 18, "← wide", "← 広い", "small"))
    s.append(t2(x1, y0 + 18, "fine →", "細かい →", "small", "end"))
    last = 30
    for k in range(1, 49):
        lv = 0.8 - 0.75 * math.log2(k) / math.log2(30) - 0.75 * math.exp(-((math.log2(k) - math.log2(9.2)) / 0.33) ** 2)
        v = 10 ** lv
        v = min(v, 0.85) if 7 <= k <= 12 else max(v, 1.08)
        if k > last:
            v = min(v, 0.95 * 10 ** (-(k - last) / 30))
        cls = "seen" if v >= 1 else "unseen"
        s.append(f'<circle class="{cls}" cx="{X(k):.1f}" cy="{Y(v):.1f}" r="3.4"/>')
        if k == 6:
            y6 = Y(v)
        if k == last:
            ylast = Y(v)
    s.append(f'<path class="flag1" d="M{X(6):.1f},{y6 - 8:.1f} l-6,-10 h12 z"/>')
    s.append(t2(X(6) - 10, y6 - 24, "rule one stops here", "決め方その一はここで止まる", "small ink bold", "end"))
    s.append(f'<path class="arc" d="M{X(6):.1f},{y6 - 22:.1f} Q{(X(6) + X(last)) / 2:.1f},{y1 - 30:.1f} {X(last):.1f},{ylast - 12:.1f}"/>')
    s.append(f'<path class="flag2" d="M{X(last):.1f},{ylast - 8:.1f} l-6,-10 h12 z"/>')
    s.append(t2(X(last) + 12, ylast - 22, "rule two", "決め方その二", "small ink bold"))
    return figure(
        4, 268, "".join(s),
        "Why the rule matters (a drawing; only the band is from the paper). With Gaussian-correlated model clouds, the "
        "signal falls below the error only in a band of middle sizes, 910 to 531 km (rings 7 to 12). Rule one goes from "
        "wide to fine and stops before the band. Rule two takes the finest size that is seen and jumps over the band.",
        "決め方が効くわけ(絵。論文から取ったのは帯だけ)。ガウス型の相関のモデルの雲では、信号が誤差を下回るのは、"
        "中くらいの大きさの帯、910〜531 km(環 7〜12)だけです。決め方その一は広い方から進み、帯の手前で止まります。"
        "決め方その二は、見えたいちばん細かい大きさを取り、帯を飛び越えます。",
        "Drawing: dots show signal divided by error for each size. They are above the line signal = error, except in a "
        "band from 910 to 531 km and at the finest sizes. Rule one stops before the band; rule two jumps over it.",
        "図: 点は大きさごとの信号÷誤差。910〜531 km の帯と、いちばん細かい所を除いて、信号 = 誤差の線より上にある。"
        "決め方その一は帯の手前で止まり、その二は帯を飛び越える。")


# ---------------------------------------------------------------- Figures 5 and 6: counts

CAT = {"clouds": ("seg-fill-cld", "clouds", "雲"), "corona": ("seg-fill-cor", "corona", "コロナ"),
       "j2": ("seg-fill-j2", "gravity shape", "重力の形"), "und": ("seg-fill-und", "undetermined", "未定")}


def stacked(x, y, w_total, total, parts, h=18):
    s = []
    for key, n in parts:
        if n == 0:
            continue
        cls, en, ja = CAT[key]
        w = w_total * n / total
        s.append(f'<g>{tip(f"{en}: {n} of {total}", f"{ja}: {total} のうち {n}")}'
                 f'<rect class="{cls}" x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}"/></g>')
        if w >= 22:
            s.append(f'<text class="on" x="{x + w / 2:.1f}" y="{y + h / 2 + 4.5}" text-anchor="middle">{n}</text>')
        x += w
    return "".join(s)


def legend(x, y, keys):
    s = []
    for key in keys:
        cls, en, ja = CAT[key]
        s.append(f'<rect class="{cls}" x="{x}" y="{y - 10}" width="12" height="12"/>')
        s.append(t2(x + 18, y, en, ja, "small"))
        x += 18 + (len(en) * 6.6 + 18)
    return "".join(s)


def fig_rules():
    s = []
    rules = [("rule one (D1)", "その一(D1)"), ("rule two (D2)", "その二(D2)"),
             ("rule three (D3)", "その三(D3)"), ("rule four (D4)", "その四(D4)")]
    gauss = [[("clouds", 93), ("und", 27)], [("corona", 80), ("und", 40)],
             [("corona", 77), ("und", 43)], [("clouds", 105), ("und", 15)]]
    expo = [[("corona", 47), ("j2", 4), ("und", 69)], [("corona", 80), ("und", 40)],
            [("corona", 79), ("und", 41)], [("corona", 78), ("und", 42)]]
    bx, bw = 150, 450
    y = 26
    for title_en, title_ja, rows in (("Gaussian-correlated model clouds", "ガウス型の相関のモデルの雲", gauss),
                                     ("Exponentially correlated model clouds", "指数型の相関のモデルの雲", expo)):
        s.append(t2(20, y, title_en, title_ja, "ink bold"))
        y += 14
        for (en, ja), parts in zip(rules, rows):
            s.append(t2(20, y + 14, en, ja, ""))
            s.append(stacked(bx, y, bw, 120, parts))
            y += 26
        y += 22
    s.append(legend(150, y - 4, ["clouds", "corona", "j2", "und"]))
    return figure(
        5, y + 8, "".join(s),
        "Which barrier sets the finest detail in the model, over 120 settings (threshold 1). The answer depends on the "
        "rule and on the kind of model cloud. The counts of “clouds”, “corona” and “gravity shape” are upper limits. "
        "Counts from the paper's Table 2. Hover over a bar for its number.",
        "モデルの中で、いちばん細かい所を決める壁(120 の設定、しきい値 1)。答えは、決め方とモデルの雲の種類で変わります。"
        "「雲」「コロナ」「重力の形」の数は上限です。数は論文の表 2 から取りました。棒に重ねると数が出ます。",
        "Bar chart. Gaussian-correlated clouds: rule one clouds 93, undetermined 27; rule two corona 80, undetermined 40; "
        "rule three corona 77, undetermined 43; rule four clouds 105, undetermined 15. Exponentially correlated clouds: "
        "rule one corona 47, gravity shape 4, undetermined 69; rule two corona 80, undetermined 40; rule three corona 79, "
        "undetermined 41; rule four corona 78, undetermined 42.",
        "棒グラフ。ガウス型: その一 雲 93・未定 27、その二 コロナ 80・未定 40、その三 コロナ 77・未定 43、その四 雲 105・未定 15。"
        "指数型: その一 コロナ 47・重力の形 4・未定 69、その二 コロナ 80・未定 40、その三 コロナ 79・未定 41、その四 コロナ 78・未定 42。")


def fig_measured():
    s = []
    data = [("January 2024", "2024 年 1 月", 8, 6, 2), ("April 2024", "2024 年 4 月", 8, 7, 1),
            ("July 2024", "2024 年 7 月", 8, 6, 2), ("October 2024", "2024 年 10 月", 12, 4, 0)]
    y = 18
    for en, ja, c, r, u in data:
        s.append(t2(20, y + 14, en, ja, ""))
        s.append(stacked(150, y, 450, 16, [("clouds", c), ("corona", r), ("und", u)]))
        y += 28
    s.append(legend(150, y + 14, ["clouds", "corona", "und"]))
    return figure(
        6, y + 26, "".join(s),
        "Which barrier sets the finest detail when the model uses the clouds measured in EPIC pictures, for the main "
        "brightness divisor: counts over 16 combinations of rule, threshold and blur normalisation in each month. "
        "Counts from the paper's Table 3. These hold for the paper's baseline only.",
        "EPIC の写真で測った雲をモデルに入れたとき、いちばん細かい所を決める壁(主な明るさの割る数)。月ごとに、決め方・しきい値・"
        "ぼやけの規格化の 16 の組み合わせで数えました。数は論文の表 3 から取りました。論文の基本の設定だけに当てはまります。",
        "Bar chart over 16 combinations. January 2024: clouds 8, corona 6, undetermined 2. April: 8, 7, 1. "
        "July: 8, 6, 2. October: clouds 12, corona 4, undetermined 0.",
        "16 の組み合わせの棒グラフ。2024 年 1 月: 雲 8・コロナ 6・未定 2。4 月: 8・7・1。7 月: 8・6・2。10 月: 雲 12・コロナ 4・未定 0。")


# ---------------------------------------------------------------- Figure 7: the categories

def fig_categories():
    s = []
    x0, x1, lo, hi = 30, 610, 0.25, 8.0

    def X(v):
        return x0 + (math.log(v) - math.log(lo)) / (math.log(hi) - math.log(lo)) * (x1 - x0)

    y = 52
    for a, b, cls, en, ja in ((lo, 2 / 3, "zone-below", "below the bound", "下限より下"),
                              (2 / 3, 2, "zone-reach", "reaches the bound", "下限に届く"),
                              (2, hi, "zone-away", "away from the bound", "下限から遠い")):
        s.append(f'<rect class="{cls}" x="{X(a):.1f}" y="{y}" width="{X(b) - X(a):.1f}" height="26"/>')
        s.append(t2((X(a) + X(b)) / 2, y - 10, en, ja, "ink bold", "middle"))
    for v, lab in ((2 / 3, "2/3"), (1, "1"), (2, "2")):
        s.append(f'<path class="axis" d="M{X(v):.1f},{y - 2} v34"/>')
        s.append(f'<text x="{X(v):.1f}" y="{y + 48}" text-anchor="middle" class="ink">{lab}</text>')
    s.append(t2((x0 + x1) / 2, y + 68, "ratio = error ÷ bound (the median over the sizes compared)",
                "比 = 誤差 ÷ 下限(比べる大きさの中での中央値)", "small", "middle"))
    yv = y + 100
    s.append(f'<path class="ebar" d="M{X(1.1):.1f},{yv} H{X(2.9):.1f} M{X(1.1):.1f},{yv - 6} v12 M{X(2.9):.1f},{yv - 6} v12"/>')
    s.append(f'<circle class="und-dot" cx="{X(1.6):.1f}" cy="{yv}" r="5"/>')
    s.append(f'<path class="rline" d="M{X(2):.1f},{yv - 16} V{yv + 12}"/>')
    s.append(t2(X(1.1) - 12, yv + 4, "the range crosses a line → undetermined", "幅が線をまたぐ → 未定", "", "end"))
    return figure(
        7, yv + 20, "".join(s),
        "How each result is judged. The paper divides the error of a reconstruction by the bound. Below 2/3 is "
        "“below the bound”, 2/3 to 2 “reaches the bound”, above 2 “away from the bound”. If the ratio and its "
        "16–84 per cent range do not fall in one category, the result is undetermined.",
        "結果の判じ方。論文は、取り戻した表面の誤差を下限で割ります。2/3 より小さければ「下限より下」、2/3〜2 なら"
        "「下限に届く」、2 より大きければ「下限から遠い」です。比とその 16〜84 % の幅が一つの区分に収まらなければ、未定です。",
        "Scale of the ratio error divided by bound, with three zones: below 2/3 below the bound, 2/3 to 2 reaches the "
        "bound, above 2 away from the bound. An example range that crosses the line at 2 is undetermined.",
        "誤差÷下限の比の目盛り。2/3 より下は下限より下、2/3〜2 は下限に届く、2 より上は下限から遠い。2 の線をまたぐ幅の例は未定。")


# ---------------------------------------------------------------- transcript and page

def clock(t):
    return f"{int(t // 60)}:{int(t % 60):02d}"


def transcript(script, chapters):
    starts = {c["id"]: c["start"] for c in chapters["chapters"]}
    out = ['<ol class="chapters">']
    for sc in script["scenes"]:
        t = starts[sc["id"]]
        mm = clock(t)
        en = " ".join(line["en"] for line in sc["lines"])
        ja = "".join(line["ja"] for line in sc["lines"])
        out.append(
            f'<li><button type="button" data-seek="{t}" aria-label="Play from {mm}" data-aria-en="Play from {mm}" '
            f'data-aria-ja="{mm} から再生">{mm}</button>'
            f'<h3><span data-l="en" lang="en">{esc(sc["title"])}</span>'
            f'<span data-l="ja" lang="ja">{esc(sc["title_ja"])}</span></h3>\n'
            f'<p data-l="en" lang="en">{esc(en)}</p>\n<p data-l="ja" lang="ja">{esc(ja)}</p></li>')
    out.append("</ol>")
    return "\n".join(out)


def main():
    page = (HERE / "page.html").read_text(encoding="utf-8")
    script = json.loads((HERE / "narration.json").read_text(encoding="utf-8"))
    chapters = json.loads((ROOT / "assets" / "video" / "chapters.json").read_text(encoding="utf-8"))
    total = round(chapters["duration"])
    head, body = page.split("</head>", 1)
    fill = {
        "{{DURATION_EN}}": f"{total // 60} min {total % 60} s",
        "{{DURATION_JA}}": f"{total // 60} 分 {total % 60} 秒",
        "{{TRANSCRIPT}}": transcript(script, chapters),
        "{{FIG_LENS}}": fig_lens(),
        "{{FIG_SCAN}}": fig_scan(),
        "{{FIG_SCALE}}": fig_scale(),
        "{{FIG_GAP}}": fig_gap(),
        "{{FIG_RULES}}": fig_rules(),
        "{{FIG_MEASURED}}": fig_measured(),
        "{{FIG_CATEGORIES}}": fig_categories(),
    }
    for k, v in fill.items():
        assert k in body, k
        body = body.replace(k, v)
    left = re.findall(r"\{\{[A-Z0-9_]+\}\}", body)
    assert not left, left
    (ROOT / "index.html").write_text(head + "</head>" + body, encoding="utf-8")
    print(f"index.html {len(head + body) / 1000:.0f} kB")


if __name__ == "__main__":
    main()
