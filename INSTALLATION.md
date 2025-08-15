<div style="text-align: center;">
    <img src="./assets/installation.png" width="900" alt="CCM Benchmate logo" class="center">
</div>

# Installation Instructions

This is a python project but it does have a few non-python dependencies. I have created an `environment.yaml` file 
that would make the installation process a little bit easier I hope. This `yaml` file will change in the future as 
we add more functionalities and move some of them to the `ContainerRunner` module.

## Installing Conda

This one is fairly straightforward, you can follow the instructions [here]() after running the installation script you should
be able to activate/deactivate conda environments. If you are installing this under HPC, I suggest that you move the locaiton
of your conda cache to a different location. You can do that by following the instructions [here](), the other option
is that you can create a [symbolic link]() to your `.cache`, `.singularity` and `.conda` folders in your `~` where the actual
folders are in a partition with more storage. 

## Installing ccm_benchmate dependencies

Here are the instructions for installation. 

```bash
git clone https://github.com/ccmbioinfo/ccm_benchmate

# go into the directory
cd ccm_benchmate

#create the conde env
conda env create -f environment.yaml #this might take a minute or 2
conda activate ccm_benchmate

# install the python dependencies
pip install -r requirements.txt

pip install . 
```



This will create the conda environment and install all the dependencies. There are a few things to keep in mind which are 
not included in this package yet and there are some gotchas:

1. MMSEQS requires AVX512 instruction sets. If you have a new-ish personal computer, that should be fine. It might not run on 
apple silicon, I have not tested that. Additionally, some of the older cpus on HPC do not support this. You will need to 
create a job where you specify this constraint by including `-constraint=avx512`

2. Singularity is not included in this package, however, there is an instance of singularity and another one of apptainer
in HPC. If you are using this package in HPC you can use `module load Singularity` or `module load apptainer`. This is not
something you need to worry about at the moment because the `ContatinerRunner` class is still under heavy development. We 
will include more instructions about how to get that running when it's better tested. 

3. Again not implemented yet, but you will need postgresql database with pgvector extension enables, while you can install
postgres with conda, the version of pgvector extension in conda is woefully out of date. We will create better instructions
for this feature when it's ready to be tested. 

Please create an issue with all the error messages if you run into issues. 