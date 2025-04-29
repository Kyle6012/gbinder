#!/usr/bin/env python3
import os
import sys
import subprocess
import tempfile
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext as _build_ext

# Git URL & tag/branch for libgbinder
GBINDER_REPO = "https://github.com/mer-hybris/libgbinder.git"
GBINDER_TAG = "v1.1.42"  

class build_ext(_build_ext):
    """Custom build_ext that vendors & builds libgbinder if pkg-config fails."""
    def run(self):
        # 1. Try system pkg-config first
        if not self._have_pkgconfig("libgbinder"):
            self.announce("⚙️  libgbinder not found via pkg-config; cloning & building manually", level=2)
            self._vendor_build_gbinder()
        return super().run()

    def _have_pkgconfig(self, name):
        try:
            subprocess.check_output(["pkg-config", "--exists", name])
            return True
        except (OSError, subprocess.CalledProcessError):
            return False

    def _vendor_build_gbinder(self):
        tmpdir = tempfile.mkdtemp(prefix="gbinder-")
        src_dir = os.path.join(tmpdir, "gbinder")
        self.announce(f"🗂 Cloning {GBINDER_REPO}@{GBINDER_TAG} into {src_dir}", level=2)
        # clone only that tag
        from git import Repo
        Repo.clone_from(GBINDER_REPO, src_dir, branch=GBINDER_TAG, depth=1)

        build_dir = os.path.join(src_dir, "build")
        os.makedirs(build_dir, exist_ok=True)

        # Run meson & ninja
        self.announce("🔨 Configuring meson …", level=2)
        subprocess.check_call(["meson", src_dir, build_dir], cwd=build_dir)
        self.announce("🏗 Building libgbinder …", level=2)
        subprocess.check_call(["ninja", "-C", build_dir])

        # Install into our build-temp prefix
        install_prefix = os.path.join(tmpdir, "install")
        self.announce(f"📦 Installing into {install_prefix}", level=2)
        subprocess.check_call(["ninja", "-C", build_dir, "install", f"--destdir={install_prefix}"])

        # Tell pkg-config where to find our local build
        pc_path = os.path.join(install_prefix, "usr", "lib", "pkgconfig")
        os.environ["PKG_CONFIG_PATH"] = pc_path + os.pathsep + os.environ.get("PKG_CONFIG_PATH", "")

    def build_extensions(self):
        # Before building extensions, re-run pkgconfig so it picks up new PKG_CONFIG_PATH
        self.extensions = [_configure_extension(ext) for ext in self.extensions]
        super().build_extensions()

def pkgconfig(package, kw):
    """Populate include_dirs, library_dirs, libraries from pkg-config."""
    flag_map = {'-I': 'include_dirs', '-L': 'library_dirs', '-l': 'libraries'}
    try:
        output = subprocess.getoutput(f'pkg-config --cflags --libs {package}')
        for token in output.split():
            key = flag_map.get(token[:2])
            if key:
                kw.setdefault(key, []).append(token[2:])
    except Exception:
        pass
    return kw

def _configure_extension(ext: Extension) -> Extension:
    cfg = {'sources': ext.sources}
    cfg = pkgconfig("libgbinder", cfg)
    for attr in ("include_dirs", "library_dirs", "libraries"):
        setattr(ext, attr, cfg.get(attr, []))
    return ext

# Determine if user explicitly wants a .pyx build
USE_CYTHON = "--cython" in sys.argv
if USE_CYTHON:
    sys.argv.remove("--cython")

file_ext = ".pyx" if USE_CYTHON else ".c"
sources = [os.path.join(os.path.dirname(__file__), f"gbinder{file_ext}")]

ext_modules = [Extension("gbinder", sources=sources)]
if USE_CYTHON:
    from Cython.Build import cythonize
    ext_modules = cythonize(ext_modules, compiler_directives={"language_level": "3"})

setup(
    name="gbinder",
    version="1.2.1",
    description="Cython extension module for C++ gbinder functions",
    author="Erfan Abdi",
    author_email="erfangplus@gmail.com",
    maintainer="Meshack Bahati",
    maintainer_email="bahatikylemeshack@gmail.com",
    url="https://github.com/Kyle6012/gbinder",
    license="GPLv3",
    python_requires=">=3.6",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Cython",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    keywords=["Cython", "C++", "gbinder", "extension module"],
)
