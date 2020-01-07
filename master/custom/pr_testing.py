# Functions to enable buildbot to test pull requests and report back
import logging

from dateutil.parser import parse as dateparse

from twisted.internet import defer
from twisted.python import log

from buildbot.util import httpclientservice
from buildbot.www.hooks.github import GitHubEventHandler

TESTING_LABEL = ":hammer: test-with-buildbots"

GITHUB_PROPERTIES_WHITELIST = ["*.labels"]

BUILD_SCHEDULED_MESSAGE = f"""\
:robot: New build scheduled with the buildbot fleet by @{{user}} for commit {{commit}} :robot:

If you want to schedule another build, you need to add the "{TESTING_LABEL}" label again.
"""


def should_pr_be_tested(change):
    return change.properties.getProperty("should_test_pr", False)


class CustomGitHubEventHandler(GitHubEventHandler):
    @defer.inlineCallbacks
    def _remove_label_and_comment(self, payload):
        headers = {"User-Agent": "Buildbot"}
        if self._token:
            headers["Authorization"] = "token " + self._token

        http = yield httpclientservice.HTTPClientService.getService(
            self.master,
            self.github_api_endpoint,
            headers=headers,
            debug=self.debug,
            verify=self.verify,
        )

        # Create the comment
        url = payload["pull_request"]["comments_url"]
        username = payload["sender"]["login"]
        commit = payload["pull_request"]["head"]["sha"]
        yield http.post(
            url.replace(self.github_api_endpoint, ""),
            json={"body": BUILD_SCHEDULED_MESSAGE.format(user=username, commit=commit)},
        )

        # Remove the label
        url = payload["pull_request"]["issue_url"] + f"/labels/{TESTING_LABEL}"
        yield http.delete(url.replace(self.github_api_endpoint, ""))

    @defer.inlineCallbacks
    def handle_pull_request(self, payload, event):
        changes = []
        number = payload["number"]
        refname = "refs/pull/{}/{}".format(number, self.pullrequest_ref)
        basename = payload["pull_request"]["base"]["ref"]
        commits = payload["pull_request"]["commits"]
        title = payload["pull_request"]["title"]
        comments = payload["pull_request"]["body"]
        repo_full_name = payload["repository"]["full_name"]
        head_sha = payload["pull_request"]["head"]["sha"]

        log.msg("Processing GitHub PR #{}".format(number), logLevel=logging.DEBUG)

        head_msg = yield self._get_commit_msg(repo_full_name, head_sha)
        if self._has_skip(head_msg):
            log.msg(
                "GitHub PR #{}, Ignoring: "
                "head commit message contains skip pattern".format(number)
            )
            return ([], "git")

        action = payload.get("action")
        if action != "labeled":
            log.msg("GitHub PR #{} {}, ignoring".format(number, action))
            return (changes, "git")

        if payload.get("label")["name"] != TESTING_LABEL:
            log.msg("Invalid label in PR #{}, ignoring".format(number))
            return (changes, "git")

        yield self._remove_label_and_comment(payload)

        properties = self.extractProperties(payload["pull_request"])
        properties.update({"should_test_pr": True})
        properties.update({"event": event})
        properties.update({"basename": basename})
        change = {
            "revision": payload["pull_request"]["head"]["sha"],
            "when_timestamp": dateparse(payload["pull_request"]["created_at"]),
            "branch": refname,
            "revlink": payload["pull_request"]["_links"]["html"]["href"],
            "repository": payload["repository"]["html_url"],
            "project": payload["pull_request"]["base"]["repo"]["full_name"],
            "category": "pull",
            "author": payload["sender"]["login"],
            "comments": "GitHub Pull Request #{0} ({1} commit{2})\n{3}\n{4}".format(
                number, commits, "s" if commits != 1 else "", title, comments
            ),
            "properties": properties,
        }

        if callable(self._codebase):
            change["codebase"] = self._codebase(payload)
        elif self._codebase is not None:
            change["codebase"] = self._codebase

        changes.append(change)

        log.msg("Received {} changes from GitHub PR #{}".format(len(changes), number))
        return (changes, "git")
