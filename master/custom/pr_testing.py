# Functions to enable buildbot to test pull requests and report back
import logging

from dateutil.parser import parse as dateparse

from twisted.internet import defer
from twisted.python import log

from buildbot.www.hooks.github import GitHubEventHandler

TESTING_LABEL = ":hammer: test-with-buildbots"

GITHUB_PROPERTIES_WHITELIST = ["*.labels"]


def should_pr_be_tested(change):
    if TESTING_LABEL in {
        label["name"]
        for label in change.properties.asDict().get("github.labels", [set()])[0]
    }:
        log.msg(f"Label detected in PR {change.branch} (commit {change.revision})",
                logLevel=logging.DEBUG)
        return True
    log.msg(f"Label not found in PR {change.branch} (commit {change.revision})",
            logLevel=logging.DEBUG)
    return False


class CustomGitHubEventHandler(GitHubEventHandler):
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
        if action not in ("opened", "reopened", "synchronize", "labeled"):
            log.msg("GitHub PR #{} {}, ignoring".format(number, action))
            return (changes, "git")

        if action == "labeled" and payload.get("label")["name"] != TESTING_LABEL:
            log.msg("Invalid label in PR #{}, ignoring".format(number))
            return (changes, "git")
        elif TESTING_LABEL not in {
            label["name"] for label in payload.get("pull_request")["labels"]
        }:
            log.msg("Invalid label in PR #{}, ignoring".format(number))
            return (changes, "git")

        properties = self.extractProperties(payload["pull_request"])
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
