from custom.factories import (
    UnixBuild,
    RHEL7Build,
    RHEL8Build,
    CentOS9Build,
    FedoraStableBuild,
    FedoraRawhideBuild,
    UnixAsanBuild,
    UnixAsanDebugBuild,
    UnixTraceRefsBuild,
    UnixVintageParserBuild,
    UnixRefleakBuild,
    UnixInstalledBuild,
    AIXBuild,
    AIXBuildWithXLC,
    NonDebugUnixBuild,
    PGOUnixBuild,
    ClangUnixBuild,
    ClangUbsanLinuxBuild,
    ClangUnixInstalledBuild,
    SharedUnixBuild,
    SlowNonDebugUnixBuild,
    SlowSharedUnixBuild,
    SlowUnixInstalledBuild,
    LTONonDebugUnixBuild,
    LTOPGONonDebugBuild,
    RHEL8NoBuiltinHashesUnixBuild,
    RHEL8NoBuiltinHashesUnixBuildExceptBlake2,
    CentOS9NoBuiltinHashesUnixBuild,
    CentOS9NoBuiltinHashesUnixBuildExceptBlake2,
    SlowWindowsBuild,
    WindowsBuild,
    Windows64Build,
    Windows64RefleakBuild,
    Windows64ReleaseBuild,
    MacOSArmWithBrewBuild,
    WindowsARM64Build,
    WindowsARM64ReleaseBuild,
    Wasm32EmscriptenNodeBuild,
    Wasm32EmscriptenBrowserBuild,
    Wasm32WASIBuild,
)

STABLE = "stable"
UNSTABLE = "unstable"
TIER_1 = "tier-1"
TIER_2 = "tier-2"
TIER_3 = "tier-3"
NO_TIER = None


def get_builders(settings):
    # Override with a default simple worker if we are using local workers
    if settings.use_local_worker:
        return [("Test Builder", "local-worker", UnixBuild, STABLE, NO_TIER)]

    return [
        # -- Stable builders --
        # Linux
        ("AMD64 Debian root", "angelico-debian-amd64", UnixBuild, STABLE, NO_TIER),
        ("AMD64 Debian PGO", "gps-debian-profile-opt", PGOUnixBuild, STABLE, NO_TIER),
        ("AMD64 Ubuntu Shared", "bolen-ubuntu", SharedUnixBuild, STABLE, NO_TIER),
        ("PPC64 Fedora", "edelsohn-fedora-ppc64", FedoraStableBuild, STABLE, NO_TIER),
        ("s390x SLES", "edelsohn-sles-z", UnixBuild, STABLE, NO_TIER),
        ("s390x Debian", "edelsohn-debian-z", UnixBuild, STABLE, NO_TIER),
        ("s390x Fedora", "edelsohn-fedora-z", UnixBuild, STABLE, TIER_3),
        ("s390x Fedora Refleaks", "edelsohn-fedora-z", UnixRefleakBuild, STABLE, NO_TIER),
        ("s390x Fedora Clang", "edelsohn-fedora-z", ClangUnixBuild, STABLE, NO_TIER),
        ("s390x Fedora Clang Installed", "edelsohn-fedora-z", ClangUnixInstalledBuild, STABLE, NO_TIER),
        ("s390x Fedora LTO", "edelsohn-fedora-z", LTONonDebugUnixBuild, STABLE, NO_TIER),
        ("s390x Fedora LTO + PGO", "edelsohn-fedora-z", LTOPGONonDebugBuild, STABLE, NO_TIER),
        ("s390x RHEL7", "edelsohn-rhel-z", UnixBuild, STABLE, NO_TIER),
        ("s390x RHEL7 Refleaks", "edelsohn-rhel-z", UnixRefleakBuild, STABLE, NO_TIER),
        ("s390x RHEL7 LTO", "edelsohn-rhel-z", LTONonDebugUnixBuild, STABLE, NO_TIER),
        ("s390x RHEL7 LTO + PGO", "edelsohn-rhel-z", LTOPGONonDebugBuild, STABLE, NO_TIER),
        ("s390x RHEL8", "edelsohn-rhel8-z", UnixBuild, STABLE, NO_TIER),
        ("s390x RHEL8 Refleaks", "edelsohn-rhel8-z", UnixRefleakBuild, STABLE, NO_TIER),
        ("s390x RHEL8 LTO", "edelsohn-rhel8-z", LTONonDebugUnixBuild, STABLE, NO_TIER),
        ("s390x RHEL8 LTO + PGO", "edelsohn-rhel8-z", LTOPGONonDebugBuild, STABLE, NO_TIER),
        ("x86 Gentoo Non-Debug with X", "ware-gentoo-x86", SlowNonDebugUnixBuild, STABLE, NO_TIER),
        ("x86 Gentoo Installed with X", "ware-gentoo-x86", SlowUnixInstalledBuild, STABLE, NO_TIER),
        ("AMD64 Fedora Stable", "cstratak-fedora-stable-x86_64", FedoraStableBuild, STABLE, NO_TIER),
        ("AMD64 Fedora Stable Refleaks", "cstratak-fedora-stable-x86_64", UnixRefleakBuild, STABLE, NO_TIER),
        ("AMD64 Fedora Stable Clang", "cstratak-fedora-stable-x86_64", ClangUnixBuild, STABLE, TIER_2),
        ("AMD64 Fedora Stable Clang Installed", "cstratak-fedora-stable-x86_64", ClangUnixInstalledBuild, STABLE, NO_TIER),
        ("AMD64 Fedora Stable LTO", "cstratak-fedora-stable-x86_64", LTONonDebugUnixBuild, STABLE, NO_TIER),
        ("AMD64 Fedora Stable LTO + PGO", "cstratak-fedora-stable-x86_64", LTOPGONonDebugBuild, STABLE, NO_TIER),
        ("AMD64 RHEL7", "cstratak-RHEL7-x86_64", RHEL7Build, STABLE, NO_TIER),
        ("AMD64 RHEL7 Refleaks", "cstratak-RHEL7-x86_64", UnixRefleakBuild, STABLE, NO_TIER),
        ("AMD64 RHEL7 LTO", "cstratak-RHEL7-x86_64", LTONonDebugUnixBuild, STABLE, NO_TIER),
        ("AMD64 RHEL7 LTO + PGO", "cstratak-RHEL7-x86_64", LTOPGONonDebugBuild, STABLE, NO_TIER),
        ("AMD64 RHEL8", "cstratak-RHEL8-x86_64", RHEL8Build, STABLE, NO_TIER),
        ("AMD64 RHEL8 Refleaks", "cstratak-RHEL8-x86_64", UnixRefleakBuild, STABLE, NO_TIER),
        ("AMD64 RHEL8 LTO", "cstratak-RHEL8-x86_64", LTONonDebugUnixBuild, STABLE, NO_TIER),
        ("AMD64 RHEL8 LTO + PGO", "cstratak-RHEL8-x86_64", LTOPGONonDebugBuild, STABLE, NO_TIER),
        ("AMD64 RHEL8 FIPS Only Blake2 Builtin Hash", "cstratak-RHEL8-fips-x86_64", RHEL8NoBuiltinHashesUnixBuildExceptBlake2, STABLE, NO_TIER),
        ("AMD64 Arch Linux Asan", "pablogsal-arch-x86_64", UnixAsanBuild, STABLE, NO_TIER),
        ("AMD64 Arch Linux Usan", "pablogsal-arch-x86_64", ClangUbsanLinuxBuild, STABLE, NO_TIER),
        ("AMD64 Arch Linux Asan Debug", "pablogsal-arch-x86_64", UnixAsanDebugBuild, STABLE, NO_TIER),
        ("AMD64 Arch Linux TraceRefs", "pablogsal-arch-x86_64", UnixTraceRefsBuild, STABLE, NO_TIER),
        # Linux PPC64le
        ("PPC64LE Fedora Stable", "cstratak-fedora-stable-ppc64le", FedoraStableBuild, STABLE, TIER_2),
        ("PPC64LE Fedora Stable Refleaks", "cstratak-fedora-stable-ppc64le", UnixRefleakBuild, STABLE, NO_TIER),
        ("PPC64LE Fedora Stable Clang", "cstratak-fedora-stable-ppc64le", ClangUnixBuild, STABLE, TIER_3),
        ("PPC64LE Fedora Stable Clang Installed", "cstratak-fedora-stable-ppc64le", ClangUnixInstalledBuild, STABLE, NO_TIER),
        ("PPC64LE Fedora Stable LTO", "cstratak-fedora-stable-ppc64le", LTONonDebugUnixBuild, STABLE, NO_TIER),
        ("PPC64LE Fedora Stable LTO + PGO", "cstratak-fedora-stable-ppc64le", LTOPGONonDebugBuild, STABLE, NO_TIER),

        ("PPC64LE RHEL7", "cstratak-RHEL7-ppc64le", RHEL7Build, STABLE, NO_TIER),
        ("PPC64LE RHEL7 Refleaks", "cstratak-RHEL7-ppc64le", UnixRefleakBuild, STABLE, NO_TIER),
        ("PPC64LE RHEL7 LTO", "cstratak-RHEL7-ppc64le", LTONonDebugUnixBuild, STABLE, NO_TIER),
        ("PPC64LE RHEL7 LTO + PGO", "cstratak-RHEL7-ppc64le", LTOPGONonDebugBuild, STABLE, NO_TIER),

        ("PPC64LE RHEL8", "cstratak-RHEL8-ppc64le", RHEL8Build, STABLE, NO_TIER),
        ("PPC64LE RHEL8 Refleaks", "cstratak-RHEL8-ppc64le", UnixRefleakBuild, STABLE, NO_TIER),
        ("PPC64LE RHEL8 LTO", "cstratak-RHEL8-ppc64le", LTONonDebugUnixBuild, STABLE, NO_TIER),
        ("PPC64LE RHEL8 LTO + PGO", "cstratak-RHEL8-ppc64le", LTOPGONonDebugBuild, STABLE, NO_TIER),

        # Linux aarch64
        ("aarch64 Fedora Stable", "cstratak-fedora-stable-aarch64", FedoraStableBuild, STABLE, TIER_2),
        ("aarch64 Fedora Stable Refleaks", "cstratak-fedora-stable-aarch64", UnixRefleakBuild, STABLE, NO_TIER),
        ("aarch64 Fedora Stable Clang", "cstratak-fedora-stable-aarch64", ClangUnixBuild, STABLE, TIER_2),
        ("aarch64 Fedora Stable Clang Installed", "cstratak-fedora-stable-aarch64", ClangUnixInstalledBuild, STABLE, NO_TIER),
        ("aarch64 Fedora Stable LTO", "cstratak-fedora-stable-aarch64", LTONonDebugUnixBuild, STABLE, NO_TIER),
        ("aarch64 Fedora Stable LTO + PGO", "cstratak-fedora-stable-aarch64", LTOPGONonDebugBuild, STABLE, NO_TIER),

        ("aarch64 RHEL8", "cstratak-RHEL8-aarch64", RHEL8Build, STABLE, NO_TIER),
        ("aarch64 RHEL8 Refleaks", "cstratak-RHEL8-aarch64", UnixRefleakBuild, STABLE, NO_TIER),
        ("aarch64 RHEL8 LTO", "cstratak-RHEL8-aarch64", LTONonDebugUnixBuild, STABLE, NO_TIER),
        ("aarch64 RHEL8 LTO + PGO", "cstratak-RHEL8-aarch64", LTOPGONonDebugBuild, STABLE, NO_TIER),


        # macOS
        ("x86-64 macOS", "billenstein-macos", UnixBuild, STABLE, NO_TIER),
        ("ARM64 macOS", "pablogsal-macos-m1", MacOSArmWithBrewBuild, STABLE, TIER_2),
        # Other Unix
        ("AMD64 FreeBSD Non-Debug", "koobs-freebsd-9e36", SlowNonDebugUnixBuild, STABLE, TIER_3),
        ("AMD64 FreeBSD Shared", "koobs-freebsd-564d", SlowSharedUnixBuild, STABLE, NO_TIER),
        # Windows
        ("AMD64 Windows11", "kloth-win11", Windows64Build, UNSTABLE, NO_TIER),
        ("AMD64 Windows11 Non-Debug", "ware-win11", Windows64ReleaseBuild, UNSTABLE, NO_TIER),
        ("AMD64 Windows11 Refleaks", "ware-win11", Windows64RefleakBuild, UNSTABLE, NO_TIER),
        ("AMD64 Windows10 Pro", "kloth-win64", Windows64Build, STABLE, NO_TIER),
        ("AMD64 Windows7 SP1", "kloth-win7", Windows64Build, STABLE, NO_TIER),
        ("AMD64 Windows10", "bolen-windows10", Windows64Build, STABLE, NO_TIER),
        ("AMD64 Windows8.1 Non-Debug", "ware-win81-release", Windows64ReleaseBuild, STABLE, NO_TIER),
        #("AMD64 Windows8.1 Refleaks", "ware-win81-release", Windows64RefleakBuild, STABLE, NO_TIER),
        ("x86 Windows7", "bolen-windows7", SlowWindowsBuild, STABLE, NO_TIER),
        # -- Unstable builders --
        # Linux x86 / AMD64
        ("AMD64 Clang UBSan", "gps-clang-ubsan", ClangUbsanLinuxBuild, UNSTABLE, NO_TIER),
        ("AMD64 Alpine Linux", "ware-alpine", UnixBuild, UNSTABLE, NO_TIER),
        ("AMD64 Fedora Rawhide", "cstratak-fedora-rawhide-x86_64", FedoraRawhideBuild, UNSTABLE, NO_TIER),
        ("AMD64 Fedora Rawhide Refleaks", "cstratak-fedora-rawhide-x86_64", UnixRefleakBuild, UNSTABLE, NO_TIER),
        ("AMD64 Fedora Rawhide Clang", "cstratak-fedora-rawhide-x86_64", ClangUnixBuild, UNSTABLE, NO_TIER),
        ("AMD64 Fedora Rawhide Clang Installed", "cstratak-fedora-rawhide-x86_64", ClangUnixInstalledBuild, UNSTABLE, NO_TIER),
        ("AMD64 Fedora Rawhide LTO", "cstratak-fedora-rawhide-x86_64", LTONonDebugUnixBuild, UNSTABLE, NO_TIER),
        ("AMD64 Fedora Rawhide LTO + PGO", "cstratak-fedora-rawhide-x86_64", LTOPGONonDebugBuild, UNSTABLE, NO_TIER),
        ("AMD64 Ubuntu", "skumaran-ubuntu-x86_64", UnixBuild, UNSTABLE, NO_TIER),
        ("AMD64 Arch Linux VintageParser", "pablogsal-arch-x86_64", UnixVintageParserBuild, UNSTABLE, NO_TIER),
        ("AMD64 RHEL8 FIPS No Builtin Hashes", "cstratak-RHEL8-fips-x86_64", RHEL8NoBuiltinHashesUnixBuild, UNSTABLE, NO_TIER),
        ("AMD64 CentOS9", "cstratak-CentOS9-x86_64", CentOS9Build, UNSTABLE, NO_TIER),
        ("AMD64 CentOS9 Refleaks", "cstratak-CentOS9-x86_64", UnixRefleakBuild, UNSTABLE, NO_TIER),
        ("AMD64 CentOS9 LTO", "cstratak-CentOS9-x86_64", LTONonDebugUnixBuild, UNSTABLE, NO_TIER),
        ("AMD64 CentOS9 LTO + PGO", "cstratak-CentOS9-x86_64", LTOPGONonDebugBuild, UNSTABLE, NO_TIER),
        ("AMD64 CentOS9 FIPS Only Blake2 Builtin Hash", "cstratak-CentOS9-fips-x86_64", CentOS9NoBuiltinHashesUnixBuildExceptBlake2, UNSTABLE, NO_TIER),
        ("AMD64 CentOS9 FIPS No Builtin Hashes", "cstratak-CentOS9-fips-x86_64", CentOS9NoBuiltinHashesUnixBuild, UNSTABLE, NO_TIER),
        # Linux PPC64le
        ("PPC64LE Fedora Rawhide", "cstratak-fedora-rawhide-ppc64le", FedoraRawhideBuild, UNSTABLE, NO_TIER),
        ("PPC64LE Fedora Rawhide Refleaks", "cstratak-fedora-rawhide-ppc64le", UnixRefleakBuild, UNSTABLE, NO_TIER),
        ("PPC64LE Fedora Rawhide Clang", "cstratak-fedora-rawhide-ppc64le", ClangUnixBuild, UNSTABLE, NO_TIER),
        ("PPC64LE Fedora Rawhide Clang Installed", "cstratak-fedora-rawhide-ppc64le", ClangUnixInstalledBuild, UNSTABLE, NO_TIER),
        ("PPC64LE Fedora Rawhide LTO", "cstratak-fedora-rawhide-ppc64le", LTONonDebugUnixBuild, UNSTABLE, NO_TIER),
        ("PPC64LE Fedora Rawhide LTO + PGO", "cstratak-fedora-rawhide-ppc64le", LTOPGONonDebugBuild, UNSTABLE, NO_TIER),
        ("PPC64LE CentOS9", "cstratak-CentOS9-ppc64le", CentOS9Build, UNSTABLE, NO_TIER),
        ("PPC64LE CentOS9 Refleaks", "cstratak-CentOS9-ppc64le", UnixRefleakBuild, UNSTABLE, NO_TIER),
        ("PPC64LE CentOS9 LTO", "cstratak-CentOS9-ppc64le", LTONonDebugUnixBuild, UNSTABLE, NO_TIER),
        ("PPC64LE CentOS9 LTO + PGO", "cstratak-CentOS9-ppc64le", LTOPGONonDebugBuild, UNSTABLE, NO_TIER),
        # Linux aarch32
        ("ARM Raspbian", "gps-raspbian", SlowNonDebugUnixBuild, UNSTABLE, TIER_3),
        # Linux aarch64
        ("aarch64 Fedora Rawhide", "cstratak-fedora-rawhide-aarch64", FedoraRawhideBuild, UNSTABLE, NO_TIER),
        ("aarch64 Fedora Rawhide Refleaks", "cstratak-fedora-rawhide-aarch64", UnixRefleakBuild, UNSTABLE, NO_TIER),
        ("aarch64 Fedora Rawhide Clang", "cstratak-fedora-rawhide-aarch64", ClangUnixBuild, UNSTABLE, NO_TIER),
        ("aarch64 Fedora Rawhide Clang Installed", "cstratak-fedora-rawhide-aarch64", ClangUnixInstalledBuild, UNSTABLE, NO_TIER),
        ("aarch64 Fedora Rawhide LTO", "cstratak-fedora-rawhide-aarch64", LTONonDebugUnixBuild, UNSTABLE, NO_TIER),
        ("aarch64 Fedora Rawhide LTO + PGO", "cstratak-fedora-rawhide-aarch64", LTOPGONonDebugBuild, UNSTABLE, NO_TIER),

        ("aarch64 CentOS9 Refleaks", "cstratak-CentOS9-aarch64", UnixRefleakBuild, UNSTABLE, NO_TIER),
        ("aarch64 CentOS9 LTO", "cstratak-CentOS9-aarch64", LTONonDebugUnixBuild, UNSTABLE, NO_TIER),
        ("aarch64 CentOS9 LTO + PGO", "cstratak-CentOS9-aarch64", LTOPGONonDebugBuild, UNSTABLE, NO_TIER),

        # Linux other archs
        ("s390x Fedora Rawhide", "edelsohn-fedora-rawhide-z", UnixBuild, UNSTABLE, NO_TIER),
        ("s390x Fedora Rawhide Refleaks", "edelsohn-fedora-rawhide-z", UnixRefleakBuild, UNSTABLE, NO_TIER),
        ("s390x Fedora Rawhide Clang", "edelsohn-fedora-rawhide-z", ClangUnixBuild, UNSTABLE, NO_TIER),
        ("s390x Fedora Rawhide Clang Installed", "edelsohn-fedora-rawhide-z", ClangUnixInstalledBuild, UNSTABLE, NO_TIER),
        ("s390x Fedora Rawhide LTO", "edelsohn-fedora-rawhide-z", LTONonDebugUnixBuild, UNSTABLE, NO_TIER),
        ("s390x Fedora Rawhide LTO + PGO", "edelsohn-fedora-rawhide-z", LTOPGONonDebugBuild, UNSTABLE, NO_TIER),

        # macOS
        # Other Unix
        ("AMD64 Cygwin64 on Windows 10", "bray-win10-cygwin-amd64", UnixBuild, UNSTABLE, NO_TIER),
        ("PPC64 AIX", "edelsohn-aix-ppc64", AIXBuild, UNSTABLE, NO_TIER),
        ("PPC64 AIX XLC", "edelsohn-aix-ppc64", AIXBuildWithXLC, UNSTABLE, NO_TIER),
        ("SPARCv9 Oracle Solaris 11.4", "kulikjak-solaris-sparcv9", UnixBuild, UNSTABLE, NO_TIER),

        # Windows/arm64
        ("ARM64 Windows", "linaro-win-arm64", WindowsARM64Build, STABLE, TIER_3),
        ("ARM64 Windows Non-Debug", "linaro-win-arm64", WindowsARM64ReleaseBuild, STABLE, NO_TIER),
        ("ARM64 Windows Azure", "linaro2-win-arm64", WindowsARM64Build, UNSTABLE, NO_TIER),
        ("ARM64 Windows Non-Debug Azure", "linaro2-win-arm64", WindowsARM64ReleaseBuild, UNSTABLE, NO_TIER),

        # WebAssembly
        ("wasm32-emscripten node (threaded)", "bcannon-wasm", Wasm32EmscriptenNodeBuild, UNSTABLE, NO_TIER),
        ("wasm32-emscripten browser (dynamic linking)", "bcannon-wasm", Wasm32EmscriptenBrowserBuild, UNSTABLE, NO_TIER),
        ("wasm32-wasi", "bcannon-wasm", Wasm32WASIBuild, UNSTABLE, NO_TIER),
    ]


DAILYBUILDERS = [
    "AMD64 Windows11 Refleaks",
    "AMD64 Fedora Rawhide Refleaks",
    "AMD64 Fedora Stable Refleaks",
    "AMD64 RHEL7 Refleaks",
    "AMD64 RHEL8 Refleaks",
    "AMD64 CentOS9 Refleaks",
    # Linux PPC64LE
    "PPC64LE Fedora Rawhide Refleaks",
    "PPC64LE Fedora Stable Refleaks",
    "PPC64LE RHEL7 Refleaks",
    "PPC64LE RHEL8 Refleaks",
    "PPC64LE CentOS9 Refleaks",
    # Linux s390x
    "s390x Fedora Rawhide Refleaks",
    "s390x Fedora Refleaks",
    "s390x RHEL7 Refleaks",
    "s390x RHEL8 Refleaks",
    # Linux aarch64
    "aarch64 Fedora Rawhide Refleaks",
    "aarch64 Fedora Stable Refleaks",
    "aarch64 RHEL8 Refleaks",
    "aarch64 CentOS9 Refleaks",
]

# Match builder name (excluding the branch name) of builders that should only
# run on the master and "custom" branches.
ONLY_MASTER_BRANCH = (
    "Alpine Linux",
    # Cygwin is not supported on 2.7, 3.6, 3.7
    "Cygwin",
    "ARM64 Windows"
)
