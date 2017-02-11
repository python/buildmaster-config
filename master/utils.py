import re

from jinja2 import Markup


REPLACEMENTS = [
    (
        '#(\d+)',
        '<a href="https://github.com/python/cpython/pull/\g<1>"'
        ' title="Pull Request \g<0>">\g<0></a>'
    ),
    (
        'bpo-(\d+)',
        '<a href="https://bugs.python.org/issue\g<1>"'
        ' title="Issue #\g<1>">\g<0></a>'
    ),
]


def changecommentlink(changetext, project_name):
    if project_name != 'Python':    # XXX temp debugging
        from twisted.python import log
        log.msg('got project name %r' % (project_name,))
    for pat, repl in REPLACEMENTS:
        changetext = re.sub(pat, Markup(repl), changetext)
    return changetext
