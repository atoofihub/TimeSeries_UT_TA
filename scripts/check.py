#!/usr/bin/env python3
"""Check the generated offline course, using only Python's standard library."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import re
import sys
import ast
from html import unescape

ROOT = Path(__file__).resolve().parents[1]
COURSE = json.loads((ROOT / 'content/course.json').read_text())
errors = []


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.ids = []
        self.references = []
        self.h1_count = 0
        self.parts = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'h1':
            self.h1_count += 1
        for attr in ('src', 'href'):
            if attr in attrs:
                self.references.append((tag, attr, attrs[attr]))

    def handle_data(self, text):
        self.parts.append(text)

    def text(self):
        return re.sub(r'\s+', ' ', ' '.join(self.parts)).strip()


pages = [ROOT / 'index.html'] + [ROOT / 'lessons' / x['file'] for x in COURSE['lessons']]
parsed = {p: Document(p.read_text()) for p in pages}
for page, doc in parsed.items():
    name = page.relative_to(ROOT)
    html = page.read_text()
    for unwanted in ('تحلیل سری زمانی ژئودزی', 'چاپ درس', 'ثبت مطالعه', 'complete-button', 'print-button', 'progress-label', 'جزوهٔ استاد و متن اصلی تمرین، مرجع اصطلاحات رسمی درس هستند.'):
        if unwanted in html:
            errors.append(f'{name}: removed UI/text returned: {unwanted}')
    if doc.h1_count != 1:
        errors.append(f'{name}: expected one h1, got {doc.h1_count}')
    for id, count in Counter(doc.ids).items():
        if count > 1:
            errors.append(f'{name}: duplicate id {id}')
    for tag, attr, value in doc.references:
        url = urlsplit(value)
        if url.scheme in ('mailto', 'tel'):
            continue
        if url.scheme or url.netloc:
            if tag != 'a':
                errors.append(f'{name}: external runtime dependency {value}')
            continue
        target = (page.parent / unquote(url.path)).resolve() if url.path else page
        if not target.is_file():
            errors.append(f'{name}: missing {value}')
        elif url.fragment and target.suffix == '.html':
            target_doc = parsed.get(target) or Document(target.read_text())
            if unquote(url.fragment) not in target_doc.ids:
                errors.append(f'{name}: missing fragment {value}')

for css in (ROOT / 'assets').glob('*.css'):
    for value in re.findall(r'url\([\'"]?([^\)\'\"]+)', css.read_text()):
        if urlsplit(value).scheme:
            errors.append(f'{css.name}: external CSS asset {value}')
        elif not (css.parent / unquote(value)).is_file():
            errors.append(f'{css.name}: missing CSS asset {value}')

formulas = 0
for lesson in COURSE['lessons']:
    fragment = (ROOT / 'content/lessons' / lesson['file']).read_text().strip()
    page = (ROOT / 'lessons' / lesson['file']).read_text()
    article = re.search(r'<article class="lesson"[^>]*>(.*?)</article>', page, re.S)
    if not article:
        errors.append(f'{lesson["file"]}: missing content article')
        continue
    normalize = lambda text: Document(text.replace('>Copy</button>', '>کپی کد</button>')).text()
    if normalize(fragment) != normalize(article[1]):
        errors.append(f'{lesson["file"]}: source content differs from generated content')
    formulas += fragment.count('\\[') + fragment.count('\\(')
    if fragment.count('\\[') != fragment.count('\\]') or fragment.count('\\(') != fragment.count('\\)'):
        errors.append(f'{lesson["file"]}: unbalanced math delimiters')
    for attributes, code in re.findall(r'<pre([^>]*)>(.*?)</pre>', fragment, re.S):
        if 'data-language="text"' in attributes:
            continue
        try:
            ast.parse(unescape(code))
        except SyntaxError as error:
            errors.append(f'{lesson["file"]}: invalid Python example: {error}')

cases = [x for x in COURSE['lessons'] if 'case_number' in x]
if [x['case_number'] for x in cases] != [1, 2, 3, 4, 5, 6]:
    errors.append('Exactly six ordered adjustment cases are required')
if [x['id'] for x in COURSE['lessons'][4:10]] != [x['id'] for x in cases]:
    errors.append('Six cases must immediately follow the three foundation lessons')
if COURSE['title'] != 'تحلیل سری زمانی':
    errors.append('Course title must be تحلیل سری زمانی')

route = (ROOT / 'assets/route-data.js').read_text()
points = json.loads(route.removeprefix('window.COURSE_ROUTE = ').rstrip().removesuffix(';'))
if not all(len(row) == 4 for row in points):
    errors.append('Route rows must have time, east, north and accuracy values')
if not all(b[0] > a[0] for a, b in zip(points, points[1:])):
    errors.append('Route times must be strictly increasing')

if errors:
    print('\n'.join(errors))
    sys.exit(1)
print(f'PASS: {len(pages)} pages, all local links and assets, one h1 per page, unique anchors.')
print(f'PASS: {len(COURSE["lessons"])} complete lesson bodies; {formulas} balanced math expressions; Python examples parse.')
print('PASS: six ordered adjustment cases follow foundations; removed UI/text is absent.')
print(f'PASS: {len(points)} embedded GNSS samples, strictly increasing times. No external HTML/CSS dependencies.')
