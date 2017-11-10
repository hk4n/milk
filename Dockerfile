FROM hk4n/toxbase:latest

COPY test_requirements.txt /
COPY requirements.txt /

RUN pyenv local ${PY27} \
    && pip install -r /test_requirements.txt \
    && pip install -r /requirements.txt \
    && pyenv local --unset

RUN pyenv local ${PY36} \
    && pip install -r /test_requirements.txt \
    && pip install -r /requirements.txt \
    && pyenv local --unset


RUN pyenv local ${PY27} ${PY36}

WORKDIR /src
COPY . /src

ENTRYPOINT ["tox", "-v"]
