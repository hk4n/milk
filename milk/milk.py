import yaml
import docker
import tarfile
import io
import time
import argparse
import os


class MilkGlobal:
    g = {}
    pass


# this is the global placeholder for all parsed arguments and running container intances
milkglobals = MilkGlobal()


class MilkBase:

    def add_global(self, key, value):
            global milkglobals

            if key in milkglobals.g:
                raise Exception("Key '%s' already exists, overwriting is not an option!")

            milkglobals.g[key] = value

    def items(self):
        return milkglobals.g.items()


class MilkTemplate(MilkBase):

    def render(self, value):
        from jinja2 import Template

        template = Template(value)

        # init globals
        for k, v in self.items():
            template.globals[k] = v

        return template.render()


class MilkArguments(MilkBase):

    def __init__(self, arguments=None):
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument("-f", "--config", default="milk.yml", dest="config")

        self.usergroup = self.parser.add_argument_group(description="User defined arguments")

        self.args, self.reminder = self.parser.parse_known_args(args=arguments)

    def add_argument(self, **kwargs):

        option = []

        import pprint
        pprint.pprint(kwargs)

        if "short_option" in kwargs:
            option.append(kwargs["short_option"])
            del kwargs["short_option"]

        if "long_option" in kwargs:
            option.append(kwargs["long_option"])
            del kwargs["long_option"]

        if len(option) == 2:
            self.usergroup.add_argument(option[0], option[1], **kwargs)
        elif len(option) == 1:
            self.usergroup.add_argument(option[0], **kwargs)
        else:
            import pprint
            pprint.pprint(kwargs)
            raise Exception("missing short_option or long_option")

    def parse_args(self):
        args = self.parser.parse_args(self.reminder)

        for key, value in vars(args).items():
            if key == 'config':
                continue

            print("adding '%s':'%s' to global" % (key, value))
            self.add_global(key, value)


class container(MilkBase):
    live_containers = {}
    client = None

    def __init__(self, name):
        if self.client is None:
            self.client = docker.from_env(version='auto')
        self.name = name

    def execute(self, config):
        if "image" not in config:
            raise Exception("'image' is missing")
        if "create" not in config:
            raise Exception("'create' is missing")

        self.containerObject = self.create(config["image"], **config["create"])

        if "copy_to" in config:
            self.copy_to(**config["copy_to"])

        self.start()

        # wait for ipadress to be assigned
        self.inspect = self.containerObject.attrs
        while self.inspect["NetworkSettings"]["IPAddress"] == '':
            self.containerObject.reload()
            self.inspect = self.containerObject.attrs

        # store
        self.live_containers[self.name] = self
        self.add_global(self.name, self)

    def run(self, image, command=None, **kwargs):

        if "detach" in kwargs and kwargs["detach"]:
            print("running container detached!")

        c = self.client.containers.run(image, command, **kwargs)
        print(type(c))

    def start(self):
        return self.containerObject.start()

    def create(self, image, command, **kwargs):

        if "extra_hosts" in kwargs:
            for key, value in dict(kwargs["extra_hosts"]).items():
                    template = MilkTemplate()
                    kwargs["extra_hosts"][key] = template.render(value)

        return self.client.containers.create(image, command, **kwargs)

    def remove(self, config):
        if type(config) is dict:
            name = config["name"]
            print("removing: %s" % name)
            del config["name"]
            del config["remove"]
            return self.live_containers[name].containerObject.remove(**config)

    # todo, implement exclude and regexp copy
    def copy_from(self, config):
        name = config["copy_from"]
        src = config["src"]
        dest = config["dest"]

        response, info = self.live_containers[name].containerObject.get_archive(src)

        tarinfo = tarfile.TarInfo(info['name'])
        tarinfo.size = info['size']
        tarinfo.mtime = info['mtime']
        tarinfo.mode = info['mode']

        tar = tarfile.TarFile(fileobj=io.BytesIO(response.data), tarinfo=tarinfo)

        if dest.endswith("/"):
            print("copy_from isdir")
            tar.extractall(path=dest)
        else:
            print("copy_from: %s to %s" % (src, dest))

            path = os.path.dirname(dest)
            if not os.path.isdir(path):
                os.makedirs(path)

            fs = tar.extractfile(tarinfo)
            with open(dest, "wb") as f:
                f.write(fs.read())

    # this will only copy one file at a time
    # there are two reasons for that, one is to try not to run out of memory
    # the other is that I'm lazy and didnt implement the copy of folders
    #
    # todo, implement exclude ,regexp copy and copy of folders
    # the file mode is not preserved, this needs to be fixed
    def copy_to(self, src, dest):
        path = "/"

        def create_archive(src, dest):

            if os.path.isdir(src):
                sourcefiles = []

                def recurse_dir(src, sf=[]):
                    from os import listdir
                    from os.path import isfile, join, isdir

                    for f in listdir(src):
                        if isfile(join(src, f)):
                            sf += [join(src, f)]
                        elif isdir(join(src, f)):
                            sf += recurse_dir(join(src, f), sf)

                    return sf

                sourcefiles = recurse_dir(src)

            else:
                sourcefiles = [src]

            tarstream = io.BytesIO()
            tar = tarfile.TarFile(fileobj=tarstream, mode='w')

            for source in sourcefiles:
                with open(source, 'rb') as f:
                    file_data = f.read()

                    tarinfo = tarfile.TarInfo(name=os.path.join(dest, source))
                    tarinfo.size = len(file_data)
                    tarinfo.mtime = time.time()

                    # calculate file mode
                    mode = oct(os.stat(source).st_mode & int('777', 8))
                    tarinfo.mode = int(mode, 8)

                    tar.addfile(tarinfo, io.BytesIO(file_data))

            # close the tar object and rewind the stream
            tar.close()
            tarstream.seek(0)
            return tarstream

        with create_archive(src, dest) as archive:
            self.containerObject.put_archive(path=path, data=archive)

    def follow(self, name):
        import sys
        for line in self.live_containers[name].containerObject.logs(stream=True, follow=True):
            sys.stdout.writelines(line.decode("utf-8"))
            sys.stdout.flush()


class Milk:
    def __init__(self, arguments=None, config=None):

        parser = MilkArguments(arguments=arguments)

        if config:
            self.parsed = yaml.load(config)
        else:
            with open(parser.args.config, "r") as f:
                self.parsed = yaml.load(f.read())

        # debug print
        import pprint
        print("\n")
        pprint.pprint(self.parsed)

        # parse arguments
        i = 0
        for item in list(self.parsed):
            if "argument" in item:
                parser.add_argument(**item["argument"])
                i += 1

        # parse user defined arguments
        parser.parse_args()

        # parse container flow
        for item in self.parsed:
            if "container" in item:
                c = container(item["container"])
                c.execute(item)

            if "follow" in item:
                container('tmp').follow(item["follow"])

            if "remove" in item:
                container('tmp').remove(item)

            if "copy_from" in item:
                container('tmp').copy_from(item)
