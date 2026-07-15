from setuptools import find_packages, setup

from estateflow import __version__

setup(
    name="estateflow",
    version=__version__,
    description="Universal real estate, housing, hospitality and property operations for ERPNext",
    author="EstateFlow contributors",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
