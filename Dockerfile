FROM ubuntu:latest
LABEL authors="alper"

ENTRYPOINT ["top", "-b"]