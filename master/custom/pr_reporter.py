import re
import logging

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

from custom.testsuite_utils import get_logs_and_tracebacks_from_build

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
    def sendMessage(self, reports):
        build = reports[0]['builds'][0]
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

        buildid = build.get('buildid', "???")
        log.msg("Considering reporting build :{}".format(buildid), logLevel=logging.INFO)

        if state != "failure":
            log.msg(
                f"Not reporting build {buildid};"
                f" state is {state!r} (from {build['results']!r}),"
                f" not failure ({FAILURE!r})",
                logLevel=logging.INFO,
            )
            return

        yield getDetailsForBuild(self.master, build, want_logs=True, want_logs_content=True, want_steps=True)

        logs, tracebacks = get_logs_and_tracebacks_from_build(build)

        context = yield props.render(self.context)

        sourcestamps = build["buildset"].get("sourcestamps")

        if not (sourcestamps and sourcestamps[0]):
            log.msg("Build {} not reported as it doesn't have source stamps".format(buildid), logLevel=logging.INFO)
            return

        changes = yield self.master.data.get(("builds", build["buildid"], "changes"))

        if len(changes) != 1:
            log.msg("Build {} not reported as it has more than one change".format(buildid), logLevel=logging.INFO)
            return

        change = changes[0]
        change_comments = change["comments"]

        if not change_comments:
            log.msg("Build {} not reported as no change comments could be found".format(buildid), logLevel=logging.INFO)
            return

        # GH-42, gh-42, or #42
        m = re.search(r"\((?:GH-|#)(\d+)\)", change_comments, flags=re.IGNORECASE)

        if m is None:
            log.msg("Build {} not reported as the issue could not be identified from the title".format(
buildid), logLevel=logging.INFO)
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

        log.msg("Attempting to issue a PR comment for failed build for build {}".format(buildid), logLevel=logging.INFO)
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
        prefix = self.master.config.buildbotURL.rstrip('/')
        return f"{prefix}/#/builders/{builderid}/builds/{build_number}"

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
