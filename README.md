## Development
1. Install [Docker Desktop](https://docs.docker.com/get-docker/)  
    Please know that the development environment is only validated against linux environments. Please do not use Windows Container for your Docker installation if you are on Windows
2. Create a .env file under `rmn_arch_0/settings/` that contains the following
    ```
    DJANGO_SECRET_KEY=<random secret key>
    DJANGO_SETTINGS_MODULE=rmn_arch_0.settings.local

    RDS_HOSTNAME=db
    RDS_PORT=5432
    RDS_PASSWORD=password
    RDS_USERNAME=web
    RDS_DB_NAME=web_db

    REDIS_HOSTNAME=redis
    ```
3. Run the following command
    ```
    . .devcontainer/.bash_aliases
    docker-start-w-log      # alias of 'docker-start && docker-log'
    ```
    Please note that if you see `django.db.utils.OperationalError: FATAL:  the database system is starting up` in the logs, run the command again in a few second. This is resulting from the database not being ready when the web container is starting.
4. Now you should be able to checkout the local development site on [localhost](http://localhost/)
5. You can run the following to create some fake content on the site
    ```
    docker-compose exec web python tests/_tools/create_content.py create_content
    ```
