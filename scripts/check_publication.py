#!/usr/bin/env python3
"""Reject local-only session materials in the public tree and Git index."""
from pathlib import Path, PurePosixPath
from html.parser import HTMLParser
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_PATTERNS = (
    'teaching.html', 'mission01-*.html', 'mission01*.json',
    'practice-*', 'verify_practice.py', 'check_mission01.py',
    'check_workshop_examples.py', '*.tar.gz', '*.zip',
)


def local_only(name):
    path = PurePosixPath(name)
    return (any(part in {'private', '_private', 'TimeSeries_UT_TA_Private'} for part in path.parts)
            or any(path.match(pattern) for pattern in PRIVATE_PATTERNS))


class References(HTMLParser):
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {'href', 'src'} and value:
                target = value.split('#')[0].split('?')[0]
                assert not local_only(target), f'Link to local-only file: {value}'


def main():
    # Check actual files too: a plain folder upload must also be safe.
    files = [p for p in ROOT.rglob('*') if p.is_file()
             and '.git' not in p.relative_to(ROOT).parts
             and '__pycache__' not in p.relative_to(ROOT).parts]
    forbidden = [str(p.relative_to(ROOT)) for p in files
                 if local_only(p.relative_to(ROOT).as_posix())]
    assert not forbidden, f'Local-only files in public directory: {forbidden}'
    for page in ROOT.glob('*.html'):
        References().feed(page.read_text())
    for page in (ROOT / 'lessons').glob('*.html'):
        References().feed(page.read_text())
    course = json.loads((ROOT / 'content/course.json').read_text())
    for lesson in course['lessons']:
        assert lesson.get('kind') != 'workshop'
        assert not any(key.startswith('teaching_') for key in lesson)
    assert all(p['id'] != 'mission01-practice' for p in course['phases'])
    if (ROOT / '.git').exists():
        tracked = subprocess.check_output(
            ['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
        assert not any(local_only(p) for p in tracked if p), 'Local-only file in Git index'
    print('PASS: public files, links, course metadata and Git index exclude local-only sessions and answers.')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as error:
        print(error, file=sys.stderr)
        sys.exit(1)
