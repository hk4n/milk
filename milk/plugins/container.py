from milk.milktemplate import MilkTemplate
from milk.plugin import Plugin
import docker
import tarfile
import io
import time
import os
import logging


class container(Plugin):
    live_containers = {}
    client = None

    def __init__(self, config):
        if self.client is None:
            self.client = docker.from_env(version='auto')

        self.name = config["container"]

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
            logging.debug("running container detached!")

        self.client.containers.run(image, command, **kwargs)

    def start(self):
        return self.containerObject.start()

    def create(self, image, command, **kwargs):

        if "extra_hosts" in kwargs:
            for key, value in dict(kwargs["extra_hosts"]).items():
                    template = MilkTemplate()
                    kwargs["extra_hosts"][key] = template.render(value)

        return self.client.containers.create(image, command, **kwargs)

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


class follow(Plugin):
    def __init__(self, config):
        self.follow(config["follow"])

    def follow(self, name):
        import sys
        for line in self.milkglobals[name].containerObject.logs(stream=True, follow=True):
            sys.stdout.writelines(line.decode("utf-8"))
            sys.stdout.flush()


class remove(Plugin):
    def __init__(self, config):
        self.remove(config)

    def remove(self, config):
        if type(config) is dict:
            name = config["name"]
            logging.debug("removing: %s" % name)
            del config["name"]
            del config["remove"]
            return self.milkglobals[name].containerObject.remove(**config)


class copy_from(Plugin):
    def __init__(self, config):
        self.copy_from(config)

    # todo, implement exclude and regexp copy
    def copy_from(self, config):
        name = config["copy_from"]
        src = config["src"]
        dest = config["dest"]

        response, info = self.milkglobals[name].containerObject.get_archive(src)

        tarinfo = tarfile.TarInfo(info['name'])
        tarinfo.size = info['size']
        tarinfo.mtime = info['mtime']
        tarinfo.mode = info['mode']

        tar = tarfile.TarFile(fileobj=io.BytesIO(response.data), tarinfo=tarinfo)

        if dest.endswith("/"):
            logging.debug("copy_from isdir")
            tar.extractall(path=dest)
        else:
            logging.debug("copy_from: %s to %s" % (src, dest))

            path = os.path.dirname(dest)
            if not os.path.isdir(path):
                os.makedirs(path)

            fs = tar.extractfile(tarinfo)
            with open(dest, "wb") as f:
                f.write(fs.read())
