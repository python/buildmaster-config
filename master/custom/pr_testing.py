# Functions to enable buildbot to test pull requests and report back
import re
import logging

from dateutil.parser import parse as dateparse

from twisted.internet import defer
from twisted.python import log

from buildbot.util import httpclientservice
from buildbot.www.hooks.github import GitHubEventHandler

TESTING_LABEL = ":hammer: test-with-buildbots"
REFLEAK_TESTING_LABEL = ":hammer: test-with-refleak-buildbots"

GITHUB_PROPERTIES_WHITELIST = ["*.labels"]

BUILD_SCHEDULED_MESSAGE = f"""\
:robot: New build scheduled with the buildbot fleet by @{{user}} for commit {{commit}} :robot:

If you want to schedule another build, you need to add the <kbd>{{label}}</kbd> label again.
"""

BUILD_COMMAND_SCHEDULED_MESSAGE = f"""\
:robot: New build scheduled with the buildbot fleet by @{{user}} for commit {{commit}} :robot:

The command will test the builders whose names match following regular expression: `{{filter}}`

The builders matched are:
{{builders}}
"""

BUILDBOT_COMMAND = re.compile(r"!buildbot (.+)")


def should_pr_be_tested(change):
    return change.properties.getProperty("should_test_pr", False)


class CustomGitHubEventHandler(GitHubEventHandler):
    def __init__(self, *args, builder_names, **kwargs):
        super().__init__(*args, **kwargs)
        self.builder_names = builder_names

    @defer.inlineCallbacks
    def _post_comment(self, comments_url, comment):
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

        yield http.post(
            comments_url.replace(self.github_api_endpoint, ""),
            json={"body": comment},
        )

    @defer.inlineCallbacks
    def _remove_label_and_comment(self, payload, label):
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
            json={
                "body": BUILD_SCHEDULED_MESSAGE.format(
                    user=username, commit=commit, label=label
                )
            },
        )

        # Remove the label
        url = payload["pull_request"]["issue_url"] + f"/labels/{label}"
        yield http.delete(url.replace(self.github_api_endpoint, ""))

    @defer.inlineCallbacks
    def _get_pull_request(self, url):
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
        res = yield http.get(url)
        if 200 <= res.code < 300:
            data = yield res.json()
            return data

        log.msg(f"Failed fetching PR from {url}: response code {res.code}")
        return None

    @defer.inlineCallbacks
    def _user_has_write_permissions(self, payload, user):
        """Check if *user* has write permissions"""

        repo = payload["repository"]["full_name"]
        url = f"https://api.github.com/repos/{repo}/collaborators/{user}/permission"
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
        res = yield http.get(url)
        if 200 <= res.code < 300:
            data = yield res.json()
            log.msg(f"User {user} has permission {data['permission']} on {repo}")
            return data["permission"] in {"admin", "write"}

        log.msg(
            f"Failed fetching user permissions from {url}: response code {res.code}"
        )
        return False

    def _get_changes_from_pull_request(
        self, changes, pr_number, payload, pull_request, event, builder_filter
    ):
        refname = "refs/pull/{}/{}".format(pr_number, self.pullrequest_ref)
        basename = pull_request["base"]["ref"]
        commits = pull_request["commits"]
        title = pull_request["title"]
        comments = pull_request["body"]
        properties = self.extractProperties(pull_request)
        properties.update({"should_test_pr": True})
        properties.update({"event": event})
        properties.update({"basename": basename})
        properties.update({"builderfilter": builder_filter})
        change = {
            "revision": pull_request["head"]["sha"],
            "when_timestamp": dateparse(pull_request["created_at"]),
            "branch": refname,
            "revlink": pull_request["_links"]["html"]["href"],
            "repository": payload["repository"]["html_url"],
            "project": pull_request["base"]["repo"]["full_name"],
            "category": "pull",
            "author": payload["sender"]["login"],
            "comments": "GitHub Pull Request #{0} ({1} commit{2})\n{3}\n{4}".format(
                pr_number, commits, "s" if commits != 1 else "", title, comments
            ),
            "properties": properties,
        }

        if callable(self._codebase):
            change["codebase"] = self._codebase(payload)
        elif self._codebase is not None:
            change["codebase"] = self._codebase

        changes.append(change)

        log.msg(
            "Received {} changes from GitHub PR #{}".format(len(changes), pr_number)
        )
        return (changes, "git")

    @defer.inlineCallbacks
    def handle_issue_comment(self, payload, event):
        changes = []
        number = payload["issue"]["number"]
        action = payload.get("action")

        # We only care about new comments
        if action != "created":
            log.msg(
                "GitHub PR #{} comment action is not 'created', ignoring".format(number)
            )
            return (changes, "git")

        # We only care about comments on PRs, not issues.
        if "pull_request" not in payload["issue"]:
            log.msg("GitHub PR #{} is not a pull request, ignoring".format(number))
            return (changes, "git")

        comment = payload["comment"]["body"].strip()

        match = BUILDBOT_COMMAND.match(comment)
        # If the comment is not a buildbot command, ignore it
        if not match:
            log.msg(
                "GitHub PR #{} comment is not a buildbot command, ignoring".format(
                    number
                )
            )
            return (changes, "git")

        builder_filter = match.group(1).strip()

        # If the command is empty, ignore it
        if not builder_filter:
            log.msg("GitHub PR #{} command is empty, ignoring".format(number))
            return (changes, "git")

        # If the command is not from a user with write permissions, ignore it
        if not (
            yield self._user_has_write_permissions(payload, payload["sender"]["login"])
        ):
            log.msg(
                "GitHub PR #{} user {} has no write permissions, ignoring".format(
                    number, payload["sender"]["login"]
                )
            )
            yield self._post_comment(
                payload["issue"]["comments_url"],
                "You don't have write permissions to trigger a build",
            )
            return (changes, "git")

        pull_url = payload["issue"]["pull_request"]["url"]

        # We need to fetch the PR data from GitHub because the payload doesn't
        # contain a lot of information we need.
        pull_request = yield self._get_pull_request(pull_url)
        if pull_request is None:
            log.msg("Failed to fetch PR #{} from {}".format(number, pull_url))
            return (changes, "git")

        repo_full_name = payload["repository"]["full_name"]
        head_sha = pull_request["head"]["sha"]

        log.msg("Processing GitHub PR #{}".format(number), logLevel=logging.DEBUG)

        head_msg = yield self._get_commit_msg(repo_full_name, head_sha)
        if self._has_skip(head_msg):
            log.msg(
                "GitHub PR #{}, Ignoring: "
                "head commit message contains skip pattern".format(number)
            )
            return ([], "git")

        builder_filter_fn = re.compile(builder_filter)
        yield self._post_comment(
            payload["issue"]["comments_url"],
            BUILD_COMMAND_SCHEDULED_MESSAGE.format(
                user=payload["sender"]["login"],
                commit=head_sha,
                filter=builder_filter,
                builders="\n".join(
                    {
                        f"- `{builder}`"
                        for builder in self.builder_names
                        if builder_filter_fn.match(builder)
                    }
                ),
            ),
        )

        return self._get_changes_from_pull_request(
            changes, number, payload, pull_request, event, builder_filter
        )

    @defer.inlineCallbacks
    def handle_pull_request(self, payload, event):

        changes = []
        number = payload["number"]
        action = payload.get("action")

        if action != "labeled":
            log.msg("GitHub PR #{} {}, ignoring".format(number, action))
            return (changes, "git")

        label = payload.get("label")["name"]
        if label not in {TESTING_LABEL, REFLEAK_TESTING_LABEL}:
            log.msg("Invalid label in PR #{}, ignoring".format(number))
            return (changes, "git")

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

        yield self._remove_label_and_comment(payload, label)

        builder_filter = ""
        if label == TESTING_LABEL:
            builder_filter = ".*"
        elif label == REFLEAK_TESTING_LABEL:
            builder_filter = ".*Refleaks.*"

        return self._get_changes_from_pull_request(
            changes, number, payload, payload["pull_request"], event, builder_filter
        )
