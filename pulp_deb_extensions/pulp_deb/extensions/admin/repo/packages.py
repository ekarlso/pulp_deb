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

"""
Commands related to searching for packages in a  repository.
"""

from gettext import gettext as _

from pulp.client.commands import options
from pulp.client.commands.criteria import DisplayUnitAssociationsCommand

from pulp_deb.common import constants

# -- constants ----------------------------------------------------------------
DESC_SEARCH = _('search for packages in a repository')


# -- commands -----------------------------------------------------------------
class PackagesCommand(DisplayUnitAssociationsCommand):
    def __init__(self, context):
        super(PackagesCommand, self).__init__(self.run, name='packages',
                                             description=DESC_SEARCH)
        self.context = context
        self.prompt = context.prompt

    def run(self, **kwargs):
        # Retrieve the packages
        repo_id = kwargs.pop(options.OPTION_REPO_ID.keyword)
        kwargs['type_ids'] = [constants.TYPE_DEB]
        packages = self.context.server.repo_unit.search(repo_id, **kwargs).response_body

        # Strip out checksum information; not sure how to render it yet
        # or if it's even useful
        map(lambda x: x['metadata'].pop('checksums', None), packages)

        order = []

        if not kwargs.get(self.ASSOCIATION_FLAG.keyword):
            # Only display the package metadata, not the association
            packages = [m['metadata'] for m in packages]
            # Make sure the key info is at the top; the rest can be alpha
            order = ['name', 'version', 'author']

        self.prompt.render_document_list(packages, order=order)
