from setuptools import setup, find_packages
import sys


if sys.version_info < (3, 7):
    sys.exit("Sorry, Python < 3.7 is not supported")

with open("README.md", "r") as fh:
    long_description = fh.read()

version_string = "v0.2.0"

setup(
    name="adrenalloopkit",
    version=version_string,
    author="AdrenalLoopKit Contributors",
    description="Python implementation of the AdrenalLoop algorithm for Addison's Disease management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Healthcare Industry',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    install_requires=[
        'numpy>=1.22.0',
        'backports-datetime-fromisoformat>=1.0.0',
    ],
    python_requires='>=3.7',
)
