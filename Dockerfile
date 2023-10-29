FROM ubuntu:22.04

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-suggests --no-install-recommends build-essential cmake libmysqlclient-dev sox libsox-fmt-mp3 tzdata pkg-config libopenblas-dev && \
    apt-get install -y --no-install-suggests --no-install-recommends python3-dev python3-pip python3-scipy python3-astropy python3-numpy python3-matplotlib python3-openimageio && \
    apt-get autoremove -y && \
    apt-get clean all && \
    rm -rf /var/lib/apt/lists/

WORKDIR /usr/src/sdr-panel
RUN MAKEFLAGS="-j$(nproc)" pip install --no-cache-dir cython ninja
COPY requirements.txt /usr/src/sdr-panel/
RUN MAKEFLAGS="-j$(nproc)" pip install --no-cache-dir -r requirements.txt
COPY . .
COPY entrypoint /entrypoint
RUN python3 manage.py collectstatic --no-input

EXPOSE 8000
