# This is an example worker setup, currently used by the ware-alpine worker.

FROM python:3.6-alpine3.7

ARG WORKER_VERSION=9999
RUN apk update \
	&& apk add --no-cache \
		ca-certificates \
		bzip2-dev \
		coreutils \
		dpkg-dev dpkg \
		expat-dev \
		gcc \
		gdbm-dev \
		git \
		libc-dev \
		libffi-dev \
		libnsl-dev \
		libtirpc-dev \
		linux-headers \
		make \
		ncurses-dev \
		openssl \
		openssl-dev \
		pax-utils \
		readline-dev \
		sqlite-dev \
		tcl-dev \
		tk \
		tk-dev \
		xz-dev \
		zlib-dev \
		xvfb \
	&& update-ca-certificates \
	&& pip install -U pip setuptools wheel --no-cache-dir \
	&& pip install -U "buildbot-worker<=${WORKER_VERSION}" --no-cache-dir \
	&& adduser -h /buildbot -S -D buildbot

USER buildbot
WORKDIR /buildbot
ARG BUILDER_NAME=test-worker
ARG BUILDER_PASS=badsecret
ARG BUILDER_MASTER=localhost:9021
ARG BUILDER_INFO="Alpine Linux 3.7 Docker image"
ARG BUILDER_ADMIN="Somebody who should have set BUILDER_ADMIN"
RUN buildbot-worker create-worker buildarea ${BUILDER_MASTER} ${BUILDER_NAME} ${BUILDER_PASS} \
	&& echo "${BUILDER_INFO}" > buildarea/info/host \
	&& echo "${BUILDER_ADMIN}" > buildarea/info/admin

ENV DISPLAY :99

CMD ["/bin/sh", "-c", "Xvfb $DISPLAY -ac & buildbot-worker start --nodaemon buildarea"]
