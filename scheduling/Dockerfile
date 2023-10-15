# Tutorial for setting up python flask project on Docker for reference:
# https://blog.logrocket.com/build-deploy-flask-app-using-docker/

# start by pulling the python image
FROM python:3.11-alpine

# copy the requriements file into the image
COPY ./requirements.txt /code/requirements.txt

# install the dependencies and packages in the requirements file
RUN pip install -r requirements.txt

# copy every content from the local file to the image
COPY . /code

CMD [ "uvicorn", "code.main:app", "--host", "0.0.0.0", "--port", "5000" ]
