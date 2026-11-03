---
name: dcinside-post
description: Write a DCInside gallery post as HTML for its HTML editor, with screenshots and clips served through jsDelivr from an images branch. Use when asked to write a 디시 글, a patch note, changelog or release post for a gallery such as 로그라이크 갤러리, or to update a game's post since an earlier one.
---

# DCInside post

The user posts it. Never submit a post to DCInside. The result is `post.html` to paste into the HTML editor and `title.txt` for the title field.

## 1. Range

1. Read the earlier post the user names. Take its date, title, tone and links.
2. Find the last release before that date. The range starts there.
3. Compare the end states of the data files (`git show <tag>:<file>` against the current file). Use commit subjects only to find hashes. A thing added, then renamed or reverted, is listed as its final result.
4. Keep what a player sees. Drop CI, refactoring, tests and build plumbing unless a player feels the result. Merge follow-up commits into one entry.
5. Check each number against the code or the data. Never put an unclear commit subject into a confident claim.

## 2. Media

Capture with the repository's own tool, through the real game path. Stage only what makes the scene readable. Look at every frame: an entry shows what it says, such as a spell that hits.

- Crop to the thing. The page shows images at most 425 px wide, so a whole 1280 px frame turns to unreadable dots.
- Clip from frames: `magick -delay 10 -loop 0 f-*.png -crop WxH+X+Y +repage -layers optimize -quality 50 clip.webp`.
- Clip from video: `ffmpeg -i in.mp4 -vf fps=15,scale=640:-1 -c:v libwebp -quality 50 -loop 0 clip.webp`.

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

- Largest player impact first. A small change is the `##` line and one sentence.
- Keep the tone of the earlier post if there is one, else short `~함` endings.
- Give before and after values: `(1 -> 3)`.
- State what changed concretely. A bare `수정`, `개선` or `변경` is not an entry.
- Use the names the game prints. Internal names from code comments stay out of the text and the media.
- Show a change with a picture or a clip before a description. Give images no caption and stamp no text on them. User: "설명보다 그림이나 영상이 훨씬 나음", "애초에 캡션을 달지 마".
- Leave out credits, contributor counts, process, promotion and hype.
- Run the `korean-humanizer` checks on the whole text.

## 4. Publish the media and render

```sh
cargo +nightly -Zscript ~/.config/claude/skills/dcinside-post/scripts/dc_post.rs <post.txt> <owner/repo>
```

The script does these steps:

1. It converts each local still to WebP (lossless if the long side is at most 128 px or it has at most 256 colours, else quality 50) and keeps the smaller file. An animated WebP stays as it is.
2. It adds the files to the orphan `images` branch of the public repository, under content-hash names, and pushes.
3. It checks that jsDelivr serves each URL, pinned to the commit. DCInside deletes GitHub image URLs.
4. It writes `post.html` and `title.txt`.

The push goes to a branch of the user's own repository. Ask first if the repository belongs to someone else. Git LFS does not work: jsDelivr serves the pointer text.

## 5. Check

1. Read `post.html`. Each line is `<p>`, and an entry gap is `<p><br></p>` and `<p><b><br></b></p>`.
2. Open each image URL once and look at it.
3. Report the paths of `post.html` and `title.txt`, and print the title.
