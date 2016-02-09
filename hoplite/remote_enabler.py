from functools import wraps
import logging
import pickle
import sys
import types

from hoplite import client
from hoplite.exceptions import JobFailedError
from globals import HopliteClientSettings


def remotify(module_name, functions=None, add_documentation=True):
    """
    Decorator which can be used to add remote capabilities to functions or
    classes.

    By using this decorator on a function, the module which contains the
    function will be given two additional functions which provide the means
    for calling the function on a remote machine running Hoplite. The names of
    these two functions are remote\_(name of original function) and
    remote_async\_(name of original function). The remote\_function calls the
    function or method asynchronously on the remote machine, and the
    remote_async\_ function returns an object which can be used to run the
    function asynchronously on the remote machine.

    By using this decorator on a class, the class will be enhanced with
    remote\_ and remote_async\_ methods which serve the same purpose as the
    remote\_ and remote_async\_ functions described above.

    In either case, documentation will be added to the new functions/methods
    giving a short description of how to use them and a link to the original
    function. This feature can be disabled by passing in False for the
    add_documentation parameter.

    For additional details, see the above documentation and examples.

    :param module_name: The namespace for the module which contains this class
      or function. This should simply be passed in as __name__
      (e.g. @remotify(__name__)
    :type module_name: str
    :param functions: A list of names of the methods which should be made
      remotable. This only applies when decorating classes. If no list is
      provided, then all methods in the class (besides those starting with __)
      will be made remotable
    :param add_documentation: If true, then the functions or methods which are
      added will be given documentation explaining how they are to be used, and
      linking to the original function. If false, then they will be given no
      documentation, though they will still show up in the Sphinx documentation
      if the associated rst file indicates that undocumented functions/methods
      should be included
    :type add_documentation: bool
    :type functions: list of [str]
    """
    if functions is None:
        functions = []

    def inner(obj):
        # If decorating a class, then add methods to the class. For some
        # reason, if a class which inherits from another class is decorated,
        # then the type of object passed in is "type" rather than "class".
        # However, the class can still be decorated just fine.
        if isinstance(obj, types.ClassType) or isinstance(obj, type):
            class_obj = obj  # Rename for clarity
            class_item_names = dir(class_obj)
            for item_name in class_item_names:
                if len(functions) > 0 and item_name not in functions:
                    continue
                if isinstance(getattr(class_obj, item_name), types.MethodType):
                    func = getattr(class_obj, item_name)
                    name = func.__name__
                    # Skip "private" functions as well as inherited functions
                    # that have already been remoted
                    if name.startswith('__') or hasattr(func, '___remoted_by_hoplite___') \
                            or hasattr(func, '___is_hoplite_remotable___'):
                        continue
                    if name.startswith('remote_') or name.startswith('async_'):
                        raise AttributeError(
                            'Unable to add remote capability to function {0}:'
                            ' function cannot begin with "remote_" or '
                            '"async_"'.format(name))
                    class_func = wraps(func)(remote_func_builder(name))
                    async_class_func = wraps(func)(
                        remote_async_func_builder(name))
                    class_func.__name__ = 'remote_' + class_func.__name__
                    async_class_func.__name__ = 'remote_async_' + \
                        async_class_func.__name__
                    if add_documentation:
                        class_func.__doc__ = _get_remote_docstring(
                            'meth', '{}.{}'.format(
                                module_name, class_obj.__name__), func.__name__
                        )
                        async_class_func.__doc__ = _get_remote_async_docstring(
                            'meth', '{}.{}'.format(
                                module_name, class_obj.__name__), func.__name__
                        )
                    else:
                        class_func.__doc__ = None
                        async_class_func.__doc__ = None
                    # Need to set attribute on __func__, which is the
                    # underlying function stored in the instancemethod This
                    # adds a tag to the function being remotified so it is not
                    # remoted twice if a remoted class is inherited
                    setattr(func.__func__, '___remoted_by_hoplite___', True)
                    # Set attribute to remotable functions for identification
                    setattr(class_func, '___is_hoplite_remotable___', True)
                    setattr(
                        async_class_func, '___is_hoplite_remotable___', True)
                    setattr(class_obj, 'remote_' + name, class_func)
                    setattr(
                        class_obj, 'remote_async_' + name, async_class_func)
        # If decorating a module function (not a class function)
        elif isinstance(obj, types.FunctionType):
            func = obj  # Rename for clarity
            module = sys.modules[module_name]
            name = func.__name__
            if name.startswith('remote_') or name.startswith('async_'):
                raise AttributeError(
                  'Unable to add remote capability to function {0}:'
                  ' function cannot begin with "remote_" or "async_"'.format(
                      name))
            mod_func = wraps(func)(
                remote_module_func_builder(name, module_name))
            async_mod_func = wraps(func)(
                remote_module_async_func_builder(name, module_name))
            mod_func.__name__ = 'remote_' + mod_func.__name__
            async_mod_func.__name__ = 'remote_async_' + async_mod_func.__name__
            if add_documentation:
                mod_func.__doc__ = _get_remote_docstring(
                    'func', module_name, func.__name__)
                async_mod_func.__doc__ = _get_remote_async_docstring(
                    'func', module_name, func.__name__)
            else:
                mod_func.__doc__ = None
                async_mod_func.__doc__ = None
            # Set attribute to remotable and remoted functions for
            # identification
            setattr(func, '___remoted_by_hoplite___', True)
            setattr(mod_func, '___is_hoplite_remotable___', True)
            setattr(async_mod_func, '___is_hoplite_remotable___', True)
            setattr(module, 'remote_' + name, mod_func)
            setattr(module, 'remote_async_' + name, async_mod_func)
        else:
            raise RuntimeError(
                'Unable to add remote capabilities to object {} which is of'
                ' type {}'.format(obj.__name__, type(obj))
            )
        return obj
    return inner


def _get_remote_docstring(ref_type, namespace, func_name):
    return 'This function calls :{0}:`{1}.{2}` on a remote machine which is ' \
           'running a Hoplite server.\n\n' \
           ':param remote_machine_address: The hostname or IP address of the' \
           'remote machine\n' \
           ':ref_type remote_machine_address: str\n' \
           ':param args: Positional arguments for {2}\n' \
           ':param kwargs: Keyword arguments for {2}\n' \
           ':returns: The value or values returned by {2} after it finishes ' \
           ' running on the remote machine\n\n' \
           'This function raises the same exceptions as {2}. If an error ' \
           'occurs in the Hoplite framework, or if the original exception ' \
           'raised on the remote machine cannot be raised on the local ' \
           'machine, then a JobFailedError (from the Hoplite module) will ' \
           'be raised.'.format(
               ref_type, namespace, func_name)


def _get_remote_async_docstring(ref_type, namespace, func_name):
    return 'This function returns an object which can be used to call ' \
           ':{0}:`{1}.{2}` asynchronously on a remote machine which is ' \
           'running a Hoplite server.  \n\n' \
           ':param remote_machine_address: The hostname or IP address of the' \
           ' remote machine\n' \
           ':ref_type remote_machine_address: str\n' \
           ':param args: Positional arguments for {2}\n' \
           ':param kwargs: Keyword arguments for {2}\n' \
           ':returns: An instance of the RemoteAsyncJobWrapper class, which ' \
           ' can be used to start {2} on the remote machine and query its ' \
           'status. This class implements the same public interface as the ' \
           'RemoteJob class in Hoplite, and therefore provides methods such ' \
           ' as start, join, and finished. When join is called, the class '\
           'will block until the function finishes executing on the remote ' \
           'machine, and then will return the values returned by the ' \
           'remotely executed function.\n' \
           ':rtype: RemoteAsyncJobWrappper\n\n' \
           'This function raises the same exceptions as {2}. If an error ' \
           'occurs in the Hoplite framework, or if the original exception ' \
           'raised on the remote machine cannot be raised on the local ' \
           'machine, then a JobFailedError (from the Hoplite module) will ' \
           'be raised. Note that any exceptions raised on the remote ' \
           'machine will not be called until the status of the job is ' \
           'checked, such as when "finished" or "join" are called on the ' \
           'RemoteAsyncJobWrappper object.'.format(
               ref_type, namespace, func_name)


class RemoteEnablerMetaClass(type):
    """
    .. deprecated:: 15.0.0.dev25
       Use the :ref:`remotify decorator <remotify>` instead

    Add remote capabilities to a class.

    If a class opts to use this as its metaclass, then every function in the
    class (besides those starting with __) will be enhanced to allow for remote
    operation through hoplite. As an example, if there is a function defined
    as::

        def do_stuff(self, input_1, input_2):
            ...

    Then two additional functions will be added to the class::

        def remote_do_stuff(self, remote_machine_address, *args, **kwargs):
            ...

        def remote_async_do_stuff(self, remote_machine_address, *args, **kwargs)
            ...

    In these new functions, \*args and \*\*kwargs represent all of the
    arguments required by the original function. "remote_machine_address" is
    the IP address or hostname of the machine on which the function will be
    run remotely. If the remote machine is running Hoplite on a port other
    than the default (5000), then "remote_machine_address" can be given in the
    form "address:port"

    When the remote_do_stuff function is called, hoplite will attempt to
    connect to the Hoplite server on the remote machine and run the function
    on it, using the current state of the object on the local machine. In
    other words, it should seem as if the function is running on the local
    machine, except that the operations themselves will affect *only* the
    remote machine. In particular, if the function being run remotely changes
    the class instance, those changes will not be reflected on the local
    machine. This must be kept in mind when creating classes that will be made
    remotable - any changes of state must be sent back to the local machine as
    return values. That includes reference variables passed as function
    parameters that would normally not need to be returned.

    When the remote_async_do_stuff function is called, a RemoteAsyncJobWrapper
    object will be returned which can be used to start the function
    asynchronously. This object implements the same public functions as the
    RemoteJob class, and so can be used in the same way. When the function is
    run, it operates in the same way as the remote_do_stuff function does,
    except that it is run asynchronously. This means that any exceptions which
    occur will not be raised until the job status is checked.

    In cases where inheritance is used in a class, the behavior is governed by
    the following rules:

    - For each class which uses the metaclass, if it inherits from another
    class then that parent class must either use the metaclass as well (in
    which case all of its functions will be made available to the child as
    remotable functions) or the parent class must be a new-style class
    (inherit from "object"), in which case its functions will not be
    available to the child as remotable functions. If the parent class does
    not use the metaclass, and if it is not a new-style class, then a TypeError
    will be raised due to some technical issues with metaclasses and
    inheritance.

    - If a class uses the metaclass, then all classes which inherit from it
    (i.e. all of its descendants) will be made remotable. In other words, if a
    parent class uses the metaclass, then it as well as its child will be made
    remotable. The parent will have access to all its own functions as
    remotable functions, and the child will have access not only to all of its
    own functions, but also all of the parent's functions, as remotable
    functions. This holds true for all descendants.

    :returns: The class, enhanced to allow for remote functionality
    """
    def __new__(mcs, clsname, bases, dct):
        for name, val in dct.items():
            if (not name.startswith('__')) and hasattr(val, '__call__'):
                # Function must be built in a separate function and then
                # assigned here.  Otherwise, there are problems with each
                # function added to the class actually pointing to the same
                # thing.
                if name.startswith('remote_') or name.startswith('async_'):
                    raise AttributeError(
                        'Unable to add remote capability to function {0}:'
                        ' function cannot begin with "remote_" or '
                        '"async_"'.format(name))
                dct['remote_' + name] = remote_func_builder(name)
                dct['remote_async_' + name] = remote_async_func_builder(name)
        return type.__new__(mcs, clsname, bases, dct)


def remote_func_builder(function_name):
    """
    Build a function that will connect to a remote machine and execute a
    function on it.

    :param function_name: The name of the class function that will be called on
        the remote machine.  This is necessary because, even though it is
        technically something like remote_do_stuff that is called, it will be
        recognized as _remote_func instead.
    :returns: Function that, when called, will connect to a remote machine and
        execute the function represented by 'function_name'
    """

    def _remote_func(self, remote_machine_address, *args, **kwargs):
        """
        Call a function on a remote machine.

        Note that the class instance is pickled and sent to the remote machine.
        This is so the current state of the class will be utilized when the
        function is called on the remote machine. There are probably lots of
        corner cases in which this will cause problems. For example, you must
        be aware of side effects of the original function that you might be
        expecting to affect the local machine, because they will not do so.

        :param remote_machine_address: IP address or hostname of the remote
            machine on which the function will be run.
            If the remote machine is running Hoplite on a port other than the
            default (5000), then "remote_machine_address" can be specified in
            the form "address:port"
        :param remote_timeout: Timeout (in floating-point seconds) of the
            function
        :param *args: Normal arguments being passed to the remotely called
            function
        :param *kwargs: Keyword arguments being passed to the remotely called
            function
        :returns: The value(s) returned by the function which was called on the
            remote machine
        """
        logger = logging.getLogger(__name__)
        logger.addHandler(logging.NullHandler())

        remote_timeout = -1
        timeout_message = ''
        if kwargs.get('remote_timeout') is not None and kwargs['remote_timeout'] > 0.0:
            remote_timeout = kwargs['remote_timeout']
            kwargs.pop('remote_timeout')
            timeout_message = ' with timeout of {} seconds'.format(
                remote_timeout)

        args_string = args.__str__()
        kwargs_string = kwargs.__str__()
        if not HopliteClientSettings.debug:
            if len(args_string) > 33:
                args_string = args_string[0:30] + '...'
            if len(kwargs_string) > 33:
                kwargs_string = kwargs_string[0:30] + '...'
        logger.info('"{0}" on target "{1}" with args: {2} and '
                    'kwargs: {3}{4}'.format(
                        function_name,
                        remote_machine_address,
                        args_string,
                        kwargs_string,
                        timeout_message))
        config = {
            'args': pickle.dumps(args),
            'kwargs': pickle.dumps(kwargs),
            'instance': pickle.dumps(self),
            'function_name': function_name
        }
        job = None
        try:
            job_manager = client.remote_job_manager.RemoteJobManager(
                remote_machine_address)
            job = job_manager.create_job(
                'hoplite.plugins.remote_enabler_job', config)
            job.start()
            job.join(remote_timeout)

        except JobFailedError as e:
            if job is None:
                logger.error(
                    'Exception occurred while creating job to call "{0}" on'
                    ' "{1}": {2}'.format(
                        function_name, remote_machine_address, str(e))
                )
            else:
                logger.error(
                  'Exception occurred while calling "{0}" on '
                  ' "{1}": {2}'.format(
                      function_name,
                      remote_machine_address,
                      e.__str__())
                )
            # ALL TRACEBACK ENTRIES BELOW THIS ARE FROM THE REMOTE MACHINE
            e.raise_remote_exception()

        return_values = pickle.loads(job.status().get('return_values'))

        if return_values is None:
            return None

        # Convert return value into either a single value, or a tuple, so that
        # it appears the same as if the function were called on the local
        # machine
        if len(return_values) > 1:
            return_object = tuple(return_values)
        else:
            return_object = return_values[0]

        return_object_string = return_object.__str__()
        # limit return object string if not debugging
        if not HopliteClientSettings.debug and len(return_object_string) > 50:
            return_object_string = return_object_string[0:47] + '...'

        logger.debug('"{0}" on target "{1}" returned {2}'.format(
            function_name,
            remote_machine_address,
            return_object_string))
        return return_object
    return _remote_func


def remote_async_func_builder(function_name):
    """
    Build a function that will connect to a remote machine and create a job
    wrapper that can be used to run a function asynchronously

    :param function_name: The name of the class function that will be called on
        the remote machine.
    :returns: Function that, when called, will connect to a remote machine and
        create then return a job wrapper for running the specified function
    """

    def _remote_async_func(self, remote_machine_address, *args, **kwargs):
        """
        Create a job on a remote machine and return a wrapper so that it has
        the same interface as a job running on the local machine.

        ***NOTE*** It seems that join must always be eventually called on jobs,
        even if they have already finished. Otherwise, a process gets orphaned,
        causing problems with future operations.

        :param remote_machine_address: IP address or hostname of the remote
            machine on which the function will be run.  If the remote machine
            is running Hoplite on a port other than the default (5000), then
            the port can be specified in the form "address:port"
        :param *args: Normal arguments being passed to the remotely called
            function
        :param *kwargs: Keyword arguments being passed to the remotely called
            function
        :returns: A wrapper around the remote job
        """
        logger = logging.getLogger(__name__)
        logger.addHandler(logging.NullHandler())

        logger.debug(
            'Creating job "{0}" on target "{1}" with args: {2} and kwargs:'
            ' {3}'.format(
                function_name, remote_machine_address, args, kwargs)
        )
        config = {
            'args': pickle.dumps(args),
            'kwargs': pickle.dumps(kwargs),
            'instance': pickle.dumps(self),
            'function_name': function_name
        }
        job_manager = client.remote_job_manager.RemoteJobManager(
            remote_machine_address)
        job = job_manager.create_job(
            'hoplite.plugins.remote_enabler_job', config)
        return RemoteAsyncJobWrapper(job, function_name)
    return _remote_async_func


def remote_module_func_builder(function_name, module_name):
    """
    Build a function that will connect to a remote machine and execute a
    function on it.

    :param function_name: The name of the function that will be called on the
        remote machine.
    :returns: Function that, when called, will connect to a remote machine and
        execute the function represented by 'function_name'
    """
    def _remote_module_func(remote_machine_address, *args, **kwargs):
        """
        Call a function on a remote machine.

        Note that the class instance is pickled and sent to the remote machine.
        This is so the current state of the class will be utilized when the
        function is called on the remote machine. There are probably lots of
        corner cases in which this will cause problems, so be aware of side
        effects of the original function.

        :param remote_machine_address: IP address or hostname of the remote
            machine on which the function will be run.  If the remote machine
            is running Hoplite on a port other than the default (5000), then
            the port can be specified in the form "address:port"
        :param *args: Normal arguments being passed to the remotely called
            function
        :param remote_timeout:
        :param *kwargs: Keyword arguments being passed to the remotely called
            function
        :returns: The value(s) returned by the function which was called on the
            remote machine
        """
        logger = logging.getLogger(__name__)
        logger.addHandler(logging.NullHandler())

        remote_timeout = -1
        timeout_message = ''
        if kwargs.get('remote_timeout') is not None and kwargs['remote_timeout'] > 0.0:
            remote_timeout = kwargs['remote_timeout']
            kwargs.pop('remote_timeout')
            timeout_message = ' with timeout of {} seconds'.format(
                remote_timeout)

        args_string = args.__str__()
        kwargs_string = kwargs.__str__()
        if not HopliteClientSettings.debug:
            if len(args_string) > 33:
                args_string = args_string[0:30] + '...'
            if len(kwargs_string) > 33:
                kwargs_string = kwargs_string[0:30] + '...'
        logger.info('"{0}" on target "{1}" with args: {2} and '
                    'kwargs: {3} {4}'.format(
                        function_name,
                        remote_machine_address,
                        args_string,
                        kwargs_string,
                        timeout_message))
        config = {
            'args': pickle.dumps(args),
            'kwargs': pickle.dumps(kwargs),
            'module_name': module_name,
            'function_name': function_name
        }
        job = None
        try:
            job_manager = client.remote_job_manager.RemoteJobManager(
                remote_machine_address)
            job = job_manager.create_job(
                'hoplite.plugins.remote_enabler_module_job', config)
            job.start()
            job.join(remote_timeout)
        except JobFailedError as e:
            if job is None:
                logger.error(
                    'Exception occurred while creating job to call "{0}" '
                    'on "{1}": {2}'.format(
                        function_name, remote_machine_address, str(e))
                )
            else:
                logger.error(
                    'Exception occurred while calling "{0}" on "{1}": '
                    '{2}'.format(
                        function_name, remote_machine_address, e.__str__())
                )
            # ALL TRACEBACK ENTRIES BELOW THIS ARE FROM THE REMOTE MACHINE
            e.raise_remote_exception()

        return_values = pickle.loads(job.status().get('return_values'))

        if return_values is None:
            return None

        # Convert return value into either a single value, or a tuple, so that
        # it appears the same as if the function were called on the local
        # machine
        if len(return_values) > 1:
            return_object = tuple(return_values)
        else:
            return_object = return_values[0]

        return_object_string = return_object.__str__()
        # limit return object string if not debugging
        if not HopliteClientSettings.debug and len(return_object_string) > 50:
            return_object_string = return_object_string[0:47] + '...'

        logger.debug(
            '"{0}" on target "{1}" returned {2}'.format(function_name,
                                                        remote_machine_address,
                                                        return_object_string))
        return return_object
    return _remote_module_func


def remote_module_async_func_builder(function_name, module_name):
    """
    Build a function that will connect to a remote machine and create a job
    wrapper that can be used to run a function asynchronously

    :param function_name: The name of the class function that will be called on
        the remote machine.
    :returns: Function that, when called, will connect to a remote machine and
        create then return a job wrapper for running the specified function
    """
    def _remote_async_module_func(remote_machine_address, *args, **kwargs):
        """
        Create a job on a remote machine and return a wrapper so that it has
        the same interface as a job running on the local machine.

        ***NOTE*** It seems that join must always be eventually called on jobs,
        even if they have already finished. Otherwise, a process gets orphaned,
        causing problems with future operations.

        :param remote_machine_address: IP address or hostname of the remote
            machine on which the function will be run. If the remote machine is
            running Hoplite on a port other than the default (5000), then the
            port can be specified in the form "address:port"
        :param *args: Normal arguments being passed to the remotely called
            function
        :param *kwargs: Keyword arguments being passed to the remotely called
            function
        :returns: A wrapper around the remote job
        """
        logger = logging.getLogger(__name__)
        logger.addHandler(logging.NullHandler())
        args_string = args.__str__()
        kwargs_string = kwargs.__str__()
        if not HopliteClientSettings.debug:
            if len(args_string) > 33:
                args_string = args_string[0:30] + '...'
            if len(kwargs_string) > 33:
                kwargs_string = kwargs_string[0:30] + '...'
        logger.info('Creating job "{0}" on target "{1}" with args: {2} and '
                    'kwargs: {3}'.format(
                        function_name,
                        remote_machine_address,
                        args_string,
                        kwargs_string))
        config = {
            'args': pickle.dumps(args),
            'kwargs': pickle.dumps(kwargs),
            'module_name': module_name,
            'function_name': function_name
        }
        job_manager = client.remote_job_manager.RemoteJobManager(
            remote_machine_address)
        job = job_manager.create_job(
            'hoplite.plugins.remote_enabler_module_job', config)
        return RemoteAsyncJobWrapper(job, function_name)
    return _remote_async_module_func


class RemoteAsyncJobWrapper:
    """
    This class is a wrapper around the RemoteJob class, and is used for
    asynchronously running functions which are called remotely on another
    machine. It implements the same public methods as the RemoteJob class,
    and the reader should refer to that module for additional information on
    how to use it.
    """

    def __init__(self, job, function_name):
        self.job = job
        self.function_name = function_name
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.NullHandler())

    def start(self):
        """
        Start running the function.
        """

        self.logger.debug(
            'Starting "{0}({1})" on "{2}:{3}"'.format(self.function_name,
                                                      self.job.uuid,
                                                      self.job.address,
                                                      self.job.port))
        self.job.start()

    def join(self, remote_timeout=-1):
        """
        Join the function once it has been started.

        This differs from the join function in RemoteJob in that, upon
        completion, it returns the values returned by the remotely executed
        function.

        :param remote_timeout: Optional timeout in seconds. -1 Implies no
            timeout
        :type remote_timeout: int
        :return: Values returned by the remotely executed function
        """
        self.logger.debug('Joining "{0}" on "{1}:{2}"'.format(
            self.function_name, self.job.address, self.job.port))
        try:
            self.job.join(remote_timeout)
        except JobFailedError as e:
            self.logger.error(
                'Exception occurred while calling "{0}" on target "{1}":'
                ' {2}'.format(
                    self.function_name, self.job.address, e.__str__())
            )
            # ALL TRACEBACK ENTRIES BELOW THIS ARE FROM THE REMOTE MACHINE
            e.raise_remote_exception()
        return_values = pickle.loads(self.job.status().get('return_values'))

        if return_values is None:
            return None

        # Convert return value into either a single value, or a tuple, so that
        # it appears the same as if the function were called on the local
        # machine
        if len(return_values) > 1:
            return_object = tuple(return_values)
        else:
            return_object = return_values[0]

        return_object_string = return_object.__str__()
        if not HopliteClientSettings.debug and (len(return_object_string) > 50):
            return_object_string = return_object_string[0:47] + '...'

        self.logger.debug(
            '"{0}" on target "{1}:{2}" returned {3}'.format(
                self.function_name,
                self.job.address,
                self.job.port,
                return_object_string))
        return return_object

    def config(self, force=False):
        """
        Get the configuration dictionary for the job.
        """
        return self.job.config(force)

    def status(self, force=False):
        """
        Check the status of the function's execution. This will raise an
        exception if the function has encountered an error since the last time
        the status was checked.
        :param force:
        :return:
        """
        return self.job.status(force)

    def kill(self, force=False):
        """
        Attempt to terminate the job.
        """
        return self.job.kill(force)

    def running(self, force=False):
        """
        Check if the job is still running.
        """
        return self.job.running(force)

    def finished(self, force=False):
        """
        Check if the job is finished.
        """
        return self.job.finished(force)


# This is used as an example of how remoted functions get automatically
# documented. Do not use.
@remotify(__name__)
def my_func(arg1, arg2):
    """Function which does stuff.

    My_func is a function which does nothing that is particularly useful. It
    serves primarily as an example.

    :param arg1: A number which will be printed to the console
    :type arg1: int
    :param arg2: A string which will also be printed
    :type arg2: str
    :returns: The concatenated number and string
    """
    concat_string = str(arg1) + arg2
    print concat_string
    return concat_string


# This is used as an example of how remoted classes get automatically
# documented. Do not use.
@remotify(__name__)
class Foo(object):
    def __init__(self, val_1):
        """Initialize a new instance of the Foo class.

        :param val_1: Any value. Doesn't matter what value it is
        """
        self.val_1 = val_1

    def print_a_val(self):
        """Prints a value.

        Prints the value that was passed in when the class instance was
        initialized.
        """
        print self.val_1

    def print_another_val(self, another_val):
        """Prints another value.

        Prints a value passed in by the user. It can be the same as the other
        value if desired.

        :param another_val: Another value. Doesn't matter what value it is
        """
        print another_val
