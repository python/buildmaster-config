from buildbot.process import factory
from buildbot.steps.shell import Configure, Compile, ShellCommand

from .steps import Test, Clean, Install, LockInstall, Uninstall

master_branch_version = "3.8"

# This (default) timeout is for each individual test file.
# It is a bit more than the default faulthandler timeout in regrtest.py
# (the latter isn't easily changed under Windows).
TEST_TIMEOUT = 20 * 60


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
    interpreterFlags = ""
    testFlags = "-j2"
    makeTarget = "all"
    test_timeout = None

    def setup(self, parallel, test_with_PTY=False, **kwargs):
        self.addStep(
            Configure(
                command=["./configure", "--prefix", "$(PWD)/target"]
                + self.configureFlags
            )
        )
        compile = ["make", self.makeTarget]
        testopts = self.testFlags
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

        self.addStep(Compile(command=compile))
        self.addStep(
            ShellCommand(
                name="pythoninfo",
                description="pythoninfo",
                command=["make", "pythoninfo"],
                warnOnFailure=True,
            )
        )
        self.addStep(
            Test(command=test, timeout=self.test_timeout, usePTY=test_with_PTY)
        )
        self.addStep(Clean())


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
            branch = master_branch_version
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
            Test(command=test, timeout=self.test_timeout, usePTY=test_with_PTY)
        )
        self.addStep(Uninstall())
        self.addStep(Clean())


class UnixBuildWithICC(UnixBuild):
    configureFlags = ["--with-pydebug", "--with-icc"]
    factory_tags = ["icc"]


class NonDebugUnixBuildWithICC(UnixBuildWithICC):
    buildersuffix = ".nondebug"
    configureFlags = ["--with-icc"]
    factory_tags = ["icc", "nondebug"]


class UnixBuildWithoutDocStrings(UnixBuild):
    configureFlags = ["--with-pydebug", "--without-doc-strings"]


class AIXBuild(UnixBuild):
    configureFlags = [
        "--with-pydebug",
        "--with-openssl=/opt/aixtools",
        "--without-computed-gotos",
    ]


class AIXBuildWithGcc(UnixBuild):
    configureFlags = [
        "--with-pydebug",
        "--with-openssl=/opt/aixtools",
        "--with-gcc=yes",
    ]


class NonDebugUnixBuild(UnixBuild):
    buildersuffix = ".nondebug"
    configureFlags = []
    factory_tags = ["nondebug"]


class OptimizeUnixBuild(UnixBuild):
    interpreterFlags = "-OO"


class PGOUnixBuild(NonDebugUnixBuild):
    configureFlags = ["--enable-optimizations"]
    factory_tags = ["pgo"]


class ClangUbsanLinuxBuild(UnixBuild):
    configureFlags = [
        "CC=clang",
        "LD=clang",
        "CFLAGS=-fsanitize=undefined",
        "LDFLAGS=-fsanitize=undefined",
    ]
    testFlags = "-j4"
    factory_tags = ["clang", "ubsan", "sanitizer"]


class SharedUnixBuild(UnixBuild):
    configureFlags = ["--with-pydebug", "--enable-shared"]
    factory_tags = ["shared"]


class UniversalOSXBuild(UnixBuild):
    configureFlags = [
        "--with-pydebug",
        "--enable-universalsdk=/",
        "--with-universal-archs=intel",
    ]
    # Disabled until issues with test_bigmem get solved
    # We could put more but it would make test_bigmem even longer
    # testFlags = "-M5.5G"


class CLangBuild(UnixBuild):
    configureFlags = ["--with-pydebug", "CC=clang"]
    factory_tags = ["clang"]


class OptimizedCLangBuild(CLangBuild):
    interpreterFlags = "-OO"


class DTraceBuild(UnixBuild):
    configureFlags = ["--with-pydebug", "--with-dtrace"]
    factory_tags = ["dtrace"]


class DTraceCLangBuild(UnixBuild):
    configureFlags = ["--with-pydebug", "--with-dtrace", "CC=clang"]
    factory_tags = ["dtrace", "clang"]


##############################################################################
############################  WINDOWS BUILDS  ################################
##############################################################################


class WindowsBuild(TaggedBuildFactory):
    build_command = [r"Tools\buildbot\build.bat"]
    test_command = [r"Tools\buildbot\test.bat"]
    clean_command = [r"Tools\buildbot\clean.bat"]
    python_command = [r"python.bat"]
    buildFlags = []
    testFlags = ["-j2"]
    cleanFlags = []
    test_timeout = None
    factory_tags = ["win32"]

    def setup(self, parallel, branch, **kwargs):
        build_command = self.build_command + self.buildFlags
        test_command = self.test_command + self.testFlags
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
        # timeout is a bit more than the regrtest default timeout
        if self.test_timeout:
            timeout = self.test_timeout
        else:
            timeout = TEST_TIMEOUT
        if branch != "2.7":
            test_command += ["--timeout", timeout - (5 * 60)]
        self.addStep(Test(command=test_command, timeout=timeout))
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
    testFlags = ["-j2", "-u-cpu", "-u-largefile"]


class Windows27VS9Build(WindowsBuild):
    buildersuffix = "vs9"
    build_command = [r"PC\VS9.0\build.bat", "-e", "-k", "-d"]
    test_command = [r"PC\VS9.0\rt.bat", "-q", "-d", "-uall", "-rwW", "--slowest"]
    clean_command = [r"PC\VS9.0\build.bat", "-t", "Clean", "-d"]
    python_command = [r"PC\VS9.0\python_d.exe"]
    factory_tags = ["win32", "vs9"]


class Windows6427VS9Build(Windows27VS9Build):
    test_command = [
        r"PC\VS9.0\rt.bat",
        "-x64",
        "-q",
        "-d",
        "-uall",
        "-rwW",
        "--slowest",
    ]
    buildFlags = ["-p", "x64"]
    cleanFlags = ["-p", "x64"]
    python_command = [r"PC\VS9.0\amd64\python_d.exe"]
    factory_tags = ["win64", "vs9"]


class Windows64Build(WindowsBuild):
    buildFlags = ["-p", "x64"]
    testFlags = ["-x64", "-j2"]
    cleanFlags = ["-p", "x64"]
    factory_tags = ["win64"]


class Windows64RefleakBuild(Windows64Build):
    buildersuffix = ".refleak"
    testFlags = ["-x64"] + WindowsRefleakBuild.testFlags
    # -R 3:3 is supposed to only require timeout x 6, but in practice,
    # it's much more slower. Use timeout x 10 to prevent timeout
    # caused by --huntrleaks.
    test_timeout = TEST_TIMEOUT * 10
    factory_tags = ["win64", "refleak"]


class Windows64ReleaseBuild(Windows64Build):
    buildFlags = Windows64Build.buildFlags + ["-c", "Release"]
    testFlags = Windows64Build.testFlags + ["+d"]
    # keep default cleanFlags, both configurations get cleaned
    factory_tags = ["win64", "nondebug"]


windows_icc_build_flags = ["--no-tkinter", "/p:PlatformToolset=Intel C++ Compiler 16.0"]


class Windows64ICCBuild(Windows64Build):
    buildFlags = Windows64Build.buildFlags + windows_icc_build_flags
    factory_tags = ["win64", "icc"]


class Windows64ICCReleaseBuild(Windows64ReleaseBuild):
    buildersuffix = ".nondebug"
    buildFlags = Windows64ReleaseBuild.buildFlags + windows_icc_build_flags
    factory_tags = ["win64", "icc", "nondebug"]
