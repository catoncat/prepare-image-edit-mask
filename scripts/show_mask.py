#!/usr/bin/env python3
"""Render an edit-area preview without modifying the source or mask."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    print("Pillow is required to render the optional mask preview.", file=sys.stderr)
    raise SystemExit(3)


def load_image(path: Path) -> Image.Image:
    try:
        with Image.open(path) as image:
            image.load()
            return ImageOps.exif_transpose(image).copy()
    except (OSError, ValueError) as error:
        raise ValueError(f"cannot read {path}: {error}") from error


def alpha_statistics(alpha: Image.Image) -> dict[str, int | float]:
    histogram = alpha.histogram()
    total = alpha.width * alpha.height
    transparent = histogram[0]
    opaque = histogram[255]
    partial = total - transparent - opaque

    def percent(value: int) -> float:
        return round(value * 100 / total, 4) if total else 0.0

    return {
        "total_pixels": total,
        "transparent_pixels": transparent,
        "transparent_percent": percent(transparent),
        "partial_pixels": partial,
        "partial_percent": percent(partial),
        "opaque_pixels": opaque,
        "opaque_percent": percent(opaque),
    }


def render_preview(source: Image.Image, alpha: Image.Image) -> Image.Image:
    base = Image.new("RGBA", source.size, (255, 255, 255, 255))
    base.alpha_composite(source.convert("RGBA"))

    edit_strength = ImageOps.invert(alpha)
    overlay = Image.new("RGBA", source.size, (239, 68, 68, 0))
    overlay.putalpha(edit_strength.point(lambda value: round(value * 0.55)))
    return Image.alpha_composite(base, overlay).convert("RGB")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Show which pixels an OpenAI image-edit mask makes editable."
    )
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--mask", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    try:
        source = load_image(args.source)
        mask = load_image(args.mask)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    errors: list[str] = []
    if args.source.suffix.lower() != ".png":
        errors.append("source must be PNG")
    if args.mask.suffix.lower() != ".png":
        errors.append("mask must be PNG")
    if source.size != mask.size:
        errors.append(
            f"dimensions differ: source={source.width}x{source.height}, "
            f"mask={mask.width}x{mask.height}"
        )
    if "A" not in mask.getbands() and "transparency" not in mask.info:
        errors.append("mask has no alpha channel")

    report: dict = {
        "valid": not errors,
        "meaning": {
            "red_preview": "editable pixels",
            "alpha_0": "editable",
            "alpha_255": "protected",
        },
        "source_dimensions": [source.width, source.height],
        "mask_dimensions": [mask.width, mask.height],
        "errors": errors,
    }

    if not errors:
        alpha = mask.convert("RGBA").getchannel("A")
        report["alpha"] = alpha_statistics(alpha)
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        render_preview(source, alpha).save(args.preview, format="PNG")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
