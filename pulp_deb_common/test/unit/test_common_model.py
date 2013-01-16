# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

import unittest
from debian.deb822 import Packages, Sources

from pulp_deb.common import constants, model, samples, utils


# -- test cases ---------------------------------------------------------------


def get_expected(data):
    newdata = {}
    for k, v in data.copy().items():
        if k in constants.PACKAGE_KEYS:
            newdata[k.lower()] = v
    return newdata


PACKAGE = get_expected(samples.get_data('package'))
DATA = samples.DATA


class UtilTests(unittest.TestCase):
    def test_cls_from_package_dict(self):
        cls = model.get_deb822_cls(PACKAGE)
        self.assertEqual(cls, Packages)

    def test_cls_from_resource(self):
        data = [('packages', Packages), ('sources', Sources)]
        for cls_type, cls_expected in data:
            resource = {'type': cls_type}
            cls = model.get_deb822_cls(resource)
            self.assertEqual(cls_expected, cls)

    def test_cls_from_string(self):
        self.assertEqual(Packages, model.get_deb822_cls('Packages.gz'))
        self.assertEqual(Sources, model.get_deb822_cls('Sources.gz'))


class DistributionTests(unittest.TestCase):
    def test_serialize_dist_wo_packages(self):
        dist = samples.get_model('dist')
        self.assertEqual(dist.serialize(exclude=['packages']), DATA['dist'])

    def test_serialize_dist_with_packages(self):
        dist = samples.get_model('dist')
        dist.add_package(DATA['component']['name'], DATA['package'])

        dist_data = dist.serialize()
        self.assertEquals(dist_data['name'], DATA['dist']['name'])

        cmpts = dist_data['components']
        self.assertEquals(len(cmpts), 1)
        self.assertEquals(cmpts[0]['arch'], DATA['component']['arch'])
        self.assertEquals(cmpts[0]['name'], DATA['component']['name'])
        self.assertEquals(len(cmpts[0]['packages']), 1)

    def test_get_indexes(self):
        dist = samples.get_valid_repo()
        indexes = dist.get_indexes()
        self.assertEquals(len(indexes), 3)


class ComponentTests(unittest.TestCase):
    def setUp(self):
        self.dist = samples.get_valid_repo()
        self.cmpt = self.dist['components'][0]

    def test_get_indexes(self):
        indexes = self.cmpt.get_indexes()
        self.assertEquals(len(indexes), 3)

    def test_update_from_index_files(self):
        # NOTE: When it's a local repository the path is valid. If not it
        # has to be downloaded before running update_from_indexes()
        indexes = [i['source'] for i in self.cmpt.get_indexes()]

        # NOTE: It has i686 as well but there's no index file for it so skip it
        self.cmpt.update_from_indexes(indexes)
        self.assertEquals(len(self.cmpt.data['packages']), 3)

    def test_update_from_resources_with_paths(self):
        # The get_index_content() looks for 'path' as a key, resource only
        # contains 'source' before it's downloaded...
        resources = []
        for resource in self.cmpt.get_indexes():
            resource['path'] = resource['source']
            resources.append(resource)

        self.cmpt.update_from_indexes(resources)
        self.assertEquals(len(self.cmpt.data['packages']), 3)

    def test_update_from_resources_with_content(self):
        resources = []
        for resource in self.cmpt.get_indexes():
            resource['content'] = utils._read(resource['source'])
            resources.append(resource)
        self.cmpt.update_from_indexes(resources)
        self.assertEquals(len(self.cmpt.data['packages']), 3)


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.pkg = samples.get_model('package')

    def test_from_dict(self):
        pkg = model.Package(**samples.load('package'))
        self.assertEquals(PACKAGE, pkg.to_dict(full=False))

    def test_from_deb822(self):
        deb822 = Packages(samples.load('package'))
        pkg = model.Package(deb822=deb822)
        self.assertEquals(PACKAGE, pkg.to_dict(full=False))

    def test_to_dict_not_full(self):
        self.assertEquals(PACKAGE, self.pkg.to_dict(full=False))

    def test_prefix(self):
        self.assertEquals(PACKAGE['package'][0:4], self.pkg.prefix())

    def test_filename_from_data_eq_filename(self):
        pkg = samples.get_model('package', component='main')
        self.assertEquals(pkg.filename_from_data(), pkg.filename_from_deb822())

    def test_filename_short(self):
        expected = PACKAGE['filename'].split('/')[-1]
        self.assertEquals(self.pkg.filename_short(), expected)
