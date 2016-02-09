import pkg_resources

from hoplite.utils import server_logging
logger = server_logging.get_server_logger(__name__)


class EntryPointManager(object):
    """
    Interface to the hoplite.jobs set of entry points
    """
    def __init__(self, group_name='hoplite.jobs'):
        self.entry_point_group_name = group_name

    def get_plugin_names(self):
        names = []
        for entry_point in self._entry_points():
            names.append(entry_point.name)
        return names

    def get_plugin_module_by_name(self, name):
        # TODO: Should we validate the module implements the correct methods
        # before returning it to the caller?
        for entry_point in self._entry_points():
            if entry_point.name == name:
                return entry_point.load()

    def _entry_points(self):
        # TODO: If it takes too long to reload pkg_resources, it might be worth
        # looking into only loading if a package
        # TODO: isn't found and then try again.
        reload(pkg_resources)  # makes sure entry points are up-to-date
        for entry_point in pkg_resources.iter_entry_points(group=self.entry_point_group_name):
            logger.debug("Found entry point: {0}".format(entry_point.name))
            yield entry_point
