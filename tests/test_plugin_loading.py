from milk.milk import Milk

import os
import pytest


@pytest.fixture
def cwd():
    currentWorkDir = os.getcwd()
    os.chdir(os.path.join(currentWorkDir, "tests", "resources"))

    yield
    os.chdir(currentWorkDir)

# to disable tests use this:
# @pytest.mark.skip(reason="no way of currently testing this")


def test_load_plugins_from_config_location(capfd):

    filename = "tests/resources/test_config/test.conf"

    Milk(arguments=["--config", filename])

    out, err = capfd.readouterr()
    assert "text: hello world" in str(out).strip()


def test_load_plugins_from_workdir(cwd, capfd):

    config = '''
- version: 1

- testplugin2:
    hello: "world2"
    '''

    Milk(arguments=[], config=config)
    out, err = capfd.readouterr()
    assert "hello: world2" in str(out).strip()


# def test_load_plugins_from_configuration(capfd):
def test_load_plugins_from_configuration(capfd):
    config = '''
- version: 1

- config:
    plugin_locations: "tests/resources/test_plugins/"

- testplugin3:
    hello: "world3"
    '''

    Milk(arguments=[], config=config)

    out, err = capfd.readouterr()
    assert "hello: world3" in str(out).strip()
