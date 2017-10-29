from milk.plugin import Plugin
import docker
import tarfile
import io
import time
import os
import logging
import tempfile


class container(Plugin):
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
        self.add_global(self.name, self)

        if "copy" in config:
            if ':' in config["copy"]["dest"]:
                raise Exception("Currently container copy is only supported in src")

            if ':' not in config["copy"]["dest"]:
                config["copy"]["dest"] = "%s:%s" % (self.name, config["copy"]["dest"])

            copy(config["copy"])

        self.start()

        # wait for ipadress to be assigned
        self.inspect = self.containerObject.attrs
        network = None
        try:
            network = config["advanced"]["network"]
        except KeyError:
            pass

        while self.getIPAdress(network) == '':
            self.containerObject.reload()
            self.inspect = self.containerObject.attrs

    def getIPAdress(self, network):
        if network:
            return self.inspect["NetworkSettings"]["Networks"][network]["IPAddress"]

        return self.inspect["NetworkSettings"]["IPAddress"]

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

        if self.get_global("milk")["config"]["version"] >= 1:
            # copy between containers support here

            # parse src
            srcContainer = ""
            src = config["src"]
            if ":" in src:
                srcContainer, src = src.split(":")

            # parse dest
            destContainer = ""
            dest = config["dest"]
            if ":" in dest:
                destContainer, dest = dest.split(":")

            if srcContainer and destContainer:
                # copy between containers
                srcContainerObject = self.milkglobals[srcContainer].containerObject
                destContainerObject = self.milkglobals[destContainer].containerObject

                tmpSrcPath = tempfile.mkdtemp()

                if src.startswith("/"):
                    newsrc = src[1:]

                newdest = os.path.dirname(os.path.join(tmpSrcPath, newsrc)) + "/"

                self.copy_from(srcContainerObject, src, newdest)

                newsrc = os.path.join(tmpSrcPath, newsrc)

                self.copy_to(destContainerObject, newsrc, dest)

                import shutil
                shutil.rmtree(tmpSrcPath)

            elif srcContainer:
                # copy from container to host
                srcContainerObject = self.milkglobals[srcContainer].containerObject

                self.copy_from(srcContainerObject, src, dest)

            elif destContainer:
                # copy from host to container
                destContainerObject = self.milkglobals[destContainer].containerObject

                self.copy_to(destContainerObject, src, dest)

            else:
                raise Exception("You cant right now copy host to host")

    # TODO! implement exclude and regexp copy
    # TODO! implement support to copy from one container into another with syntax from id1:src to id2:dest
    def copy_from(self, containerObject, src, dest):

        response, info = containerObject.get_archive(src)

        tarinfo = tarfile.TarInfo(info['name'])
        tarinfo.size = info['size']
        tarinfo.mode = info['mode']
        tarinfo.mtime = info['mtime']

        tar = tarfile.TarFile(fileobj=io.BytesIO(response.data), tarinfo=tarinfo)

        path = os.path.dirname(dest)

        # make sure the destination folders exists
        if not os.path.isdir(path):
            os.makedirs(path)

        # extract the file/files
        if dest.endswith("/"):
            logging.debug("copy_from isdir: extracts whole tar to dest")
            tar.extractall(path=dest)
        else:
            logging.debug("copy_from: %s to %s" % (src, dest))

            # the extractfile and extract functions in tarfile does not work properly,
            # so for now we use extractall and rename the file afterwards

            tmpdest = tempfile.mkdtemp()
            destsrc = os.path.join(tmpdest, os.path.basename(src))

            tar.extractall(path=tmpdest)
            os.rename(destsrc, dest)

            import shutil
            shutil.rmtree(tmpdest)

    # TODO!, implement exclude
    # TODO! implement support to copy from one container into containerObject with syntax from id1:src to dest
    @staticmethod
    def copy_to(containerObject, src, dest):
        path = "/"

        def create_archive(src, dest):

            sourcefiles = []

            # add wildcard string to src string if identified as a directory
            if os.path.isdir(src):
                src = os.path.join(src, "**/*")

            import glob2
            tmpfiles = glob2.glob(src, recursive=True)
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
