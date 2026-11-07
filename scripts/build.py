#!/usr/bin/env python3
"""Generate portable HTML from course.json and editable lesson fragments. Stdlib only."""
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
COURSE = json.loads((ROOT / 'content/course.json').read_text())
LESSONS = COURSE['lessons']
IDS = {lesson['id']: lesson for lesson in LESSONS}


def fa(value):
    return str(value).translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))


class PlainText(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.parts = []
        self.feed(html)

    def handle_data(self, text):
        self.parts.append(text)

    def text(self):
        return ' '.join(' '.join(self.parts).split())


def lesson_link(lesson, prefix=''):
    return prefix + 'lessons/' + lesson['file']


def head(title, prefix, description):
    return f'''<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{escape(description, quote=True)}">
  <meta name="color-scheme" content="light">
  <title>{escape(title)} | تحلیل سری زمانی · دانشگاه تهران</title>
  <link rel="icon" href="{prefix}assets/ut_logo.png" type="image/png">
  <link rel="stylesheet" href="{prefix}assets/lesson-content.css">
  <link rel="stylesheet" href="{prefix}assets/style.css">
  <script src="{prefix}assets/site.js" defer></script>
</head>'''


def header(prefix):
    return f'''<a class="skip-link" href="#main">رفتن به محتوای اصلی</a>
<div class="page-shell">
<header class="university-header">
  <img class="university-logo" src="{prefix}assets/ut_logo.png" width="84" height="100" alt="دانشگاه تهران">
  <a class="course-identity" href="{prefix}index.html"><span>دانشگاه تهران · دانشکدهٔ فنی</span><strong>تحلیل سری زمانی</strong><span class="identity-en" lang="en" dir="ltr">TIME SERIES ANALYSIS</span></a>
  <img class="faculty-logo" src="{prefix}assets/fanni_logo.png" width="114" height="100" alt="دانشکدهٔ فنی دانشگاه تهران">
</header>
<nav class="main-nav" aria-label="ناوبری اصلی">
  <a href="{prefix}index.html" class="{'active' if not prefix else ''}">سرفصل‌های درس</a>
  <a href="{prefix}index.html#assignment-01">صورت تمرین و داده‌ها</a>
  <a href="{lesson_link(IDS['ch15'], prefix)}">پروژهٔ GNSS</a>
  <a href="{lesson_link(IDS['appendix'], prefix)}">فرمول‌ها و واژه‌نامه</a>
  <span class="nav-caption">درس‌نامه و تمرین‌های آموزشی</span>
</nav>'''


def footer():
    return f'''<footer class="site-footer">
  <div><strong>تحلیل سری زمانی · دانشگاه تهران</strong><p>استاد: {escape(COURSE['instructor'])} <span class="footer-separator">|</span> دستیار آموزشی: {escape(COURSE['ta'])}</p></div>
  <a href="mailto:{escape(COURSE['email'])}" dir="ltr">{escape(COURSE['email'])}</a>
</footer></div>
</body></html>'''


def wave():
    return '''<svg class="series-visual" viewBox="0 0 420 160" role="img" aria-label="نمای شماتیک مشاهده‌های سری زمانی و روند برآوردشده">
<defs><pattern id="grid" width="42" height="32" patternUnits="userSpaceOnUse"><path d="M 42 0 L 0 0 0 32" fill="none" stroke="#d8e4ec" stroke-width="1"/></pattern></defs>
<rect width="420" height="160" fill="url(#grid)"/>
<path d="M8 125 L25 133 L42 94 L59 108 L76 80 L93 103 L110 73 L127 89 L144 56 L161 81 L178 59 L195 78 L212 56 L229 82 L246 47 L263 65 L280 34 L297 49 L314 22 L331 42 L348 20 L365 35 L382 12 L405 21" fill="none" stroke="#a5b7c5" stroke-width="1.7"/>
<path d="M8 128 C50 120 60 96 96 91 S148 62 180 67 S220 73 246 61 S288 39 322 33 S372 21 405 18" fill="none" stroke="#247eaf" stroke-width="3"/>
<g fill="#247eaf"><circle cx="96" cy="91" r="4"/><circle cx="180" cy="67" r="4"/><circle cx="246" cy="61" r="4"/><circle cx="322" cy="33" r="4"/></g>
<text x="8" y="154" fill="#637788" font-size="10" font-family="monospace" direction="ltr">OBSERVATION → ESTIMATION</text></svg>'''


def build_index():
    lesson_count = sum(1 for x in LESSONS if x['id'] not in {'intro', 'appendix'} and x.get('kind') != 'workshop')
    phases = []
    for phase in COURSE['phases']:
        rows = []
        for lesson in LESSONS:
            if lesson['phase'] != phase['id']:
                continue
            rows.append(f'''<li class="lesson-row" data-lesson="{lesson['id']}">
  <a href="{lesson_link(lesson)}" class="lesson-card">
    <span class="lesson-number">{escape(lesson['label'])}</span>
    <span class="lesson-summary"><strong>{escape(lesson['title'])}</strong><span>{escape(lesson['description'])}</span></span>
    <span class="lesson-state">مطالعهٔ درس <span aria-hidden="true">←</span></span>
  </a></li>''')
        phases.append(f'''<section class="learning-phase" id="{phase['id']}" aria-labelledby="heading-{phase['id']}">
  <div class="phase-heading"><span class="phase-number">{phase['number']}</span><div><h3 id="heading-{phase['id']}">{phase['title']}</h3><p>{phase['description']}</p></div><span class="phase-count">{fa(len(rows))} بخش</span></div>
  <ol class="lesson-list">{''.join(rows)}</ol>
</section>''')
    phase_links = ''.join(f'<a href="#{p["id"]}"><span>{p["number"]}</span>{p["title"]}</a>' for p in COURSE['phases'])
    html = head('سرفصل‌های درس', '', 'درس‌نامهٔ فارسی تحلیل سری زمانی دانشگاه تهران؛ از مبانی و سرشکنی تا فیلتر کالمن و پروژهٔ GNSS.')
    html += '<body data-page="home">' + header('')
    html += f'''<main id="main">
<section class="course-intro" aria-labelledby="course-title">
  <div class="intro-copy"><span class="eyebrow">کارشناسی ارشد مهندسی نقشه‌برداری · گرایش ژئودزی</span>
  <h1 id="course-title">تحلیل سری زمانی</h1>
  <p class="intro-lead">مباحث درس شامل مبانی مدل خطی، شش حالت سرشکنی و برآورد، مؤلفه‌های واریانس، برآورد دسته‌ای و بازگشتی، سیستم‌های دینامیکی و فیلتر کالمن است.</p>
  <a class="button primary" href="{lesson_link(LESSONS[0])}">مطالعهٔ مقدمه <span aria-hidden="true">←</span></a>
  </div>
  <div class="intro-aside">{wave()}<div class="course-facts"><span><strong>{fa(lesson_count)}</strong> درس</span><span><strong>۶</strong> حالت سرشکنی</span><span><strong>۱</strong> پروژهٔ GNSS</span></div><p>روابط ریاضی و مثال‌های عددی</p></div>
</section>
<section class="assignment-resources" id="assignment-01" aria-labelledby="assignment-title"><h2 id="assignment-title">تمرین اول: صورت تمرین و داده‌ها</h2><p>صورت تمرین، اقلام تحویل و تعریف داده‌ها را مشخص می‌کند. برای انجام پروژه، فایل کامل مشاهدات را دریافت کنید.</p><ul><li><a href="assets/mission-01/assignment.pdf">صورت تمرین اول، PDF</a></li><li><a href="assets/mission-01/observations.csv" download>دریافت observations.csv</a></li><li><a href="assets/mission-01/can_optional.csv" download>دریافت دادهٔ اختیاری CAN</a></li></ul></section>
<div class="course-tools"><p class="course-outline">مبانی ← شش حالت سرشکنی ← برآورد استاتیک ← برآورد دینامیکی</p>
<div class="lesson-search"><label for="lesson-search">جست‌وجو در درس‌ها</label><input id="lesson-search" type="search" placeholder="مثلاً کالمن، کوواریانس، نویز…" autocomplete="off" aria-controls="learning-path"></div></div>
<div class="path-layout"><aside class="path-sidebar"><h2>فهرست فصل‌ها</h2><nav aria-label="فصل‌های درس">{phase_links}</nav><p>ترتیب فصل‌ها بر مبنای مدل‌های سرشکنی، برآورد استاتیک و مدل فضای حالت تنظیم شده است.</p></aside>
<div class="path-main"><div class="path-title"><h2>ترتیب مباحث</h2><span>مبانی، نظریه و کاربرد</span></div><p id="search-status" class="search-status" role="status" hidden></p><div id="learning-path">{''.join(phases)}</div></div></div>
</main>'''
    html += footer()
    (ROOT / 'index.html').write_text(html)


def build_lesson(lesson, index):
    body = (ROOT / 'content/lessons' / lesson['file']).read_text().strip()
    if len(re.findall(r'<h2(?:\s[^>]*)?>', body)) != 1:
        raise ValueError(f'{lesson["file"]}: expected one h2 lesson title')
    # Preserve all educational content; only promote its main heading and repair links.
    body = re.sub(r'<h2(\s[^>]*)?>', r'<h1\1>', body, count=1).replace('</h2>', '</h1>', 1)
    body = re.sub(r'href="#([^"]+)"', lambda m: f'href="{IDS[m[1]]["file"]}"' if m[1] in IDS and m[1] != lesson['id'] else m[0], body)
    body = body.replace('>Copy</button>', '>کپی کد</button>')
    toc = []
    count = 0

    def add_anchor(match):
        nonlocal count
        count += 1
        anchor = f'section-{count}'
        label = PlainText(match[1]).text()
        toc.append(f'<a href="#{anchor}">{escape(label)}</a>')
        return f'<h3 id="{anchor}">{match[1]}</h3>'

    body = re.sub(r'<h3>(.*?)</h3>', add_anchor, body, flags=re.S)
    current_phase = next(p for p in COURSE['phases'] if p['id'] == lesson['phase'])
    prev = LESSONS[index - 1] if index else None
    next_lesson = LESSONS[index + 1] if index + 1 < len(LESSONS) else None
    previous = f'<a class="previous-lesson" href="{prev["file"]}"><span>درس قبلی</span><strong>→ {escape(prev["title"])}</strong></a>' if prev else '<a class="previous-lesson" href="../index.html">→ سرفصل‌های درس</a>'
    following = f'<a class="next-lesson" href="{next_lesson["file"]}"><span>بخش بعدی</span><strong>{escape(next_lesson["title"])} ←</strong></a>' if next_lesson else '<a class="next-lesson" href="../index.html"><span>پایان مسیر</span><strong>بازگشت به سرفصل‌های درس ←</strong></a>'
    all_links = ''.join(f'<a href="{item["file"]}" {"aria-current=page" if item["id"] == lesson["id"] else ""}><span>{item["label"]}</span>{escape(item["title"])}</a>' for item in LESSONS)
    html = head(lesson['title'], '../', lesson['description'])
    html = html.replace('</head>', '<script src="../assets/math-config.js" defer></script>\n<script src="../assets/vendor/mathjax-tex-svg.js" defer></script>\n</head>')
    html += f'<body data-page="lesson" data-lesson-id="{lesson["id"]}">' + header('../')
    html += f'''<div class="lesson-toolbar"><nav aria-label="مسیر صفحه"><a href="../index.html">سرفصل‌های درس</a><span aria-hidden="true">/</span><a href="../index.html#{current_phase['id']}">{current_phase['title']}</a><span aria-hidden="true">/</span><span>{lesson['label']}</span></nav></div>
<div class="lesson-layout"><aside class="lesson-sidebar">
<details class="section-menu" open><summary>فهرست مطالب</summary><nav aria-label="فهرست همین درس">{''.join(toc) if toc else '<a href="#main">مطالعهٔ این بخش</a>'}</nav></details>
<details class="all-lessons"><summary>فهرست درس‌ها</summary><nav aria-label="فهرست کامل درس‌ها">{all_links}</nav></details>
<a class="sidebar-back" href="../index.html">→ بازگشت به سرفصل‌های درس</a>
</aside>
<main id="main" class="lesson-main"><article class="lesson" id="{lesson['id']}">{body}</article>
<nav class="lesson-pagination" aria-label="درس قبلی و بعدی">{previous}{following}</nav>
</main></div>'''
    if lesson['id'] == 'ch15':
        html += '<script src="../assets/route-data.js" defer></script><script src="../assets/route-demo.js" defer></script>'
    html += footer()
    (ROOT / 'lessons' / lesson['file']).write_text(html)


def main():
    if len(IDS) != len(LESSONS) or len({x['file'] for x in LESSONS}) != len(LESSONS):
        raise ValueError('Lesson IDs and filenames must be unique')
    for lesson in LESSONS:
        if not re.fullmatch(r'[a-z0-9-]+\.html', lesson['file']):
            raise ValueError('Use a simple portable HTML filename')
        if lesson['phase'] not in {p['id'] for p in COURSE['phases']}:
            raise ValueError(f'Unknown phase: {lesson["phase"]}')
    (ROOT / 'lessons').mkdir(exist_ok=True)
    build_index()
    for i, lesson in enumerate(LESSONS):
        build_lesson(lesson, i)
    print(f'Built index.html and {len(LESSONS)} public lesson pages. No runtime server or build dependencies.')


if __name__ == '__main__':
    main()
