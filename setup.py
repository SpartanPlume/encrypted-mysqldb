"""Needed for package creation"""

import setuptools

from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name="encrypted_mysqldb",
    version="1.0.0",
    description="A basic interface to Mysqldb library with integrated encryption",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="mysqldb mysql encrypted-mysqldb encrypted_mysqldb encryption hash db database mariadb",
    url="https://github.com/SpartanPlume/encrypted-mysqldb",
    author="Spartan Plume",
    author_email="spartan.plume@gmail.com",
    license="MIT",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    install_requires=["mysql-connector-python", "inflection"],
    zip_safe=False,
)
