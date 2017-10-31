**Milk**
====
### *A automation tool for running containers in a non traditional way*

## Table of content

- [Requirements](#requirements)
- [Installation](#installation)
- [Basic example](#basic-example)
- [Image](#image)
 - build example
 - remove example
- [Container](#container)
 - container basics
 - advanced
- Copy
 - Before start
 - From host to container
 - From container to host
 - From container to container
- Follow
- Remove
- Network
 - Create
 - Add to container
 - Remove
- Debug
- Variables
- Arguments
- Jinja2


## Requirements
- python >=2.7.13 or >=3.6.1
- pip >=9.0
- docker >2.12

## Installation
1. Clone the repository

2. Run the pip command bellow from inside the repository folder
~~~
$ pip install .
~~~
3. you are done

## Basic example
Save the content below to test.yml
~~~yaml
- version: 1

- container:
    image: busybox
    name: test
    command: ["echo", "hello world"]

- follow:
  name: test

- remove:
  name: test
~~~
Run the command:
~~~
$ milk -f test.yml
hello world
~~~

## Image
The build plugin support basic building and removal of images.

#### Build example
~~~yaml
- image:
    build:
      tag: "my_awesome/image:1.0"
      dockerfile: ./path/to/Dockerfile
      path: ./path/to/
~~~

#### Remove example
~~~yaml
- image:
    remove: "my_awesome/image:1.0"
    noprune: False
    force: True
~~~

## Container
The container plugin has four regular config options where two is mandatory. The advanced section is a direct translation of the [dockerpy](https://docker-py.readthedocs.io/en/stable/) clients create functions arguments but few are tested, see the [advanced](#advanced) section for more information.
- **name:** name of container inside milk, mandatory
- **image:** name of image, mandatory
- **command:** command to execute, does not override entrypoint settings, optional
- **detach:** set to True to have the container run in detached mode

See the [basic example](#basic-example) how to start a simple container.

#### Advanced
There are few settings that are tested, network, working_dir and extra_hosts.
All other arguemnts from [dockerpy](https://docker-py.readthedocs.io/en/stable/) clients create function can work if properly translated to yaml.

**network**

~~~yaml
- container:
  advanced:
    network: my_network
~~~

**working_dir**

~~~yaml
- container:
  advanced:
    working_dir: /container/folder
~~~

**extra_hosts**

The extra_hosts settings is built up by a yaml list of *ip:hostname*, see example below.

~~~yaml
- container:
  advanced:
    extra_hosts:
      - "192.168.0.1:www.myawesomesite.com"
      - "192.168.0.2:helloworld"
~~~


## Copy
The copy plugin supports copying between host and container or container to container.

Basic regular expression are supported when coping from host to container. The syntax is the same as py36 glob module.
~~~yaml
copy:
  src: /tmp/**/*
  dest: /path/on/dest/
~~~

#### Before start
This will copy from the host to a container before the container have started
~~~yaml
- container:
    image: busybox
    name: test
    copy:
      src: folder/file
      dest: folder/file
~~~

#### From host to container
~~~yaml
- copy:
    src: folder/file
    dest: id:folder/file
~~~

#### From container to host
~~~yaml
- copy:
    src: id:folder/file
    dest: folder/file
~~~

#### From container to container
~~~yaml
- copy:
    src: id1:folder/file
    dest: id2:folder/file
~~~

## Follow
Follow is like tail -f on the containers stdout. You can only follow one container at the time.

~~~yaml
- follow:
    name: mycontainer
~~~

## Remove
Remove is used to remove an container after or when it is running, You can use the force option to forcefully kill and remove and running container.  

~~~yaml
- remove:
    name: mycontainer
    force: True
~~~

## Network
The network plugin is used to create and remove networks. You can specify advanced options but they are right now untested.

#### Create
~~~yaml
- network:
    create:
      name: my_network
      driver: bridge
~~~
#### Add to container
~~~yaml
- container:
    advanced:
      network: my_network
~~~

#### Remove
~~~yaml
- network:
    remove:
      name: my_network
~~~

## Debug
Debug is used to print various texts and variable content to stdout
There are two types of debug settings:
#### variable
- **pretty:** Tries to format the variables data.
- **verbose:** Writes the variables data type.

~~~yaml
- debug:
    variable: myvar

- debug:
    variable: myvar
    pretty: True

- debug:
    variable: myvar
    verbose: True

~~~
#### text

~~~yaml
- debug:
    text: "My awesome debug text printout"
~~~

## Variables
Variables are used feed other plugins with information with the use the [Jinja2](http://jinja.pocoo.org/docs/2.9/templates/) format. The Jinja parsing are executed per plugin configuration, so make sure you order the configuration correctly.

~~~yaml
- variables:
    myvar1: "First variable text"
    myvar2: "Second variable text"

- debug:
    text: "{{ myvar1 }}"
~~~

## Arguments
The argument plugin provides the support to have custom arguments to configuration. The values from these arguments are stored in the same way as the in the variables plugin.

The arguments are taken care of before the parsing and execution of the other plugins and it doesn't matter where in the config file they are located, but for readability having them in the top of the file helps.

- **long_option:** conditional optional when short_option is used.
- **short_option:** conditional optional when long_option is used.
- **dest:** optional
- **default:** optional
- **required:** optional

~~~yaml
- argument:
    long_option: --example
    short_option: -e
    dest: example
    default: "hello world"
    required: False

- debug:
    text: "{{ example }}"
~~~

~~~
$ milk -f myexample.conf --example
hello world
$ milk -f myexample.conf --example 'hello universe'
hello universe
~~~
