import datetime
import os
import time
from functools import cached_property, total_ordering
import enum
from dataclasses import dataclass
import itertools
import urllib.request
import urllib.error
import json
from pathlib import Path
from xml.etree import ElementTree

from flask import Flask
from flask import render_template, request
import jinja2
import humanize

from buildbot.data.resultspec import Filter
import buildbot.process.results

N_BUILDS = 200
MAX_CHANGES = 50


# Cache result for 6 minutes. Generating the page is slow and a Python build
# takes at least 5 minutes, a common build takes 10 to 30 minutes.  There is a
# cronjob that forces a refresh every 5 minutes, so all human requests should
# get a cache hit.
CACHE_DURATION = 6 * 60

BRANCHES_URL = "https://raw.githubusercontent.com/python/devguide/main/include/release-cycle.json"


def _gimme_error(func):
    """Decorator to turn AttributeError into a different Exception

    jinja2 tends to swallow AttributeError or report it in some place it
    didn't happen. When that's a problem, use this decorator to get
    a usable traceback.
    """
    def decorated(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AttributeError as e:
            raise Exception(f'your error: {e!r}')
    return decorated


class DashboardObject:
    """Base wrapper for a dashboard object.

    Acts as a dict with the info we get (usually) from JSON API.

    All computed information should be cached using @cached_property.
    For a fresh view, discard all these objects and build them again.
    (Computing info on demand means the "for & if" logic in the template
    doesn't need to be duplicated in Python code.)

    Objects are arranged in a tree: every one (except the root) has a parent.
    (Cross-tree references must go through the root.)

    N.B.: In Jinja, mapping keys and attributes are interchangeable.
    Shadow the `info` dict wisely.
    """
    def __init__(self, parent, info):
        self._parent = parent
        self._root = parent._root
        self._info = info

    def __getitem__(self, key):
        return self._info[key]

    def dataGet(self, *args, **kwargs):
        """Call Buildbot API"""
        # Buildbot sets `buildbot_api` as an attribute on the WSGI app,
        # a bit later than we'd like. Get to it dynamically.
        return self._root._app.flask_app.buildbot_api.dataGet(*args, **kwargs)

    def __repr__(self):
        return f'<{type(self).__name__} at {id(self)}: {self._info}>'


class DashboardState(DashboardObject):
    """The root of our abstraction, a bit special.
    """
    def __init__(self, app):
        self._root = self
        self._app = app
        super().__init__(self, {})
        self._tiers = {}

    @cached_property
    def builders(self):
        active_builderids = set()
        for worker in self.workers:
            for cnf in worker["configured_on"]:
                active_builderids.add(cnf["builderid"])
        return [
            Builder(self, info)
            for info in self.dataGet("/builders")
            if info["builderid"] in active_builderids
        ]

    @cached_property
    def workers(self):
        return [Worker(self, info) for info in self.dataGet("/workers")]

    @cached_property
    def branches(self):
        branches = []
        for version, info in self._app.branch_info.items():
            if info['status'] == 'end-of-life':
                continue
            if info['branch'] == 'main':
                tag = '3.x'
            else:
                tag = version
            branches.append(Branch(self, {
                **info, 'version': version, 'tag': tag
            }))
        branches.append(self._no_branch)
        return branches

    @cached_property
    def _no_branch(self):
        return Branch(self, {'tag': 'no-branch'})

    @cached_property
    def tiers(self):
        tiers = [Tier(self, {'tag': f'tier-{n}'}) for n in range(1, 4)]
        tiers.append(self._no_tier)
        return tiers

    @cached_property
    def _no_tier(self):
        # Hack: 'tierless' sorts after 'tier-#' alphabetically,
        # so we don't need to use numeric priority to sort failures by tier
        return Tier(self, {'tag': 'tierless'})

    @cached_property
    def now(self):
        return datetime.datetime.now(tz=datetime.timezone.utc)


def cached_sorted_property(func=None, /, **sort_kwargs):
    """Like cached_property, but calls sorted() on the value

    This is sometimes used just to turn a generator into a list, as the
    Jinja template generally likes to know if sequences are empty.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            return sorted(func(*args, **kwargs), **sort_kwargs)
        return cached_property(wrapper)
    if func:
        return decorator(func)
    return decorator


@total_ordering
class Builder(DashboardObject):
    @cached_property
    def builds(self):
        endpoint = ("builders", self["builderid"], "builds")
        infos = self.dataGet(
            endpoint,
            limit=N_BUILDS,
            order=["-complete_at"],
            filters=[Filter("complete", "eq", ["True"])],
        )
        builds = []
        for info in infos:
            builds.append(Build(self, info))
        return [Build(self, info) for info in infos]

    @cached_property
    def tags(self):
        return frozenset(self["tags"])

    @cached_property
    def branch(self):
        for branch in self._parent.branches:
            if branch.tag in self.tags:
                return branch
        return self._parent._no_branch

    @cached_property
    def tier(self):
        for tier in self._parent.tiers:
            if tier.tag in self.tags:
                return tier
        return self._parent._no_tier

    @cached_property
    def is_stable(self):
        return 'stable' in self.tags

    @cached_property
    def is_release_blocking(self):
        return self.tier.value in (1, 2)

    def __lt__(self, other):
        return self["name"] < other["name"]

    def iter_interesting_builds(self):
        """Yield builds except unfinished/skipped/interrupted ones"""
        for build in self.builds:
            if build["results"] in (
                buildbot.process.results.SUCCESS,
                buildbot.process.results.WARNINGS,
                buildbot.process.results.FAILURE,
            ):
                yield build

    @cached_sorted_property()
    def problems(self):
        latest_build = None
        for build in self.iter_interesting_builds():
            latest_build = build
            break

        if not latest_build:
            yield NoBuilds(self)
            return
        elif latest_build["results"] == buildbot.process.results.WARNINGS:
            yield BuildWarning(latest_build)
        elif latest_build["results"] == buildbot.process.results.FAILURE:
            failing_streak = 0
            first_failing_build = None
            for build in self.iter_interesting_builds():
                if build["results"] == buildbot.process.results.FAILURE:
                    first_failing_build = build
                    continue
                elif build["results"] == buildbot.process.results.SUCCESS:
                    if latest_build != first_failing_build:
                        yield BuildFailure(latest_build, first_failing_build)
                    break
            else:
                yield BuildFailure(latest_build)

        if not self.connected_workers:
            yield BuilderDisconnected(self)

    @cached_sorted_property
    def connected_workers(self):
        for worker in self._root.workers:
            if worker["connected_to"]:
                for cnf in worker["configured_on"]:
                    if cnf["builderid"] == self["builderid"]:
                        yield worker

class Worker(DashboardObject):
    pass  # The JSON is fine! :)

@total_ordering
class _BranchTierBase(DashboardObject):
    """Base class for Branch and Tag"""
    # Branches have several kinds of names:
    # 'tag': '3.x' (used as key)
    # 'version': '3.14'
    # 'branch': 'main'
    # To prevent confusion, there's no 'name'

    @cached_property
    def tag(self):
        return self["tag"]

    def __hash__(self):
        return hash(self.tag)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.tag == other
        return self.sort_key == other.sort_key

    def __lt__(self, other):
        return self.sort_key < other.sort_key

    def __str__(self):
        return self.tag

@total_ordering
class Branch(_BranchTierBase):
    @cached_property
    def sort_key(self):
        if self.tag.startswith("3."):
            try:
                return (1, int(self.tag[2:]))
            except ValueError:
                return (2, 99)
        return (0, 0)

    @cached_property
    def title(self):
        if self.tag == '3.x':
            return 'main'
        return self.tag

    @cached_sorted_property()
    def problems(self):
        problems = []
        for builder in self._root.builders:
            if builder.branch == self:
                problems.extend(builder.problems)
        return problems

    @cached_property
    def featured_problem(self):
       try:
        try:
            return self.problems[0]
        except IndexError:
            return NoProblem()
       except AttributeError:
           raise SystemError

    def get_grouped_problems(self):
        def key(problem):
            return problem.description
        for d, problems in itertools.groupby(self.problems, key):
            yield d, list(problems)


class Tier(_BranchTierBase):
    @cached_property
    def value(self):
        if self.tag.startswith("tier-"):
            try:
                return int(self.tag[5:])
            except ValueError:
                pass
        return 99

    @cached_property
    def title(self):
        return self.tag.title()

    @cached_property
    def sort_key(self):
        return self.value

    @cached_property
    def is_release_blocking(self):
        return self.value in {1, 2}


class Build(DashboardObject):
    @cached_property
    def builder(self):
        assert self._parent["builderid"] == self["builderid"]
        return self._parent

    @cached_property
    def changes(self):
        infos = self.dataGet(
            ("builds", self["buildid"], "changes"),
            limit=MAX_CHANGES,
        )
        if len(infos) == MAX_CHANGES:
            # Buildbot lists changes since the last *successful* build,
            # so in a failing streak the list can get very big.
            # When this happens, it's probably better to pretend we don't have
            # any info (which we'll also get when information is
            # scrubbed after some months)
            return []
        return [Change(self, info) for info in infos]

    @cached_property
    def started_at(self):
        if self["started_at"]:
            return datetime.datetime.fromtimestamp(self["started_at"],
                                                   tz=datetime.timezone.utc)

    @cached_property
    def age(self):
        if self["started_at"]:
            return self._root.now - self.started_at

    @cached_property
    def results_symbol(self):
        if self["results"] == buildbot.process.results.FAILURE:
            return '\N{HEAVY BALLOT X}'
        if self["results"] == buildbot.process.results.WARNINGS:
            return '\N{WARNING SIGN}'
        if self["results"] == buildbot.process.results.SUCCESS:
            return '\N{HEAVY CHECK MARK}'
        if self["results"] == buildbot.process.results.SKIPPED:
            return '\N{CIRCLED MINUS}'
        if self["results"] == buildbot.process.results.EXCEPTION:
            return '\N{CIRCLED DIVISION SLASH}'
        if self["results"] == buildbot.process.results.RETRY:
            return '\N{ANTICLOCKWISE OPEN CIRCLE ARROW}'
        if self["results"] == buildbot.process.results.CANCELLED:
            return '\N{CIRCLED TIMES}'
        return str(self["results"])

    @cached_property
    def results_string(self):
        return buildbot.process.results.statusToString(self["results"])

    @cached_property
    def css_color_class(self):
        if self["results"] == buildbot.process.results.SUCCESS:
            return 'success'
        if self["results"] == buildbot.process.results.WARNINGS:
            return 'warning'
        if self["results"] == buildbot.process.results.FAILURE:
            return 'danger'
        return 'unknown'

    @cached_property
    def junit_results(self):
        filepath = (
            self._root._app.test_result_dir
            / self.builder.branch.tag
            / self.builder["name"]
            / f'build_{self["number"]}.xml'
        )
        try:
            file = filepath.open()
        except OSError:
            return None
        with file:
            etree = ElementTree.parse(file)
        result = JunitResult(self, {})
        for element in etree.iterfind('.//error/..'):
            result.add(element)
        return result

    @cached_property
    def duration(self):
        try:
            seconds = (
                self["complete_at"]
                - self["started_at"]
                - self["locks_duration_s"]
            )
        except (KeyError, TypeError):
            return None
        return datetime.timedelta(seconds=seconds)


class JunitResult(DashboardObject):
    def __init__(self, *args):
        super().__init__(*args)
        self.contents = {}
        self.errors = []
        self.error_types = set()

    def add(self, element):
        errors = []
        error_types = set()
        for error_elem in element.iterfind('error'):
            new_error = JunitError(self, {
                **error_elem.attrib,
                'text': error_elem.text,
            })
            errors.append(new_error)
            error_types.add(new_error["type"])
        result = self
        name_parts = element.attrib.get('name', '??').split('.')
        if name_parts[0] == 'test':
            name_parts.pop(0)
        for part in name_parts:
            result.error_types.update(error_types)
            result = result.contents.setdefault(part, JunitResult(self, {}))
        result.error_types.update(error_types)
        for error in errors:
            if error not in result.errors:
                # De-duplicate, since failing tests are re-run and often fail
                # the same way
                result.errors.extend(errors)


class JunitError(DashboardObject):
    def __eq__(self, other):
        return self._info == other._info


class Change(DashboardObject):
    pass


class Severity(enum.IntEnum):
    # "Headings" and concrete values are all sortable enum items

    NO_PROBLEM = enum.auto()
    no_builds_yet = enum.auto()
    disconnected_unstable_builder = enum.auto()
    unstable_warnings = enum.auto()
    unstable_builder_failure = enum.auto()

    TRIVIAL = enum.auto()
    stable_warnings = enum.auto()
    disconnected_stable_builder = enum.auto()
    disconnected_blocking_builder = enum.auto()

    CONCERNING = enum.auto()
    nonblocking_failure = enum.auto()

    BLOCKING = enum.auto()
    release_blocking_failure = enum.auto()

    @cached_property
    def css_color_class(self):
        if self >= Severity.BLOCKING:
            return 'danger'
        if self >= Severity.CONCERNING:
            return 'warning'
        return 'success'

    @cached_property
    def symbol(self):
        if self >= Severity.BLOCKING:
            return '\N{HEAVY BALLOT X}'
        if self >= Severity.CONCERNING:
            return '\N{WARNING SIGN}'
        return '\N{HEAVY CHECK MARK}'

    @cached_property
    def releasability(self):
        if self >= Severity.BLOCKING:
            return 'Unreleasable'
        if self >= Severity.CONCERNING:
            return 'Concern'
        return 'Releasable'


class Problem:
    def __str__(self):
        return self.description

    @cached_property
    def order_key(self):
        return -self.severity, self.description

    def __eq__(self, other):
        return self.order_key == other.order_key

    def __lt__(self, other):
        return self.order_key < other.order_key

    @cached_property
    def severity(self):
        self.severity, self.description = self.get_severity_and_description()
        return self.severity

    @cached_property
    def description(self):
        self.severity, self.description = self.get_severity_and_description()
        return self.description

    @property
    def affected_builds(self):
        return {}


@dataclass
class BuildFailure(Problem):
    """The most recent build failed"""
    latest_build: Build
    first_failing_build: 'Build | None' = None

    def get_severity_and_description(self):
        if not self.builder.is_stable:
            return Severity.unstable_builder_failure, "Unstable build failed"
        if self.builder.is_release_blocking:
            severity = Severity.release_blocking_failure
        else:
            severity = Severity.nonblocking_failure
        description = f"{self.builder.tier.title} build failed"
        return severity, description

    @property
    def builder(self):
        return self.latest_build.builder

    @cached_property
    def affected_builds(self):
        result = {"Latest build": self.latest_build}
        if self.first_failing_build:
            result["Breaking build"] = self.first_failing_build
        return result


@dataclass
class BuildWarning(Problem):
    """The most recent build warns"""
    build: Build

    def get_severity_and_description(self):
        # Description word order is different from BuildFailure, to tell these
        # apart at a glance
        if not self.builder.is_stable:
            return Severity.unstable_warnings, "Warnings from unstable build"
        severity = Severity.stable_warnings
        description = f"Warnings from {self.builder.tier.title} build"
        return severity, description

    @property
    def builder(self):
        return self.build.builder

    @cached_property
    def affected_builds(self):
        return {"Warning build": self.build}


@dataclass
class NoBuilds(Problem):
    """Builder has no finished builds yet"""
    builder: Builder

    description = "Builder has no builds"
    severity = Severity.no_builds_yet


@dataclass
class BuilderDisconnected(Problem):
    """Builder has no finished builds yet"""
    builder: Builder

    def get_severity_and_description(self):
       try:
        if not self.builder.is_stable:
            severity = Severity.disconnected_unstable_builder
            description = "Disconnected unstable builder"
        else:
            description = f"Disconnected {self.builder.tier.title} builder"
            if self.builder.is_release_blocking:
                severity = Severity.disconnected_blocking_builder
            else:
                severity = Severity.disconnected_stable_builder
        for build in self.builder.iter_interesting_builds():
            if build.age and build.age < datetime.timedelta(hours=6):
                description += ' (with recent build)'
                if severity >= Severity.BLOCKING:
                    severity = Severity.CONCERNING
                if severity >= Severity.CONCERNING:
                    severity = Severity.TRIVIAL
            break
        return severity, description
       except:
           raise SystemError


class NoProblem(Problem):
    """Dummy problem"""
    name = "Releasable"

    description = "No problem detected"
    severity = Severity.NO_PROBLEM


class ReleaseDashboard:
    # This doesn't get recreated for every render.
    # The Flask app and caches go here.
    def __init__(self, test_result_dir=None):
        self.flask_app = Flask("test", root_path=os.path.dirname(__file__))
        self.cache = None

        self._refresh_branch_info()

        self.flask_app.jinja_env.add_extension('jinja2.ext.loopcontrols')
        self.flask_app.jinja_env.undefined = jinja2.StrictUndefined

        self.test_result_dir = Path(test_result_dir)

        @self.flask_app.route('/')
        @self.flask_app.route("/index.html")
        def main():
            force_refresh = request.args.get("refresh", "").lower() in {"1", "yes", "true"}

            if self.cache is not None and not force_refresh:
                result, deadline = self.cache
                if time.monotonic() <= deadline:
                    return result

                try:
                    self._refresh_branch_info()
                except urllib.error.HTTPError:
                    pass

            result = self.get_release_status()
            deadline = time.monotonic() + CACHE_DURATION
            self.cache = (result, deadline)
            return result

        @self.flask_app.template_filter('first_line')
        def first_line(text):
            return text.partition('\n')[0]

        @self.flask_app.template_filter('committer_name')
        def committer_name(text):
            return text.partition(' <')[0]

        @self.flask_app.template_filter('format_datetime')
        def format_timestamp(dt):
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            ago = humanize.naturaldelta(now - dt)
            return f'{dt:%Y-%m-%d %H:%M:%S}, {ago} ago'

        @self.flask_app.template_filter('format_timedelta')
        def format_timedelta(delta):
            return humanize.naturaldelta(delta)

        @self.flask_app.template_filter('short_rm_name')
        def short_rm_name(full_name):
            # DEBT: this assumes the first word of a release manager's name
            # is a good way to call them.
            # When that's no longer true we should put a name in the data.
            return full_name.split()[0]

    def _refresh_branch_info(self):
        with urllib.request.urlopen(BRANCHES_URL) as file:
            self.branch_info = json.load(file)

    def get_release_status(self):
        state = DashboardState(self)

        return render_template(
            "releasedashboard.html",
            state=state,
            Severity=Severity,
            generated_at=state.now,
        )

def get_release_status_app(buildernames=None, **kwargs):
    return ReleaseDashboard(**kwargs).flask_app
