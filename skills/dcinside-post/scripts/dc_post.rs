#!/usr/bin/env -S cargo +nightly -Zscript
---
[package]
edition = "2024"
[dependencies]
sha2 = "0.10"
---
//! Renders a post to the HTML for the DCInside HTML editor and serves its media through jsDelivr.
//! Usage: dc_post.rs <post.txt> <owner/repo>
//! Writes post.html and title.txt next to post.txt. Local media goes to the orphan `images` branch of the
//! public repository under a content-hash name, and each URL pins the commit. An http line stays as it is.

use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::{env, fs};

const BRANCH: &str = "images";
const QUALITY: &str = "50";
const PIXEL_ART_SIDE: u32 = 128;
const PIXEL_ART_COLOURS: u32 = 256;

fn run(cmd: &mut Command) -> Vec<u8> {
    let out = cmd.stderr(Stdio::inherit()).output().expect("spawn");
    assert!(out.status.success(), "failed: {cmd:?}");
    out.stdout
}

fn escape(text: &str) -> String {
    text.replace('&', "&amp;").replace('<', "&lt;").replace('>', "&gt;").replace('"', "&quot;")
}

/// `![caption](target)`, or `[name](url)` with no leading `!`.
fn link(line: &str) -> Option<(&str, &str)> {
    let (name, rest) = line.strip_prefix('[')?.split_once("](")?;
    let target = rest.strip_suffix(')')?;
    let clean = !target.is_empty() && !target.contains(|c: char| c.is_whitespace() || c == ')');
    (clean && !name.contains(']')).then_some((name, target))
}

fn image(line: &str) -> Option<(&str, &str)> {
    link(line.strip_prefix('!')?)
}

fn render(lines: &[&str], urls: &HashMap<&str, String>) -> String {
    let mut html = Vec::new();
    for line in lines.iter().filter(|l| !l.starts_with("# ")) {
        if let Some(heading) = line.strip_prefix("## ") {
            if !html.is_empty() {
                html.push("<p><br></p>\n<p><b><br></b></p>".to_string());
            }
            html.push(match link(heading) {
                Some((name, url)) => format!(
                    "<p><b><a href=\"{}\" target=\"_blank\">{}</a></b></p>",
                    escape(url),
                    escape(name)
                ),
                None => format!("<p><b>{}</b></p>", escape(heading)),
            });
        } else if let Some((caption, target)) = image(line) {
            let url = urls.get(target).map_or(target, String::as_str);
            html.push(format!(
                "<p><img src=\"{}\" alt=\"{}\" style=\"max-width:425px;height:auto;\"></p>",
                escape(url),
                escape(caption)
            ));
            if !caption.is_empty() {
                html.push(format!("<p>▲ {}</p>", escape(caption)));
            }
        } else if let Some(bullet) = line.strip_prefix("- ") {
            html.push(format!("<p>• {}</p>", escape(bullet)));
        } else {
            html.push(format!("<p>{}</p>", escape(line)));
        }
    }
    html.join("\n") + "\n"
}

/// The WebP copy of a still, or nothing when ImageMagick cannot encode it (beyond the WebP size limit).
fn webp(path: &Path) -> Option<Vec<u8>> {
    let id = Command::new("magick").args(["identify", "-format", "%w %h %k"]).arg(format!("{}[0]", path.display())).output().ok()?;
    let id: Vec<u32> = String::from_utf8(id.stdout).ok()?.split(' ').filter_map(|n| n.parse().ok()).collect();
    let pixel_art = *id.first()?.max(id.get(1)?) <= PIXEL_ART_SIDE || *id.get(2)? <= PIXEL_ART_COLOURS;
    let mode: &[&str] = if pixel_art { &["-define", "webp:lossless=true"] } else { &["-quality", QUALITY] };
    let out = Command::new("magick").arg(path).args(mode).arg("webp:-").output().ok()?;
    out.status.success().then_some(out.stdout)
}

/// The bytes to publish and their extension: a still as WebP when that is smaller, lossless for
/// pixel art (small or palette-sized, where lossy blurs it), an animated WebP untouched.
fn compress(path: &Path) -> (Vec<u8>, String) {
    let bytes = fs::read(path).expect("read media");
    let ext = path.extension().unwrap().to_string_lossy().to_string();
    if ext == "webp" {
        return (bytes, ext);
    }
    match webp(path) {
        Some(webp) if webp.len() < bytes.len() => (webp, "webp".into()),
        _ => (bytes, ext),
    }
}

/// A folder that goes when it leaves scope, on a panic too.
struct TempDir(PathBuf);

impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

fn publish(targets: &[(&str, PathBuf)], repo: &str) -> HashMap<String, String> {
    let temp = TempDir(env::temp_dir().join(format!("dc-post-{}", std::process::id())));
    let dir = &temp.0;
    let remote = format!("https://github.com/{repo}.git");
    let git = |args: &[&str]| run(Command::new("git").arg("-C").arg(dir).args(args));
    let has_branch = !run(Command::new("git").args(["ls-remote", &remote, &format!("refs/heads/{BRANCH}")])).is_empty();
    if has_branch {
        run(Command::new("git").args(["clone", "--quiet", "--depth", "1", "--branch", BRANCH, &remote]).arg(dir));
    } else {
        fs::create_dir_all(dir).unwrap();
        git(&["init", "--quiet", "--initial-branch", BRANCH]);
        git(&["remote", "add", "origin", &remote]);
    }
    let mut names = Vec::new();
    for (target, path) in targets {
        let (bytes, ext) = compress(path);
        let name = format!("{:x}.{ext}", Sha256::digest(&bytes));
        fs::write(dir.join(&name), bytes).unwrap();
        println!("{target} -> {name}");
        names.push(((*target).to_string(), name));
    }
    git(&["add", "--all"]);
    if !git(&["status", "--porcelain"]).is_empty() {
        git(&["commit", "--quiet", "-m", "chore: add post media"]);
        git(&["push", "--quiet", "origin", &format!("HEAD:{BRANCH}")]);
    }
    let commit = String::from_utf8(git(&["rev-parse", "HEAD"])).unwrap();
    let commit = commit.trim();
    let urls = names.into_iter().map(|(target, name)| {
        let url = format!("https://cdn.jsdelivr.net/gh/{repo}@{commit}/{name}");
        run(Command::new("curl").args(["-fsSIL", "--retry", "5", "--retry-all-errors", "--retry-delay", "5", "--max-time", "60", "-o", "/dev/null", &url]));
        (target, url)
    });
    urls.collect()
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let [_, post, repo] = args.as_slice() else { panic!("usage: dc_post.rs <post.txt> <owner/repo>") };
    let post = PathBuf::from(post);
    let text = fs::read_to_string(&post).expect("read post");
    let lines: Vec<&str> = text.lines().map(str::trim).filter(|l| !l.is_empty()).collect();
    let title = lines.first().and_then(|l| l.strip_prefix("# ")).expect("first line: # title");
    assert!(lines.iter().any(|l| l.starts_with("## ")), "no ## entry");
    let base = post.parent().unwrap();
    let mut targets: Vec<(&str, PathBuf)> = Vec::new();
    for (_, target) in lines.iter().filter_map(|l| image(l)) {
        if !target.starts_with("http") && !targets.iter().any(|(t, _)| *t == target) {
            targets.push((target, base.join(target)));
        }
    }
    let published = if targets.is_empty() { HashMap::new() } else { publish(&targets, repo) };
    let urls: HashMap<&str, String> = published.iter().map(|(t, u)| (t.as_str(), u.clone())).collect();
    fs::write(base.join("post.html"), render(&lines, &urls)).unwrap();
    fs::write(base.join("title.txt"), format!("{title}\n")).unwrap();
}
