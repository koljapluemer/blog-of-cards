from __future__ import annotations

import json
import re
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "posts"


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "untitled"


def load_posts() -> dict[str, dict]:
    posts: dict[str, dict] = {}
    for path in sorted(POSTS_DIR.glob("*.json")):
        with path.open("r", encoding="utf-8") as f:
            posts[path.stem] = json.load(f)
    return posts


def save_post(slug: str, data: dict) -> None:
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    path = POSTS_DIR / f"{slug}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


st.set_page_config(page_title="Blog of Cards Editor", layout="wide")

if "posts" not in st.session_state:
    st.session_state["posts"] = load_posts()

posts = st.session_state["posts"]

if "active_slug" not in st.session_state or st.session_state["active_slug"] not in posts:
    st.session_state["active_slug"] = next(iter(posts), None)

st.sidebar.header("Posts")

if posts:
    slugs = list(posts.keys())
    active_slug = st.sidebar.selectbox(
        "Select post",
        slugs,
        format_func=lambda s: posts[s].get("title", s),
        key="active_slug",
    )
else:
    active_slug = None
    st.sidebar.info("No posts yet. Create your first one.")

with st.sidebar.expander("Create new post", expanded=False):
    new_title = st.text_input("Title", key="new_post_title")
    new_slug = st.text_input(
        "Slug",
        value=slugify(new_title) if new_title else "",
        key="new_post_slug",
        help="Used for the filename and URL.",
    )
    if st.button("Create post", use_container_width=True):
        slug = slugify(new_slug or new_title)
        if not slug:
            st.warning("Add a title to create the post.")
        elif slug in posts:
            st.warning("That slug already exists.")
        else:
            posts[slug] = {"title": new_title or "Untitled", "cards": []}
            st.session_state["active_slug"] = slug
            st.experimental_rerun()

st.sidebar.divider()

confirm_delete = st.sidebar.checkbox("Confirm delete", value=False)
if st.sidebar.button("Delete active post", use_container_width=True, disabled=not active_slug):
    if not confirm_delete:
        st.sidebar.warning("Check confirm delete first.")
    else:
        (POSTS_DIR / f"{active_slug}.json").unlink(missing_ok=True)
        posts.pop(active_slug, None)
        st.session_state["active_slug"] = next(iter(posts), None)
        st.experimental_rerun()

if active_slug is None:
    st.title("No posts yet")
    st.stop()

post = posts[active_slug]

st.title("Post editor")
post["title"] = st.text_input("Post title", value=post.get("title", ""), key=f"title_{active_slug}")

cards = post.setdefault("cards", [])

st.subheader("Cards")

for idx, card in enumerate(cards):
    card_title_key = f"{active_slug}_card_title_{idx}"
    card_content_key = f"{active_slug}_card_content_{idx}"
    with st.expander(f"Card {idx + 1}", expanded=True):
        card["title"] = st.text_input(
            "Card title (optional)",
            value=card.get("title", ""),
            key=card_title_key,
        )
        card["content"] = st.text_area(
            "Card content (Markdown)",
            value=card.get("content", ""),
            key=card_content_key,
            height=140,
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Move up", key=f"{active_slug}_move_up_{idx}", disabled=idx == 0):
                cards[idx - 1], cards[idx] = cards[idx], cards[idx - 1]
                st.experimental_rerun()
        with col2:
            if st.button(
                "Move down",
                key=f"{active_slug}_move_down_{idx}",
                disabled=idx == len(cards) - 1,
            ):
                cards[idx + 1], cards[idx] = cards[idx], cards[idx + 1]
                st.experimental_rerun()
        with col3:
            if st.button("Delete card", key=f"{active_slug}_delete_{idx}"):
                cards.pop(idx)
                st.experimental_rerun()

st.divider()

col_a, col_b, col_c = st.columns([1, 1, 2])
with col_a:
    if st.button("Add card"):
        cards.append({"title": "", "content": ""})
        st.experimental_rerun()
with col_b:
    if st.button("Save post"):
        save_post(active_slug, post)
        st.success("Saved.")
with col_c:
    if st.button("Reload from disk"):
        st.session_state["posts"] = load_posts()
        st.session_state["active_slug"] = active_slug
        st.experimental_rerun()
