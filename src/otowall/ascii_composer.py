"""Retro ASCII CRT TV and curated retro cloud background composer for OtoWall.

Features:
- Full-resolution desktop wallpaper generation (1920x1080 or dynamic display size).
- 3 Pure, Gorgeous, Curated Retro Background Styles:
  1. Pop-Art Halftone Screen Clouds (clean sky, round halftone cloud dots)
  2. Manga Screentone Dither Clouds (classic retro manga screentone cumulus clouds)
  3. Original Retro ASCII / Bayer Dither Clouds (procedural 8x8 Bayer dot-dithered clouds)
- True Dynamic Color Harmonization:
  Accurately extracts the dominant vibrant hue directly from the album cover art (purple, crimson,
  rose, amber, emerald, sky blue, etc.) and tints the sky, cloud shadows, and accents with zero
  artificial blue bias and zero washing out to white.
- Cute, charming, highly-crafted ASCII retro CRT TV:
  * Symmetrical rabbit ears with knurled sockets, golden ball tips, and ASCII radio sparks
  * Dual symmetrical corner badges framing the antenna sockets without overlapping
  * Retro carrying handle on top
  * Splayed wooden peg legs with rubber feet and ambient drop shadow
  * Tactile ASCII bezel texture shading across TV face
  * Vintage right control panel: rotary channel dial [CH-04], volume dial [VOL],
    tactile power switch with glowing phosphor green LED (●) ON, horizontal speaker louvers,
    and circular headphone jack [PHONES]
  * Bottom player control bar: [ ◄◄ REW ]  [ ▶ PLAY ]  [ ►► FWD ]  [ ■ STOP ]
  * Curved CRT picture tube with full-bleed edge-to-edge album art, subtle scanlines,
    spherical corner glass glare arc reflection, and lower-third frosted title/artist vignette.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS_DIR = Path(__file__).parent / "fonts"
ASSETS_DIR = Path(__file__).parent / "assets"

BAYER_8 = (
    np.array(
        [
            [0, 32, 8, 40, 2, 34, 10, 42],
            [48, 16, 56, 24, 50, 18, 58, 26],
            [12, 44, 4, 36, 14, 46, 6, 38],
            [60, 28, 52, 20, 62, 30, 54, 22],
            [3, 35, 11, 43, 1, 33, 9, 41],
            [51, 19, 59, 27, 49, 17, 57, 25],
            [15, 47, 7, 39, 13, 45, 5, 37],
            [63, 31, 55, 23, 61, 29, 53, 21],
        ],
        dtype=float,
    )
    / 64.0
)

ASCII_RAMP = " .:-=+*#%@"
ASCII_BLOCKS = " ░▒▓█"

_LAST_STYLE_INDEX: int = -1


def load_font(name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in [FONTS_DIR / name, name]:
        try:
            return ImageFont.truetype(str(path), size)
        except Exception:
            continue
    try:
        import os

        sys_font = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / name
        if sys_font.is_file():
            return ImageFont.truetype(str(sys_font), size)
    except Exception:
        pass
    return ImageFont.load_default()


def extract_cover_palette(
    cover: Image.Image,
) -> tuple[
    tuple[int, int, int],  # sky / primary
    tuple[int, int, int],  # shadow / secondary
    tuple[int, int, int],  # light / highlight
    tuple[int, int, int],  # accent (vibrant)
]:
    """Accurately extract the true dominant color palette from cover art without arbitrary bias."""
    small = cover.convert("RGB").resize((128, 128), Image.Resampling.LANCZOS)
    q = small.quantize(colors=16, method=Image.Quantize.MEDIANCUT)
    raw_pal = q.getpalette() or []
    colors = [
        tuple(raw_pal[i : i + 3])
        for i in range(0, min(len(raw_pal), 48), 3)
        if len(raw_pal[i : i + 3]) == 3
    ]
    counts = q.histogram()[: len(colors)]

    scored = []
    for c, count in zip(colors, counts, strict=False):
        r, g, b = c
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        sat = (max_c - min_c) / max(max_c, 1)
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        if 20 <= lum <= 240:
            score = (sat**1.2) * (count**0.5) * (1.0 - abs(lum - 128) / 160.0)
            scored.append((score, c, lum, sat))

    if not scored:
        arr = np.array(small, dtype=float)
        mean_c = tuple(arr.mean(axis=(0, 1)).astype(int))
        scored.append((1.0, mean_c, 128, 0.5))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_c = scored[0][1]

    # Harmonize sky luminance into comfortable rich range [65, 160]
    r, g, b = best_c
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    target_lum = max(65.0, min(160.0, lum))
    if lum > 0:
        factor = target_lum / lum
        sky = tuple(int(max(20, min(230, ch * factor))) for ch in (r, g, b))
    else:
        sky = (40, 100, 180)

    cloud_light = (255, 255, 255)
    # Cloud shadow is a soft tint of sky mixed with pure white
    cloud_shadow = tuple(int(sky[i] * 0.35 + cloud_light[i] * 0.65) for i in range(3))
    accent = tuple(int(max(40, min(255, ch * 1.2 + 15))) for ch in best_c)

    return sky, cloud_shadow, cloud_light, accent


# ─────────────────────────────────────────────────────────────
# 3 CURATED, HIGH-CRAFT RETRO CLOUD BACKGROUNDS
# ─────────────────────────────────────────────────────────────


def bg_halftone_manga_clouds(
    w: int,
    h: int,
    sky: tuple[int, int, int],
    shadow: tuple[int, int, int],
    light: tuple[int, int, int],
    accent: tuple[int, int, int],
    seed: int = 101,
) -> Image.Image:
    """Style 1: Pop-Art Halftone Clouds (clean sky, round halftone cloud dots)."""
    asset_file = ASSETS_DIR / "halftone_clouds_1.jpg"
    if asset_file.is_file():
        try:
            base_img = Image.open(asset_file).convert("RGB")
            scale = max(w / base_img.width, h / base_img.height)
            nw, nh = int(base_img.width * scale), int(base_img.height * scale)
            resized = base_img.resize((nw, nh), Image.Resampling.LANCZOS)
            cl = (nw - w) // 2
            ct = (nh - h) // 2
            cropped = resized.crop((cl, ct, cl + w, ct + h))

            arr = np.array(cropped, dtype=float)
            max_c = arr.max(axis=-1)
            min_c = arr.min(axis=-1)
            sat = (max_c - min_c) / np.maximum(max_c, 1.0)
            lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]

            # Cloud mask: high brightness and low saturation
            w_lum = np.clip((lum - 80.0) / (230.0 - 80.0), 0.0, 1.0)
            w_sat = 1.0 - np.clip((sat - 0.12) / (0.55 - 0.12), 0.0, 1.0)
            w_cloud = np.clip(w_lum * w_sat, 0.0, 1.0)[:, :, None]

            # Smooth sky gradient from sky at top to slightly lighter at bottom
            sky_top = sky
            sky_bot = (
                int(max(0, min(255, sky[0] * 0.85 + 25))),
                int(max(0, min(255, sky[1] * 0.85 + 25))),
                int(max(0, min(255, sky[2] * 0.85 + 25))),
            )
            y_coords = np.linspace(0, 1, h)[:, None, None]
            sky_grad = (1.0 - y_coords) * np.array(sky_top) + y_coords * np.array(sky_bot)

            white = np.array(light, dtype=float)
            out = (1.0 - w_cloud) * sky_grad + w_cloud * white
            return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
        except Exception:
            pass

    return bg_halftone_manga_clouds_procedural(w, h, sky, shadow, light, accent, seed)


def bg_halftone_manga_clouds_procedural(
    w: int,
    h: int,
    sky: tuple[int, int, int],
    shadow: tuple[int, int, int],
    light: tuple[int, int, int],
    accent: tuple[int, int, int],
    seed: int = 101,
) -> Image.Image:
    """Procedural fallback for pop-art halftone clouds with clean sky."""
    canvas = Image.new("RGB", (w, h), sky)
    draw = ImageDraw.Draw(canvas)

    sky_top = sky
    sky_bot = (
        min(255, int(sky[0] * 0.85 + 25)),
        min(255, int(sky[1] * 0.85 + 25)),
        min(255, int(sky[2] * 0.85 + 25)),
    )
    for y in range(h):
        t = y / float(h)
        col = (
            int(sky_top[0] * (1 - t) + sky_bot[0] * t),
            int(sky_top[1] * (1 - t) + sky_bot[1] * t),
            int(sky_top[2] * (1 - t) + sky_bot[2] * t),
        )
        draw.line([(0, y), (w, y)], fill=col)

    cols = 160
    rows = max(80, int(cols * h / w))
    dot_w, dot_h = w / float(cols), h / float(rows)
    rng = np.random.default_rng(seed)

    density = Image.new("L", (cols, rows), 0)
    dd = ImageDraw.Draw(density)

    # Clean clouds concentrated in lower-middle with open sky above
    clusters = [
        (0.22, 0.58, 28, 18),
        (0.78, 0.62, 32, 20),
        (0.50, 0.72, 38, 22),
        (0.12, 0.78, 24, 15),
        (0.88, 0.76, 26, 16),
    ]

    for cx_f, cy_f, rx, ry in clusters:
        cx = int(cols * (cx_f + rng.uniform(-0.02, 0.02)))
        cy = int(rows * (cy_f + rng.uniform(-0.02, 0.02)))
        dd.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=int(rng.uniform(220, 245)))
        for _ in range(8):
            px = int(cx + rng.uniform(-rx * 0.7, rx * 0.7))
            py = int(cy - ry * 0.2 + rng.uniform(-ry * 0.6, ry * 0.3))
            pr = int(rng.uniform(rx * 0.3, rx * 0.5))
            dd.ellipse([px - pr, py - pr, px + pr, py + pr], fill=255)

    density = density.filter(ImageFilter.GaussianBlur(2.2))
    darr = np.array(density, dtype=float) / 255.0
    max_r = min(dot_w, dot_h) * 0.50

    for r in range(rows):
        for c in range(cols):
            val = darr[r, c]
            if val < 0.12:
                continue
            cur_r = max_r * ((val - 0.10) / 0.90) ** 0.85
            cx = c * dot_w + dot_w * 0.5
            cy = r * dot_h + dot_h * 0.5
            if val > 0.60:
                color = light
            elif val > 0.32:
                color = shadow
            else:
                color = tuple(int(sky[i] * 0.50 + shadow[i] * 0.50) for i in range(3))
            draw.ellipse([cx - cur_r, cy - cur_r, cx + cur_r, cy + cur_r], fill=color)

    return canvas


def bg_screentone_clouds(
    w: int,
    h: int,
    sky: tuple[int, int, int],
    shadow: tuple[int, int, int],
    light: tuple[int, int, int],
    accent: tuple[int, int, int],
    seed: int = 202,
) -> Image.Image:
    """Style 2: Manga Screentone Dither Clouds (retro manga screentone cumulus clouds)."""
    asset_file = ASSETS_DIR / "halftone_clouds_2.jpg"
    if asset_file.is_file():
        try:
            base_img = Image.open(asset_file).convert("RGB")
            scale = max(w / base_img.width, h / base_img.height)
            nw, nh = int(base_img.width * scale), int(base_img.height * scale)
            resized = base_img.resize((nw, nh), Image.Resampling.LANCZOS)
            cl = (nw - w) // 2
            ct = (nh - h) // 2
            cropped = resized.crop((cl, ct, cl + w, ct + h))

            arr = np.array(cropped, dtype=float)
            r = arr[:, :, 0]
            g = arr[:, :, 1]
            b = arr[:, :, 2]
            diff = b - r
            lum = 0.299 * r + 0.587 * g + 0.114 * b

            # Pure white cloud mask: high luminance AND low chroma difference
            is_cloud = np.clip((lum - 220.0) / 30.0, 0.0, 1.0) * (
                1.0 - np.clip((diff - 8.0) / 25.0, 0.0, 1.0)
            )
            is_cloud = is_cloud[:, :, None]

            # In the sky, map dark screentone dots to deep sky and inter-dot sky to soft shadow tint
            t_ink = np.clip((lum - 40.0) / (235.0 - 40.0), 0.0, 1.0)[:, :, None]
            sky_deep = np.array(sky, dtype=float)
            sky_light = np.array(shadow, dtype=float)
            white = np.array(light, dtype=float)

            sky_pattern = (1.0 - t_ink) * sky_deep + t_ink * sky_light
            out = (1.0 - is_cloud) * sky_pattern + is_cloud * white

            return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
        except Exception:
            pass

    return bg_original_ascii_clouds(w, h, sky, shadow, light, accent, seed)


def bg_original_ascii_clouds(
    w: int,
    h: int,
    sky: tuple[int, int, int],
    shadow: tuple[int, int, int],
    light: tuple[int, int, int],
    accent: tuple[int, int, int],
    seed: int = 303,
) -> Image.Image:
    """Style 3: Original Retro ASCII / Bayer 8x8 Dot-Dithered Cumulus Clouds."""
    cols = 200
    rows = max(90, int(200 * h / w))
    dot_w = w / float(cols)
    dot_h = h / float(rows)
    dot_r = min(dot_w, dot_h) * 0.44

    density = Image.new("L", (cols, rows), 0)
    dd = ImageDraw.Draw(density)
    rng = np.random.default_rng(seed)

    horizon_r = int(rows * 0.54)
    dd.rectangle([0, horizon_r, cols, rows], fill=210)

    for i in range(15):
        cx = int(cols * (0.02 + 0.96 * i / 14 + rng.uniform(-0.04, 0.04)))
        cy = int(rows * (0.46 + 0.11 * math.sin(i * 1.15) + rng.uniform(-0.03, 0.03)))
        rx = int(rng.uniform(22, 48))
        ry = int(rng.uniform(16, 38))
        dd.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=int(rng.uniform(225, 255)))

    for _i in range(18):
        cx = int(cols * rng.uniform(0.05, 0.95))
        cy = int(rows * rng.uniform(0.35, 0.65))
        rad = int(rng.uniform(14, 34))
        dd.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=255)

    density = density.filter(ImageFilter.GaussianBlur(2.4))
    darr = np.array(density, dtype=float) / 255.0

    tile_y = int(np.ceil(rows / 8))
    tile_x = int(np.ceil(cols / 8))
    bayer = np.tile(BAYER_8, (tile_y, tile_x))[:rows, :cols]

    canvas = Image.new("RGB", (w, h), sky)
    draw = ImageDraw.Draw(canvas)

    sky_top = sky
    sky_bot = (
        min(255, int(sky[0] * 0.85 + 35)),
        min(255, int(sky[1] * 0.85 + 35)),
        min(255, int(sky[2] * 0.90 + 35)),
    )
    for y in range(h):
        t = y / float(h)
        col = (
            int(sky_top[0] * (1 - t) + sky_bot[0] * t),
            int(sky_top[1] * (1 - t) + sky_bot[1] * t),
            int(sky_top[2] * (1 - t) + sky_bot[2] * t),
        )
        draw.line([(0, y), (w, y)], fill=col)

    for r in range(rows):
        for c in range(cols):
            d = darr[r, c]
            b = bayer[r, c]
            if (d + (b - 0.5) * 0.36) > 0.62:
                col = light
            elif (d + (b - 0.5) * 0.44) > 0.30:
                col = shadow
            else:
                continue
            cx = c * dot_w + dot_w * 0.5
            cy = r * dot_h + dot_h * 0.5
            draw.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill=col)

    return canvas


# Curated background generator list strictly containing the user's approved cloud styles
BG_GENERATORS = [
    bg_halftone_manga_clouds,  # 0: Pop-Art Halftone Screen Clouds (Reference Image 1)
    bg_screentone_clouds,  # 1: Manga Screentone Dither Clouds (Reference Image 2)
    bg_original_ascii_clouds,  # 2: Original Retro ASCII / Bayer Dither Clouds
]


def choose_bg_style_index(title: str, artist: str, track_id: str = "") -> int:
    """Deterministically select a non-repeating background style from the 3 curated styles."""
    global _LAST_STYLE_INDEX
    key = f"{title.strip().lower()}|{artist.strip().lower()}|{track_id.strip().lower()}"
    if not key.strip("|"):
        idx = 0
    else:
        h = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16)
        idx = h % len(BG_GENERATORS)

    if idx == _LAST_STYLE_INDEX and len(BG_GENERATORS) > 1:
        idx = (idx + 1) % len(BG_GENERATORS)

    _LAST_STYLE_INDEX = idx
    return idx


# ─────────────────────────────────────────────────────────────
# CUTE & ATTRACTIVE RETRO ASCII CRT TV CHASSIS
# ─────────────────────────────────────────────────────────────


def draw_cute_ascii_tv(
    canvas: Image.Image,
    tv_rect: tuple[int, int, int, int],
    screen_rect: tuple[int, int, int, int],
    scale: float,
    accent: tuple[int, int, int],
) -> None:
    """Render a charming retro ASCII CRT television with rabbit ears, dials, and tactile bezel."""
    tx, ty, tx2, ty2 = tv_rect
    tv_w, tv_h = tx2 - tx, ty2 - ty
    sx, sy, sx2, sy2 = screen_rect

    body_top = ty + int(115 * scale)
    body_bot = ty2 - int(65 * scale)
    body_left = tx + int(24 * scale)
    body_right = tx2 - int(24 * scale)
    body_radius = int(32 * scale)

    draw = ImageDraw.Draw(canvas)

    # 1. Soft ambient shadow under cabinet
    shadow_pad = int(18 * scale)
    shadow_img = Image.new("RGBA", (tv_w + shadow_pad * 2, tv_h + shadow_pad * 2), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_img)
    s_draw.rounded_rectangle(
        [
            shadow_pad + int(16 * scale),
            shadow_pad + int(120 * scale),
            shadow_pad + tv_w - int(16 * scale),
            shadow_pad + tv_h - int(55 * scale),
        ],
        radius=body_radius,
        fill=(0, 0, 0, 130),
    )
    shadow_blur = shadow_img.filter(ImageFilter.GaussianBlur(max(2, shadow_pad * 0.7)))
    canvas.paste(
        Image.alpha_composite(
            canvas.crop(
                (tx - shadow_pad, ty - shadow_pad, tx2 + shadow_pad, ty2 + shadow_pad)
            ).convert("RGBA"),
            shadow_blur,
        ).convert("RGB"),
        (tx - shadow_pad, ty - shadow_pad),
    )

    # 2. Base cabinet silhouette (rich dark charcoal / indigo with warm retro tone)
    chassis_base = (24, 26, 36)
    draw.rounded_rectangle(
        [body_left, body_top, body_right, body_bot],
        radius=body_radius,
        fill=chassis_base,
    )
    # Inner subtle cabinet highlight rim
    draw.rounded_rectangle(
        [body_left + 1, body_top + 1, body_right - 1, body_bot - 1],
        radius=body_radius - 1,
        outline=(52, 60, 78),
        width=max(1, int(1.5 * scale)),
    )

    # 3. Cute Stubby Wooden Peg Legs with dark rubber feet
    foot_bot = ty2 - int(5 * scale)
    foot_top = body_bot - int(6 * scale)
    leg_wood = (58, 46, 38)
    leg_highlight = (185, 155, 120)

    # Left leg
    draw.polygon(
        [
            (tx + int(90 * scale), foot_top),
            (tx + int(155 * scale), foot_top),
            (tx + int(120 * scale), foot_bot),
            (tx + int(55 * scale), foot_bot),
        ],
        fill=leg_wood,
        outline=leg_highlight,
    )
    draw.rectangle(
        [tx + int(55 * scale), foot_bot - 4, tx + int(120 * scale), foot_bot], fill=(18, 18, 20)
    )

    # Right leg
    draw.polygon(
        [
            (tx2 - int(155 * scale), foot_top),
            (tx2 - int(90 * scale), foot_top),
            (tx2 - int(55 * scale), foot_bot),
            (tx2 - int(120 * scale), foot_bot),
        ],
        fill=leg_wood,
        outline=leg_highlight,
    )
    draw.rectangle(
        [tx2 - int(120 * scale), foot_bot - 4, tx2 - int(55 * scale), foot_bot], fill=(18, 18, 20)
    )

    # 4. Cute Symmetrical Rabbit-Ear Antennas with Glowing Metallic Ball Tips & Signal Sparks!
    ant_cx = tx + tv_w // 2 - int(25 * scale)

    # Cute top carrying handle in center
    handle_w = int(140 * scale)
    handle_h = int(24 * scale)
    handle_top = body_top - handle_h
    draw.rounded_rectangle(
        [ant_cx - handle_w // 2, handle_top, ant_cx + handle_w // 2, body_top + 2],
        radius=int(6 * scale),
        fill=(32, 36, 48),
        outline=(85, 96, 120),
        width=max(1, int(1.5 * scale)),
    )
    # Handle rivets
    draw.ellipse(
        [ant_cx - handle_w // 2 + 4, handle_top + 4, ant_cx - handle_w // 2 + 10, handle_top + 10],
        fill=(180, 190, 210),
    )
    draw.ellipse(
        [ant_cx + handle_w // 2 - 10, handle_top + 4, ant_cx + handle_w // 2 - 4, handle_top + 10],
        fill=(180, 190, 210),
    )

    # Antenna mounts at top of cabinet (knurled chrome sockets)
    draw.rounded_rectangle(
        [
            ant_cx - int(78 * scale),
            body_top - int(8 * scale),
            ant_cx - int(52 * scale),
            body_top + 2,
        ],
        radius=2,
        fill=(115, 125, 145),
    )
    draw.rounded_rectangle(
        [
            ant_cx + int(52 * scale),
            body_top - int(8 * scale),
            ant_cx + int(78 * scale),
            body_top + 2,
        ],
        radius=2,
        fill=(115, 125, 145),
    )

    # Left antenna rod (taller, proud V-shape)
    l_top_x = ant_cx - int(140 * scale)
    l_top_y = ty + int(8 * scale)
    draw.line(
        [(ant_cx - int(65 * scale), body_top - int(6 * scale)), (l_top_x, l_top_y)],
        fill=(195, 210, 235),
        width=max(2, int(4 * scale)),
    )
    # Right antenna rod
    r_top_x = ant_cx + int(140 * scale)
    r_top_y = ty + int(8 * scale)
    draw.line(
        [(ant_cx + int(65 * scale), body_top - int(6 * scale)), (r_top_x, r_top_y)],
        fill=(195, 210, 235),
        width=max(2, int(4 * scale)),
    )

    # Metallic Golden Ball Tips (draw.ellipse with specular highlight)
    tip_r = max(5, int(8.5 * scale))
    for tx_tip, ty_tip in [(l_top_x, l_top_y), (r_top_x, r_top_y)]:
        draw.ellipse(
            [tx_tip - tip_r - 2, ty_tip - tip_r - 2, tx_tip + tip_r + 2, ty_tip + tip_r + 2],
            fill=(255, 210, 50, 140),
        )
        draw.ellipse(
            [tx_tip - tip_r, ty_tip - tip_r, tx_tip + tip_r, ty_tip + tip_r], fill=(255, 225, 75)
        )
        draw.ellipse([tx_tip - tip_r + 2, ty_tip - tip_r + 2, tx_tip, ty_tip], fill=(255, 255, 255))

    # Cute ASCII Radio Signal waves around antenna tips: * . ( (   ) ) . *
    font_signal = load_font("consolab.ttf", max(11, int(14 * scale)))
    draw.text(
        (l_top_x - int(20 * scale), l_top_y),
        "* . ( (",
        fill=(255, 230, 100),
        font=font_signal,
        anchor="rm",
    )
    draw.text(
        (r_top_x + int(20 * scale), r_top_y),
        ") ) . *",
        fill=(255, 230, 100),
        font=font_signal,
        anchor="lm",
    )

    # 5. Tactile Shaded ASCII Bezel Texture across TV Face
    cols = 72
    rows = 56
    cell_w = tv_w / float(cols)
    cell_h = tv_h / float(rows)
    font_ascii = load_font("consolab.ttf", max(10, int(cell_h * 1.05)))

    ascii_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ad = ImageDraw.Draw(ascii_layer)

    for r in range(rows):
        for c in range(cols):
            px = int(tx + c * cell_w + cell_w * 0.5)
            py = int(ty + r * cell_h + cell_h * 0.5)

            if not (body_left + 6 <= px <= body_right - 6 and body_top + 6 <= py <= body_bot - 6):
                continue
            if sx - int(6 * scale) <= px <= sx2 + int(6 * scale) and sy - int(
                6 * scale
            ) <= py <= sy2 + int(6 * scale):
                continue
            if py >= body_bot - int(38 * scale):
                continue

            dist_left = (px - body_left) / float(body_right - body_left)
            dist_top = (py - body_top) / float(body_bot - body_top)
            edge_dist = min(dist_left, 1.0 - dist_left, dist_top, 1.0 - dist_top)

            if edge_dist < 0.04:
                ch, alpha = ":", 145
            elif edge_dist < 0.08:
                ch, alpha = "=", 175
            else:
                pat = (r * 7 + c * 13) % len(ASCII_RAMP)
                ch = ASCII_RAMP[max(3, pat)]
                alpha = 195

            ad.text(
                (int(tx + c * cell_w), int(ty + r * cell_h)),
                ch,
                fill=(185, 195, 225, alpha),
                font=font_ascii,
            )

    canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), ascii_layer).convert("RGB"), (0, 0))

    # Four tactile corner screws: [ ✦ ]
    font_screw = load_font("consolab.ttf", max(10, int(12 * scale)))
    screw_pad = int(14 * scale)
    for scr_x, scr_y in [
        (body_left + screw_pad, body_top + screw_pad),
        (body_right - screw_pad, body_top + screw_pad),
        (body_left + screw_pad, body_bot - screw_pad),
        (body_right - screw_pad, body_bot - screw_pad),
    ]:
        draw.ellipse(
            [scr_x - 7, scr_y - 7, scr_x + 7, scr_y + 7], fill=(16, 18, 24), outline=(85, 95, 120)
        )
        draw.text((scr_x, scr_y), "+", fill=(190, 205, 230), font=font_screw, anchor="mm")

    # 6. Cute Symmetrical Top Bezel Badges (framing the antenna sockets)
    banner_y = body_top + int(16 * scale)
    badge_font = load_font("consolab.ttf", max(9, int(11 * scale)))
    draw.text(
        (sx + int(70 * scale), banner_y),
        "[ * RETRO-CRT * ]",
        fill=(185, 200, 230),
        font=badge_font,
        anchor="mm",
    )
    draw.text(
        (sx2 - int(70 * scale), banner_y),
        "[ * MODEL 84-HD * ]",
        fill=(185, 200, 230),
        font=badge_font,
        anchor="mm",
    )

    # 7. Cute Right-Side Control Panel (Dials, Power LED, Speaker Louvers, AUX)
    ctrl_cx = sx2 + (body_right - sx2) // 2
    font_knob = load_font("consolab.ttf", max(10, int(11 * scale)))

    # Channel Dial (CH)
    dial1_cy = body_top + int(82 * scale)
    dial_r = int(26 * scale)
    draw.ellipse(
        [ctrl_cx - dial_r - 3, dial1_cy - dial_r - 3, ctrl_cx + dial_r + 3, dial1_cy + dial_r + 3],
        fill=(14, 16, 22),
    )
    draw.ellipse(
        [ctrl_cx - dial_r, dial1_cy - dial_r, ctrl_cx + dial_r, dial1_cy + dial_r],
        fill=(38, 42, 56),
        outline=(160, 175, 205),
        width=max(1, int(1.5 * scale)),
    )
    draw.line(
        [ctrl_cx, dial1_cy - dial_r + int(4 * scale), ctrl_cx, dial1_cy - int(6 * scale)],
        fill=(255, 255, 255),
        width=max(2, int(2.5 * scale)),
    )
    draw.text(
        (ctrl_cx, dial1_cy - dial_r - int(13 * scale)),
        "CH-04",
        fill=(210, 225, 250),
        font=font_knob,
        anchor="mm",
    )

    # Volume Dial (VOL with gauge)
    dial2_cy = dial1_cy + int(96 * scale)
    draw.ellipse(
        [ctrl_cx - dial_r - 3, dial2_cy - dial_r - 3, ctrl_cx + dial_r + 3, dial2_cy + dial_r + 3],
        fill=(14, 16, 22),
    )
    draw.ellipse(
        [ctrl_cx - dial_r, dial2_cy - dial_r, ctrl_cx + dial_r, dial2_cy + dial_r],
        fill=(38, 42, 56),
        outline=(160, 175, 205),
        width=max(1, int(1.5 * scale)),
    )
    draw.line(
        [
            ctrl_cx - int(4 * scale),
            dial2_cy - dial_r + int(6 * scale),
            ctrl_cx + int(8 * scale),
            dial2_cy - int(4 * scale),
        ],
        fill=(255, 255, 255),
        width=max(2, int(2.5 * scale)),
    )
    draw.text(
        (ctrl_cx, dial2_cy - dial_r - int(13 * scale)),
        "VOL",
        fill=(210, 225, 250),
        font=font_knob,
        anchor="mm",
    )

    # Cute Power Switch & Vibrant Phosphor Green LED with Soft Luminous Halo
    pwr_y = dial2_cy + int(60 * scale)
    draw.rounded_rectangle(
        [
            ctrl_cx - int(15 * scale),
            pwr_y - int(9 * scale),
            ctrl_cx + int(15 * scale),
            pwr_y + int(9 * scale),
        ],
        radius=int(3 * scale),
        fill=(16, 18, 24),
        outline=(120, 130, 155),
        width=1,
    )
    draw.text(
        (ctrl_cx, pwr_y),
        "POWER",
        fill=(200, 210, 235),
        font=load_font("consolab.ttf", max(8, int(9 * scale))),
        anchor="mm",
    )

    led_y = pwr_y + int(24 * scale)
    led_r = max(4, int(5 * scale))
    draw.ellipse(
        [ctrl_cx - led_r - 4, led_y - led_r - 4, ctrl_cx + led_r + 4, led_y + led_r + 4],
        fill=(20, 160, 80),
    )
    draw.ellipse(
        [ctrl_cx - led_r, led_y - led_r, ctrl_cx + led_r, led_y + led_r], fill=(50, 255, 140)
    )
    draw.ellipse([ctrl_cx - 2, led_y - 2, ctrl_cx + 2, led_y + 2], fill=(200, 255, 230))
    draw.text(
        (ctrl_cx + int(16 * scale), led_y),
        "ON",
        fill=(50, 255, 140),
        font=load_font("consolab.ttf", max(8, int(9 * scale))),
        anchor="lm",
    )

    # Speaker Louver Grille (8 horizontal slots)
    speaker_top = led_y + int(28 * scale)
    slot_w = int(54 * scale)
    slot_gap = max(5, int(8 * scale))
    slot_h = max(2, int(2.5 * scale))
    for i in range(8):
        sy_slot = speaker_top + i * slot_gap
        draw.rounded_rectangle(
            [ctrl_cx - slot_w // 2, sy_slot, ctrl_cx + slot_w // 2, sy_slot + slot_h],
            radius=1,
            fill=(14, 16, 22),
        )

    # Cute AUX / Headphone jack
    aux_y = speaker_top + 8 * slot_gap + int(10 * scale)
    draw.ellipse(
        [ctrl_cx - 5, aux_y - 5, ctrl_cx + 5, aux_y + 5], fill=(10, 12, 16), outline=(90, 100, 120)
    )
    draw.text(
        (ctrl_cx, aux_y + int(10 * scale)),
        "PHONES",
        fill=(150, 160, 185),
        font=load_font("consolab.ttf", max(7, int(8 * scale))),
        anchor="mm",
    )

    # 8. Thick 3D Molded CRT Picture Tube Bezel (Deep recessed frame)
    bezel_pad = int(14 * scale)
    # Outer bezel chassis border
    draw.rounded_rectangle(
        [sx - bezel_pad, sy - bezel_pad, sx2 + bezel_pad, sy2 + bezel_pad],
        radius=int(30 * scale),
        fill=(14, 16, 22),
        outline=(75, 85, 105),
        width=max(1, int(1.5 * scale)),
    )
    # Angled inner bevel rim (catches ambient highlight on top-left, shadow on bottom-right)
    draw.rounded_rectangle(
        [sx - bezel_pad + 2, sy - bezel_pad + 2, sx2 + bezel_pad - 2, sy2 + bezel_pad - 2],
        radius=int(28 * scale),
        outline=(32, 36, 48),
        width=max(2, int(3 * scale)),
    )
    # Inner rubber gasket holding the glass tube
    draw.rounded_rectangle(
        [sx - 2, sy - 2, sx2 + 2, sy2 + 2],
        radius=int(26 * scale),
        outline=(10, 12, 16),
        width=2,
    )

    # 9. Cute Retro Brand Stamp & Player Control Bar at Bottom
    brand_y = body_bot - int(18 * scale)
    draw.text(
        (tx + (tx2 - tx) // 2, brand_y),
        "[ ◄◄ REW ]  [ ▶ PLAY ]  [ ►► FWD ]  [ ■ STOP ]   * OTOWALL COLOR CRT-84 *",
        fill=(180, 195, 225),
        font=load_font("consolab.ttf", max(9, int(11 * scale))),
        anchor="mm",
    )


def compose_wallpaper(
    cover: Image.Image,
    *,
    title: str = "",
    artist: str = "",
    width: int = 1920,
    height: int = 1080,
    bg_style_index: int | None = None,
) -> Image.Image:
    """Compose the retro ASCII CRT TV wallpaper with curated cloud backgrounds."""
    sky_color, cloud_shadow, cloud_light, accent = extract_cover_palette(cover)

    if bg_style_index is not None:
        style_idx = bg_style_index % len(BG_GENERATORS)
    else:
        style_idx = choose_bg_style_index(title, artist)

    bg_gen = BG_GENERATORS[style_idx]
    seed = (style_idx * 137 + 101) % 9999
    wallpaper = bg_gen(width, height, sky_color, cloud_shadow, cloud_light, accent, seed)

    scale = min(width / 1920.0, height / 1080.0)
    tv_w = int(840 * scale)
    tv_h = int(870 * scale)
    tv_x = (width - tv_w) // 2
    tv_y = (height - tv_h) // 2 + int(10 * scale)
    tv_rect = (tv_x, tv_y, tv_x + tv_w, tv_y + tv_h)

    body_top = tv_y + int(115 * scale)
    body_bot = tv_y + tv_h - int(65 * scale)
    body_left = tv_x + int(24 * scale)
    body_right = tv_x + tv_w - int(24 * scale)

    screen_left = body_left + int(44 * scale)
    screen_top = body_top + int(36 * scale)
    screen_right = body_right - int(146 * scale)
    screen_bot = body_bot - int(38 * scale)
    screen_rect = (screen_left, screen_top, screen_right, screen_bot)

    draw_cute_ascii_tv(wallpaper, tv_rect, screen_rect, scale, accent)

    sc_w = screen_right - screen_left
    sc_h = screen_bot - screen_top

    # 1. Scale & center-crop cover art to fill entire CRT screen
    scale_c = max(sc_w / cover.width, sc_h / cover.height)
    cw = max(1, int(round(cover.width * scale_c)))
    ch = max(1, int(round(cover.height * scale_c)))
    full_cover = cover.convert("RGB").resize((cw, ch), Image.Resampling.LANCZOS)
    cl = (cw - sc_w) // 2
    ct = (ch - sc_h) // 2
    screen_base = full_cover.crop((cl, ct, cl + sc_w, ct + sc_h))

    # 2. Barrel distortion: physical convex curvature of the glass picture tube
    arr = np.array(screen_base, dtype=float)
    y, x = np.indices((sc_h, sc_w), dtype=float)
    u = (2.0 * x - (sc_w - 1)) / float(sc_w)
    v = (2.0 * y - (sc_h - 1)) / float(sc_h)
    r2 = u**2 + v**2
    k = 0.08
    factor = 1.0 + k * r2
    src_x = np.clip((u * factor * sc_w + (sc_w - 1)) / 2.0, 0, sc_w - 1)
    src_y = np.clip((v * factor * sc_h + (sc_h - 1)) / 2.0, 0, sc_h - 1)

    x0 = np.floor(src_x).astype(int)
    x1 = np.minimum(x0 + 1, sc_w - 1)
    y0 = np.floor(src_y).astype(int)
    y1 = np.minimum(y0 + 1, sc_h - 1)
    wx = (src_x - x0)[:, :, None]
    wy = (src_y - y0)[:, :, None]

    wa = (1.0 - wx) * (1.0 - wy)
    wb = wx * (1.0 - wy)
    wc = (1.0 - wx) * wy
    wd = wx * wy
    curved_arr = wa * arr[y0, x0] + wb * arr[y0, x1] + wc * arr[y1, x0] + wd * arr[y1, x1]

    # 3. CRT Radial Vignette: natural edge & corner phosphor light falloff
    vig = np.clip(1.0 - 0.32 * r2, 0.45, 1.0)[:, :, None]
    curved_arr *= vig

    # 4. RGB Phosphor Aperture Grille: subtle vertical subpixel phosphor triads
    rgb_mask = np.ones((sc_h, sc_w, 3), dtype=float)
    for c_idx in range(3):
        rgb_mask[:, c_idx::3, c_idx] = 1.05
        rgb_mask[:, (c_idx + 1) :: 3, c_idx] = 0.95
    curved_arr = np.clip(curved_arr * rgb_mask, 0, 255)

    # 5. Horizontal Raster Scanlines: authentic electron beam scanlines
    scan_mask = np.ones((sc_h, sc_w, 1), dtype=float)
    for row in range(0, sc_h, 3):
        scan_mask[row, :, 0] = 0.78
    curved_arr = np.clip(curved_arr * scan_mask, 0, 255)

    screen_canvas = Image.fromarray(curved_arr.astype(np.uint8)).convert("RGBA")

    # 6. Deep Recessed Inner Bezel Shadow (ambient occlusion inside the tube housing)
    inner_shadow = Image.new("RGBA", (sc_w, sc_h), (0, 0, 0, 0))
    is_d = ImageDraw.Draw(inner_shadow)
    sh_depth = int(24 * scale)
    for i in range(sh_depth):
        t = i / float(sh_depth)
        alpha = int(140 * (1.0 - t) ** 1.4)
        is_d.rounded_rectangle(
            [i, i, sc_w - 1 - i, sc_h - 1 - i],
            radius=int(22 * scale) - i // 2,
            outline=(0, 0, 0, alpha),
        )
    screen_canvas = Image.alpha_composite(screen_canvas, inner_shadow)

    # 7. Curved Glass Reflections (ambient room glare + specular highlight arc)
    glare_layer = Image.new("RGBA", (sc_w, sc_h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glare_layer)
    gd.ellipse(
        [int(-sc_w * 0.2), int(-sc_h * 0.2), int(sc_w * 0.85), int(sc_h * 0.70)],
        fill=(255, 255, 255, 24),
    )
    gd.arc(
        [int(12 * scale), int(12 * scale), int(sc_w * 0.75), int(sc_h * 0.75)],
        start=180,
        end=270,
        fill=(255, 255, 255, 55),
        width=max(2, int(4 * scale)),
    )
    glare_blur = glare_layer.filter(ImageFilter.GaussianBlur(max(2, int(5 * scale))))
    screen_canvas = Image.alpha_composite(screen_canvas, glare_blur)

    # 8. Vintage CRT On-Screen Display (OSD) in Top-Left: Glowing Green Phosphor
    font_osd = load_font("consolab.ttf", max(10, int(13 * scale)))
    font_osd_sm = load_font("consolab.ttf", max(8, int(10 * scale)))
    osd_layer = Image.new("RGBA", (sc_w, sc_h), (0, 0, 0, 0))
    od = ImageDraw.Draw(osd_layer)
    osd_x = int(22 * scale)
    osd_y = int(20 * scale)
    od.text((osd_x + 1, osd_y + 1), "CH-04  STEREO", fill=(0, 0, 0, 200), font=font_osd)
    od.text((osd_x, osd_y), "CH-04  STEREO", fill=(60, 255, 140, 230), font=font_osd)
    od.text(
        (osd_x + 1, osd_y + int(16 * scale) + 1),
        "REC ● PLAY",
        fill=(0, 0, 0, 180),
        font=font_osd_sm,
    )
    od.text(
        (osd_x, osd_y + int(16 * scale)), "REC ● PLAY", fill=(50, 240, 130, 210), font=font_osd_sm
    )
    screen_canvas = Image.alpha_composite(screen_canvas, osd_layer)

    # 9. Clean Lower-Third Frosted Acrylic Song Card with subtle glass bevel
    clean_title = (title or "").strip()
    clean_artist = (artist or "").strip()

    if clean_title or clean_artist:
        card_h = int(78 * scale)
        card_w = int(sc_w - int(48 * scale))
        card_x = (sc_w - card_w) // 2
        card_y = sc_h - card_h - int(18 * scale)

        card_layer = Image.new("RGBA", (sc_w, sc_h), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card_layer)
        cd.rounded_rectangle(
            [card_x, card_y, card_x + card_w, card_y + card_h],
            radius=int(10 * scale),
            fill=(10, 12, 18, 205),
            outline=(120, 140, 175, 110),
            width=1,
        )

        font_title = load_font("Inter-Bold.ttf", max(14, int(20 * scale)))
        font_artist = load_font("Inter-Medium.ttf", max(11, int(14 * scale)))

        cd.text(
            (sc_w // 2 + 1, card_y + int(24 * scale) + 1),
            clean_title,
            fill=(0, 0, 0, 220),
            font=font_title,
            anchor="mm",
        )
        cd.text(
            (sc_w // 2, card_y + int(24 * scale)),
            clean_title,
            fill=(255, 255, 255, 255),
            font=font_title,
            anchor="mm",
        )

        cd.text(
            (sc_w // 2 + 1, card_y + int(50 * scale) + 1),
            clean_artist,
            fill=(0, 0, 0, 200),
            font=font_artist,
            anchor="mm",
        )
        cd.text(
            (sc_w // 2, card_y + int(50 * scale)),
            clean_artist,
            fill=(185, 210, 240, 240),
            font=font_artist,
            anchor="mm",
        )

        screen_canvas = Image.alpha_composite(screen_canvas, card_layer)

    # 10. Bulbous Pillow Screen Mask
    screen_mask = Image.new("L", (sc_w, sc_h), 0)
    ImageDraw.Draw(screen_mask).rounded_rectangle(
        [0, 0, sc_w, sc_h], radius=int(26 * scale), fill=255
    )

    wall_rgba = wallpaper.convert("RGBA")
    screen_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    screen_layer.paste(screen_canvas, (screen_left, screen_top), screen_mask)
    wall_rgba = Image.alpha_composite(wall_rgba, screen_layer)

    return wall_rgba.convert("RGB")


# Backward compatibility and aliases
compose_ascii_crt_wallpaper = compose_wallpaper


def generate_dither_clouds(
    width: int,
    height: int,
    sky_color: tuple[int, int, int],
    cloud_shadow: tuple[int, int, int],
    cloud_light: tuple[int, int, int],
    seed: int = 101,
) -> Image.Image:
    """Backward compatibility wrapper for default cloud background."""
    accent = (40, 180, 240)
    return bg_original_ascii_clouds(
        width, height, sky_color, cloud_shadow, cloud_light, accent, seed
    )
