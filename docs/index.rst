Aktionskarten Backend
=====================

Purpose of *aktionkskarten/backend* is to persistently store spatial data and
visualize it. For that it provides a *ReST API* and relies on openstreetmap
data. A client can create, edit and delete new maps. Moreover these maps can
be visualized as raster maps in file formats like PDF, PNG or SVG.

The backend itself is written in python with help of flask, postgres, mapnik
and openstreetmap-carto. As rendereing is time and ressource intensive and
therefor it's not done in the webapp itself but through a task queue. We use
*redis queue* for that. So as summary the following dependencies exist:

Databases
    * postgres
    * redis

Libraries
    * flask
    * sqlalchemy + geoalchemy2
    * mapnik
    * cairo

Tools
    * osm2pgsql
    * carto

We try to aggregate as little data as possible. This results that there is
no user management. Each map has a security token. Only with this secret
you're able to edit a map.

You can find more informations about the API itself or classes here:

.. toctree::
    :glob:

    api.rst
    modules.rst


Install
-------

Dependencies
............

At least postgres, postgis, mapnik, cairo and redis need to be installed. Do
this through your os package manager:

build fails with libmapnik3.1

Ubuntu 20.04

.. sourcecode:: bash

  $ sudo apt install gcc build-essentials postgresql libmapnik3.0 libmapnik-dev redis python3-venv python3-dev libcairo2 libcairo2-dev libboost-python-dev



Start DBs

.. sourcecode:: bash

  $ sudo systemctl start postgresql
  $ sudo systemctl start redis


Setup
.....

.. sourcecode:: bash

  $ git clone --recursive https://github.com/aktionskarten/backend
  $ cd backend
  $ python -m venv env
  $ . env/bin/activate
  $ pip install -r requirements.txt
  $ export BOOST_PYTHON_LIB=boost_python 
  $ ln -s /usr/lib/x86_64-linux-gnu/libboost_python38.so /usr/lib/libboost_python.so
  $ python app/cli/pymapnik.py install # install custom python mapnik package
                                       # can call through flask cli because it
                                       # is essential to instantiate the app
  $ flask postgres init     # create app database
  $ flask osm init          # download osm dump and create db for it
  $ flask gen-markers       # generate markers
  $ flask create-tables     # create app sql tables
  $ rq worker               # start task queue worker
  $ flask run --with-threads --no-reload # start backend

Tests
-----

Tests are written with pytest. To run them do the following:

.. sourcecode:: bash

  $ python -m pytest -s tests/


Docker
------

There exists Dockerfiles for testing/development in the deploy/docker directory.
Either you create them by hand in the following way:

.. sourcecode:: bash

  $ cd deploy/docker
  $ docker-compose up --build

Or you use the provided images of DockerHub. For this you need to remove the
build entries in the docker-compose.yml file (see akionskarten.js for an
example). These images are not meant for production deployment.
