Jeff's Data Analysis Toolchain
==============================

Installing dependencies
-----------------------

You will need access to these commands on the command line:

- ``conda`` (Anaconda_ or Miniconda_ with Python 3)
- ``git`` (git-scm.com_)

Create a new conda environment::

    conda env create -f environment.yml -n <envname>

or update an existing one::

    conda env update -f environment.yml -n <envname>

You may use ``environment-XXXX-XX-XX.yml`` instead to create an exact replica of
an environment created from ``environment.yml`` from a particular date (these
files were created using ``conda env export``, with git commands pointing to
specific commits added manually). This is useful for tracking down bugs or
reproducing old results exactly when external package updates create unexpected
changes in output. Using old environment snapshots may result in installing old
versions of packages when newer versions would work just as well, so try
``environment.yml`` first.

.. _Anaconda:       https://www.anaconda.com/download/
.. _Miniconda:      https://conda.io/miniconda.html
.. _git-scm.com:    https://git-scm.com/downloads

Getting started
---------------

Activate your conda environment and launch Jupyter notebook::

    conda activate <envname>
    jupyter notebook

Click on an ``.ipynb`` notebook file to open it and begin a session.

    Note: As of 2018-10-28, with ipykernel>=5.0.0, the Python kernel may fail to
    start when launching a Jupyter notebook. If when opening the notebook you
    see the error "Failed to start the kernel. FileNotFoundError: [WinError 2]
    The system cannot find the file specified", it may be caused by a bad path
    to the Python executable in a configuration file name ``kernel.json`` (see
    related discussion `here`__; this bug appears to affect Windows
    installations only). You can locate the config file using ::

        jupyter kernelspec list

    One solution is to manually correct the path to the Python executable within
    the config file (remove ``/bin``). Another is to delete the kernel
    configuration entirely and fall back on the default kernel configuration,
    which can be done easily from the command line::

        jupyter kernelspec remove python3

    A third, heavy-handed solution is used in ``environment.yml``, which pins
    ipykernel to an older version, both to avoid this bug and to work around an
    unrelated but coincident issue with tridesclous in which the kernel fails to
    recognize that a GUI window has been closed and becomes unresponsive. If you
    use ``environment.yml`` or force ipykernel to an older version manually, you
    shouldn't need to worry about these bugs.

    __ https://github.com/conda-forge/ipykernel-feedstock/issues/6
