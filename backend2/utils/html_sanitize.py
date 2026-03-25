"""日记正文 HTML：清洗 XSS、统一入库与校验非空。"""
import re

import bleach
from bleach.css_sanitizer import CSSSanitizer


def _strip_script_style_blocks(html: str) -> str:
    """bleach 剥离 script 标签时可能留下内部文本，先整块删除。"""
    if not html:
        return ""
    s = re.sub(
        r"<script\b[^>]*>[\s\S]*?</script>",
        "",
        html,
        flags=re.I,
    )
    s = re.sub(
        r"<style\b[^>]*>[\s\S]*?</style>",
        "",
        s,
        flags=re.I,
    )
    return s

_ALLOWED_TAGS = frozenset(
    [
        "p",
        "br",
        "strong",
        "b",
        "em",
        "i",
        "u",
        "s",
        "strike",
        "del",
        "ins",
        "span",
        "div",
        "section",
        "article",
        "ul",
        "ol",
        "li",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "blockquote",
        "pre",
        "code",
        "img",
        "a",
        "hr",
    ]
)

_ALLOWED_ATTRIBUTES = {
    "a": ["href", "target", "rel"],
    "img": ["src", "alt", "width", "height", "style", "class"],
    "*": ["style", "class"],
}

_CSS = CSSSanitizer(
    allowed_css_properties=frozenset(
        [
            "color",
            "background-color",
            "text-align",
            "font-weight",
            "font-size",
            "font-style",
            "font-family",
            "text-decoration",
            "line-height",
            "margin",
            "margin-top",
            "margin-bottom",
            "margin-left",
            "margin-right",
            "padding",
            "padding-top",
            "padding-bottom",
            "padding-left",
            "padding-right",
            "text-indent",
            "direction",
            "letter-spacing",
        ]
    )
)


def sanitize_diary_html(raw):
    if raw is None:
        return ""
    if not isinstance(raw, str):
        raw = str(raw)
    raw = _strip_script_style_blocks(raw)
    return bleach.clean(
        raw,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        css_sanitizer=_CSS,
        strip=True,
    )


def diary_html_is_effectively_empty(html: str) -> bool:
    """无可见文字且无图片则视为空。"""
    if not html or not str(html).strip():
        return True
    plain = bleach.clean(html, tags=[], strip=True).strip()
    if plain:
        return False
    return not bool(re.search(r"<img\b", html, re.I))


def html_to_plain_text(html: str) -> str:
    """供分词 / AI 使用的纯文本。"""
    if not html:
        return ""
    return bleach.clean(_strip_script_style_blocks(html), tags=[], strip=True)
