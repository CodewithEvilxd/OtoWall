"""Tests for retro ASCII CRT TV and dither cloud wallpaper composer."""

from __future__ import annotations

import numpy as np
from PIL import Image

from otowall.ascii_composer import (
    BG_GENERATORS,
    choose_bg_style_index,
    compose_ascii_crt_wallpaper,
    extract_cover_palette,
    generate_dither_clouds,
)
from otowall.composer import compose_wallpaper


def test_extract_cover_palette():
    img = Image.new("RGB", (64, 64), (30, 120, 210))
    sky, shadow, light, accent = extract_cover_palette(img)
    for color in (sky, shadow, light, accent):
        assert len(color) == 3
        for channel in color:
            assert 0 <= channel <= 255


def test_generate_dither_clouds():
    sky = (40, 100, 180)
    shadow = (140, 170, 210)
    light = (252, 254, 255)
    clouds = generate_dither_clouds(480, 270, sky, shadow, light, seed=42)
    assert clouds.size == (480, 270)
    assert clouds.mode == "RGB"
    arr = np.array(clouds)
    assert len(np.unique(arr)) > 2


def test_compose_ascii_crt_wallpaper():
    cover = Image.new("RGB", (300, 300), (200, 60, 40))
    wall = compose_ascii_crt_wallpaper(
        cover,
        title="Test Song",
        artist="Test Artist",
        width=960,
        height=540,
    )
    assert wall.size == (960, 540)
    assert wall.mode == "RGB"


def test_composer_delegates_to_ascii_crt():
    cover = Image.new("RGB", (200, 200), (50, 150, 200))
    wall = compose_wallpaper(
        cover,
        title="Delegated Song",
        artist="Delegated Artist",
        width=800,
        height=600,
        style="ascii_crt",
    )
    assert wall.size == (800, 600)
    assert wall.mode == "RGB"


def test_all_bg_generators_render():
    sky = (30, 90, 180)
    shadow = (120, 150, 200)
    light = (250, 250, 255)
    accent = (240, 80, 120)
    assert len(BG_GENERATORS) == 3
    for idx, gen in enumerate(BG_GENERATORS):
        bg = gen(320, 180, sky, shadow, light, accent, seed=idx + 1)
        assert bg.size == (320, 180)
        assert bg.mode == "RGB"


def test_choose_bg_style_index_non_repeating():
    idx1 = choose_bg_style_index("Song One", "Artist")
    idx2 = choose_bg_style_index("Song One", "Artist")
    # Immediate repeat changes index
    assert idx1 != idx2
    idx3 = choose_bg_style_index("Song Two", "Artist")
    assert 0 <= idx3 < len(BG_GENERATORS)
