# Contributing to Clanvas

Thanks for your interest in helping out. Take a look at some of the guides below to get started.A

## Contribution guidelines
* [Development/test server](#developmenttest-server)
* [Setting up a development environment](#setting-up-a-development-environment)
  * [Required software](#required-software)
  * [Forking the repo](#forking-the-repo)
  * [Cloning your fork](#cloning-your-fork)
  * [Set the upstream remote](#set-the-upstream-remote)
  * [Creating a new branch for a change](#creating-a-new-branch-for-a-change)
  * [Setting up the Python environment](#setting-up-the-python-environment)
* [Developing a change](#developing-a-change)
  * [Running regression tests](#running-regression-tests)
  * [Creating new regression tests](#creating-new-regression-tests)
    * [Specifying requirements](#specifying-requirements)
    * [Getting test data](#getting-test-data)
  * [Creating a pull request](#creating-a-pull-request)
* [Other Resources](#other-resources)
  * [Case students](#case-students)

## Development/test server

I've set up a Canvas server where I can give people permissions to create courses so that we can
test anything: admin, professor, TA, and student features.

Send me an email at [markwlalor@gmail.com](mailto:markwlalor@gmail.com) (or a message on
Slack if you are a Case student) and I'll make you an account, let me know the email address
you want to use with the account as well as the SIS ID you want to use. I'll create an account
with a random password which you can change. Then you can log in at
[https://canvas.marklalor.com](https://canvas.marklalor.com). Maybe at some point we can set
up a server for doing integration tests as well.

## Setting up a development environment

### Required software

The core software needed for development is quite simple.

1. `git` for obvious reasons.
2. `python` 3.6 or greater.

For an IDE, [PyCharm](https://www.jetbrains.com/pycharm/download/) is recommended.
[Visual Studio Code](https://code.visualstudio.com/) should work well too.

### Forking the repo

Click on the `Fork` button located on the top-right page of Github to create your
own copy of the clanvas repository for development. This will set up a project on your
account at `github.com/yourusername/cmd2.git`.

(More info about forking [here](https://help.github.com/articles/fork-a-repo/))

### Cloning your fork

Clone your `clanvas` fork.

```
git clone https://github.com/yourusername/clanvas.git
```

Enter the directory with `cd clanvas`.

### Set the upstream remote

If you check the remotes, you will see that fetching and pushing is configured for
your copy of the repository.

```
$ git remote -v
origin	https://github.com/yourusername/clanvas.git (fetch)
origin	https://github.com/yourusername/clanvas.git (push)
```

In order to pull up-to-date changes from the main repository, add the
main repository as a remote called `upstream`.

```
$ git remote add upstream https://github.com/marklalor/clanvas.git
```
Now you have another remote set to access the upstream changes! Check with `remote -v`

```
$ git remote -v
origin	  https://github.com/yourusername/clanvas.git (fetch)
origin	  https://github.com/yourusername/clanvas.git (push)
upstream  https://github.com/marklalor/clanvas.git (fetch)
upstream  https://github.com/marklalor/clanvas.git (push)
```

### Creating a new branch for a change

*Note: if it has been a while since you first cloned the repository, see
[keeping your fork up to date](#keeping-your-fork-up-to-date) before proceeding.*

Before making changes, creating a new branch will allow you to keep your work
separate from the `master` branch, so that the `master` branch can be easily updated
with the latest changes from `upstream` at any time.

Choose a name for the branch that describes the issue, and create the branch on
your local machine.

```
$ git checkout -b [your_branch_name]
``` 

### Setting up the Python environment

Setting up a virtual environment is highly recommended. The main motivation behind virtual
environments is versioning. If `clanvas` uses version `1.0` of software `A`, but some other
project you work on uses version `2.0` of software `A`, then which version should be installed
on your computer?

The answer is to create separated Python environments for each project!

First of all, we need to make sure we are using a `Python 3.6+` distribution, a good way to
get a distribution is through the `Anaconda` package manager. This is especially good for
developing on `macOS`, because `Anaconda` python comes with `GNU readline`, which is needed for
proper tab-completion support.

Install `Anaconda` on your system with the
[instructions on their website](https://conda.io/docs/user-guide/install/index.html#)

Make sure that you've added the anaconda binaries directory to your path so that you are using
the correct python. Add the following line to your `.bash_profile` or `.zshrc`  
```
# At some point after your PATH is defined...
export PATH=/usr/local/anaconda3/bin:"$PATH"
```

Save and then source your edited rc file with `source ~/.zshrc` or equivalent (or restart your terminal).

**Now `Anaconda`'s commands are available to use!**

Create a new virtual environment.
```
$ conda create --name clanvasdev python=3.6
```
Follow the instructions on screen to install the conda environment.

Activate the environment in your current terminal session.
```
conda activate clanvasdev
```

Then, make sure you are in the top level directory of the clanvas project, and run the following
command to make a virtual environment specifically for this project based on the anaconda python.

```
python -m venv venv
``` 

The proper binary files will now be installed in a folder called `venv` in your project.
Check using the `ls` command

```
$ ls -l venv/bin
total 64
-rw-rw-r--  1 mark  staff  2205 Oct 13 23:53 activate
-rw-rw-r--  1 mark  staff  1261 Oct 13 23:53 activate.csh
-rw-rw-r--  1 mark  staff  2425 Oct 13 23:53 activate.fish
-rwxr-xr-x  1 mark  staff   259 Oct 13 23:53 easy_install
-rwxr-xr-x  1 mark  staff   259 Oct 13 23:53 easy_install-3.6
-rwxr-xr-x  1 mark  staff   241 Oct 13 23:53 pip
-rwxr-xr-x  1 mark  staff   241 Oct 13 23:53 pip3
-rwxr-xr-x  1 mark  staff   241 Oct 13 23:53 pip3.6
lrwxr-xr-x  1 mark  staff     7 Oct 13 23:53 python -> python3
lrwxr-xr-x  1 mark  staff    48 Oct 13 23:53 python3 -> /usr/local/anaconda3/envs/clanvasdev/bin/python3
```

Restart your terminal to remove the direct pointers to the conda installation.

Now, whenever you want to use python for `clanvas`, go to the clanvas directory and type
```
source venv/bin/activate
```

Now, when you use the `python` or `pip`  commands, they are specific to this clone of clanvas
and are isolated from any other Python on your system.

```
$ which python
/path/to/clanvas/venv/bin/python
```

Now you install all the development requirements to your virtual environment. 

```
pip install -e .[dev]
```

If you are using PyCharm, you should add the venv python (see 
[Adding Existing Virtual Environment](https://www.jetbrains.com/help/pycharm-edu/adding-existing-virtual-environment.html)) 

## Developing a change

Before developing a change, select an existing issue, or open a new issue
on [clanvas/issues](https://github.com/marklalor/clanvas/issues). Let us
know you're working on an issue so that we don't have multiple people working
on the same task. If it's not an existing issue, we want to make sure you don't
go developing some code only to be later told that the feature is not needed.

### Running tests

The entire test suite can be run using `suite.py`.

This includes unit tests and regression tests.

```
python -m unittest -v tests.suite
```

Always run this after making any changes to make sure you haven't accidentally messed up
existing behavior. [Travis CI](https://travis-ci.org/marklalor/clanvas) will
also run this to check any changes pushed. 

### Running regression tests

Currently there is a single test case that runs all regression tests
located in the `tests/regression` folder.

```
python -m unittest -v tests.regression.test_regression.TestRegression
```

### Updating regression tests

If you change existing behavior, update the unit tests running
regression.py and providing a name for the commands to be updated.

For example, if you want to regenerate transcripts for the `lc` command after making changes:
```
python tests/test_regression.py lc
```

### Creating new regression tests

#### Specifying requirements
If you take a look at regression.py, you'll see a structure that maps command names to
a set of script names that maps to another structure that describes the HTTP endpoints
that need to be mocked in order to run this command. For example, this is the subset of
mappings for the `whoami` command.

```python

login_requirements = {'user': {'self', 'profile'}, 'courses': {'courses'}}

script_requirements = {
    'whoami': {
        'whoami': login_requirements,
        'whoami_verbose': login_requirements
    }
}
```

The requirements dictionary is structured as follows: the key corresponds to a json file in
the fixtures directory, for example `user` corresponds to `tests/fixtures/user.json`. The value
corresponds to a set of top-level objects in the `user.json` file. These objects then describe
the HTTP responses that will be mocked.

The `login_requirements` dictionary is a common set of requirements that is needed for
any script since when Clanvas starts up the user profile and their set of courses is 
immediately requested in another thread for speed purposes. You can use the `compose_requirements`
function to combine several dictionaries structured like this one.

#### Getting test data

You can/should add a `get_` method to `data_extraction.py` if you need new data from canvas
to mock a request for testing. Make a method that returns the json format used in the fixture
json files. See the rest of the See the other `get_` methods for examples of how this works.

To run the method, you can use the script's provided setup and teardown functionality, once you've
written a method all you have to do is something like the following example:

```
python tests/data_extraction.py user_profile --rcfile=~/.clanvasrc
```

Specifying `user_profile` makes the script call the `get_user_profile` method.

You can also omit the `--rcfile` if you want to manually enter in a URL/token. If you want
the output to be a file, you can use the `--output` option. Either way, you can take the output
and add it to an existing fixture json or create a new one.

### Creating a pull request

Once you've added/regenerated/checked appropriate tests, you are ready to submit a pull request.
Use git to commit the changes that you want reflected in the main project. Once you've made your
commits, push it up to your fork on Github:

```
git push -u origin [your_branch_name]
```

Now you can submit a pull request from the Github interface.

1. Go to your fork at `https://github.com/yourname/clanvas.git`, you will
see a `Compare and pull request` button.
2. Make sure that the pull request is against the master branch of Clanvas, and against
your change branch for your fork (this should be the default).
3. Add a descriptive title that summarizes your changes.
4. Include a more detailed summary of exactly what changes you made in order to
communicate your changeset effectively.
5. If you are unsure about your implementation, note that in your description! Creating a
change is an iterative process that benefits from feedback.

Once you've made the pull request, a few things will happen.

1. The regression tests will be run automatically, and the status will be shown on your
pull request page once they complete.
2. The maintainers will be notified and can take a look at your code to make suggestions.

If your code was not accepted right away, or failed some tests, don't despair!
Make the appropriate changes, and then amend your commit with `git commit --amend`. Then you
can update your fork with `git push --force`. This will update the associated pull request.
Leave a comment on the pull request describing the changes you have made.

## Other Resources

This guide purposely leaves out steps, because if every single tangentially-relevant detail
was included, the page would take hours to read and it would be hard to pull relevant information
out of. This guide is beginner friendly, but it doesn't quite hold your hand all the way through.
For example if you're not at all familiar with `git` you may be scratching your head on how to
fill in the missing steps.

Here are some good resources explaining how to use things like git, Github, or
contributing to open source projects in general.

* [Github Guide: *How to Contribute to Open Source*](https://opensource.guide/how-to-contribute/)
* [Video Tutorials: *How to Contribute to an Open Source Project on GitHub*](https://egghead.io/series/how-to-contribute-to-an-open-source-project-on-github)
* [Github: *Fork a repo*](https://help.github.com/articles/fork-a-repo/)
