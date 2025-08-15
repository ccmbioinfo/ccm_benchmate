<div style="text-align: center;">
    <img src="./assets/contributing.jpeg" width="500" alt="CCM Benchmate logo" class="center">
</div>

# Contributing

We are so glad that you want to contribute to our project! Here are some guidelines to help you get started:

We are using git for version control, if you are familiar with git feel free to skip this section. The first thing you will
need is a github account. If you don't have one, you can create one at [github.com](github.com). After that you can fork the 
repository by clicking the "Fork" button in the top right corner of the repository page. This will create a copy of the repository in your own account.

Here are some basic git instuctions:

## Creating a local git repo

Github is built on top of git. Git is a popular code version control system that tracks your edits to files and whether
new files are added or old ones are delelted. To create a git repository in a directory of your choosing

```bash
cd mydirectory
git init
```

this will create a blank git repository and you will be in the `main` branch.

Better yet clone this repository using:

```bash
git clone https://github.com/ccmbioinfo/ccm_benchmate
```

This branch is reserved for the "production" code and things will not be added here until they are tested and ready to
go. You can create a new branch by:

```bash
git branch new_branch
```

you can switch between branches using:

```bash
git checkout old_branch
```

to add new files/folder to your git repository use:

```bash
git add new_file.py
```

to commit use:

```bash
git commit -m "commit message"
```

See below for more guidelines on branching, commit pushes and pull requests.

You can configure your remote repository with:

```bash
git remote add origin https://github.com/ccmbioinfo/ccm_benchmate
```

and you can push using

```bash
git push -u origin <branch name>
```

Please create a `.gitignore` file to keep the unwanted from being added and commited to the repository. You can also use the 
exisiting file and make changes as you see fit. 

### Commiting guidelines

Please make sure to write clear and concise commit messages. A good commit message should explain what changes were made and why.
Do not try to make multiple unrelated changes in a single commit. Instead, break them down into smaller, logical commits, this not only
makes it easier to review your changes, but also helps in tracking down issues later on. When you want to create a pull request make sure that
it is related to a single feature or bug fix. If you have multiple features or bug fixes, create separate pull requests for each one. This will
allow us to review and merge them independently, making the process smoother and more efficient.

### Branching guidelines

When you are working on a new feature or bug fix, please create a new branch for your changes. This will help keep the main branch clean and will also
avoid conflicts with other contributors. 

## Code Style

As you can tell this is mainly a Python project, so please follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code.
To make everyone's life easier we are going to keep a very relaxed style guide. We are not going to enforce any specific line length, or any specific 
indentation style. We do however ask that you use spaces instead of tabs for indentation, and that you use 4 spaces for each level of indentation.

Find a clear but short name for your task obviously `myawesomecode` is not an appropritae name for a folder or python
code but neither is `scibertsummarizerforclinicalnotesbasedonpreviouscomments`. Something like `summarizer` is a much
better choice. While naming folders and files try and be as explicit as possible so if your code does not summarize but
select sections of notes `section_selector` might be more suitable.

Within each folder there should be at least one python module with the same name, this module will contain the main code
that does the task. This does not mean that it will contain **all** the code related to the task. Have a clear separtion
of different kinds of things each module does and try to contain each of these in their respective module. You can
make this as a CLI script that is callable with arguments (see below) or you can choose to include another file
(this can be python or bash -let's keep things standard, if you use bash please set `-oe pipefail`).

For processing data, and general manipulation tasks create a module called `utils.py` this will contain the utilities
that are helper functions and classes but do not perform the main task. For example: a function that takes all the
tab (`\t`) and converts them to new lines (`\n`) will be in the utils.

If this module is going to be part of the knowledge base and will be used by other modules, please make sure that you describe
in detail how it works and what it does in the `README.md` file. 

Additionally you will need to structure your data in a way that it can be stored in a normalized SQL database. This means that
you will need to create a module called tables.py and that will contain the SQLAlchemy models that will be used to generate and
populate the tables in the database. Some of the modules already have this files, so feel free to use them as a reference.

If you are not familiar with SQLAlchemy, please take a look at the [SQLAlchemy documentation](https://docs.sqlalchemy.org/en/14/orm/tutorial.html) and
if you have any questions about how to sructure your data in a way that it can be stored in a normalized SQL database, see 
[here](https://www.datacamp.com/tutorial/normalization-in-sql) for reference and you can always reach out to us via issues.

There is no limit to how many modules you can create but one helpful rule I find is to focus on the task not on the
code. Each task should get its own module that is then imported by the main module.

In addition to code your folder should also contain a `README.md` that is properly formatted in markdown style (like
this README). This
document will include:

+ A brief summary of what the task(s) is (are)
+ How they are accomplished
+ list of 3rd party modules
+ detailed description of modules
+ usage instructions for main classes and functions

If you are using conda you can choose to inlcude an `enviroment.yaml`. Please use these names in and not something else
to make sure that we are all in the same page.

## Code style

This is a python project so at the very least we will stick to PEP8 guides with 120 characters per line (we can change
that if you'd like).

Each function/class should contain detailed docstring that has at the very least the following information

+ What does the function do use common sense in describing the function, if the task is simple the description can be
  simple
+ parameters and types, we can use reST style docstrings
+ outputs

for inputs like `*args` and `**kwargs` describe how they might be used and how they are passed to different functions
inside the function.

Avoid lambdas unless the task is extremely simple, same goes for list comprehensions. There is no performance
cost/benefit but a `for` loop is much easier to read.

For classes use CamelCase, for functions use lowercase. In classes there should be a docstring for the class as well as
class methods like so:

```python

class NewClass:
    """
    this class does something awesome
    """

    def __init__(self, input1, input2):
        """
        initiate a new instance of NewClass with some basic calculations and some other things
        param: self:, self NewClass
        param: input1: an input1
        param: input2 an input2
        type: input1: pandas DataFrame
        type: input2: bool
        return: a dict of different awesome results
        rtype: dict
        """
        pass

    def method1(self, *args, **kwargs):
        pass

```

Feel free to structure your code however you wish as long as it's well documented. That said try and avoid exotic cases
python inheritance cases and global variables and scoping out variables using `global`. Each function/class should be
self contained and any input(s) it relies on should be passed during function call.

Use common sense when you are structuring your code, if you really need Subclassing go for it, if you really need mixins
that's ok too but with complexity comes side effects and convoluted code. If you think you need some of these
features please feel free to reach out and we can discuss if we can have a simpler architecture.

If you like using type hints please do so, but do not feel obligated to use them. If you do use them please make sure that
the types are correct and that they are used consistently throughout the codebase. Whenever applicaple at least describe
what types are expected for the inputs and outputs of the functions within the docstring. 


### Lazy vs Eager eval

Try and write your code as lazy as possible. Nothing should be calculated/processed/edited unless that method is
explicitly called. If you want method chaining that's ok too but make sure that you really need it.

### Dunder ("\_\_") methods and operator overloading

If you choose you can set up `__str__` and `__repr__` methods of your classes and subclasses. If you want to do
operator overloading please have a good reason to do so and make sure that it is well documented in your code and
README.

### Errors and Exceptions

Please code as defensively as possible. There are a lot of built-in exceptions that you can use to catch errors that
you can foresee happening like a `FileNotFoundError`. Feel free to create your own exceptions like so:

```python
class NewException(Exception):
    pass
```

### Threading and multicore processing

Currently, I think we are all using python 3.10. While python does allow multithreaded applications with the
`threading` module it is complicated to use. You can choose to multi core processing but please provide arguments
(see below) to allow user to set up the number of cores that can be used. While performing multiprocessing keep in
mind that your RAM usage basically multiplies with the number of cores you are using. Be mindful and don't crash the
VM (not a big deal it just would take a bit for me to reset and everyone will be kicked out until the reset is done).

### Arguments and settings

For simple CLI arguments use the `argparse` module. This is an extremely flexible module and you can have subparsers
for different modes of analysis. Please do not use a 3rd parth module like `click`. There is no need to increase the
number of dependencies.

If your code requires extensive parameters (it might for experimentation) you can have a `json` or a `yaml` file to
keep these values as a key:value store. Make sure that this file location is NOT hardcoded but rather passed as an
argument in the callable script.

### Push guides

As long as you are following the guidelines above you can push to your branches as much as you want. Github tracks
your git repo so if you have done multiple commits a single push will show up as multiple commits on the remote repo
as well.

### Pull requests

If you want to contribute to someone else's code please create a pull request unless you are actively working with
that person. The tagged person will then review the code and will approve or edit as they see fit. Save for the
simplest of taskt please keep the discussion within the issues section so we all know what's going on.

I'm excited to work with you all on this project and sorry for the wall of text. I hope this was not all boring for
you and it will be a good learning experience for all of us. Please let me know if you run into git issues and need 
some config help. 

## Docker/singularity containers

If you are using docker or singularity containers please make sure that you have a `Dockerfile` or a `Singularity` file. 
Additionally your containers not only should have all the dependencies installed but also should be able to run using the code
and files that are inside the container. This means that if you are using any kind of AI models you should download and inlcude the
model weights within the container. While this will make the container larger it will also make it easier to use for other people. 

For each container please include a `README.md` file that describes how to build and run the container. This should include:

+ How the container can be built (as simple as Dockerfile will be enough)
+ Which command(s) to use to run the container

Avoid including complicated pipelines inside the container. It is possible to generate a pipline using a series of contianers
this will also make it easier to use/maintain and modularize. For simple things like running multiple QC metrics for an RNA-Seq
pipeline you can use a single container that has all the dependencies installed.

If you are generating a pipeline using multiple containers please include a `README.md` file that describes how to use the pipeline. 
Use WDL or Snakemake to generate the pipeline. Your rules should clearly state which containers map to which rules. 