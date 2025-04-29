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
        if not self._has_pkgconfig("gbinder"):
            self.announce("⚙️  libgbinder not found; cloning & building…", level=2)
            self._vendor_and_build()
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

        # 1) Clone upstream, fallback to default branch if tag missing
        from git import Repo, GitCommandError
        try:
            Repo.clone_from(GBINDER_REPO, src, branch=GBINDER_TAG, depth=1)
        except GitCommandError:
            self.announce(f"⚠️ Tag '{GBINDER_TAG}' not found; cloning default branch", level=2)
            Repo.clone_from(GBINDER_REPO, src, depth=1)

        # 2) Verify Makefile exists
        makefile = os.path.join(src, "Makefile")
        if not os.path.exists(makefile):
            raise RuntimeError("No Makefile found in libgbinder repo – cannot build.")

        # 3) Build & install via Makefile
        env = os.environ.copy()
        env["DESTDIR"] = install_prefix

        # Build everything (debug + release + pkgconfig)
        self.announce("🏗 Running make all…", level=2)
        subprocess.check_call(["make", "all"], cwd=src, env=env)

        # Install runtime libs
        self.announce("📦 Running make install…", level=2)
        subprocess.check_call(["make", "install"], cwd=src, env=env)

        # Install headers & pkg-config file
        self.announce("📦 Running make install-dev…", level=2)
        subprocess.check_call(["make", "install-dev"], cwd=src, env=env)

        # 4) Point pkg-config at our vendored build
        pc_dir = os.path.join(install_prefix, "usr", "lib", "pkgconfig")
        os.environ["PKG_CONFIG_PATH"] = pc_dir + os.pathsep + os.environ.get("PKG_CONFIG_PATH", "")

    def build_extensions(self):
        # Reconfigure include/lib paths now that PKG_CONFIG_PATH is set
        self.extensions = [_reconfigure(ext) for ext in self.extensions]
        super().build_extensions()


def _reconfigure(ext: Extension) -> Extension:
    flags = subprocess.getoutput("pkg-config --cflags --libs gbinder").split()
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
    version="1.2.7",
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
