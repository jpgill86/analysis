Jeff's Data Analysis Toolchain
==============================

Installing dependencies
-----------------------

You will need access to these commands on the command line:

- ``conda`` (Anaconda_ or Miniconda_ with Python 3)
- ``git`` (``conda install git`` or git-scm.com_)

Download this source code, either manually through GitHub_ or using ``git``::

    git clone https://github.com/jpgill86/analysis.git

On the command line, navigate to the top-level directory::

    cd analysis

Create a new conda environment::

    conda env create -f environment.yml -n analysis

or update an existing one::

    conda env update -f environment.yml -n analysis

Instead of ``analysis``, you could use any environment name you like, but the
scripts in the ``scripts`` directory assume this is your enviroment name.

.. _Anaconda:       https://www.anaconda.com/download/
.. _Miniconda:      https://docs.conda.io/en/latest/miniconda.html
.. _git-scm.com:    https://git-scm.com/downloads
.. _GitHub:         https://github.com/jpgill86/analysis/

Getting started
---------------

Activate your conda environment and launch Jupyter notebook::

    conda activate analysis
    jupyter notebook

Using the Jupyter file browser, navigate to the ``notebooks`` directory and
select a Jupyter notebook file (``*.ipynb``) to begin a session.

The ``launch-notebooks`` script located under ``scripts`` can run these
commands and navigate to the correct directory for you.

Running the ephyviewer example
------------------------------

Follow the steps given above but navigate to the ``example`` directory instead
and launch the ``Data Explorer`` notebook.

Alternatively, run the ``launch-example`` script located under ``scripts`` to
accomplish the same thing.

After the notebook opens, run all cells in order. A Qt-based graphical user
interface will launch. (Note that this type of GUI cannot be launched from a
Jupyter server running on a remote computer, such as with MyBinder.org.)

.. image:: example/ephyviewer-screenshot.png

The ephyviewer interface is interactive and highly customizable.

- Pressing the play button will scroll through the data and video in real time,
  or at higher or lower rate if the speed parameter is changed.
- Right-clicking and dragging right or left will contract or expand time to show
  more or less at once.
- Scrolling the mouse wheel in the trace viewer or the video viewer will zoom.
- The epoch encoder can be used to block out periods of time during which
  something interesting is happening for later review or further analysis.
- All panels are optional and can be hidden, undocked, or repositioned
  on the fly.

See the `ephyviewer documentation`__ for more details.

__ http://ephyviewer.readthedocs.io

Notes
-----

When creating a new conda environment, you may use one of the files in the
``snapshots`` directory instead of ``environment.yml`` to create an exact
replica of an environment created using that file on a particular date (these
files were created using ``conda env export``, with git commands pointing to
specific commits added manually). This is useful for tracking down bugs or
reproducing old results exactly when external package updates create unexpected
changes in output. Using old environment snapshots may result in installing old
versions of packages when newer versions would work just as well, so try
``environment.yml`` first.
