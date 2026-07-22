import os
import sys
from dataclasses import dataclass
from functools import cached_property

from custom import factories
from custom.factories import (
    UnixBuild,
    UnixPerfBuild,
    RHEL8Build,
    CentOS9Build,
    CentOS10Build,
    FedoraStableBuild,
    FedoraRawhideBuild,
    FedoraRawhideFreedthreadingBuild,
    UnixAsanBuild,
    UnixAsanDebugBuild,
    UnixBigmemBuild,
    UnixTraceRefsBuild,
    UnixRefleakBuild,
    UnixNoGilBuild,
    UnixNoGilRefleakBuild,
    MacOSAsanNoGilBuild,
    ClangUnixBuild,
    ClangUbsanLinuxBuild,
    ClangUbsanFunctionLinuxBuild,
    ClangUnixInstalledBuild,
    SharedUnixBuild,
    SlowDebugUnixBuild,
    SlowUnixNoGilBuild,
    SlowNonDebugUnixBuild,
    SlowNonDebugUnixBuild15BitDigits,
    SlowUnixInstalledBuild,
    SlowClangUnixBuild,
    NonDebugUnixBuild,
    UnixInstalledBuild,
    LTONonDebugUnixBuild,
    LTOPGONonDebugBuild,
    RHEL8NoBuiltinHashesUnixBuild,
    RHEL8NoBuiltinHashesUnixBuildExceptBlake2,
    CentOS9NoBuiltinHashesUnixBuild,
    CentOS9NoBuiltinHashesUnixBuildExceptBlake2,
    Windows64Build,
    Windows64ClangBuild,
    Windows64NoGilBuild,
    Windows64PGOBuild,
    Windows64PGOTailcallBuild,
    Windows64PGONoGilBuild,
    Windows64PGONoGilTailcallBuild,
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
    EmscriptenBuild,
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

# https://peps.python.org/pep-0011/ defines Platform Support Tiers
TIER_1 = "tier-1"
TIER_2 = "tier-2"
TIER_3 = "tier-3"

# linguistic hack: this sorts after 'tier-#' alphabetically
NO_TIER = "tierless"


@dataclass
class BuilderDef:
    """Definition for a builder.

    master.cfg turns this definition into several builders (one per branch).
    """
    name: str
    factory: factories.BaseBuild
    tags: frozenset[str]
    worker_name: str

    def __init__(self, name, factory, *, tags, worker_name):
        self.name = name
        self.factory = factory
        self.worker_name = worker_name
        self.tags = frozenset(tags)

    @cached_property
    def tier(self):
        return get_tier_from_tags(self.tags)

    @cached_property
    def stability(self):
        if STABLE in self.tags:
            return STABLE
        return UNSTABLE

def get_tier_from_tags(tags):
    # Get the first (highest) of the tier flags
    tags = sorted(tags & {TIER_1, TIER_2, TIER_3})
    if tags:
        return tags[0]
    return NO_TIER


# -- Dataclass-based builders -------------------------------------------

# For now, most builders are defined in "generate_builderdefs" calls below,
# grouped by stability and tier.
# Feel free to convert them to a `BuilderDef` call and move them here when
# updating them (e.g. changing stability)

BUILDER_DEFS = [
    # Tests that require the 'tzdata' and 'xpickle' resources
    BuilderDef(
        "aarch64 Ubuntu Oddballs",
        factories.UnixOddballsBuild,
        tags={STABLE, TIER_1},
        worker_name="stan-aarch64-ubuntu",
    ),
    BuilderDef(
        "AMD64 Windows Server 2025 Clang",
        factories.Windows64ClangBuild,
        tags={UNSTABLE, NO_TIER},
        worker_name="ware-ws2025",
    ),
    BuilderDef(
        "AMD64 Windows Server 2025 Refleaks",
        factories.Windows64RefleakBuild,
        tags={UNSTABLE, TIER_1},
        worker_name="ware-ws2025",
    ),
    BuilderDef(
        "AMD64 Windows PGO",
        factories.Windows64PGOBuild,
        tags={STABLE, TIER_1},
        worker_name="bolen-windows10",
    ),
]

def generate_builderdefs(tags, tuples):
    tags = frozenset(tags)
    for name, worker_name, factory in tuples:
        yield BuilderDef(name, factory, tags=tags, worker_name=worker_name)


# -- Stable Tier-1 builder ----------------------------------------------
BUILDER_DEFS.extend(generate_builderdefs({STABLE, TIER_1}, [
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
    ("AMD64 CentOS9", "cstratak-CentOS9-x86_64", CentOS9Build),
    ("AMD64 CentOS9 Refleaks", "cstratak-CentOS9-x86_64", UnixRefleakBuild),
    ("AMD64 CentOS9 LTO", "cstratak-CentOS9-x86_64", LTONonDebugUnixBuild),
    ("AMD64 CentOS9 LTO + PGO", "cstratak-CentOS9-x86_64", LTOPGONonDebugBuild),
    ("AMD64 CentOS9 NoGIL", "itamaro-centos-aws", UnixNoGilBuild),
    ("AMD64 CentOS9 NoGIL Refleaks", "itamaro-centos-aws", UnixNoGilRefleakBuild),

    # Windows x86-64 MSVC
    ("AMD64 Windows10", "bolen-windows10", Windows64Build),
    ("AMD64 Windows11 Non-Debug", "ware-win11", Windows64ReleaseBuild),
    ("AMD64 Windows11 Refleaks", "ware-win11", Windows64RefleakBuild),
    ("AMD64 Windows Server 2022 NoGIL", "itamaro-win64-srv-22-aws", Windows64NoGilBuild),
    ("AMD64 Windows PGO Tailcall", "itamaro-win64-srv-22-aws", Windows64PGOTailcallBuild),
    ("AMD64 Windows PGO NoGIL", "itamaro-win64-srv-22-aws", Windows64PGONoGilBuild),
    ("AMD64 Windows PGO NoGIL Tailcall", "itamaro-win64-srv-22-aws", Windows64PGONoGilTailcallBuild),
]))


# -- Stable Tier-2 builder ----------------------------------------------
BUILDER_DEFS.extend(generate_builderdefs({STABLE, TIER_2}, [
    # Fedora Linux x86-64 Clang
    ("AMD64 Fedora Stable Clang", "cstratak-fedora-stable-x86_64", ClangUnixBuild),
    ("AMD64 Fedora Stable Clang Installed", "cstratak-fedora-stable-x86_64", ClangUnixInstalledBuild),

    # Fedora Linux ppc64le GCC
    ("PPC64LE Fedora Stable", "cstratak-fedora-stable-ppc64le", FedoraStableBuild),
    ("PPC64LE Fedora Stable Refleaks", "cstratak-fedora-stable-ppc64le", UnixRefleakBuild),
    ("PPC64LE Fedora Stable LTO", "cstratak-fedora-stable-ppc64le", LTONonDebugUnixBuild),
    ("PPC64LE Fedora Stable LTO + PGO", "cstratak-fedora-stable-ppc64le", LTOPGONonDebugBuild),

    # RHEL8 ppc64le GCC
    ("PPC64LE RHEL8", "cstratak-RHEL8-ppc64le", RHEL8Build),
    ("PPC64LE RHEL8 Refleaks", "cstratak-RHEL8-ppc64le", UnixRefleakBuild),
    ("PPC64LE RHEL8 LTO", "cstratak-RHEL8-ppc64le", LTONonDebugUnixBuild),
    ("PPC64LE RHEL8 LTO + PGO", "cstratak-RHEL8-ppc64le", LTOPGONonDebugBuild),

    # CentOS Stream 9 Linux ppc64le GCC
    ("PPC64LE CentOS9", "cstratak-CentOS9-ppc64le", CentOS9Build),
    ("PPC64LE CentOS9 Refleaks", "cstratak-CentOS9-ppc64le", UnixRefleakBuild),
    ("PPC64LE CentOS9 LTO", "cstratak-CentOS9-ppc64le", LTONonDebugUnixBuild),
    ("PPC64LE CentOS9 LTO + PGO", "cstratak-CentOS9-ppc64le", LTOPGONonDebugBuild),

    # Fedora Linux aarch64 GCC/Clang
    ("aarch64 Fedora Stable", "cstratak-fedora-stable-aarch64", FedoraStableBuild),
    ("aarch64 Fedora Stable Refleaks", "cstratak-fedora-stable-aarch64", UnixRefleakBuild),
    ("aarch64 Fedora Stable Clang", "cstratak-fedora-stable-aarch64", ClangUnixBuild),
    ("aarch64 Fedora Stable Clang Installed", "cstratak-fedora-stable-aarch64", ClangUnixInstalledBuild),
    ("aarch64 Fedora Stable LTO", "cstratak-fedora-stable-aarch64", LTONonDebugUnixBuild),
    ("aarch64 Fedora Stable LTO + PGO", "cstratak-fedora-stable-aarch64", LTOPGONonDebugBuild),

    # RHEL8 aarch64 GCC
    ("aarch64 RHEL8", "cstratak-RHEL8-aarch64", RHEL8Build),
    ("aarch64 RHEL8 Refleaks", "cstratak-RHEL8-aarch64", UnixRefleakBuild),
    ("aarch64 RHEL8 LTO", "cstratak-RHEL8-aarch64", LTONonDebugUnixBuild),
    ("aarch64 RHEL8 LTO + PGO", "cstratak-RHEL8-aarch64", LTOPGONonDebugBuild),

    # CentOS Stream 9 Linux aarch64 GCC
    ("aarch64 CentOS9", "cstratak-CentOS9-aarch64", CentOS9Build),
    ("aarch64 CentOS9 Refleaks", "cstratak-CentOS9-aarch64", UnixRefleakBuild),
    ("aarch64 CentOS9 LTO", "cstratak-CentOS9-aarch64", LTONonDebugUnixBuild),
    ("aarch64 CentOS9 LTO + PGO", "cstratak-CentOS9-aarch64", LTOPGONonDebugBuild),

    # macOS aarch64 clang
    ("ARM64 macOS", "pablogsal-macos-m1", MacOSArmWithBrewBuild),
    ("ARM64 MacOS M1 NoGIL", "itamaro-macos-arm64-aws", MacOSArmWithBrewNoGilBuild),
    ("ARM64 MacOS M1 Refleaks NoGIL", "itamaro-macos-arm64-aws", MacOSArmWithBrewNoGilRefleakBuild),

    # macOS x86-64 clang
    ("x86-64 macOS", "billenstein-macos", UnixBuild),
    ("x86-64 MacOS Intel NoGIL", "itamaro-macos-intel-aws", UnixNoGilBuild),
    ("x86-64 MacOS Intel ASAN NoGIL", "itamaro-macos-intel-aws", MacOSAsanNoGilBuild),

    # WASI
    ("wasm32-wasi Non-Debug", "bcannon-wasi", Wasm32WasiCrossBuild),
    ("wasm32-wasi", "bcannon-wasi", Wasm32WasiPreview1DebugBuild),
]))


# -- Stable Tier-3 builder ----------------------------------------------
BUILDER_DEFS.extend(generate_builderdefs({STABLE, TIER_3}, [

    # Fedora Linux s390x GCC/Clang
    ("s390x Fedora Stable", "cstratak-fedora-stable-s390x", UnixBuild),
    ("s390x Fedora Stable Refleaks", "cstratak-fedora-stable-s390x", UnixRefleakBuild),
    ("s390x Fedora Stable Clang", "cstratak-fedora-stable-s390x", ClangUnixBuild),
    ("s390x Fedora Stable Clang Installed", "cstratak-fedora-stable-s390x", ClangUnixInstalledBuild),
    ("s390x Fedora Stable LTO", "cstratak-fedora-stable-s390x", LTONonDebugUnixBuild),
    ("s390x Fedora Stable LTO + PGO", "cstratak-fedora-stable-s390x", LTOPGONonDebugBuild),

    # RHEL9 GCC
    ("s390x RHEL9", "cstratak-rhel9-s390x", UnixBuild),
    ("s390x RHEL9 Refleaks", "cstratak-rhel9-s390x", UnixRefleakBuild),
    ("s390x RHEL9 LTO", "cstratak-rhel9-s390x", LTONonDebugUnixBuild),
    ("s390x RHEL9 LTO + PGO", "cstratak-rhel9-s390x", LTOPGONonDebugBuild),

    # RHEL8 GCC
    ("s390x RHEL8", "cstratak-rhel8-s390x", UnixBuild),
    ("s390x RHEL8 Refleaks", "cstratak-rhel8-s390x", UnixRefleakBuild),
    ("s390x RHEL8 LTO", "cstratak-rhel8-s390x", LTONonDebugUnixBuild),
    ("s390x RHEL8 LTO + PGO", "cstratak-rhel8-s390x", LTOPGONonDebugBuild),

    # Fedora Linux ppc64le Clang
    ("PPC64LE Fedora Stable Clang", "cstratak-fedora-stable-ppc64le", ClangUnixBuild),
    ("PPC64LE Fedora Stable Clang Installed", "cstratak-fedora-stable-ppc64le", ClangUnixInstalledBuild),

    # Linux armv7l (32-bit) GCC
    ("ARM Raspbian", "gps-raspbian", SlowNonDebugUnixBuild15BitDigits),

    # Linux armv8 (64-bit) GCC
    ("ARM64 Raspbian", "stan-raspbian", SlowNonDebugUnixBuild),
    ("ARM64 Raspbian Debug", "savannah-raspbian", SlowDebugUnixBuild),

    # FreBSD x86-64 clang
    ("AMD64 FreeBSD Refleaks", "opsec-fbsd14", UnixRefleakBuild),
    ("AMD64 FreeBSD14", "opsec-fbsd14", UnixBuild),

    # iOS
    ("iOS ARM64 Simulator", "rkm-arm64-ios-simulator", IOSARM64SimulatorBuild),

    # Android
    ("aarch64 Android", "mhsmith-android-aarch64", AndroidBuild),
    ("AMD64 Android", "mhsmith-android-x86_64", AndroidBuild),

    # Emscripten
    ("WASM Emscripten", "rkm-emscripten", EmscriptenBuild),
]))


# -- Stable No Tier builders --------------------------------------------
BUILDER_DEFS.extend(generate_builderdefs({STABLE}, [
    # Linux x86-64 GCC musl
    ("AMD64 Alpine Linux", "ware-alpine", UnixBuild),
    # Linux x86-64 GCC musl Freethreading
    ("AMD64 Alpine Linux NoGIL", "ware-alpine", UnixNoGilBuild),

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

    # riscv64 GCC
    ("riscv64 Ubuntu", "onder-riscv64", SlowUnixInstalledBuild),
]))


# -- Unstable Tier-1 builders -------------------------------------------
BUILDER_DEFS.extend(generate_builderdefs({UNSTABLE, TIER_1}, [
    # Ubuntu Linux AArch64
    ("aarch64 Ubuntu 24.04 BigMem", "diegorusso-aarch64-bigmem", UnixBigmemBuild),

    # Linux x86-64 GCC
    # Fedora Rawhide is unstable
    ("AMD64 Fedora Rawhide", "cstratak-fedora-rawhide-x86_64", FedoraRawhideBuild),
    ("AMD64 Fedora Rawhide Refleaks", "cstratak-fedora-rawhide-x86_64", UnixRefleakBuild),
    ("AMD64 Fedora Rawhide LTO", "cstratak-fedora-rawhide-x86_64", LTONonDebugUnixBuild),
    ("AMD64 Fedora Rawhide LTO + PGO", "cstratak-fedora-rawhide-x86_64", LTOPGONonDebugBuild),

    ("AMD64 Ubuntu", "skumaran-ubuntu-x86_64", UnixBuild),

    ("AMD64 RHEL8 FIPS No Builtin Hashes", "cstratak-RHEL8-fips-x86_64", RHEL8NoBuiltinHashesUnixBuild),

    ("AMD64 CentOS9 FIPS Only Blake2 Builtin Hash", "cstratak-CentOS9-fips-x86_64", CentOS9NoBuiltinHashesUnixBuildExceptBlake2),
    ("AMD64 CentOS9 FIPS No Builtin Hashes", "cstratak-CentOS9-fips-x86_64", CentOS9NoBuiltinHashesUnixBuild),

    ("AMD64 Arch Linux Valgrind", "pablogsal-arch-x86_64", ValgrindBuild),
]))


# -- Unstable Tier-2 builders -------------------------------------------
BUILDER_DEFS.extend(generate_builderdefs({UNSTABLE, TIER_2}, [
    # Linux x86-64 Clang
    # Fedora Rawhide is unstable
    # UBSan is a special build
    ("AMD64 Fedora Rawhide Clang", "cstratak-fedora-rawhide-x86_64", ClangUnixBuild),
    ("AMD64 Fedora Rawhide Clang Installed", "cstratak-fedora-rawhide-x86_64", ClangUnixInstalledBuild),

    # Fedora Linux ppc64le GCC
    # Fedora Rawhide is unstable
    ("PPC64LE Fedora Rawhide", "cstratak-fedora-rawhide-ppc64le", FedoraRawhideBuild),
    ("PPC64LE Fedora Rawhide Refleaks", "cstratak-fedora-rawhide-ppc64le", UnixRefleakBuild),
    ("PPC64LE Fedora Rawhide LTO", "cstratak-fedora-rawhide-ppc64le", LTONonDebugUnixBuild),
    ("PPC64LE Fedora Rawhide LTO + PGO", "cstratak-fedora-rawhide-ppc64le", LTOPGONonDebugBuild),

    # Fedora Linux aarch64 GCC/Clang
    # Fedora Rawhide is unstable
    ("aarch64 Fedora Rawhide", "cstratak-fedora-rawhide-aarch64", FedoraRawhideBuild),
    ("aarch64 Fedora Rawhide Refleaks", "cstratak-fedora-rawhide-aarch64", UnixRefleakBuild),
    ("aarch64 Fedora Rawhide Clang", "cstratak-fedora-rawhide-aarch64", ClangUnixBuild),
    ("aarch64 Fedora Rawhide Clang Installed", "cstratak-fedora-rawhide-aarch64", ClangUnixInstalledBuild),
    ("aarch64 Fedora Rawhide LTO", "cstratak-fedora-rawhide-aarch64", LTONonDebugUnixBuild),
    ("aarch64 Fedora Rawhide LTO + PGO", "cstratak-fedora-rawhide-aarch64", LTOPGONonDebugBuild),

    # CentOS Stream 10 Linux aarch64 GCC/Clang
    ("aarch64 CentOS10", "cstratak-CentOS10-aarch64", CentOS10Build),
    ("aarch64 CentOS10 Refleaks", "cstratak-CentOS10-aarch64", UnixRefleakBuild),
    ("aarch64 CentOS10 Clang", "cstratak-CentOS10-aarch64", ClangUnixBuild),
    ("aarch64 CentOS10 Clang Installed", "cstratak-CentOS10-aarch64", ClangUnixInstalledBuild),
    ("aarch64 CentOS10 LTO", "cstratak-CentOS10-aarch64", LTONonDebugUnixBuild),
    ("aarch64 CentOS10 LTO + PGO", "cstratak-CentOS10-aarch64", LTOPGONonDebugBuild),

    # WebAssembly
    ("wasm32 WASI 8Core", "kushaldas-wasi", Wasm32WasiCrossBuild),
]))


# -- Unstable Tier-3 builders -------------------------------------------
BUILDER_DEFS.extend(generate_builderdefs({UNSTABLE, TIER_3}, [
    # Linux ppc64le Clang
    # Fedora Rawhide is unstable
    ("PPC64LE Fedora Rawhide Clang", "cstratak-fedora-rawhide-ppc64le", ClangUnixBuild),
    ("PPC64LE Fedora Rawhide Clang Installed", "cstratak-fedora-rawhide-ppc64le", ClangUnixInstalledBuild),

    # Linux s390x GCC/Clang
    ("s390x Fedora Rawhide", "cstratak-fedora-rawhide-s390x", UnixBuild),
    ("s390x Fedora Rawhide Refleaks", "cstratak-fedora-rawhide-s390x", UnixRefleakBuild),
    ("s390x Fedora Rawhide Clang", "cstratak-fedora-rawhide-s390x", ClangUnixBuild),
    ("s390x Fedora Rawhide Clang Installed", "cstratak-fedora-rawhide-s390x", ClangUnixInstalledBuild),
    ("s390x Fedora Rawhide LTO", "cstratak-fedora-rawhide-s390x", LTONonDebugUnixBuild),
    ("s390x Fedora Rawhide LTO + PGO", "cstratak-fedora-rawhide-s390x", LTOPGONonDebugBuild),

    # CentOS Stream 10 Linux s390x GCC/Clang
    ("s390x CentOS10", "cstratak-c10s-s390x", CentOS10Build),
    ("s390x CentOS10 Refleaks", "cstratak-c10s-s390x", UnixRefleakBuild),
    ("s390x CentOS10 Clang", "cstratak-c10s-s390x", ClangUnixBuild),
    ("s390x CentOS10 Clang Installed", "cstratak-c10s-s390x", ClangUnixInstalledBuild),
    ("s390x CentOS10 LTO", "cstratak-c10s-s390x", LTONonDebugUnixBuild),
    ("s390x CentOS10 LTO + PGO", "cstratak-c10s-s390x", LTOPGONonDebugBuild),

    # FreeBSD x86-64 clang
    # FreeBSD 15 is CURRENT: development branch (at 2023-10-17)
    ("AMD64 FreeBSD15", "opsec-fbsd15", UnixBuild),
    # FreeBSD 16 is CURRENT: development branch (at 2026-01-09)
    ("AMD64 FreeBSD16", "opsec-fbsd16", UnixBuild),

    # Windows aarch64 MSVC
    ("ARM64 Windows", "ware-win11-arm64", WindowsARM64Build),
    ("ARM64 Windows Non-Debug", "ware-win11-arm64", WindowsARM64ReleaseBuild),

]))


# -- Unstable No Tier builders ------------------------------------------
BUILDER_DEFS.extend(generate_builderdefs({UNSTABLE}, [
    # Linux GCC Fedora Rawhide Freethreading builders
    ("AMD64 Fedora Rawhide NoGIL", "cstratak-fedora-rawhide-x86_64", FedoraRawhideFreedthreadingBuild),
    ("aarch64 Fedora Rawhide NoGIL", "cstratak-fedora-rawhide-aarch64", FedoraRawhideFreedthreadingBuild),
    ("PPC64LE Fedora Rawhide NoGIL", "cstratak-fedora-rawhide-ppc64le", FedoraRawhideFreedthreadingBuild),
    ("s390x Fedora Rawhide NoGIL", "cstratak-fedora-rawhide-s390x", FedoraRawhideFreedthreadingBuild),
    # Linux GCC Fedora Rawhide Freethreading refleak builders
    ("AMD64 Fedora Rawhide NoGIL refleaks", "cstratak-fedora-rawhide-x86_64", UnixNoGilRefleakBuild),
    ("aarch64 Fedora Rawhide NoGIL refleaks", "cstratak-fedora-rawhide-aarch64", UnixNoGilRefleakBuild),
    ("PPC64LE Fedora Rawhide NoGIL refleaks", "cstratak-fedora-rawhide-ppc64le", UnixNoGilRefleakBuild),
    ("s390x Fedora Rawhide NoGIL refleaks", "cstratak-fedora-rawhide-s390x", UnixNoGilRefleakBuild),

    # Linux x86-64 NixOS Unstable
    ("AMD64 NixOS Unstable", "malvex-nixos-x86_64", UnixBuild),
    ("AMD64 NixOS Unstable Refleaks", "malvex-nixos-x86_64", UnixRefleakBuild),
    ("AMD64 NixOS Unstable Perf", "malvex-nixos-x86_64", UnixPerfBuild),

    # Solaris sparcv9
    ("SPARCv9 Oracle Solaris 11.4", "kulikjak-solaris-sparcv9", UnixBuild),

    # Arch Usan (see stable "AMD64 Arch Linux Usan Function" above)
    ("AMD64 Arch Linux Usan", "pablogsal-arch-x86_64", ClangUbsanLinuxBuild),

    # RISC-V 64-bit GCC
    ("RISC-V 64-bit Ubuntu", "rise-riscv64-4", SlowDebugUnixBuild),
    ("RISC-V 64-bit Ubuntu NoGIL", "rise-riscv64-3", SlowUnixNoGilBuild),
    ("RISC-V 64-bit Ubuntu Clang", "rise-riscv64-2", SlowClangUnixBuild),
]))


def get_builder_defs(settings):
    # Override with a simple default if we are using local workers
    if settings.use_local_worker:
        local_buildfactory = getattr(
            factories, settings.local_worker_buildfactory, UnixBuild
        )
        return [BuilderDef(
            "Test Builder",
            local_buildfactory,
            tags={STABLE},
            worker_name="local-worker",
        )]

    return BUILDER_DEFS


# Match builder name (excluding the branch name) of builders that should only
# run on the main and PR branches.
ONLY_MAIN_BRANCH = (
    "Windows PGO",
    "AMD64 Arch Linux Perf",
    "AMD64 Arch Linux Valgrind",
)


if __name__ == "__main__":
    # Print a list to the terminal
    import itertools

    colorize = bool(sys.stdout.isatty() and not os.environ.get('NO_COLOR'))
    NAME = '\x1b[36m' * colorize
    END = '\x1b[m' * colorize

    def key(builder_def):
        return builder_def.stability, builder_def.tier

    defs = sorted(BUILDER_DEFS, key=key)

    for (stability, tier), defs in itertools.groupby(defs, key):
        print()
        title = f'{stability.title()}, {tier}'
        print(title)
        print('-' * len(title))
        print()
        for d in defs:
            print(f'{NAME}{d.name}{END}')
            print(f'  {d.factory.__name__} on {d.worker_name}')
            print(f'  [{' '.join(sorted(d.tags))}]')
