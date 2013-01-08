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

from gettext import gettext as _
import sys

from pulp.bindings.exceptions import BadRequestException
from pulp.client.commands.unit import UnitCopyCommand

from pulp_deb.common import constants

# -- constants ----------------------------------------------------------------
DESC_COPY = _('copies packages from one repository into another')


# -- commands -----------------------------------------------------------------
class PackageCopyCommand(UnitCopyCommand):

    def __init__(self, context, name='copy', description=DESC_COPY, method=None):

        if method is None:
            method = self.run

        super(PackageCopyCommand, self).__init__(method, name=name,
                                                description=description)

        self.context = context
        self.prompt = context.prompt

    def run(self, **kwargs):
        from_repo = kwargs['from-repo-id']
        to_repo = kwargs['to-repo-id']
        kwargs['type_ids'] = [constants.TYPE_DEB]

        # If rejected an exception will bubble up and be handled by middleware.
        # The only caveat is if the source repo ID is invalid, it will come back
        # from the server as source_repo_id. The client-side name for this value
        # is from-repo-id, so do a quick substitution in the exception and then
        # reraise it for the middleware to handle like normal.
        try:
            response = self.context.server.repo_unit.copy(from_repo, to_repo, **kwargs)
        except BadRequestException, e:
            if 'source_repo_id' in e.extra_data.get('property_names', []):
                e.extra_data['property_names'].remove('source_repo_id')
                e.extra_data['property_names'].append('from-repo-id')
            raise e, None, sys.exc_info()[2]

        progress_msg = _('Progress on this task can be viewed using the '
                         'commands under "repo tasks".')

        if response.response_body.is_postponed():
            d = _('Unit copy postponed due to another operation on the destination '
                  'repository. ')
            d += progress_msg
            self.context.prompt.render_paragraph(d, tag='postponed')
            self.context.prompt.render_reasons(response.response_body.reasons)
        else:
            self.context.prompt.render_paragraph(progress_msg, tag='progress')
