"""Legacy setuptools entry point used by Bench/uv editable installs.

Keep the version literal here: importing ``estateflow`` during an isolated PEP
517 build fails because the project package is not yet on sys.path.
"""

from setuptools import find_packages, setup


setup(
    name="estateflow",
    version="0.2.0",
    description="Universal real estate, housing, hospitality and property operations for ERPNext",
    author="EstateFlow contributors",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
