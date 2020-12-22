FROM pytorch/pytorch:1.6.0-cuda10.1-cudnn7-runtime
WORKDIR /astroturf

COPY ./requirements.txt ./
RUN pip install -r requirements.txt

COPY ./requirements-dev.txt ./
RUN pip install -r requirements-dev.txt

COPY . /astroturf

ENV GOOGLE_APPLICATION_CREDENTIALS="astroturf-update.json"
