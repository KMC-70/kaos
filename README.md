# Project KAOS (Kerbodyne Analytical Orbit System)

[![Build Status](https://travis-ci.org/KMC-70/kaos.svg?branch=master)](https://travis-ci.org/KMC-70/kaos)
[![codecov](https://codecov.io/gh/KMC-70/kaos/branch/master/graph/badge.svg)](https://codecov.io/gh/KMC-70/kaos)

KAOS is a scalable satellite mission planning suite for Earth observation satellites.

## Setup

### (Optional) virtualenv

Not required, but a great idea.

With [Python2.7](https://www.python.org/downloads/release/python-2715/) and [pip](https://pip.pypa.io/en/stable/installing/) installed:

```
pip install virtualenv
virtualenv -p /usr/bin/python2.7 --no-site-packages kenv
source kenv/bin/activate
```

**Note**: please do not commit the `kenv` folder.

### Install dependencies

```
pip install -r requirements.txt
```

### Configure the database
In order for KAOS to run it needs to be connected to a PSQL database. For convenience two scripts
have been included in  the `scripts` directory to automatically set up the PSQL instances and create
the databases and users expected by the default configs for KAOS.

If another PSQL config is required with different users and database names then
`kaos/settings_test.cfg` and `kaos/settings.cfg` must also be modified to point KAOS to the new DB.

Optionally, if a quick database setup is required for rapid testing a prototyping then the following
command can be used to quickly spin up a docker instance:
`docker run --name kaos-test -e POSTGRES_PASSWORD=kaosuserpassword -e POSTGRES_USER=kaosuser -e POSTGRES_DB=kaostestdb -P -p 127.0.0.1:5432:5432 -d postgres`

### Run tests and pep8

```
pytest test -s
flake8 kaos
```

### Run the server

```
flask run
```

## Development

We (mostly) use the [Google Python style guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md). The tl;dr of style rules:

* PEP8 compliant
* 100 chars per line max
* prefer `string.format` over C printf formatting
* snake case variable names
* readable docstring format:

```python
def get_the_answer(x, y, *args):
    """This function answers ALL THE THINGS.

    Args:
        x (int): The first thing to answer.
        y (str): The second thing to answer.
        *args: All the other things to answer.

    Returns:
        The answer (probably 42).
    """
    # do stuff
```

# About the Project

This project was created for the [UBC](https://www.ubc.ca/) Electrical and Computer Engineering Capstone project, in partnership with [MDA Corporation](https://mdacorporation.com/).

## Team KMC-70

James Asefa  
Ray Li  
Roy Rouyani  
Lise Savard  
Zeyad Tamimi  
