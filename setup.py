#!/usr/bin/env python3
import os
import sys
import subprocess
import tempfile
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext as _build_ext

GBINDER_REPO = "https://github.com/mer-hybris/libgbinder.git"
GBINDER_TAG  = "v1.1.30"  # adjust to a real tag or branch

class build_ext(_build_ext):
    def run(self):
        # 1. If pkg-config can see libgbinder, skip vendoring
        if not self._has_pkgconfig("libgbinder"):
            self.announce("⚙️  libgbinder not found on system; cloning & building…", level=2)
            self._vendor_and_build()
        # 2. Proceed with normal ext build
        super().run()

    def _has_pkgconfig(self, name: str) -> bool:
        try:
            subprocess.check_output(["pkg-config", "--exists", name])
            return True
        except Exception:
            return False

    def _vendor_and_build(self):
        tmpdir = tempfile.mkdtemp(prefix="gbinder-")
        src    = os.path.join(tmpdir, "libgbinder")
        install_prefix = os.path.join(tmpdir, "install")

        # Clone with tag fallback
        from git import Repo, GitCommandError
        try:
            Repo.clone_from(GBINDER_REPO, src, branch=GBINDER_TAG, depth=1)
        except GitCommandError:
            self.announce(f"⚠️ Tag '{GBINDER_TAG}' not found; cloning default branch", level=2)
            Repo.clone_from(GBINDER_REPO, src, depth=1)

        # Autodetect build system
        if os.path.exists(os.path.join(src, "meson.build")):
            self._build_meson(src, install_prefix)
        elif os.path.exists(os.path.join(src, "configure")) or os.path.exists(os.path.join(src, "configure.ac")):
            self._build_autotools(src, install_prefix)
        elif os.path.exists(os.path.join(src, "CMakeLists.txt")):
            self._build_cmake(src, install_prefix)
        else:
            raise RuntimeError(
                "Unknown build system in libgbinder: "
                "no meson.build, configure(.ac), or CMakeLists.txt found."
            )

        # Point pkg-config at our vendored install
        pcdir = os.path.join(install_prefix, "usr", "lib", "pkgconfig")
        os.environ["PKG_CONFIG_PATH"] = pcdir + os.pathsep + os.environ.get("PKG_CONFIG_PATH", "")

    def _build_meson(self, src, prefix):
        bld = os.path.join(src, "build-meson")
        os.makedirs(bld, exist_ok=True)
        self.announce("🔨 Meson: configure…", level=2)
        subprocess.check_call(["meson", src, bld, "--prefix=/usr"])
        self.announce("🏗 Meson: build…", level=2)
        subprocess.check_call(["ninja", "-C", bld])
        self.announce("📦 Meson: install…", level=2)
        subprocess.check_call(["ninja", "-C", bld, "install", f"--destdir={prefix}"])

    def _build_autotools(self, src, prefix):
        cwd = os.getcwd()
        os.chdir(src)
        try:
            self.announce("🔧 Autotools: autoreconf…", level=2)
            if os.path.exists("configure.ac") and not os.path.exists("configure"):
                subprocess.check_call(["autoreconf", "-fi"])
            self.announce("🏗 Autotools: configure…", level=2)
            subprocess.check_call(["./configure", "--prefix=/usr"])
            self.announce("🏗 Autotools: build…", level=2)
            subprocess.check_call(["make", "-j"])
            self.announce("📦 Autotools: install…", level=2)
            subprocess.check_call(["make", f"DESTDIR={prefix}", "install"])
        finally:
            os.chdir(cwd)

    def _build_cmake(self, src, prefix):
        bld = os.path.join(src, "build-cmake")
        os.makedirs(bld, exist_ok=True)
        self.announce("🔨 CMake: configure…", level=2)
        subprocess.check_call([
            "cmake", "-S", src, "-B", bld,
            "-DCMAKE_INSTALL_PREFIX=/usr"
        ])
        self.announce("🏗 CMake: build…", level=2)
        subprocess.check_call(["cmake", "--build", bld, "--", "-j"])
        self.announce("📦 CMake: install…", level=2)
        subprocess.check_call([
            "cmake", "--install", bld,
            "--prefix", "/usr", "--root", prefix
        ])

    def build_extensions(self):
        # Reload each Extension’s include/library paths now that PKG_CONFIG_PATH is set
        self.extensions = [_reconfigure(ext) for ext in self.extensions]
        super().build_extensions()


def _reconfigure(ext):
    cfg = {'sources': ext.sources}
    flags = subprocess.getoutput("pkg-config --cflags --libs libgbinder").split()
    for tok in flags:
        if tok.startswith("-I"):
            ext.include_dirs.append(tok[2:])
        elif tok.startswith("-L"):
            ext.library_dirs.append(tok[2:])
        elif tok.startswith("-l"):
            ext.libraries.append(tok[2:])
    return ext


# Detect optional Cython build
USE_CYTHON = "--cython" in sys.argv
if USE_CYTHON:
    sys.argv.remove("--cython")

suffix = ".pyx" if USE_CYTHON else ".c"
mod_src = [os.path.join(os.path.dirname(__file__), f"gbinder{suffix}")]
exts = [Extension("gbinder", sources=mod_src)]

if USE_CYTHON:
    from Cython.Build import cythonize
    exts = cythonize(exts, compiler_directives={"language_level": "3"})

setup(
    name="gbinder",
    version="1.2.5",  
    description="Cython extension module for C++ gbinder functions",
    author="Erfan Abdi",
    author_email="erfangplus@gmail.com",
    maintainer="Meshack Bahati",
    maintainer_email="bahatikylemeshack@gmail.com",
    url="https://github.com/Kyle6012/gbinder",
    license="GPLv3",
    python_requires=">=3.6",
    ext_modules=exts,
    cmdclass={"build_ext": build_ext},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Cython",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    keywords=["Cython", "C++", "gbinder", "extension module"],
)
