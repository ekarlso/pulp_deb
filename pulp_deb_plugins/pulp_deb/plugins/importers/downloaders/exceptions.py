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


class InvalidURL(Exception):
    def __init__(self, url, *args):
        Exception.__init__(self, url, *args)
        self.url = url


class UnsupportedURLType(Exception):
    def __init__(self, url_type, *args):
        Exception.__init__(self, url_type, *args)
        self.url_type = url_type

# -- file retrieval exceptions ------------------------------------------------

class FileRetrievalException(Exception):
    """
    Base class for all exceptions related to trying to retrieve files, either
    metadata documents or modules. This should only directly be used if there
    is no more specific subclass.
    """
    def __init__(self, location, *args):
        """
        :param location: where the document was attempted to be read from
        :type  location: str
        """
        Exception.__init__(self, location, *args)
        self.location = location

    def __str__(self):
        template = '%s: %s'
        return template % (self.__class__.__name__, self.location)


class FileNotFoundException(FileRetrievalException):
    """
    Raised if a requested file cannot be found.
    """
    pass



class UnauthorizedException(FileRetrievalException):
    """
    Raised if a file fails to be retrieved because it could not be read
    (e.g. 401 from a web request, no read perms for a local read).
    """
    pass
