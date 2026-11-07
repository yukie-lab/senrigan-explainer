"""Manim scenes for the explainer video (Manim Community Edition 0.22).

Each scene reads the clip lengths in build/timing.json. A beat starts with
self.beat() and ends with self.done(), which waits until the line and a short
pause have played. The real start time of every beat is written to
build/marks/<scene>.json, and tools/assemble.py places the clips there, so the
voice stays in step with the picture even if an animation runs long.

The pictures of planets, clouds and curves are drawings. Only the numbers that
the narration says (and the counts in the bar charts) come from the paper
(Maeda 2026, version 1.0).

Render one scene:  manim render -r 1920,1080 --fps 30 tools/video.py S1
"""
import json
from pathlib import Path

import numpy as np
from manim import *

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"
TIMING = json.loads((BUILD / "timing.json").read_text(encoding="utf-8"))
GAP = 0.45  # pause after each line, in seconds

config.background_color = "#0e1014"
FONT = "CMU Serif"

C_SUN = "#E8C11C"
C_COR = "#FF9F43"     # corona noise
C_CLD = "#58C4DD"     # clouds
C_J2 = "#C58AE6"      # shape of the Sun's gravity (solar quadrupole)
C_UND = "#8F959E"     # undetermined
C_BELOW = "#FC6255"   # below the bound
C_REACH = "#83C167"   # reaches the bound
C_AWAY = "#F4D345"    # away from the bound
C_KEY = "#F4D345"     # key statements
C_DIM = "#A3A9B1"
C_FAINT = "#5B616A"
C_RAY = "#FFE9A8"

TOP = 3.25           # y of scene headings; the bottom of the frame stays free for subtitles


def T(s, size=34, color=WHITE, **kw):
    return Text(s, font=FONT, font_size=size, color=color, **kw)


def M(s, size=34, color=WHITE, **kw):
    return MarkupText(s, font=FONT, font_size=size, color=color, **kw)


def head(s):
    return T(s, 40).move_to([0, TOP, 0])


def glow(point, color, r=0.12, layers=4, spread=0.8, alpha=0.07):
    g = VGroup()
    for i in range(layers, 0, -1):
        g.add(Dot(point, radius=r * (1 + spread * i), color=color, fill_opacity=alpha))
    g.add(Dot(point, radius=r, color=color))
    return g


def note(s):
    """Small grey note in the top right corner (the bottom is kept free for subtitles)."""
    return T(s, 22, C_FAINT).to_corner(UR, buff=0.35)


def check(size=0.35, color=C_REACH):
    p = VMobject(color=color, stroke_width=6)
    p.set_points_as_corners([[-0.5, 0, 0], [-0.15, -0.38, 0], [0.55, 0.45, 0]])
    return p.scale(size / 0.9)


def cross(size=0.3, color=C_BELOW):
    a = Line([-1, -1, 0], [1, 1, 0], color=color, stroke_width=6)
    b = Line([-1, 1, 0], [1, -1, 0], color=color, stroke_width=6)
    return VGroup(a, b).scale(size / 2)


def box(mob, color=C_DIM, buff=0.22, r=0.12):
    return SurroundingRectangle(mob, color=color, buff=buff, corner_radius=r, stroke_width=2)


# ---------------------------------------------------------------- pictures (drawings, not data)

def field(n, slope, seed, cut=None):
    """Random field whose power falls as k**slope (an illustration)."""
    rng = np.random.default_rng(seed)
    kx = np.fft.fftfreq(n)[:, None]
    ky = np.fft.fftfreq(n)[None, :]
    k = np.hypot(kx, ky)
    k[0, 0] = 1.0
    amp = k ** (slope / 2)
    if cut:
        amp = amp * np.exp(-(k * n / cut) ** 2)
    amp[0, 0] = 0.0
    f = np.fft.ifft2(amp * (rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n)))).real
    return (f - f.mean()) / f.std()


def surface_rgb(f):
    """Colour a field as sea and land."""
    sea0, sea1 = np.array([18, 44, 96]), np.array([38, 92, 160])
    lnd0, lnd1 = np.array([62, 118, 64]), np.array([160, 128, 84])
    t = np.clip((f + 2.0) / 2.2, 0, 1)[..., None]
    u = np.clip((f - 0.2) / 1.6, 0, 1)[..., None]
    sea = sea0 + (sea1 - sea0) * t
    land = lnd0 + (lnd1 - lnd0) * u
    return np.where((f > 0.2)[..., None], land, sea)


def clouds_alpha(f, level=0.5, soft=0.6):
    return np.clip((f - level) / soft, 0, 1)


def disk_mask(n):
    y, x = np.mgrid[0:n, 0:n]
    r = np.hypot(x - (n - 1) / 2, y - (n - 1) / 2) / (n / 2)
    return np.clip((1.0 - r) * n / 2, 0, 1)


def to_image(rgb, alpha=None, height=2.0, nearest=False):
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    a = np.full(rgb.shape[:2], 255, np.uint8) if alpha is None else (np.clip(alpha, 0, 1) * 255).astype(np.uint8)
    img = ImageMobject(np.dstack([rgb, a]))
    if nearest:
        img.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
    img.scale_to_fit_height(height)
    return img


def planet(height=2.0, seed=3, cloud_seed=None, n=160, cloud_level=0.45):
    """An Earth-like planet seen as a disk (a drawing)."""
    rgb = surface_rgb(field(n, -3.0, seed))
    if cloud_seed is not None:
        a = clouds_alpha(field(n, -3.6, cloud_seed), cloud_level)[..., None]
        rgb = rgb * (1 - a) + np.array([236, 240, 244]) * a
    y, x = np.mgrid[0:n, 0:n]
    r = np.hypot(x - (n - 1) / 2, y - (n - 1) / 2) / (n / 2)
    shade = np.clip(1.0 - 0.45 * r ** 3, 0, 1)[..., None]
    return to_image(rgb * shade, disk_mask(n), height)


def gray_image(f, height, nearest=True, lo=None, hi=None):
    lo = f.min() if lo is None else lo
    hi = f.max() if hi is None else hi
    g = np.clip((f - lo) / (hi - lo), 0, 1)
    rgb = np.stack([30 + 200 * g, 40 + 190 * g, 60 + 180 * g], -1)
    return to_image(rgb, None, height, nearest)


def lens_ray(b, sx, sy, fx, x0=-6.2, x1=None, color=C_RAY, width=2.5, opacity=0.85):
    """A light ray that passes the Sun at height b and crosses the axis at fx (not to scale)."""
    x1 = fx + 1.6 if x1 is None else x1
    slope = -b / (fx - sx)
    p = VMobject(stroke_color=color, stroke_width=width, stroke_opacity=opacity)
    p.set_points_as_corners([[x0, sy + b, 0], [sx, sy + b, 0], [x1, sy + b + slope * (x1 - sx), 0]])
    return p


def telescope(color=GREY_B):
    tube = Rectangle(width=0.62, height=0.26, color=color, fill_color=color, fill_opacity=0.9, stroke_width=0)
    lip = Rectangle(width=0.08, height=0.36, color=color, fill_color=color, fill_opacity=1, stroke_width=0)
    lip.next_to(tube, LEFT, buff=0)
    return VGroup(tube, lip)


def spacecraft():
    body = Square(0.22, color=GREY_B, fill_color=GREY_B, fill_opacity=1, stroke_width=0)
    p1 = Rectangle(width=0.36, height=0.14, color="#3A6FB0", fill_color="#3A6FB0", fill_opacity=1, stroke_width=0)
    p2 = p1.copy()
    p1.next_to(body, LEFT, buff=0.04)
    p2.next_to(body, RIGHT, buff=0.04)
    return VGroup(body, p1, p2)


def bell(width=2.0, height=1.0, color=WHITE, skew=0.0, tail=0.0):
    """A bell curve, or a lopsided curve with a heavy tail (a drawing)."""
    def f(t):
        x = t * width / 2
        z = t * 3.0
        y = np.exp(-z * z / 2)
        if skew:
            y = np.exp(-z * z / 2) * (1 + np.tanh(skew * z)) / 2 + tail * np.exp(-max(z, 0) / 1.6) * (z > 0)
        return [x, y * height, 0]
    c = ParametricFunction(f, t_range=[-1, 1, 0.01], color=color, stroke_width=4)
    return c


def lopsided(width=2.0, height=1.0, color=WHITE, alpha=4.0):
    """A lopsided curve with a long tail on one side (a skew-normal shape; a drawing)."""
    import math
    zs = np.linspace(-3, 3, 601)
    ys = np.array([math.exp(-z * z / 2) * (1 + math.erf(alpha * z / math.sqrt(2))) for z in zs])
    peak = ys.max()

    def f(t):
        zz = t * 3.0 * 1.25 + 0.9
        v = math.exp(-zz * zz / 2) * (1 + math.erf(alpha * zz / math.sqrt(2))) / peak
        return [t * width / 2, v * height, 0]
    return ParametricFunction(f, t_range=[-1, 1, 0.005], color=color, stroke_width=4)


class Beats(Scene):
    SID = None

    def setup(self):
        self.lines = TIMING[self.SID]
        self.k = -1
        self.marks = []
        self._note = None

    def set_note(self, s):
        """Show one small note in the corner; a new note replaces the old one, None removes it."""
        if self._note is not None:
            self.remove(self._note)
            self._note = None
        if s:
            self._note = note(s)
            self.add(self._note)

    def beat(self):
        self.k += 1
        self.t0 = self.renderer.time
        self.marks.append(round(self.t0, 4))

    def done(self, extra=0.0):
        end = self.t0 + self.lines[self.k]["dur"] + GAP + extra
        rem = end - self.renderer.time
        if rem < -0.05:
            print(f"[{self.SID} line {self.lines[self.k]['id']}] picture runs {-rem:.2f} s past the line")
        if rem > 1 / 30:
            self.wait(rem)

    def tear_down(self):
        assert len(self.marks) == len(self.lines), (self.SID, len(self.marks), len(self.lines))
        out = BUILD / "marks"
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{self.SID}.json").write_text(
            json.dumps({"marks": self.marks, "end": round(self.renderer.time, 4)}), encoding="utf-8")

    def fade_all(self, run_time=0.6):
        mobs = [m for m in self.mobjects]
        if mobs:
            self.play(*[FadeOut(m) for m in mobs], run_time=run_time)
        for m in mobs:
            m.clear_updaters()
        self._note = None


# ---------------------------------------------------------------- 1. the Sun as a lens

class S1(Beats):
    SID = "s1"

    def construct(self):
        # Title card (no voice); its middle frame is the poster.
        title = T("The Sun as a lens", 66)
        t2 = T("What limits the picture of a far planet?", 40, C_DIM).next_to(title, DOWN, buff=0.35)
        sub = T("A plain-language guide to a 2026 research paper", 28, C_FAINT).next_to(t2, DOWN, buff=0.6)
        card = VGroup(title, t2, sub).move_to(UP * 0.4)
        sun0 = glow([0, -2.0, 0], C_SUN, r=0.2, layers=5, alpha=0.06)
        self.play(FadeIn(VGroup(title, t2), shift=UP * 0.2), FadeIn(sun0), run_time=1.0)
        self.play(FadeIn(sub), run_time=0.6)
        self.wait(1.6)
        self.play(FadeOut(card), FadeOut(sun0), run_time=0.6)

        sx, sy = -3.2, 0.3
        sun = glow([sx, sy, 0], C_SUN, r=0.42, layers=5, spread=0.35, alpha=0.08)
        sun_l = T("Sun", 26, C_DIM).next_to(sun, DOWN, buff=0.35)
        axis = DashedLine([-6.6, sy, 0], [6.8, sy, 0], color=C_FAINT, dash_length=0.08, stroke_width=1.5)

        # 1.1 gravity bends light
        self.beat()
        self.play(FadeIn(sun), FadeIn(sun_l), Create(axis), run_time=0.8)
        r1 = lens_ray(0.62, sx, sy, 0.4)
        self.play(Create(r1), run_time=1.4)
        lab = T("light is bent near the Sun", 26, C_RAY).move_to([-1.0, 1.55, 0])
        self.play(FadeIn(lab), run_time=0.5)
        self.set_note("drawing, not to scale")
        self.done()

        # 1.2 bent light comes together far away
        self.beat()
        bs = [0.62, 0.8, 1.0, 1.2]
        fxs = [0.4, 1.4, 2.5, 3.6]
        rays = VGroup(*[lens_ray(b, sx, sy, fx) for b, fx in zip(bs[1:], fxs[1:])])
        rays_dn = VGroup(*[lens_ray(-b, sx, sy, fx) for b, fx in zip(bs, fxs)])
        self.play(LaggedStart(*[Create(r) for r in rays], *[Create(r) for r in rays_dn], lag_ratio=0.15),
                  run_time=1.8)
        fline = Line([0.4, sy, 0], [6.6, sy, 0], color=C_RAY, stroke_width=7, stroke_opacity=0.8)
        flab = T("light comes together here", 26, C_RAY).move_to([3.8, -0.75, 0])
        self.play(Create(fline), FadeIn(flab), run_time=0.9)
        self.done()

        # 1.3 a telescope there, pictures of planets of other stars
        self.beat()
        tel = telescope().move_to([4.6, sy, 0])
        tel_l = T("telescope", 26, C_DIM).next_to(tel, UP, buff=0.3)
        far = planet(0.55, seed=11, cloud_seed=4).move_to([-6.35, 2.35, 0])
        far_l = T("a planet of another star", 24, C_DIM).next_to(far, RIGHT, buff=0.25)
        far_l2 = T("(very far away, to the left)", 20, C_FAINT).next_to(far_l, DOWN, buff=0.08, aligned_edge=LEFT)
        self.play(FadeOut(lab), FadeIn(far), FadeIn(far_l), FadeIn(far_l2), run_time=0.8)
        self.play(FadeIn(tel, shift=LEFT * 0.3), FadeIn(tel_l), run_time=0.8)
        self.done()

        # 1.4 solar gravitational lens
        self.beat()
        name = T("the solar gravitational lens", 40, C_SUN).move_to([0.6, 3.15, 0])
        self.play(Write(name), run_time=1.4)
        self.done()

        # 1.5 the question
        self.beat()
        scene = VGroup(sun, sun_l, axis, r1, rays, rays_dn, fline, flab, tel, tel_l, far_l, far_l2, name)
        self.play(scene.animate.fade(0.85), far.animate.fade(0.85), run_time=0.6)
        q1 = T("In a simple model of this imaging,", 40).move_to([0, 0.8, 0])
        q2 = T("what limits the detail of the picture?", 46, C_KEY).next_to(q1, DOWN, buff=0.3)
        self.play(FadeIn(q1, shift=UP * 0.15), run_time=0.7)
        self.play(FadeIn(q2, shift=UP * 0.15), run_time=0.8)
        self.done()

        # 1.6 not about whether or when
        self.beat()
        n1 = T("The paper does not say whether or when", 30, C_DIM)
        n2 = T("a mission could take such a picture.", 30, C_DIM).next_to(n1, DOWN, buff=0.15)
        ng = VGroup(n1, n2).next_to(q2, DOWN, buff=0.6)
        self.play(FadeIn(ng), run_time=0.8)
        self.done()
        self.fade_all()


# ---------------------------------------------------------------- 2. how the picture is made

class S2(Beats):
    SID = "s2"

    def construct(self):
        self.play(FadeIn(head("How the picture is made")), run_time=0.5)

        # 2.1 baseline target
        self.beat()
        p = planet(2.6, seed=3).move_to([-3.4, 0.2, 0])
        l1 = T("an Earth-like surface", 32).move_to([2.2, 0.75, 0])
        l2 = T("30 parsecs away", 32, C_DIM).next_to(l1, DOWN, buff=0.3)
        l3 = T("(the paper's baseline)", 24, C_FAINT).next_to(l2, DOWN, buff=0.3)
        self.play(FadeIn(p, scale=0.9), run_time=0.9)
        self.play(FadeIn(l1), FadeIn(l2), FadeIn(l3), run_time=0.8)
        self.done()

        # 2.2 distance and opening
        self.beat()
        y = 0.0
        self.play(FadeOut(VGroup(l1, l2, l3)), p.animate.scale(0.32).move_to([-6.1, y, 0]), run_time=0.8)
        sun = glow([-2.4, y, 0], C_SUN, r=0.3, layers=4, spread=0.4)
        sun_l = T("Sun", 24, C_DIM).next_to(sun, UP, buff=0.35)
        gap = T("30 pc", 24, C_FAINT).move_to([-4.3, y + 0.35, 0])
        dots = DashedLine([-5.55, y, 0], [-2.95, y, 0], color=C_FAINT, dash_length=0.1)
        tel = telescope().move_to([5.4, y, 0])
        arr = DoubleArrow([-2.4, y - 0.9, 0], [5.4, y - 0.9, 0], buff=0, color=C_DIM, stroke_width=3,
                          tip_length=0.2)
        dl = T("650 × the distance from the Sun to the Earth", 28).next_to(arr, DOWN, buff=0.2)
        ap = T("opening: 1 m", 26, C_DIM).next_to(tel, UP, buff=0.3)
        self.play(FadeIn(sun), FadeIn(sun_l), Create(dots), FadeIn(gap), run_time=0.8)
        self.play(FadeIn(tel), GrowFromCenter(arr), FadeIn(dl), run_time=1.0)
        self.play(FadeIn(ap), run_time=0.5)
        self.set_note("not to scale")
        self.done()
        self.play(*[FadeOut(m) for m in [p, sun, sun_l, gap, dots, tel, arr, dl, ap]], run_time=0.5)
        self.set_note(None)

        # 2.3 scanning the image, one step per pixel
        self.beat()
        n, s = 8, 0.5
        cells = VGroup(*[Square(s, stroke_color=C_FAINT, stroke_width=1.5, fill_color=C_CLD, fill_opacity=0.0)
                         for _ in range(n * n)])
        cells.arrange_in_grid(n, n, buff=0).move_to([-3.0, -0.1, 0])
        img_l = T("image of the planet", 26, C_DIM).next_to(cells, UP, buff=0.25)
        self.play(Create(cells), FadeIn(img_l), run_time=1.0)
        ring = Circle(radius=s * 0.36, color=WHITE, stroke_width=4).move_to(cells[0])
        tl = T("the telescope moves one step per pixel", 26).move_to([3.5, 1.4, 0])
        self.play(FadeIn(ring), FadeIn(tl), run_time=0.4)
        for i in range(1, 10):
            self.play(ring.animate.move_to(cells[i]), run_time=0.22)
        self.done()

        # 2.4 128 x 128 pixels, 99.5 km
        self.beat()
        a1 = T("128 × 128 pixels", 34).move_to([3.5, 0.4, 0])
        a2 = T("(8 × 8 drawn here)", 22, C_FAINT).next_to(a1, DOWN, buff=0.15)
        a3 = T("1 pixel = 99.5 km on the planet", 30, C_CLD).next_to(a2, DOWN, buff=0.45)
        self.play(FadeIn(a1), FadeIn(a2), run_time=0.7)
        self.play(FadeIn(a3), run_time=0.6)
        self.done()

        # 2.5 own pixel plus a faint blur from all others
        self.beat()
        self.play(FadeOut(VGroup(tl, a1, a2, a3)), run_time=0.4)
        me = 3 * n + 4
        self.play(ring.animate.move_to(cells[me]), cells[me].animate.set_fill(C_SUN, 0.9), run_time=0.6)
        own = T("light of its own pixel", 28, C_SUN).move_to([3.5, 1.0, 0])
        self.play(FadeIn(own), run_time=0.4)
        others = [c for i, c in enumerate(cells) if i != me]
        self.play(*[c.animate.set_fill(C_SUN, 0.16) for c in others], run_time=0.8)
        rays = VGroup(*[Line(cells[j].get_center(), cells[me].get_center(), color=C_SUN, stroke_width=1.5,
                             stroke_opacity=0.45) for j in [0, 7, 9, 21, 40, 47, 56, 62, 63, 30, 2, 50]])
        blur = T("+ a faint blur from all the other pixels", 28, C_DIM).next_to(own, DOWN, buff=0.35)
        self.play(LaggedStart(*[Create(r) for r in rays], lag_ratio=0.06), FadeIn(blur), run_time=1.2)
        self.done()

        # 2.6 the data are a mix; a computation takes it apart
        self.beat()
        self.play(FadeOut(VGroup(cells, rays, ring, img_l, own, blur)), run_time=0.5)
        f = field(64, -2.6, 21)
        yy, xx = np.mgrid[0:64, 0:64]
        rr = np.hypot(np.minimum(xx, 64 - xx), np.minimum(yy, 64 - yy)).astype(float)
        ker = np.where(rr == 0, 1.12 * 3, 1.0 / (np.pi * np.maximum(rr, 1)))
        mix = np.fft.ifft2(np.fft.fft2(f) * np.fft.fft2(ker)).real
        sharp = gray_image(f, 2.6).move_to([3.6, -0.1, 0])
        blurry = gray_image(mix, 2.6).move_to([-3.6, -0.1, 0])
        bl = T("data: a mix", 28, C_DIM).next_to(blurry, UP, buff=0.25)
        sl = T("the picture", 28, C_DIM).next_to(sharp, UP, buff=0.25)
        ar = Arrow([-2.0, -0.1, 0], [2.0, -0.1, 0], buff=0, color=WHITE, stroke_width=5)
        al = T("computation", 28, C_KEY).next_to(ar, UP, buff=0.2)
        self.play(FadeIn(blurry), FadeIn(bl), run_time=0.7)
        self.play(GrowArrow(ar), FadeIn(al), run_time=0.7)
        self.play(FadeIn(sharp), FadeIn(sl), run_time=0.7)
        self.done()
        self.fade_all()


# ---------------------------------------------------------------- 3. three barriers and one bound

class S3(Beats):
    SID = "s3"

    def construct(self):
        # 3.1
        self.beat()
        h = head("Three things that limit the picture")
        self.play(FadeIn(h), run_time=0.7)
        self.done()

        xs = [-4.6, 0.0, 4.6]
        yc = 0.7

        # 3.2 corona
        self.beat()
        sun = glow([xs[0], yc, 0], C_SUN, r=0.45, layers=7, spread=0.32, alpha=0.07)
        rng = np.random.default_rng(5)
        specks = VGroup(*[Dot([xs[0] + x, yc + y, 0], radius=0.022, color=C_COR, fill_opacity=0.9)
                          for x, y in rng.uniform(-1.4, 1.4, size=(90, 2)) if 0.62 < np.hypot(x, y) < 1.45])
        l1 = T("1  the corona", 32, C_COR).move_to([xs[0], -1.25, 0])
        l1b = T("adds random noise", 24, C_DIM).next_to(l1, DOWN, buff=0.15)
        self.play(FadeIn(sun), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(d, scale=2) for d in specks], lag_ratio=0.02), FadeIn(l1), FadeIn(l1b),
                  run_time=1.4)
        self.done()

        # 3.3 clouds that change between visits
        self.beat()
        pa = planet(2.1, seed=3, cloud_seed=31).move_to([xs[1], yc, 0])
        pb = planet(2.1, seed=3, cloud_seed=32).move_to([xs[1], yc, 0])
        pc = planet(2.1, seed=3, cloud_seed=33).move_to([xs[1], yc, 0])
        l2 = T("2  clouds", 32, C_CLD).move_to([xs[1], -1.25, 0])
        l2b = T("change from visit to visit", 24, C_DIM).next_to(l2, DOWN, buff=0.15)
        self.play(FadeIn(pa), FadeIn(l2), FadeIn(l2b), run_time=0.7)
        self.play(FadeOut(pa), FadeIn(pb), run_time=0.9)
        self.play(FadeOut(pb), FadeIn(pc), run_time=0.9)
        self.done()

        # 3.4 shape of the Sun's gravity: a point becomes a caustic
        self.beat()
        dot = Dot([xs[2], yc, 0], radius=0.07, color=C_J2)
        ast = ParametricFunction(lambda t: [xs[2] + 0.85 * np.cos(t) ** 3, yc + 0.85 * np.sin(t) ** 3, 0],
                                 t_range=[0, TAU, 0.01], color=C_J2, stroke_width=5)
        l3 = T("3  shape of the Sun's gravity", 27, C_J2).move_to([xs[2] - 0.15, -1.25, 0])
        l3b = T("a point becomes a caustic", 24, C_DIM).next_to(l3, DOWN, buff=0.15)
        self.play(FadeIn(dot, scale=2), FadeIn(l3), run_time=0.7)
        self.wait(1.2)
        self.play(ReplacementTransform(dot, ast), FadeIn(l3b), run_time=1.4)
        self.done()

        # 3.5 one simple model: parts add up, random parts follow the bell curve
        self.beat()
        three = Group(sun, specks, l1, l1b, pc, l2, l2b, ast, l3, l3b)
        self.play(three.animate.scale(0.55).move_to([0, 1.75, 0]), run_time=0.9)
        mb = RoundedRectangle(width=9.6, height=1.9, corner_radius=0.15, color=C_DIM, stroke_width=2)
        mb.move_to([0, -0.85, 0])
        m1 = T("one simple model", 30, C_KEY).next_to(mb.get_top(), DOWN, buff=0.22)
        m2 = T("the parts add up", 28).move_to([-2.4, -1.15, 0])
        bc = bell(1.8, 0.75).move_to([2.6, -1.0, 0])
        m3 = T("random parts: bell curve", 24, C_DIM).next_to(bc, DOWN, buff=0.12)
        self.play(Create(mb), FadeIn(m1), run_time=0.7)
        self.play(FadeIn(m2), Create(bc), FadeIn(m3), run_time=1.0)
        self.done()

        # 3.6 the bound
        self.beat()
        self.play(FadeOut(three), FadeOut(h), Group(mb, m1, m2, bc, m3).animate.scale(0.7).move_to([0, 2.6, 0]),
                  run_time=0.8)
        ax = Arrow([-5.2, -0.6, 0], [5.4, -0.6, 0], buff=0, color=C_DIM, stroke_width=3, tip_length=0.2)
        axl = T("error", 26, C_DIM).next_to(ax, RIGHT, buff=0.15)
        bx = -1.6
        floor = Line([bx, -1.2, 0], [bx, 1.0, 0], color=C_KEY, stroke_width=6)
        shade = Rectangle(width=bx + 5.2, height=2.2, stroke_width=0, fill_color=C_KEY, fill_opacity=0.08)
        shade.move_to([(-5.2 + bx) / 2, -0.1, 0])
        fl = T("the bound", 30, C_KEY).next_to(floor, UP, buff=0.15)
        no = T("no unbiased method", 22, C_DIM).move_to([(-5.2 + bx) / 2, 0.25, 0])
        no2 = T("gets here (in the model)", 22, C_DIM).next_to(no, DOWN, buff=0.08)
        tries = VGroup(*[Dot([x, -0.6, 0], radius=0.09, color=WHITE) for x in [-0.9, 0.4, 1.6, 3.1]])
        self.play(GrowArrow(ax), FadeIn(axl), run_time=0.6)
        self.play(Create(floor), FadeIn(shade), FadeIn(fl), run_time=0.8)
        self.play(FadeIn(no), FadeIn(no2), LaggedStart(*[FadeIn(d, scale=2) for d in tries], lag_ratio=0.2),
                  run_time=1.2)
        self.done()

        # 3.7 belongs to the model
        self.beat()
        st = T("It belongs to the model.", 34, C_KEY).move_to([0, -1.85, 0])
        st2 = T("It is not a limit for every method.", 30).next_to(st, DOWN, buff=0.18)
        self.play(FadeIn(st, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(st2), run_time=0.6)
        self.done()
        self.fade_all()


# ---------------------------------------------------------------- 4. scale by scale

def kx(k, x0=-5.4, x1=5.4):
    """Position of ring k (1 to 64) on a scale where each step halves the size."""
    return x0 + np.log2(k) / 6 * (x1 - x0)


class S4(Beats):
    SID = "s4"

    def construct(self):
        self.play(FadeIn(head("Scale by scale")), run_time=0.5)

        # 4.1 patterns of different sizes
        self.beat()
        n = 96
        yy, xx = np.mgrid[0:n, 0:n] / n
        pats = Group()
        for k, ang in [(1, 0.5), (4, 1.1), (16, 0.3)]:
            f = np.cos(TAU * k * (np.cos(ang) * xx + np.sin(ang) * yy))
            pats.add(gray_image(f, 1.9, nearest=False))
        pats.arrange(RIGHT, buff=1.4).move_to([0, 0.75, 0])
        lw = T("wide", 28, C_DIM).next_to(pats[0], DOWN, buff=0.25)
        lf = T("fine", 28, C_DIM).next_to(pats[2], DOWN, buff=0.25)
        dots = T("…", 40, C_DIM).move_to((pats[0].get_right() + pats[1].get_left()) / 2)
        dots2 = dots.copy().move_to((pats[1].get_right() + pats[2].get_left()) / 2)
        self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.2) for p in pats], lag_ratio=0.3), run_time=1.4)
        self.play(FadeIn(lw), FadeIn(lf), FadeIn(dots), FadeIn(dots2), run_time=0.5)
        self.done()

        # 4.2 the bound for each size
        self.beat()
        self.play(FadeOut(Group(pats, lw, lf, dots, dots2)), run_time=0.5)
        y = -0.5
        axis = Line([kx(1) - 0.3, y, 0], [kx(64) + 0.3, y, 0], color=C_DIM, stroke_width=2)
        ks = [1, 2, 4, 8, 16, 32, 64]
        ticks = VGroup(*[Line([kx(k), y - 0.1, 0], [kx(k), y + 0.1, 0], color=C_DIM, stroke_width=2) for k in ks])
        wide = T("← wide", 26, C_DIM).next_to(axis, DOWN, buff=0.3).align_to(axis, LEFT)
        fine = T("fine →", 26, C_DIM).next_to(axis, DOWN, buff=0.3).align_to(axis, RIGHT)
        heights = [0.95, 1.08, 1.2, 1.36, 1.56, 1.8, 2.05]
        bars = VGroup(*[Rectangle(width=0.5, height=h, stroke_width=0, fill_color=WHITE, fill_opacity=0.75)
                        .move_to([kx(k), y + h / 2, 0]) for k, h in zip(ks, heights)])
        bl = T("bound for each size (drawing)", 24, C_DIM).move_to([0, 2.45, 0])
        self.play(Create(axis), FadeIn(ticks), FadeIn(wide), FadeIn(fine), run_time=0.8)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.12), FadeIn(bl), run_time=1.2)
        self.done()

        # 4.3 remove one barrier at a time
        self.beat()
        chips = VGroup(T("remove the corona", 24, C_COR), T("remove the clouds", 24, C_CLD),
                       T("remove the gravity shape", 24, C_J2)).arrange(RIGHT, buff=0.7).move_to([0, 2.2, 0])
        self.play(FadeOut(bl), FadeIn(chips), run_time=0.6)
        for i, c in enumerate(chips):
            fr = box(c, color=c.get_color(), buff=0.12)
            self.play(Create(fr), run_time=0.35)
            self.play(FadeOut(fr), run_time=0.3)
        self.done()

        # 4.4 clouds at the widest sizes
        self.beat()
        yb = y - 0.95
        seg_c = Line([kx(1) - 0.25, yb, 0], [kx(4) + 0.25, yb, 0], color=C_CLD, stroke_width=14)
        lc = T("clouds", 30, C_CLD).next_to(seg_c, DOWN, buff=0.18)
        lc2 = T("about 1,600 km and larger", 22, C_DIM).next_to(lc, DOWN, buff=0.08)
        self.play(*[bars[i].animate.set_fill(C_CLD, 0.85) for i in range(3)], Create(seg_c), run_time=0.8)
        self.play(FadeIn(lc), FadeIn(lc2), FadeOut(wide), run_time=0.5)
        self.done()

        # 4.5 corona at the finest sizes
        self.beat()
        seg_r = Line([kx(32) - 0.25, yb, 0], [kx(64) + 0.25, yb, 0], color=C_COR, stroke_width=14)
        lr = T("corona noise", 30, C_COR).next_to(seg_r, DOWN, buff=0.18)
        lr2 = T("200 km and smaller", 22, C_DIM).next_to(lr, DOWN, buff=0.08)
        self.play(*[bars[i].animate.set_fill(C_COR, 0.85) for i in (5, 6)], Create(seg_r), run_time=0.8)
        self.play(FadeIn(lr), FadeIn(lr2), FadeOut(fine), run_time=0.5)
        self.done()

        # 4.6 in between: undetermined
        self.beat()
        seg_u = Line([kx(8) - 0.25, yb, 0], [kx(16) + 0.25, yb, 0], color=C_UND, stroke_width=14)
        lu = T("undetermined", 30, C_UND).next_to(seg_u, DOWN, buff=0.18)
        self.play(*[bars[i].animate.set_fill(C_UND, 0.85) for i in (3, 4)], Create(seg_u), run_time=0.8)
        self.play(FadeIn(lu), run_time=0.5)
        self.done()

        # 4.7 one size where the information vanishes
        self.beat()
        x11 = kx(11)
        cr = cross(0.34, C_J2).move_to([x11, y + 0.75, 0])
        hole = Line([x11, y, 0], [x11, y + 2.9, 0], color=C_J2, stroke_width=3)
        lj = T("in one setting: no information at one size", 26, C_J2).move_to([0, 2.55, 0])
        self.play(FadeOut(chips), Create(hole), FadeIn(cr, scale=1.5), run_time=0.8)
        self.play(FadeIn(lj), run_time=0.5)
        self.set_note("ring 11 in the paper")
        self.done()
        self.fade_all()


# ---------------------------------------------------------------- 5. what "finest detail" means

class S5(Beats):
    SID = "s5"

    def construct(self):
        # 5.1
        self.beat()
        q = T("Which barrier sets the finest detail?", 40).move_to([0, 0.6, 0])
        q2 = T("It depends on how we define “finest detail”.", 32, C_KEY).next_to(q, DOWN, buff=0.35)
        self.play(FadeIn(q), run_time=0.7)
        self.play(FadeIn(q2), run_time=0.7)
        self.done()

        # 5.2 signal compared with error; the line where they are equal
        self.beat()
        self.play(FadeOut(VGroup(q, q2)), run_time=0.4)
        x0, x1 = -5.6, 5.6
        y0, y1 = -1.7, 2.6

        def X(k):
            return x0 + np.log2(k) / 6 * (x1 - x0)

        def Y(v):  # v from 0.1 to 10 on a log scale
            return y0 + (np.log10(v) + 1) / 2 * (y1 - y0)

        xa = Line([x0 - 0.2, y0, 0], [x1 + 0.2, y0, 0], color=C_DIM, stroke_width=2)
        ya = Line([x0 - 0.2, y0, 0], [x0 - 0.2, y1, 0], color=C_DIM, stroke_width=2)
        yl = T("signal ÷ error", 24, C_DIM).rotate(PI / 2).next_to(ya, LEFT, buff=0.15)
        xw = T("← wide", 22, C_DIM).next_to(xa, DOWN, buff=0.12).align_to(xa, LEFT)
        xf = T("fine →", 22, C_DIM).next_to(xa, DOWN, buff=0.12).align_to(xa, RIGHT)
        one = DashedLine([x0 - 0.2, Y(1), 0], [x1 + 0.2, Y(1), 0], color=WHITE, dash_length=0.12)
        onel = T("signal = error", 24).next_to(one, UP, buff=0.08).align_to(one, RIGHT)
        seen = T("seen", 24, C_REACH).move_to([x0 + 0.6, Y(1) + 0.35, 0])
        unseen = T("not seen", 24, C_UND).move_to([x0 + 0.85, Y(1) - 0.35, 0])
        self.play(Create(xa), Create(ya), FadeIn(yl), FadeIn(xw), FadeIn(xf), run_time=0.8)
        self.play(Create(one), FadeIn(onel), FadeIn(seen), FadeIn(unseen), run_time=0.9)
        self.done()

        # 5.3 the band of middle sizes
        self.beat()
        ks = np.arange(1, 49)

        def g(k):  # a drawing: high at wide sizes, a dip at rings 7 to 12, a fall at the fine end
            lv = 0.8 - 0.75 * np.log2(k) / np.log2(30) - 0.75 * np.exp(-((np.log2(k) - np.log2(9.2)) / 0.33) ** 2)
            return 10 ** lv

        vals = np.array([g(k) for k in ks])
        vals[(ks >= 7) & (ks <= 12)] = np.minimum(vals[(ks >= 7) & (ks <= 12)], 0.85)
        vals[(ks < 7) | (ks > 12)] = np.maximum(vals[(ks < 7) | (ks > 12)], 1.08)
        last = 30
        vals[ks > last] = np.minimum(vals[ks > last], 0.95 * 10 ** (-(ks[ks > last] - last) / 30))
        pts = VGroup(*[Dot([X(k), Y(v), 0], radius=0.06, color=C_REACH if v >= 1 else C_UND)
                       for k, v in zip(ks, vals)])
        band = Rectangle(width=X(12.5) - X(6.5), height=y1 - y0, stroke_width=0, fill_color=C_CLD,
                         fill_opacity=0.12).move_to([(X(6.5) + X(12.5)) / 2, (y0 + y1) / 2, 0])
        bandl = T("910 – 531 km", 26, C_CLD).next_to(band, UP, buff=0.08)
        self.play(LaggedStart(*[FadeIn(p) for p in pts], lag_ratio=0.03), run_time=1.8)
        self.play(FadeIn(band), FadeIn(bandl), run_time=0.7)
        self.set_note("drawing; the band is the paper's (one kind of model cloud)")
        self.done()

        # 5.4 rule one stops before the band
        self.beat()
        w1 = Triangle(color=C_KEY, fill_opacity=1).scale(0.13).rotate(PI).move_to([X(1), Y(vals[0]) + 0.3, 0])
        self.play(FadeIn(w1), run_time=0.3)
        for k in range(2, 7):
            self.play(w1.animate.move_to([X(k), Y(vals[k - 1]) + 0.3, 0]), run_time=0.28)
        stop1 = T("rule one stops here", 26, C_KEY).next_to(w1, UP, buff=0.12).shift(LEFT * 0.6)
        self.play(FadeIn(stop1), run_time=0.5)
        self.done()

        # 5.5 rule two jumps over the band
        self.beat()
        w2 = w1.copy().set_color(WHITE)
        kl = last
        arc = ArcBetweenPoints([X(6), Y(vals[5]) + 0.45, 0], [X(kl), Y(vals[kl - 1]) + 0.45, 0], angle=-PI / 3,
                               color=WHITE, stroke_width=3)
        self.play(Create(arc), MoveAlongPath(w2, arc), run_time=1.4)
        stop2 = T("rule two", 26).next_to(w2, UP, buff=0.12)
        self.play(FadeIn(stop2), run_time=0.4)
        self.done()

        # 5.6 counts over 120 settings
        self.beat()
        chart = VGroup(xa, ya, yl, xw, xf, one, onel, seen, unseen, pts, band, bandl, w1, w2, arc, stop1, stop2)
        self.play(chart.animate.fade(0.85), run_time=0.5)
        W = 7.2

        def row(label, parts, yrow):
            lab = T(label, 28).move_to([-4.6, yrow, 0])
            segs, txt = VGroup(), VGroup()
            x = -2.9
            for n, col, name in parts:
                w = W * n / 120
                r = Rectangle(width=w, height=0.55, stroke_width=0, fill_color=col, fill_opacity=0.9)
                r.move_to([x + w / 2, yrow, 0])
                segs.add(r)
                txt.add(T(f"{name} {n}", 22, BLACK if col != C_UND else WHITE).move_to(r))
                x += w
            return lab, segs, txt

        a = row("rule one", [(93, C_CLD, "clouds"), (27, C_UND, "undet.")], 0.9)
        b = row("rule two", [(80, C_COR, "corona"), (40, C_UND, "undetermined")], -0.2)
        cap = T("120 settings, the kind of model cloud above", 22, C_DIM).move_to([0.7, -1.0, 0])
        for lab, segs, txt in (a, b):
            self.play(FadeIn(lab), LaggedStart(*[GrowFromEdge(s, LEFT) for s in segs], lag_ratio=0.5), run_time=1.0)
            self.play(FadeIn(txt), run_time=0.4)
        self.play(FadeIn(cap), run_time=0.4)
        self.done()

        # 5.7 also the other rules, the threshold, the kind of cloud
        self.beat()
        also = T("It also changes with the other rules, the threshold,", 28, C_KEY).move_to([0, -1.45, 0])
        also2 = T("and the kind of model cloud.", 28, C_KEY).next_to(also, DOWN, buff=0.12)
        self.play(FadeIn(also), FadeIn(also2), run_time=0.8)
        self.done()
        self.fade_all(0.5)

        # 5.8 without clouds and the gravity shape: 637, 354, 199 km
        self.beat()
        h = T("No clouds, no gravity-shape effect", 34).move_to([0, 2.6, 0])
        h2 = T("finest size seen, after this much observing", 26, C_DIM).next_to(h, DOWN, buff=0.15)
        self.play(FadeIn(h), FadeIn(h2), run_time=0.7)
        rows = VGroup()
        for i, (yr, km) in enumerate([("1 year", 637), ("10 years", 354), ("100 years", 199)]):
            yv = 0.9 - i * 1.0
            lab = T(yr, 30).move_to([-4.2, yv, 0])
            w = 7.0 * km / 637
            bar = Rectangle(width=w, height=0.5, stroke_width=0, fill_color=C_COR, fill_opacity=0.85)
            bar.move_to([-2.8 + w / 2, yv, 0])
            num = T(f"{km} km", 30, C_COR).next_to(bar, RIGHT, buff=0.25)
            rows.add(VGroup(lab, bar, num))
        for r in rows:
            self.play(FadeIn(r[0]), GrowFromEdge(r[1], LEFT), run_time=0.7)
            self.play(FadeIn(r[2]), run_time=0.3)
            self.wait(1.4)
        self.set_note("the paper's baseline")
        self.done()
        self.fade_all()


# ---------------------------------------------------------------- 6. real clouds

class S6(Beats):
    SID = "s6"

    def construct(self):
        self.play(FadeIn(head("Real clouds")), run_time=0.5)

        # 6.1 model clouds are simple
        self.beat()
        n = 120
        mc = clouds_alpha(field(n, -6.0, 41, cut=10), 0.3, 1.0)
        mod = to_image(np.full((n, n, 3), 236), mc * disk_mask(n), 2.3).move_to([-3.2, 0.3, 0])
        modb = Circle(radius=1.15, color=C_FAINT, stroke_width=2).move_to(mod)
        ml = T("model clouds: simple", 28, C_DIM).next_to(modb, DOWN, buff=0.3)
        qm = T("?", 110, C_CLD).move_to([3.2, 0.3, 0])
        ql = T("real clouds", 28, C_DIM).next_to(qm, DOWN, buff=0.35).align_to(ml, DOWN)
        self.play(FadeIn(mod), Create(modb), FadeIn(ml), run_time=0.9)
        self.play(FadeIn(qm, scale=1.3), FadeIn(ql), run_time=0.8)
        self.done()

        # 6.2 EPIC on DSCOVR, the whole day side
        self.beat()
        self.play(FadeOut(Group(mod, modb, ml, qm, ql)), run_time=0.4)
        earth = planet(3.0, seed=7, cloud_seed=8, cloud_level=0.35).move_to([-2.4, 0.1, 0])
        sc = spacecraft().move_to([3.6, 1.2, 0])
        look = DashedLine(sc.get_left() + LEFT * 0.1, earth.get_right() + RIGHT * 0.15 + UP * 0.6, color=C_FAINT,
                          dash_length=0.1)
        l1 = T("the EPIC camera on DSCOVR", 28).next_to(sc, DOWN, buff=0.35)
        l2 = T("sees the whole day side", 24, C_DIM).next_to(l1, DOWN, buff=0.15)
        self.play(FadeIn(earth), run_time=0.7)
        self.play(FadeIn(sc), Create(look), FadeIn(l1), FadeIn(l2), run_time=0.9)
        self.set_note("drawing, not an EPIC picture")
        self.done()

        # 6.3 four months of 2024, two times a day
        self.beat()
        self.play(FadeOut(Group(earth, sc, look, l1, l2)), run_time=0.4)
        self.set_note(None)
        months = VGroup()
        for i, m in enumerate(["January", "April", "July", "October"]):
            r = RoundedRectangle(width=2.6, height=1.3, corner_radius=0.12, color=C_DIM, stroke_width=2)
            t1 = T(m, 28).move_to(r.get_center() + UP * 0.22)
            t2 = T("days 1 – 30", 22, C_DIM).move_to(r.get_center() + DOWN * 0.27)
            months.add(VGroup(r, t1, t2))
        months.arrange(RIGHT, buff=0.35).move_to([0, 1.3, 0])
        yr = T("2024", 30, C_KEY).next_to(months, UP, buff=0.25)
        times = VGroup(T("near 00:00 UTC", 28), T("near 12:00 UTC", 28)).arrange(RIGHT, buff=1.6)
        times.move_to([0, -0.5, 0])
        tl = T("two pictures a day (universal time)", 24, C_DIM).next_to(times, DOWN, buff=0.2)
        self.play(FadeIn(yr), LaggedStart(*[FadeIn(m, shift=UP * 0.1) for m in months], lag_ratio=0.2),
                  run_time=1.4)
        self.wait(1.6)
        self.play(FadeIn(times), FadeIn(tl), run_time=0.8)
        self.done()

        # 6.4 surface = a low value per spot; clouds = the rest
        self.beat()
        self.play(FadeOut(VGroup(months, yr, times, tl)), run_time=0.4)
        n = 72
        sf = field(n, -3.0, 51)
        s_rgb = surface_rgb(sf)
        stack = Group()
        for i in range(5):
            a = clouds_alpha(field(n, -3.6, 60 + i), 0.4)[..., None]
            rgb = s_rgb * (1 - a) + np.array([236, 240, 244]) * a
            im = to_image(rgb, None, 1.9)
            im.move_to([-4.6 + 0.16 * i, 0.4 - 0.16 * i, 0])
            stack.add(im)
        stl = T("pictures of one month", 24, C_DIM).next_to(stack, DOWN, buff=0.3)
        surf = to_image(s_rgb, None, 1.9).move_to([0.1, 0.25, 0])
        sul = T("surface", 28, C_REACH).next_to(surf, DOWN, buff=0.3)
        su2 = T("a low value for each spot", 20, C_DIM).next_to(sul, DOWN, buff=0.08)
        a5 = clouds_alpha(field(n, -3.6, 64), 0.4)
        cl = to_image(np.full((n, n, 3), 236), a5, 1.9).move_to([4.6, 0.25, 0])
        clb = Square(1.9, color=C_FAINT, stroke_width=2).move_to(cl)
        cll = T("cloud part", 28, C_CLD).next_to(clb, DOWN, buff=0.3)
        cl2 = T("picture − surface", 20, C_DIM).next_to(cll, DOWN, buff=0.08)
        ar1 = Arrow([-3.1, 0.25, 0], [-1.1, 0.25, 0], buff=0, color=WHITE, stroke_width=4)
        ar2 = Arrow([1.3, 0.25, 0], [3.4, 0.25, 0], buff=0, color=WHITE, stroke_width=4)
        self.play(LaggedStart(*[FadeIn(im) for im in stack], lag_ratio=0.15), FadeIn(stl), run_time=1.0)
        self.play(GrowArrow(ar1), FadeIn(surf), FadeIn(sul), FadeIn(su2), run_time=0.9)
        self.wait(0.8)
        self.play(GrowArrow(ar2), FadeIn(clb), FadeIn(cl), FadeIn(cll), FadeIn(cl2), run_time=0.9)
        self.set_note("drawing")
        self.done()

        # 6.5 day-to-day change fits the model's class
        self.beat()
        self.play(FadeOut(Group(stack, stl, surf, sul, su2, cl, clb, cll, cl2, ar1, ar2)), run_time=0.4)
        self.set_note(None)
        ok = T("how fast clouds change from day to day", 30).move_to([-0.4, 1.0, 0])
        ok2 = T("fits the class of the model", 30, C_REACH).next_to(ok, DOWN, buff=0.2)
        ck = check(0.5).next_to(ok2, RIGHT, buff=0.3)
        self.play(FadeIn(ok), run_time=0.5)
        self.play(FadeIn(ok2), Create(ck), run_time=0.7)
        self.done()

        # 6.6 binding barrier with measured clouds (counts of the paper's Table 3)
        self.beat()
        self.play(VGroup(ok, ok2, ck).animate.scale(0.7).move_to([0, 2.35, 0]), run_time=0.5)
        data = [("Jan", 8, 6, 2), ("Apr", 8, 7, 1), ("Jul", 8, 6, 2), ("Oct", 12, 4, 0)]
        rows = VGroup()
        W = 6.4
        for i, (m, c, r, u) in enumerate(data):
            yv = 1.2 - i * 0.78
            lab = T(m, 28).move_to([-4.6, yv, 0])
            x = -3.6
            segs = VGroup()
            for n_, col in ((c, C_CLD), (r, C_COR), (u, C_UND)):
                if n_ == 0:
                    continue
                w = W * n_ / 16
                seg = Rectangle(width=w, height=0.5, stroke_width=0, fill_color=col, fill_opacity=0.9)
                seg.move_to([x + w / 2, yv, 0])
                segs.add(VGroup(seg, T(str(n_), 22, BLACK if col != C_UND else WHITE).move_to(seg)))
                x += w
            rows.add(VGroup(lab, segs))
        key = VGroup(T("clouds", 24, C_CLD), T("corona", 24, C_COR), T("undetermined", 24, C_UND))
        key.arrange(DOWN, buff=0.22, aligned_edge=LEFT).move_to([4.6, 0.1, 0])
        cap = T("which barrier sets the finest detail: 16 choices per month, 2024", 22, C_DIM)
        cap.move_to([-0.4, -1.95, 0])
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.2) for r in rows], lag_ratio=0.2), FadeIn(key),
                  run_time=1.6)
        self.play(FadeIn(cap), run_time=0.5)
        self.done()

        # 6.7 what real clouds do that the model lacks
        self.beat()
        self.play(FadeOut(VGroup(ok, ok2, ck, rows, key, cap)), run_time=0.4)
        b1 = bell(3.2, 1.5, C_FAINT).move_to([-3.4, 0.6, 0])
        b2 = lopsided(3.2, 1.5, C_CLD).align_to(b1, DOWN).align_to(b1, LEFT)
        bl = T("values: lopsided, heavy tails", 26, C_CLD).next_to(b1, DOWN, buff=0.35)
        bl2 = T("grey: the bell curve", 22, C_FAINT).next_to(bl, DOWN, buff=0.1)
        self.play(Create(b1), run_time=0.6)
        self.play(Create(b2), FadeIn(bl), FadeIn(bl2), run_time=1.0)
        # correlation after 1, 2 and 3 days
        ox, oy = 1.4, -0.6
        ax = Line([ox, oy, 0], [ox + 4.6, oy, 0], color=C_DIM, stroke_width=2)
        ay = Line([ox, oy, 0], [ox, oy + 2.6, 0], color=C_DIM, stroke_width=2)
        rho = 0.55
        days = [1, 2, 3]
        px = [ox + 1.2 * d for d in days]
        model = VGroup(*[Dot([x, oy + 2.4 * rho ** d, 0], radius=0.09, color=C_FAINT) for x, d in zip(px, days)])
        meas = VGroup(*[Dot([x, oy + 2.4 * (rho ** d + (0.0 if d == 1 else 0.13)), 0], radius=0.09, color=C_CLD)
                        for x, d in zip(px, days)])
        dl = VGroup(*[T(f"{d} day" + ("s" if d > 1 else ""), 22, C_DIM).move_to([x, oy - 0.3, 0])
                      for x, d in zip(px, days)])
        al = T("how alike, days apart", 24, C_DIM).next_to(ay, UP, buff=0.12).shift(RIGHT * 1.2)
        self.play(Create(ax), Create(ay), FadeIn(dl), FadeIn(al), FadeIn(model), run_time=0.9)
        self.play(*[TransformFromCopy(model[i], meas[i]) for i in range(3)], run_time=0.9)
        ml = T("blue: measured   grey: model", 22, C_DIM).move_to([ox + 2.3, oy - 0.75, 0])
        self.play(FadeIn(ml), run_time=0.4)
        self.set_note("drawing; the paper gives the numbers")
        self.done()

        # 6.8 a property of the model only
        self.beat()
        self.play(FadeOut(VGroup(b1, b2, bl, bl2, ax, ay, model, meas, dl, al, ml)), run_time=0.5)
        self.set_note(None)
        s1 = T("So the bound is treated", 38).move_to([0, 0.7, 0])
        s2 = T("as a property of the model only.", 38, C_KEY).next_to(s1, DOWN, buff=0.25)
        self.play(FadeIn(s1), FadeIn(s2), run_time=0.8)
        self.done()
        self.fade_all()


# ---------------------------------------------------------------- 7. a test with real pictures

def ratio_axis(x0=-5.6, x1=5.6, y=-0.2, lo=0.25, hi=8.0):
    def X(v):
        return x0 + (np.log(v) - np.log(lo)) / (np.log(hi) - np.log(lo)) * (x1 - x0)
    g = VGroup()
    regions = [(lo, 2 / 3, C_BELOW, "below"), (2 / 3, 2, C_REACH, "reaches"), (2, hi, C_AWAY, "away")]
    for a, b, col, name in regions:
        r = Rectangle(width=X(b) - X(a), height=0.5, stroke_width=0, fill_color=col, fill_opacity=0.35)
        r.move_to([(X(a) + X(b)) / 2, y, 0])
        g.add(r)
    line = Line([x0, y - 0.25, 0], [x1, y - 0.25, 0], color=C_DIM, stroke_width=2)
    g.add(line)
    for v, s in ((2 / 3, "2/3"), (1, "1"), (2, "2")):
        g.add(Line([X(v), y - 0.35, 0], [X(v), y + 0.25, 0], color=WHITE, stroke_width=2))
        g.add(T(s, 24).move_to([X(v), y - 0.6, 0]))
    names = VGroup(*[T(n, 26, c).move_to([(X(a) + X(b)) / 2, y + 0.55, 0]) for a, b, c, n in regions])
    return g, names, X


class S7(Beats):
    SID = "s7"

    def construct(self):
        self.play(FadeIn(head("A test with real pictures")), run_time=0.5)

        # 7.1 real pictures through the imaging model
        self.beat()
        labels = ["real picture", "imaging model", "mixed data", "4 methods", "recovered surface"]
        boxes = VGroup()
        for s in labels:
            t = T(s, 24)
            b = RoundedRectangle(width=max(t.width + 0.4, 1.9), height=0.8, corner_radius=0.12,
                                 color=C_KEY if s == "imaging model" else C_DIM, stroke_width=2)
            boxes.add(VGroup(b, t.move_to(b)))
        boxes.arrange(RIGHT, buff=0.55).move_to([0, 1.7, 0])
        arrows = VGroup(*[Arrow(boxes[i].get_right(), boxes[i + 1].get_left(), buff=0.06, color=C_DIM,
                                stroke_width=3, tip_length=0.15) for i in range(4)])
        self.play(LaggedStart(*[FadeIn(b) for b in boxes[:3]], *[GrowArrow(a) for a in arrows[:2]], lag_ratio=0.2),
                  run_time=1.6)
        self.done()

        # 7.2 first half = truth, second half = test pictures, four methods
        self.beat()
        self.play(FadeIn(boxes[3]), FadeIn(boxes[4]), GrowArrow(arrows[2]), GrowArrow(arrows[3]), run_time=0.9)
        tl = VGroup()
        a = Rectangle(width=4.5, height=0.55, stroke_width=0, fill_color=C_REACH, fill_opacity=0.6)
        b = Rectangle(width=4.5, height=0.55, stroke_width=0, fill_color=C_CLD, fill_opacity=0.6)
        VGroup(a, b).arrange(RIGHT, buff=0.06).move_to([0, 0.1, 0])
        ta = T("days 1 – 15: the truth (surface)", 22, BLACK).move_to(a)
        tb = T("days 16 – 30: pictures to test", 22, BLACK).move_to(b)
        ml = T("one month", 22, C_DIM).next_to(VGroup(a, b), UP, buff=0.12)
        tl.add(a, b, ta, tb, ml)
        self.play(FadeIn(tl), run_time=0.8)
        self.wait(1.5)
        mq = T("four methods: Q1, Q2, Q3, Q4", 26, C_DIM).move_to([0, -0.9, 0])
        self.play(FadeIn(mq), Indicate(boxes[3], color=C_KEY), run_time=1.0)
        self.done()

        # 7.3 ratio = error / bound
        self.beat()
        self.play(FadeOut(VGroup(tl, mq)), VGroup(boxes, arrows).animate.scale(0.75).move_to([0, 2.4, 0]),
                  run_time=0.6)
        fr = T("ratio = error ÷ bound", 40, C_KEY).move_to([0, 1.2, 0])
        self.play(Write(fr), run_time=1.0)
        self.done()

        # 7.4 three categories
        self.beat()
        ax, names, X = ratio_axis()
        self.play(FadeIn(ax), run_time=0.8)
        for nm in names:
            self.play(FadeIn(nm, shift=UP * 0.1), run_time=0.5)
            self.wait(0.9)
        self.done()

        # 7.5 undetermined
        self.beat()
        yv = -1.4
        d = Dot([X(1.6), yv, 0], radius=0.11, color=WHITE)
        bar = Line([X(1.1), yv, 0], [X(2.9), yv, 0], color=WHITE, stroke_width=4)
        ends = VGroup(Line([X(1.1), yv - 0.12, 0], [X(1.1), yv + 0.12, 0], color=WHITE, stroke_width=4),
                      Line([X(2.9), yv - 0.12, 0], [X(2.9), yv + 0.12, 0], color=WHITE, stroke_width=4))
        guide = DashedLine([X(2), -0.45, 0], [X(2), yv - 0.3, 0], color=WHITE, dash_length=0.08)
        ul = T("crosses a line → undetermined", 26, C_UND).next_to(ends[0], LEFT, buff=0.35)
        self.play(FadeIn(d), Create(bar), FadeIn(ends), run_time=0.7)
        self.play(Create(guide), FadeIn(ul), d.animate.set_color(C_UND), bar.animate.set_color(C_UND),
                  ends.animate.set_color(C_UND), run_time=0.8)
        self.done()

        # 7.6 near midnight: no comparison possible
        self.beat()
        self.play(FadeOut(VGroup(d, bar, ends, guide, ul, ax, names, fr)), run_time=0.5)
        c0 = T("near 00:00 UTC", 34).move_to([-3.4, 0.9, 0])
        c0b = T("no comparison possible", 30, C_UND).next_to(c0, DOWN, buff=0.25)
        c0c = T("(the set of sizes to compare was empty)", 22, C_DIM).next_to(c0b, DOWN, buff=0.12)
        c1 = T("near 12:00 UTC", 34).move_to([3.4, 0.9, 0])
        c1b = T("compared", 30, C_REACH).next_to(c1, DOWN, buff=0.25)
        self.play(FadeIn(c0), FadeIn(c0b), FadeIn(c0c), run_time=0.8)
        self.play(FadeIn(c1), FadeIn(c1b), run_time=0.6)
        nm = T("This does not mean that the surface cannot be seen.", 26, C_KEY).move_to([0, -0.9, 0])
        self.wait(2.0)
        self.play(FadeIn(nm), run_time=0.6)
        self.done()

        # 7.7 2024: 22 results below the bound
        self.beat()
        self.play(FadeOut(VGroup(c0, c0b, c0c, c1, c1b, nm)), run_time=0.4)
        ax, names, X = ratio_axis(y=-0.3)
        self.add(ax, names)
        rng = np.random.default_rng(2)
        pos = [[X(rng.uniform(0.33, 0.62)), 0.35 + 0.17 * (i % 7), 0] for i in range(22)]
        dots = VGroup(*[Dot(p, radius=0.075, color=C_BELOW) for p in pos])
        for i, dd in enumerate(dots):
            dd.move_to([X(0.3) + 0.2 * (i % 11) + 0.1, 0.72 + 0.2 * (i // 11), 0])
        lab = T("2024: 22 results below the bound", 30, C_BELOW).move_to([0, 1.55, 0])
        self.play(LaggedStart(*[FadeIn(dd, scale=2) for dd in dots], lag_ratio=0.05), FadeIn(lab), run_time=1.4)
        self.done()

        # 7.8 after seeing: a bound for each time of day
        self.beat()
        pl = T("after seeing this: a bound built for each time of day", 26, C_KEY).move_to([0, -1.6, 0])
        self.play(FadeIn(pl), run_time=0.7)
        self.done()

        # 7.9 none stays below: 16 reach, 6 undetermined
        self.beat()
        anims = []
        for i, dd in enumerate(dots):
            if i < 16:
                tgt = [X(1.0) - 0.7 + 0.2 * (i % 8), 0.72 + 0.2 * (i // 8), 0]
                anims.append(dd.animate.move_to(tgt).set_color(C_REACH))
            else:
                j = i - 16
                tgt = [X(2.0) + 0.6 + 0.2 * (j % 3), 0.72 + 0.2 * (j // 3), 0]
                anims.append(dd.animate.move_to(tgt).set_color(C_UND))
        self.play(*anims, run_time=1.6)
        r1 = T("16 reach", 26, C_REACH).move_to([X(1.0), 1.25, 0])
        r2 = T("6 undetermined", 26, C_UND).move_to([X(2.0) + 0.8, 1.25, 0])
        r0 = T("0 below", 26, C_BELOW).move_to([X(0.42), 1.25, 0])
        self.play(FadeOut(lab), FadeIn(r1), FadeIn(r2), FadeIn(r0), run_time=0.6)
        self.done()

        # 7.10 chosen after seeing: test again on other data
        self.beat()
        self.play(FadeOut(pl), run_time=0.3)
        t1 = T("chosen after seeing the results", 30, C_KEY).move_to([0, -1.5, 0])
        t2 = T("→ test it again, on other data", 30).next_to(t1, DOWN, buff=0.15)
        self.play(FadeIn(t1), run_time=0.5)
        self.play(FadeIn(t2), run_time=0.5)
        self.done()
        self.fade_all()


# ---------------------------------------------------------------- 8. a test fixed in advance

def padlock(color=C_KEY):
    body = RoundedRectangle(width=0.9, height=0.7, corner_radius=0.08, color=color, fill_color=color,
                            fill_opacity=0.9, stroke_width=0)
    arc = Arc(radius=0.3, start_angle=0, angle=PI, color=color, stroke_width=8).next_to(body, UP, buff=-0.02)
    return VGroup(arc, body)


class S8(Beats):
    SID = "s8"

    def construct(self):
        self.play(FadeIn(head("A test fixed in advance")), run_time=0.5)

        # 8.1 fixed before any 2023 number
        self.beat()
        lock = padlock().move_to([-4.6, 1.0, 0])
        items = VGroup(T("the bound for each time of day", 28), T("the methods and the categories", 28),
                       T("what counts as “holds” or “breaks”", 28)).arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        items.move_to([0.9, 1.0, 0])
        when = T("fixed before any 2023 number was computed", 26, C_KEY).move_to([0, -0.5, 0])
        self.play(FadeIn(lock, scale=1.2), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(i, shift=RIGHT * 0.2) for i in items], lag_ratio=0.5), run_time=2.2)
        self.play(FadeIn(when), run_time=0.6)
        self.done()

        # 8.2 four months of 2023
        self.beat()
        self.play(FadeOut(VGroup(lock, items, when)), run_time=0.4)
        months = VGroup()
        for m in ["January", "April", "July", "October"]:
            r = RoundedRectangle(width=2.7, height=0.9, corner_radius=0.12, color=C_DIM, stroke_width=2)
            months.add(VGroup(r, T(m, 28).move_to(r)))
        months.arrange(RIGHT, buff=0.3).move_to([0, 2.0, 0])
        yr = T("2023", 30, C_KEY).next_to(months, LEFT, buff=0.3)
        self.play(FadeIn(yr), LaggedStart(*[FadeIn(m) for m in months], lag_ratio=0.15), run_time=1.2)
        self.done()

        # 8.3 none below the bound, in any month
        self.beat()
        zeros = VGroup()
        for m in months:
            z = T("0", 64, C_REACH).next_to(m, DOWN, buff=0.3)
            zl = T("of 96 below", 22, C_DIM).next_to(z, DOWN, buff=0.08)
            zeros.add(VGroup(z, zl))
        self.play(LaggedStart(*[FadeIn(z, shift=DOWN * 0.15) for z in zeros], lag_ratio=0.25), run_time=1.6)
        self.done()

        # 8.4 midnight not compared; some noon results undetermined
        self.beat()
        mid = VGroup()
        noon = VGroup()
        for m, u in zip(months, [0, 5, 4, 7]):
            a = T("00:00: not compared", 20, C_UND).move_to([m.get_x(), -1.15, 0])
            b = T(f"12:00: {u} of 48 undet.", 20, C_DIM).next_to(a, DOWN, buff=0.12)
            mid.add(a)
            noon.add(b)
        self.play(FadeIn(mid), run_time=0.7)
        self.wait(1.3)
        self.play(FadeIn(noon), run_time=0.7)
        self.done()

        # 8.5 the other findings
        self.beat()
        self.play(FadeOut(VGroup(months, yr, zeros, mid, noon)), run_time=0.5)
        sub = T("the other findings of 2024, checked in 2023", 28, C_DIM).move_to([0, 2.45, 0])
        self.play(FadeIn(sub), run_time=0.4)
        rows = [
            (VGroup(*[check(0.3) for _ in range(4)]).arrange(RIGHT, buff=0.12), "4 held again", C_REACH),
            (T("◐", 34, C_KEY), "1 held only with the four months together", WHITE),
            (T("2/4", 28, C_KEY), "1 could be applied in only two months", WHITE),
            (cross(0.3), "1 broke in one month", C_BELOW),
            (T("?", 36, C_UND), "1 could not be tested", C_UND),
        ]
        grp = VGroup()
        for i, (icon, text, col) in enumerate(rows):
            yv = 1.6 - i * 0.78
            icon.move_to([-4.3, yv, 0])
            t = T(text, 28, col).move_to([-3.2, yv, 0], aligned_edge=LEFT)
            grp.add(VGroup(icon, t))
        for gr in grp:
            self.play(FadeIn(gr, shift=RIGHT * 0.2), run_time=0.5)
            self.wait(1.6)
        self.done()

        # 8.6 2023 does not strengthen 2024
        self.beat()
        self.play(FadeOut(VGroup(sub, grp)), run_time=0.5)
        a = T("2023 does not make the 2024 statements stronger.", 32, C_KEY).move_to([0, 0.9, 0])
        b = T("It shows what the same method, fixed in advance,", 28).next_to(a, DOWN, buff=0.4)
        c = T("gives on other months.", 28).next_to(b, DOWN, buff=0.12)
        self.play(FadeIn(a), run_time=0.7)
        self.wait(1.5)
        self.play(FadeIn(b), FadeIn(c), run_time=0.7)
        self.done()
        self.fade_all()


# ---------------------------------------------------------------- 9. what the paper does not claim

class S9(Beats):
    SID = "s9"

    def construct(self):
        h = head("What the paper does not claim")
        self.add(h)
        texts = [
            ("The bound belongs to the declared model,", "not to every method."),
            ("No statement on whether or when a mission", "could take a picture of a planet of another star."),
            ("One camera, one colour of light, two times of day, the stated months;", "nothing extended to other planets or other times."),
            ("Not in the model: for example, clouds on a round planet,", "and other kinds of noise."),
        ]
        rows = VGroup()
        for i, (a, b) in enumerate(texts):
            yv = 2.15 - i * 1.12
            ta = T(a, 27).move_to([-5.9, yv, 0], aligned_edge=LEFT)
            tb = T(b, 27, C_DIM).next_to(ta, DOWN, buff=0.08, aligned_edge=LEFT)
            dot = Dot([-6.3, yv, 0], radius=0.07, color=C_KEY)
            rows.add(VGroup(dot, ta, tb))
        for i in range(4):
            self.beat()
            self.play(FadeIn(rows[i], shift=RIGHT * 0.2), run_time=0.7)
            self.done()

        # 9.5 read the paper
        self.beat()
        self.play(FadeOut(rows), FadeOut(h), run_time=0.5)
        c1 = T("Maeda, Y. (2026). Clouds, coronal noise and the definition of resolution", 26)
        c2 = T("in solar-gravitational-lens imaging: a linear-Gaussian information map", 26)
        c3 = T("and clouds measured in DSCOVR/EPIC images of Earth. Zenodo.", 26)
        c4 = T("doi:10.5281/zenodo.24014285", 32, C_KEY)
        cite = VGroup(c1, c2, c3).arrange(DOWN, buff=0.12, aligned_edge=LEFT).move_to([0, 1.2, 0])
        c4.next_to(cite, DOWN, buff=0.45)
        self.play(FadeIn(cite), run_time=0.8)
        self.play(FadeIn(c4), run_time=0.5)
        self.done()

        # 9.6 made with AI, synthetic voice
        self.beat()
        e1 = T("Made with the help of AI. The voice is synthetic (Kokoro-82M).", 24, C_DIM)
        e2 = T("Animation: Manim Community Edition.  License: CC BY 4.0.", 24, C_DIM)
        end = VGroup(e1, e2).arrange(DOWN, buff=0.15).move_to([0, -1.0, 0])
        self.play(FadeIn(end), run_time=0.7)
        self.done(extra=1.2)
        self.fade_all(0.8)
