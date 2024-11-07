from custom.factories import (
    UnixBuild,
    UnixPerfBuild,
    RHEL8Build,
    CentOS9Build,
    FedoraStableBuild,
    FedoraRawhideBuild,
    FedoraRawhideFreedthreadingBuild,
    UnixAsanBuild,
    UnixAsanDebugBuild,
    UnixBigmemBuild,
    UnixTraceRefsBuild,
    UnixVintageParserBuild,
    UnixRefleakBuild,
    UnixNoGilBuild,
    UnixNoGilRefleakBuild,
    MacOSAsanNoGilBuild,
    AIXBuild,
    AIXBuildWithXLC,
    ClangUnixBuild,
    ClangUbsanLinuxBuild,
    ClangUbsanFunctionLinuxBuild,
    ClangUnixInstalledBuild,
    SharedUnixBuild,
    SlowNonDebugUnixBuild,
    SlowUnixInstalledBuild,
    NonDebugUnixBuild,
    UnixInstalledBuild,
    LTONonDebugUnixBuild,
    LTOPGONonDebugBuild,
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
    MacOSArmWithBrewNoGilBuild,
    MacOSArmWithBrewNoGilRefleakBuild,
    WindowsARM64Build,
    WindowsARM64ReleaseBuild,
    Wasm32WasiCrossBuild,
    Wasm32WasiPreview1DebugBuild,
    IOSARM64SimulatorBuild,
    AndroidBuild,
    ValgrindBuild,
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
    ("AMD64 Ubuntu Shared", "bolen-ubuntu", SharedUnixBuild),
    ("AMD64 Fedora Stable", "cstratak-fedora-stable-x86_64", FedoraStableBuild),
    ("AMD64 Fedora Stable Refleaks", "cstratak-fedora-stable-x86_64", UnixRefleakBuild),
    ("AMD64 Fedora Stable LTO", "cstratak-fedora-stable-x86_64", LTONonDebugUnixBuild),
    ("AMD64 Fedora Stable LTO + PGO", "cstratak-fedora-stable-x86_64", LTOPGONonDebugBuild),
    ("AMD64 RHEL8", "cstratak-RHEL8-x86_64", RHEL8Build),
    ("AMD64 RHEL8 Refleaks", "cstratak-RHEL8-x86_64", UnixRefleakBuild),
    ("AMD64 RHEL8 LTO", "cstratak-RHEL8-x86_64", LTONonDebugUnixBuild),
    ("AMD64 RHEL8 LTO + PGO", "cstratak-RHEL8-x86_64", LTOPGONonDebugBuild),
    ("AMD64 CentOS9 NoGIL", "itamaro-centos-aws", UnixNoGilBuild),
    ("AMD64 CentOS9 NoGIL Refleaks", "itamaro-centos-aws", UnixNoGilRefleakBuild),

    # Windows x86-64 MSVC
    ("AMD64 Windows10", "bolen-windows10", Windows64Build),
    ("AMD64 Windows11 Bigmem", "ambv-bb-win11", Windows64BigmemBuild),
    ("AMD64 Windows11 Non-Debug", "ware-win11", Windows64ReleaseBuild),
    ("AMD64 Windows11 Refleaks", "ware-win11", Windows64RefleakBuild),
    ("AMD64 Windows Server 2022 NoGIL", "itamaro-win64-srv-22-aws", Windows64NoGilBuild),

    # macOS x86-64 clang
    ("x86-64 macOS", "billenstein-macos", UnixBuild),
    ("x86-64 MacOS Intel NoGIL", "itamaro-macos-intel-aws", UnixNoGilBuild),
    ("x86-64 MacOS Intel ASAN NoGIL", "itamaro-macos-intel-aws", MacOSAsanNoGilBuild),
]


# -- Stable Tier-2 builder ----------------------------------------------
STABLE_BUILDERS_TIER_2 = [
    # Linux x86-64 Clang
    ("AMD64 Fedora Stable Clang", "cstratak-fedora-stable-x86_64", ClangUnixBuild),
    ("AMD64 Fedora Stable Clang Installed", "cstratak-fedora-stable-x86_64", ClangUnixInstalledBuild),

    # Linux ppc64le GCC
    ("PPC64LE Fedora Stable", "cstratak-fedora-stable-ppc64le", FedoraStableBuild),
    ("PPC64LE Fedora Stable Refleaks", "cstratak-fedora-stable-ppc64le", UnixRefleakBuild),
    ("PPC64LE Fedora Stable LTO", "cstratak-fedora-stable-ppc64le", LTONonDebugUnixBuild),
    ("PPC64LE Fedora Stable LTO + PGO", "cstratak-fedora-stable-ppc64le", LTOPGONonDebugBuild),

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

    # macOS aarch64 clang
    ("ARM64 macOS", "pablogsal-macos-m1", MacOSArmWithBrewBuild),
    ("ARM64 MacOS M1 NoGIL", "itamaro-macos-arm64-aws", MacOSArmWithBrewNoGilBuild),
    ("ARM64 MacOS M1 Refleaks NoGIL", "itamaro-macos-arm64-aws", MacOSArmWithBrewNoGilRefleakBuild),

    # WASI
    ("wasm32-wasi Non-Debug", "bcannon-wasi", Wasm32WasiCrossBuild),
    ("wasm32-wasi", "bcannon-wasi", Wasm32WasiPreview1DebugBuild),
]


# -- Stable Tier-3 builder ----------------------------------------------
STABLE_BUILDERS_TIER_3 = [

    # Linux s390x GCC
    ("s390x RHEL9", "cstratak-rhel9-s390x", UnixBuild),
    ("s390x RHEL9 Refleaks", "cstratak-rhel9-s390x", UnixRefleakBuild),
    ("s390x RHEL9 LTO", "cstratak-rhel9-s390x", LTONonDebugUnixBuild),
    ("s390x RHEL9 LTO + PGO", "cstratak-rhel9-s390x", LTOPGONonDebugBuild),
    ("s390x RHEL8", "cstratak-rhel8-s390x", UnixBuild),
    ("s390x RHEL8 Refleaks", "cstratak-rhel8-s390x", UnixRefleakBuild),
    ("s390x RHEL8 LTO", "cstratak-rhel8-s390x", LTONonDebugUnixBuild),
    ("s390x RHEL8 LTO + PGO", "cstratak-rhel8-s390x", LTOPGONonDebugBuild),

    # Linux ppc64le Clang
    ("PPC64LE Fedora Stable Clang", "cstratak-fedora-stable-ppc64le", ClangUnixBuild),
    ("PPC64LE Fedora Stable Clang Installed", "cstratak-fedora-stable-ppc64le", ClangUnixInstalledBuild),

    # Linux armv7l (32-bit) GCC
    ("ARM Raspbian", "gps-raspbian", SlowNonDebugUnixBuild),

    # FreBSD x86-64 clang
    ("AMD64 FreeBSD", "ware-freebsd", UnixBuild),
    ("AMD64 FreeBSD Refleaks", "ware-freebsd", UnixRefleakBuild),
    ("AMD64 FreeBSD14", "opsec-fbsd14", UnixBuild),

    # Windows aarch64 MSVC
    ("ARM64 Windows", "linaro-win-arm64", WindowsARM64Build),
    ("ARM64 Windows Non-Debug", "linaro-win-arm64", WindowsARM64ReleaseBuild),

    # iOS
    ("iOS ARM64 Simulator", "rkm-arm64-ios-simulator", IOSARM64SimulatorBuild),

    # Android
    ("aarch64 Android", "mhsmith-android-aarch64", AndroidBuild),
    ("AMD64 Android", "mhsmith-android-x86_64", AndroidBuild),
]


# -- Stable No Tier builders --------------------------------------------
STABLE_BUILDERS_NO_TIER = [
    # Linux x86-64 GCC/Clang
    # Special builds: FIPS, ASAN, UBSAN, TraceRefs, Perf, etc.
    ("AMD64 RHEL8 FIPS Only Blake2 Builtin Hash", "cstratak-RHEL8-fips-x86_64", RHEL8NoBuiltinHashesUnixBuildExceptBlake2),
    ("AMD64 Arch Linux Asan", "pablogsal-arch-x86_64", UnixAsanBuild),
    ("AMD64 Arch Linux Asan Debug", "pablogsal-arch-x86_64", UnixAsanDebugBuild),
    ("AMD64 Arch Linux TraceRefs", "pablogsal-arch-x86_64", UnixTraceRefsBuild),
    ("AMD64 Arch Linux Perf", "pablogsal-arch-x86_64", UnixPerfBuild),
    # UBSAN with -fno-sanitize=function, without which we currently fail (as
    #  tracked in gh-111178). The full "AMD64 Arch Linux Usan" is unstable, below
    ("AMD64 Arch Linux Usan Function", "pablogsal-arch-x86_64", ClangUbsanFunctionLinuxBuild),

    # Linux x86 (32-bit) GCC
    ("x86 Debian Non-Debug with X", "ware-debian-x86", NonDebugUnixBuild),
    ("x86 Debian Installed with X", "ware-debian-x86", UnixInstalledBuild),
]


# -- Unstable Tier-1 builders -------------------------------------------
UNSTABLE_BUILDERS_TIER_1 = [
    # Linux x86-64 GCC
    # Fedora Rawhide is unstable
    ("AMD64 Fedora Rawhide", "cstratak-fedora-rawhide-x86_64", FedoraRawhideBuild),
    ("AMD64 Fedora Rawhide Refleaks", "cstratak-fedora-rawhide-x86_64", UnixRefleakBuild),
    ("AMD64 Fedora Rawhide LTO", "cstratak-fedora-rawhide-x86_64", LTONonDebugUnixBuild),
    ("AMD64 Fedora Rawhide LTO + PGO", "cstratak-fedora-rawhide-x86_64", LTOPGONonDebugBuild),

    ("AMD64 Ubuntu", "skumaran-ubuntu-x86_64", UnixBuild),

    ("AMD64 Arch Linux VintageParser", "pablogsal-arch-x86_64", UnixVintageParserBuild),

    ("AMD64 RHEL8 FIPS No Builtin Hashes", "cstratak-RHEL8-fips-x86_64", RHEL8NoBuiltinHashesUnixBuild),

    ("AMD64 CentOS9", "cstratak-CentOS9-x86_64", CentOS9Build),
    ("AMD64 CentOS9 Refleaks", "cstratak-CentOS9-x86_64", UnixRefleakBuild),
    ("AMD64 CentOS9 LTO", "cstratak-CentOS9-x86_64", LTONonDebugUnixBuild),
    ("AMD64 CentOS9 LTO + PGO", "cstratak-CentOS9-x86_64", LTOPGONonDebugBuild),
    ("AMD64 CentOS9 FIPS Only Blake2 Builtin Hash", "cstratak-CentOS9-fips-x86_64", CentOS9NoBuiltinHashesUnixBuildExceptBlake2),
    ("AMD64 CentOS9 FIPS No Builtin Hashes", "cstratak-CentOS9-fips-x86_64", CentOS9NoBuiltinHashesUnixBuild),

    ("AMD64 Arch Linux Valgrind", "pablogsal-arch-x86_64", ValgrindBuild),
]


# -- Unstable Tier-2 builders -------------------------------------------
UNSTABLE_BUILDERS_TIER_2 = [
    # Linux x86-64 Clang
    # Fedora Rawhide is unstable
    # UBSan is a special build
    ("AMD64 Fedora Rawhide Clang", "cstratak-fedora-rawhide-x86_64", ClangUnixBuild),
    ("AMD64 Fedora Rawhide Clang Installed", "cstratak-fedora-rawhide-x86_64", ClangUnixInstalledBuild),

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
    ("aarch64 Ubuntu 22.04 BigMem", "diegorusso-aarch64-bigmem", UnixBigmemBuild),

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

    # WebAssembly
    ("wasm32 WASI 8Core", "kushaldas-wasi", Wasm32WasiCrossBuild),
]


# -- Unstable Tier-3 builders -------------------------------------------
UNSTABLE_BUILDERS_TIER_3 = [
    # Linux ppc64le Clang
    # Fedora Rawhide is unstable
    ("PPC64LE Fedora Rawhide Clang", "cstratak-fedora-rawhide-ppc64le", ClangUnixBuild),
    ("PPC64LE Fedora Rawhide Clang Installed", "cstratak-fedora-rawhide-ppc64le", ClangUnixInstalledBuild),

    # FreBSD x86-64 clang
    # FreeBSD 15 is CURRENT: development branch (at 2023-10-17)
    ("AMD64 FreeBSD15", "opsec-fbsd15", UnixBuild),
]


# -- Unstable No Tier builders ------------------------------------------
UNSTABLE_BUILDERS_NO_TIER = [
    # Linux x86-64 GCC musl
    ("AMD64 Alpine Linux", "ware-alpine", UnixBuild),

    # Linux x86-64 GCC Fedora Rawhide Freethreading builders
    ("AMD64 Fedora Rawhide NoGIL", "cstratak-fedora-rawhide-x86_64", FedoraRawhideFreedthreadingBuild),
    ("aarch64 Fedora Rawhide NoGIL", "cstratak-fedora-rawhide-aarch64", FedoraRawhideFreedthreadingBuild),
    ("PPC64LE Fedora Rawhide NoGIL", "cstratak-fedora-rawhide-ppc64le", FedoraRawhideFreedthreadingBuild),
    # Linux x86-64 GCC Fedora Rawhide Freethreading refleak builders
    ("AMD64 Fedora Rawhide NoGIL refleaks", "cstratak-fedora-rawhide-x86_64", UnixNoGilRefleakBuild),
    ("aarch64 Fedora Rawhide NoGIL refleaks", "cstratak-fedora-rawhide-aarch64", UnixNoGilRefleakBuild),
    ("PPC64LE Fedora Rawhide NoGIL refleaks", "cstratak-fedora-rawhide-ppc64le", UnixNoGilRefleakBuild),

    # AIX ppc64
    ("PPC64 AIX", "edelsohn-aix-ppc64", AIXBuild),
    ("PPC64 AIX XLC", "edelsohn-aix-ppc64", AIXBuildWithXLC),

    # Solaris sparcv9
    ("SPARCv9 Oracle Solaris 11.4", "kulikjak-solaris-sparcv9", UnixBuild),

    # riscv64 GCC
    ("riscv64 Ubuntu23", "onder-riscv64", SlowUnixInstalledBuild),

    # Arch Usan (see stable "AMD64 Arch Linux Usan Function" above)
    ("AMD64 Arch Linux Usan", "pablogsal-arch-x86_64", ClangUbsanLinuxBuild),
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


# Match builder name (excluding the branch name) of builders that should only
# run on the main and "custom" branches.
ONLY_MAIN_BRANCH = (
    "Alpine Linux",
    # Cygwin is not supported on 2.7, 3.6, 3.7
    "Cygwin",
    "ARM64 Windows",
    "AMD64 Arch Linux Perf",
    "AMD64 Arch Linux Valgrind",
)
