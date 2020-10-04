import os

from setuptools import find_packages, setup

VERSION = "0.1.0"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

setup(
    name="pi_internet",
    description=("PI Internet Monitor"),
    long_description_content_type="text/markdown",
    version=VERSION,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    scripts=["monitor/bin/in_monitor"],
    install_requires=[
        "click==7.1.2",
        "fake-rpi @ git+https://github.com/sn4k3"
        "/FakeRPi@0f30d320d5f715d8a4fb94e7105448508586ae94",
        "requests==2.24.0",
        "websocket_client==0.57.0",
    ],
    author="Craig Rueda",
    author_email="craig@craigrueda.com",
    url="https://craigrueda.com",
    download_url="https://github.com/craig-rueda/pi-speed",
    classifiers=["Programming Language :: Python :: 3.7"],
    tests_require=["nose>=1.0"],
    test_suite="nose.collector",
)
