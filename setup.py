import sys
import subprocess
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext as _build_ext

def pkgconfig(package, kw):
    flag_map = {'-I': 'include_dirs', '-L': 'library_dirs', '-l': 'libraries'}
    output = subprocess.getoutput(f'pkg-config --cflags --libs {package}')
    for token in output.strip().split():
        if token[:2] in flag_map:
            kw.setdefault(flag_map[token[:2]], []).append(token[2:])
    return kw

USE_CYTHON = False
if "--cython" in sys.argv:
    sys.argv.remove("--cython")
    USE_CYTHON = True

ext = ".pyx" if USE_CYTHON else ".c"
ext_kwargs = {'sources': [f"gbinder{ext}"]}
ext_kwargs = pkgconfig("libgbinder", ext_kwargs)

extensions = [Extension("gbinder", **ext_kwargs)]

if USE_CYTHON:
    from Cython.Build import cythonize
    extensions = cythonize(extensions, compiler_directives={"language_level": "3"})

setup(
    name="gbinder",
    version="1.2.1",
    description="Cython extension module for C++ gbinder functions",
    author="Erfan Abdi",
    author_email="erfangplus@gmail.com",
    maintainer="Meshack Bahati",
    maintainer_email="bahatikylemeshack@gmail.com",
    license="GPLv3",
    url="https://github.com/Kyle6012/gbinder",
    ext_modules=extensions,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Cython",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    keywords=["Cython", "C++", "gbinder", "extension module"],
    python_requires=">=3.6",
)
