import re

from jinja2 import Markup


REPLACEMENTS = [
    (
        '(?<!&)(?:gh-?|pr-?|#)(\d+)(?!;)',
        '<a href="https://github.com/python/cpython/pull/\g<1>"'
        ' title="GitHub Pull Request #\g<1>">\g<0></a>'
    ),
    (
        'bpo-(\d+)',
        '<a href="https://bugs.python.org/issue\g<1>"'
        ' title="bugs.python.org Issue #\g<1>">\g<0></a>'
    ),
]


def changecommentlink(changetext, project_name):
    for pat, repl in REPLACEMENTS:
        changetext = re.sub(pat, Markup(repl), changetext, flags=re.I)
    return changetext
