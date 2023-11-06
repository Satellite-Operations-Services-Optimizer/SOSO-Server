# Steps to initialize a local database

Follow these instructions to either a local database for SOSO prototype of a containerized docker database.

A. Local Database Steps

    1. Download PostgreSQL version 16 from: <https://www.enterprisedb.com/downloads/postgres-postgresql-downloads>.
    2. Use the default installer for your OS of choice and install all opetions:
        i.   postgres server
        ii.  pgAdmin4
        iii. StackBuilder
        iv.  command line tools
    3. Choose default directories and make an easy password for the server.
    4. Run pgAdmin4 and create a new database called "soso_db" in default server.
    5. Within this database, execute the script "soso.sql".
    6. The database is now setup, you can run the server and access it from within the backend of the project through API calls.

B. Containerized Database Steps:

    1. Download and install docker along with docker desktop with default settings from: <https://docs.docker.com/engine/install/>.
    2. Restart the computer and navigate to the database directory and open a terminal here.
    3. Execute command "docker-compose config" to check if file is correct.
    4. Execute command "docker-compose up --build to build and run the container.
    5. Check docker desktop to confirm container is spun up and running. Note: that you can also start/stop the container here now.
    6. You will need to retrieve the IP address for the pgAdmin4 web browser GUI to be able to use it.
        i.   In the terminal execute command "docker inspect ps" to find ID of container. Retrieve the first 4 characters of this ID.
        ii.  In the terminal execute command "docker-compose {4 chars of ID from above}
        iii. Retrieve the IP Address and save it.
    7. Access the pgAdmins4 continer instance with this ip address.
    8. Follow A.4-6
