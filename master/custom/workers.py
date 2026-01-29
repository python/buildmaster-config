# -*- python -*-  vi:ft=python:
# kate: indent-mode python; hl python;
# vim:set ts=8 sw=4 sts=4 et:

from functools import partial

from buildbot.plugins import worker as _worker

from custom.factories import MAIN_BRANCH_NAME


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
        branches=None,
        not_branches=None,
        parallel_builders=None,
        parallel_tests=None,
        exclude_test_resources=None,
    ):
        self.name = name
        self.tags = tags or set()
        self.branches = branches
        self.not_branches = not_branches
        self.parallel_builders = parallel_builders
        self.parallel_tests = parallel_tests
        self.exclude_test_resources = exclude_test_resources
        worker_settings = settings.workers[name]
        owner = name.split("-")[0]
        owner_settings = settings.owners[owner]
        pw = worker_settings.get("password", None) or owner_settings.password
        owner_email = owner_settings.get("email", None)
        emails = [str(owner_email)] if owner_email else []
        if settings.use_local_worker:
            self.bb_worker = _worker.LocalWorker(name)
        else:
            self.bb_worker = _worker.Worker(name, str(pw),
                                            notify_on_missing=emails,
                                            keepalive_interval=KEEPALIVE)


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
            branches=['3.10', '3.11', '3.12'],
        ),
        cpw(
            name="cstratak-RHEL8-fips-x86_64",
            tags=['linux', 'unix', 'rhel', 'amd64', 'x86-64', 'fips'],
            parallel_tests=6,
            # Only 3.12 for RHEL8 FIPS builder
            branches=['3.12'],
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
            not_branches=["3.10", "3.11"],
        ),
        cpw(
            name="cstratak-fedora-rawhide-ppc64le",
            tags=['linux', 'unix', 'fedora', 'ppc64le'],
            parallel_tests=10,
        ),
        cpw(
            name="cstratak-fedora-stable-ppc64le",
            tags=['linux', 'unix', 'fedora', 'ppc64le'],
            parallel_tests=10,
        ),
        cpw(
            name="cstratak-RHEL8-ppc64le",
            tags=['linux', 'unix', 'rhel', 'ppc64le'],
            parallel_tests=10,
            branches=['3.10', '3.11', '3.12'],
        ),
        cpw(
            name="cstratak-CentOS9-ppc64le",
            tags=['linux', 'unix', 'rhel', 'ppc64le'],
            parallel_tests=10,
        ),
        cpw(
            name="cstratak-fedora-rawhide-aarch64",
            tags=['linux', 'unix', 'fedora', 'arm', 'arm64', 'aarch64'],
            parallel_tests=40,
        ),
        cpw(
            name="cstratak-fedora-stable-aarch64",
            tags=['linux', 'unix', 'fedora', 'arm', 'arm64', 'aarch64'],
            parallel_tests=40,
        ),
        cpw(
            name="cstratak-RHEL8-aarch64",
            tags=['linux', 'unix', 'rhel', 'arm', 'arm64', 'aarch64'],
            parallel_tests=40,
            branches=['3.10', '3.11', '3.12'],
        ),
        cpw(
            name="cstratak-CentOS9-aarch64",
            tags=['linux', 'unix', 'rhel', 'arm', 'arm64', 'aarch64'],
            parallel_tests=40,
        ),
        cpw(
            name="diegorusso-aarch64-bigmem",
            tags=['linux', 'unix', 'ubuntu', 'arm', 'arm64', 'aarch64', 'bigmem'],
            not_branches=['3.10', '3.11', '3.12', '3.13', '3.14'],
            parallel_tests=8,
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
            branches=['3.10', '3.11', '3.12'],
        ),
        cpw(
            name="cstratak-rhel9-s390x",
            tags=['linux', 'unix', 'rhel', 's390x'],
            parallel_tests=10,
        ),
        cpw(
            name="edelsohn-aix-ppc64",
            tags=['aix', 'unix', 'ppc64'],
            parallel_tests=10,
        ),
        cpw(
            name="gps-raspbian",
            tags=['linux', 'unix', 'raspbian', 'debian', 'armv6', 'armv7l',
                  'aarch32', 'arm'],
            parallel_tests=4,
        ),
        cpw(
            name="stan-raspbian",
            tags=['linux', 'unix', 'raspbian', 'debian', 'armv8',
                  'aarch64', 'arm'],
            parallel_tests=4,
            # Tests fail with latin1 encoding on 3.12, probably earlier
            not_branches=['3.12', '3.11', '3.10'],
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
        ),
        cpw(
            name="pablogsal-macos-m1",
            tags=['macOS', 'unix', 'arm', 'arm64'],
            parallel_tests=4,
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
            not_branches=['3.10', '3.11', '3.12', '3.13'],
            parallel_tests=6,
        ),
        cpw(
            name="ware-freebsd",
            tags=['freebsd', 'bsd', 'unix', 'amd64', 'x86-64'],
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
            name="linaro-win-arm64",
            tags=['windows', 'arm64'],
            parallel_tests=4,
        ),
        cpw(
            name="bcannon-wasi",
            tags=['wasm', 'wasi'],
            not_branches=['3.10'],
            parallel_tests=2,
            parallel_builders=2,
        ),
        cpw(
            name="ambv-bb-win11",
            tags=['windows', 'win11', 'amd64', 'x86-64', 'bigmem'],
            not_branches=['3.10', '3.11', '3.12', '3.13', '3.14'],
            parallel_tests=4,
        ),
        cpw(
            name="itamaro-centos-aws",
            tags=['linux', 'unix', 'rhel', 'amd64', 'x86-64'],
            not_branches=['3.10', '3.11', '3.12'],
            parallel_tests=10,
            parallel_builders=2,
        ),
        cpw(
            name="itamaro-win64-srv-22-aws",
            tags=['windows', 'win-srv-22', 'amd64', 'x86-64'],
            not_branches=['3.10', '3.11', '3.12'],
            parallel_tests=10,
            parallel_builders=2,
        ),
        cpw(
            name="itamaro-macos-intel-aws",
            tags=['macOS', 'unix', 'amd64', 'x86-64'],
            not_branches=['3.10', '3.11', '3.12'],
            parallel_tests=10,
        ),
        cpw(
            name="itamaro-macos-arm64-aws",
            tags=['macOS', 'unix', 'arm', 'arm64'],
            not_branches=['3.10', '3.11', '3.12'],
            parallel_tests=10,
        ),
        cpw(
            name="kushaldas-wasi",
            tags=['wasm', 'wasi'],
            not_branches=['3.10'],
            parallel_tests=4,
            parallel_builders=2,
        ),
        cpw(
            name="onder-riscv64",
            tags=['linux', 'unix', 'ubuntu', 'riscv64'],
            not_branches=['3.10'],
            parallel_tests=4,
        ),
        cpw(
            name="rkm-arm64-ios-simulator",
            tags=['iOS'],
            not_branches=['3.10', '3.11', '3.12'],
            parallel_builders=1,  # All builds use the same simulator
        ),
        cpw(
            name="rkm-emscripten",
            tags=['emscripten'],
            not_branches=['3.10', '3.11', '3.12', '3.13'],
            parallel_builders=4,
        ),
        cpw(
            name="mhsmith-android-aarch64",
            tags=['android'],
            not_branches=['3.10', '3.11', '3.12'],
            parallel_builders=1,  # All builds use the same emulator and app ID.
        ),
        cpw(
            name="mhsmith-android-x86_64",
            tags=['android'],
            not_branches=['3.10', '3.11', '3.12'],
            parallel_builders=1,  # All builds use the same emulator and app ID.
        ),
        cpw(
            name="malvex-nixos-x86_64",
            tags=['linux', 'unix', 'nixos', 'amd64', 'x86-64'],
            parallel_tests=10,
        ),
    ]
