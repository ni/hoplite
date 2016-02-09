.. |Hoplite| replace:: **Hoplite**

Job Developer API
*****************

The following information describes how to create job plugins for |Hoplite|. Note that the plugin architecture is no
longer intended for use by Hoplite end-users, as it has been superseded by the
:ref:`Remote Enabler API <remote-enabler>`. However, the documentation is still included for those who still want to
use the plugin system.

.. _job-plugins:

Writing Job Plugins
===================

Job plugins are the runnable modules invoked by jobs. You need to satisfy two requirements to have |Hoplite| load
your plugin.

    1. A `setup.py` that defines the `hoplite.jobs` entry point
    2. The module must define a run method which takes two arguments: a dictionary containing the configuration and
       a :py:class:`hoplite.client.StatusUpdater` which can be used to update the status of job::

        def run(config, status)

setup.py Entry Points
=====================

Your call to `setup()` in your `setup.py` should have a parameter that looks like this::

        entry_points={
            'hoplite.jobs': [
                'the.name.you.want.to.show.up.in.hoplite = yourpackage.yourmodule',
                'another.name.for.your.hoplite.job = yourotherpackage.yourmodule'
            ]
        }

RemoteJobManager
===================

    ..  automodule:: hoplite.client.remote_job_manager

    ..  autoclass:: hoplite.client.RemoteJobManager
        :members:


RemoteJob
=========

    ..  automodule:: hoplite.client.remote_job

    .. autoclass:: hoplite.client.RemoteJob
        :members:

StatusUpdater
=============

    ..  automodule:: hoplite.client.status_updater

    .. autoclass:: hoplite.client.StatusUpdater
        :members:

    .. autoclass:: hoplite.client.MockStatusUpdater
        :members:
