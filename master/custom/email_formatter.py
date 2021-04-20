from buildbot.plugins import reporters

from custom.testsuite_utils import get_logs_and_tracebacks_from_build

MAIL_TEMPLATE = """\
The Buildbot has detected a {{ status_detected }} on builder {{ buildername }} while building {{ projects }}.
Full details are available at:
    {{ build_url }}

Buildbot URL: {{ buildbot_url }}

Worker for this Build: {{ workername }}

Build Reason: {{ build['properties'].get('reason', ["<unknown>"])[0] }}
Blamelist: {{ ", ".join(blamelist) }}

{{ summary }}


Summary of the results of the build (if available):
===================================================

{{ build['final_log'].test_summary() }}


Captured traceback
==================

{{ "\n\n".join(build['tracebacks']) }}


Test report
===========

{{ build['final_log'].format_failing_tests() }}



Sincerely,
 -The Buildbot
"""

TESTS_STEP = "test"


class CustomMessageFormatter(reporters.MessageFormatter):
    def buildAdditionalContext(self, master, ctx):
        ctx.update(self.context)
        build = ctx["build"]

        logs, tracebacks = get_logs_and_tracebacks_from_build(build)

        ctx["build"]["tracebacks"] = tracebacks
        ctx["build"]["final_log"] = logs


MESSAGE_FORMATTER = CustomMessageFormatter(
    template=MAIL_TEMPLATE,
    template_type="plain",
    wantLogs=True,
    wantProperties=True,
    wantSteps=True,
)
