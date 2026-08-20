"""All the info about Buildbot branches

We treat the main branch specially, and we use a pseudo-branch for the
Pull Request buildbots.
In older branches some config needs to be nudged -- for example,
free-threading builds only make sense in 3.13+.

Complex enough to wrap up in a dataclass: BranchInfo.


Run this as a CLI command to print the info out:

    python master/custom/branches.py

"""

import collections.abc
import dataclasses
from functools import total_ordering
from typing import Any

# Buildbot configuration first; see below for the BranchInfo class.

def generate_branches():
    yield BranchInfo(
        '3.x',
        version_tuple=(3, 16),
        git_branch='main',
        is_main=True,
        builddir_name='3.x',
        builder_tag='3.x',
        sort_key=-9999,
    )
    yield _maintenance_branch(3, 15)
    yield _maintenance_branch(3, 14)
    yield _maintenance_branch(3, 13)
    yield _maintenance_branch(3, 12)
    yield _maintenance_branch(3, 11)
    yield _maintenance_branch(3, 10)
    yield BranchInfo(
        'PR',
        version_tuple=None,
        git_branch=None,
        is_pr=True,
        builddir_name='pull_request',
        builder_tag='PullRequest',
        sort_key=0,
    )


def _maintenance_branch(major, minor, **kwargs):
    version_tuple = (major, minor)
    version_str = f'{major}.{minor}'
    result = BranchInfo(
        name=version_str,
        builder_tag=version_str,
        version_tuple=version_tuple,
        git_branch=version_str,
        builddir_name=version_str,
        sort_key=-minor,
    )

    if version_tuple < (3, 11):
        # Before 3.11, test_asyncio wasn't split out, and refleaks tests
        # need more time.
        result.monolithic_test_asyncio = True

    if version_tuple < (3, 13):
        # Free-threaded builds are available since 3.13
        result.gil_only = True

    return result


@total_ordering
@dataclasses.dataclass
class BranchInfo:
    name: str
    version_tuple: tuple[int, int] | None
    git_branch: str | None
    builddir_name: str
    builder_tag: str

    sort_key: Any

    is_main: bool = False
    is_pr: bool = False

    # Branch features.
    # Defaults are for main (and PR), overrides are in _maintenance_branch.
    gil_only: bool = False
    monolithic_test_asyncio: bool = False

    def __str__(self):
        return self.name

    def __eq__(self, other):
        try:
            other_key = other.sort_key
        except AttributeError:
            return NotImplemented
        return self.sort_key == other.sort_key

    def __hash__(self):
        return hash(self.sort_key)

    def __lt__(self, other):
        try:
            other_key = other.sort_key
        except AttributeError:
            return NotImplemented
        return self.sort_key < other.sort_key


class BranchSet(collections.abc.Set):
    """An immutable set of BranchInfo objects, with some convenience API"""

    def __init__(self, branches):
        self._branches = tuple(branches)

    def __iter__(self):
        return iter(self._branches)

    def __len__(self):
        return len(self._branches)

    def __contains__(self, element):
        return element in self._branches

    def __getitem__(self, version_tuple):
        """branchset[3, x] -> BranchInfo for 3.x"""
        for branch in self._branches:
            if branch.version_tuple == version_tuple:
                return branch
        raise LookupError(f'version {version_tuple} not found')

    def only_since(self, major, minor, include_pr=True):
        """only_since(3, x) -> BranchSet with 3.x and later"""
        return BranchSet(
            b for b in self._branches if (
                include_pr if b.is_pr
                else b.version_tuple >= (major, minor)
            )
        )

    def only_until(self, major, minor, include_pr=False):
        """only_since(3, x) -> BranchSet with up to (and including) 3.x"""
        return BranchSet(
            b for b in self._branches if (
                include_pr if b.is_pr
                else b.version_tuple <= (major, minor)
            )
        )


BRANCHES = BranchSet(generate_branches())
[MAIN_BRANCH] = [b for b in BRANCHES if b.is_main]
[PR_BRANCH] = [b for b in BRANCHES if b.is_pr]

# Verify that the (sort) keys are distinct
assert len(set(BRANCHES)) == len(list(BRANCHES))

if __name__ == "__main__":
    # Print a table to the terminal
    cols = [[f.name + ':' for f in dataclasses.fields(BranchInfo)]]
    for branch in sorted(BRANCHES):
        cols.append([repr(val) for val in dataclasses.astuple(branch)])
    column_sizes = [max(len(val) for val in col) for col in cols]
    column_sizes[-2] += 2  # PR is special, offset it a bit
    for row in zip(*cols):
        for size, val in zip(column_sizes, row):
            print(val.ljust(size), end=' ')
        print()
