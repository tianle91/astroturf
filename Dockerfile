FROM python:3.7
WORKDIR /astroturf

COPY ./requirements.txt ./
RUN pip install -r requirements.txt

COPY ./requirements-dev.txt ./
RUN pip install -r requirements-dev.txt

COPY . ./
