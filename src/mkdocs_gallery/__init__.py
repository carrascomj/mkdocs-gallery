# ─── src/mkdocs_gallery/__init__.py ────────────────────────────────
from __future__ import annotations
import re, html
from pathlib import Path

from mkdocs.plugins import BasePlugin
from mkdocs.utils   import get_relative_url
from markdown       import markdown  as md_to_html   # ← NEW
from pygments       import highlight as pyg_highlight
from pygments.lexers      import get_lexer_by_name, TextLexer
from pygments.formatters  import HtmlFormatter

HTML_FORMATTER = HtmlFormatter()     # keeps <pre> so line-breaks survive

IMG_RE  = re.compile(r'!\[(?P<alt>[^\]]*)\]\((?P<src>[^\)]+)\)', re.M)
CODE_RE = re.compile(
    r'^```(?P<lang>[^\s\n`]*)\s*\n'   # ```python
    r'(?P<code>.*?)^```',            # code …
    re.S | re.M
)

class Plugin(BasePlugin):            # MkDocs expects this exact name
    def on_page_markdown(self, md, page, config, files):
        if page.meta.get("gallery") or Path(page.file.src_path).stem == "gallery":
            return self._build_gallery(md, page.url or "")
        return md

    # ----------------------------------------------------------------
    def _build_gallery(self, md: str, page_url: str) -> str:
        items, pos = [], 0
        while (img := IMG_RE.search(md, pos)):
            code_match = CODE_RE.search(md, img.end())
            if not code_match:
                pos = img.end(); continue
            items.append((
                img.group("alt"),
                img.group("src"),
                code_match.group("lang").lower() or "text",
                code_match.group("code"),
            ))
            pos = code_match.end()

        if not items:
            return md

        out = ['<div class="gallery">']
        for alt, src_raw, lang, code in items:
            src = get_relative_url(src_raw, page_url)

            if lang == "url":
                # -------- render *Markdown* (links etc.) -------------
                rendered = md_to_html(code.strip(),
                                       extensions=["pymdownx.superfences",
                                                   "pymdownx.highlight"])
                panel_html = f'<div class="url-panel">{rendered}</div>'
            else:
                # -------- normal syntax-highlighted code -------------
                try:
                    lexer = get_lexer_by_name(lang, stripall=True)
                except Exception:
                    lexer = TextLexer(stripall=True)
                highlighted = pyg_highlight(code, lexer, HTML_FORMATTER)
                panel_html = f'<div class="code-panel">{highlighted}</div>'

            out.append(f'''
<div class="gallery-item" tabindex="0">
  <img src="{src}" alt="{html.escape(alt)}">
  <div class="overlay" aria-hidden="true">
    <button class="close" aria-label="Close">&times;</button>
    <img src="{src}" alt="{html.escape(alt)}" class="full">
    {panel_html}
  </div>
</div>''')
        out.append('</div>')
        return '\n'.join(out)
