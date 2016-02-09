from flask import Blueprint
import platform
import sys
import os
import site
import pkg_resources

from hoplite.api.helpers import jsonify

bp = Blueprint('site', __name__)


def reload_site_packages():
    # TODO: Can probably be replaced with reload(pkg_resources)
    opsys = platform.system().lower()
    python_exe_path = sys.executable
    bin_path = os.path.split(python_exe_path)[0]
    venv_path = os.path.split(bin_path)[0]
    site_path = ""
    if opsys == 'windows':
        # If running in virtual environment, we must account for different
        # folder structure
        if hasattr(sys, 'real_prefix'):
            site_path = os.path.join(venv_path, "..", "Lib", "site-packages")
        else:
            site_path = os.path.join(venv_path, "Lib", "site-packages")
    elif opsys == 'linux' or opsys == 'darwin':
        # If running in virtual environment, we must account for different
        # folder structure
        if hasattr(sys, 'real_prefix'):
            site_path = os.path.join(
                venv_path, "..", "lib", "python{0}.{1}".format(
                    sys.version_info[0], sys.version_info[1]), "site-packages")
        else:
            site_path = os.path.join(
                venv_path, "lib", "python{0}.{1}".format(
                    sys.version_info[0], sys.version_info[1]), "site-packages")
    site.addsitedir(site_path)
    for path in sys.path:
        pkg_resources.working_set.add_entry(path)


@bp.route("reload", methods=["PUT"])
def reload_site_packages_endpoint():
    reload_site_packages()
    return jsonify()
