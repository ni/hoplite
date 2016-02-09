from setuptools import setup, find_packages

setup(
    name = "entrypointtest",
    version = "0.1",
    packages = find_packages(),
    entry_points={
        'entry.point.test': [
            'entry_point_1=test_entry_point.module_one',
            'entry_point_2=test_entry_point.module_two'
        ]
    }
)
