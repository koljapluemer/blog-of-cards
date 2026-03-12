from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown import markdown
from markupsafe import Markup

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "posts"
SITE_DIR = ROOT / "_site"
POSTS_OUT_DIR = SITE_DIR / "posts"


def render_markdown(text: str) -> str:
    return markdown(text or "", extensions=["extra", "sane_lists"])


def strip_markdown(text: str) -> str:
    if not text:
        return ""
    html_text = markdown(text, extensions=["extra", "sane_lists"])
    no_tags = re.sub(r"<[^>]+>", " ", html_text)
    return re.sub(r"\s+", " ", no_tags).strip()


def excerpt(text: str, limit: int = 140) -> str:
    clean = strip_markdown(text)
    if len(clean) <= limit:
        return clean
    cutoff = clean.rfind(" ", 0, limit)
    if cutoff == -1:
        cutoff = limit
    return clean[:cutoff].rstrip() + "…"


def first_image(cards: list[dict]) -> str | None:
    pattern = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
    for card in cards:
        content = card.get("content", "")
        match = pattern.search(content)
        if match:
            return match.group(1).strip()
    return None


def load_posts() -> list[dict]:
    posts: list[dict] = []
    for path in sorted(POSTS_DIR.glob("*.json")):
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        cards = []
        for card in data.get("cards", []):
            content = card.get("content", "")
            cards.append(
                {
                    "title": card.get("title", ""),
                    "content": content,
                    "content_html": Markup(render_markdown(content)),
                }
            )
        first_content = data.get("cards", [{}])[0].get("content", "")
        posts.append(
            {
                "slug": path.stem,
                "title": data.get("title", "Untitled"),
                "cards": cards,
                "card_count": len(cards),
                "excerpt": excerpt(first_content),
                "first_image": first_image(data.get("cards", [])),
            }
        )
    return posts


def write_styles() -> None:
    css = """@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;700&family=Space+Grotesk:wght@400;600&display=swap');

:root {
  color-scheme: light;
  --bg: #f4f1ea;
  --bg-accent: #efe4d0;
  --ink: #1c1a17;
  --muted: #6b5f4d;
  --card: #fbf8f2;
  --card-border: #e6d8c3;
  --accent: #c96b3c;
  --shadow: 0 20px 40px rgba(28, 26, 23, 0.15);
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: 'Space Grotesk', sans-serif;
  background: radial-gradient(circle at top, var(--bg-accent), var(--bg) 55%);
  color: var(--ink);
  min-height: 100vh;
}

a {
  color: inherit;
  text-decoration: none;
}

.site {
  max-width: 1100px;
  margin: 0 auto;
  padding: 48px 24px 80px;
}

.masthead {
  display: grid;
  gap: 12px;
  margin-bottom: 36px;
}

.masthead__title {
  font-family: 'Fraunces', serif;
  font-size: clamp(2.4rem, 4vw, 3.6rem);
  margin: 0;
}

.masthead__subtitle {
  color: var(--muted);
  font-size: 1.05rem;
  max-width: 560px;
  margin: 0;
}

.post-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
  grid-auto-flow: dense;
}

.post-card {
  background: var(--card);
  border: 1px solid var(--card-border);
  border-radius: 20px;
  padding: 22px;
  box-shadow: var(--shadow);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  position: relative;
  overflow: hidden;
}

.post-card--wide {
  grid-row: span 2;
}

@media (max-width: 700px) {
  .post-card--wide {
    grid-row: span 1;
  }
}

.post-card::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(140deg, rgba(201, 107, 60, 0.16), transparent 55%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.post-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 26px 45px rgba(28, 26, 23, 0.2);
}

.post-card:hover::after {
  opacity: 1;
}

.post-card__content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

hr {
color: rgba(201, 107, 60, 0.16);
    }

.post-card__title {
  font-family: 'Fraunces', serif;
  margin: 0;
  font-size: 1.5rem;
}

.post-card__image {
  width: 100%;
  height: 160px;
  object-fit: cover;
  border-radius: 14px;
}

.post-card__excerpt {
  color: var(--muted);
  margin: 0;
  line-height: 1.5;
}

.post-card__meta {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--accent);
}

.post-header {
  display: grid;
  gap: 14px;
  margin-bottom: 28px;
}

.post-header__back {
  font-size: 0.95rem;
  color: var(--accent);
}

.post-header__title {
  font-family: 'Fraunces', serif;
  font-size: clamp(2rem, 3vw, 3rem);
  margin: 0;
}

.card-grid {
  display: grid;
  gap: 24px;
}

.card {
  background: var(--card);
  border: 1px solid var(--card-border);
  border-radius: 18px;
  padding: 20px;
  box-shadow: var(--shadow);
}

.card h3 {
  margin: 0 0 12px;
  font-family: 'Fraunces', serif;
}

.card__content p {
  line-height: 1.6;
}

.card__content p:last-child {
  margin-bottom: 0;
}

.card__content img {
  max-width: 100%;
  height: auto;
  display: block;
}

blockquote {
  margin: 0;
  padding: 12px 16px;
  border-left: 3px solid var(--accent);
  background: rgba(201, 107, 60, 0.08);
  border-radius: 12px;
}

.footer {
  margin-top: 48px;
  color: var(--muted);
  font-size: 0.9rem;
}
"""
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "styles.css").write_text(css, encoding="utf-8")


def build() -> None:
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    POSTS_OUT_DIR.mkdir(parents=True, exist_ok=True)

    if (SITE_DIR / "media").exists():
        shutil.rmtree(SITE_DIR / "media")
    if (ROOT / "media").exists():
        shutil.copytree(ROOT / "media", SITE_DIR / "media")

    write_styles()

    env = Environment(
        loader=FileSystemLoader(str(ROOT)),
        autoescape=select_autoescape(["html", "jinja"]),
    )
    overview_template = env.get_template("overview_template.jinja")
    post_template = env.get_template("post_template.jinja")

    posts = load_posts()

    overview_html = overview_template.render(
        site_title="Blog of Cards",
        posts=posts,
    )
    (SITE_DIR / "index.html").write_text(overview_html, encoding="utf-8")

    for post in posts:
        post_html = post_template.render(site_title="Blog of Cards", post=post)
        (POSTS_OUT_DIR / f"{post['slug']}.html").write_text(
            post_html, encoding="utf-8"
        )


if __name__ == "__main__":
    build()
