FROM python:3
WORKDIR /astroturf
COPY ./requirements.txt ./
RUN pip install -r requirements.txt
COPY . ./
