Hoplite
=======

Overview
--------
Hoplite's main purpose is to make it easy to remotely invoke python code.

It does this by loading all modules registered with the setuptool's entry point
'hoplite.jobs'. These 'jobs' satisfy a simple interface, which allows Hoplite
to run them, and to report on their status.

Installation
------------
Hoplite can be installed by cloning the master branch and then in a command
line in the directory of setup.py run:

   pip install --pre .

hoplite.remotify
----------------
Since creating plugins for simple tasks is cumbersome, Hoplite also provides
a very simple way of running existing Python code on remote machines. This
functionality is provided in the form of a decorator `@remotify`which, when 
applied to a function or class, adds the ability to execute the function or
class methods on the remote machine.

For example if you create a function:
   from hoplite import remotify

   @remotify(__name__)
   def foo(arg1):
      print(arg1)

A new function will be added to the module on import called remote_foo that
can be called like:
   remote_foo(remote_host_name, arg1)

This will serialize the arguments and send them to a hoplite server running
on remote_host_name.

Classes can also be made remoteable by adding the same decorator before the
class definition.  This will have the effect of adding new methods to the
class called `remote_method_name1`, `remote_method_name2`, etc.

Note code to be remoted must be available in the python environment on
both the client and server when remote versions of the functions are
enabled.

For more information refer to documentation for hoplite.remotify.

Starting Hoplite
----------------
To start the server invoked `hoplite-server` on the command line.

On windows you can also enable hoplite-server to start on boot by
calling `hoplite-auto-start`.

Development
-----------
Code in hoplite attempts to conform to PEP8.  Any pull requests should conform
to PEP8.

License
-------
The MIT License (MIT) Copyright (c) 2016 National Instruments

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
