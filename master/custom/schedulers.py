import re
from buildbot.schedulers.basic import AnyBranchScheduler
from twisted.internet import defer
from twisted.python import log


class GitHubPrScheduler(AnyBranchScheduler):
    @defer.inlineCallbacks
    def addBuildsetForChanges(self, **kwargs):
        log.msg("Preapring buildset for PR changes")
        changeids = kwargs.get("changeids")
        if changeids is None or len(changeids) != 1:
            log.msg("No changeids or more than one changeid found")
            yield super().addBuildsetForChanges(**kwargs)
            return

        changeid = changeids[0]
        chdict = yield self.master.db.changes.getChange(changeid)

        builder_filter = chdict["properties"].get("builderfilter", None)
        builder_names = kwargs.get("builderNames", self.builderNames)
        if builder_filter and builder_names:
            log.msg("Found builder filter: {}".format(builder_filter))
            builder_filter, _ = builder_filter
            matcher = re.compile(builder_filter)
            builder_names = [
                builder_name
                for builder_name in builder_names
                if matcher.match(builder_name)
            ]
            log.msg("Bulder names filtered: {}".format(builder_names))
            kwargs.update(builderNames=builder_names)
            yield super().addBuildsetForChanges(**kwargs)
            return

        log.msg("Scheduling regular non-filtered buildset")
        yield super().addBuildsetForChanges(**kwargs)
        return
