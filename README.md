# Flight-Duck Back-End

A Django server providing the Flight & Hotel pricing and to perform booking operations.

# Dev environment set up

### For Back-End only

1. Install [Python](https://www.python.org/downloads/)
    * For Mac/Linux systems, install `python-dev` tools. [Source](https://stackoverflow.com/a/21530768)
2. Install [Pip](https://pip.pypa.io/en/stable/installation/) for your system
3. Install [Postgres](https://www.postgresql.org/download/) and [pg_group](https://stackoverflow.com/a/12037133) for your system
3. Install `pip` packages from `requirements.txt` file
```shell
python -m pip install -r requirements.txt
```
3. Start server with: `python manage.py runserver`
4. Profit!

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
