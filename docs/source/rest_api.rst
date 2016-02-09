.. _REST-API:

Hoplite Server HTTP API
***********************

The following information specifies the underlying API used to interact with Hoplite.
Any exceptions thrown by running jobs will be available in the status of that job under the
"exception" key. Note that this API is largely superseded by the :ref:`Remote Enabler API <remote-enabler>`

.. _REST-API-Server:

Server
======

..  http:put:: /reload

    Makes the server reload all the packages in the local site-packages directory. This should be used after installing
    any packages to the python environment. It forces an update of sys.path to include those new packages.

.. _REST-API-Job-Plugins:

Job Plugins
===========

..  http:get:: /job_plugins

    Get a list of all the job plugins that have been loaded. Jobs can be created to run any of the plugins
    in this list.

    **Example response**:

        ..  sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json
            {
                job_plugins: [
                    "matts_job_plugins.do_this",
                    "matts_job_plugins.do_that",
                    "matts_job_plugins.wait_here"
                ]
            }

..  http:post:: /job_plugins/reload

    Clears the current set of loaded job plugins and searches for them in the plugin load paths
    that can be accessed via GET /job_plugins/paths

    **Example request**:

        ..  sourcecode:: http

            POST /job_plugins/reload HTTP/1.1

    **Example response**:

        ..  sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json
            {
                job_plugins: [
                    "matts_job_plugins.do_this",
                    "matts_job_plugins.do_that",
                    "matts_job_plugins.wait_here"
                ]
            }

.. _REST-API-Jobs:

Jobs
====

Jobs are the main model in the hoplite application. In order to create and invoke a job you must first load a job plugin using the API above.
Once the job plugin is loaded you can create it via a job plugin's name. The name is what you define on the left side of the equals sign
in your entry points::

    Entry Point: "job_name=my_package.module_name"

    plugin_name: "job_name"

..  http:get:: /jobs

    All jobs that have been created.

    **Example request**:

    .. sourcecode:: http

        GET /jobs HTTP/1.1
        Accept: application/json

    **Example response**:

    ..  sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json
        {
            jobs:
            [
                {
                    "uuid": "755eeb1f-4ac7-4db9-b3a7-ce5b5f238eb9",
                    "plugin_name": "Run LV Test",
                    "running": true,
                    "finished": false,
                    "killed": false,
                    "config": { "VI": "test.vi" }
                    "status": { "state": "Running" }
                }
                {
                    "uuid": "a3cfb65d-cde0-409b-a2d7-99f758041e8a",
                    "plugin_name": "Provision Slave"
                    "running": false,
                    "finished": true,
                    "killed": true,
                    "config": { "ESXiServerAddr": 10.2.327.3, "OS": "Windows 8" },
                    "status": { "SlaveIP": 10.2.22.283 }
                }
            ]
        }

    :statuscode 200: No Error

..  http:post:: /jobs

    Create a job. If the job throws an exception the exception
    information will be put in the status of the job under the key "exception"

    :jsonparam string name: the name of the job to create
    :jsonparam object config: the configuration data for the job
    :jsonparam boolean run: if set to true the job will run as soon as it is able to

    **Example request**:

    ..  sourcecode:: http

        POST /jobs HTTP/1.1
        Content-Type: application/json
        {
            "plugin_name": "example_plugins.do_something_really_important",
            "config": { "really_important_path": "/hello/moto" },
            "run": "False"
        }


    **Example response**:

    :status 201: The job was created
    :status 404: Cannot create a job because the specified name does not exist

..  http:get:: /jobs/running

    A list of all the currently running jobs

    **Example Response**:

    ..  sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json
        {
            jobs:
            [
                {
                    "uuid": "755eeb1f-4ac7-4db9-b3a7-ce5b5f238eb9",
                    "plugin_name":d "riott_plugins.run_lv_test",
                    "running": true,
                    "finished": false,
                    "killed": false,
                    "config": { "VI": "test.vi" }
                    "status": { "state": "Running" }
                }
                {
                    "uuid": "a3cfb65d-cde0-409b-a2d7-99f758041e8a",
                    "plugin_name": "riott_plugins.provision_slave"
                    "running": true,
                    "finished": false,
                    "killed": false,
                    "config": { "ESXiServerAddr": 10.2.327.3, "OS": "Windows 8" },
                    "status": { "state": "Provisioning" }
                }
            ]
        }

    :statuscode 200: No Error

..  http:get:: /jobs/(int:job_uuid)

    The job with (job_uuid)

    **Example Response**:

    ..  sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json
        {
            job:
                {
                    "uuid": "8b7fea59-2c0d-4afa-8109-2bc0a26ec865",
                    "name": "Run LV Test",
                    "running": true,
                    "finished": false,
                    "killed": false,
                    "config": { "VI": "test.vi" }
                    "status": { "state": "Running" }
                }
        }

    :statuscode 200: No Error
    :statuscode 404: The job with uuid (job_uuid) was not found

..  http:put:: /jobs/(int:job_uuid)

    Edit the job with (job_uuid). Only the status of the job can be updated.
    All other paramters will be ignored

    :jsonparam object status: This will replace the status currently on the job
    :jsonparam string api_key: This is required. The API key is only known by the running job,
               only it can update its status.

    **Example Request**:

    ..  sourcecode:: http

        PUT /jobs/8b7fea59-2c0d-4afa-8109-2bc0a26ec865 HTTP/1.1
        Content-Type: application/json
        {
            "status": { "statue": "Running", "some_status_key": "updated value for key" },
            "api_key": "94e9979c-ef59-4b20-8dae-793c94c731ff"
        }

    **Example Response**:

    ..  sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json
        {
            job:
                {
                    "uuid": "8b7fea59-2c0d-4afa-8109-2bc0a26ec865",
                    "name": "custom_plugins.get_vi_info",
                    "running": true,
                    "finished": false,
                    "killed": false,
                    "config": { "VI": "test.vi" }
                    "status": { "state": "Running",
                                "some_status_key": "updated value for key" }
                }
        }


    :status 200: Job successfully updated
    :status 403: You provided keys that cannot be updated on the object
    :status 404: The job with uuid (job_uuid) was not found

..  http:put:: /jobs/(int:job_uuid)/start

    Starts the job in a new process

    **Example Response**

    ..  sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json
        {
            "uuid": "8b7fea59-2c0d-4afa-8109-2bc0a26ec865",
            "started": true
        }

    :status 200: Job was started
    :status 404: Job with uuid (job_uuid) was not found


..  http:put:: /jobs/(int:job_uuid)/kill

    Kills the process running the job. On Unix this is done using the SIGTERM signal;
    on Windows TerminateProcess() is used.


    **Example Response**

    ..  sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json
        {
            "uuid": "8b7fea59-2c0d-4afa-8109-2bc0a26ec865",
            "killed": true
        }

    :status 200: Job was sent the kill signal
    :status 404: Job with uuid (job_uuid) was not found

