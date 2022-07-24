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

from custom.testsuite_utils import get_logs_and_tracebacks_from_build

MESSAGE = """\
:warning: **Buildbot failure** :warning:

The buildbot **{buildername}** has failed when building commit {sha}(https://github.com/python/cpython/commit/{sha}).

You can take a look at the buildbot page here:

{build_url}

```
{failed_test_text}
```
"""


class DiscordReporter(reporters.HttpStatusPush):
    name = "DiscordReporter"

    def __init__(self, *args, verbose=True, **kwargs):
        self.verbose = True
        super().__init__(*args, **kwargs)

    @defer.inlineCallbacks
    def sendMessage(self, reports):
        build = reports[0]["builds"][0]

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

        yield getDetailsForBuild(
            self.master, build, want_logs=True, want_logs_content=True, want_steps=True
        )

        logs, _ = get_logs_and_tracebacks_from_build(build)

        sourcestamps = build["buildset"].get("sourcestamps")

        if not (sourcestamps and sourcestamps[0]):
            return

        changes = yield self.master.data.get(("builds", build["buildid"], "changes"))

        if len(changes) != 1:
            return

        change = changes[0]
        change_comments = change["comments"]

        if not change_comments:
            return

        # GH-42, gh-42, or #42
        m = re.search(r"\((?:GH-|#)(\d+)\)", change_comments, flags=re.IGNORECASE)

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
            sha = change["revision"]
            yield self.createReport(
                build=build,
                sha=sha,
                logs=logs,
            )
            if self.verbose:
                log.msg(
                    "Issued a dicord comment for {repoOwner}/{repoName} "
                    "at {sha}, issue {issue}.".format(
                        repoOwner=repoOwner,
                        repoName=repoName,
                        sha=sha,
                        issue=issue,
                    )
                )
        except Exception as e:
            log.err(
                e,
                "Failed to issue a discord comment for {repoOwner}/{repoName} "
                "at {sha}, issue {issue}.".format(
                    repoOwner=repoOwner,
                    repoName=repoName,
                    sha=sha,
                    issue=issue,
                ),
            )

    def _getURLForBuild(self, builderid, build_number):
        prefix = self.master.config.buildbotURL
        return prefix + "#builders/%d/builds/%d" % (builderid, build_number)

    def createReport(
        self,
        build,
        sha,
        logs,
    ):

        message = MESSAGE.format(
            buildername=build["builder"]["name"],
            build_url=self._getURLForBuild(
                build["builder"]["builderid"], build["number"]
            ),
            sha=sha,
            failed_test_text=logs.format_failing_tests(),
        )

        payload = {"content": message, "embeds": []}

        return self._http.post("", json=payload)
