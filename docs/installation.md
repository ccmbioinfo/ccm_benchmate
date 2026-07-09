---
layout: default
title: Installation
nav_order: 2
---

![](assets/installation.png)

# Installation Instructions

This is a python project, but it does have a few non-python dependencies. I have created an `environment.yaml` file 
that would make the installation process a little bit easier I hope. 

## Installing Conda

This one is fairly straightforward, you can follow the instructions [here](https://docs.conda.io/projects/conda/en/stable/user-guide/install/index.html) after running the installation script you should
be able to activate/deactivate conda environments. If you are installing this under HPC, I suggest that you move the location
of your conda cache to a different location. You can do that by following the instructions [here](https://stackoverflow.com/questions/58131555/how-to-change-the-path-of-conda-base), the other option
is that you can create a [symbolic link](https://stackoverflow.com/questions/1951742/how-can-i-symlink-a-file-in-linux) to your `.cache`, `.singularity` and `.conda` folders in your `~` where the actual
folders are in a partition with more storage. 

## Installing Benchmate

The project comes with a conda `enviroment.yaml` file that has all the dependencies listed. Keep in mind that this project
is still under heavy development and the dependencies might change and that might result in older installations to break. 

First you will need to clone the repository using git. 

```bash
# clone the repository
git clone https://github.com/ccmbioinfo/ccm_benchmate

# enter benchmate director
cd ccm_benchmate
```

Then you can create the conda environment and install all the dependencies with a single command. 

```bash
conda create env -f environmemt.yaml

conda activate benchmate
```

This will install all the dependencies including a postgres server. This is needed for using the project instance an all the
related modules, if you are not interested in that you can comment out that section in the `yaml` file.

After installing dependencies you will need to install benchmate itself. 

```bash
pip install . 
```

### If you are using postgres

Benchmate will not create a database for you. You will need to do that as the pg admin. 

**Start the database server:** 

You will need to start the database server, postgres comes with many reasonable defaults but if you need to change them please
check their documentation. The default port for postgres is `5432`. 

To start the database server you will need to specify a folder and a logfile. The directory needs to be empty. 

```bash
# intialize the process, if <database_dir> does not exist you need to create it
initdb -D <database_dir>

#start the server
pg_ctl -D <database_dir> -l <database_dir>/logfile start
```

With this you will have posgres server running, then you will need to log into the databse and create a new one. 

```bash
psql -d template1 #this one is a small template that comes with db installation
```

**Create the database and user**

```postgresql

CREATE ROLE <username> WITH LOGIN SUPERUSER PASSWORD `password`; 

CREATE DATABASE <your_db_name> OWNER <username>
```

A few of the modules (literature and molecule) depend on postgres extensions we need to activate them. 

```postgresql
create extension if not exists rdkit; 

create extension if not exists vector;
```

Then we should be good to go. 

## A Quick note about model selection

You can see in the `config.yaml` file that we have made some decisions about which models to use as a default in the package. 
These decisions were made with a couple of important considerations in ming. 

1. The models need to be robust and actually follow instructions (not every instruction tuned model does that or does it reliably)
2. They need to be small enough to be run in <40GB of VRAM (you can probably run benchmate no problem with a GTX5090 that you can buy at a computer hardware store)
3. They are fast(-ish), this was the main consideration for choosing a static model for semantic chunking. 

## Containers

We are working on creating docker containers and a `docker_compose.yaml` file to make this a less painful process. 
Once those developments are done this documentation will be updated. 

Please create an issue with all the error messages if you run into problems. 