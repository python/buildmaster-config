from custom.factories import (
    UnixBuild,
    UnixTraceRefsBuild,
    UnixRefleakBuild,
    UnixInstalledBuild,
    AIXBuild,
    AIXBuildWithoutComputedGotos,
    NonDebugUnixBuild,
    PGOUnixBuild,
    ClangUbsanLinuxBuild,
    ClangUnixInstalledBuild,
    SharedUnixBuild,
    LTONonDebugUnixBuild,
    LTOPGONonDebugBuild,
    WindowsBuild,
    SlowWindowsBuild,
    Windows27VS9Build,
    Windows6427VS9Build,
    Windows64Build,
    Windows64RefleakBuild,
    Windows64ReleaseBuild,
    WindowsArm32Build,
    WindowsArm32ReleaseBuild,
)

STABLE = "stable"
UNSTABLE = "unstable"


# classes using longer timeout for koobs's very slow buildbots
class SlowNonDebugUnixBuild(NonDebugUnixBuild):
    test_timeout = 30 * 60


class SlowSharedUnixBuild(SharedUnixBuild):
    test_timeout = 30 * 60


def get_builders(settings):
    # Override with a default simple worker if we are using local workers
    if settings.use_local_worker:
        return [("Test Builder", "local-worker", UnixBuild, STABLE)]

    return [
        # -- Stable builders --
        # Linux
        ("AMD64 Debian root", "angelico-debian-amd64", UnixBuild, STABLE),
        ("AMD64 Debian PGO", "gps-debian-profile-opt", PGOUnixBuild, STABLE),
        ("AMD64 Ubuntu Shared", "bolen-ubuntu", SharedUnixBuild, STABLE),
        ("ARMv7 Debian buster", "gps-ubuntu-exynos5-armv7l", UnixBuild, STABLE),
        ("PPC64 Fedora", "edelsohn-fedora-ppc64", UnixBuild, STABLE),
        ("PPC64LE Fedora", "edelsohn-fedora-ppc64le", UnixBuild, STABLE),
        ("s390x SLES", "edelsohn-sles-z", UnixBuild, STABLE),
        ("s390x Debian", "edelsohn-debian-z", UnixBuild, STABLE),
        ("s390x RHEL7", "edelsohn-rhel-z", UnixBuild, STABLE),
        ("s390x RHEL8", "edelsohn-rhel8-z", UnixBuild, STABLE),
        ("x86 Gentoo Non-Debug with X", "ware-gentoo-x86", NonDebugUnixBuild, STABLE),
        ("x86 Gentoo Installed with X", "ware-gentoo-x86", UnixInstalledBuild, STABLE),
        ("x86 Gentoo Refleaks", "ware-gentoo-x86", UnixRefleakBuild, STABLE),
        ("AMD64 Fedora Stable", "cstratak-fedora-stable-x86_64", UnixBuild, STABLE),
        ("AMD64 Fedora Stable Refleaks", "cstratak-fedora-stable-x86_64", UnixRefleakBuild, STABLE,),
        ("AMD64 Fedora Stable Clang", "cstratak-fedora-stable-x86_64", ClangUbsanLinuxBuild, STABLE,),
        ("AMD64 Fedora Stable Clang Installed", "cstratak-fedora-stable-x86_64", ClangUnixInstalledBuild, STABLE,),
        ("AMD64 Fedora Stable LTO", "cstratak-fedora-stable-x86_64", LTONonDebugUnixBuild, STABLE,),
        ("AMD64 Fedora Stable LTO + PGO", "cstratak-fedora-stable-x86_64", LTOPGONonDebugBuild, STABLE,),
        ("AMD64 RHEL7", "cstratak-RHEL7-x86_64", UnixBuild, STABLE),
        ("AMD64 RHEL7 Refleaks", "cstratak-RHEL7-x86_64", UnixRefleakBuild, STABLE),
        ("AMD64 RHEL7 LTO", "cstratak-RHEL7-x86_64", LTONonDebugUnixBuild, STABLE),
        ("AMD64 RHEL7 LTO + PGO", "cstratak-RHEL7-x86_64", LTOPGONonDebugBuild, STABLE),
        ("AMD64 RHEL8", "cstratak-RHEL8-x86_64", UnixBuild, STABLE),
        ("AMD64 RHEL8 Refleaks", "cstratak-RHEL8-x86_64", UnixRefleakBuild, STABLE),
        ("AMD64 RHEL8 LTO", "cstratak-RHEL8-x86_64", LTONonDebugUnixBuild, STABLE),
        ("AMD64 RHEL8 LTO + PGO", "cstratak-RHEL8-x86_64", LTOPGONonDebugBuild, STABLE),
        # macOS
        ("x86-64 macOS", "billenstein-macos", UnixBuild, STABLE),
        # Other Unix
        ("AMD64 FreeBSD Non-Debug", "koobs-freebsd-9e36", SlowNonDebugUnixBuild, STABLE,),
        ("AMD64 FreeBSD Shared", "koobs-freebsd-564d", SlowSharedUnixBuild, STABLE),
        # Windows
        ("AMD64 Windows7 SP1", "kloth-win64", Windows64Build, STABLE),
        ("AMD64 Windows7 SP1 VS9.0", "kloth-win64", Windows6427VS9Build, STABLE),
        ("AMD64 Windows10", "bolen-windows10", Windows64Build, STABLE),
        ("AMD64 Windows8.1 Non-Debug", "ware-win81-release", Windows64ReleaseBuild, STABLE,),
        ("AMD64 Windows8.1 Refleaks", "ware-win81-release", Windows64RefleakBuild, STABLE,),
        ("x86 Windows7", "bolen-windows7", SlowWindowsBuild, STABLE),
        ("x86 Windows XP", "bolen-windows", WindowsBuild, STABLE),
        ("x86 Windows XP VS9.0", "bolen-windows", Windows27VS9Build, STABLE),
        # -- Unstable builders --
        # Linux x86 / AMD64
        ("AMD64 Clang UBSan", "gps-clang-ubsan", ClangUbsanLinuxBuild, UNSTABLE),
        ("AMD64 Alpine Linux", "ware-alpine", UnixBuild, UNSTABLE),
        ("AMD64 Ubuntu", "einat-ubuntu", UnixBuild, UNSTABLE),
        ("AMD64 Fedora Rawhide", "cstratak-fedora-rawhide-x86_64", UnixBuild, UNSTABLE),
        ("AMD64 Fedora Rawhide Refleaks", "cstratak-fedora-rawhide-x86_64", UnixRefleakBuild, UNSTABLE,),
        ("AMD64 Fedora Rawhide Clang", "cstratak-fedora-rawhide-x86_64", ClangUbsanLinuxBuild, UNSTABLE,),
        ("AMD64 Fedora Rawhide Clang Installed", "cstratak-fedora-rawhide-x86_64", ClangUnixInstalledBuild, UNSTABLE,),
        ("AMD64 Fedora Rawhide LTO", "cstratak-fedora-rawhide-x86_64", LTONonDebugUnixBuild, UNSTABLE,),
        ("AMD64 Fedora Rawhide LTO + PGO", "cstratak-fedora-rawhide-x86_64", LTOPGONonDebugBuild, UNSTABLE,),
        ("AMD64 Arch Linux TraceRefs", "pablogsal-arch-x86_64", UnixTraceRefsBuild, STABLE),
        # Linux other archs
        # macOS
        # Other Unix
        ("AMD64 Cygwin64 on Windows 10", "bray-win10-cygwin-amd64", UnixBuild, UNSTABLE,),
        ("POWER6 AIX", "aixtools-aix-power6", AIXBuildWithoutComputedGotos, UNSTABLE),
        ("PPC64 AIX", "edelsohn-aix-ppc64", AIXBuild, UNSTABLE),
        # Windows
        ("ARM32 Windows10 1903", "monson-win-arm32", WindowsArm32Build, UNSTABLE),
        ("ARM32 Windows10 1903 Non-Debug", "monson-win-arm32", WindowsArm32ReleaseBuild, UNSTABLE,),
    ]


DAILYBUILDERS = [
    "x86 Gentoo Refleaks",
    "AMD64 Windows8.1 Refleaks",
    "AMD64 Fedora Rawhide Refleaks",
    "AMD64 Fedora Stable Refleaks",
    "AMD64 RHEL7 Refleaks",
    "AMD64 RHEL8 Refleaks",
]

# Match builder name (excluding the branch name) of builders that should only
# run on the master and "custom" branches.
ONLY_MASTER_BRANCH = (
    "Alpine Linux",
    # Cygwin is not supported on 2.7, 3.6, 3.7
    "Cygwin",
    # ARM32 Windows support is 3.8+ only
    "ARM32 Windows",
)
