import errno
import logging
import logging.config
import logging.handlers
import os
import platform
import string

# Tone down logging from the http modules
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)
log = logging.getLogger('requests')
log.setLevel(logging.WARNING)
log = logging.getLogger('tornado')
log.setLevel(logging.WARNING)


def get_server_logger(name=""):
    # set up hoplite_logging
    logger = _get_base_logger(name)
    return logger


def get_job_logger(name="", uuid=""):
    logger = _get_base_logger("hoplite.{0}_{1}".format(name, uuid))

    log_file = "{0}_{1}.log".format(name, uuid)
    log_file_path = log_file

    opsys = platform.system().lower()
    if opsys == 'windows':
        log_file_path = os.path.join(r"C:\logs\hoplite\jobs", name)
        try:
            os.makedirs(log_file_path)
        except OSError as e:
            if not (e.errno == errno.EEXIST and os.path.isdir(log_file_path)):
                raise
        log_file_path = os.path.join(log_file_path, log_file)
    elif opsys == 'linux' or opsys == 'darwin':
        log_file_path = os.path.join(
            os.path.expanduser('~'), '.hoplite', 'jobs', name)
        try:
            os.makedirs(log_file_path)
        except OSError as e:
            if not (e.errno == errno.EEXIST and os.path.isdir(log_file_path)):
                raise
        log_file_path = os.path.join(log_file_path, log_file)

    fh = logging.handlers.RotatingFileHandler(
        filename=log_file_path,
        maxBytes=2097152,
        backupCount=100)
    fh.setLevel(logging.DEBUG)
    # Add context info
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


def _get_base_logger(name=""):
    opsys = platform.system().lower()
    if opsys == 'windows':
        log_file_path = os.path.join(r"C:\logs\hoplite\hoplite")
    elif opsys == 'linux' or opsys == 'darwin':
        log_file_path = os.path.join(
            os.path.expanduser('~'), '.hoplite', 'hoplite')
    else:
        raise NotImplementedError()

    # Create the directory if it doesn't exist
    try:
        os.makedirs(log_file_path)
    except OSError as e:
        if not (e.errno == errno.EEXIST and os.path.isdir(log_file_path)):
            raise

    logging.config.fileConfig(
        os.path.join(
            os.path.split(__file__)[0], "default{0}.cfg".format(opsys)),
        disable_existing_loggers=False
    )
    logger = logging.getLogger(name)
    return logger


def add_remote_function_logging_handlers(function_namespace, timestamp, filename=None):
    logger = logging.getLogger()

    # If this function has already been called in this process
    if len(logger.handlers) >= 2:
        return

    # This function gets called twice for each remote function call. On the
    # first call, filename is not provided. On the second call, the filename
    # from last time is passed in so the same log filename is used.
    if filename is None:
        full_log_name = get_log_filename(function_namespace, timestamp)
    else:
        full_log_name = filename

    logger.setLevel(logging.DEBUG)

    hoplite_remote_enabler_fh = logging.FileHandler(full_log_name)
    hoplite_remote_enabler_fh.setLevel(logging.DEBUG)
    hoplite_remote_enabler_fh.setFormatter(get_formatter_verbose())

    hoplite_remote_enabler_sh = logging.StreamHandler()
    hoplite_remote_enabler_sh.setLevel(logging.INFO)
    hoplite_remote_enabler_sh.setFormatter(get_formatter_limited())

    logger.addHandler(hoplite_remote_enabler_fh)
    logger.addHandler(hoplite_remote_enabler_sh)

    return full_log_name


def get_log_filename(function_namespace, timestamp):
    namespace_split = string.split(function_namespace, '.')
    function_name = namespace_split.pop()
    folder_hierarchy = os.path.join(*namespace_split)
    opsys = platform.system().lower()
    if opsys == 'windows':
        log_root_path = os.path.join(r'C:\logs\hoplite\remoted_functions')
    elif opsys == 'linux' or opsys == 'darwin':
        log_root_path = os.path.join(
            os.path.expanduser('~'), '.hoplite', 'remoted_functions')
    else:
        raise NotImplementedError()
    log_root_path = os.path.join(log_root_path, folder_hierarchy)
    # Create the directory if it doesn't exist
    try:
        os.makedirs(log_root_path)
    except OSError as e:
        if not (e.errno == errno.EEXIST and os.path.isdir(log_root_path)):
            raise
    # Handle the case where multiple instances of the same function are called
    # within a single second. This would otherwise result in the same filename
    # being used multiple times
    extension_num = 1
    log_file_name = os.path.join(
        log_root_path, timestamp + ' ' + function_name + ".log")
    while os.path.isfile(log_file_name):
        log_file_name = os.path.join(
            log_root_path,
            timestamp + ' ' + function_name + '_' + str(extension_num) + ".log")
        extension_num += 1

    return log_file_name


def get_formatter_verbose():
    return logging.Formatter('%(levelname)-8s '
                             '%(asctime)s '
                             '%(filename)+30s:%(lineno)-5s '
                             '%(threadName)-15s %(message)s',
                             "%I:%M:%S %p")


def get_formatter_limited():
    return logging.Formatter('%(levelname)-8s '
                             '%(asctime)s '
                             '%(filename)+20s:%(lineno)-5s '
                             '%(message).200s',
                             "%I:%M:%S %p")
