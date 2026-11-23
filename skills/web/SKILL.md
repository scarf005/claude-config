---
name: web
description: Checklist for building or deploying a public web page or site (static site, Vite app, GitHub Pages). Use when creating a web project, publishing it, or reviewing its index.html head.
---

# Web page checklist

- Head metadata in `index.html`: `<title>`, `description`, Open Graph (`og:type`, `og:title`, `og:description`, `og:url`,
  `og:image` + `og:image:width`/`height`) and `twitter:card=summary_large_image`.
- `og:image` and `og:url` are absolute public URLs (scrapers ignore relative ones). Image is 1200x630, taken with
  `playwright-cli` from the real app, committed as WebP quality 50 in the public dir.
- Test with `playwright-cli`. When setting up a project's test workflow, add a `prek` pre-commit hook (format, lint,
  types, tests). Deno: follow the Deno testing, snapshot and fast-check docs.
- After deploying, fetch the live URL and check the tags and that the image URL returns 200.
