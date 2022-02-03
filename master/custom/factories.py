import os.path
from buildbot.process import factory
from buildbot.steps.shell import Configure, Compile, ShellCommand

from .steps import (
    Test,
    Clean,
    Install,
    LockInstall,
    Uninstall,
    UploadTestResults,
)

main_branch_version = "3.11"
CUSTOM_BRANCH_NAME = "custom"

# This (default) timeout is for each individual test file.
# It is a bit more than the default faulthandler timeout in regrtest.py
# (the latter isn't easily changed under Windows).
TEST_TIMEOUT = 20 * 60


def regrtest_has_cleanup(branch):
    return branch not in {CUSTOM_BRANCH_NAME}


class TaggedBuildFactory(factory.BuildFactory):
    factory_tags = []

    def __init__(self, source, *, extra_tags=[], **kwargs):
        super().__init__([source])
        self.setup(**kwargs)
        self.tags = self.factory_tags + extra_tags


class FreezeBuild(TaggedBuildFactory):
    buildersuffix = ".freeze"  # to get unique directory names on master
    test_timeout = None
    factory_tags = ["freeze"]

    def setup(self, **kwargs):
        self.addStep(Configure(command=["./configure", "--prefix", "$(PWD)/target"]))
        self.addStep(Compile(command=["make"]))
        self.addStep(
            ShellCommand(
                name="install", description="installing", command=["make", "install"]
            )
        )
        self.addStep(
            Test(
                command=[
                    "make",
                    "-C",
                    "Tools/freeze/test",
                    "PYTHON=../../../target/bin/python3",
                    "OUTDIR=../../../target/freezetest",
                ]
            )
        )


##############################################################################
###############################  UNIX BUILDS  ################################
##############################################################################


class UnixBuild(TaggedBuildFactory):
    configureFlags = ["--with-pydebug"]
    compile_environ = {}
    interpreterFlags = ""
    testFlags = "-j2"
    makeTarget = "all"
    test_timeout = None
    test_environ = {}
    build_out_of_tree = False

    def setup(self, parallel, branch, test_with_PTY=False, **kwargs):
        out_of_tree_dir = "build_oot"

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
        testopts = self.testFlags
        if "-R" not in self.testFlags:
            testopts += " --junit-xml test-results.xml"
        # Timeout for the buildworker process
        self.test_timeout = self.test_timeout or TEST_TIMEOUT
        # Timeout for faulthandler
        faulthandler_timeout = self.test_timeout - 5 * 60
        if parallel:
            compile = ["make", parallel, self.makeTarget]
            testopts = testopts + " " + parallel
        if "-j" not in testopts:
            testopts = "-j2 " + testopts
        test = [
            "make",
            "buildbottest",
            "TESTOPTS=" + testopts + " ${BUILDBOT_TESTOPTS}",
            "TESTPYTHONOPTS=" + self.interpreterFlags,
            "TESTTIMEOUT=" + str(faulthandler_timeout),
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
        self.addStep(
            Test(
                command=test,
                timeout=self.test_timeout,
                usePTY=test_with_PTY,
                env=self.test_environ,
                **oot_kwargs
            )
        )
        if branch not in ("3",) and "-R" not in self.testFlags:
            filename = "test-results.xml"
            if self.build_out_of_tree:
                filename = os.path.join(out_of_tree_dir, filename)
            self.addStep(UploadTestResults(branch, filename=filename))
        self.addStep(Clean(**oot_kwargs))


class UnixTraceRefsBuild(UnixBuild):
    def setup(self, parallel, branch, test_with_PTY=False, **kwargs):
        # Only Python >3.8 has --with-trace-refs
        self.configureFlags = ["--with-pydebug", "--with-trace-refs"]
        return super().setup(parallel, branch, test_with_PTY=test_with_PTY, **kwargs)


class UnixVintageParserBuild(UnixBuild):
    buildersuffix = ".oldparser"  # to get unique directory names on master
    test_environ = {'PYTHONOLDPARSER': 'old'}


class UnixRefleakBuild(UnixBuild):
    buildersuffix = ".refleak"
    testFlags = "-R 3:3 -u-cpu"
    # -R 3:3 is supposed to only require timeout x 6, but in practice,
    # it's much more slower. Use timeout x 10 to prevent timeout
    # caused by --huntrleaks.
    test_timeout = TEST_TIMEOUT * 10
    factory_tags = ["refleak"]


class UnixInstalledBuild(TaggedBuildFactory):
    buildersuffix = ".installed"
    configureFlags = []
    interpreterFlags = ["-Wdefault", "-bb", "-E"]
    defaultTestOpts = ["-rwW", "-uall", "-j2"]
    makeTarget = "all"
    installTarget = "install"
    test_timeout = None
    factory_tags = ["installed"]

    def setup(self, parallel, branch, test_with_PTY=False, **kwargs):
        if branch == "3.x":
            branch = main_branch_version
        elif branch == "custom":
            branch = "3"
        installed_python = "./target/bin/python%s" % branch
        self.addStep(
            Configure(
                command=["./configure", "--prefix", "$(PWD)/target"]
                + self.configureFlags
            )
        )

        compile = ["make", self.makeTarget]
        install = ["make", self.installTarget]
        testopts = self.defaultTestOpts[:]
        # Timeout for the buildworker process
        self.test_timeout = self.test_timeout or TEST_TIMEOUT
        # Timeout for faulthandler
        faulthandler_timeout = self.test_timeout - 5 * 60
        testopts += [f"--timeout={faulthandler_timeout}"]
        if parallel:
            compile = ["make", parallel, self.makeTarget]
            install = ["make", parallel, self.installTarget]
            testopts = testopts + [parallel]

        test = [installed_python] + self.interpreterFlags
        test += ["-m", "test.regrtest"] + testopts

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
        self.addStep(
            Test(command=test, timeout=self.test_timeout, usePTY=test_with_PTY)
        )
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
    # These tests are currently raising false positives or are interfering with the ASAN mechanism,
    # so we need to skip them unfortunately.
    testFlags = ("-j1 -x test_ctypes test_capi test_crypt test_decimal test_faulthandler test_interpreters")
    # Sometimes test_multiprocessing_fork times out after 15 minutes
    test_timeout = TEST_TIMEOUT * 2


class UnixAsanDebugBuild(UnixAsanBuild):
    buildersuffix = ".asan_debug"
    configureFlags = UnixAsanBuild.configureFlags + ["--with-pydebug"]


class UnixBuildWithoutDocStrings(UnixBuild):
    configureFlags = ["--with-pydebug", "--without-doc-strings"]


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
        if branch not in {'3.8', '3.9'}:
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

    # These tests are currently raising false positives or are interfering with the USAN mechanism,
    # so we need to skip them unfortunately.
    testFlags = "-j1 -x test_faulthandler test_hashlib test_concurrent_futures test_ctypes"


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


class SlowSharedUnixBuild(SharedUnixBuild):
    test_timeout = SLOW_TIMEOUT


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


class RHEL7Build(UnixBuild):
    # Build Python on 64-bit RHEL7.
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
        # Not all workers have dtrace installed
        # "--with-dtrace",
        # Not all workers have Valgrind headers installed
        # "--with-valgrind",
    ]
    # Don't use --with-lto: building Python with LTO doesn't work
    # with RHEL7 GCC.

    # Building Python out of tree: similar to what the specfile does, but
    # buildbot uses a single subdirectory, and the specfile uses two
    # sub-directories.
    #
    # On Fedora/RHEL specfile, the following directories are used:
    # /builddir/build/BUILD/Python-3.10: source code
    # /builddir/build/BUILD/Python-3.10/build/optimized: configure, make, tests
    build_out_of_tree = True


class RHEL8Build(RHEL7Build):
    # Build Python on 64-bit RHEL8.
    configureFlags = RHEL7Build.configureFlags + [
        "--with-lto",
    ]

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
    # https://src.fedoraproject.org/rpms/python3.10/blob/rawhide/f/python3.10.spec
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
    testFlags = UnixBuild.testFlags + " -x test_dbm test_dbm_ndbm test_shelve"

##############################################################################
############################  WINDOWS BUILDS  ################################
##############################################################################


class WindowsBuild(TaggedBuildFactory):
    build_command = [r"Tools\buildbot\build.bat"]
    remote_deploy_command = [r"Tools\buildbot\remoteDeploy.bat"]
    remote_pythonInfo_command = [r"Tools\buildbot\remotePythoninfo.bat"]
    test_command = [r"Tools\buildbot\test.bat"]
    clean_command = [r"Tools\buildbot\clean.bat"]
    python_command = [r"python.bat"]
    buildFlags = ["-p", "Win32"]
    remoteDeployFlags = []
    remotePythonInfoFlags = []
    testFlags = ["-p", "Win32", "-j2"]
    cleanFlags = []
    test_timeout = None
    factory_tags = ["win32"]
    remoteTest = False

    def setup(self, parallel, branch, **kwargs):
        build_command = self.build_command + self.buildFlags
        test_command = self.test_command + self.testFlags
        if "-R" not in self.testFlags:
            test_command += [r"--junit-xml", r"test-results.xml"]
        clean_command = self.clean_command + self.cleanFlags
        if parallel:
            test_command.append(parallel)
        self.addStep(Compile(command=build_command))
        if self.remoteTest:
            # deploy
            self.addStep(
                ShellCommand(
                    name="remotedeploy",
                    description="remotedeploy",
                    command=self.remote_deploy_command + self.remoteDeployFlags,
                    warnOnFailure=True,
                )
            )
            # pythonInfo
            self.addStep(
                ShellCommand(
                    name="remotepythoninfo",
                    description="remotepythoninfo",
                    command=self.remote_pythonInfo_command + self.remotePythonInfoFlags,
                    warnOnFailure=True,
                )
            )
        else:
            self.addStep(
                ShellCommand(
                    name="pythoninfo",
                    description="pythoninfo",
                    command=self.python_command + ["-m", "test.pythoninfo"],
                    warnOnFailure=True,
                )
            )
        timeout = self.test_timeout if self.test_timeout else TEST_TIMEOUT
        test_command += ["--timeout", timeout - (5 * 60)]
        self.addStep(Test(command=test_command, timeout=timeout))
        if branch not in ("3",) and "-R" not in self.testFlags:
            self.addStep(UploadTestResults(branch))
        self.addStep(Clean(command=clean_command))


class WindowsRefleakBuild(WindowsBuild):
    buildersuffix = ".refleak"
    testFlags = ["-j2", "-R", "3:3", "-u-cpu"]
    # -R 3:3 is supposed to only require timeout x 6, but in practice,
    # it's much more slower. Use timeout x 10 to prevent timeout
    # caused by --huntrleaks.
    test_timeout = TEST_TIMEOUT * 10
    factory_tags = ["win32", "refleak"]


class SlowWindowsBuild(WindowsBuild):
    test_timeout = TEST_TIMEOUT * 2
    testFlags = ["-j2", "-u-cpu", "-u-largefile"]


class Windows64Build(WindowsBuild):
    buildFlags = ["-p", "x64"]
    testFlags = ["-p", "x64", "-j2"]
    cleanFlags = ["-p", "x64"]
    factory_tags = ["win64"]


class Windows64RefleakBuild(Windows64Build):
    buildersuffix = ".refleak"
    testFlags = ["-p", "x64"] + WindowsRefleakBuild.testFlags
    # -R 3:3 is supposed to only require timeout x 6, but in practice,
    # it's much more slower. Use timeout x 10 to prevent timeout
    # caused by --huntrleaks.
    test_timeout = TEST_TIMEOUT * 10
    factory_tags = ["win64", "refleak"]


class Windows64ReleaseBuild(Windows64Build):
    buildersuffix = ".nondebug"
    buildFlags = Windows64Build.buildFlags + ["-c", "Release"]
    testFlags = Windows64Build.testFlags + ["+d"]
    # keep default cleanFlags, both configurations get cleaned
    factory_tags = ["win64", "nondebug"]


class WindowsARM64Build(WindowsBuild):
    buildFlags = ["-p", "ARM64"]
    testFlags = ["-p", "ARM64", "-j2"]
    cleanFlags = ["-p", "ARM64"]
    factory_tags = ["win-arm64"]

class WindowsARM64ReleaseBuild(WindowsARM64Build):
    buildersuffix = ".nondebug"
    buildFlags = WindowsARM64Build.buildFlags + ["-c", "Release"]
    testFlags = WindowsARM64Build.testFlags + ["+d"]
    # keep default cleanFlags, both configurations get cleaned
    factory_tags = ["win-arm64", "nondebug"]
