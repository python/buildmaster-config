import os.path
from buildbot.process import factory
from buildbot.steps.shell import (
    Configure,
    Compile,
    ShellCommand,
    SetPropertyFromCommand,
)

from buildbot.plugins import util

from . import (MAIN_BRANCH_VERSION, MAIN_BRANCH_NAME,
               JUNIT_FILENAME)
from .steps import (
    Test,
    Clean,
    Install,
    LockInstall,
    Uninstall,
    UploadTestResults,
)

# This (default) timeout is for each individual test file.
# It is a bit more than the default faulthandler timeout in regrtest.py
# (the latter isn't easily changed under Windows).
TEST_TIMEOUT = 20 * 60  # 20 minutes

# Refleak timeout (-R 3:3) for each individual test file.
REFLEAK_TIMEOUT = 45 * 60  # 45 minutes


def step_timeout(timeout):
    # timeout is the regrtest timeout in seconds. If a test runs longer than
    # the timeout, it should be killed by faulthandler. Give 10 minutes to
    # faulthandler to kill the process. Tests should always be shorter than the
    # buildbot step timeout, unless faulthandler fails to kill the process.
    return timeout + 10 * 60


class BaseBuild(factory.BuildFactory):
    factory_tags = []
    test_timeout = TEST_TIMEOUT

    def __init__(self, source, *, extra_tags=[], **kwargs):
        super().__init__([source])
        self.setup(**kwargs)
        self.tags = self.factory_tags + extra_tags


##############################################################################
###############################  UNIX BUILDS  ################################
##############################################################################


def has_option(option, test_options):
    # return True for option='-j' and test_options=['-uall', '-j2']
    return option in ' '.join(test_options)


class UnixBuild(BaseBuild):
    configureFlags = ["--with-pydebug"]
    compile_environ = {}
    interpreterFlags = ""
    testFlags = ["-j2"]
    makeTarget = "all"
    test_environ = {}
    build_out_of_tree = False

    def setup(self, parallel, branch, test_with_PTY=False, **kwargs):
        out_of_tree_dir = "build_oot"

        # Adjust the timeout for this worker
        self.test_timeout *= kwargs.get("timeout_factor", 1)

        # In 3.9 and 3.10, test_asyncio wasn't split out, and refleaks tests
        # need more time.
        if branch in ("3.9", "3.10") and has_option("-R", self.testFlags):
            self.test_timeout *= 2

        if self.build_out_of_tree:
            self.addStep(
                ShellCommand(
                    name="mkdir out-of-tree directory",
                    description="Create out-of-tree directory",
                    command=["mkdir", "-p", out_of_tree_dir],
                    warnOnFailure=True,
                )
            )

        if self.build_out_of_tree:
            configure_cmd = "../configure"
            oot_kwargs = {'workdir': os.path.join("build", out_of_tree_dir)}
        else:
            configure_cmd = "./configure"
            oot_kwargs = {}
        configure_cmd = [configure_cmd, "--prefix", "$(PWD)/target"]
        configure_cmd += self.configureFlags
        self.addStep(
            Configure(command=configure_cmd, **oot_kwargs)
        )
        compile = ["make", self.makeTarget]
        testopts = list(self.testFlags)
        if not has_option("-R", self.testFlags):
            testopts.extend(("--junit-xml", JUNIT_FILENAME))
        if parallel:
            compile = ["make", parallel, self.makeTarget]
            testopts.append(parallel)
        if not has_option("-j", testopts):
            testopts.append("-j2")
        test = [
            "make",
            "buildbottest",
            "TESTOPTS=" + " ".join(testopts) + " ${BUILDBOT_TESTOPTS}",
            f"TESTPYTHONOPTS={self.interpreterFlags}",
            f"TESTTIMEOUT={self.test_timeout}",
        ]

        self.addStep(Compile(command=compile,
                             env=self.compile_environ,
                             **oot_kwargs))
        self.addStep(
            ShellCommand(
                name="pythoninfo",
                description="pythoninfo",
                command=["make", "pythoninfo"],
                warnOnFailure=True,
                env=self.test_environ,
                **oot_kwargs
            )
        )
        self.addStep(Test(
            command=test,
            timeout=step_timeout(self.test_timeout),
            usePTY=test_with_PTY,
            env=self.test_environ,
            **oot_kwargs
        ))
        if branch not in ("3",) and not has_option("-R", self.testFlags):
            filename = JUNIT_FILENAME
            if self.build_out_of_tree:
                filename = os.path.join(out_of_tree_dir, filename)
            self.addStep(UploadTestResults(branch, filename=filename))
        self.addStep(Clean(**oot_kwargs))


class UnixPerfBuild(UnixBuild):
    buildersuffix = ".perfbuild"
    configureFlags = ["CFLAGS=-fno-omit-frame-pointer -mno-omit-leaf-frame-pointer"]


class UnixTraceRefsBuild(UnixBuild):
    def setup(self, parallel, branch, test_with_PTY=False, **kwargs):
        self.configureFlags = ["--with-pydebug", "--with-trace-refs"]
        return super().setup(parallel, branch, test_with_PTY=test_with_PTY, **kwargs)


class UnixVintageParserBuild(UnixBuild):
    buildersuffix = ".oldparser"  # to get unique directory names on master
    test_environ = {'PYTHONOLDPARSER': 'old'}


class UnixRefleakBuild(UnixBuild):
    buildersuffix = ".refleak"
    testFlags = ["-R", "3:3", "-u-cpu"]
    test_timeout = REFLEAK_TIMEOUT
    factory_tags = ["refleak"]


class UnixNoGilBuild(UnixBuild):
    buildersuffix = ".nogil"
    configureFlags = ["--with-pydebug", "--disable-gil"]
    factory_tags = ["nogil"]
    # 2024-04-11: Free-threading can still be slower than regular build in some
    # code paths, so tolerate longer timeout.
    test_timeout = int(TEST_TIMEOUT * 1.5)


class UnixNoGilRefleakBuild(UnixBuild):
    buildersuffix = ".refleak.nogil"
    configureFlags = ["--with-pydebug", "--disable-gil"]
    testFlags = ["-R", "3:3", "-u-cpu"]
    test_timeout = REFLEAK_TIMEOUT
    factory_tags = ["nogil", "refleak"]


class UnixInstalledBuild(BaseBuild):
    buildersuffix = ".installed"
    configureFlags = []
    interpreterFlags = ["-Wdefault", "-bb", "-E"]
    defaultTestOpts = ["-rwW", "-uall", "-j2"]
    makeTarget = "all"
    installTarget = "install"
    factory_tags = ["installed"]

    def setup(self, parallel, branch, test_with_PTY=False, **kwargs):
        if branch == MAIN_BRANCH_NAME:
            branch = MAIN_BRANCH_VERSION
        elif branch == "custom":
            branch = "3"
        installed_python = f"./target/bin/python{branch}"
        self.addStep(
            Configure(
                command=["./configure", "--prefix", "$(PWD)/target"]
                + self.configureFlags
            )
        )

        compile = ["make", self.makeTarget]
        install = ["make", self.installTarget]
        testopts = list(self.defaultTestOpts)
        testopts.append(f"--timeout={self.test_timeout}")
        if parallel:
            compile = ["make", parallel, self.makeTarget]
            install = ["make", parallel, self.installTarget]
            testopts.append(parallel)

        test = [installed_python,
                *self.interpreterFlags,
                "-m", "test",
                *testopts]

        self.addStep(Compile(command=compile))
        self.addStep(Install(command=install))
        self.addStep(LockInstall())
        self.addStep(
            ShellCommand(
                name="pythoninfo",
                description="pythoninfo",
                command=[installed_python, "-m", "test.pythoninfo"],
                warnOnFailure=True,
            )
        )
        self.addStep(Test(
            command=test,
            timeout=step_timeout(self.test_timeout),
            usePTY=test_with_PTY,
        ))
        self.addStep(Uninstall())
        self.addStep(Clean())


class UnixAsanBuild(UnixBuild):
    buildersuffix = ".asan"
    configureFlags = ["--without-pymalloc", "--with-address-sanitizer"]
    factory_tags = ["asan", "sanitizer"]
    # See https://bugs.python.org/issue42985 for more context on why
    # SIGSEGV is ignored on purpose.
    compile_environ = {'ASAN_OPTIONS': 'detect_leaks=0:allocator_may_return_null=1:handle_segv=0'}
    test_environ = {'ASAN_OPTIONS': 'detect_leaks=0:allocator_may_return_null=1:handle_segv=0'}


class UnixAsanDebugBuild(UnixAsanBuild):
    buildersuffix = ".asan_debug"
    configureFlags = UnixAsanBuild.configureFlags + ["--with-pydebug"]


class UnixAsanNoGilBuild(UnixAsanBuild):
    buildersuffix = ".asan.nogil"
    configureFlags = UnixAsanBuild.configureFlags + ["--disable-gil"]
    factory_tags = UnixAsanBuild.factory_tags + ["nogil"]


class UnixBuildWithoutDocStrings(UnixBuild):
    configureFlags = ["--with-pydebug", "--without-doc-strings"]


class UnixBigmemBuild(UnixBuild):
    buildersuffix = ".bigmem"
    testFlags = ["-M60g", "-j4", "-uall,extralargefile"]
    test_timeout = TEST_TIMEOUT * 4
    factory_tags = ["bigmem"]


class AIXBuild(UnixBuild):
    configureFlags = [
        "--with-pydebug",
        "--with-openssl=/opt/aixtools",
    ]


class AIXBuildWithXLC(UnixBuild):
    buildersuffix = ".xlc"
    configureFlags = [
        "--with-pydebug",
        "--with-openssl=/opt/aixtools",
        "CC=xlc_r",
        "LD=xlc_r",
    ]
    factory_tags = ["xlc"]


class NonDebugUnixBuild(UnixBuild):
    buildersuffix = ".nondebug"
    # Enable assertions regardless. Some children will override this,
    # that is fine.
    configureFlags = ["CFLAGS=-UNDEBUG"]
    factory_tags = ["nondebug"]


class PGOUnixBuild(NonDebugUnixBuild):
    buildersuffix = ".pgo"
    configureFlags = ["--enable-optimizations"]
    factory_tags = ["pgo"]

    def setup(self, parallel, branch, *args, **kwargs):
        # Only Python >3.10 has --with-readline=edit
        if branch != '3.9':
            # Use libedit instead of libreadline on this buildbot for
            # some libedit Linux compilation coverage.
            self.configureFlags = self.configureFlags + ["--with-readline=edit"]
        return super().setup(parallel, branch, *args, **kwargs)


class ClangUnixBuild(UnixBuild):
    buildersuffix = ".clang"
    configureFlags = [
        "CC=clang",
        "LD=clang",
        "--with-pydebug",
    ]
    factory_tags = ["clang"]


class ClangUbsanLinuxBuild(UnixBuild):
    buildersuffix = ".clang-ubsan"
    configureFlags = [
        "CC=clang",
        "LD=clang",
        "CFLAGS=-fno-sanitize-recover",
        "--with-undefined-behavior-sanitizer",
    ]
    factory_tags = ["clang", "ubsan", "sanitizer"]


class ClangUbsanFunctionLinuxBuild(UnixBuild):
    buildersuffix = ".clang-ubsan-function"
    configureFlags = [
        "CC=clang",
        "LD=clang",
        "CFLAGS=-fsanitize=undefined -fno-sanitize=function -fsanitize-recover",
        "--with-undefined-behavior-sanitizer",
    ]
    factory_tags = ["clang", "ubsan", "sanitizer"]


class ClangUnixInstalledBuild(UnixInstalledBuild):
    buildersuffix = ".clang-installed"
    configureFlags = [
        "CC=clang",
        "LD=clang",
    ]
    factory_tags = ["clang", "installed"]


class SharedUnixBuild(UnixBuild):
    configureFlags = ["--with-pydebug", "--enable-shared"]
    factory_tags = ["shared"]


# faulthandler uses a timeout 5 minutes smaller: it should be enough for the
# slowest test.
SLOW_TIMEOUT = 40 * 60


# These use a longer timeout for very slow buildbots.
class SlowNonDebugUnixBuild(NonDebugUnixBuild):
    test_timeout = SLOW_TIMEOUT
    testFlags = [*NonDebugUnixBuild.testFlags, "-u-cpu"]


class SlowUnixInstalledBuild(UnixInstalledBuild):
    test_timeout = SLOW_TIMEOUT


class LTONonDebugUnixBuild(NonDebugUnixBuild):
    buildersuffix = ".lto"
    configureFlags = [
        "--with-lto",
    ]
    factory_tags = ["lto", "nondebug"]


class LTOPGONonDebugBuild(NonDebugUnixBuild):
    buildersuffix = ".lto-pgo"
    configureFlags = [
        "--with-lto",
        "--enable-optimizations",
    ]
    factory_tags = ["lto", "pgo", "nondebug"]


class ClangLTOPGONonDebugBuild(NonDebugUnixBuild):
    buildersuffix = ".clang.lto-pgo"
    configureFlags = [
        "CC=clang",
        "LD=clang",
        "--with-lto",
        "--enable-optimizations",
    ]
    factory_tags = ["lto", "pgo", "nondebug", "clang"]


class RHEL8Build(UnixBuild):
    # Build Python on 64-bit RHEL8.
    configureFlags = [
        "--with-pydebug",
        "--with-platlibdir=lib64",
        "--enable-ipv6",
        "--enable-shared",
        "--with-computed-gotos=yes",
        "--with-dbmliborder=gdbm:ndbm:bdb",
        # FIXME: enable these flags
        # "--with-system-expat",
        # "--with-system-ffi",
        "--enable-loadable-sqlite-extensions",
        "--with-ssl-default-suites=openssl",
        "--without-static-libpython",
        "--with-lto",
        # Not all workers have dtrace installed
        # "--with-dtrace",
        # Not all workers have Valgrind headers installed
        # "--with-valgrind",
    ]

    # Building Python out of tree: similar to what the specfile does, but
    # buildbot uses a single subdirectory, and the specfile uses two
    # sub-directories.
    #
    # On Fedora/RHEL specfile, the following directories are used:
    # /builddir/build/BUILD/Python-3.11: source code
    # /builddir/build/BUILD/Python-3.11/build/optimized: configure, make, tests
    build_out_of_tree = True


class CentOS9Build(RHEL8Build):
    # Build on 64-bit CentOS Stream 9.
    # For now, it's the same as RHEL8, but later it may get different
    # options.
    pass


class FedoraStableBuild(RHEL8Build):
    # Build Python on 64-bit Fedora Stable.
    #
    # Try to be as close as possible to the Fedora specfile used to build
    # the RPM package:
    # https://src.fedoraproject.org/rpms/python3.11/blob/rawhide/f/python3.11.spec
    configureFlags = RHEL8Build.configureFlags + [
        # Options specific to Fedora
        # FIXME: enable this flag
        # "--with-system-libmpdec",
        # Don't make a buildbot fail when pip/setuptools is updated in Python,
        # whereas the buildbot uses older versions.
        # "--with-wheel-pkg-dir=/usr/share/python-wheels/",
    ]


class FedoraRawhideBuild(FedoraStableBuild):
    # Build on 64-bit Fedora Rawhide.
    # For now, it's the same than Fedora Stable, but later it may get different
    # options.
    pass


class FedoraRawhideFreedthreadingBuild(FedoraRawhideBuild):
    # Build on 64-bit Fedora Rawhide.
    buildersuffix = ".nogil"
    configureFlags = FedoraRawhideBuild.configureFlags + [
        "--disable-gil",
    ]
    factory_tags = ["nogil"]


class RHEL8NoBuiltinHashesUnixBuildExceptBlake2(RHEL8Build):
    # Build on 64-bit RHEL8 using: --with-builtin-hashlib-hashes=blake2
    buildersuffix = ".no-builtin-hashes-except-blake2"
    configureFlags = RHEL8Build.configureFlags + [
        "--with-builtin-hashlib-hashes=blake2"
    ]
    factory_tags = ["no-builtin-hashes-except-blake2"]


class RHEL8NoBuiltinHashesUnixBuild(RHEL8Build):
    # Build on 64-bit RHEL8 using: --without-builtin-hashlib-hashes
    buildersuffix = ".no-builtin-hashes"
    configureFlags = RHEL8Build.configureFlags + [
        "--without-builtin-hashlib-hashes"
    ]
    factory_tags = ["no-builtin-hashes"]


class CentOS9NoBuiltinHashesUnixBuildExceptBlake2(CentOS9Build):
    # Build on 64-bit CentOS Stream 9 using: --with-builtin-hashlib-hashes=blake2
    buildersuffix = ".no-builtin-hashes-except-blake2"
    configureFlags = CentOS9Build.configureFlags + [
        "--with-builtin-hashlib-hashes=blake2"
    ]
    factory_tags = ["no-builtin-hashes-except-blake2"]


class CentOS9NoBuiltinHashesUnixBuild(CentOS9Build):
    # Build on 64-bit CentOS Stream 9 using: --without-builtin-hashlib-hashes
    buildersuffix = ".no-builtin-hashes"
    configureFlags = CentOS9Build.configureFlags + [
        "--without-builtin-hashlib-hashes"
    ]
    factory_tags = ["no-builtin-hashes"]


##############################################################################
############################  MACOS BUILDS  ##################################
##############################################################################

class MacOSArmWithBrewBuild(UnixBuild):
    buildersuffix = ".macos-with-brew"
    configureFlags = UnixBuild.configureFlags + [
        "--with-openssl=/opt/homebrew/opt/openssl@3",
        "CPPFLAGS=-I/opt/homebrew/include",
        "LDFLAGS=-L/opt/homebrew/lib",
    ]
    # These tests are known to crash on M1 macs (see bpo-45289).
    testFlags = [*UnixBuild.testFlags,
                 "-x", "test_dbm", "test_dbm_ndbm", "test_shelve"]


class MacOSArmWithBrewNoGilBuild(UnixNoGilBuild):
    buildersuffix = ".macos-with-brew.nogil"
    configureFlags = [
        *UnixNoGilBuild.configureFlags,
        "--with-openssl=/opt/homebrew/opt/openssl@3",
        "CPPFLAGS=-I/opt/homebrew/include",
        "LDFLAGS=-L/opt/homebrew/lib",
    ]


class MacOSArmWithBrewRefleakBuild(UnixRefleakBuild):
    buildersuffix = ".macos-with-brew.refleak"
    configureFlags = [
        *UnixRefleakBuild.configureFlags,
        "--with-openssl=/opt/homebrew/opt/openssl@3",
        "CPPFLAGS=-I/opt/homebrew/include",
        "LDFLAGS=-L/opt/homebrew/lib",
    ]


class MacOSArmWithBrewNoGilRefleakBuild(UnixNoGilRefleakBuild):
    buildersuffix = ".macos-with-brew.refleak.nogil"
    configureFlags = [
        *UnixNoGilRefleakBuild.configureFlags,
        "--with-openssl=/opt/homebrew/opt/openssl@3",
        "CPPFLAGS=-I/opt/homebrew/include",
        "LDFLAGS=-L/opt/homebrew/lib",
    ]


class MacOSAsanNoGilBuild(UnixAsanNoGilBuild):
    buildersuffix = ".macos-with-brew.asan.nogil"
    configureFlags = UnixAsanNoGilBuild.configureFlags + [
        "--with-openssl=/opt/homebrew/opt/openssl@3",
        "CPPFLAGS=-I/opt/homebrew/include",
        "LDFLAGS=-L/opt/homebrew/lib",
    ]
    asan_options = 'detect_leaks=0:allocator_may_return_null=1:handle_segv=0'
    compile_environ = {'ASAN_OPTIONS': asan_options}
    test_environ = {
        'ASAN_OPTIONS': asan_options,
        # Note: Need to set `MallocNanoZone=0` environment variable to workaround a macOS issue.
        # This was needed to workaround an issue with this builder that manifested as failures in 3 tests:
        # test_cmd_line, test_posix, test_subprocess
        # These failures seem to be related to the occurrence of this warning:
        # python.exe(74602,0x7ff84626a700) malloc: nano zone abandoned due to inability to reserve vm space.
        # It is unclear why (or if) it's *directly* causing the test failures, but setting `MallocNanoZone=0`
        # disables this optimization (and fixes the tests), which appears to be interfering with ASAN. See also:
        # https://stackoverflow.com/questions/64126942/malloc-nano-zone-abandoned-due-to-inability-to-preallocate-reserved-vm-space
        # https://github.com/python/buildmaster-config/issues/450 (and attached PR)
        'MallocNanoZone': '0',
    }


##############################################################################
############################  WINDOWS BUILDS  ################################
##############################################################################


class BaseWindowsBuild(BaseBuild):
    build_command = [r"Tools\buildbot\build.bat"]
    test_command = [r"Tools\buildbot\test.bat"]
    clean_command = [r"Tools\buildbot\clean.bat"]
    python_command = [r"python.bat"]
    buildFlags = ["-p", "Win32"]
    testFlags = ["-p", "Win32", "-j2"]
    cleanFlags = []
    factory_tags = ["win32"]

    def setup(self, parallel, branch, **kwargs):
        build_command = self.build_command + self.buildFlags
        test_command = [*self.test_command, *self.testFlags]
        if not has_option("-R", self.testFlags):
            test_command.extend((r"--junit-xml", JUNIT_FILENAME))
        clean_command = self.clean_command + self.cleanFlags
        if parallel:
            test_command.append(parallel)
        self.addStep(Compile(command=build_command))
        self.addStep(
            ShellCommand(
                name="pythoninfo",
                description="pythoninfo",
                command=self.python_command + ["-m", "test.pythoninfo"],
                warnOnFailure=True,
            )
        )
        test_command.extend(("--timeout", str(self.test_timeout)))
        self.addStep(Test(
            command=test_command,
            timeout=step_timeout(self.test_timeout),
        ))
        if branch not in ("3",) and not has_option("-R", self.testFlags):
            self.addStep(UploadTestResults(branch))
        self.addStep(Clean(command=clean_command))


class WindowsBuild(BaseWindowsBuild):
    buildersuffix = '.x32'


class WindowsRefleakBuild(BaseWindowsBuild):
    buildersuffix = ".x32.refleak"
    testFlags = ["-j2", "-R", "3:3", "-u-cpu"]
    test_timeout = REFLEAK_TIMEOUT
    factory_tags = ["win32", "refleak"]


class SlowWindowsBuild(WindowsBuild):
    test_timeout = TEST_TIMEOUT * 2
    testFlags = ["-j2", "-u-cpu", "-u-largefile"]


class Windows64Build(BaseWindowsBuild):
    buildFlags = ["-p", "x64"]
    testFlags = ["-p", "x64", "-j2"]
    cleanFlags = ["-p", "x64"]
    factory_tags = ["win64"]


class Windows64BigmemBuild(BaseWindowsBuild):
    buildersuffix = ".bigmem"
    buildFlags = ["-p", "x64"]
    testFlags = ["-p", "x64", "-M33g", "-uall,extralargefile"]
    test_timeout = TEST_TIMEOUT * 4
    cleanFlags = ["-p", "x64"]
    factory_tags = ["win64", "bigmem"]


class Windows64RefleakBuild(Windows64Build):
    buildersuffix = ".refleak"
    testFlags = ["-p", "x64", *WindowsRefleakBuild.testFlags]
    test_timeout = REFLEAK_TIMEOUT
    factory_tags = ["win64", "refleak"]


class Windows64ReleaseBuild(Windows64Build):
    buildersuffix = ".nondebug"
    buildFlags = Windows64Build.buildFlags + ["-c", "Release"]
    testFlags = [*Windows64Build.testFlags, "+d"]
    # keep default cleanFlags, both configurations get cleaned
    factory_tags = ["win64", "nondebug"]


class Windows64NoGilBuild(Windows64Build):
    buildersuffix = '.x64.nogil'
    buildFlags = Windows64Build.buildFlags + ["--disable-gil"]
    testFlags = Windows64Build.testFlags + ["--disable-gil"]
    factory_tags = ["win64", "nogil"]


class WindowsARM64Build(BaseWindowsBuild):
    buildFlags = ["-p", "ARM64"]
    testFlags = ["-p", "ARM64", "-j2"]
    cleanFlags = ["-p", "ARM64"]
    factory_tags = ["win-arm64"]


class WindowsARM64ReleaseBuild(WindowsARM64Build):
    buildersuffix = ".nondebug"
    buildFlags = WindowsARM64Build.buildFlags + ["-c", "Release"]
    testFlags = [*WindowsARM64Build.testFlags, "+d"]
    # keep default cleanFlags, both configurations get cleaned
    factory_tags = ["win-arm64", "nondebug"]

##############################################################################
##############################  WASI BUILDS  #################################
##############################################################################


class UnixCrossBuild(UnixBuild):
    extra_configure_flags = []
    host_configure_cmd = ["../../configure"]
    host = None
    host_make_cmd = ["make"]
    can_execute_python = True

    def setup(self, parallel, branch, test_with_PTY=False, **kwargs):
        assert self.host is not None, "Must set self.host on cross builds"

        out_of_tree_dir = "build_oot"
        oot_dir_path = os.path.join("build", out_of_tree_dir)
        oot_build_path = os.path.join(oot_dir_path, "build")
        oot_host_path = os.path.join(oot_dir_path, "host")

        self.addStep(
            SetPropertyFromCommand(
                name="Gather build triple from worker",
                description="Get the build triple config.guess",
                command="./config.guess",
                property="build_triple",
                warnOnFailure=True,
            )
        )

        # Create out of tree directory for "build", the platform we are
        # currently running on
        self.addStep(
            ShellCommand(
                name="mkdir build out-of-tree directory",
                description="Create build out-of-tree directory",
                command=["mkdir", "-p", oot_build_path],
                warnOnFailure=True,
            )
        )
        # Create directory for "host", the platform we want to compile *for*
        self.addStep(
            ShellCommand(
                name="mkdir host out-of-tree directory",
                description="Create host out-of-tree directory",
                command=["mkdir", "-p", oot_host_path],
                warnOnFailure=True,
            )
        )

        # First, we build the "build" Python, which we need to cross compile
        # the "host" Python
        self.addStep(
            Configure(
                name="Configure build Python",
                command=["../../configure"],
                workdir=oot_build_path
            )
        )
        if parallel:
            compile = ["make", parallel]
        else:
            compile = ["make"]

        self.addStep(
            Compile(
                name="Compile build Python",
                command=compile,
                workdir=oot_build_path
            )
        )

        # Now that we have a "build" architecture Python, we can use that
        # to build a "host" (also known as the target we are cross compiling)
        # Take a copy so that the class-level definition isn't tainted
        configure_cmd = list(self.host_configure_cmd)
        configure_cmd += ["--prefix", "$(PWD)/target/host"]
        configure_cmd += self.configureFlags + self.extra_configure_flags
        configure_cmd += [util.Interpolate("--build=%(prop:build_triple)s")]
        configure_cmd += [f"--host={self.host}"]
        configure_cmd += ["--with-build-python=../build/python"]
        self.addStep(
            Configure(
                name="Configure host Python",
                command=configure_cmd,
                env=self.compile_environ,
                workdir=oot_host_path
            )
        )

        testopts = list(self.testFlags)
        if not has_option("-R", self.testFlags):
            testopts.extend((" --junit-xml", JUNIT_FILENAME))
        if parallel:
            testopts.append(parallel)
        if not has_option("-j", self.testFlags):
            testopts.append("-j2")

        test = [
            "make",
            "buildbottest",
            "TESTOPTS=" + " ".join(testopts) + " ${BUILDBOT_TESTOPTS}",
            f"TESTPYTHONOPTS={self.interpreterFlags}",
            f"TESTTIMEOUT={self.test_timeout}",
        ]

        if parallel:
            compile = self.host_make_cmd + [parallel, self.makeTarget]
        else:
            compile = self.host_make_cmd + [self.makeTarget]
        self.addStep(
            Compile(
                name="Compile host Python",
                command=compile,
                env=self.compile_environ,
                workdir=oot_host_path,
            )
        )
        if self.can_execute_python:
            self.addStep(
                ShellCommand(
                    name="pythoninfo",
                    description="pythoninfo",
                    command=["make", "pythoninfo"],
                    warnOnFailure=True,
                    env=self.test_environ,
                    workdir=oot_host_path,
                )
            )
            self.addStep(Test(
                command=test,
                timeout=step_timeout(self.test_timeout),
                usePTY=test_with_PTY,
                env=self.test_environ,
                workdir=oot_host_path,
            ))
            if branch not in ("3",) and not has_option("-R", self.testFlags):
                filename = os.path.join(oot_host_path, JUNIT_FILENAME)
                self.addStep(UploadTestResults(branch, filename=filename))
        self.addStep(
            Clean(
                name="Clean build Python",
                workdir=oot_build_path,
            )
        )
        self.addStep(
            Clean(
                name="Clean host Python",
                workdir=oot_host_path,
            )
        )


# Deprecated since Python 3.13; can be dropped once `wasi.py` is in all versions.
class Wasm32WasiCrossBuild(UnixCrossBuild):
    """wasm32-wasi builder

    * WASI SDK >= 16 must be installed to default path /opt/wasi-sdk
    * wasmtime must be installed and on PATH
    """

    buildersuffix = ".wasi.nondebug"
    factory_tags = ["wasm", "wasi", "nondebug"]
    extra_configure_flags = [
        # debug builds exhaust the limited call stack on WASI
        "--without-pydebug",
    ]
    compile_environ = {
        "CONFIG_SITE": "../../Tools/wasm/config.site-wasm32-wasi",
    }
    host = "wasm32-unknown-wasi"
    host_configure_cmd = ["../../Tools/wasm/wasi-env", "../../configure"]

    def setup(self, parallel, branch, test_with_PTY=False, **kwargs):
        self.addStep(
            ShellCommand(
                name="Touch srcdir Modules/Setup.local",
                description="Hack to work around wasmtime mapdir issue",
                command=["touch", "Modules/Setup.local"],
                haltOnFailure=True,
            )
        )
        super().setup(parallel, branch, test_with_PTY=test_with_PTY, **kwargs)


class _Wasm32WasiBuild(UnixBuild):
    """Build Python for wasm32-wasi using Tools/wasm/wasi.py."""
    buildersuffix = ".wasi"
    factory_tags = ["wasm", "wasi"]
    # pydebug and append_suffix defined in subclasses.

    def __init__(self, source, *, extra_tags=[], **kwargs):
        if not self.pydebug:
            extra_tags.append("nondebug")
        self.buildersuffix += self.append_suffix
        super().__init__(source, extra_tags=extra_tags, **kwargs)

    def setup(self, parallel, branch, test_with_PTY=False, **kwargs):
        wasi_py = "Tools/wasm/wasi.py"
        host_path = "build/cross-build/wasm32-wasi"

        # Build Python
        build_configure = ["python3", wasi_py, "configure-build-python"]
        if self.pydebug:
            build_configure.extend(["--", "--with-pydebug"])
        self.addStep(
            Configure(
                name="Configure build Python",
                command=build_configure,
            )
        )
        self.addStep(
            Compile(
                name="Compile build Python",
                command=["python3", wasi_py, "make-build-python"],
            )
        )

        # Host/WASI Python
        self.addStep(
            # Pydebug build automatically inferred from build Python.
            Configure(
                name="Configure host Python",
                command=["python3", wasi_py, "configure-host"],
            )
        )
        self.addStep(
            Compile(
                name="Compile host Python",
                command=["python3", wasi_py, "make-host"],
            )
        )

        self.addStep(
            ShellCommand(
                name="pythoninfo",
                description="pythoninfo",
                command=["make", "pythoninfo"],
                warnOnFailure=True,
                workdir=host_path,
            )
        )

        # Copied from UnixBuild.
        testopts = list(self.testFlags)
        if not has_option("-R", self.testFlags):
            testopts.extend(("--junit-xml", JUNIT_FILENAME))
        if parallel:
            testopts.append(parallel)
        if not has_option("-j", testopts):
            testopts.append("-j2")
        test = [
            "make",
            "buildbottest",
            "TESTOPTS=" + " ".join(testopts) + " ${BUILDBOT_TESTOPTS}",
            f"TESTPYTHONOPTS={self.interpreterFlags}",
            f"TESTTIMEOUT={self.test_timeout}",
        ]
        self.addStep(
            Test(
                command=test,
                timeout=step_timeout(self.test_timeout),
                usePTY=test_with_PTY,
                env=self.test_environ,
                workdir=host_path,
            )
        )
        if branch not in ("3",) and not has_option("-R", self.testFlags):
            filename = os.path.join(host_path, JUNIT_FILENAME)
            self.addStep(UploadTestResults(branch, filename=filename))

        self.addStep(
            Clean(
                name="Clean the builds",
                command=["python3", wasi_py, "clean"],
            )
        )


# Preventing this from running on versions older than 3.13 is managed in
# master.cfg.
class Wasm32WasiDebugBuild(_Wasm32WasiBuild):
    append_suffix = ".debug"
    pydebug = True
    testFlags = ["-u-cpu"]


##############################################################################
################################  IOS BUILDS  ################################
##############################################################################

class _IOSSimulatorBuild(UnixBuild):
    """iOS Simulator build.

    * Xcode must be installed, with all licenses accepted
    * The iOS Simulator must be installed
    * The ~buildbot/support/iphonesimulator.{arch} folder must be populated
      with pre-compiled builds of libFFI, XZ, Bzip2 and OpenSSL.

    Subclasses should define `arch`.

    This workflow is largely the same as the UnixCrossBuild, except that:
     * It has the required iOS configure options baked in
     * It isolates the build path so that Homebrew and other macOS libraries
       can't leak into the build
     * It adds the environment flags and configuration paths for the binary
       dependencies.
     * It installs the host python after build (which finalizes the Framework
       build)
     * It invokes `make testios` as a test target
    """
    buildersuffix = ".iOS-simulator"
    ios_min_version = ""  # use the default from the configure file
    factory_tags = ["iOS"]
    extra_configure_flags = []
    host_configure_cmd = ["../../configure"]

    def __init__(self, source, **kwargs):
        self.buildersuffix += f".{self.arch}"
        self.host = f"{self.arch}-apple-ios{self.ios_min_version}-simulator"

        super().__init__(source, **kwargs)

    def setup(self, parallel, branch, test_with_PTY=False, **kwargs):
        out_of_tree_dir = "build_oot"
        oot_dir_path = os.path.join("build", out_of_tree_dir)
        oot_build_path = os.path.join(oot_dir_path, "build")
        oot_host_path = os.path.join(oot_dir_path, "host")

        # Create out of tree directory for "build", the platform we are
        # currently running on
        self.addStep(
            ShellCommand(
                name="mkdir build out-of-tree directory",
                description="Create build out-of-tree directory",
                command=["mkdir", "-p", oot_build_path],
                warnOnFailure=True,
            )
        )
        # Create directory for "host", the platform we want to compile *for*
        self.addStep(
            ShellCommand(
                name="mkdir host out-of-tree directory",
                description="Create host out-of-tree directory",
                command=["mkdir", "-p", oot_host_path],
                warnOnFailure=True,
            )
        )

        # First, we build the "build" Python, which we need to cross compile
        # the "host" Python
        self.addStep(
            Configure(
                name="Configure build Python",
                command=["../../configure"],
                workdir=oot_build_path
            )
        )
        if parallel:
            compile = ["make", parallel]
        else:
            compile = ["make"]

        self.addStep(
            Compile(
                name="Compile build Python",
                command=compile,
                workdir=oot_build_path
            )
        )

        # Ensure the host path is isolated from Homebrew et al, but includes
        # the host helper binaries. Also add the configuration paths for
        # library dependencies.
        support_path = f"/Users/buildbot/support/iphonesimulator.{self.arch}"
        compile_environ = dict(self.compile_environ)
        compile_environ.update({
            "PATH": os.pathsep.join([
                # This is intentionally a relative path. Buildbot doesn't expose
                # the absolute working directory where the build is running as
                # something that can be expanded into an environment variable.
                "../../iOS/Resources/bin",
                "/usr/bin",
                "/bin",
                "/usr/sbin",
                "/sbin",
                "/Library/Apple/usr/bin",
            ]),
            "LIBLZMA_CFLAGS": f"-I{support_path}/xz/include",
            "LIBLZMA_LIBS": f"-L{support_path}/xz/lib -llzma",
            "BZIP2_CFLAGS": f"-I{support_path}/bzip2/include",
            "BZIP2_LIBS": f"-L{support_path}/bzip2/lib -lbz2",
            "LIBFFI_CFLAGS": f"-I{support_path}/libffi/include",
            "LIBFFI_LIBS": f"-L{support_path}/libffi/lib -lffi",
        })

        # Now that we have a "build" architecture Python, we can use that
        # to build a "host" (also known as the target we are cross compiling)
        # Take a copy so that the class-level definition isn't tainted
        configure_cmd = list(self.host_configure_cmd)
        configure_cmd += self.configureFlags
        configure_cmd += self.extra_configure_flags
        configure_cmd += [
            f"--with-openssl={support_path}/openssl",
            f"--build={self.arch}-apple-darwin",
            f"--host={self.host}",
            "--with-build-python=../build/python.exe",
            "--enable-framework"
        ]

        self.addStep(
            Configure(
                name="Configure host Python",
                command=configure_cmd,
                env=compile_environ,
                workdir=oot_host_path
            )
        )

        if parallel:
            compile = ["make", parallel, self.makeTarget]
            install = ["make", parallel, "install"]
        else:
            compile = ["make", self.makeTarget]
            install = ["make", "install"]

        self.addStep(
            Compile(
                name="Compile host Python",
                command=compile,
                env=compile_environ,
                workdir=oot_host_path,
            )
        )
        self.addStep(
            Compile(
                name="Install host Python",
                command=install,
                env=compile_environ,
                workdir=oot_host_path,
            )
        )
        self.addStep(
            Test(
                command=["make", "testios"],
                timeout=step_timeout(self.test_timeout),
                usePTY=test_with_PTY,
                env=self.test_environ,
                workdir=oot_host_path,
            )
        )

        self.addStep(
            Clean(
                name="Clean build Python",
                workdir=oot_build_path,
            )
        )
        self.addStep(
            Clean(
                name="Clean host Python",
                workdir=oot_host_path,
            )
        )


class IOSARM64SimulatorBuild(_IOSSimulatorBuild):
    """An ARM64 iOS simulator build."""
    arch = "arm64"


##############################################################################
##############################  ANDROID BUILDS  ##############################
##############################################################################

class AndroidBuild(BaseBuild):
    """Build Python for Android on a Linux or Mac machine, and test it using a
    Gradle-managed emulator.

    To set up a worker, see cpython/Android/README.md, especially the following
    sections:

    * Install everything listed under "Prerequisites".
    * Do any OS-specific setup mentioned under "Testing".
    * If the managed emulator appears to be running out of memory, increase
      its RAM size as described under "Testing".
    """

    def setup(self, **kwargs):
        android_py = "Android/android.py"
        self.addSteps([
            SetPropertyFromCommand(
                name="Get build triple",
                command=["./config.guess"],
                property="build_triple",
                haltOnFailure=True,
            ),
            Configure(
                name="Configure build Python",
                command=[android_py, "configure-build"],
            ),
            Compile(
                name="Compile build Python",
                command=[android_py, "make-build"],
            ),
            Configure(
                name="Configure host Python",
                command=[android_py, "configure-host", self.host_triple],
            ),
            Compile(
                name="Compile host Python",
                command=[android_py, "make-host", self.host_triple],
            ),
            Test(
                command=[
                    android_py, "test", "--managed", "maxVersion", "-v", "--",
                    "-uall", "--single-process", "--rerun", "-W",
                ],
                timeout=step_timeout(self.test_timeout),
            ),
            ShellCommand(
                name="Clean",
                command=[android_py, "clean"],
            ),
        ])

    @util.renderer
    def host_triple(props):
        build_triple = props.getProperty("build_triple")
        return build_triple.split("-")[0] + "-linux-android"


class ValgrindBuild(UnixBuild):
    buildersuffix = ".valgrind"
    configureFlags = [
        "--with-pydebug",
        "--with-valgrind",
        "--without-pymalloc",
    ]
    testFlags = [
        "test_grammar",
        "test_syntax",
        "test_tokenize",
        "test_fstring",
        "test_ast",
        "test_exceptions",
    ]
    factory_tags = ["valgrind"]
    test_timeout = TEST_TIMEOUT * 5

    def setup(self, parallel, branch, **kwargs):
        self.addStep(
            Configure(
                command=["./configure", "--prefix", "$(PWD)/target"] + self.configureFlags
            )
        )

        compile = ["make", self.makeTarget]
        if parallel:
            compile = ["make", parallel, self.makeTarget]

        self.addStep(Compile(command=compile, env=self.compile_environ))

        self.addStep(
            ShellCommand(
                name="pythoninfo",
                description="pythoninfo",
                command=["make", "pythoninfo"],
                warnOnFailure=True,
                env=self.test_environ,
            )
        )

        test = [
            "valgrind",
            "--leak-check=full",
            "--show-leak-kinds=definite",
            "--error-exitcode=10",
            "--gen-suppressions=all",
            "--track-origins=yes",
            "--trace-children=yes",
            "--suppressions=$(PWD)/Misc/valgrind-python.supp",
            "./python",
            "-m", "test",
            *self.testFlags,
            f"--timeout={self.test_timeout}",
        ]

        self.addStep(Test(
            command=test,
            timeout=step_timeout(self.test_timeout),
            env=self.test_environ,
        ))

        self.addStep(Clean())
