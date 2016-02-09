from setuptools import setup, find_packages
import os
import re


def hoplite_plugins():
    hoplite_top_level = os.path.split(__file__)[0]
    plugin_dir = os.path.join(hoplite_top_level, "hoplite", "builtin_plugins")
    plugins = []
    for directory, dirnames, filenames in os.walk(plugin_dir):
        for filename in filenames:
            match = re.search('(\w+_job)\.py$', filename)
            if match:
                fqdn = 'hoplite.plugins.{0}'.format(match.group(1))
                module_name = 'hoplite.builtin_plugins.{0}'.format(match.group(1))
                entry = '{0} = {1}'.format(fqdn, module_name)
                plugins.append(entry)
    return plugins

setup(
    name="hoplite",
    version="15.0.0.dev21",
    packages=find_packages(exclude='tests'),
    license='MIT',
    install_requires=['flask>=0.10.1',
                      'requests>=2.2.0',
                      'argparse>=1.1',
                      'pymongo>=3.0',
                      'tornado',
                      'tblib'],
    entry_points={
        'console_scripts': [
            'hoplite-server = hoplite.main:server_main',
            'hoplite-client = hoplite.main:client_main',
            'hoplite-auto-start = hoplite.auto_start:main'
        ],
        'hoplite.jobs': hoplite_plugins()
    },
    include_package_data=True,
    package_data={
        '': ['*.cfg']
    }
)
