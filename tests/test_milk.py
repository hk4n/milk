from milk.milk import Milk
import pytest
import sys

# def test_run_container():

#     config = '''
# - container: sut
#   run:
#     image: "hello-world"
#     '''
#
#     m = Milk(config)
#
#     # mc = MilkDocker()
#     # mc.run(**m.parsed[0]["run"])

# def test_printpwd():
#     import os
#     print(os.getcwd())
#
#


def test_variables(capfd):
    config = '''
- version: 1

- argument:
    long_option: --hello
    dest: hello

- argument:
    long_option: --world
    dest: world

- variables:
    banan: olle

- debug:
    text: "{{ banan }}"
    '''

    Milk(arguments=["--hello", "apa", "--world", "nisse"], config=config)
    out, err = capfd.readouterr()
    assert out == "olle\n"


# @pytest.mark.skip(reason="no way of currently testing this")
def test_parsed_create_copy_start_copy_flow():
    config = '''
- version: 1
- argument:
    long_option: --example
    short_option: -e
    dest: example
    default: "hello world"
    required: False

- container:
    name: sut
    image: "ubuntu:16.04"
    command: "sleep 30"
    detach: True

- container:
    name: te
    image: "ping"
    command: ["ping", "-c", "5", "sut"]

    copy:
      src: "tests/from.txt"
      dest: "/"

    advanced:
      extra_hosts:
          sut: "{{ sut.inspect.NetworkSettings.IPAddress }}"
          example: 10.0.0.1
      #command: ["ls", "-la", "/tests"]
      working_dir: /

- follow:
    name: te

- follow:
    name: sut

- copy:
    name: te
    src: "/tests/from.txt"
    dest: "tests/banan.txt"

- remove:
    name: te

- remove:
    name: sut
    force: True
    '''
    Milk(arguments=["--example", "banan"], config=config)

    with open("tests/banan.txt", "r") as f:
        for line in f:
            sys.stdout.write(line)
            sys.stdout.flush()


@pytest.mark.skip(reason="no way of currently testing this")
def test_copy_from_single_file():
    config = '''

- container: test
  image: ping
  create:
    command: 'ls -la /tmp/tests'
  copy_to:
    src: tests/
    dest: /tmp

- follow: test

- copy_from: test
  src: /tmp/tests/from.txt
  dest: tests/tmp/test.txt

- remove:
  name: test

    '''

    Milk(arguments=[], config=config)

    with open("tests/tmp/test.txt", "r") as f:
        for line in f:
            sys.stdout.write(line)
            sys.stdout.flush()
