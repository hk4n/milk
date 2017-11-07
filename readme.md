**Milk**
====
### *An automation tool for running containers in a non traditional way*

The traditional way to run containers is to have images prepared with everything and just start the containers up with a bare minimum of arguments.

But there are cases where configuration files, test packages etc. needs to get in to the container during create or runtime. This is not that easy to solve without some kind of scripting.

Milk solves this by enables copying of files between the create and start of the container with the help of a simple yaml configuration syntax, see the [Copy](#copy) section for more details.

Now Milk is so much more than just copying files, it has borrowed ideas from other well known provisioning tools and can be used to simplify the task to execute complex test flows within containers, the combinations are endless and it is just your imagination that sets the limits of what Milk can do. You can see the list of supported features in the plugin list below and if there are no plugin that supports your ideas, it is easy to create your own.

## Table of content

- [Requirements](#requirements)
- [Installation](#installation)
- [Basic example](#basic-example)
- [Plugin development](#plugin-development)

#### Plugins
- [Image](#image)
- [Container](#container)
- [Copy](#copy)
- [Follow](#follow)
- [Remove](#remove)
- [Network](#network)
- [Debug](#debug)
- [Variables](#variables)
- [Arguments](#arguments)


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

## Plugin development
The custom plugins that you develop should be placed inside a *plugins* folder in either the working folder of milk or the location of your configuration file.

~~~sh
# this will load both the my_working_dir_plugin and the my_plugin

# /working_dir/plugins
#   my_working_dir_plugin.py

# /working_dir/my_plugin_example/plugins
#   my_plugin.py

$ cd /working_dir/
$ milk -f my_plugin_example/my_config.conf
~~~

#### Simple plugin example
This plugin code will just pretty print the parsed configuration from the supplied configuration file.
~~~python
from milk.plugins import Plugin
from pprint import pprint

class my_plugin(Plugin):
  def __init__(self, config):
    pprint(config)
~~~
configuration file
~~~yaml
- version: 1

- my_plugin:
    my_first_setting: "hello"
    my_second_setting: "world"
~~~

#### Plugin load order and settings
The plugins load order are:
1. Default plugins installed with Milk
2. plugins located in:
~~~
<working dir>/plugins
~~~
3. plugins located in:
~~~
 <config file location>/plugins
~~~
4. plugin_locations configuration in the config file either as a string or as a list. If the location is and relative path it will start from the current working directory.

##### Plugin loading configuration in the config file
~~~yaml
# string version
- version: 1

- config:
    plugin_locations: "my/awesome/plugins/"

~~~
~~~yaml
# list version
- version: 1

- config:
    plugin_locations:
      - "/my/awesome/plugin/"
      - "/my/second/awesome/plugin/"

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
