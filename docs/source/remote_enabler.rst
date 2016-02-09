.. _remote-enabler:

Remote Enabler
==============

This module provides the means to execute functions and class methods on a remote machine. When a class or function is
decorated with the :ref:`remotify <remotify>` decorator, the class or module is given additional functions which can be used to
execute the original code on a remote machine which is running Hoplite.

Decorating functions
--------------------

When the decorator is used to decorate a module-level function, then that module will be enhanced to allow that
function to be called remotely through hoplite. As an example, if a function is decorated as follows::

    @remotify(__name__)
    def do_stuff(input_1, input_2):
        ...

Then two additional functions will be added to the module::

    def remote_do_stuff(remote_machine_address, *args, **kwargs):
        ...

    def remote_async_do_stuff(remote_machine_address, *args, **kwargs):
        ...

In these new functions, \*args and \*\*kwargs represent all of the arguments required by the original function.
"remote_machine_address" is the IP address or hostname of the machine on which the function will be remotely
called. If the remote machine is running Hoplite on a port other than the default (5000), then
"remote_machine_address" can be given in the form "address:port"

When the remote_do_stuff function is called, the Hoplite installation on the local machine will attempt to connect
to a Hoplite server running on the remote machine and run the function on it. Arguments passed to the function are
passed through the network to the remote Hoplite server, and so in most cases it should seem as if the function is
running on the local machine, except that the operations themselves will affect *only* the remote machine. There are
several cases in which this does not quite work, which you can read about :ref:`below <knownissues>`

When the remote_async_do_stuff function is called, a RemoteAsyncJobWrapper object will be returned which can be
used to start the function asynchronously. This object implements the same public functions as the RemoteJob class,
and so can be used in the same way. When the function is run, it operates in the same way as the remote_do_stuff
function does, except that it is run asynchronously. This means that any exceptions which occur will not be raised
until the job status is checked (by joining to the job, checking if the job is finished, etc.).

Decorating classes
------------------

When this decorator is used to decorate a class, then every method in the class (besides those starting with __, and
besides those excluded from the optional list of methods to make remotable) will be enhanced to allow for remote
operation through hoplite. The effect is essentially the same as when a module-level function is decorated, except
that the functions are class methods. As an example, if a class is decorated as follows::

    @remotify(__name__)
    class Foo:
        def do_stuff(self, input_1, input_2):
            ...

Then two additional methods will be added to the class::

    def remote_do_stuff(self, remote_machine_address, *args, **kwargs):
        ...

    def remote_async_do_stuff(self, remote_machine_address, *args, **kwargs):
        ...

In these new methods, self is the class instance (as would be expected). \*args and \*\*kwargs represent all of the
arguments required by the original method. "remote_machine_address" is the IP address or hostname of the machine
on which the method will be remotely called. If the remote machine is running Hoplite on a port other than the
default (5000), then "remote_machine_address" can be given in the form "address:port"

When called, the methods operate in the same way as module-level decorated functions. The primary difference is
that the class instance is pickled and sent over the network to the remote Hoplite server, and so the class state
at the time of calling the method is used when the method is called on the remote machine.

In cases where it is desirable that some, but not all, methods in the class be made remotable, it is possible to
specify a list of the methods that should be made remotable. For example, if a class is decorated as follows::

    @remotify(__name__, ['func_1', 'func_3'])
    class Foo:
        def func_1(self, input_1, input_1):
            ...

        def func_2(self, input_a, input_b):
            ...

        def func_3(self, input_i, input_ii):
            ...

Then four additional methods will be added to the class::

    def remote_func_1(self, remote_machine_address, *args, **kwargs):
        ...

    def remote_async_func_1(self, remote_machine_address, *args, **kwargs):
        ...

    def remote_func_3(self, remote_machine_address, *args, **kwargs):
        ...

    def remote_async_func_3(self, remote_machine_address, *args, **kwargs):
        ...

It should be noted that if an empty list is provided, or if no second argument is provided, then the decorator will
add remote capabilities to all methods in the class (excepting those beginning with __)

Inheritance
-----------

In cases where inheritance is used in a class, then remoted methods are inherited in the same way other methods
are inherited, and any inherited methods which are not already made remotable will be made remotable. For the sake
of clarity, here is a list of rules governing the inheritance of remoted methods:

- If a parent class is decorated, but a class which inherits from it is not decorated, then all of
  the methods in the parent class which were made remotable are passed on to its children. No methods
  in the child will be made remotable.
- If a child class is decorated but its parent is not, then methods in both the parent and the child
  class will be made remotable (because inherited methods are always made remotable)
- If both a child and a parent class are decorated, then methods in both classes will be made
  remotable. However, methods in the parent class will only be made remotable once (for example,
  remote_do_stuff in the parent will not get remoted to become remote_remote_do_stuff in the child)

Remote asynchronous function calls
----------------------------------

When a *remote_async_...* function is called on a remoted module or class, an instance of the
:ref:`RemoteAsyncJobWrapper <jobwrapper>` class is returned which can be used to interact with the function. This class
implements the same public methods as the RemoteJobClass.

Remote Exceptions
-----------------

If a function which is called remotely raises an exception, Hoplite does its best to raise that same exception on the
local machine. What this means is that (if possible) the same exception will be raised on the local machine, containing
the same information, and displaying nearly the same traceback as would have been displayed on the remote machine.
However, in addition to the traceback for the remote function call, the traceback leading up to the call to the remote
function will also be displayed. As an example, suppose that you have a package called "important_stuff", which contains
the following files:

**other_functions.py**::

    from hoplite.remote_enabler import remotify


    @remotify(__name__)
    def foo():
        bar()

    def bar():
        baz()

    def baz():
        print 'Hello world!'
        raise EnvironmentError('Uh-oh, something went wrong')

**main.py**::

    from other_functions import remote_foo


    def call_remote_function():
        remote_foo('localhost')

    def main():
        call_remote_function()

Running the main() function in important_stuff.main results in the following output *on the local machine* (note the
structure of the traceback)::

    >>> from important_stuff.main import main
    >>> main()
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "c:\Python27\lib\site-packages\important_stuff-15.0.0.dev0-py2.7.egg\important_stuff\main.py", line 8, in main
        call_remote_function()
      File "c:\Python27\lib\site-packages\important_stuff-15.0.0.dev0-py2.7.egg\important_stuff\main.py", line 5, in call_remote_function
        remote_foo('localhost')
      File "c:\Python27\lib\site-packages\hoplite\remote_enabler.py", line 399, in _remote_module_func
        e.raise_remote_exception()  # ALL TRACEBACK ENTRIES BELOW THIS ARE FROM THE REMOTE MACHINE
      File "c:\Python27\lib\site-packages\important_stuff-15.0.0.dev0-py2.7.egg\important_stuff\other_functions.py", line 5, in foo
        bar()
      File "c:\Python27\lib\site-packages\important_stuff-15.0.0.dev0-py2.7.egg\important_stuff\other_functions.py", line 8, in bar
        baz()
      File "c:\Python27\lib\site-packages\important_stuff-15.0.0.dev0-py2.7.egg\important_stuff\other_functions.py", line 12, in baz
        raise EnvironmentError('Uh-oh, something went wrong')
    EnvironmentError: Uh-oh, something went wrong

In the traceback, the divide between the local and remote call stacks is at "e.raise_remote_exception()" in
_remote_module_func. A comment has been included to try and make this more obvious, since there is no other way to
indicate that the bottom half of the traceback is referring to the call stack on the remote machine.

Even though the traceback is a little more difficult to read this way, having both the local and remote call stacks
displayed in the traceback should make it much easier to debug remote functions.

In the event that the exception on the remote machine cannot be raised on the local machine, a JobFailedError will be
raised instead. The reason for this would be if the exception class cannot be pickled, which is the case for any
custom exceptions which accept arguments in their __init__ functions. Suppose that other_functions.py was written
slightly differently:

**other_functions.py**::

    from hoplite.remote_enabler import remotify


    class MyCustomError(Exception):
        def __init__(self, message, custom_val):
            super(Exception, self).__init__(message)
            self.custom_val = custom_val

        def __str__(self):
            return 'Something bad happened: {}'.format(self.custom_val)

    @remotify(__name__)
    def foo():
        bar()

    def bar():
        baz()

    def baz():
        print 'Hello world!'
        raise MyCustomError('Error!', 12345)

Calling the foo() function remotely in the same way as before produces the following output on the local machine::

    >>> from important_stuff.main import main
    >>> main()
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "c:\Python27\lib\site-packages\important_stuff-15.0.0.dev0-py2.7.egg\important_stuff\main.py", line 8, in main
        call_remote_function()
      File "c:\Python27\lib\site-packages\important_stuff-15.0.0.dev0-py2.7.egg\important_stuff\main.py", line 5, in call_remote_function
        remote_foo('localhost')
      File "c:\Python27\lib\site-packages\hoplite\remote_enabler.py", line 399, in _remote_module_func
        e.raise_remote_exception()  # ALL TRACEBACK ENTRIES BELOW THIS ARE FROM THE REMOTE MACHINE
      File "c:\Python27\lib\site-packages\important_stuff-15.0.0.dev0-py2.7.egg\important_stuff\other_functions.py", line 14, in foo
        bar()
      File "c:\Python27\lib\site-packages\important_stuff-15.0.0.dev0-py2.7.egg\important_stuff\other_functions.py", line 17, in bar
        baz()
      File "c:\Python27\lib\site-packages\important_stuff-15.0.0.dev0-py2.7.egg\important_stuff\other_functions.py", line 21, in baz
        raise MyCustomError('Error!', 12345)
    hoplite.exceptions.JobFailedError: Full traceback for all jobs descended from current job:
       In job with UUID: 9afae195-d70f-44f3-9250-970ea09bc0af
       Running on machine: localhost
          Traceback:
          File "c:\Python27\lib\site-packages\hoplite\server\jobs\job_wrapper.py", line 31, in job_wrapper
             module.run(config, status_updater)
          File "c:\Python27\lib\site-packages\hoplite\builtin_plugins\remote_enabler_module_job.py", line 45, in run
             return_values = getattr(mod, function_name)(*args, **kwargs)  # Run function
          File "c:\Python27\lib\site-packages\important_stuff-15.0.0.dev0-py2.7.egg\important_stuff\other_functions.py", line 14, in foo
             bar()
          File "c:\Python27\lib\site-packages\important_stuff-15.0.0.dev0-py2.7.egg\important_stuff\other_functions.py", line 17, in bar
             baz()
          File "c:\Python27\lib\site-packages\important_stuff-15.0.0.dev0-py2.7.egg\important_stuff\other_functions.py", line 21, in baz
             raise MyCustomError('Error!', 12345)
       Root Error Type: <class 'important_stuff.other_functions.MyCustomError'>
       Root Error Message: Error!

Since MyCustomError is not picklable, Hoplite will raise a JobFailedError. Since this exception is tailored for
this specific case, it is possible to provide more information about the error in the remote function than if the
original exception were raised. This is why the error message is longer and more detailed.

Importing
---------

Because the remote functions are added when the enclosing module is imported, Python IDEs will complain that the
functions cannot be found when you try and import them directly. However, it does work to import the remote functions
just as you would any other function. It should be noted that importing the non-remoted function does not give you
access to the remoted function. For example, if a function called "do_stuff" is defined in a module "foo.bar", then
the following does **NOT** work::

    from foo.bar import do_stuff
    remote_do_stuff('remote_machine_name', 'baz')

However, the following are all valid ways of importing and running the remote_do_stuff function::

    from foo.bar import remote_do_stuff
    remote_do_stuff('remote_machine_name', 'baz')

    from foo import bar
    bar.remote_do_stuff('remote_machine_name', 'baz')

    import foo.bar
    foo.bar.remote_do_stuff('remote_machine_name', 'baz')

    import foo.bar as bob
    bob.remote_do_stuff('remote_machine_name', 'baz')

    from foo import bar as fred
    fred.remote_do_stuff('remote_machine_name', 'baz')

Logging
-------

Hoplite has limited support for capturing logging calls made in remote functions. Before calling the function on the
remote machine, Hoplite adds a handler to the root logger for the process the remote function will run in. This means
that all logs will be captured, not just the ones from the remote function. However, it is the most reliable way to
capture logs which does not require making assumptions about how logging is set up for the remote function.

Logging calls with level INFO and higher will be logged to the console, and logging calls with level DEBUG and higher
will be logged to a file on the remote machine. Logging to the local machine is currently not supported.

Log files for remoted functions are placed in a hierarchy under the root folder c:\\logs\\hoplite\\remoted_functions on
the remote machine. The location of the log file within this folder is determined by its namespace. For example, if a
module has the namespace my_module.cool_functions, then the log files for its functions which are called remotely will
be placed in the folder c:\\logs\\hoplite\\remoted_functions\\my_module\\cool_functions. The names of the files are
based on the name of the functions which are called, as well as the time the function was called (YYYY-MM-DD HH-MM-SS).
In the event that multiple calls of the same remote function occur within a single second, _1 will be appended to the
end of the filename for the second call, then _2 for the third, etc.

As an example, suppose there is a function (in a module my_module.cool_functions) which is defined as follows::

    @remotify(__name__)
    def do_something(val_a, val_b):
        logger.info('Hello world! Received values {} and {}'.format(val_a, val_b))
        return val_a + val_b
The log file from calling this function remotely might look like this:

**2015-05-19 18-16-34 do_something.log**::

    INFO     18:16:34 AM   remote_enabler_module_job.py:43    MainThread      Beginning execution of do_something with args: (123, 456) and kwargs: {}
    INFO     18:16:34 AM              cool_functions.py:21    MainThread      Hello world! Received values 123 and 456
    INFO     18:16:34 AM   remote_enabler_module_job.py:59    MainThread      Returning from do_something with return value(s): (579)

Documentation
-------------

The remotify decorator also adds documentation for the newly added functions/methods. This includes a short description
of how to use the remoted function, as well as a link to the documentation for the original function. Here is an
example of what this looks like:

**Python code**::

    def my_func(arg1, arg2):
        """Function to do stuff.

        My_func is a function which does nothing in particular. It serves primarily as an example.

        :param arg1: A number which will be printed to the console
        :type arg1: int
        :param arg2: A string which will also be printed
        :type arg2: str
        :returns: The concatenated number and string
        """
        concat_string = str(arg1) + arg2
        print concat_string
        return concat_string

**The resulting documentation**:

..  autofunction:: hoplite.remote_enabler.my_func
..  autofunction:: hoplite.remote_enabler.remote_my_func
..  autofunction:: hoplite.remote_enabler.remote_async_my_func

Here is another example, this one of a remoted class:

**Python code**::

    @remotify(__name__)
    class Foo(object):
        def __init__(self, val_1):
            """Initialize a new instance of the Foo class.

            :param val_1: Any value. Doesn't matter what value it is
            """
            self.val_1 = val_1

        def print_a_val(self):
            """Prints a value.

            Prints the value that was passed in when the class instance was initialized.
            """
            print self.val_1

        def print_another_val(self, another_val):
            """Prints another value.

            Prints a value passed in by the user. It can be the same as the other value if desired.

            :param another_val: Another value. Doesn't matter what value it is
            """
            print another_val

**The resulting documentation**:

..  autoclass:: hoplite.remote_enabler.Foo
    :members:

Examples
--------

**NOTE:** For each of these examples, it is implied that the sample code is contained in a python package, and that the
package is installed on the remote machine.

Suppose you want a way to execute windows commands on a remote machine (with hostname machine-123) and parse the results
using Python on your local machine. One way to do this is as follows:

**tasks.py**::

    import subprocess

    from hoplite.remote_enabler import remotify

    @remotify(__name__)
    def run_win_command(command):
        output = subprocess.check_output(command)
        return output

**main_script.py**::

    import tasks

    print tasks.remote_run_win_command('machine-123', 'echo Hello World!')
    print tasks.remote_run_win_command('machine-123', 'hostname')  # Command "hostname" prints the machine's hostname

**Output**::

    Hello World!
    machine-123


As another example, suppose you write a class that can be used to parse text files and return the names of all files
which contain lines that match a certain pattern. You could do it this way:

**parser.py**::

    import os
    import re

    from hoplite.remote_enabler import remotify

    @remotify(__name__)
    class Parser(object):
        def __init__(self, folder_path, extension):
            self.folder_path = folder_path
            self.extension = extension

        def parse_folder(self, regex):
            matches = []
            for root, _, filenames in os.walk(self.folder_path):
                for filename in filenames:
                    if not filename.endswith(self.extension):
                        continue
                    with open(os.path.join(root, filename)) as f:
                        for line in f:
                            if re.search(regex, line):
                                matches.append(os.path.join(root, filename))
                                break
            return matches

**main_script.py**::

    from parser import Parser

    my_parser = Parser(r'C:\\users\\foo\\desktop\\python_files', '.py')
    results = my_parser.remote_parse_folder('machine-123', r'from .* import \*')  # Find all scripts which do "import *"
    print 'Files which use "import *":\\n'
    for result in results:
        print result

**Sample output**::

    Files which use "import *":

    C:\\users\\foo\\desktop\\python_files\\project_foo\\stuff.py
    C:\\users\\foo\\desktop\\python_files\\project_bar\\more_stuff.py
    C:\\users\\foo\\desktop\\python_files\\project_baz\\even_more_stuff.py


For another example, suppose you wanted to search on a remote machine for a file. You know it will take a long time, and
you want the local machine to perform some tasks while the remote machine is busy searching. You could do this in the
following way:

**searcher.py**::

    import os

    from hoplite.remote_enabler import remotify

    @remotify(__name__)
    def search_for_file(search_filename, root_dir):
        for root, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename == search_filename:
                    return os.path.join(root, filename)
        raise OSError('File {} not found anywhere in {} or its subdirectories'.format(filename, root_dir))

**main_script.py**::

    import searcher
    import time

    job = searcher.remote_async_search_for_file('machine-123', 'hard_to_find.foo', 'C:\')
    job.start()

    print 'Aha, I can do whatever I want, because I'm not blocking'

    start = time.time()
    filepath = job.join()
    end = time.time()

    print 'File hard_to_find.foo found at location "{}"'.format(filepath)
    print 'While waiting for the file to be found, I had {} seconds of downtime'.format(round(end - start, 2))


**Sample output**::

    Aha, I can do whatever I want, because I'm not blocking
    File hard_to_find.foo found at location "C:\\users\\foo\\stuff\\hard_to_find.foo"
    While waiting for the file to be found, I had 78.37 seconds of downtime

.. _knownissues:

Caveats and Known Issues
------------------------

- The names of functions decorated with remotify **CANNOT** start with remote_ or async_. If two functions were
  defined, do_something and remote_do_something, and they were both decorated with remotify, then there would be a
  conflict between the preexisting remote_do_something and the remoted version of do_something. The same problem arises
  if two functions called do_something and async_do_something were both decorated with remotify, because
  remote_async_do_something would be ambiguous. To avoid these types of problems, the remotify decorator will raise an
  exception if a remoted function starts with either remote_ or async_.
- If changes to the class state are made on the remote machine, then those are **NOT** reflected in the class instance
  on the local machine
- Any globally defined variables are not passed to the remote machine, and cannot be accessed
- Any changes made to mutable arguments passed to remoted functions or methods will **NOT** be reflected in the local
  copies of the arguments
- If a remotely-called function or method raises a custom exception which accepts multiple arguments in its __init__
  function, there may be problems with raising the same error on the local machine. This is due to a limitation in the
  pickle module - pickling of custom exceptions doesn't work right when the __init__ takes more than one argument
- The traceback of exceptions raised in remote functions or methods will reflect the stack on the local machine, rather
  than the stack on the remote machine. However, printing the exception or calling str() on it will display detailed
  information which includes the stack trace for the remote machine
- Class methods decorated with @staticmethod will not be made remotable. However, this feature will likely be supported
  in a later version of Hoplite
- Decorated classes must be picklable
- The package that contains the remoted functions or classes must be installed on both the local machine and the
  remote machine. Also, if the versions are not the same then there may be unpredictable results
- The same version of Hoplite must be installed on both the local machine and the remote machine. If not, then obscure
  and hard-to-debug errors may result
- This decorator may not play well with classes which use custom metaclasses. For example, if a metaclass is used which
  adds methods to the class, they might not get made remotable. Use at your own risk

API
---

.. _remotify:

..  autofunction:: hoplite.remote_enabler.remotify

.. _jobwrapper:

..  autoclass:: hoplite.remote_enabler.RemoteAsyncJobWrapper
    :members:
    :undoc-members:

..  autoclass:: hoplite.remote_enabler.RemoteEnablerMetaClass
    :members: