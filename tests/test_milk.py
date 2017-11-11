from milk.milk import Milk
from milk.milk import MilkExceptions

import os
import sys
import pytest
import mock

# to disable tests use this:
# @pytest.mark.skip(reason="no way of currently testing this")


def test_supress(capfd):
    config = '''
- version: 1

- debug:
    '''

    Milk(arguments=[], config=config, exceptions=MilkExceptions.supress)

    out, err = capfd.readouterr()
    assert "missing options 'variable' or 'text'" in err


def test_no_config_file(capfd):

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        Milk(arguments=["config", "mini.conf"], exceptions=MilkExceptions.supress)
        assert pytest_wrapped_e.value.code == 1

    out, err = capfd.readouterr()
    assert "No config file found" in out


def test_io_error_config_file_branch(capfd):

    if sys.version_info.major < 3:
        open_name = '__builtin__.open'
    else:
        open_name = 'builtins.open'

    with mock.patch(open_name) as mock_open:
        mock_open.side_effect = IOError("Mocked open IOError")
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            filename = os.path.join(os.getcwd(), "tests/mini_debug.conf")
            Milk(arguments=["--config", filename])
            assert pytest_wrapped_e.value.code == 1
    out, err = capfd.readouterr()
    assert "Mocked open IOError" in out


def test_config_file(capfd):

    filename = os.path.join(os.getcwd(), "tests/mini_debug.conf")

    Milk(arguments=["--config", filename])

    out, err = capfd.readouterr()
    assert "hello world" in out


def test_create_assign_remove_network(capfd):
    config = '''
- version: 1

- network:
    create: my_network
    driver: bridge

- container:
    id: test
    image: ping
    command: "sleep 300"
    detach: True

    advanced:
        network: my_network

- debug:
    text: "<test>{{ test.inspect.NetworkSettings.Networks.my_network.Gateway }}</test>"

- container:
    id: test1
    image: ping
    command: "sleep 300"
    detach: True

    advanced:
        network: my_network

- debug:
    text: "<test1>{{ test1.inspect.NetworkSettings.Networks.my_network.Gateway }}</test1>"

- remove:
    id: test
    force: true

- remove:
    id: test1
    force: true

- network:
    remove: my_network
    '''

    Milk(arguments=[], config=config)
    out, err = capfd.readouterr()

    import re
    test = re.search('<test>(.+)</test>', out).group(1)
    test1 = re.search('<test1>(.+)</test1>', out).group(1)

    assert test == test1


def test_build_image(capfd):
    config = '''
- version: 1

- image:
    build:
      tag: "ping:test_version"
      dockerfile: ./tests/Dockerfile.ping
      path: ./tests/

- container:
    id: buildtest
    image: "ping:test_version"
    command: ["ping", "-c", "5", "localhost"]

- follow:
    id: buildtest

- remove:
    id: buildtest

- image:
    remove: "ping:test_version"
    noprune: False
    force: True
    '''

    Milk(arguments=[], config=config)
    out, err = capfd.readouterr()


def test_version_config(capfd):
    config = '''
- version: 1

- debug:
    text: "{{ milk.config.version }}"
    '''

    Milk(arguments=[], config=config)
    out, err = capfd.readouterr()
    assert out == "1\n"


def test_copy_from_host_to_from_from_to_to_to_to_host():
    config = '''
- version: 1

- container:
    id: to
    image: "ping"
    command: "sleep 300"
    detach: True

- container:
    id: from
    image: "ping"
    command: "sleep 300"
    detach: True

    copy:
      src: tests/from.*
      dest: /tmp/

- copy:
    src: from:/tmp/from.txt
    dest: to:/tmp/

- copy:
    src: to:/tmp/from.txt
    dest: /tmp/tests/from_to.txt

- remove:
    id: from
    force: True

- remove:
    id: to
    force: True

    '''

    Milk(arguments=[], config=config)

    assert os.path.isfile("/tmp/tests/from_to.txt")

    # compare file content
    import filecmp
    assert filecmp.cmp("/tmp/tests/from_to.txt", "tests/from.txt", shallow=False)


def test_short_arguments(capfd):
    config = '''
- version: 1

- argument:
    short_option: -z
    dest: zeta

- debug:
    text: "{{ zeta }}"
    '''

    Milk(arguments=["-z", "olle"], config=config)
    out, err = capfd.readouterr()
    assert out == "olle\n"


def test_long_arguments(capfd):
    config = '''
- version: 1

- argument:
    long_option: --zeta
    dest: zeta

- debug:
    text: "{{ zeta }}"
    '''

    Milk(arguments=["--zeta", "nisse"], config=config)
    out, err = capfd.readouterr()
    assert out == "nisse\n"


def test_variables(capfd):
    config = '''
- version: 1

- variables:
    banan: olle

- debug:
    text: "{{ banan }}"
    '''

    Milk(arguments=[], config=config)
    out, err = capfd.readouterr()
    assert out == "olle\n"


def test_ping_from_container(capfd):
    config = '''
- version: 1
- argument:
    long_option: --example
    short_option: -e
    dest: example
    default: "hello world"
    required: False

- container:
    id: to
    image: "ping"
    command: "sleep 30"
    detach: True

- container:
    id: from
    image: "ping"
    command: ["ping", "-c", "5", "to"]

    advanced:
      extra_hosts:
          to: "{{ to.inspect.NetworkSettings.IPAddress }}"
          example: "{{ example }}"
      working_dir: /

- follow:
    id: from

- remove:
    id: from

- remove:
    id: to
    force: True
    '''
    Milk(arguments=["--example", "10.0.0.1"], config=config)

    out, err = capfd.readouterr()
    assert "5 packets transmitted, 5 packets received, 0% packet loss" in out


def test_copy_single_file_from_container(capfd):
    config = '''
- version: 1
- container:
    id: test
    image: ping
    command: 'ls -la /tmp/'
    copy:
      src: tests/from.*
      dest: /tmp

- follow:
    id: test

- copy:
    src: test:/tmp/from.txt
    dest: /tmp/tests/tmp/test.txt

- remove:
    id: test

    '''

    Milk(arguments=[], config=config)

    out, err = capfd.readouterr()

    # check if the file was copied to the container
    assert "from.txt" in out

    # compare file content
    import filecmp
    assert filecmp.cmp("/tmp/tests/tmp/test.txt", "tests/from.txt", shallow=False)


def test_always_pull_image_before_create(capfd):
    config = '''
- version: 1

- container:
    id: test
    image: 'busybox:1.27.2'
    command: 'echo hello world'
    pull: always

- follow:
    id: test

- remove:
    id: test

- image:
    remove: 'busybox:1.27.2'
    '''

    Milk(arguments=[], config=config)

    out, err = capfd.readouterr()

    # check if the file was copied to the container
    assert "hello world" in out


def test_auto_pull_image_before_create(capfd):
    config = '''
- version: 1

- container:
    id: test
    image: 'busybox:1.27.2'
    command: 'echo hello world'

- follow:
    id: test

- remove:
    id: test

- image:
    remove: 'busybox:1.27.2'
    '''

    Milk(arguments=[], config=config)

    out, err = capfd.readouterr()

    # check if the file was copied to the container
    assert "hello world" in out


def test_disabled_pull_image_before_create(capfd):
    config = '''
- version: 1

- container:
    id: test
    image: 'ping'
    command: 'echo hello world'
    pull: disabled

- follow:
    id: test

- remove:
    id: test
    '''

    Milk(arguments=[], config=config)

    out, err = capfd.readouterr()

    # check if the file was copied to the container
    assert "hello world" in out
