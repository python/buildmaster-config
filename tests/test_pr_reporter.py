import unittest
from unittest import mock

from twisted.internet import defer
from twisted.trial import unittest as trial

from custom.pr_reporter import GitHubPullRequestReporter


class PullRequestReporterTests(trial.TestCase):
    def test_create_status_waits_for_http_response(self):
        reporter = GitHubPullRequestReporter('example-token')
        reporter._getURLForBuild = mock.Mock(return_value='https://example.org/build')
        reporter._get_auth_header = mock.Mock(return_value=defer.succeed({}))
        pending = defer.Deferred()
        reporter._http = mock.Mock()
        reporter._http.post.return_value = pending
        result = reporter.createStatus(
            build={'builder': {'name': 'builder', 'builderid': 1, 'tags': []}, 'number': 2},
            repo_user='python', repo_name='cpython', sha='abc', state='failure',
            props=mock.Mock(), issue='123', tracebacks=[], logs=mock.Mock(),
        )
        self.assertNoResult(result)
        response = mock.Mock(code=201)
        pending.callback(response)
        self.assertIs(self.successResultOf(result), response)


if __name__ == '__main__':
    unittest.main()
