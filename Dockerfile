ARG PYTHON_IMAGE=python:3.9-alpine
FROM $PYTHON_IMAGE
RUN apk add gcc libc-dev
COPY requirements.txt /
RUN pip install -r requirements.txt
COPY . /climux
WORKDIR /climux
CMD ./scripts.py test && ./scripts.py lint
