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

        self.name = config["name"]

        if "image" not in config:
            raise Exception("'image' is missing")

        if "advanced" not in config:
            config["advanced"] = {}

        # adding optional settings to advanced
        for arg in ["command", "detach"]:
            if arg in config:
                config["advanced"][arg] = config[arg]

        # create the container
        self.containerObject = self.create(config["image"], **config["advanced"])

        if "copy" in config:
            copy.copy_to(self.containerObject, **config["copy"])

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
        return self.client.containers.create(image, command, **kwargs)


class follow(Plugin):
    def __init__(self, config):
        self.follow(config["name"])

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
            return self.milkglobals[name].containerObject.remove(**config)


class copy(Plugin):
    def __init__(self, config):
        self.copy_from(config)

    # TODO! implement exclude and regexp copy
    # TODO! implement support to copy from one container into another with syntax from id1:src to id2:dest
    def copy_from(self, config):
        name = config["name"]
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

    # TODO!, implement exclude
    # TODO! implement support to copy from one container into containerObject with syntax from id1:src to dest
    def copy_to(containerObject, src, dest):
        path = "/"

        def create_archive(src, dest):

            sourcefiles = []

            # add wildcard string to src string if identified as a directory
            if os.path.isdir(src):
                src = os.path.join(src, "**/*")

            import glob
            tmpfiles = glob.glob(src, recursive=True)
            for source in tmpfiles:
                if os.path.isdir(source):
                    continue
                else:
                    sourcefiles += [source]

            tarstream = io.BytesIO()
            tar = tarfile.TarFile(fileobj=tarstream, mode='w')

            for source in sourcefiles:

                # make sure we do not add the "basename" from src to the tar content
                stripme = src.split(os.path.basename(src))[0]

                with open(source, 'rb') as f:
                    file_data = f.read()

                    tarinfo = tarfile.TarInfo(name=os.path.join(dest, source[len(stripme):]))
                    tarinfo.size = len(file_data)
                    tarinfo.mtime = time.time()

                    # preserv file mode
                    mode = oct(os.stat(source).st_mode & int('777', 8))
                    tarinfo.mode = int(mode, 8)

                    tar.addfile(tarinfo, io.BytesIO(file_data))

            # close the tar object and rewind the stream
            tar.close()
            tarstream.seek(0)
            return tarstream

        with create_archive(src, dest) as archive:
            containerObject.put_archive(path=path, data=archive)
