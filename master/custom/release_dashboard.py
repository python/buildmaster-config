import os

from flask import Flask
from flask import render_template

from buildbot.process.results import statusToString
from buildbot.data.resultspec import Filter

FAILED_BUILD_STATUS = 2


def get_release_status_app(buildernames):
    release_status_app = Flask("test", root_path=os.path.dirname(__file__))

    buildernames = set(buildernames)

    @release_status_app.route("/index.html")
    def main():
        builders = release_status_app.buildbot_api.dataGet("/builders")

        failed_builds_by_branch = {}

        for builder in builders:
            if builder["name"] not in buildernames:
                continue

            if "stable" not in builder["tags"]:
                continue

            branch = [tag for tag in builder["tags"] if "3." in tag]

            if not branch:
                continue

            (branch,) = branch

            if branch not in failed_builds_by_branch:
                failed_builds_by_branch[branch] = []

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

            failed_builds_by_branch[branch].append((builder, last_build))

        failed_builders = sorted(failed_builds_by_branch.items(), reverse=True)
        return render_template("releasedashboard.html", failed_builders=failed_builders)

    return release_status_app
