#!/usr/bin/env python3
"""Normalize, preview, and inspect arbitrary image-edit mask selections."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    print("Pillow is required. Use a Python environment that provides PIL.", file=sys.stderr)
    raise SystemExit(3)


MODES = (
    "transparent-is-edit",
    "opaque-is-edit",
    "white-is-edit",
    "black-is-edit",
)


class ContractError(ValueError):
    pass


def load(path: Path) -> Image.Image:
    try:
        with Image.open(path) as image:
            image.load()
            return ImageOps.exif_transpose(image).copy()
    except (OSError, ValueError) as error:
        raise ContractError(f"cannot read {path}: {error}") from error


def require_png(path: Path, label: str) -> None:
    if path.suffix.lower() != ".png":
        raise ContractError(f"{label} must use a .png extension: {path}")


def has_alpha(image: Image.Image) -> bool:
    return "A" in image.getbands() or "transparency" in image.info


def selection_alpha(selection: Image.Image, mode: str) -> Image.Image:
    if mode in ("transparent-is-edit", "opaque-is-edit"):
        if not has_alpha(selection):
            raise ContractError(f"selection mode {mode} requires an alpha channel")
        alpha = selection.convert("RGBA").getchannel("A")
        return alpha if mode == "transparent-is-edit" else ImageOps.invert(alpha)

    luminance = ImageOps.grayscale(selection.convert("RGB"))
    return ImageOps.invert(luminance) if mode == "white-is-edit" else luminance


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


def preview(source: Image.Image, alpha: Image.Image) -> Image.Image:
    base = Image.new("RGBA", source.size, (255, 255, 255, 255))
    base.alpha_composite(source.convert("RGBA"))
    overlay = Image.new("RGBA", source.size, (239, 68, 68, 0))
    edit_strength = ImageOps.invert(alpha)
    overlay.putalpha(edit_strength.point(lambda value: round(value * 0.55)))
    return Image.alpha_composite(base, overlay).convert("RGB")


def save_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")


def inspect_pair(source_path: Path, mask_path: Path) -> tuple[Image.Image, Image.Image, dict]:
    source = load(source_path)
    mask = load(mask_path)
    errors: list[str] = []

    if source_path.suffix.lower() != ".png":
        errors.append("source must be PNG")
    if mask_path.suffix.lower() != ".png":
        errors.append("mask must be PNG")
    if source.size != mask.size:
        errors.append(
            f"dimensions differ: source={source.width}x{source.height}, "
            f"mask={mask.width}x{mask.height}"
        )
    if not has_alpha(mask):
        errors.append("mask must contain an alpha channel")

    alpha = mask.convert("RGBA").getchannel("A")
    stats = alpha_statistics(alpha)
    if stats["opaque_pixels"] == stats["total_pixels"]:
        errors.append("mask has no editable pixels; every pixel has alpha 255")

    warnings: list[str] = []
    if stats["opaque_pixels"] == 0:
        warnings.append("mask has no fully protected pixels; this requests a whole-image edit")

    report = {
        "valid": not errors,
        "contract": {
            "editable": "alpha=0",
            "protected": "alpha=255",
            "soft_edge": "alpha=1..254",
        },
        "source": {
            "path": str(source_path),
            "width": source.width,
            "height": source.height,
        },
        "mask": {
            "path": str(mask_path),
            "width": mask.width,
            "height": mask.height,
            **stats,
        },
        "warnings": warnings,
        "errors": errors,
    }
    return source, alpha, report


def write_report(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


def normalize(args: argparse.Namespace) -> int:
    source = load(args.source)
    selection = load(args.selection)
    if source.size != selection.size:
        raise ContractError(
            f"dimensions differ: source={source.width}x{source.height}, "
            f"selection={selection.width}x{selection.height}"
        )

    for path, label in (
        (args.output_source, "source output"),
        (args.output_mask, "mask output"),
        (args.output_preview, "preview output"),
    ):
        require_png(path, label)

    alpha = selection_alpha(selection, args.selection_mode)
    normalized_source = source.convert("RGBA")
    normalized_mask = Image.new("RGBA", source.size, (255, 255, 255, 255))
    normalized_mask.putalpha(alpha)
    save_png(normalized_source, args.output_source)
    save_png(normalized_mask, args.output_mask)

    checked_source, checked_alpha, report = inspect_pair(
        args.output_source, args.output_mask
    )
    report["selection"] = {
        "path": str(args.selection),
        "mode": args.selection_mode,
    }
    save_png(preview(checked_source, checked_alpha), args.output_preview)
    write_report(report, args.output_report)
    return 0 if report["valid"] else 2


def inspect(args: argparse.Namespace) -> int:
    require_png(args.output_preview, "preview output")
    source, alpha, report = inspect_pair(args.source, args.mask)
    if source.size == alpha.size:
        save_png(preview(source, alpha), args.output_preview)
    write_report(report, args.output_report)
    return 0 if report["valid"] else 2


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Prepare arbitrary selections for masked image editing."
    )
    commands = root.add_subparsers(dest="command", required=True)

    normalize_command = commands.add_parser("normalize")
    normalize_command.add_argument("--source", type=Path, required=True)
    normalize_command.add_argument("--selection", type=Path, required=True)
    normalize_command.add_argument("--selection-mode", choices=MODES, required=True)
    normalize_command.add_argument("--output-source", type=Path, required=True)
    normalize_command.add_argument("--output-mask", type=Path, required=True)
    normalize_command.add_argument("--output-preview", type=Path, required=True)
    normalize_command.add_argument("--output-report", type=Path, required=True)
    normalize_command.set_defaults(handler=normalize)

    inspect_command = commands.add_parser("inspect")
    inspect_command.add_argument("--source", type=Path, required=True)
    inspect_command.add_argument("--mask", type=Path, required=True)
    inspect_command.add_argument("--output-preview", type=Path, required=True)
    inspect_command.add_argument("--output-report", type=Path, required=True)
    inspect_command.set_defaults(handler=inspect)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        return args.handler(args)
    except ContractError as error:
        print(f"mask contract error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
