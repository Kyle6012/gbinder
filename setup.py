#!/usr/bin/env python3
import os
import sys
import subprocess
import tempfile
import shutil
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext as _build_ext

# Repo + tag/branch
GBINDER_REPO = "https://github.com/mer-hybris/libgbinder.git"
GBINDER_TAG  = "v1.1.30"  # adjust to your desired tag

class build_ext(_build_ext):
    def run(self):
        if not self._have_pkgconfig("libgbinder"):
            self.announce("⚙️  libgbinder not found; cloning & building…", level=2)
            self._vendor_build_gbinder()
        super().run()

    def _have_pkgconfig(self, name):
        try:
            subprocess.check_output(["pkg-config", "--exists", name])
            return True
        except Exception:
            return False

    def _vendor_build_gbinder(self):
        tmpdir   = tempfile.mkdtemp(prefix="gbinder-")
        src_dir  = os.path.join(tmpdir, "libgbinder")
        install_prefix = os.path.join(tmpdir, "install")

        # 1. Clone
        from git import Repo, GitCommandError
        try:
            Repo.clone_from(GBINDER_REPO, src_dir, branch=GBINDER_TAG, depth=1)
        except GitCommandError:
            self.announce(f"⚠️ Tag '{GBINDER_TAG}' not found, cloning default branch", level=2)
            Repo.clone_from(GBINDER_REPO, src_dir, depth=1)

        # 2. Detect build system
        #   - Meson if meson.build present
        #   - Autotools if configure.ac or configure present
        if os.path.exists(os.path.join(src_dir, "meson.build")):
            self._build_with_meson(src_dir, install_prefix)
        elif (os.path.exists(os.path.join(src_dir, "configure")) or
              os.path.exists(os.path.join(src_dir, "configure.ac"))):
            self._build_with_autotools(src_dir, install_prefix)
        else:
            raise RuntimeError("Unknown build system in libgbinder repo; "
                               "neither meson.build nor configure(.*) found.")

        # 3. Point pkg-config to our vendored build
        pc_dir = os.path.join(install_prefix, "usr", "lib", "pkgconfig")
        os.environ["PKG_CONFIG_PATH"] = pc_dir + os.pathsep + os.environ.get("PKG_CONFIG_PATH", "")

    def _build_with_meson(self, src, prefix):
        build_dir = os.path.join(src, "build")
        os.makedirs(build_dir, exist_ok=True)
        self.announce("🔨 Meson: configuring…", level=2)
        subprocess.check_call(["meson", src, build_dir, f"--prefix=/usr"], cwd=build_dir)
        self.announce("🏗 Meson: building…", level=2)
        subprocess.check_call(["ninja", "-C", build_dir])
        self.announce("📦 Meson: installing…", level=2)
        subprocess.check_call(["ninja", "-C", build_dir, "install", f"--destdir={prefix}"])

    def _build_with_autotools(self, src, prefix):
        self.announce("🔧 Autotools: preparing…", level=2)
        cwd = os.getcwd()
        os.chdir(src)
        try:
            # generate configure if needed
            if os.path.exists("configure.ac") and not os.path.exists("configure"):
                subprocess.check_call(["autoreconf", "-fi"])
            # configure
            subprocess.check_call([
                "./configure",
                "--prefix=/usr",
                f"--datarootdir={prefix}/usr/share",
                f"--libdir={prefix}/usr/lib"
            ])
            self.announce("🏗 Autotools: building…", level=2)
            subprocess.check_call(["make", "-j"])
            self.announce("📦 Autotools: installing…", level=2)
            subprocess.check_call(["make", f"DESTDIR={prefix}", "install"])
        finally:
            os.chdir(cwd)

    def build_extensions(self):
        # reconfigure each ext so the vendored install is picked up
        self.extensions = [_configure_extension(ext) for ext in self.extensions]
        super().build_extensions()


def pkgconfig(pkg, cfg):
    """Populate include_dirs, library_dirs, libraries from pkg-config."""
    flag_map = {'-I': 'include_dirs', '-L': 'library_dirs', '-l': 'libraries'}
    try:
        out = subprocess.getoutput(f"pkg-config --cflags --libs {pkg}")
        for token in out.split():
            key = flag_map.get(token[:2])
            if key:
                cfg.setdefault(key, []).append(token[2:])
    except Exception:
        pass
    return cfg

def _configure_extension(ext):
    cfg = pkgconfig("libgbinder", {'sources': ext.sources})
    for attr in ("include_dirs", "library_dirs", "libraries"):
        setattr(ext, attr, cfg.get(attr, []))
    return ext

# detect --cython flag
USE_CYTHON = "--cython" in sys.argv
if USE_CYTHON:
    sys.argv.remove("--cython")

ext_file = ".pyx" if USE_CYTHON else ".c"
src = [os.path.join(os.path.dirname(__file__), f"gbinder{ext_file}")]
ext_modules = [Extension("gbinder", sources=src)]

if USE_CYTHON:
    from Cython.Build import cythonize
    ext_modules = cythonize(ext_modules, compiler_directives={"language_level": "3"})

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
