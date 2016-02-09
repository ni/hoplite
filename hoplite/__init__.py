"""
Overview
========

Hoplite's main purpose is to make it easy to remotely invoke python code.
It does this by loading all modules registered with the setuptool's entry point
'hoplite.jobs'. These 'jobs' satisfy a simple interface, which allows Hoplite
to run them, and to report on their status. For more information on building
modules to plug into Hoplite see :ref:`job-plugins`.

Since creating plugins for simple tasks is cumbersome, Hoplite also provides
a very simple way of running existing Python code on remote machines. This
functionality is provided in the form of a decorator which, when applied to a
function or class, adds the ability to execute the function or class methods
on the remote machine. Detailed information on how to do this is provided
:ref:`here <remote-enabler>`.

Hoplite is split into a server and a client. The server can be invoked via the
command line with :ref:`hoplite-server` and the client is invoked with
:ref:`hoplite-client`. The client is used to manage local and
remote hoplite-server instances.
"""
from hoplite.remote_enabler import remotify
from hoplite.public_api import (
    is_hoplite_available,
    wait_for_hoplite,
    remote_install_python_package,
    remote_uninstall_python_package)
