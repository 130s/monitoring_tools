import glob
import os

from setuptools import find_packages
from setuptools import setup

package_name = 'topic_monitor_ros1'

setup(
    name=package_name,
    version='0.20.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=[
        'setuptools',
    ],
    zip_safe=True,
    keywords=['ROS'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Topic :: Software Development',
    ],
    description='Package containing tools for monitoring ROS 2 topics.',
    license='Apache License, Version 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'topic_monitor = topic_monitor_ros1.topic_monitor:main',
        ],
    },
)
