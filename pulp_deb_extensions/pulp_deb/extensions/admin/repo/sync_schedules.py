# Copyright (c) 2012 Red Hat, Inc.
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

from pulp.client.commands.schedule import (
    DeleteScheduleCommand, ListScheduleCommand, CreateScheduleCommand,
    UpdateScheduleCommand, NextRunCommand, ScheduleStrategy)
from pulp.client.commands.options import OPTION_REPO_ID

from pulp_deb.common.constants import IMPORTER_ID


# -- constants ----------------------------------------------------------------
DESC_LIST = _('list scheduled sync operations')
DESC_CREATE = _('adds a new scheduled sync operation')
DESC_DELETE = _('delete a sync schedule')
DESC_UPDATE = _('updates an existing schedule')
DESC_NEXT_RUN = _('displays the next scheduled sync run for a repository')


# -- commands -----------------------------------------------------------------
class ListScheduleCommand(ListScheduleCommand):
    def __init__(self, context):
        strategy = RepoSyncScheduleStrategy(context)
        super(ListScheduleCommand, self).__init__(context, strategy,
                                                        description=DESC_LIST)
        self.add_option(OPTION_REPO_ID)


class CreateScheduleCommand(CreateScheduleCommand):
    def __init__(self, context):
        strategy = RepoSyncScheduleStrategy(context)
        super(CreateScheduleCommand, self).__init__(context, strategy,
                                                          description=DESC_CREATE)
        self.add_option(OPTION_REPO_ID)


class DeleteScheduleCommand(DeleteScheduleCommand):
    def __init__(self, context):
        strategy = RepoSyncScheduleStrategy(context)
        super(DeleteScheduleCommand, self).__init__(context, strategy,
                                                          description=DESC_DELETE)
        self.add_option(OPTION_REPO_ID)


class UpdateScheduleCommand(UpdateScheduleCommand):
    def __init__(self, context):
        strategy = RepoSyncScheduleStrategy(context)
        super(UpdateScheduleCommand, self).__init__(context, strategy,
                                                          description=DESC_UPDATE)
        self.add_option(OPTION_REPO_ID)


class NextRunCommand(NextRunCommand):
    def __init__(self, context):
        strategy = RepoSyncScheduleStrategy(context)
        super(NextRunCommand, self).__init__(context, strategy,
                                                   description=DESC_NEXT_RUN)
        self.add_option(OPTION_REPO_ID)

# -- internal -----------------------------------------------------------------

class RepoSyncScheduleStrategy(ScheduleStrategy):

    # See super class for method documentation

    def __init__(self, context):
        super(RepoSyncScheduleStrategy, self).__init__()
        self.context = context
        self.api = context.server.repo_sync_schedules

    def create_schedule(self, schedule, failure_threshold, enabled, kwargs):
        repo_id = kwargs[OPTION_REPO_ID.keyword]

        # Eventually we'll support passing in sync arguments to the scheduled
        # call. When we do, override_config will be created here from kwargs.
        override_config = {}

        return self.api.add_schedule(repo_id, IMPORTER_ID, schedule,
                                     override_config, failure_threshold, enabled)

    def delete_schedule(self, schedule_id, kwargs):
        repo_id = kwargs[OPTION_REPO_ID.keyword]
        return self.api.delete_schedule(repo_id, IMPORTER_ID, schedule_id)

    def retrieve_schedules(self, kwargs):
        repo_id = kwargs[OPTION_REPO_ID.keyword]
        return self.api.list_schedules(repo_id, IMPORTER_ID)

    def update_schedule(self, schedule_id, **kwargs):
        repo_id = kwargs.pop(OPTION_REPO_ID.keyword)
        return self.api.update_schedule(repo_id, IMPORTER_ID, schedule_id, **kwargs)
