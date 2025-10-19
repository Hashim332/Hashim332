## SVG and ASCII guide (fidelity-preserving, non-code workflow)

This guide explains how to preserve the exact typography, spacing, and colors of your SVGs while only swapping in new content (ASCII block and metric values). It avoids code-driven layout, so your design stays pixel-precise.

### What you’ll create

- **Master SVGs**: `reference/dark_mode.master.svg` and `reference/light_mode.master.svg`
  - They contain all layout, styles, and text objects.
  - They have stable placeholder IDs so you can update content without touching styles.

Reference repo: [Andrew6rant (fork)](https://github.com/Hashim332/Andrew6rant)

---

## 1) Design your master SVGs in Inkscape/Illustrator

1. Open your existing `dark_mode.svg` and `light_mode.svg` in Inkscape (or Illustrator).
2. Create one text object for the ASCII block:
   - Use a monospaced font and set exact font size, fill color, and line spacing.
   - Set `xml:space="preserve"` on the text node (Inkscape: Text → XML Editor → add attribute).
   - Give it `id="ascii_text"`.
   - Make the text box wide enough to avoid wrapping and tall enough for exactly 25 lines.
3. For metrics on the right, keep your existing labels and styling, but put the dynamic value in a `tspan` with a stable id so it inherits your styles. Common ids you may want:
   - `age_data`, `age_data_dots`
   - `follower_data`, `follower_data_dots`
   - `commit_data`, `commit_data_dots`
   - `star_data`, `star_data_dots`
   - `repo_data`, `repo_data_dots`
   - `contrib_data`
   - `loc_data`, `loc_data_dots`, `loc_add`, `loc_del`, `loc_del_dots`
4. Save as:
   - `reference/dark_mode.master.svg`
   - `reference/light_mode.master.svg`

Tips

- Keep styles inline (avoid external CSS). Don’t convert text to paths.
- If you need absolute cross-platform fidelity, embed a webfont via `@font-face` (data URI) and keep a robust monospace fallback stack.

---

## 2) Fill placeholders without altering layout

Pick one of these approaches. All of them preserve your exact typography/colors.

### Option A — Manual (zero tooling)

1. Open the master SVG.
2. Paste your 25-line ASCII content directly into the `ascii_text` box.
3. Update metric `tspan` values by hand.
4. Save As final `dark_mode.svg` / `light_mode.svg` (keep masters unchanged).

### Option B — Token file + text replace

1. In your master SVG, put literal tokens where content should go, e.g. `@@ASCII@@`, `@@AGE@@`, `@@FOLLOWERS@@`.
2. Ensure the ASCII node has `xml:space="preserve"` so newlines render correctly.
3. Use a text editor search/replace to swap tokens with your content. For ASCII, paste multi-line text directly.

### Option C — Minimal XML-aware replacement

Use an XML editor to replace only text nodes by id (keeps all styling):

```bash
# Example using xmlstarlet (install with your package manager)
ASCII_ESCAPED=$(perl -0777 -pe 's/&/&amp;/g; s/</&lt;/g; s/>/&gt;/g; s/\r?\n/&#10;/g' /home/hashim/projects/Hashim332/25charascii)

xmlstarlet ed \
  -u "//*[@id='ascii_text']" -v "$ASCII_ESCAPED" \
  -u "//*[@id='age_data']" -v "$AGE_DATA" \
  -u "//*[@id='follower_data']" -v "$FOLLOWERS" \
  reference/dark_mode.master.svg > dark_mode.svg
```

Notes

- Replace only text values; don’t add/remove nodes.
- Prepare a 25-line ASCII file at `/home/hashim/projects/Hashim332/25charascii`. Lines will render as-is.

---

## 3) Optional: Minify with SVGO while preserving IDs/whitespace

`svgo.config.json`:

```json
{
  "multipass": true,
  "plugins": [
    {
      "name": "preset-default",
      "params": {
        "overrides": {
          "cleanupIDs": false,
          "removeUnknownsAndDefaults": false,
          "minifyStyles": false,
          "convertShapeToPath": false,
          "mergePaths": false
        }
      }
    },
    { "name": "removeViewBox", "active": false }
  ]
}
```

Run:

```bash
svgo --config=svgo.config.json dark_mode.svg
svgo --config=svgo.config.json light_mode.svg
```

---

## 4) Practical ASCII rendering tips

- Use a single `<text id="ascii_text" xml:space="preserve">` node with line breaks, not 25 separate nodes.
- Control line spacing in the design tool (consistent across renderers).
- Ensure the text box is wide enough to prevent wraps; adjust `letter-spacing` if needed.
- If GitHub’s preview shifts slightly, increase line spacing by a small amount until it matches your live rendering.

---

## 5) Light automation (optional)

If you want daily updates without code-driven layout changes:

- Keep your master SVGs as the source of truth.
- A small cron/CI step can run the XML-aware replacements (Option C) using current data.
- Commit the generated `dark_mode.svg` / `light_mode.svg` as artifacts for your README.

You can also continue using your existing Python for data fetching only and pipe the values into the XML replacement step, instead of letting Python alter the DOM layout.

---

## Checklist

- Master SVGs saved in `reference/` with:
  - `id="ascii_text"` on a single `<text>` node with `xml:space="preserve"`.
  - `tspan` ids for values: `age_data`, `follower_data`, etc. (see list above).
- 25-line ASCII text file ready.
- Replacement method chosen (A/B/C).
- Optional SVGO pass completed.
