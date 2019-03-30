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

TESTS_STEP = 4

TRACEBACK_REGEX = re.compile(
    r"""
     ^Traceback # Lines starting with "Traceback"
     [\s\S]+? # Match greedy any text (preserving ASCII flags).
     (?=^(?:\d|test|\Z)) # Stop matching in lines starting with
                         # a number (log time), "test" or the end
                         # of the string.
    """, re.MULTILINE | re.VERBOSE,
)

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

        tracebacks = list()
        try:
            test_log = build["steps"][TESTS_STEP]["logs"][0]["content"]["content"]
            test_log = "\n".join([line.lstrip("eo") for line in test_log.splitlines()])
            tracebacks = TRACEBACK_REGEX.findall(test_log)
        except IndexError:
            pass

        if not tracebacks:
            tracebacks = list(self._construct_tracebacks_from_stderr(build))

        context = yield props.render(self.context)

        sourcestamps = build["buildset"].get("sourcestamps")

        if not sourcestamps or not sourcestamps[0]:
            return

        changes = yield self.master.data.get(("builds", build["buildid"], "changes"))

        if len(changes) > 1:
            return

        change, = changes

        m = re.search(r"\((?:GH-|#)(\d+)\)", change["comments"])

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
    ):
        message = PR_MESSAGE.format(
            buildername=build["builder"]["name"],
            build_url=self._getURLForBuild(
                build["builder"]["builderid"], build["number"]
            ),
            sha=sha,
            tracebacks="```python-traceback\n{}\n```".format("\n\n".join(tracebacks)),
        )

        payload = {"body": message}

        return self._http.post(
            "/".join(["/repos", repo_user, repo_name, "issues", issue, "comments"]),
            json=payload,
        )
