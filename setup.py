from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="vibereminder",
    version="1.0.0",
    author="vinmusicmail-source",
    description="Умные напоминания с голосом для Windows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vinmusicmail-source/VibeReminder",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business :: Scheduling",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pygame>=2.5.0",
        "pyaudio>=0.2.13",
        "numpy>=1.24.0",
    ],
    entry_points={
        "console_scripts": [
            "vibereminder=reminder_app:main",
        ],
    },
)
