FROM ubuntu:16.04

ENV PYENV_ROOT $HOME/.pyenv
ENV PATH $HOME/.pyenv/shims:$HOME/.pyenv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

RUN apt-get update && \
    apt-get install -y \
        make \
        git \
        build-essential \
        libssl-dev \
        zlib1g-dev \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        wget \
        curl \
        llvm \
        libncurses5-dev \
        libncursesw5-dev \
        xz-utils

RUN curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash

ENV PY27 2.7.13
ENV PY36 3.6.1

RUN pyenv install ${PY27}
RUN pyenv install ${PY36}

COPY test_requirements.txt /
COPY requirements.txt /

RUN pyenv local ${PY27} \
    && pip install --upgrade \
        setuptools \
        pip \
        tox \
    && pip install -r /test_requirements.txt \
    && pip install -r /requirements.txt \
    && pyenv local --unset

RUN pyenv local ${PY36} \
    && pip install --upgrade \
        setuptools \
        pip \
        tox \
    && pip install -r /test_requirements.txt \
    && pip install -r /requirements.txt \
    && pyenv local --unset


RUN pyenv local ${PY27} ${PY36}

WORKDIR /src
COPY . /src

ENTRYPOINT ["tox", "-v"]
