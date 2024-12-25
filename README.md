# gbinder: Cython Extension Module for `libgbinder`

`gbinder` is a Python module providing a Cython-based interface to the `libgbinder` library, enabling Python developers to leverage the power of `libgbinder` seamlessly. This README will guide you through the installation, usage, and development process for the `gbinder` module.

## Features

- Python bindings for `libgbinder` using Cython.
- Easy integration with your projects.
- Support for both PyPI and manual source builds.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
   - [Installing from PyPI](#installing-from-pypi)
   - [Installing via `apt`](#installing-via-apt)
3. [Usage](#usage)
   - [Verifying the Installation](#verifying-the-installation)
4. [Building from Source](#building-from-source)
5. [Acknowledgements](#acknowledgements)

---

## Prerequisites

Before installing `gbinder`, ensure the following dependencies are installed on your system:

```bash
sudo apt update
sudo apt install libgbinder-dev libglibutil-dev pkgconf
```

If you plan to develop or customize `gbinder`, you will also need to install Cython:

```bash
pip install cython
```

---

## Installation

### Installing from PyPI

The easiest way to install `gbinder` is via PyPI:

```bash
pip install gbinder
```

### Installing via `apt`

If your Linux distribution provides `gbinder` in its repositories, you can install it using:

```bash
sudo apt install python-gbinder
```

---

## Usage

### Verifying the Installation

After installation, verify the module by importing it in a Python shell:

```python
python
>>> import gbinder
>>> print("gbinder imported successfully.")
```

---

## Building from Source

For those who wish to contribute or build `gbinder` from source, follow these steps:

1. Clone the repository:

    ```bash
    git clone https://github.com/Kyle6012/gbinder.git
    cd gbinder
    pip install build
    ```

2. Build the extension using Cython:

    ```bash
    python setup.py build_ext --inplace 
	# or
    python -m build
    ```

3. Test the module from the current directory:

    ```python
    python
    >>> import gbinder
    >>> print("gbinder is working.")
    ```

---

## Additional Information

For detailed usage instructions and API documentation, refer to the source code or open an issue on the [GitHub repository](https://github.com/Kyle6012/gbinder).

---

## Acknowledgements

This README is inspired by the [`geographiclib-cython-bindings`](https://github.com/megaserg/geographiclib-cython-bindings) project. Special thanks to @megaserg for the inspiration and guidance.

---
