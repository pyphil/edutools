"""Server-side HTML sanitizer for rich-text card content.

Cards can be created by anonymous students via QR access, so the HTML coming
from the CKEditor widget must never be trusted. Only a small allowlist of tags,
attributes and inline styles produced by the editor toolbar is kept.
"""
import re
from html import escape
from html.parser import HTMLParser

ALLOWED_TAGS = {
    'p', 'br', 'hr', 'strong', 'b', 'em', 'i', 'u', 's', 'strike', 'del', 'sub', 'sup',
    'code', 'pre', 'blockquote', 'mark', 'span', 'div', 'a',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li',
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption', 'colgroup', 'col', 'figure', 'figcaption',
}
VOID_TAGS = {'br', 'hr', 'col'}
# Elements whose whole content is dropped
DROP_CONTENT_TAGS = {'script', 'style', 'iframe', 'object', 'embed', 'template', 'noscript', 'svg', 'math'}

ALLOWED_ATTRS = {
    '*': {'class', 'style'},
    'a': {'href', 'title', 'target', 'rel'},
    'td': {'colspan', 'rowspan'},
    'th': {'colspan', 'rowspan', 'scope'},
    'col': {'span'},
    'ol': {'start', 'reversed'},
}

ALLOWED_STYLE_PROPS = {
    'color', 'background-color', 'font-size', 'font-family', 'font-weight', 'font-style',
    'text-align', 'text-decoration', 'margin-left', 'padding-left', 'width', 'height',
    'border', 'border-color', 'border-style', 'border-width', 'vertical-align',
}
SAFE_STYLE_VALUE = re.compile(r"^[#\w\s.,%()'\"-]*$")
SAFE_URL = re.compile(r'^(https?:|mailto:|tel:|/|#)', re.IGNORECASE)
SAFE_CLASS = re.compile(r'^[\w\s-]*$')


def _clean_style(value):
    cleaned = []
    for declaration in value.split(';'):
        if ':' not in declaration:
            continue
        prop, _, val = declaration.partition(':')
        prop = prop.strip().lower()
        val = val.strip()
        lowered = val.lower()
        if prop not in ALLOWED_STYLE_PROPS:
            continue
        if 'url(' in lowered or 'expression' in lowered or 'javascript' in lowered:
            continue
        if not SAFE_STYLE_VALUE.match(val):
            continue
        cleaned.append(f'{prop}:{val}')
    return ';'.join(cleaned)


class _Sanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.open_tags = []
        self.drop_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in DROP_CONTENT_TAGS:
            self.drop_depth += 1
            return
        if self.drop_depth or tag not in ALLOWED_TAGS:
            return
        allowed = ALLOWED_ATTRS['*'] | ALLOWED_ATTRS.get(tag, set())
        rendered = []
        for name, value in attrs:
            name = name.lower()
            if name not in allowed or value is None:
                continue
            if name == 'href':
                value = value.strip()
                if not SAFE_URL.match(value):
                    continue
            elif name == 'style':
                value = _clean_style(value)
                if not value:
                    continue
            elif name == 'class':
                if not SAFE_CLASS.match(value):
                    continue
            elif name == 'target':
                value = '_blank' if value == '_blank' else ''
                if not value:
                    continue
            elif name in {'colspan', 'rowspan', 'span', 'start'}:
                if not value.isdigit():
                    continue
            rendered.append(f'{name}="{escape(value, quote=True)}"')
        if tag == 'a':
            rendered = [a for a in rendered if not a.startswith('rel=')]
            rendered.append('rel="noopener noreferrer nofollow"')
        attr_str = (' ' + ' '.join(rendered)) if rendered else ''
        self.out.append(f'<{tag}{attr_str}>')
        if tag not in VOID_TAGS:
            self.open_tags.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag.lower() not in VOID_TAGS and self.open_tags and self.open_tags[-1] == tag.lower():
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in DROP_CONTENT_TAGS:
            if self.drop_depth:
                self.drop_depth -= 1
            return
        if self.drop_depth or tag not in ALLOWED_TAGS or tag in VOID_TAGS:
            return
        if tag not in self.open_tags:
            return
        # close any unclosed tags nested inside this one
        while self.open_tags:
            open_tag = self.open_tags.pop()
            self.out.append(f'</{open_tag}>')
            if open_tag == tag:
                break

    def handle_data(self, data):
        if not self.drop_depth:
            self.out.append(escape(data, quote=False))

    def result(self):
        while self.open_tags:
            self.out.append(f'</{self.open_tags.pop()}>')
        return ''.join(self.out)


def sanitize_html(value):
    if not value:
        return ''
    parser = _Sanitizer()
    parser.feed(value)
    parser.close()
    return parser.result()
