#!/usr/bin/env python3
"""
convert_to_webp.py
------------------
Scans all HTML files in the website root, finds every raster image reference
(src=, href=, url() in style attributes), converts those images to WebP, and
updates every reference in the HTML files automatically.

Requirements:
    pip install Pillow

Usage:
    python convert_to_webp.py

Notes:
  - Original images are kept; only the HTML references are rewritten.
  - Images already in WebP, SVG, or GIF format are left untouched.
  - The favicon (Logo_black.png) is kept as PNG for universal browser support.
  - Re-running the script is safe: images already converted are skipped.
"""

import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow is not installed.\nRun:  pip install Pillow")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent          # website root (where the .html files live)
WEBP_QUALITY = 82                     # 0–100; 80–85 is the recommended sweet spot
SKIP_IMAGES = {"Logo_black.png"}      # keep as PNG (favicon cross-browser compat)
CONVERT_EXTENSIONS = {".jpg", ".jpeg", ".png"}

# ---------------------------------------------------------------------------
# Image discovery
# ---------------------------------------------------------------------------

# Matches both:
#   src="images/foo.jpg"  href="images/foo.png"
#   url('images/foo.jpeg')  url("images/foo.jpg")  url(images/foo.jpg)
_REF_RE = re.compile(
    r'(?:src|href)=["\']([^"\']+\.(?:png|jpe?g))["\']'
    r'|url\(["\']?([^"\'()\s]+\.(?:png|jpe?g))["\']?\)',
    re.IGNORECASE,
)


def find_image_refs(content: str) -> set[str]:
    """Return every unique raster-image path found in an HTML string."""
    refs: set[str] = set()
    for m in _REF_RE.finditer(content):
        ref = m.group(1) or m.group(2)
        if ref:
            refs.add(ref)
    return refs


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------

def convert_to_webp(img_path: Path) -> Path | None:
    """
    Convert *img_path* to WebP next to the original.
    Returns the WebP path on success, None on failure.
    Skips silently if the WebP already exists.
    """
    webp_path = img_path.with_suffix(".webp")

    if webp_path.exists():
        size_kb = webp_path.stat().st_size // 1024
        print(f"  [skip]  {img_path.name}  (webp already exists, {size_kb} KB)")
        return webp_path

    if not img_path.exists():
        print(f"  [warn]  {img_path.name}  — file not found, skipping")
        return None

    try:
        with Image.open(img_path) as img:
            # Preserve alpha channel for PNGs that have one
            if img_path.suffix.lower() == ".png" and img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")
            img.save(webp_path, "webp", quality=WEBP_QUALITY, method=6)

        before_kb = img_path.stat().st_size // 1024
        after_kb  = webp_path.stat().st_size // 1024
        saving    = (1 - webp_path.stat().st_size / img_path.stat().st_size) * 100
        print(f"  [ok]    {img_path.name}  →  {webp_path.name}"
              f"  ({before_kb} KB → {after_kb} KB,  {saving:.0f}% smaller)")
        return webp_path

    except Exception as exc:
        print(f"  [error] {img_path.name}  — {exc}")
        return None


# ---------------------------------------------------------------------------
# HTML rewriting
# ---------------------------------------------------------------------------

def update_html_file(html_path: Path, replacements: dict[str, str]) -> int:
    """
    Replace every old image path with its WebP equivalent inside *html_path*.
    Returns the number of substitutions made.
    """
    content = html_path.read_text(encoding="utf-8")
    original = content
    count = 0

    for old, new in replacements.items():
        occurrences = content.count(old)
        if occurrences:
            content = content.replace(old, new)
            count += occurrences

    if content != original:
        html_path.write_text(content, encoding="utf-8")

    return count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    html_files = sorted(ROOT.glob("*.html"))
    if not html_files:
        print("No HTML files found in", ROOT)
        sys.exit(0)

    print(f"Root : {ROOT}")
    print(f"Files: {[f.name for f in html_files]}\n")

    # --- Step 1: collect every unique image reference across all HTML files ---
    all_refs: set[str] = set()
    for html in html_files:
        all_refs.update(find_image_refs(html.read_text(encoding="utf-8")))

    raster_refs = {
        ref for ref in all_refs
        if Path(ref).suffix.lower() in CONVERT_EXTENSIONS
    }

    print(f"Found {len(raster_refs)} unique raster image reference(s) to convert:\n")

    # --- Step 2: convert & build replacement map ---
    replacements: dict[str, str] = {}

    for ref in sorted(raster_refs):
        img_path = ROOT / ref

        if img_path.name in SKIP_IMAGES:
            print(f"  [skip]  {img_path.name}  — kept as PNG (favicon)")
            continue

        new_path = convert_to_webp(img_path)
        if new_path:
            # Keep the same directory component, just swap the extension
            new_ref = str(Path(ref).with_suffix(".webp")).replace("\\", "/")
            replacements[ref] = new_ref

    # --- Step 3: rewrite HTML files ---
    if not replacements:
        print("\nNothing to update — all images are already in WebP format.")
        return

    print(f"\nUpdating {len(html_files)} HTML file(s)…")
    total = 0
    for html in html_files:
        n = update_html_file(html, replacements)
        if n:
            print(f"  {html.name}: {n} reference(s) updated")
            total += n
        else:
            print(f"  {html.name}: no changes")

    print(f"\nAll done!  {total} reference(s) updated across {len(html_files)} file(s).")
    print("Original images are preserved — delete them once you've verified the site.")


if __name__ == "__main__":
    main()
