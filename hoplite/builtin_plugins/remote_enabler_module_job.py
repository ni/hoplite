import importlib
import logging
import pickle
import time
import traceback

from hoplite.utils.server_logging import add_remote_function_logging_handlers

hoplite_logger = logging.getLogger()
hoplite_logger.setLevel(logging.DEBUG)


def run(config, status):
    """
    Run a function called from another machine.

    :param config: Dictionary which contains information needed to run the
        function.
        It must contain the following keys:
        * args - The original non-keyword arguments which are intended to be
          sent to the function being called
        * kwargs - The original keyword arguments which are intended to be sent
          to the function being called
        * module_name - The name of the module which defines the class on which
          the function will be called. This module will be imported so that the
          class can be unpickled and then used.
        * function_name - The name of the function to call from the class
          object.
        * instance - The pickled instance of the class from which the function
          will be called
    :param status: Used to store information regarding the results of running
        the job
    """
    args = pickle.loads(config.get('args', []))
    kwargs = pickle.loads(config.get('kwargs', {}))
    module_name = config.get('module_name')
    function_name = config.get('function_name')
    mod = importlib.import_module(module_name)
    status.status.update({
        'Positional arguments for function call': str(args),
        'Keyword arguments for function call': str(kwargs)
    })
    status.update(status.status)
    try:
        timestamp = time.strftime('%Y-%m-%d %H-%M-%S')
        log_filename = add_remote_function_logging_handlers(
            module_name + '.' + function_name, timestamp)
        hoplite_logger.info(
            'Beginning execution of {} with args: {} and kwargs: {}'.format(
                function_name, args, kwargs))
        # Run function
        return_values = getattr(mod, function_name)(*args, **kwargs)
        # Remove and re-add handlers because the function could have messed
        # with the root logger
        all_handlers = list(hoplite_logger.handlers)
        for handler in all_handlers:
            handler.close()
            hoplite_logger.removeHandler(handler)
        # We need to pass in log filename this time so that a new file isn't
        # created
        add_remote_function_logging_handlers(
            module_name + '.' + function_name, timestamp, log_filename)
    except:
        hoplite_logger.error(
            'An exception occurred: \n{}'.format(
                traceback.format_exc().rstrip()))
        status.status.update({
            'Exception logging info': traceback.format_exc().replace('\\n', '\n')
        })
        status.update(status.status)
        raise

    hoplite_logger.info(
        'Returning from {} with return value(s): {}'.format(
            function_name, return_values))

    if return_values.__class__ is tuple:
        return_values = list(return_values)
    else:
        return_values = [return_values]

    status.status.update({
        'return_values': pickle.dumps(return_values)
    })
    status.update(status.status)

    for handler in all_handlers:
        handler.close()
        hoplite_logger.removeHandler(handler)
