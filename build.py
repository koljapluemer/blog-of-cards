from __future__ import annotations

import json
import random
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
        raw_cards = data.get("cards", [])
        fixed_cards = []
        loose_cards = []
        for card in raw_cards:
            if card.get("fixedPosition") is True:
                fixed_cards.append(card)
            else:
                loose_cards.append(card)
        random.shuffle(loose_cards)
        ordered_cards = fixed_cards + loose_cards
        cards = []
        for card in ordered_cards:
            content = card.get("content", "")
            cards.append(
                {
                    "title": card.get("title", ""),
                    "content": content,
                    "content_html": Markup(render_markdown(content)),
                    "fixedPosition": card.get("fixedPosition", False),
                }
            )
        first_content = ordered_cards[0].get("content", "") if ordered_cards else ""
        posts.append(
            {
                "slug": path.stem,
                "title": data.get("title", "Untitled"),
                "cards": cards,
                "card_count": len(cards),
                "excerpt": excerpt(first_content),
                "first_image": first_image(ordered_cards),
            }
        )
    return posts


def write_styles() -> None:
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "styles.css", SITE_DIR / "styles.css")


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
    random.shuffle(posts)

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
