# -*- python -*-  vi:ft=python:
# kate: indent-mode python; hl python;
# vim:set ts=8 sw=4 sts=4 et:

from functools import partial
from zoneinfo import ZoneInfo
import calendar

from buildbot.plugins import worker as _worker

from custom.worker_downtime import no_builds_between
from custom.branches import BRANCHES, MAIN_BRANCH, PR_BRANCH

# List of workers.
# See also: Buildbot worker documentation, http://docs.buildbot.net/current/manual/configuration/workers.html#defining-workers



# By default, the buildmaster sends a simple, non-blocking message to each
# worker every hour. These keepalives ensure that traffic is flowing over the
# underlying TCP connection, allowing the system’s network stack to detect any
# problems before a build is started.
#
# The default is 3600 seconds. Use a shorter interval to avoid
# "lost remote step" on the worker side.
# https://bugs.python.org/issue41642
KEEPALIVE = 60


class CPythonWorker:
    def __init__(
        self,
        settings,
        name,
        tags=None,
        branches=BRANCHES,
        parallel_builders=1,
        parallel_tests=None,
        timeout_factor=1,
        exclude_test_resources=None,
        downtime=None,
        git_options=None,
    ):
        self.name = name
        self.tags = tags or set()
        self.branches = branches
        self.parallel_tests = parallel_tests
        self.timeout_factor = timeout_factor
        self.exclude_test_resources = exclude_test_resources or []
        self.downtime = downtime
        self.git_options = git_options or {}

        for branch in branches:
            if isinstance(branch, str):
                raise TypeError('use BRANCHES for branch filtering')

        worker_settings = settings.workers[name]
        owner = name.split("-")[0]
        owner_settings = settings.owners[owner]
        pw = worker_settings.get("password", None) or owner_settings.password
        owner_email = owner_settings.get("email", None)
        emails = [str(owner_email)] if owner_email else []
        if settings.use_local_worker:
            self.bb_worker = _worker.LocalWorker(name)
        else:
            self.bb_worker = _worker.Worker(
                name,
                str(pw),
                notify_on_missing=emails,
                keepalive_interval=KEEPALIVE,
                max_builds=parallel_builders,
            )

# Some of Itamar's workers are reprovisioned every Wednesday at 9am PT.
# Builds scheduled between 8am - 10am PT on Wednesdays will be delayed to
# 10am PT.
itamaro_downtime = no_builds_between(
    "8:00", "10:00",
    day_of_week=calendar.WEDNESDAY,
    tz=ZoneInfo("America/Los_Angeles"),
)

def get_workers(settings):
    cpw = partial(CPythonWorker, settings)
    if settings.use_local_worker:
        return [cpw(name="local-worker")]
    return [
        cpw(
            name="angelico-debian-amd64",
            tags=['linux', 'unix', 'debian', 'amd64', 'x86-64'],
        ),
        cpw(
            name="billenstein-macos",
            tags=['macOS', 'unix', 'amd64', 'x86-64'],
        ),
        cpw(
            name="bolen-ubuntu",
            tags=['linux', 'unix', 'ubuntu', 'amd64', 'x86-64'],
        ),
        cpw(
            name="bolen-windows10",
            tags=['windows', 'win10', 'amd64', 'x86-64'],
        ),
        cpw(
            name="cstratak-fedora-rawhide-x86_64",
            tags=['linux', 'unix', 'fedora', 'amd64', 'x86-64'],
            parallel_tests=10,
        ),
        cpw(
            name="cstratak-fedora-stable-x86_64",
            tags=['linux', 'unix', 'fedora', 'amd64', 'x86-64'],
            parallel_tests=10,
        ),
        cpw(
            name="cstratak-RHEL8-x86_64",
            tags=['linux', 'unix', 'rhel', 'amd64', 'x86-64'],
            parallel_tests=10,
            branches=BRANCHES.only_until(3, 12),
        ),
        cpw(
            name="cstratak-RHEL8-fips-x86_64",
            tags=['linux', 'unix', 'rhel', 'amd64', 'x86-64', 'fips'],
            parallel_tests=6,
            # Only 3.12 for RHEL8 FIPS builder
            branches={BRANCHES[3, 12]},
        ),
        cpw(
            name="cstratak-CentOS9-x86_64",
            tags=['linux', 'unix', 'rhel', 'amd64', 'x86-64'],
            parallel_tests=6,
        ),
        cpw(
            name="cstratak-CentOS9-fips-x86_64",
            tags=['linux', 'unix', 'rhel', 'amd64', 'x86-64', 'fips'],
            parallel_tests=6,
            # Only 3.12+ for FIPS builder
            branches=BRANCHES.only_since(3, 12),
        ),
        cpw(
            name="cstratak-fedora-rawhide-ppc64le",
            tags=['linux', 'unix', 'fedora', 'ppc64le'],
            parallel_tests=10,
            timeout_factor=2,  # Increase the timeout on this slow worker
        ),
        cpw(
            name="cstratak-fedora-stable-ppc64le",
            tags=['linux', 'unix', 'fedora', 'ppc64le'],
            parallel_tests=10,
            timeout_factor=2,  # Increase the timeout on this slow worker
        ),
        cpw(
            name="cstratak-RHEL8-ppc64le",
            tags=['linux', 'unix', 'rhel', 'ppc64le'],
            parallel_tests=10,
            branches=BRANCHES.only_until(3, 12),
            timeout_factor=2,  # Increase the timeout on this slow worker
        ),
        cpw(
            name="cstratak-CentOS9-ppc64le",
            tags=['linux', 'unix', 'rhel', 'ppc64le'],
            parallel_tests=10,
            timeout_factor=2,  # Increase the timeout on this slow worker
        ),
        cpw(
            name="cstratak-fedora-rawhide-aarch64",
            tags=['linux', 'unix', 'fedora', 'arm', 'arm64', 'aarch64'],
            parallel_tests=32,
        ),
        cpw(
            name="cstratak-fedora-stable-aarch64",
            tags=['linux', 'unix', 'fedora', 'arm', 'arm64', 'aarch64'],
            parallel_tests=32,
        ),
        cpw(
            name="cstratak-RHEL8-aarch64",
            tags=['linux', 'unix', 'rhel', 'arm', 'arm64', 'aarch64'],
            parallel_tests=32,
            branches=BRANCHES.only_until(3, 12),
        ),
        cpw(
            name="cstratak-CentOS9-aarch64",
            tags=['linux', 'unix', 'rhel', 'arm', 'arm64', 'aarch64'],
            parallel_tests=32,
        ),
        cpw(
            name="cstratak-CentOS10-aarch64",
            tags=['linux', 'unix', 'rhel', 'arm', 'arm64', 'aarch64'],
            parallel_tests=32,
        ),
        cpw(
            name="diegorusso-aarch64-bigmem",
            tags=['linux', 'unix', 'ubuntu', 'arm', 'arm64', 'aarch64', 'bigmem'],
            branches={MAIN_BRANCH, PR_BRANCH},
            parallel_tests=8,
            # This worker runs pyperformance for speed.python.org at 12am UTC.
            # The pyperformance run lasts less than 2h.
            # From 2am to 8am the node runs GH benchmarks for https://www.doesjitgobrrr.com
            # The node is connected here: https://github.com/diegorusso/pyperf-bench
            # If a build is scheduled between 10pm UTC and 8am UTC,
            # it will be delayed to 8am UTC.
            downtime=no_builds_between("22:00", "8:00")
        ),
        cpw(
            name="cstratak-fedora-rawhide-s390x",
            tags=['linux', 'unix', 'fedora', 's390x'],
            parallel_tests=10,
        ),
        cpw(
            name="cstratak-fedora-stable-s390x",
            tags=['linux', 'unix', 'fedora', 's390x'],
            parallel_tests=10,
        ),
        cpw(
            name="cstratak-rhel8-s390x",
            tags=['linux', 'unix', 'rhel', 's390x'],
            parallel_tests=10,
            branches=BRANCHES.only_until(3, 12),
        ),
        cpw(
            name="cstratak-rhel9-s390x",
            tags=['linux', 'unix', 'rhel', 's390x'],
            parallel_tests=10,
        ),
        cpw(
            name="cstratak-c10s-s390x",
            tags=['linux', 'unix', 'rhel', 's390x'],
            parallel_tests=10,
        ),
        cpw(
            name="gps-raspbian",
            tags=['linux', 'unix', 'raspbian', 'debian', 'armv6', 'armv7l',
                  'aarch32', 'arm'],
            parallel_tests=4,
        ),
        cpw(
            name="rise-riscv64-2",
            tags=['linux', 'unix', 'ubuntu', 'riscv64'],
            not_branches=['3.10'],
            parallel_tests=4,
        ),
        cpw(
            name="rise-riscv64-3",
            tags=['linux', 'unix', 'ubuntu', 'riscv64'],
            not_branches=['3.10'],
            parallel_tests=4,
        ),
        cpw(
            name="rise-riscv64-4",
            tags=['linux', 'unix', 'ubuntu', 'riscv64'],
            not_branches=['3.10'],
            parallel_tests=4,
        ),
        cpw(
            name="stan-aarch64-ubuntu",
            tags=['linux', 'unix', 'ubuntu', 'arm', 'arm64', 'aarch64'],
            parallel_tests=4,
            # test_xpickle was added in 3.13
            branches=BRANCHES.only_since(3, 13),
        ),
        cpw(
            name="stan-raspbian",
            tags=['linux', 'unix', 'raspbian', 'debian', 'armv8',
                  'aarch64', 'arm'],
            parallel_tests=4,
            # Tests fail with latin1 encoding on 3.12, probably earlier
            branches=BRANCHES.only_since(3, 13),
            # Problematic ISP causes issues connecting to testpython.net
            exclude_test_resources=['urlfetch', 'network'],
        ),
        cpw(
            name="savannah-raspbian",
            tags=['linux', 'unix', 'raspbian', 'debian', 'armv8',
                  'aarch64', 'arm'],
            parallel_tests=4,
        ),
        cpw(
            name="kulikjak-solaris-sparcv9",
            tags=['solaris', 'unix', 'sparc', 'sparcv9'],
            parallel_tests=16,
        ),
        cpw(
            name="pablogsal-arch-x86_64",
            tags=['linux', 'unix', 'arch', 'amd64', 'x86-64'],
            # Problematic ISP causes issues connecting to testpython.net
            exclude_test_resources=['urlfetch', 'network'],
        ),
        cpw(
            name="pablogsal-macos-m1",
            tags=['macOS', 'unix', 'arm', 'arm64'],
            parallel_tests=4,
            # Problematic ISP causes issues connecting to testpython.net
            exclude_test_resources=['urlfetch', 'network'],
        ),
        cpw(
            name="pablogsal-rasp",
            tags=['linux', 'unix', 'raspbian', 'debian', 'arm'],
            parallel_tests=1,  # Reduced from 2: ASAN builds use 2-10x more memory
            # Problematic ISP causes issues connecting to testpython.net
            exclude_test_resources=['urlfetch', 'network'],
        ),
        cpw(
            name="skumaran-ubuntu-x86_64",
            tags=['linux', 'unix', 'ubuntu', 'amd64', 'x86-64'],
        ),
        cpw(
            name="ware-alpine",
            tags=['linux', 'unix', 'alpine', 'docker', 'amd64', 'x86-64', 'musl'],
            branches=BRANCHES.only_since(3, 14),
            parallel_tests=6,
        ),
        cpw(
            name="opsec-fbsd14",
            tags=['freebsd', 'bsd', 'unix', 'amd64', 'x86-64'],
            parallel_tests=4,
        ),
        cpw(
            name="opsec-fbsd15",
            tags=['freebsd', 'bsd', 'unix', 'amd64', 'x86-64'],
            parallel_tests=4,
        ),
        cpw(
            name="opsec-fbsd16",
            tags=['freebsd', 'bsd', 'unix', 'amd64', 'x86-64'],
            parallel_tests=4,
        ),
        cpw(
            name="ware-debian-x86",
            tags=['linux', 'unix', 'debian', 'x86'],
            parallel_tests=6,
        ),
        cpw(
            name="ware-win11",
            tags=['windows', 'win11', 'amd64', 'x86-64'],
            parallel_tests=2,
        ),
        cpw(
            name="ware-win11-arm64",
            tags=['windows', 'win11', 'arm64'],
            parallel_tests=8,
            branches=BRANCHES.only_since(3, 13),
            git_options=dict(
                # Do a full shallow clone for every build
                mode="full",
                method="clobber",
                shallow=True,
                # Disable the default, if set
                filters=None,
            ),
        ),
        cpw(
            name="bcannon-wasi",
            tags=['wasm', 'wasi'],
            branches=BRANCHES.only_since(3, 11),
            parallel_tests=2,
            parallel_builders=2,
            timeout_factor=2,  # Increase the timeout on this slow worker
        ),
        cpw(
            name="itamaro-centos-aws",
            tags=['linux', 'unix', 'rhel', 'amd64', 'x86-64'],
            branches=BRANCHES.only_since(3, 14),
            parallel_tests=10,
            parallel_builders=2,
            downtime=itamaro_downtime,
        ),
        cpw(
            name="itamaro-win64-srv-22-aws",
            tags=['windows', 'win-srv-22', 'amd64', 'x86-64'],
            branches=BRANCHES.only_since(3, 14),
            parallel_tests=20,
            # Parallel MSBuild builds are "unusual", and more likely to hit obscure bugs
            # (such as file locking issues across builds)
            # Explicit limit parallel builders to 1 to avoid such issues
            # https://github.com/python/cpython/issues/148255#issuecomment-4534972557
            parallel_builders=1,
            downtime=itamaro_downtime,
        ),
        cpw(
            name="itamaro-macos-intel-aws",
            tags=['macOS', 'unix', 'amd64', 'x86-64'],
            branches=BRANCHES.only_since(3, 14),
            parallel_tests=10,
        ),
        cpw(
            name="itamaro-macos-arm64-aws",
            tags=['macOS', 'unix', 'arm', 'arm64'],
            branches=BRANCHES.only_since(3, 14),
            parallel_tests=10,
        ),
        cpw(
            name="kushaldas-wasi",
            tags=['wasm', 'wasi'],
            branches=BRANCHES.only_since(3, 11),
            parallel_tests=4,
            parallel_builders=2,
        ),
        cpw(
            name="onder-riscv64",
            tags=['linux', 'unix', 'ubuntu', 'riscv64'],
            branches=BRANCHES.only_since(3, 11),
            parallel_tests=4,
        ),
        cpw(
            name="rkm-arm64-ios-simulator",
            tags=['iOS'],
            branches=BRANCHES.only_since(3, 13),
            parallel_builders=1,  # All builds use the same simulator
        ),
        cpw(
            name="rkm-emscripten",
            tags=['emscripten'],
            branches=BRANCHES.only_since(3, 14),
            parallel_builders=4,
        ),
        cpw(
            name="mhsmith-android-aarch64",
            tags=['android'],
            branches=BRANCHES.only_since(3, 13),
            parallel_builders=1,  # All builds use the same emulator and app ID.
        ),
        cpw(
            name="mhsmith-android-x86_64",
            tags=['android'],
            branches=BRANCHES.only_since(3, 13),
            parallel_builders=1,  # All builds use the same emulator and app ID.
        ),
        cpw(
            name="malvex-nixos-x86_64",
            tags=['linux', 'unix', 'nixos', 'amd64', 'x86-64'],
            parallel_tests=10,
        ),
    ]
