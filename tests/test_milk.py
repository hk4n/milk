from milk.milk import Milk

import os

# to disable tests use this:
# import pytest
# @pytest.mark.skip(reason="no way of currently testing this")


def test_build_image():
    config = '''
- version: 1

- image:
    build:
      tag: "ping:test_version"
      dockerfile: ./tests/Dockerfile.ping
      path: ./tests/

- container:
    name: buildtest
    image: "ping:test_version"
    command: ["ping", "-c", "5", "localhost"]

- follow:
    name: buildtest

- remove:
    name: buildtest

- image:
    remove: "ping:test_version"
    '''

    Milk(arguments=[], config=config)


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
    name: to
    image: "ubuntu:16.04"
    command: "sleep 300"
    detach: True

- container:
    name: from
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
    dest: tests/from_to.txt

- remove:
    name: from
    force: True

- remove:
    name: to
    force: True

    '''

    Milk(arguments=[], config=config)

    assert os.path.isfile("tests/from_to.txt")

    # compare file content
    import filecmp
    assert filecmp.cmp("tests/from_to.txt", "tests/from.txt", shallow=False)


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
    name: to
    image: "ubuntu:16.04"
    command: "sleep 30"
    detach: True

- container:
    name: from
    image: "ping"
    command: ["ping", "-c", "5", "to"]

    advanced:
      extra_hosts:
          to: "{{ to.inspect.NetworkSettings.IPAddress }}"
          example: "{{ example }}"
      working_dir: /

- follow:
    name: from

- remove:
    name: from

- remove:
    name: to
    force: True
    '''
    Milk(arguments=["--example", "10.0.0.1"], config=config)

    out, err = capfd.readouterr()
    assert "5 packets transmitted, 5 packets received, 0% packet loss" in out


def test_copy_single_file_from_container(capfd):
    config = '''
- version: 1
- container:
    name: test
    image: ping
    command: 'ls -la /tmp/'
    copy:
      src: tests/from.*
      dest: /tmp

- follow:
    name: test

- copy:
    src: test:/tmp/from.txt
    dest: tests/tmp/test.txt

- remove:
    name: test

    '''

    Milk(arguments=[], config=config)

    out, err = capfd.readouterr()

    # check if the file was copied to the container
    assert "from.txt" in out

    # compare file content
    import filecmp
    assert filecmp.cmp("tests/tmp/test.txt", "tests/from.txt", shallow=False)
