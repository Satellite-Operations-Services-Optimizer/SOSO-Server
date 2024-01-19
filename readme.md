# SOSO - Server

This repository stores the backend functionalities of Satellite Operation Services Optimizer

## Prerequisites

Before you begin, ensure you have met the following requirements:

* You have installed Python v3.11. You can download it [here](https://www.python.org/downloads/).
* You have installed pip (Comes installed with Python by default).

## Setting Up RabbitMQ

You need to set up a RabbitMQ server. This can be done in one of three ways:

1. Setting it up on your local machine. Follow the instructions [here](https://www.rabbitmq.com/download.html).
2. Using a Docker container. Instructions can be found [here](https://hub.docker.com/_/rabbitmq).
3. Using a cloud-based service.

After setting up RabbitMQ, ensure you configure the RabbitMQ settings according to your environment.

## Running the EventRelayAPI 

Follow these steps to run the EventRelayAPI:

1. Open a command prompt and navigate to the directory containing `main.py`.
2. Run the following command: python -m uvicorn main:app --port 1527 --reload


## Running Other Services

To run any other services: 

1. Open a command prompt and navigate to the directory with the desired project's `main.py` file.
2. Run the following command: python main.py

## Installing Required Python Packages

To install all the required Python packages, follow these steps:

1. Open a command prompt and navigate to the directory containing `requirements.txt`.
2. Run the following command: pip install -r requirements.txt

3. If one or more packages fail to install, you can attempt to install them individually with: pip install <package_name>

# Running the microservices on docker
To run the microservices, you have to run two commands.

Run the following command to build the docker containers:
```shell
docker compose build
```

Run the following command to start running the docker containers:
```shell
docker compose up
```

If you want to build or start only particular services, you can specify the services you want to start by writing out their names. For example, the command below starts up the relay-api service, rabbitmq service, and postgres service all in one command:
```shell
docker compose up relay-api rabbitmq postgres
```

When you are starting up a service using `docker up`, it automatically starts following the logs - showing you all the activity happening in those services. If you do not want that, you can start the services up in detached mode using the `-d` flag as shown below:
```shell
docker compose up relay-api -d
```


# Logging
The [docker logs documentation](https://docs.docker.com/engine/reference/commandline/logs/#usage) explains in detail how to view the logs coming from your docker container. However, here is a brief overview of some important commands for viewing your logs.

If you want to display the logs for all docker containers at once, use:
```shell
docker compose logs
```

However, if you want to display the logs for a particular service, say the `relay-api` for example, you can use the following command
```shell
docker logs relay-api
```

## Docker Log flags
There are specific flags you can use to enhance your experience in viewing logs. They are all detailed in the docker logs documentation linked above, but here are a few essential ones to get you started.

If you want to display your logs live as they come in, use the `--follow` flag as shown below:
```shell
docker logs relay-api --follow
```

If you want to show the last 50 entries to the log, use the `--tail` flag as shown below:
```shell
docker logs relay-api --tail 50
``` 

## Fixes
If you are having problems with experiencing bugs that are supposed to be fixed, or your changes not being reflected in docker, maybe docker is caching something, instead of using the lastest version. To fix, do this:

```shell
docker compose down
docker system prune -a
```
CAREFUL!!! this deletes all your images and containers, not only the ones associated with this project. If you don't want that to happen, delete the images AND containers for this project manually from the docker app, and run docker compose build --no-cache`
