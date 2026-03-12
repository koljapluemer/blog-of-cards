# Blog of Cards

Minimal static blog generator that renders JSON posts into a card-based site.

**What’s here**
- `posts/`: JSON posts made of cards.
- `build.py`: static site generator that writes to `_site/`.
- `edit.py`: Streamlit editor for posts + images.
- `media/`: uploaded images.

**Run locally**
```bash
uv sync
uv run python build.py
```

**Edit posts**
```bash
uv run streamlit run edit.py
```

**Post format**
```json
{
  "title": "Post title",
  "cards": [
    {
      "title": "Card title",
      "content": "Markdown content",
      "fixedPosition": true
    }
  ]
}
```

**Netlify**
Netlify reads `netlify.toml` and builds with:
```
python -m pip install -U uv && uv sync --no-dev --python 3.11 && uv run python build.py
```
