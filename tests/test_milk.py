from milk.milk import Milk
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


def test_parsed_create_copy_start_copy_flow():
    config = '''

- argument:
    long_option: --example
    short_option: -e
    dest: example
    default: "hello world"
    required: False

- container: sut
  image: "ubuntu:16.04"

  create:
    command: "sleep 30"
    detach: True

- container: te
  image: "ping"

  copy_to:
    src: "tests/from.txt"
    dest: "/"

  create:
    extra_hosts:
        sut: "{{ sut.inspect.NetworkSettings.IPAddress }}"
        example: 10.0.0.1
    #command: ["ls", "-la", "/tests"]
    command: ["ping", "-c", "5", "sut"]
    working_dir: /

- follow: te

- follow: sut

- copy_from: te
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
