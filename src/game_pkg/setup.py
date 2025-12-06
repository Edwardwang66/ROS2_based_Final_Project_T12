from setuptools import setup
import os
from glob import glob

package_name = 'game_pkg'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Edward Wang',
    maintainer_email='your_email@example.com',
    description='Game interaction package for Rock-Paper-Scissors',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'game_node = game_pkg.game_node:main',
        ],
    },
)

