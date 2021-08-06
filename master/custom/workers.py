# -*- python -*-  vi:ft=python:
# kate: indent-mode python; hl python;
# vim:set ts=8 sw=4 sts=4 et:

from functools import partial

from buildbot.plugins import worker as _worker


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
        parallel_builders=None,
        parallel_tests=None,
    ):
        self.name = name
        self.tags = tags or set()
        self.branches = branches
        self.parallel_builders = parallel_builders
        self.parallel_tests = parallel_tests
        worker_settings = settings.workers[name]
        owner = name.split("-")[0]
        owner_settings = settings.owners[owner]
        pw = worker_settings.get("password", None) or owner_settings.password
        owner_email = owner_settings.get("email", None)
        emails = list(
            map(str, filter(None, (settings.get("status_email", None), owner_email)))
        )
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
            name="bolen-windows7",
            tags=['windows', 'win7', 'x86'],
        ),
        cpw(
            name="bray-win10-cygwin-amd64",
            tags=['windows', 'win10', 'cygwin', 'unix', 'amd64', 'x86-64'],
            branches=['3.x'],
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
            name="cstratak-RHEL7-x86_64",
            tags=['linux', 'unix', 'rhel', 'amd64', 'x86-64'],
            parallel_tests=10,
        ),
        cpw(
            name="cstratak-RHEL8-x86_64",
            tags=['linux', 'unix', 'rhel', 'amd64', 'x86-64'],
            parallel_tests=10,
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
            name="cstratak-RHEL7-ppc64le",
            tags=['linux', 'unix', 'rhel', 'ppc64le'],
            parallel_tests=10,
        ),
        cpw(
            name="cstratak-RHEL8-ppc64le",
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
        ),
        cpw(
            name="cstratak-RHEL8-fips-x86_64",
            tags=['linux', 'unix', 'rhel', 'amd64', 'x86-64'],
            parallel_tests=6,
        ),
        cpw(
            name="edelsohn-aix-ppc64",
            tags=['aix', 'unix', 'ppc64'],
            branches=['3.8', '3.9', '3.10', '3.x'],
            parallel_tests=10,
        ),
        cpw(
            name="edelsohn-debian-z",
            tags=['linux', 'unix', 'debian', 's390x'],
            parallel_tests=6,
        ),
        cpw(
            name="edelsohn-fedora-rawhide-z",
            tags=['linux', 'unix', 'fedora', 's390x'],
            parallel_tests=6,
        ),
        cpw(
            name="edelsohn-fedora-ppc64",
            tags=['linux', 'unix', 'fedora', 'ppc64'],
        ),
        cpw(
            name="edelsohn-fedora-z",
            tags=['linux', 'unix', 'fedora', 's390x'],
            parallel_tests=6,
        ),
        cpw(
            name="edelsohn-rhel-z",
            tags=['linux', 'unix', 'rhel', 's390x'],
            parallel_tests=6,
        ),
        cpw(
            name="edelsohn-rhel8-z",
            tags=['linux', 'unix', 'rhel', 's390x'],
            parallel_tests=6,
        ),
        cpw(
            name="edelsohn-sles-z",
            tags=['linux', 'unix', 'sles', 's390x'],
            parallel_tests=6,
        ),
        cpw(
            name="gps-clang-ubsan",
            tags=['linux', 'unix', 'amd64', 'x86-64'],
        ),
        cpw(
            name="gps-debian-profile-opt",
            tags=['linux', 'unix', 'debian', 'amd64', 'x86-64'],
        ),
        cpw(
            name="gps-raspbian",
            tags=['linux', 'unix', 'raspbian', 'debian', 'armv6', 'armv7l',
                  'aarch32', 'arm'],
            parallel_tests=6,
        ),
        cpw(
            name="isidentical-centos-power8",
            tags=['linux', 'unix', 'centos', 'power8'],
            parallel_tests=4,
            branches=['3.8', '3.9', '3.10', '3.x'],
        ),
        cpw(
            name="kloth-win64",
            tags=['windows', 'win10', 'amd64', 'x86-64'],
            parallel_tests=8,
        ),
        cpw(
            name="kloth-win7",
            tags=['windows', 'win7', 'amd64', 'x86-64'],
            parallel_tests=6,
        ),
        cpw(
            name="koobs-freebsd-9e36",
            tags=['bsd', 'unix', 'freebsd', 'amd64', 'x86-64'],
            parallel_tests=4,
        ),
        cpw(
            name="koobs-freebsd-564d",
            tags=['bsd', 'unix', 'freebsd', 'amd64', 'x86-64'],
            parallel_tests=4,
        ),
        cpw(
            name="monson-win-arm32",
            tags=['windows', 'win10', 'arm', 'arm32'],
            branches=['3.x'],
        ),
        cpw(
            name="pablogsal-arch-x86_64",
            tags=['linux', 'unix', 'arch', 'amd64', 'x86-64'],
        ),
        cpw(
            name="skumaran-ubuntu-x86_64",
            tags=['linux', 'unix', 'ubuntu', 'amd64', 'x86-64'],
        ),
        cpw(
            name="ware-alpine",
            tags=['linux', 'unix', 'alpine', 'docker', 'amd64', 'x86-64'],
            branches=['3.x'],
        ),
        cpw(
            name="ware-gentoo-x86",
            tags=['linux', 'unix', 'gentoo', 'x86'],
            parallel_builders=2,
        ),
        cpw(
            name="ware-win81-release",
            tags=['windows', 'win8', 'amd64', 'x86-64'],
            parallel_tests=4,
        ),
    ]
