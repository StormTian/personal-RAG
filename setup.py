#!/usr/bin/env python
"""
RAG Application - Setup Script
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

with open("requirements-dev.txt", "r", encoding="utf-8") as fh:
    dev_requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#") and not line.startswith("-r")]

setup(
    name="rag-demo",
    version="0.3.0",
    author="RAG Team",
    author_email="rag@example.com",
    description="A tiny offline RAG (Retrieval-Augmented Generation) demo application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rag-demo",
    packages=find_packages(exclude=["tests", "tests.*", ".deps", ".deps.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
        "docs": [
            "sphinx>=7.2.0",
            "sphinx-rtd-theme>=2.0.0",
            "myst-parser>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "rag-demo=app:main",
            "rag-web=web_app:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
