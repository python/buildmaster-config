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
        ("s390x SLES", "edelsohn-sles-z", UnixBuild, STABLE),
        ("s390x Debian", "edelsohn-debian-z", UnixBuild, STABLE),
        ("s390x Fedora", "edelsohn-fedora-z", UnixBuild, STABLE),
        ("s390x Fedora Refleaks", "edelsohn-fedora-z", UnixRefleakBuild, STABLE),
        ("s390x Fedora Clang", "edelsohn-fedora-z", ClangUbsanLinuxBuild, STABLE),
        ("s390x Fedora Clang Installed", "edelsohn-fedora-z", ClangUnixInstalledBuild, STABLE),
        ("s390x Fedora LTO", "edelsohn-fedora-z", LTONonDebugUnixBuild, STABLE),
        ("s390x Fedora LTO + PGO", "edelsohn-fedora-z", LTOPGONonDebugBuild, STABLE),
        ("s390x RHEL7", "edelsohn-rhel-z", UnixBuild, STABLE),
        ("s390x RHEL7 Refleaks", "edelsohn-rhel-z", UnixRefleakBuild, STABLE),
        ("s390x RHEL7 LTO", "edelsohn-rhel-z", LTONonDebugUnixBuild, STABLE),
        ("s390x RHEL7 LTO + PGO", "edelsohn-rhel-z", LTOPGONonDebugBuild, STABLE),
        ("s390x RHEL8", "edelsohn-rhel8-z", UnixBuild, STABLE),
        ("s390x RHEL8 Refleaks", "edelsohn-rhel8-z", UnixRefleakBuild, STABLE),
        ("s390x RHEL8 LTO", "edelsohn-rhel8-z", LTONonDebugUnixBuild, STABLE),
        ("s390x RHEL8 LTO + PGO", "edelsohn-rhel8-z", LTOPGONonDebugBuild, STABLE),
        ("x86 Gentoo Non-Debug with X", "ware-gentoo-x86", NonDebugUnixBuild, STABLE),
        ("x86 Gentoo Installed with X", "ware-gentoo-x86", UnixInstalledBuild, STABLE),
        ("x86 Gentoo Refleaks", "ware-gentoo-x86", UnixRefleakBuild, STABLE),
        ("AMD64 Fedora Stable", "cstratak-fedora-stable-x86_64", UnixBuild, STABLE),
        ("AMD64 Fedora Stable Refleaks", "cstratak-fedora-stable-x86_64", UnixRefleakBuild, STABLE),
        ("AMD64 Fedora Stable Clang", "cstratak-fedora-stable-x86_64", ClangUbsanLinuxBuild, STABLE),
        ("AMD64 Fedora Stable Clang Installed", "cstratak-fedora-stable-x86_64", ClangUnixInstalledBuild, STABLE),
        ("AMD64 Fedora Stable LTO", "cstratak-fedora-stable-x86_64", LTONonDebugUnixBuild, STABLE),
        ("AMD64 Fedora Stable LTO + PGO", "cstratak-fedora-stable-x86_64", LTOPGONonDebugBuild, STABLE),
        ("AMD64 RHEL7", "cstratak-RHEL7-x86_64", UnixBuild, STABLE),
        ("AMD64 RHEL7 Refleaks", "cstratak-RHEL7-x86_64", UnixRefleakBuild, STABLE),
        ("AMD64 RHEL7 LTO", "cstratak-RHEL7-x86_64", LTONonDebugUnixBuild, STABLE),
        ("AMD64 RHEL7 LTO + PGO", "cstratak-RHEL7-x86_64", LTOPGONonDebugBuild, STABLE),
        ("AMD64 RHEL8", "cstratak-RHEL8-x86_64", UnixBuild, STABLE),
        ("AMD64 RHEL8 Refleaks", "cstratak-RHEL8-x86_64", UnixRefleakBuild, STABLE),
        ("AMD64 RHEL8 LTO", "cstratak-RHEL8-x86_64", LTONonDebugUnixBuild, STABLE),
        ("AMD64 RHEL8 LTO + PGO", "cstratak-RHEL8-x86_64", LTOPGONonDebugBuild, STABLE),
        ("PPC64LE Fedora Stable", "cstratak-fedora-stable-ppc64le", UnixBuild, STABLE),
        ("PPC64LE Fedora Stable Refleaks", "cstratak-fedora-stable-ppc64le", UnixRefleakBuild, STABLE),
        ("PPC64LE Fedora Stable Clang", "cstratak-fedora-stable-ppc64le", ClangUbsanLinuxBuild, STABLE),
        ("PPC64LE Fedora Stable Clang Installed", "cstratak-fedora-stable-ppc64le", ClangUnixInstalledBuild, STABLE),
        ("PPC64LE Fedora Stable LTO", "cstratak-fedora-stable-ppc64le", LTONonDebugUnixBuild, STABLE),
        ("PPC64LE Fedora Stable LTO + PGO", "cstratak-fedora-stable-ppc64le", LTOPGONonDebugBuild, STABLE),
        ("PPC64LE RHEL7", "cstratak-RHEL7-ppc64le", UnixBuild, STABLE),
        ("PPC64LE RHEL7 Refleaks", "cstratak-RHEL7-ppc64le", UnixRefleakBuild, STABLE),
        ("PPC64LE RHEL7 LTO", "cstratak-RHEL7-ppc64le", LTONonDebugUnixBuild, STABLE),
        ("PPC64LE RHEL7 LTO + PGO", "cstratak-RHEL7-ppc64le", LTOPGONonDebugBuild, STABLE),
        ("PPC64LE RHEL8", "cstratak-RHEL8-ppc64le", UnixBuild, STABLE),
        ("PPC64LE RHEL8 Refleaks", "cstratak-RHEL8-ppc64le", UnixRefleakBuild, STABLE),
        ("PPC64LE RHEL8 LTO", "cstratak-RHEL8-ppc64le", LTONonDebugUnixBuild, STABLE),
        ("PPC64LE RHEL8 LTO + PGO", "cstratak-RHEL8-ppc64le", LTOPGONonDebugBuild, STABLE),
        # macOS
        ("x86-64 macOS", "billenstein-macos", UnixBuild, STABLE),
        # Other Unix
        ("AMD64 FreeBSD Non-Debug", "koobs-freebsd-9e36", SlowNonDebugUnixBuild, STABLE),
        ("AMD64 FreeBSD Shared", "koobs-freebsd-564d", SlowSharedUnixBuild, STABLE),
        # Windows
        ("AMD64 Windows7 SP1", "kloth-win64", Windows64Build, STABLE),
        ("AMD64 Windows7 SP1 VS9.0", "kloth-win64", Windows6427VS9Build, STABLE),
        ("AMD64 Windows10", "bolen-windows10", Windows64Build, STABLE),
        ("AMD64 Windows8.1 Non-Debug", "ware-win81-release", Windows64ReleaseBuild, STABLE),
        ("AMD64 Windows8.1 Refleaks", "ware-win81-release", Windows64RefleakBuild, STABLE),
        ("x86 Windows7", "bolen-windows7", SlowWindowsBuild, STABLE),
        ("x86 Windows XP", "bolen-windows", WindowsBuild, STABLE),
        ("x86 Windows XP VS9.0", "bolen-windows", Windows27VS9Build, STABLE),
        # -- Unstable builders --
        # Linux x86 / AMD64
        ("AMD64 Clang UBSan", "gps-clang-ubsan", ClangUbsanLinuxBuild, UNSTABLE),
        ("AMD64 Alpine Linux", "ware-alpine", UnixBuild, UNSTABLE),
        ("AMD64 Ubuntu", "einat-ubuntu", UnixBuild, UNSTABLE),
        ("AMD64 Fedora Rawhide", "cstratak-fedora-rawhide-x86_64", UnixBuild, UNSTABLE),
        ("AMD64 Fedora Rawhide Refleaks", "cstratak-fedora-rawhide-x86_64", UnixRefleakBuild, UNSTABLE),
        ("AMD64 Fedora Rawhide Clang", "cstratak-fedora-rawhide-x86_64", ClangUbsanLinuxBuild, UNSTABLE),
        ("AMD64 Fedora Rawhide Clang Installed", "cstratak-fedora-rawhide-x86_64", ClangUnixInstalledBuild, UNSTABLE),
        ("AMD64 Fedora Rawhide LTO", "cstratak-fedora-rawhide-x86_64", LTONonDebugUnixBuild, UNSTABLE),
        ("AMD64 Fedora Rawhide LTO + PGO", "cstratak-fedora-rawhide-x86_64", LTOPGONonDebugBuild, UNSTABLE),
        ("AMD64 Arch Linux TraceRefs", "pablogsal-arch-x86_64", UnixTraceRefsBuild, STABLE),
        # Linux PPC64le
        ("PPC64LE Fedora Rawhide", "cstratak-fedora-rawhide-ppc64le", UnixBuild, UNSTABLE),
        ("PPC64LE Fedora Rawhide Refleaks", "cstratak-fedora-rawhide-ppc64le", UnixRefleakBuild, UNSTABLE),
        ("PPC64LE Fedora Rawhide Clang", "cstratak-fedora-rawhide-ppc64le", ClangUbsanLinuxBuild, UNSTABLE),
        ("PPC64LE Fedora Rawhide Clang Installed", "cstratak-fedora-rawhide-ppc64le", ClangUnixInstalledBuild, UNSTABLE),
        ("PPC64LE Fedora Rawhide LTO", "cstratak-fedora-rawhide-ppc64le", LTONonDebugUnixBuild, UNSTABLE),
        ("PPC64LE Fedora Rawhide LTO + PGO", "cstratak-fedora-rawhide-ppc64le", LTOPGONonDebugBuild, UNSTABLE),
        # Linux aarch64
        ("aarch64 Fedora Rawhide", "cstratak-fedora-rawhide-aarch64", UnixBuild, UNSTABLE),
        ("aarch64 Fedora Rawhide Refleaks", "cstratak-fedora-rawhide-aarch64", UnixRefleakBuild, UNSTABLE),
        ("aarch64 Fedora Rawhide Clang", "cstratak-fedora-rawhide-aarch64", ClangUbsanLinuxBuild, UNSTABLE),
        ("aarch64 Fedora Rawhide Clang Installed", "cstratak-fedora-rawhide-aarch64", ClangUnixInstalledBuild, UNSTABLE),
        ("aarch64 Fedora Rawhide LTO", "cstratak-fedora-rawhide-aarch64", LTONonDebugUnixBuild, UNSTABLE),
        ("aarch64 Fedora Rawhide LTO + PGO", "cstratak-fedora-rawhide-aarch64", LTOPGONonDebugBuild, UNSTABLE),

        ("aarch64 Fedora Stable", "cstratak-fedora-stable-aarch64", UnixBuild, UNSTABLE),
        ("aarch64 Fedora Stable Refleaks", "cstratak-fedora-stable-aarch64", UnixRefleakBuild, UNSTABLE),
        ("aarch64 Fedora Stable Clang", "cstratak-fedora-stable-aarch64", ClangUbsanLinuxBuild, UNSTABLE),
        ("aarch64 Fedora Stable Clang Installed", "cstratak-fedora-stable-aarch64", ClangUnixInstalledBuild, UNSTABLE),
        ("aarch64 Fedora Stable LTO", "cstratak-fedora-stable-aarch64", LTONonDebugUnixBuild, UNSTABLE),
        ("aarch64 Fedora Stable LTO + PGO", "cstratak-fedora-stable-aarch64", LTOPGONonDebugBuild, UNSTABLE),

        ("aarch64 RHEL7", "cstratak-RHEL7-aarch64", UnixBuild, UNSTABLE),
        ("aarch64 RHEL7 Refleaks", "cstratak-RHEL7-aarch64", UnixRefleakBuild, UNSTABLE),
        ("aarch64 RHEL7 LTO", "cstratak-RHEL7-aarch64", LTONonDebugUnixBuild, UNSTABLE),
        ("aarch64 RHEL7 LTO + PGO", "cstratak-RHEL7-aarch64", LTOPGONonDebugBuild, UNSTABLE),

        ("aarch64 RHEL8", "cstratak-RHEL8-aarch64", UnixBuild, UNSTABLE),
        ("aarch64 RHEL8 Refleaks", "cstratak-RHEL8-aarch64", UnixRefleakBuild, UNSTABLE),
        ("aarch64 RHEL8 LTO", "cstratak-RHEL8-aarch64", LTONonDebugUnixBuild, UNSTABLE),
        ("aarch64 RHEL8 LTO + PGO", "cstratak-RHEL8-aarch64", LTOPGONonDebugBuild, UNSTABLE),

        # Linux other archs
        ("s390x Fedora Rawhide", "edelsohn-fedora-rawhide-z", UnixBuild, UNSTABLE),
        ("s390x Fedora Rawhide Refleaks", "edelsohn-fedora-rawhide-z", UnixRefleakBuild, UNSTABLE),
        ("s390x Fedora Rawhide Clang", "edelsohn-fedora-rawhide-z", ClangUbsanLinuxBuild, UNSTABLE),
        ("s390x Fedora Rawhide Clang Installed", "edelsohn-fedora-rawhide-z", ClangUnixInstalledBuild, UNSTABLE),
        ("s390x Fedora Rawhide LTO", "edelsohn-fedora-rawhide-z", LTONonDebugUnixBuild, UNSTABLE),
        ("s390x Fedora Rawhide LTO + PGO", "edelsohn-fedora-rawhide-z", LTOPGONonDebugBuild, UNSTABLE),
        # macOS
        # Other Unix
        ("AMD64 Cygwin64 on Windows 10", "bray-win10-cygwin-amd64", UnixBuild, UNSTABLE),
        ("POWER6 AIX", "aixtools-aix-power6", AIXBuildWithoutComputedGotos, UNSTABLE),
        ("PPC64 AIX", "edelsohn-aix-ppc64", AIXBuild, UNSTABLE),
        # Windows
        ("ARM32 Windows10 1903", "monson-win-arm32", WindowsArm32Build, UNSTABLE),
        ("ARM32 Windows10 1903 Non-Debug", "monson-win-arm32", WindowsArm32ReleaseBuild, UNSTABLE),
    ]


DAILYBUILDERS = [
    "x86 Gentoo Refleaks",
    "AMD64 Windows8.1 Refleaks",
    "AMD64 Fedora Rawhide Refleaks",
    "AMD64 Fedora Stable Refleaks",
    "AMD64 RHEL7 Refleaks",
    "AMD64 RHEL8 Refleaks",
    # Linux PPC64LE
    "PPC64LE Fedora Rawhide Refleaks",
    "PPC64LE Fedora Stable Refleaks",
    "PPC64LE RHEL7 Refleaks",
    "PPC64LE RHEL8 Refleaks",
    # Linux s390x
    "s390x Fedora Rawhide Refleaks",
    "s390x Fedora Refleaks",
    "s390x RHEL7 Refleaks",
    "s390x RHEL8 Refleaks",
    # Linux aarch64
    "aarch64 Fedora Rawhide Refleaks",
    "aarch64 Fedora Stable Refleaks",
    "aarch64 RHEL7 Refleaks",
    "aarch64 RHEL8 Refleaks",
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
