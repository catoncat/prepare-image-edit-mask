---
name: use-image-edit-mask
description: Teach image-edit mask usage. Use when a customer asks how to create or export a mask, check whether its transparent direction is correct, submit it with an image edit, or troubleshoot edits affecting the wrong area.
---

# Use Image Edit Mask

Teach the customer to prepare and check a mask themselves. Adapt the explanation to their image, intended edit, software, and technical level.

## Teaching Workflow

1. Establish the customer's example.
   - Identify the source image, what should change, what must remain, and the software used to prepare the mask.
   - For complex subjects such as hair, clothing, products, people, holes, reflections, or overlapping objects, refer to the real selected pixels rather than reducing the example to a geometric shape.
   - Complete when the editable and protected regions are unambiguous.

2. Explain the mental model using the customer's example:

   ```text
   transparent mask pixels = editable
   opaque mask pixels      = protected
   partial alpha           = soft transition
   ```

   Alpha transparency controls the edit. Black and white RGB colors alone do not.
   - Complete when the customer can state which part of their image should be transparent.

3. Give software-specific creation steps. Use the actual application's terminology when known; otherwise use these portable actions:
   - Create a document or layer with exactly the source image's pixel dimensions.
   - Start with the whole mask fully opaque.
   - Select the real region to edit with the application's brush, selection, path, subject-selection, or layer-mask tools.
   - Clear that selected region to transparency. Preserve partial alpha around hair, fur, glass, motion blur, or feathered edges when appropriate.
   - Export as PNG with transparency enabled. Recommend converting the source to PNG as well so the pair has the same format and dimensions.
   - Complete when the customer has a PNG whose intended edit region is transparent.

4. Teach visual self-checking before submission.
   - View the mask over a checkerboard or place a bright temporary color behind it so transparent pixels are visible.
   - Also preview the editable region as a colored overlay on top of the source image. The overlay must cover exactly what the customer intends to change.
   - Opening a transparent PNG against a white background may look blank; treat that appearance as inconclusive.
   - When a concrete demonstration would help and a Python environment with Pillow is available, run `scripts/show_mask.py`. It reads the pair and produces a red-overlay preview plus alpha statistics; it does not rewrite either input.
   - Complete when the customer can visibly distinguish editable and protected regions without guessing.

5. Explain submission:
   - `image`: the source PNG.
   - `mask`: the same-size mask PNG.
   - `prompt`: describe the desired final content in the editable region and what should remain stable.
   - Complete when each file and its role are named correctly.

6. Diagnose the observed result with the troubleshooting table, then return to the relevant earlier step.

## Troubleshooting

| Observation | Likely cause | Customer action |
|---|---|---|
| Nothing changes | Mask is fully opaque | Make the intended edit region transparent |
| The whole image changes | Mask is fully transparent or missing | Restore opacity outside the intended region |
| The opposite region changes | Input convention was reversed | Swap which pixels are transparent and opaque |
| Mask looks blank in a viewer | Viewer uses a white background | Inspect it over a checkerboard or colored background |
| Edges look harsh | Selection has a hard alpha edge | Feather only the boundary that needs a soft transition |
| Hair, holes, or overlap are wrong | The pixel selection is inaccurate | Refine the selection in the authoring software |
| Service rejects the pair | Dimensions, format, size, or alpha channel is invalid | Export both as same-size PNG files with mask transparency |

## Customer Handoff

End with a short, image-specific checklist instead of a generic API lecture:

```text
[ ] The transparent area is exactly what I want changed.
[ ] Everything I want preserved is opaque.
[ ] Source and mask are same-size PNG files.
[ ] Transparency is visible on a checkerboard or overlay preview.
[ ] The prompt describes the desired replacement or change.
```

State that a mask guides the model but does not guarantee a mathematically exact pixel boundary.

## Optional Demonstration

```bash
$MASK_PYTHON scripts/show_mask.py \
  --source source.png \
  --mask mask.png \
  --preview mask-preview.png \
  --report mask-report.json
```

Set `MASK_PYTHON` to an interpreter for which `import PIL` succeeds. In Codex App, use the workspace-dependencies tool to locate the bundled Python. The teaching workflow remains usable without this script.
