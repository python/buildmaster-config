from custom.factories import (
    UnixBuild,
    UnixPerfBuild,
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
    UnixNoGilBuild,
    UnixNoGilRefleakBuild,
    AIXBuild,
    AIXBuildWithXLC,
    PGOUnixBuild,
    ClangUnixBuild,
    ClangUbsanLinuxBuild,
    ClangUnixInstalledBuild,
    SharedUnixBuild,
    SlowNonDebugUnixBuild,
    NonDebugUnixBuild,
    UnixInstalledBuild,
    LTONonDebugUnixBuild,
    LTOPGONonDebugBuild,
    ClangLTOPGONonDebugBuild,
    RHEL8NoBuiltinHashesUnixBuild,
    RHEL8NoBuiltinHashesUnixBuildExceptBlake2,
    CentOS9NoBuiltinHashesUnixBuild,
    CentOS9NoBuiltinHashesUnixBuildExceptBlake2,
    Windows64Build,
    Windows64BigmemBuild,
    Windows64NoGilBuild,
    Windows64RefleakBuild,
    Windows64ReleaseBuild,
    MacOSArmWithBrewBuild,
    WindowsARM64Build,
    WindowsARM64ReleaseBuild,
    Wasm32EmscriptenNodePThreadsBuild,
    Wasm32EmscriptenNodeDLBuild,
    Wasm32EmscriptenBrowserBuild,
    Wasm32WASIBuild,
)

# A builder can be marked as stable when at least the 10 latest builds are
# successful, but it's way better to wait at least for at least one week of
# successful builds before considering to mark a builder as stable.
STABLE = "stable"

# New builders should always be marked as unstable. If a stable builder starts
# to fail randomly, it can be downgraded to unstable if it is not a Tier-1 or
# Tier-2 builder.
UNSTABLE = "unstable"

# https://peps.python.org/pep-0011/ defines Platfom Support Tiers
TIER_1 = "tier-1"
TIER_2 = "tier-2"
TIER_3 = "tier-3"
NO_TIER = None


# -- Stable Tier-1 builder ----------------------------------------------
STABLE_BUILDERS_TIER_1 = [
    # Linux x86-64 GCC
    ("AMD64 Debian root", "angelico-debian-amd64", UnixBuild),
    ("AMD64 Debian PGO", "gps-debian-profile-opt", PGOUnixBuild),
    ("AMD64 Ubuntu Shared", "bolen-ubuntu", SharedUnixBuild),
    ("AMD64 Fedora Stable", "cstratak-fedora-stable-x86_64", FedoraStableBuild),
    ("AMD64 Fedora Stable Refleaks", "cstratak-fedora-stable-x86_64", UnixRefleakBuild),
    ("AMD64 Fedora Stable LTO", "cstratak-fedora-stable-x86_64", LTONonDebugUnixBuild),
    ("AMD64 Fedora Stable LTO + PGO", "cstratak-fedora-stable-x86_64", LTOPGONonDebugBuild),
    ("AMD64 RHEL7", "cstratak-RHEL7-x86_64", RHEL7Build),
    ("AMD64 RHEL7 Refleaks", "cstratak-RHEL7-x86_64", UnixRefleakBuild),
    ("AMD64 RHEL7 LTO", "cstratak-RHEL7-x86_64", LTONonDebugUnixBuild),
    ("AMD64 RHEL7 LTO + PGO", "cstratak-RHEL7-x86_64", LTOPGONonDebugBuild),
    ("AMD64 RHEL8", "cstratak-RHEL8-x86_64", RHEL8Build),
    ("AMD64 RHEL8 Refleaks", "cstratak-RHEL8-x86_64", UnixRefleakBuild),
    ("AMD64 RHEL8 LTO", "cstratak-RHEL8-x86_64", LTONonDebugUnixBuild),
    ("AMD64 RHEL8 LTO + PGO", "cstratak-RHEL8-x86_64", LTOPGONonDebugBuild),

    # Windows x86-64 MSVC
    ("AMD64 Windows10", "bolen-windows10", Windows64Build),
    ("AMD64 Windows11 Bigmem", "ambv-bb-win11", Windows64BigmemBuild),
    ("AMD64 Windows11 Non-Debug", "ware-win11", Windows64ReleaseBuild),
    ("AMD64 Windows11 Refleaks", "ware-win11", Windows64RefleakBuild),

    # macOS x86-64 clang
    ("x86-64 macOS", "billenstein-macos", UnixBuild),
]


# -- Stable Tier-2 builder ----------------------------------------------
STABLE_BUILDERS_TIER_2 = [
    # Linux x86-64 Clang
    ("AMD64 Fedora Stable Clang", "cstratak-fedora-stable-x86_64", ClangUnixBuild),
    ("AMD64 Fedora Stable Clang Installed", "cstratak-fedora-stable-x86_64", ClangUnixInstalledBuild),

    # Linux ppc64le GCC
    ("PPC64 Fedora", "edelsohn-fedora-ppc64", FedoraStableBuild),

    ("PPC64LE Fedora Stable", "cstratak-fedora-stable-ppc64le", FedoraStableBuild),
    ("PPC64LE Fedora Stable Refleaks", "cstratak-fedora-stable-ppc64le", UnixRefleakBuild),
    ("PPC64LE Fedora Stable LTO", "cstratak-fedora-stable-ppc64le", LTONonDebugUnixBuild),
    ("PPC64LE Fedora Stable LTO + PGO", "cstratak-fedora-stable-ppc64le", LTOPGONonDebugBuild),

    ("PPC64LE RHEL7", "cstratak-RHEL7-ppc64le", RHEL7Build),
    ("PPC64LE RHEL7 Refleaks", "cstratak-RHEL7-ppc64le", UnixRefleakBuild),
    ("PPC64LE RHEL7 LTO", "cstratak-RHEL7-ppc64le", LTONonDebugUnixBuild),
    ("PPC64LE RHEL7 LTO + PGO", "cstratak-RHEL7-ppc64le", LTOPGONonDebugBuild),

    ("PPC64LE RHEL8", "cstratak-RHEL8-ppc64le", RHEL8Build),
    ("PPC64LE RHEL8 Refleaks", "cstratak-RHEL8-ppc64le", UnixRefleakBuild),
    ("PPC64LE RHEL8 LTO", "cstratak-RHEL8-ppc64le", LTONonDebugUnixBuild),
    ("PPC64LE RHEL8 LTO + PGO", "cstratak-RHEL8-ppc64le", LTOPGONonDebugBuild),

    # Linux aarch64 GCC/clang
    ("aarch64 Fedora Stable", "cstratak-fedora-stable-aarch64", FedoraStableBuild),
    ("aarch64 Fedora Stable Refleaks", "cstratak-fedora-stable-aarch64", UnixRefleakBuild),
    ("aarch64 Fedora Stable Clang", "cstratak-fedora-stable-aarch64", ClangUnixBuild),
    ("aarch64 Fedora Stable Clang Installed", "cstratak-fedora-stable-aarch64", ClangUnixInstalledBuild),
    ("aarch64 Fedora Stable LTO", "cstratak-fedora-stable-aarch64", LTONonDebugUnixBuild),
    ("aarch64 Fedora Stable LTO + PGO", "cstratak-fedora-stable-aarch64", LTOPGONonDebugBuild),

    ("aarch64 RHEL8", "cstratak-RHEL8-aarch64", RHEL8Build),
    ("aarch64 RHEL8 Refleaks", "cstratak-RHEL8-aarch64", UnixRefleakBuild),
    ("aarch64 RHEL8 LTO", "cstratak-RHEL8-aarch64", LTONonDebugUnixBuild),
    ("aarch64 RHEL8 LTO + PGO", "cstratak-RHEL8-aarch64", LTOPGONonDebugBuild),

    ("aarch64 Debian Clang LTO + PGO", "gps-arm64-debian", ClangLTOPGONonDebugBuild),

    # macOS aarch64 clang
    ("ARM64 macOS", "pablogsal-macos-m1", MacOSArmWithBrewBuild),
]


# -- Stable Tier-3 builder ----------------------------------------------
STABLE_BUILDERS_TIER_3 = [
    # Linux s390x GCC
    ("s390x SLES", "edelsohn-sles-z", UnixBuild),
    ("s390x Debian", "edelsohn-debian-z", UnixBuild),
    ("s390x Fedora", "edelsohn-fedora-z", UnixBuild),
    ("s390x Fedora Refleaks", "edelsohn-fedora-z", UnixRefleakBuild),
    ("s390x Fedora LTO", "edelsohn-fedora-z", LTONonDebugUnixBuild),
    ("s390x Fedora LTO + PGO", "edelsohn-fedora-z", LTOPGONonDebugBuild),
    ("s390x RHEL7", "edelsohn-rhel-z", UnixBuild),
    ("s390x RHEL7 Refleaks", "edelsohn-rhel-z", UnixRefleakBuild),
    ("s390x RHEL7 LTO", "edelsohn-rhel-z", LTONonDebugUnixBuild),
    ("s390x RHEL7 LTO + PGO", "edelsohn-rhel-z", LTOPGONonDebugBuild),
    ("s390x RHEL8", "edelsohn-rhel8-z", UnixBuild),
    ("s390x RHEL8 Refleaks", "edelsohn-rhel8-z", UnixRefleakBuild),
    ("s390x RHEL8 LTO", "edelsohn-rhel8-z", LTONonDebugUnixBuild),
    ("s390x RHEL8 LTO + PGO", "edelsohn-rhel8-z", LTOPGONonDebugBuild),

    # Linux ppc64le Clang
    ("PPC64LE Fedora Stable Clang", "cstratak-fedora-stable-ppc64le", ClangUnixBuild),
    ("PPC64LE Fedora Stable Clang Installed", "cstratak-fedora-stable-ppc64le", ClangUnixInstalledBuild),

    # Linux armv7l (32-bit) GCC
    ("ARM Raspbian", "gps-raspbian", SlowNonDebugUnixBuild),

    # FreBSD x86-64 clang
    ("AMD64 FreeBSD", "ware-freebsd", UnixBuild),
    ("AMD64 FreeBSD14", "opsec-fbsd14", UnixBuild),

    # Windows aarch64 MSVC
    ("ARM64 Windows", "linaro-win-arm64", WindowsARM64Build),
    ("ARM64 Windows Non-Debug", "linaro-win-arm64", WindowsARM64ReleaseBuild),

    # WebAssembly
    ("wasm32-emscripten node (pthreads)", "bcannon-wasm", Wasm32EmscriptenNodePThreadsBuild),
    ("wasm32-emscripten node (dynamic linking)", "bcannon-wasm", Wasm32EmscriptenNodeDLBuild),
    ("wasm32-emscripten browser (dynamic linking, no tests)", "bcannon-wasm", Wasm32EmscriptenBrowserBuild),
    ("wasm32-wasi", "bcannon-wasm", Wasm32WASIBuild),
]


# -- Stable No Tier builders --------------------------------------------
STABLE_BUILDERS_NO_TIER = [
    # Linux x86-64 GCC/Clang
    # Special builds: FIPS, ASAN, UBSAN, TraceRefs, Perf, etc.
    ("AMD64 RHEL8 FIPS Only Blake2 Builtin Hash", "cstratak-RHEL8-fips-x86_64", RHEL8NoBuiltinHashesUnixBuildExceptBlake2),
    ("AMD64 Arch Linux Asan", "pablogsal-arch-x86_64", UnixAsanBuild),
    ("AMD64 Arch Linux Usan", "pablogsal-arch-x86_64", ClangUbsanLinuxBuild),
    ("AMD64 Arch Linux Asan Debug", "pablogsal-arch-x86_64", UnixAsanDebugBuild),
    ("AMD64 Arch Linux TraceRefs", "pablogsal-arch-x86_64", UnixTraceRefsBuild),
    ("AMD64 Arch Linux Perf", "pablogsal-arch-x86_64", UnixPerfBuild),

    # Linux s390x Clang
    ("s390x Fedora Clang", "edelsohn-fedora-z", ClangUnixBuild),
    ("s390x Fedora Clang Installed", "edelsohn-fedora-z", ClangUnixInstalledBuild),
]


# -- Unstable Tier-1 builders -------------------------------------------
UNSTABLE_BUILDERS_TIER_1 = [
    # Linux x86-64 GCC
    # Fedora Rawhide is unstable
    ("AMD64 Fedora Rawhide", "cstratak-fedora-rawhide-x86_64", FedoraRawhideBuild),
    ("AMD64 Fedora Rawhide Refleaks", "cstratak-fedora-rawhide-x86_64", UnixRefleakBuild),
    ("AMD64 Fedora Rawhide LTO", "cstratak-fedora-rawhide-x86_64", LTONonDebugUnixBuild),
    ("AMD64 Fedora Rawhide LTO + PGO", "cstratak-fedora-rawhide-x86_64", LTOPGONonDebugBuild),

    ("AMD64 Fedora NoGIL", "itamaro-fedora-x1", UnixNoGilBuild),
    ("AMD64 Ubuntu NoGIL", "itamaro-ubuntu-aws", UnixNoGilBuild),
    ("AMD64 Ubuntu NoGIL Refleaks", "itamaro-ubuntu-aws", UnixNoGilRefleakBuild),

    ("AMD64 Ubuntu", "skumaran-ubuntu-x86_64", UnixBuild),

    ("AMD64 Arch Linux VintageParser", "pablogsal-arch-x86_64", UnixVintageParserBuild),

    ("AMD64 RHEL8 FIPS No Builtin Hashes", "cstratak-RHEL8-fips-x86_64", RHEL8NoBuiltinHashesUnixBuild),

    ("AMD64 CentOS9", "cstratak-CentOS9-x86_64", CentOS9Build),
    ("AMD64 CentOS9 Refleaks", "cstratak-CentOS9-x86_64", UnixRefleakBuild),
    ("AMD64 CentOS9 LTO", "cstratak-CentOS9-x86_64", LTONonDebugUnixBuild),
    ("AMD64 CentOS9 LTO + PGO", "cstratak-CentOS9-x86_64", LTOPGONonDebugBuild),
    ("AMD64 CentOS9 FIPS Only Blake2 Builtin Hash", "cstratak-CentOS9-fips-x86_64", CentOS9NoBuiltinHashesUnixBuildExceptBlake2),
    ("AMD64 CentOS9 FIPS No Builtin Hashes", "cstratak-CentOS9-fips-x86_64", CentOS9NoBuiltinHashesUnixBuild),

    # MacOS
    ("x86-64 MacOS Intel NoGIL", "itamaro-macos-intel-aws", UnixNoGilBuild),

    # Windows x86-64 MSVC
    ("AMD64 Windows Server 2022 NoGIL", "itamaro-win64-srv-22-aws", Windows64NoGilBuild),
]


# -- Unstable Tier-2 builders -------------------------------------------
UNSTABLE_BUILDERS_TIER_2 = [
    # Linux x86-64 Clang
    # Fedora Rawhide is unstable
    # UBSan is a special build
    ("AMD64 Fedora Rawhide Clang", "cstratak-fedora-rawhide-x86_64", ClangUnixBuild),
    ("AMD64 Fedora Rawhide Clang Installed", "cstratak-fedora-rawhide-x86_64", ClangUnixInstalledBuild),
    ("AMD64 Clang UBSan", "gps-clang-ubsan", ClangUbsanLinuxBuild),

    # Linux ppc64le GCC
    # Fedora Rawhide is unstable
    ("PPC64LE Fedora Rawhide", "cstratak-fedora-rawhide-ppc64le", FedoraRawhideBuild),
    ("PPC64LE Fedora Rawhide Refleaks", "cstratak-fedora-rawhide-ppc64le", UnixRefleakBuild),
    ("PPC64LE Fedora Rawhide LTO", "cstratak-fedora-rawhide-ppc64le", LTONonDebugUnixBuild),
    ("PPC64LE Fedora Rawhide LTO + PGO", "cstratak-fedora-rawhide-ppc64le", LTOPGONonDebugBuild),

    ("PPC64LE CentOS9", "cstratak-CentOS9-ppc64le", CentOS9Build),
    ("PPC64LE CentOS9 Refleaks", "cstratak-CentOS9-ppc64le", UnixRefleakBuild),
    ("PPC64LE CentOS9 LTO", "cstratak-CentOS9-ppc64le", LTONonDebugUnixBuild),
    ("PPC64LE CentOS9 LTO + PGO", "cstratak-CentOS9-ppc64le", LTOPGONonDebugBuild),

    # Linux aarch64 GCC/Clang
    # Fedora Rawhide is unstable
    ("aarch64 Fedora Rawhide", "cstratak-fedora-rawhide-aarch64", FedoraRawhideBuild),
    ("aarch64 Fedora Rawhide Refleaks", "cstratak-fedora-rawhide-aarch64", UnixRefleakBuild),
    ("aarch64 Fedora Rawhide Clang", "cstratak-fedora-rawhide-aarch64", ClangUnixBuild),
    ("aarch64 Fedora Rawhide Clang Installed", "cstratak-fedora-rawhide-aarch64", ClangUnixInstalledBuild),
    ("aarch64 Fedora Rawhide LTO", "cstratak-fedora-rawhide-aarch64", LTONonDebugUnixBuild),
    ("aarch64 Fedora Rawhide LTO + PGO", "cstratak-fedora-rawhide-aarch64", LTOPGONonDebugBuild),

    ("aarch64 CentOS9 Refleaks", "cstratak-CentOS9-aarch64", UnixRefleakBuild),
    ("aarch64 CentOS9 LTO", "cstratak-CentOS9-aarch64", LTONonDebugUnixBuild),
    ("aarch64 CentOS9 LTO + PGO", "cstratak-CentOS9-aarch64", LTOPGONonDebugBuild),
]


# -- Unstable Tier-3 builders -------------------------------------------
UNSTABLE_BUILDERS_TIER_3 = [
    # Linux ppc64le Clang
    # Fedora Rawhide is unstable
    ("PPC64LE Fedora Rawhide Clang", "cstratak-fedora-rawhide-ppc64le", ClangUnixBuild),
    ("PPC64LE Fedora Rawhide Clang Installed", "cstratak-fedora-rawhide-ppc64le", ClangUnixInstalledBuild),

    # Linux s390x GCC
    # Fedora Rawhide is unstable
    ("s390x Fedora Rawhide", "edelsohn-fedora-rawhide-z", UnixBuild),
    ("s390x Fedora Rawhide Refleaks", "edelsohn-fedora-rawhide-z", UnixRefleakBuild),
    ("s390x Fedora Rawhide LTO", "edelsohn-fedora-rawhide-z", LTONonDebugUnixBuild),
    ("s390x Fedora Rawhide LTO + PGO", "edelsohn-fedora-rawhide-z", LTOPGONonDebugBuild),

    # FreBSD x86-64 clang
    # FreeBSD 15 is CURRENT: development branch (at 2023-10-17)
    ("AMD64 FreeBSD15", "opsec-fbsd15", UnixBuild),
]


# -- Unstable No Tier builders ------------------------------------------
UNSTABLE_BUILDERS_NO_TIER = [
    # Linux x86-64 GCC musl
    ("AMD64 Alpine Linux", "ware-alpine", UnixBuild),

    # Linux x86 (32-bit) GCC
    ("x86 Debian Non-Debug with X", "ware-debian-x86", NonDebugUnixBuild),
    ("x86 Debian Installed with X", "ware-debian-x86", UnixInstalledBuild),

    # Linux s390x Clang
    ("s390x Fedora Rawhide Clang", "edelsohn-fedora-rawhide-z", ClangUnixBuild),
    ("s390x Fedora Rawhide Clang Installed", "edelsohn-fedora-rawhide-z", ClangUnixInstalledBuild),

    # AIX ppc64
    ("PPC64 AIX", "edelsohn-aix-ppc64", AIXBuild),
    ("PPC64 AIX XLC", "edelsohn-aix-ppc64", AIXBuildWithXLC),

    # Solaris sparcv9
    ("SPARCv9 Oracle Solaris 11.4", "kulikjak-solaris-sparcv9", UnixBuild),
]


def get_builders(settings):
    # Override with a default simple worker if we are using local workers
    if settings.use_local_worker:
        return [("Test Builder", "local-worker", UnixBuild, STABLE, NO_TIER)]

    all_builders = []
    for builders, stability, tier in (
        (STABLE_BUILDERS_TIER_1, STABLE, TIER_1),
        (STABLE_BUILDERS_TIER_2, STABLE, TIER_2),
        (STABLE_BUILDERS_TIER_3, STABLE, TIER_3),
        (STABLE_BUILDERS_NO_TIER, STABLE, NO_TIER),

        (UNSTABLE_BUILDERS_TIER_1, UNSTABLE, TIER_1),
        (UNSTABLE_BUILDERS_TIER_2, UNSTABLE, TIER_2),
        (UNSTABLE_BUILDERS_TIER_3, UNSTABLE, TIER_3),
        (UNSTABLE_BUILDERS_NO_TIER, UNSTABLE, NO_TIER),
    ):
        for name, worker_name, buildfactory in builders:
            all_builders.append((name, worker_name, buildfactory, stability, tier))
    return all_builders


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
ONLY_MAIN_BRANCH = (
    "Alpine Linux",
    # Cygwin is not supported on 2.7, 3.6, 3.7
    "Cygwin",
    "ARM64 Windows",
    "AMD64 Arch Linux Perf",
)
