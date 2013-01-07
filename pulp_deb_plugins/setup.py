# Copyright (c) 2012 Bouvet ASA.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

from setuptools import setup, find_packages

setup(
    name='pulp_deb',
    version='2.0.0',
    license='GPLv2+',
    packages=find_packages(exclude=['test', 'test.*']),
    author='Endre Karlson',
    author_email='endre.karlson@bouvet.no',
    entry_points={
        #'pulp.distributors': [
        #    'distributor = pulp_deb.plugins.distributors.distributor:entry_point',
        #],

        'pulp.importers': [
            'importer = pulp_deb.plugins.importers.importer:entry_point',
        ],
        'pulp.server.db.migrations': [
            'pulp_deb = pulp_deb.plugins.migrations',
        ],
        'pulp.downloaders.deb': [
            'http = pulp_deb.plugins.importers.downloaders.web:HttpDownloader',
            'file = pulp_deb.plugins.importers.downloaders.local:LocalDownloader',
        ]
    }
)
