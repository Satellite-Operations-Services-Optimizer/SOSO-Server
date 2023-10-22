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

1. Open a command prompt and navigate to the directory containing `requiredLibs.txt`.
2. Run the following command: pip install -r requirements.txt

3. If one or more packages fail to install, you can attempt to install them individually with: pip install <package_name>
