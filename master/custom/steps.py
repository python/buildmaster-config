import re

from buildbot.plugins import steps, util
from buildbot.process.results import SUCCESS, WARNINGS
from buildbot.steps.shell import ShellCommand, Test as BaseTest
from buildbot.steps.source.git import Git as _Git
from buildbot.steps.source.github import GitHub as _GitHub

from . import JUNIT_FILENAME


class Git(_Git):
    # GH-68: If "git clone" fails, mark the whole build as WARNING
    # (warnOnFailure), not as "FAILURE" (flunkOnFailure)
    haltOnFailure = True
    flunkOnFailure = False
    warnOnFailure = True


class GitHub(_GitHub):
    # GH-68: If "git clone" fails, mark the whole build as WARNING
    # (warnOnFailure), not as "FAILURE" (flunkOnFailure)
    haltOnFailure = True
    flunkOnFailure = False
    warnOnFailure = True


class Test(BaseTest):
    # Regular expression used to catch warnings, errors and bugs
    warningPattern = (
        # regrtest saved_test_environment warning:
        # Warning -- files was modified by test_distutils
        # test.support @reap_threads:
        # Warning -- threading_cleanup() failed to cleanup ...
        r"Warning -- ",

        # Py_FatalError() call
        r"Fatal Python error:",

        # PyErr_WriteUnraisable() exception: usually, error in
        # garbage collector or destructor
        r"Exception ignored in:",

        # faulthandler_exc_handler(): Windows exception handler installed with
        # AddVectoredExceptionHandler() by faulthandler.enable()
        r"Windows fatal exception:",

        # Resource warning: unclosed file, socket, etc.
        # NOTE: match the "ResourceWarning" anywhere, not only at the start
        r"ResourceWarning",

        # regrtest: At least one test failed. Log a warning even if the test
        # passed on the second try, to notify that a test is unstable.
        r"Re-running failed tests in verbose mode",

        # Re-running test 'test_multiprocessing_fork' in verbose mode
        r"Re-running test.* in verbose mode",

        # Thread last resort exception handler in t_bootstrap()
        r"Unhandled exception in thread started by ",

        # test_os leaked [6, 6, 6] memory blocks, sum=18,
        r"test_[^ ]+ leaked ",

        # FAIL: test_stdin_broken_pipe (test.test_asyncio...)
        r"FAIL: ",

        # ERROR: test_pipe_handle (test.test_asyncio...)
        r"ERROR: ",

        # test.* ... unexpected success
        r"unexpected success",

        # Kill worker process 15215 running for 1350.1 sec
        r"Kill worker process ",

        # test test_ssl failed -- multiple errors occurred; run in verbose mode for details
        r"test .* failed -- multiple errors occurred; run in verbose mode for details",

        # OSError: [Errno 28] No space left on device: ...
        r'No space left on device',
    )
    # Use ".*" prefix to search the regex anywhere since stdout is mixed
    # with stderr, so warnings are not always written at the start
    # of a line. The log consumer calls warningPattern.match(line)
    warningPattern = r".*(?:%s)" % "|".join(warningPattern)
    warningPattern = re.compile(warningPattern)

    # if tests have warnings, mark the overall build as WARNINGS (orange)
    warnOnWarnings = True

    # 4 hours should be enough even for refleak builds. In practice,
    # faulthandler kills worker processes with a way shorter timeout
    # (regrtest --timeout parameter).
    maxTime = 4 * 60 * 60
    # Give SIGTERM 30 seconds to shut things down before SIGKILL.
    sigtermTime = 30

    # Treat "regrtest --fail-rerun" exit code (5) as WARNINGS
    # https://github.com/python/cpython/issues/108834
    decodeRC = {
        0: SUCCESS,

        # Treat --fail-rerun exit code (5) to WARNINGS, when a test failed but
        # passed when run again in verbose mode in a fresh process (unstable
        # test).
        5: WARNINGS,     # EXITCODE_RERUN_FAIL

        # Any exit code not present in the dictionary is treated as FAILURE.
        # So there is no need to map each regrtest exit code to FAILURE.
        #
        # 2: FAILURE,    # EXITCODE_BAD_TEST
        # 3: FAILURE,    # EXITCODE_ENV_CHANGED
        # 4: FAILURE,    # EXITCODE_NO_TESTS_RAN
        # 130: FAILURE,  # EXITCODE_INTERRUPTED
    }

    def evaluateCommand(self, cmd):
        result = super().evaluateCommand(cmd)
        if cmd.didFail():
            self.setProperty("test_failed_to_build", True)
            self.setProperty("want_xml_upload", True)
        elif result == WARNINGS:
            # For warnings, upload XML for main branch stable builders
            tags = self.build.builder.config.tags
            if 'stable' in tags and '3.x' in tags:
                self.setProperty("want_xml_upload", True)
        return result


class Clean(ShellCommand):
    name = "clean"
    flunkOnFailure = False
    warnOnFailure = True
    description = ["cleaning"]
    descriptionDone = ["clean"]
    command = ["make", "distclean"]
    alwaysRun = True


class CleanupTest(ShellCommand):
    name = "cleantest"
    description = ["cleaning previous tests"]
    descriptionDone = ["clean previous tests"]
    flunkOnFailure = False
    warnOnFailure = True


class Install(ShellCommand):
    name = "install"
    description = ["installing"]
    descriptionDone = ["Installed"]
    command = ["make", "install"]
    haltOnFailure = True


class LockInstall(ShellCommand):
    name = "chmod"
    description = ["changing permissions"]
    descriptionDone = ["made install dir unwritable"]
    command = ["chmod", "-R", "-w", "target/"]


class Uninstall(ShellCommand):
    name = "uninstall"
    description = ["uninstalling"]
    descriptionDone = ["Uninstalled"]
    command = "chmod -R +w target/ &&  rm -rf target/"
    alwaysRun = True
    usePTY = False
    # GH-68: For "Install" builbot workers, when "git clone" fails, the
    # uninstall step fails since the target/ directory doesn't exist. In this
    # case, only mark the build as WARNING (warnOnFailure), instead of
    # "FAILURE" (flunkOnFailure).
    warnOnFailure = True


class UploadTestResults(steps.FileUpload):
    warnOnFailure = True
    haltOnFailure = False
    flunkOnFailure = False
    alwaysRun = True

    def _want_xml_upload(self, build):
        return self.getProperty("want_xml_upload")

    def __init__(self, branch, filename=JUNIT_FILENAME):
        super().__init__(
            doStepIf=self._want_xml_upload,
            workersrc=filename,
            masterdest=util.Interpolate(
                f"/data/www/buildbot/test-results/{branch}/%(prop:buildername)s/build_%(prop:buildnumber)s.xml"
            ),
            mode=0o755,
        )
