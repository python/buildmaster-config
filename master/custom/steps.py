import re

from buildbot.steps.shell import ShellCommand, Test as BaseTest


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
        r'Re-running failed tests in verbose mode',
        # Re-running test 'test_multiprocessing_fork' in verbose mode
        r'Re-running test .* in verbose mode',
        # Thread last resort exception handler in t_bootstrap()
        r'Unhandled exception in thread started by ',
        # test_os leaked [6, 6, 6] memory blocks, sum=18,
        r'test_[^ ]+ leaked ',
        # FAIL: test_stdin_broken_pipe (test.test_asyncio...)
        r'\bFAIL: ',
        # ERROR: test_pipe_handle (test.test_asyncio...)
        r'\bERROR: ',
    )
    # Use ".*" prefix to search the regex anywhere since stdout is mixed
    # with stderr, so warnings are not always written at the start
    # of a line. The log consumer calls warningPattern.match(line)
    warningPattern = r".*(?:%s)" % "|".join(warningPattern)
    warningPattern = re.compile(warningPattern)

    # if tests have warnings, mark the overall build as WARNINGS (orange)
    warnOnWarnings = True


class Clean(ShellCommand):
    name = "clean"
    warnOnFailure = 1
    description = ["cleaning"]
    descriptionDone = ["clean"]
    command = ["make", "distclean"]
    alwaysRun = True


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
