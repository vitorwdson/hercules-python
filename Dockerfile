# syntax=docker/dockerfile:1
FROM python:3.11-bullseye
WORKDIR /code

# Installing build requirements
RUN apt update
RUN apt upgrade

# Configuring locale and timezones
RUN apt install locales -y
RUN sed -i 's/^# *\(pt_BR\)/\1/' /etc/locale.gen
RUN locale-gen

# Installing project requirements
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copying source files
COPY . .

# Running the application
RUN mkdir ./logs
RUN mkdir ./static
RUN mkdir ./media