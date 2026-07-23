# Prepare Image Edit Mask

A Codex skill that helps users prepare reliable masks for OpenAI image edits. It supports arbitrary complex pixel selections, including hair, clothing, products, holes, occlusions, and soft edges.

## Install

```bash
npx skills add catoncat/prepare-image-edit-mask --skill prepare-image-edit-mask --agent codex -g -y
```

Then ask Codex to use `$prepare-image-edit-mask` with your source image and intended edit.

## What It Does

The skill chooses the appropriate path for the user's situation:

- **Prepare**: obtain a real pixel selection through an existing mask, freehand annotation, design tool, or available segmentation tool.
- **Convert**: normalize transparent-selected, opaque-selected, white-selected, or black-selected raster conventions.
- **Verify**: render editable pixels as a red overlay and report alpha statistics before submission.
- **Teach**: give software-specific instructions when the user wants to create the mask themselves.
- **Troubleshoot**: diagnose blank masks, reversed regions, invalid dimensions, missing alpha, and inaccurate complex boundaries.

The workflow produces:

```text
source.png
mask.png
mask-preview.png
mask-report.json
```

The core contract is:

```text
alpha 0     = editable
alpha 255   = protected
alpha 1-254 = soft transition
```

## Optional Helper

[`scripts/mask_tool.py`](scripts/mask_tool.py) converts arbitrary raster selections and creates a visible preview. It does not perform semantic segmentation; object boundaries must come from a real selection, annotation, or segmentation tool.

The helper requires Python with [Pillow](https://python-pillow.org/). The skill remains usable as a teaching and orchestration workflow when Pillow is unavailable.

## License

MIT
