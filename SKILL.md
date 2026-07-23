---
name: prepare-image-edit-mask
description: Prepare and troubleshoot masks for OpenAI image edits. Use when a user needs help selecting an edit region, creating or converting an arbitrary raster selection, validating an existing mask, learning a software-specific workflow, or diagnosing an edit that changed the wrong area.
---

# Prepare Image Edit Mask

Own the outcome: deliver or teach the user to deliver a verified image/mask pair. Run selection-first: establish real edit pixels before mechanical mask conversion.

## Workflow

1. Establish the intended edit.
   - Identify the source image, what should change, what must remain, and whether the user wants assistance or instruction.
   - Complete when editable and protected content is unambiguous.

2. Obtain an explicit pixel selection.
   - Reuse an existing mask, freehand selection, design-tool export, or segmentation output.
   - For semantic targets such as hair, clothing, products, people, reflections, holes, or overlaps, use a proven selection or segmentation tool when available. Otherwise ask the user to mark the region.
   - Preserve real boundaries and soft edges. A bounding shape is not a substitute for a complex object selection.
   - Complete when an arbitrary raster selection exists and its convention is known: transparent selected, opaque selected, white selected, or black selected.

3. Normalize the selection with `scripts/mask_tool.py normalize`.
   - `transparent-is-edit`: copy the selection alpha.
   - `opaque-is-edit`: invert the selection alpha.
   - `white-is-edit`: convert white luminance to transparent edit pixels.
   - `black-is-edit`: convert black luminance to transparent edit pixels.
   - The command writes `source.png`, `mask.png`, a red-overlay preview, and a JSON report.
   - Complete when it exits 0 and all four outputs exist.

4. Pass the preview gate with the user.
   - Red pixels are editable; uncolored pixels are protected.
   - Check complex boundaries, holes, occlusions, and feathering against the user's intent.
   - Improve the upstream selection when the boundary is wrong. Alpha conversion cannot recover a missing semantic boundary.
   - Complete when the visible overlay matches the intended edit region.

5. Validate the final pair with `scripts/mask_tool.py inspect`.
   - Complete only when `valid` is true, dimensions match, both outputs are PNG, the mask has an alpha channel, and the intended local edit includes alpha below 255.

6. Hand off the pair and submission roles.
   - `image`: `source.png`
   - `mask`: `mask.png`
   - `prompt`: describe the desired result in the editable region and what should remain stable.
   - State: "透明区域会被编辑；不透明区域会被保护。"

## Teaching Branch

When the user wants instructions instead of file preparation, adapt steps to their software:

1. Create a layer or document at the source image's exact pixel dimensions.
2. Start fully opaque.
3. Select the real edit region using brush, path, subject-selection, or layer-mask tools.
4. Clear the selection to transparency; retain partial alpha for soft boundaries.
5. Export a transparency-preserving PNG.
6. Preview it over a checkerboard and as a colored overlay on the source.

Opening a transparent PNG against a white viewer background may look blank. Alpha, not black or white RGB color, defines editability.

## Troubleshooting

| Observation | Likely cause | Action |
|---|---|---|
| Nothing changes | Mask is fully opaque | Make the intended region transparent |
| Whole image changes | Mask is fully transparent or missing | Restore opacity outside the edit region |
| Opposite region changes | Selection convention was reversed | Normalize with the matching selection mode |
| Mask looks blank | Viewer hides transparency | Use the red-overlay preview or checkerboard |
| Complex edge is wrong | Pixel selection is inaccurate | Refine selection or segmentation |
| Client claims to send a mask but none is observed | Request body may omit or rename the mask field | Capture the actual multipart request with `examples/capture-image-edit-request.js`, then inspect the downloaded files |
| Service rejects the pair | Format, dimensions, size, or alpha is invalid | Re-export a same-size PNG pair with alpha |

## Commands

Locate a Python interpreter where `import PIL` succeeds. In Codex App, use the workspace-dependencies tool to locate the bundled Python and assign it to `MASK_PYTHON`.

```bash
$MASK_PYTHON scripts/mask_tool.py normalize \
  --source INPUT_IMAGE \
  --selection INPUT_SELECTION \
  --selection-mode white-is-edit \
  --output-source source.png \
  --output-mask mask.png \
  --output-preview mask-preview.png \
  --output-report mask-report.json

$MASK_PYTHON scripts/mask_tool.py inspect \
  --source source.png \
  --mask mask.png \
  --output-preview mask-preview.png \
  --output-report mask-report.json
```

The helper requires Pillow. Request permission before installing dependencies into a user's project or global environment.

## Completion Contract

- Source and mask are same-size PNG files.
- Alpha 0 is editable, alpha 255 is protected, and alpha 1-254 is a soft transition.
- The red overlay has been compared with the user's intended region.
- The JSON report says `valid: true`.
- The user understands that a mask guides the model but does not guarantee a mathematically exact pixel boundary.
