from buildbot.process import factory
from buildbot.steps.shell import Configure, Compile, ShellCommand

from .steps import Test, Clean, CleanupTest, Install, LockInstall, Uninstall, UploadTestResults

master_branch_version = "3.9"
CUSTOM_BRANCH_NAME = "custom"

# This (default) timeout is for each individual test file.
# It is a bit more than the default faulthandler timeout in regrtest.py
# (the latter isn't easily changed under Windows).
TEST_TIMEOUT = 20 * 60


def regrtest_has_cleanup(branch):
    # "python -m test --cleanup" is available in Python 3.7 and newer,
    # and in Python 2.7.
    return (branch not in ("3.4", "3.5", "3.6", CUSTOM_BRANCH_NAME))


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

    def setup(self, parallel, branch, test_with_PTY=False, **kwargs):
        self.addStep(
            Configure(
                command=["./configure", "--prefix", "$(PWD)/target"]
                + self.configureFlags
            )
        )
        compile = ["make", self.makeTarget]
        testopts = self.testFlags
        if branch != "2.7":
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
        cleantest = [
            "make",
            "cleantest",
            "TESTOPTS=" + testopts + " ${BUILDBOT_TESTOPTS}",
            "TESTPYTHONOPTS=" + self.interpreterFlags,
            "TESTTIMEOUT=" + str(faulthandler_timeout),
        ]
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
        # FIXME: https://bugs.python.org/issue37359#msg346686
        #if regrtest_has_cleanup(branch):
        #    self.addStep(CleanupTest(command=cleantest))
        self.addStep(
            Test(command=test, timeout=self.test_timeout, usePTY=test_with_PTY)
        )
        if branch != "2.7":
            self.addStep(UploadTestResults())
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
        if branch != "2.7":
            faulthandler_timeout = self.test_timeout - 5 * 60
            testopts += [f'--timeout={faulthandler_timeout}']
        if parallel:
            compile = ["make", parallel, self.makeTarget]
            install = ["make", parallel, self.installTarget]
            testopts = testopts + [parallel]

        test = [installed_python] + self.interpreterFlags
        test += ["-m", "test.regrtest"] + testopts

        cleantest = test + ["--cleanup"]

        self.addStep(Compile(command=compile))
        self.addStep(Install(command=install))
        self.addStep(LockInstall())
        # FIXME: https://bugs.python.org/issue37359#msg346686
        #if regrtest_has_cleanup(branch):
        #    self.addStep(CleanupTest(command=cleantest))
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


class UnixBuildWithoutDocStrings(UnixBuild):
    configureFlags = ["--with-pydebug", "--without-doc-strings"]


class AIXBuildWithoutComputedGotos(UnixBuild):
    configureFlags = [
        "--with-pydebug",
        "--with-openssl=/opt/aixtools",
        "--without-computed-gotos",
    ]


class AIXBuild(UnixBuild):
    configureFlags = [
        "--with-pydebug",
        "--with-openssl=/opt/aixtools",
    ]


class NonDebugUnixBuild(UnixBuild):
    buildersuffix = ".nondebug"
    configureFlags = []
    factory_tags = ["nondebug"]


class PGOUnixBuild(NonDebugUnixBuild):
    buildersuffix = ".pgo"
    configureFlags = ["--enable-optimizations"]
    factory_tags = ["pgo"]


class ClangUbsanLinuxBuild(UnixBuild):
    buildersuffix = ".clang-ubsan"
    configureFlags = [
        "CC=clang",
        "LD=clang",
        "CFLAGS=-fsanitize=undefined",
        "LDFLAGS=-fsanitize=undefined",
    ]
    testFlags = "-j4"
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
    buildFlags = []
    remoteDeployFlags = []
    remotePythonInfoFlags = []
    testFlags = ["-j2"]
    cleanFlags = []
    test_timeout = None
    factory_tags = ["win32"]
    remoteTest = False

    def setup(self, parallel, branch, **kwargs):
        build_command = self.build_command + self.buildFlags
        test_command = self.test_command + self.testFlags
        if branch != "2.7":
            test_command += " --junit-xml test-results.xml"
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
        # timeout is a bit more than the regrtest default timeout
        if self.test_timeout:
            timeout = self.test_timeout
        else:
            timeout = TEST_TIMEOUT
        if branch != "2.7":
            test_command += ["--timeout", timeout - (5 * 60)]
        # FIXME: https://bugs.python.org/issue37359#msg346686
        #if regrtest_has_cleanup(branch):
        #    cleantest = test_command + ["--cleanup"]
        #    self.addStep(CleanupTest(command=cleantest))
        self.addStep(Test(command=test_command, timeout=timeout))
        if branch != "2.7":
            self.addStep(UploadTestResults())
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
    buildersuffix = ".nondebug"
    buildFlags = Windows64Build.buildFlags + ["-c", "Release"]
    testFlags = Windows64Build.testFlags + ["+d"]
    # keep default cleanFlags, both configurations get cleaned
    factory_tags = ["win64", "nondebug"]


windows_icc_build_flags = ["--no-tkinter", "/p:PlatformToolset=Intel C++ Compiler 16.0"]


class WindowsArm32Build(WindowsBuild):
    buildFlags = ["-p", "ARM", "--no-tkinter"]
    # test_multiprocessing_spawn doesn't complete over simple ssh connection
    # skip test_multiprocessing_spawn for now
    remoteTest = True
    remoteDeployFlags = ["-arm32"]
    remotePythonInfoFlags = ["-arm32"]
    testFlags = ["-arm32", "-x", "test_multiprocessing_spawn", "-x", "test_winconsoleio", "-x", "test_distutils"]
    cleanFlags = ["-p", "ARM", "--no-tkinter"]
    factory_tags = ["win-arm32"]


class WindowsArm32ReleaseBuild(WindowsArm32Build):
    buildersuffix = ".nondebug"
    buildFlags = WindowsArm32Build.buildFlags + ["-c", "Release"]
    remotePythonInfoFlags = WindowsArm32Build.remotePythonInfoFlags + ["+d"]
    testFlags = WindowsArm32Build.testFlags + ["+d"]
    # keep default cleanFlags, both configurations get cleaned
    factory_tags = ["win-arm32", "nondebug"]
