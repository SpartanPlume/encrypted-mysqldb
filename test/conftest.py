import os
import subprocess
import pytest

has_been_configured = False


def pytest_configure(config):
    try:
        subprocess.run(os.path.join(config.rootpath, "test", "setup.sh"), shell=True, check=True)
        global has_been_configured
        has_been_configured = True
    except subprocess.CalledProcessError:
        pytest.exit("Could not create the test database. Please check that the mysql service has been started.")


def pytest_unconfigure(config):
    if has_been_configured:
        try:
            subprocess.run(os.path.join(config.rootpath, "test", "teardown.sh"), shell=True, check=True)
        except subprocess.CalledProcessError:
            pytest.exit("Could not delete the test database.")
