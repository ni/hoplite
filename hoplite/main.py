from hoplite.utils import server_logging
from hoplite.api import create_app
from hoplite.client.remote_job_manager import RemoteJobManager
from hoplite.exceptions import JobFailedError
import traceback
from hoplite.serializer import hoplite_loads
import argparse
import pprint
import sys
from datetime import timedelta
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from globals import HopliteServerSettings

logger = server_logging.get_server_logger(__name__)

pp = pprint.PrettyPrinter(indent=4)


def job_status(manager, args):
    job = manager.get_job(args.uuid)
    print "Config: {0}".format(job.config())
    try:
        print "Status: {0}".format(job.status())
    except JobFailedError as e:
        print "Job raised an exception during execution."
        print "Exception Type: {0}".format(e.type_string)
        print "Exception Message: {0}".format(e.msg)
        print "Traceback:"
        for line in traceback.format_list(e.traceback):
            print line
    print "Running: {0}".format(job.running())
    print "Finished: {0}".format(job.finished())


def start_job(manager, args):
    job = manager.get_job(args.uuid)
    job.start()
    print "Job Started"


def create_job(manager, args):
    try:
        file = args.job_config
        json_data = open(file).read()
        config = hoplite_loads(json_data)
    except ValueError, e:
        print("JSON parsing error: {0}".format(e))
        return
    except Exception, e:
        config = args.job_config
        print("Could not read file, assuming you passed in config as a string.")

    job = manager.create_job(args.job_name, config, port=args.port)
    if args.start:
        job.start()
    print "UUID: {0}".format(job.uuid)


def list_job_plugins(manager, args):
    print "Current Job Plugins:"
    pp.pprint(manager.get_job_plugins())


def get_running_jobs(manager, args):
    print "Currently running jobs:"
    pp.pprint(manager.get_running_jobs())


def reload_plugins(manager, args):
    plugins = manager.reload_job_plugins()
    print "Current Job Plugins:"
    pp.pprint(plugins)


def get_client_options_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('-a', '--address', default="localhost", help='The address of the hoplite server'
                                                                          ' you want to target')
    parser.add_argument('-p', '--port', default=5000, help='The port the hoplite server is listening on')

    subparsers = parser.add_subparsers(help='sub-command help')
    list_parser = subparsers.add_parser('list', help='list all available job builtin_plugins')
    list_parser.set_defaults(func=list_job_plugins)

    create_parser = subparsers.add_parser('create', help='Create a job'
                                                         '(config can be a string, or a path to a json file)')
    create_parser.add_argument('-s', '--start', action='store_true', help='starts the job after it is created')
    create_parser.add_argument('job_name', help='The namespaced name of the job you want to create')
    create_parser.add_argument('job_config', help='Path to a json file you would like '
                                                  'passed into the job for its configuration')
    create_parser.set_defaults(func=create_job)

    start_parser = subparsers.add_parser('start', help='Start a job')
    start_parser.add_argument('uuid', help='uuid of the job')
    start_parser.set_defaults(func=start_job)

    status_parser = subparsers.add_parser('info', help='Get information about a job')
    status_parser.add_argument('uuid', help='uuid of the job')
    status_parser.set_defaults(func=job_status)

    running_parser = subparsers.add_parser('running', help='Get a list of all running jobs')
    running_parser.set_defaults(func=get_running_jobs)

    reload_parser = subparsers.add_parser('reload', help='Search all the paths in sys.path and '
                                                         'reload all available plugins registered under '
                                                         'the hoplite.jobs entry point')
    reload_parser.set_defaults(func=reload_plugins)

    return parser


def get_server_options_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--port', default='5000', help='The port number to listen on')
    parser.add_argument('-d', '--debug', action='store_true', help='Start the server in debug mode')

    return parser


def server_main(args=sys.argv):
    parser = get_server_options_parser()
    # sys.argv includes the path of invocation as the first index in the list
    # argparse expects just the parameters if we pass a list into parse_args
    # so here we get rid of that path parameter and are left with only the args
    # from the command line
    if args == sys.argv:
        args = args[1:]
    args = parser.parse_args(args)

    HopliteServerSettings.debug = args.debug

    app = create_app()
    logger.info('Starting Hoplite server on port {}'.format(args.port))
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(args.port)
    ioloop = IOLoop.instance()
    # This is needed to ensure Ctrl-C kills the server quickly
    set_ping(ioloop, timedelta(seconds=2))
    try:
        ioloop.start()
    except:
        raise
    finally:
        # Ensure that the server always closes the socket when it's no longer
        # in use
        ioloop.stop()


def client_main():
    parser = get_client_options_parser()
    args = parser.parse_args()
    manager = RemoteJobManager(args.address, args.port)
    args.func(manager, args)


# I think this periodically pings the tornado server. The reason this is needed
# is because Tornado apparently doesn't process the Ctrl-C exception until the
# next request after the Ctrl-C is received.
def set_ping(ioloop, timeout):
    ioloop.add_timeout(timeout, lambda: set_ping(ioloop, timeout))
