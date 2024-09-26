import datetime
import os
import time

from flask import Flask
from flask import render_template, request

from buildbot.data.resultspec import Filter

FAILED_BUILD_STATUS = 2

# Cache result for 5 minutes. Generating the page is slow and a Python build
# takes at least 5 minutes, a common build takes 10 to 30 minutes.
CACHE_DURATION = 5 * 60


def get_release_status_app(buildernames):
    release_status_app = Flask("test", root_path=os.path.dirname(__file__))
    buildernames = set(buildernames)
    cache = None

    def get_release_status():
        builders = release_status_app.buildbot_api.dataGet("/builders")

        failed_builds_by_branch_and_tier = {}
        disconnected_workers = {}

        for builder in builders:
            if builder["name"] not in buildernames:
                continue

            if "stable" not in builder["tags"]:
                continue

            for worker in release_status_app.buildbot_api.dataGet(
                ("builders", builder["builderid"], "workers"),
            ):
                if not worker["connected_to"]:
                    disconnected_workers[worker["name"]] = worker

            branch = None
            tier = 'no tier'
            for tag in builder["tags"]:
                if "3." in tag:
                    branch = tag
                if tag.startswith('tier-'):
                    tier = tag

            if not branch:
                continue

            failed_builds_by_tier = failed_builds_by_branch_and_tier.setdefault(branch, {})
            failed_builds = failed_builds_by_tier.setdefault(tier, [])

            endpoint = ("builders", builder["builderid"], "builds")
            last_build = release_status_app.buildbot_api.dataGet(
                endpoint,
                limit=1,
                order=["-complete_at"],
                filters=[Filter("complete", "eq", ["True"])],
            )
            if not last_build:
                continue

            (last_build,) = last_build

            if last_build["results"] != FAILED_BUILD_STATUS:
                continue

            failed_builds.append((builder, last_build))

        def tier_sort_key(item):
            tier, data = item
            if tier == 'no tier':
                return 'zzz'  # sort last
            return tier
        failed_builders = []
        for branch, failed_builds_by_tier in failed_builds_by_branch_and_tier.items():
            failed_builders.append((
                branch,
                sorted(failed_builds_by_tier.items(), key=tier_sort_key)
            ))
        failed_builders.sort(reverse=True)

        generated_at = datetime.datetime.now(tz=datetime.timezone.utc)

        return render_template(
            "releasedashboard.html",
            failed_builders=failed_builders,
            generated_at=generated_at,
            disconnected_workers=sorted(disconnected_workers.items()),
        )

    @release_status_app.route("/index.html")
    def main():
        nonlocal cache

        force_refresh = request.args.get("refresh", "").lower() in {"1", "yes", "true"}

        if cache is not None and not force_refresh:
            result, deadline = cache
            if time.monotonic() <= deadline:
                return result

        result = get_release_status()
        deadline = time.monotonic() + CACHE_DURATION
        cache = (result, deadline)
        return result

    return release_status_app
