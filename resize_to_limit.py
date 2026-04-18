#!/usr/bin/env python3
"""
resize_to_limit.py
------------------
Resizes images that exceed MAX_SIZE_KB by progressively scaling their
dimensions down until the re-encoded WebP file fits within the budget.

Operates in-place on WebP files (and converts nmetab.jpg to WebP too).
No HTML changes needed — references already point to .webp after
the earlier convert_to_webp.py run.

Usage:
    py resize_to_limit.py
"""

import shutil
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

ROOT        = Path(__file__).parent / "images"
MAX_SIZE_KB = 500
WEBP_QUALITY = 82      # keep consistent with convert_to_webp.py
SCALE_STEP   = 0.85    # multiply both dimensions by this each iteration
MIN_SCALE    = 0.10    # stop if we'd go below 10% of original size

# Images to process: all .webp files, plus nmetab.jpg which never got converted
TARGET_FILES = list(ROOT.glob("*.webp")) + [ROOT / "nmetab.jpg"]

# The GIF is an animation — skip it; would need ffmpeg for proper treatment
SKIP_NAMES = {"Green_dynamics_mtStayGold_U2OS__9_MMStack_Pos0_destripped.ome-1.gif"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def size_kb(path: Path) -> int:
    return path.stat().st_size // 1024


def scale_and_save(img: Image.Image, out_path: Path, scale: float) -> int:
    """Resize *img* by *scale* and save to *out_path* as WebP. Returns file KB."""
    new_w = max(1, int(img.width  * scale))
    new_h = max(1, int(img.height * scale))
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    resized.save(out_path, "webp", quality=WEBP_QUALITY, method=6)
    return size_kb(out_path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    oversized = [
        f for f in TARGET_FILES
        if f.name not in SKIP_NAMES and f.exists() and size_kb(f) > MAX_SIZE_KB
    ]

    if not oversized:
        print("All images are already within the 500 KB limit.")
        return

    print(f"Images exceeding {MAX_SIZE_KB} KB:\n")
    for f in sorted(oversized, key=size_kb, reverse=True):
        print(f"  {f.name:<55} {size_kb(f):>6} KB")

    print(f"\nResizing to ≤ {MAX_SIZE_KB} KB …\n")

    for src in sorted(oversized, key=size_kb, reverse=True):
        before_kb = size_kb(src)

        # Determine output path (.jpg → .webp conversion for nmetab)
        out_path = src if src.suffix == ".webp" else src.with_suffix(".webp")
        tmp_path = out_path.with_suffix(".tmp.webp")

        # Backup original if it might be overwritten
        backup = src.with_name(src.stem + "_original" + src.suffix)
        if not backup.exists():
            shutil.copy2(src, backup)

        # Open original (from backup so repeated runs start from full-res)
        with Image.open(backup) as base:
            mode = "RGBA" if (base.mode in ("RGBA", "LA", "P") and src.suffix == ".png") else "RGB"
            base = base.convert(mode)
            orig_w, orig_h = base.width, base.height

            scale      = 1.0
            last_kb    = before_kb
            converged  = False

            # Estimate a starting scale using the square-root heuristic
            import math
            est_scale = math.sqrt(MAX_SIZE_KB / before_kb)
            scale = min(est_scale * 0.95, 1.0)   # start 5% below estimate

            while scale >= MIN_SCALE:
                kb = scale_and_save(base, tmp_path, scale)
                if kb <= MAX_SIZE_KB:
                    converged = True
                    break
                scale *= SCALE_STEP

            if not converged:
                tmp_path.unlink(missing_ok=True)
                print(f"  [fail]  {src.name}  — could not reach target (minimum scale hit)")
                continue

        # Commit
        tmp_path.replace(out_path)

        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        after_kb = size_kb(out_path)
        saving = (1 - after_kb / before_kb) * 100

        print(
            f"  [ok]  {src.name:<52}"
            f"  {before_kb:>5} KB → {after_kb:>4} KB  ({saving:.0f}% smaller)"
            f"   {orig_w}×{orig_h} → {new_w}×{new_h}"
        )

        # If input was jpg and output is a new webp, update HTML references
        if src.suffix != ".webp":
            _update_html(src.parent.parent, src.name, out_path.name)

    print("\nDone.  _original backups kept alongside each image.")


def _update_html(root: Path, old_name: str, new_name: str) -> None:
    """Swap the one filename that changed in all HTML files."""
    # Build partial paths as they appear in HTML: images/foo.jpg → images/foo.webp
    old_ref = f"images/{old_name}"
    new_ref = f"images/{new_name}"
    for html in root.glob("*.html"):
        text = html.read_text(encoding="utf-8")
        if old_ref in text:
            html.write_text(text.replace(old_ref, new_ref), encoding="utf-8")
            print(f"       updated {html.name}: {old_ref} → {new_ref}")


if __name__ == "__main__":
    main()
