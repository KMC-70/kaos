# Project KAOS (Kerbodyne Analytical Orbit System)

[![Build Status](https://travis-ci.org/KMC-70/kaos.svg?branch=master)](https://travis-ci.org/KMC-70/kaos)

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

### Run tests

```
pytest test -s
```

### Run the server

```
flask run
```

## Development

We (mostly) use the [Google Python style guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md). The tl;dr of style rules:

* 80 chars per line max
* snake case variable names
* readable docstring format:

```python
def get_the_answer(x, y, *args):
    """
    This function answers ALL THE THINGS.

    Args:
        x (int): The first thing to answer.
        y (str): The second thing to answer.
        *args: All the other things to answer.

    Returns:
        The answer (probably 42).
    """
    # do stuff
```

* prefer `string.format` over C printf formatting

# About the Project

This project was created for the [UBC](https://www.ubc.ca/) Electrical and Computer Engineering Capstone project, in partnership with [MDA Corporation](https://mdacorporation.com/).

## Team KMC-70

James Asefa  
Ray Li  
Roy Rouyani  
Lise Savard  
Zeyad Tamimi  
