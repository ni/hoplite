from .. import HopliteAppTestCase
from hoplite.api import create_app


class HopliteApiTestCase(HopliteAppTestCase):
    def _create_app(self):
        return create_app('hoplite.test_jobs')
