from buildbot.plugins import reporters

from custom.pr_reporter import Logs

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
    def _construct_tracebacks_from_stderr(self, build):
        for step in build["steps"]:
            try:
                test_log = step["logs"][0]["content"]["content"]
            except IndexError:
                continue
            test_log = "\n".join(
                [
                    line.lstrip("e")
                    for line in test_log.splitlines()
                    if line.startswith("e")
                ]
            )
            if not test_log:
                continue
            yield test_log

    def buildAdditionalContext(self, master, ctx):
        ctx.update(self.ctx)
        build = ctx["build"]

        test_log = ""
        try:
            test_step = [step for step in build["steps"] if step["name"] == TESTS_STEP][0]
            test_log = test_step["logs"][0]["content"]["content"]
            test_log = "\n".join([line.lstrip("eo") for line in test_log.splitlines()])
        except IndexError:
            pass

        logs = Logs(test_log)
        tracebacks = list(logs.get_tracebacks())

        if not tracebacks:
            tracebacks = list(self._construct_tracebacks_from_stderr(build))

        ctx["build"]["tracebacks"] = tracebacks
        ctx["build"]["final_log"] = logs


MESSAGE_FORMATTER = CustomMessageFormatter(
    template=MAIL_TEMPLATE,
    template_type="html",
    wantLogs=True,
    wantProperties=True,
    wantSteps=True,
)
