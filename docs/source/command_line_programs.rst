Command-Line Programs
*********************

Three command line applications are provided with Hoplite: hoplite-server, hoplite-client, and hoplite-auto-start. In
most cases, only hoplite-server and hoplite-autostart will be used, as hoplite-client is primarily useful when manually
running job plugins. In most cases, Hoplite will be started on a remote machine using hoplite-server, or configured to
run on startup using hoplite-auto-start, and then the :ref:`Remote Enabler API <remote-enabler>` will be used on the
client side to interact with Hoplite.

..  _hoplite-server:

hoplite-server
==============

..  argparse::
    :module: hoplite.main
    :func: get_server_options_parser
    :prog: hoplite-server


.. _hoplite-client:

hoplite-client
==============

..  argparse::
    :module: hoplite.main
    :func: get_client_options_parser
    :prog: hoplite-client

hoplite-auto-start
==================

When executed, this will configure the current machine to run Hoplite at startup. Specifically, a batch file which
calls hoplite-server is copied to the Windows startup folder (and therefore, this only works on Windows). If the option
--disable or -d is provided, then the current machine will be configured so that Hoplite will no longer run at startup.