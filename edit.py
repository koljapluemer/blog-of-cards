from __future__ import annotations

import json
import re
from pathlib import Path

import streamlit as st
from PIL import Image

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


def queue_active_slug(slug: str | None) -> None:
    st.session_state["next_active_slug"] = slug


def handle_create_post() -> None:
    posts = st.session_state["posts"]
    new_title = st.session_state.get("new_post_title", "").strip()
    new_slug = st.session_state.get("new_post_slug", "").strip()
    slug = slugify(new_slug or new_title)
    if not new_title:
        st.session_state["create_post_error"] = "Add a title to create the post."
        return
    if slug in posts:
        st.session_state["create_post_error"] = "That slug already exists."
        return
    posts[slug] = {"title": new_title or "Untitled", "cards": []}
    st.session_state["create_post_error"] = ""
    queue_active_slug(slug)


def handle_delete_post() -> None:
    posts = st.session_state["posts"]
    active = st.session_state.get("active_slug_select")
    if not active:
        return
    (POSTS_DIR / f"{active}.json").unlink(missing_ok=True)
    posts.pop(active, None)
    queue_active_slug(next(iter(posts), None))


def handle_reload_posts() -> None:
    st.session_state["posts"] = load_posts()
    queue_active_slug(st.session_state.get("active_slug_select"))


st.set_page_config(page_title="Blog of Cards Editor", layout="wide")

if "posts" not in st.session_state:
    st.session_state["posts"] = load_posts()

posts = st.session_state["posts"]

if "next_active_slug" in st.session_state:
    st.session_state["active_slug_select"] = st.session_state.pop("next_active_slug")

if "active_slug_select" not in st.session_state or st.session_state["active_slug_select"] not in posts:
    st.session_state["active_slug_select"] = next(iter(posts), None)

st.sidebar.header("Posts")

if posts:
    slugs = list(posts.keys())
    active_slug = st.sidebar.selectbox(
        "Select post",
        slugs,
        format_func=lambda s: posts[s].get("title", s),
        key="active_slug_select",
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
    if st.button("Create post", use_container_width=True, on_click=handle_create_post):
        pass
    create_error = st.session_state.get("create_post_error", "")
    if create_error:
        st.warning(create_error)

st.sidebar.divider()

confirm_delete = st.sidebar.checkbox("Confirm delete", value=False)
if st.sidebar.button(
    "Delete active post",
    use_container_width=True,
    disabled=not active_slug or not confirm_delete,
    on_click=handle_delete_post,
):
    if not confirm_delete:
        st.sidebar.warning("Check confirm delete first.")

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
        card["fixedPosition"] = st.checkbox(
            "Fixed position",
            value=bool(card.get("fixedPosition", False)),
            key=f"{active_slug}_card_fixed_{idx}",
            help="Keep this card pinned at the top in its current order.",
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
    if st.button("Reload from disk", on_click=handle_reload_posts):
        pass

st.divider()
st.subheader("Images")

images_dir = ROOT / "media" / "img" / active_slug
images_dir.mkdir(parents=True, exist_ok=True)

uploaded_file = st.file_uploader(
    "Upload image",
    type=["png", "jpg", "jpeg", "webp", "gif"],
    help="Images are stored in media/img/<post-slug>/ and referenced in Markdown.",
)
image_slug = st.text_input(
    "Image slug (letters, numbers, dash)",
    value="",
    help="Used as the filename. Example: cover-shot",
)

slug_ok = bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", image_slug))
if image_slug and not slug_ok:
    st.warning("Slug must be lowercase letters, numbers, and dashes only.")

if st.button("Save image", disabled=uploaded_file is None or not slug_ok):
    if uploaded_file is None:
        st.warning("Choose a file first.")
    elif not slug_ok:
        st.warning("Fix the slug format first.")
    else:
        target_path = images_dir / f"{image_slug}.webp"
        try:
            image = Image.open(uploaded_file)
            if (image.format or "").upper() == "WEBP":
                target_path.write_bytes(uploaded_file.getvalue())
            else:
                if image.mode in ("RGBA", "LA", "P"):
                    image = image.convert("RGBA")
                else:
                    image = image.convert("RGB")
                image.save(target_path, format="WEBP", quality=95, method=6)
            st.session_state["last_uploaded_image"] = target_path.name
            st.success(f"Saved {target_path.name}")
        except Exception as exc:
            st.error(f"Failed to process image: {exc}")

st.divider()
st.subheader("Post images")

image_files = sorted(images_dir.glob("*.webp"))
if not image_files:
    st.info("No images uploaded yet.")
else:
    columns = st.columns(3)
    for idx, image_path in enumerate(image_files):
        rel_path = f"../media/img/{active_slug}/{image_path.name}"
        with columns[idx % 3]:
            st.image(str(image_path), caption=image_path.name, width=220)
            st.code(f"![alt text]({rel_path})", language="markdown")
            if st.session_state.get("last_uploaded_image") == image_path.name:
                st.caption("Last uploaded")
            if st.button("Delete image", key=f"delete_image_{image_path.name}"):
                image_path.unlink(missing_ok=True)
                if st.session_state.get("last_uploaded_image") == image_path.name:
                    st.session_state.pop("last_uploaded_image", None)
                st.experimental_rerun()
