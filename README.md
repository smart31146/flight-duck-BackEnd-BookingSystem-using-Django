# FlightDuck Back-End

A Django server providing the Flight & Hotel pricing and to perform booking operations.

# Dev environment set up

### For Back-End only

1. Install [Python](https://www.python.org/downloads/)
    * For Mac/Linux systems, install `python-dev` tools. [Source](https://stackoverflow.com/a/21530768)
2. Install [py](https://pip.pypa.io/en/stable/installation/) for your system
3. Install [Postgres](https://www.postgresql.org/download/) and [pg_group](https://stackoverflow.com/a/12037133) for your system
4. Install `pip` packages from `requirements.txt` file
```shell
python -m pip install -r requirements.txt
```
5. Get the `.env` from a developer and place in root directory of repo
6. Start server with: `python manage.py runserver`
7. Profit! 

### Run both Front-End with Back-End

See `README.md` on `FlightDuck-FrontEnd` repo for dependencies to install.

1. See Back-End instructions above
2. CD into `FlightDuck-FrontEnd` repo on your machine
3. Run `npm start` to install npm packages & run

# Operations information

Will be running on AWS, more details of set up as it's created. [Here's a preview](./docs/infra_proposal.md)

Things to come:
1. Secrets stored in [SSM Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
2. Use Environment Variables using debug code

# Setup Troubleshooting

### Error: pg_config executable not found.

On Linux, if you get this:
```
Error: pg_config executable not found.
```

This executable is found in the `libpq-dev` package (PostgreSQL development tool package). To fix this:
1. Install the `libpq-dev` (or `libpq-devel`) and `python-dev` (or `python-devel`) packages. ([Source](https://stackoverflow.com/a/12037133))
2. Also make sure that the relevant path is exported in your `PATH` environment variable (`export PATH=$PATH:/usr/pgsql-10/bin`)

If you edit your `PATH`, open a new terminal session for it to take effect.


<!-- Flight duck project

Leaving this in but commented out so future generations see the dumb shit we had to deal with

## Python Packages required - 
1. django
2. django-cors-headers
3. djangorestframework
4. markdown
5. django-filter

##### to install any python package write - pip install `package-name`

## To run python server
1. CD to directory of python-backend
2. Type the following command `python manage.py runserver`

## React Packages - 
1. CD to directory of frontend.
2. Run command `npm install`

## To run react server
1. CD to directory of frontend.
2. Run command `npm start` -->
