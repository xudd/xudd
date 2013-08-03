from setuptools import setup, find_packages

setup(
    name="XUDD",
    version="0.1.0",
    description="An actor model system for python",
    author="Christopher Allan Webber",
    author_email="cwebber@dustycloud.org",
    url="https://github.com/cwebber/xudd",
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
)
