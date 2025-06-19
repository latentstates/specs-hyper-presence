#!/usr/bin/env python3
"""
Setup script for SPECS Hyper Presence beacon tracking system
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="specs-hyper-presence",
    version="2.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="BLE beacon tracking system with SPECS Form integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/latentstates/specs-hyper-presence",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "bleak>=0.21.0",
    ],
    extras_require={
        "enhanced": [
            "numpy>=1.24.0",
            "pandas>=2.0.0",
        ],
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
        ],
        "server": [
            "fastapi>=0.104.0",
            "uvicorn>=0.24.0",
            "sqlalchemy>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "beacon-scanner=beacon_scanner.beacon_scanner:main",
            "beacon-simulator=specs_client.simulator.beacon_simulator:main",
        ],
    },
    include_package_data=True,
    package_data={
        "beacon_scanner": ["*.json.example", "*.md"],
        "specs_client": ["*.md"],
    },
)