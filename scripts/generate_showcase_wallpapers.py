import io
import json
from pathlib import Path
import urllib.parse
from PIL import Image
import requests

from otowall.ascii_composer import compose_wallpaper

out_dir = Path("docs/wallpapers")
out_dir.mkdir(parents=True, exist_ok=True)

songs = [
    {
        "query": "Liggi Ritviz",
        "title": "Liggi",
        "artist": "Ritviz",
        "style_idx": 0,
        "filename": "wallpaper_liggi_ritviz.png",
        "desc": "Pop-Art Halftone Screen Clouds",
    },
    {
        "query": "Uff Harshdeep Kaur Bang Bang",
        "title": "Uff",
        "artist": "Harshdeep Kaur",
        "style_idx": 1,
        "filename": "wallpaper_uff_bang_bang.png",
        "desc": "Manga Screentone Dither Clouds",
    },
    {
        "query": "Senorita ZNMD Farhan Akhtar",
        "title": "Senorita",
        "artist": "Farhan Akhtar",
        "style_idx": 2,
        "filename": "wallpaper_senorita_znmd.png",
        "desc": "Original Retro ASCII Bayer Dither Clouds",
    },
]

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

for s in songs:
    save_path = out_dir / s["filename"]
    if save_path.exists() and save_path.stat().st_size > 100000:
        print(f"Already exists: {save_path} ({save_path.stat().st_size} bytes)")
        continue

    url = f"https://itunes.apple.com/search?term={urllib.parse.quote(s['query'])}&entity=song&limit=1"
    resp = session.get(url, timeout=15)
    data = resp.json()
    art_url = data["results"][0]["artworkUrl100"].replace("100x100bb.jpg", "600x600bb.jpg")
    r2 = session.get(art_url, timeout=15)
    cover = Image.open(io.BytesIO(r2.content)).convert("RGB")

    wall = compose_wallpaper(cover, title=s["title"], artist=s["artist"], bg_style_index=s["style_idx"])
    wall.save(save_path)
    print(f"Generated {s['title']} ({s['desc']}) -> {save_path} ({wall.size})")

print("All showcase wallpapers generated successfully!")

