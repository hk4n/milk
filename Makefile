DOCKER := $(shell which docker)
IMAGE := ${USER}-milk-test
RUN := $(DOCKER) run -it --rm

all: build test

build:
	$(DOCKER) build -t ${IMAGE} .

buildping:
	$(DOCKER) build -t ping:latest -f tests/Dockerfile.ping .


test: build buildping
	$(RUN) -v /var/run/docker.sock:/var/run/docker.sock $(IMAGE)

console: build buildping
	$(RUN) -v /var/run/docker.sock:/var/run/docker.sock --entrypoint /bin/bash $(IMAGE)

pep8: build
	$(RUN) $(IMAGE) -e flake8

clean:
	$(DOCKER) rmi -f $(IMAGE)
	$(DOCKER) rmi -f $(EXAMPLEIMAGE)

.PHONY: all build test
