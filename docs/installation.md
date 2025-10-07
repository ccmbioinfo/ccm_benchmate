---
layout: default
title: Installation
nav_order: 2
---

![](assets/installation.png)

# Installation Instructions

This is a python project but it does have a few non-python dependencies. I have created an `environment.yaml` file 
that would make the installation process a little bit easier I hope. This `yaml` file will change in the future as 
we add more functionalities and move some of them to the `ContainerRunner` module.

## Installing Conda

This one is fairly straightforward, you can follow the instructions [here]() after running the installation script you should
be able to activate/deactivate conda environments. If you are installing this under HPC, I suggest that you move the location
of your conda cache to a different location. You can do that by following the instructions [here](), the other option
is that you can create a [symbolic link]() to your `.cache`, `.singularity` and `.conda` folders in your `~` where the actual
folders are in a partition with more storage. 

## Installing Benchmate

This project has a decent number of dependencies, to overcome some hurdles we have created an installation script but this 
has only been tested on Linux systems. 

```bash
# clone the repository
git clone https://github.com/ccmbioinfo/ccm_benchmate

# enter benchmate director
cd benchmate

bash install_benchmate.sh

```

This will create the minimum installation instance without any database support. If you want to install a postgres
database locally you will need to set some parameters

```bash
# install postgres and create the database
bash install_benchmate.sh -p -c -e .env_file -d <database_dir>
```

The env file contains all the secrets you will need to set up the database. Below is a quick example. The 
variable names **have to** match otherwise the script will fail. 

```dotenv
PG_USER=<username>
PG_PASSWORD=<password>
PG_DATABASE=benchmate
PG_HOST=localhost
PG_PORT=5432
```

After the installation is complete you should have a benchmate installation under the conda environment named "benchmate"

You can activate this by usint `conda activate benchmate`. Your database instance should already be running under
`PG_HOST:PG_PORT`. All the data associated with the database will be under the `<database_dir>` you specified in the installation
script. The database will continue running until the machine running the database is turned off (or if this is running in HPC) until
that specific job is completed. This does not mean that you will need to re-do the calculations and queries all over again. You will
just need to re-start the database instance.

```bash
conda activate benchmate

pg_ctl -D <database_dir> -l <database_dir>/logfile start
```

## Containers

We are working on creating docker containers and a `docker_compose.yaml` file to make this a less painful process. 
Once those developments are done this documentation will be updated. 


Please create an issue with all the error messages if you run into issues. 