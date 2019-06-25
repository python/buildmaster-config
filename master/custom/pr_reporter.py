import re

from twisted.internet import defer
from twisted.python import log

from buildbot.process.properties import Properties
from buildbot.process.results import (
    CANCELLED,
    EXCEPTION,
    FAILURE,
    RETRY,
    SKIPPED,
    SUCCESS,
    WARNINGS,
)
from buildbot.util.giturlparse import giturlparse
from buildbot.plugins import reporters
from buildbot.reporters.utils import getDetailsForBuild

TESTS_STEP = "test"

TRACEBACK_REGEX = re.compile(
    r"""
     ^Traceback # Lines starting with "Traceback"
     [\s\S]+? # Match greedy any text (preserving ASCII flags).
     (?=^(?:\d|test|\Z|\n|ok)) # Stop matching in lines starting with
                               # a number (log time), "test" or the end
                               # of the string.
    """, re.MULTILINE | re.VERBOSE,
)

LEAKS_REGEX = re.compile(r"(test_\w+) leaked \[.*]\ (.*),.*", re.MULTILINE)


class Logs:
    def __init__(self, raw_logs):
        self._logs = raw_logs

    @property
    def raw_logs(self):
        return self._logs

    def _get_test_results(self, header):
        test_regexp = re.compile(
            rf"""
             ^\d+\s{header}: # Lines starting with "header"
             [\s\S]+? # Match greedy any text (preserving ASCII flags).
             (?=^(?:\d|test|\Z|Total)) # Stop matching in lines starting with
                                       # a number (log time), "test" or the end
                                       # of the string.
            """,
            re.MULTILINE | re.VERBOSE,
        )

        failed_blocks = list(set(test_regexp.findall(self._logs)))
        if not failed_blocks:
            return set()
        # Pick the last re-run of the test
        block = failed_blocks[-1]
        tests = []
        for line in block.split("\n")[1:]:
            if not line:
                continue
            test_names = line.split(" ")
            tests.extend(test for test in test_names if test)
        return set(tests)

    def get_tracebacks(self):
        for traceback in set(TRACEBACK_REGEX.findall(self._logs)):
            yield traceback

    def get_leaks(self):
        for test_name, resource in set(LEAKS_REGEX.findall(self._logs)):
            yield (test_name, resource)

    def get_failed_tests(self):
        for test_name in set(self._get_test_results(r"tests?\sfailed")):
            yield test_name

    def get_rerun_tests(self):
        for test_name in set(self._get_test_results(r"re-run\stests?")):
            yield test_name

    def get_failed_subtests(self):
        failed_subtest_regexp = re.compile(
            r"=+"  # Decoration prefix
            r"\n[A-Z]+:"  # Test result (e.g. FAIL:)
            r"\s(\w+)\s"  # test name (e.g. test_tools)
            r"\((.*?)\)"  # subtest name (e.g. test.test_tools.test_unparse.DirectoryTestCase)
            r".*"  # Trailing text (e.g. filename)
            r"\n*"  # End of the line
            r".*" # Maybe some test description
            r"-+",  # Trailing decoration
            re.MULTILINE | re.VERBOSE
        )
        for test, subtest in set(failed_subtest_regexp.findall(self._logs)):
            yield (test, subtest)

    def test_summary(self):
        result_start = [
            match.start() for match in re.finditer("== Tests result", self._logs)
        ][-1]
        result_end = [
            match.start() for match in re.finditer("Tests result:", self._logs)
        ][-1]
        return self._logs[result_start:result_end]

    def format_failing_tests(self):

        text = []
        failed = list(self.get_failed_tests())
        if failed:
            text.append("Failed tests:\n")
            text.extend([f"- {test_name}" for test_name in failed])
            text.append("")
        failed_subtests = list(self.get_failed_subtests())
        if failed_subtests:
            text.append("Failed subtests:\n")
            text.extend([f"- {test} - {subtest}" for test, subtest in failed_subtests])
            text.append("")
        leaked = list(self.get_leaks())
        if leaked:
            text.append("Test leaking resources:\n")
            text.extend([f"- {test_name}: {resource}" for test_name, resource in leaked])
            text.append("")
        return "\n".join(text)


PR_MESSAGE = """\
:warning::warning::warning: Buildbot failure :warning::warning::warning:
------------------------------------------------------------------------

Hi! The buildbot **{buildername}** has failed when building commit {sha}.

What do you need to do:

1. Don't panic.
2. Check [the buildbot page in the devguide](https://devguide.python.org/buildbots/) \
if you don't know what the buildbots are or how they work.
3. Go to the page of the buildbot that failed ({build_url}) \
and take a look at the build logs.
4. Check if the failure is related to this commit ({sha}) or \
if it is a false positive.
5. If the failure is related to this commit, please, reflect \
that on the issue and make a new Pull Request with a fix.

You can take a look at the buildbot page here:

{build_url}

{failed_test_text}

Summary of the results of the build (if available):

{summary_text}

<details>
<summary>Click to see traceback logs</summary>

{tracebacks}

</details>
"""


class GitHubPullRequestReporter(reporters.GitHubStatusPush):

    name = "GitHubPullRequestReporter"

    @defer.inlineCallbacks
    def send(self, build):
        props = Properties.fromDict(build["properties"])
        props.master = self.master

        if build["complete"]:
            state = {
                SUCCESS: "success",
                WARNINGS: "success",
                FAILURE: "failure",
                SKIPPED: "success",
                EXCEPTION: "error",
                RETRY: "pending",
                CANCELLED: "error",
            }.get(build["results"], "error")
        else:
            return

        if state != "failure":
            return

        yield getDetailsForBuild(self.master, build, wantLogs=True, wantSteps=True)

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

        context = yield props.render(self.context)

        sourcestamps = build["buildset"].get("sourcestamps")

        if not sourcestamps or not sourcestamps[0]:
            return

        changes = yield self.master.data.get(("builds", build["buildid"], "changes"))

        if len(changes) != 1:
            return

        change_comments = changes["comments"]

        if not change_comments:
            return

        m = re.search(r"\((?:GH-|#)(\d+)\)", change_comments)

        if m is None:
            return

        issue = m.groups()[-1]

        project = sourcestamps[0]["project"]

        if "/" in project:
            repoOwner, repoName = project.split("/")
        else:
            giturl = giturlparse(sourcestamps[0]["repository"])
            repoOwner = giturl.owner
            repoName = giturl.repo

        if self.verbose:
            log.msg(
                "Updating github status: repoOwner={repoOwner}, repoName={repoName}".format(
                    repoOwner=repoOwner, repoName=repoName
                )
            )

        try:
            repo_user = repoOwner
            repo_name = repoName
            sha = change["revision"]
            target_url = build["url"]
            context = context
            yield self.createStatus(
                build=build,
                repo_user=repo_user,
                repo_name=repo_name,
                sha=sha,
                state=state,
                target_url=target_url,
                context=context,
                issue=issue,
                tracebacks=tracebacks,
                logs=logs,
            )
            if self.verbose:
                log.msg(
                    "Issued a Pull Request comment for {repoOwner}/{repoName} "
                    'at {sha}, context "{context}", issue {issue}.'.format(
                        repoOwner=repoOwner,
                        repoName=repoName,
                        sha=sha,
                        issue=issue,
                        context=context,
                    )
                )
        except Exception as e:
            log.err(
                e,
                "Failed to issue a Pull Request comment for {repoOwner}/{repoName} "
                'at {sha}, context "{context}", issue {issue}.'.format(
                    repoOwner=repoOwner,
                    repoName=repoName,
                    sha=sha,
                    issue=issue,
                    context=context,
                ),
            )

    def _getURLForBuild(self, builderid, build_number):
        prefix = self.master.config.buildbotURL
        return prefix + "#builders/%d/builds/%d" % (builderid, build_number)

    def _construct_tracebacks_from_stderr(self, build):
        for step in build["steps"]:
            try:
                test_log = step["logs"][0]["content"]["content"]
            except IndexError:
                continue
            test_log = "\n".join([line.lstrip("e") for line in test_log.splitlines()
                                  if line.startswith("e")])
            if not test_log:
                continue
            yield test_log

    def createStatus(
        self,
        build,
        repo_user,
        repo_name,
        sha,
        state,
        target_url=None,
        context=None,
        issue=None,
        tracebacks=None,
        logs=None,
    ):

        message = PR_MESSAGE.format(
            buildername=build["builder"]["name"],
            build_url=self._getURLForBuild(
                build["builder"]["builderid"], build["number"]
            ),
            sha=sha,
            tracebacks="```python-traceback\n{}\n```".format("\n\n".join(tracebacks)),
            summary_text=logs.test_summary(),
            failed_test_text=logs.format_failing_tests(),
        )

        payload = {"body": message}

        return self._http.post(
            "/".join(["/repos", repo_user, repo_name, "issues", issue, "comments"]),
            json=payload,
        )
