from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="openharmony-filebrowser",
    version="0.1.0",
    author="OpenHarmony_FileBrowser Contributors",
    description="A cross-platform file browser for OpenHarmony/HarmonyOS devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/OpenHarmony_FileBrowser",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "openharmony-filebrowser=src.main:main",
        ],
    },
    package_data={
        "": ["*.qss", "*.ico", "*.png"],
    },
    include_package_data=True,
    zip_safe=False,
)