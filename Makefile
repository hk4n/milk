DOCKER := $(shell which docker)
IMAGE := ${USER}-milk-test
RUN := $(DOCKER) run -it --rm

all: build test

build:
	$(DOCKER) build -t ${IMAGE} .

test: build
	$(RUN) -v /var/run/docker.sock:/var/run/docker.sock $(IMAGE) -e py36

console: build
	$(RUN) -v /var/run/docker.sock:/var/run/docker.sock --entrypoint /bin/bash $(IMAGE)

pep8: build
	$(RUN) $(IMAGE) -e flake8

clean:
	$(DOCKER) rmi -f $(IMAGE)
	$(DOCKER) rmi -f $(EXAMPLEIMAGE)

.PHONY: all build test
