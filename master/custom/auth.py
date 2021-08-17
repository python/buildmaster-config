from buildbot.www.auth import NoAuth
from buildbot.plugins import util

from twisted.python import log


def set_up_authorization(settings):
    if bool(settings.do_auth):
        auth = util.GitHubAuth(
            clientId=str(settings.github_auth_id),
            clientSecret=str(settings.github_auth_secret),
            apiVersion=4,
            getTeamsMembership=True,
        )
        authz = util.Authz(
            allowRules=[
                # Admins can do anything.
                util.AnyEndpointMatcher(role="admins", defaultDeny=False),
                # Allow authors to stop, force or rebuild their own builds,
                # allow core devs to stop, force or rebuild any build.
                util.StopBuildEndpointMatcher(role="owner", defaultDeny=False),
                util.StopBuildEndpointMatcher(
                    role="buildbot-owners", defaultDeny=False
                ),
                util.StopBuildEndpointMatcher(role="python-triage", defaultDeny=False),
                util.StopBuildEndpointMatcher(role="python-core"),
                util.RebuildBuildEndpointMatcher(role="owner", defaultDeny=False),
                util.RebuildBuildEndpointMatcher(
                    role="python-triage", defaultDeny=False
                ),
                util.RebuildBuildEndpointMatcher(
                    role="buildbot-owners", defaultDeny=False
                ),
                util.RebuildBuildEndpointMatcher(role="python-core"),
                util.ForceBuildEndpointMatcher(role="owner", defaultDeny=False),
                util.ForceBuildEndpointMatcher(role="python-triage", defaultDeny=False),
                util.ForceBuildEndpointMatcher(role="python-core"),
                # Allow release managers to enable/disable schedulers.
                util.EnableSchedulerEndpointMatcher(role="python-release-managers"),
                # Future-proof control endpoints.
                util.AnyControlEndpointMatcher(role="admins"),
            ],
            roleMatchers=[
                util.RolesFromGroups(groupPrefix="python/"),
                util.RolesFromOwner(role="owner"),
                util.RolesFromUsername(
                    roles=["admins"],
                    usernames=[
                        "zware",
                        "vstinner",
                        "bitdancer",
                        "pitrou",
                        "pablogsal",
                    ],
                ),
            ],
        )
    else:
        log.err("WARNING: Web UI is completely open")
        # Completely open
        auth = NoAuth()
        authz = util.Authz()

    return auth, authz
