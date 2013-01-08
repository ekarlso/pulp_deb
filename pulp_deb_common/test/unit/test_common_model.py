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

from debian.deb822 import Packages
import os.path
import unittest

from pulp.common.compat import json

from pulp_deb.common import constants
from pulp_deb.common.model import Repository, DebianPackage

# -- constants ----------------------------------------------------------------

PKG_DATA = {
    'Architecture': u'amd64',
    'Conflicts': u'python2.3-crypto, python2.4-crypto',
    'Depends': u'python2.7, python (>= 2.7.1-0ubuntu2), python (<< 2.8), libc6 (>= 2.14), libgmp10',
    'Description': u'cryptographic algorithms and protocols for Python\n A collection of cryptographic algorithms and protocols, implemented\n for use from Python. Among the contents of the package:\n .\n * Hash functions: HMAC, MD2, MD4, MD5, RIPEMD160, SHA, SHA256.\n * Block encryption algorithms: AES, ARC2, Blowfish, CAST, DES, Triple-DES.\n * Stream encryption algorithms: ARC4, simple XOR.\n * Public-key algorithms: RSA, DSA, ElGamal.\n * Protocols: All-or-nothing transforms, chaffing/winnowing.\n * Miscellaneous: RFC1751 package for converting 128-key keys\n into a set of English words, primality testing, random number gereration.',
    'Filename': u'pool/main/p/python-crypto/python-crypto_2.6-2build3~ubuntu12.04.1~grizzly0_amd64.deb',
    'Installed-Size': u'1500',
    'MD5sum': u'e9242f4b733d993da0b096bea5809d42',
    'Maintainer': u'Sebastian Ramacher <s.ramacher@gmx.at>',
    'Package': u'python-crypto',
    'Priority': u'optional',
    'Provides': u'python2.7-crypto',
    'Replaces': u'python2.3-crypto, python2.4-crypto',
    'SHA1': u'd40743e0d669b0f6b6499da1892a7a39dbca5f8a',
    'Section': u'python',
    'Size': u'362600',
    'Suggests': u'python-crypto-dbg, python-crypto-doc',
    'Version': u'2.6-2build3~ubuntu12.04.1~grizzly0',
    'component': 'main'}


# -- test cases ---------------------------------------------------------------


def get_expected(data):
    newdata = {}
    for k, v in data.copy().items():
        if k in constants.PACKAGE_KEYS:
            newdata[DebianPackage.lowered_key(k)] = v
    return newdata


class RepositoryTests(unittest.TestCase):
    def test_update_from_packages(self):
        metadata = Repository()
        path = os.path.dirname(__file__) + "/Packages"
        metadata.update_from_packages(path)


class DebianPackageTests(unittest.TestCase):
    def setUp(self):
        self.deb = DebianPackage(PKG_DATA)

    def test_from_dict(self):
        expected = get_expected(PKG_DATA)
        self.assertEquals(expected, self.deb.to_dict(full=False))

    def test_to_dict_not_full(self):
        expected = get_expected(PKG_DATA)
        self.assertEquals(expected, self.deb.to_dict(full=False))

    def test_from_deb822(self):
        expected = get_expected(PKG_DATA)
        self.assertEquals(expected, self.deb.to_dict(full=False))

    def test_prefix(self):
        self.assertEquals(self.deb.prefix(), PKG_DATA['Package'][0])

    def test_filename_from_url_and_filename(self):
        deb = DebianPackage(PKG_DATA)
        deb.filename_from_data()


    def test_filename_from_data(self):
        # FIXME: Need to fix this...
        return None
        deb = DebianPackage(PKG_DATA)
        filename = deb.filename()

        deb_data = deb.to_dict()
        name = constants.DEB_FILENAME % deb_data
        self.assertEquals(name, filename)
