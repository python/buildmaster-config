from __future__ import absolute_import
from __future__ import print_function

import textwrap
import re

from twisted.internet import defer
from twisted.python import log

from buildbot.process.properties import Properties
from buildbot.process.results import CANCELLED
from buildbot.process.results import EXCEPTION
from buildbot.process.results import FAILURE
from buildbot.process.results import RETRY
from buildbot.process.results import SKIPPED
from buildbot.process.results import SUCCESS
from buildbot.process.results import WARNINGS
from buildbot.util import unicode2NativeString
from buildbot.util.giturlparse import giturlparse
from buildbot.plugins import reporters


class GitHubPullRequestReporter(reporters.GitHubStatusPush):
    @defer.inlineCallbacks
    def send(self, build):
        props = Properties.fromDict(build['properties'])
        props.master = self.master

        if build['complete']:
            state = {
                SUCCESS: 'success',
                WARNINGS: 'success',
                FAILURE: 'failure',
                SKIPPED: 'success',
                EXCEPTION: 'error',
                RETRY: 'pending',
                CANCELLED: 'error'
            }.get(build['results'], 'error')
        else:
            return

        if state != "failure":
            return

        context = yield props.render(self.context)

        sourcestamps = build['buildset'].get('sourcestamps')

        if not sourcestamps or not sourcestamps[0]:
            return

        changes = yield self.master.data.get(
                ("builds", build["buildid"], "changes"))

        if len(changes) > 1:
            return

        change, = changes

        m = re.search(r"\((?:GH-|#)(\d+)\)", change["comments"])

        if m is None:
            return

        issue = m.groups()[-1]

        project = sourcestamps[0]['project']

        if "/" in project:
            repoOwner, repoName = project.split('/')
        else:
            giturl = giturlparse(sourcestamps[0]['repository'])
            repoOwner = giturl.owner
            repoName = giturl.repo

        if self.verbose:
            log.msg("Updating github status: repoOwner={repoOwner}, repoName={repoName}".format(
                repoOwner=repoOwner, repoName=repoName))

        try:
            repo_user = unicode2NativeString(repoOwner)
            repo_name = unicode2NativeString(repoName)
            sha = unicode2NativeString(change["revision"])
            target_url = unicode2NativeString(build['url'])
            context = unicode2NativeString(context)
            yield self.createStatus(
                build=build,
                repo_user=repo_user,
                repo_name=repo_name,
                sha=sha,
                state=state,
                target_url=target_url,
                context=context,
                issue=issue,
            )
            if self.verbose:
                log.msg(
                    'Issued a Pull Request comment for {repoOwner}/{repoName} '
                    'at {sha}, context "{context}", issue {issue}.'.format(
                        repoOwner=repoOwner, repoName=repoName,
                        sha=sha, issue=issue, context=context))
        except Exception as e:
            log.err(
                e,
                'Failed to issue a Pull Request comment for {repoOwner}/{repoName} '
                'at {sha}, context "{context}", issue {issue}.'.format(
                    repoOwner=repoOwner, repoName=repoName,
                    sha=sha, issue=issue, context=context))

    def _getURLForBuild(self, builderid, build_number):
        prefix = self.master.config.buildbotURL
        return prefix + "#builders/%d/builds/%d" % (
            builderid,
            build_number)


    def createStatus(self,
                     build, repo_user, repo_name, sha, state, target_url=None,
                     context=None, issue=None):
        message = textwrap.dedent("""\
        Hi! The buildbot {buildername} has failed when building commit {sha}.

        You can take a look here:

        {build_url}
        """.format(
            buildername=build['builder']['name'],
            build_url=self._getURLForBuild(build['builder']['builderid'], build['number']),
            sha=sha,
            )
        )

        payload = {'body': message}

        return self._http.post( '/'.join(['/repos', repo_user, repo_name, 'issues', issue, 'comments']), json=payload)
