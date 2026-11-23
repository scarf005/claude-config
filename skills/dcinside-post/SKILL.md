---
name: dcinside-post
description: Write a DCInside gallery post as HTML for its HTML editor, with screenshots and clips served through jsDelivr from an images branch. Use when asked to write a 디시 글, a patch note, changelog or release post for a gallery such as 로그라이크 갤러리, or to update a game's post since an earlier one.
---
# DCInside post
The user posts it. Never submit to DCInside. Output: `post.html` for the HTML editor and `title.txt` for the title field.

## 1. Range
1. Read the earlier post the user names: date, title, tone, links. The range starts at the last release before that date.
2. Compare end states of data files (`git show <tag>:<file>` against current); commit subjects only find hashes. A thing
   added, then renamed or reverted, is listed as its final result.
3. Keep what a player sees; drop CI, refactoring, tests, build plumbing. Merge follow-ups. Check each number against code
   or data; no confident claim from an unclear commit subject.

## 2. Media
Capture with the repository's tool through the real game path. Stage only what makes the scene readable. Look at every
frame: an entry shows what it says.

- Crop to the thing; the page shows images at most 425 px wide, so a full 1280 px frame is unreadable.
- Frames: `magick -delay 10 -loop 0 f-*.png -crop WxH+X+Y +repage -layers optimize -quality 50 clip.webp`.
- Video: `ffmpeg -i in.mp4 -vf fps=15,scale=640:-1 -c:v libwebp -quality 50 -loop 0 clip.webp`.

## 3. Text
Write `post.txt` beside the media:

```text
# 제목

## 항목 이름
![](media/first.webp)
무엇이 바뀌었는지 한 문장
어떻게 달라지는지 조건과 수치를 붙인 문장
- 핵심 1
- 핵심 2
![](media/second.png)
## [링크 항목](https://example.com)
한 문장
```

- Largest player impact first; a small change is the `##` line and one sentence.
- Keep the earlier post's tone, else short `~함` endings. Give before and after values: `(1 -> 3)`.
- State changes concretely; a bare `수정`, `개선` or `변경` is not an entry.
- Use names the game prints; no internal names from code comments in text or media.
- Picture or clip before description; no captions, no text stamped on images ("설명보다 그림이나 영상이 훨씬 나음", "애초에 캡션을 달지 마").
- Leave out credits, contributor counts, process, promotion, hype. Run `korean-humanizer` checks on the whole text.

## 4. Publish the media and render
`cargo +nightly -Zscript ~/.config/claude/skills/dcinside-post/scripts/dc_post.rs <post.txt> <owner/repo>`

1. Converts each still to WebP (lossless if long side <= 128 px or <= 256 colours, else quality 50), keeps the smaller;
   animated WebP stays.
2. Adds files to the orphan `images` branch of the public repository under content-hash names and pushes.
3. Checks jsDelivr serves each URL, pinned to the commit (DCInside deletes GitHub image URLs). Writes `post.html`, `title.txt`.

The push goes to the user's own repository; ask first if it belongs to someone else. Git LFS fails: jsDelivr serves the
pointer text.

## 5. Check
Read `post.html` (each line `<p>`, entry gap `<p><br></p>` and `<p><b><br></b></p>`). Open each image URL once and look
at it. Report the paths of `post.html` and `title.txt`; print the title.
