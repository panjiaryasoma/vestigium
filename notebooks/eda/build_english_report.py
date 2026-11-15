#!/usr/bin/env python3
"""Regenerate the self-contained English VESTIGIUM EDA report from Markdown and figures."""
from pathlib import Path
from html import escape
import base64,re,mistune
r=Path(__file__).resolve().parent
md=(r/'VESTIGIUM_EDA_COMPLETE_EN.md').read_text()
body=mistune.create_markdown(plugins=['table','strikethrough'])(md)
def repl(m):
    p=r/'figures'/m.group(1)
    if not p.exists():raise FileNotFoundError(p)
    return '<img src="data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode('ascii')+'" alt="'+escape(m.group(2))+'">'
body,n=re.subn(r'<img src="figures/([^"<>]+)" alt="([^"]*)"\s*/?>',repl,body)
assert n==17,f'Expected 17 figures, found {n}'
# Preserve the originally authored HTML styling when regenerating.
existing=(r/'VESTIGIUM_EDA_REPORT_EN.html').read_text()
start=existing.index('<style>')+len('<style>');end=existing.index('</style>')
css=existing[start:end]
html='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>VESTIGIUM | Comprehensive FIRMS EDA (EN)</title><style>'+css+'</style></head><body><main><header><span class="eyebrow">NASA SPACE APPS 2026 · TEAM GA TIDUR</span><span class="meta">INDONESIA / 2000–2025 / RESEARCH ARCHIVE</span></header>'+body+'</main></body></html>'
(r/'VESTIGIUM_EDA_REPORT_EN.html').write_text(html)
print('Built English HTML with',n,'embedded figures')
