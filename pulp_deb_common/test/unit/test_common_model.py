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
from debian import deb822

from pulp_deb.common import constants, samples
from pulp_deb.common.model import Distribution, Component, Package


# -- test cases ---------------------------------------------------------------


def get_expected(data):
    newdata = {}
    for k, v in data.copy().items():
        if k in constants.PACKAGE_KEYS:
            newdata[Package.lowered_key(k)] = v
    return newdata


PACKAGE = get_expected(samples.data('package'))
DATA = samples.DATA

import ipdb


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.dist = samples.model('dist')

    def test_serialize_dist_wo_packages(self):
        self.assertEqual(self.dist.serialize(exclude=['packages']), DATA['dist'])

    def test_serialize_dist_with_packages(self):
        self.dist.add_package(DATA['component']['name'], DATA['package'])

        dist = self.dist.serialize()
        self.assertEquals(dist['name'], DATA['dist']['name'])

        cmpts = dist['components']
        self.assertEquals(len(cmpts), 1)
        self.assertEquals(cmpts[0]['arch'], DATA['component']['arch'])
        self.assertEquals(cmpts[0]['name'], DATA['component']['name'])
        self.assertEquals(len(cmpts[0]['packages']), 1)


class ComponentTests(unittest.TestCase):
    def setUp(self):
        self.dist = samples.valid_repo()
        self.cmpt = self.dist['components'][0]

    def test_resource_urls(self):
        resource = self.cmpt.get_indexes()
        self.assertEquals(len(resource), 3)


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.pkg = samples.model('package')

    def test_from_dict(self):
        pkg = Package(**samples.load('package'))
        self.assertEquals(PACKAGE, pkg.to_dict(full=False))

    def test_from_deb822(self):
        deb = deb822.Packages(samples.load('package'))
        pkg = Package(deb=deb)
        self.assertEquals(PACKAGE, pkg.to_dict(full=False))

    def test_to_dict_not_full(self):
        self.assertEquals(PACKAGE, self.pkg.to_dict(full=False))

    def test_prefix(self):
        self.assertEquals(PACKAGE['package'][0:4], self.pkg.prefix())

    def test_filename_from_data_eq_filename(self):
        pkg = samples.model('package', component='main')
        self.assertEquals(pkg.filename_from_data(), pkg.filename_from_deb822())

    def test_filename_short(self):
        expected = PACKAGE['filename'].split('/')[-1]
        self.assertEquals(self.pkg.filename_short(), expected)
