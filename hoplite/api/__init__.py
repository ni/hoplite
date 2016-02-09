from flask import Flask
from hoplite.api.root import bp as site_bp
from hoplite.api.jobs import bp as jobs_bp
from hoplite.api.job_plugins import bp as job_plugins_bp
from hoplite.server.jobs.job_manager import JobManager
from hoplite.plugin_manager import EntryPointManager
import hoplite.api.helpers


def create_app(group_name='hoplite.jobs'):
    app = Flask(__name__)
    app.register_blueprint(site_bp, url_prefix='/')
    app.register_blueprint(jobs_bp, url_prefix='/jobs')
    app.register_blueprint(job_plugins_bp, url_prefix='/job_plugins')
    hoplite.api.helpers.manager = JobManager(EntryPointManager(group_name))
    return app
