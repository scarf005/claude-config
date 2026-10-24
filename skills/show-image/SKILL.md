---
name: show-image
description: Show image files inline in the terminal reply. Use when the user asks to show, view, preview, or display images or screenshots, or when an image is the answer.
---

# Show image

The raster-view mod draws every image path written in a reply under that message; `Read` shows nothing on screen.

- Write each image as an absolute path in the reply text: `/dir/name.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`. Spaces and Korean are fine.
- One path per line, not wrapped in a code block or link. Add one short caption line per image only when it helps.
- Use the exact path of the file to show; convert or copy only when the format is not listed (for example `ffmpeg -i in.avif /tmp/out.png`).
- Show at most about 10 images per reply; each is at most 30 rows tall.
- GIF and video show the first frame only.
