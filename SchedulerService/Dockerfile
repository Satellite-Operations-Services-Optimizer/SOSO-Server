# Tutorial for setting up python flask project on Docker for reference:
# https://blog.logrocket.com/build-deploy-flask-app-using-docker/

# start by pulling the python image
FROM python:3.11-alpine

# install git on container
RUN apk update
RUN apk add git

RUN pip install --upgrade pip

WORKDIR /code

# copy the base requirements file for all services, and install it
COPY ./requirements.txt base-requirements.txt
RUN pip install -r base-requirements.txt

# copy requirements file for the service if it exists, and install it
COPY ./SchedulerService/requirement[s].txt requirements.txt
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# copy every content from the local file to the image
COPY ./SchedulerService/ .

CMD ["python", "main.py"] 
