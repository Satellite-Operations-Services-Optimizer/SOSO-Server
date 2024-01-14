# Tutorial for setting up python flask project on Docker for reference:
# https://blog.logrocket.com/build-deploy-flask-app-using-docker/


# start by pulling the python image
FROM python:3.11-alpine

ARG SERVICE_NAME=GroundStationOutboundService

# install git on container
RUN apk update
RUN apk add git

RUN pip install --upgrade pip

# copy the base requirements file for all services, and install it
COPY ./requirements.txt ./code/base-requirements.txt
RUN pip install -r ./code/base-requirements.txt

# copy requirements file for the service if it exists, and install it (the [s] is a hack to make it do nothing if the file doesn't exist, rather than throw an error)
COPY ./${SERVICE_NAME}/requirement[s].txt ./code/requirements.txt
RUN if [ -f ./code/requirements.txt ]; then pip install -r ./code/requirements.txt; fi

# setup app configuration code
COPY ./app_config ./code/app_config
RUN python /code/app_config/scripts/add_config_to_python_path.py

# copy every relevant content from the host machine to the image
COPY ./${SERVICE_NAME} ./code/${SERVICE_NAME}

WORKDIR /code/${SERVICE_NAME}
CMD ["python", "main.py"]