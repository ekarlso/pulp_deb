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
import traceback

from pulp.client.commands.repo.sync_publish import StatusRenderer
from pulp.client.extensions.core import COLOR_FAILURE

from pulp_deb.common import constants
from pulp_deb.common.publish_progress import  PublishProgressReport
from pulp_deb.common.sync_progress import SyncProgressReport


class StatusRenderer(StatusRenderer):
    def __init__(self, context):
        super(StatusRenderer, self).__init__(context)

        # Sync Steps
        self.sync_metadata_last_state = constants.STATE_NOT_STARTED
        self.sync_packages_last_state = constants.STATE_NOT_STARTED

        # Publish Steps
        self.publish_packages_last_state = constants.STATE_NOT_STARTED
        self.publish_metadata_last_state = constants.STATE_NOT_STARTED
        self.publish_http_last_state = constants.STATE_NOT_STARTED
        self.publish_https_last_state = constants.STATE_NOT_STARTED

        # UI Widgets
        self.sync_metadata_bar = self.prompt.create_progress_bar()
        self.sync_packages_bar = self.prompt.create_progress_bar()
        self.publish_packages_bar = self.prompt.create_progress_bar()
        self.publish_metadata_spinner = self.prompt.create_spinner()

    def display_report(self, progress_report):

        # Sync Steps
        if constants.IMPORTER_ID in progress_report:
            sync_report = SyncProgressReport.from_progress_dict(progress_report[constants.IMPORTER_ID])
            self._display_sync_metadata_step(sync_report)
            self._display_sync_packages_step(sync_report)

        # Publish Steps
        if constants.DISTRIBUTOR_ID in progress_report:
            publish_report = PublishProgressReport.from_progress_dict(progress_report[constants.DISTRIBUTOR_ID])
            self._display_publish_packages_step(publish_report)
            self._display_publish_metadata_step(publish_report)
            self._display_publish_http_https_step(publish_report)

    # -- private --------------------------------------------------------------

    def _display_sync_metadata_step(self, sync_report):

        # Do nothing if it hasn't started yet or has already finished
        if sync_report.metadata_state == constants.STATE_NOT_STARTED or \
           self.sync_metadata_last_state in constants.COMPLETE_STATES:
            return

        # Only render this on the first non-not-started state
        if self.sync_metadata_last_state == constants.STATE_NOT_STARTED:
            self.prompt.write(_('Downloading metadata...'), tag='download-metadata')

        # Same behavior for running or success
        if sync_report.metadata_state in (constants.STATE_RUNNING, constants.STATE_SUCCESS):
            items_done = sync_report.metadata_query_finished_count
            items_total = sync_report.metadata_query_total_count
            item_type = _('Metadata Query')

            self._render_itemized_in_progress_state(items_done, items_total,
                item_type, self.sync_metadata_bar, sync_report.metadata_state)

        # The only state left to handle is if it failed
        else:
            self.prompt.render_failure_message(_('... failed'))
            self.prompt.render_spacer()
            self._render_error(sync_report.metadata_error_message,
                                sync_report.metadata_exception,
                                sync_report.metadata_traceback)

        # Before finishing update the state
        self.sync_metadata_last_state = sync_report.metadata_state

    def _display_sync_packages_step(self, sync_report):

        # Do nothing if it hasn't started yet or has already finished
        if sync_report.packages_state == constants.STATE_NOT_STARTED or \
           self.sync_packages_last_state in constants.COMPLETE_STATES:
            return

        # Only render this on the first non-not-started state
        if self.sync_packages_last_state == constants.STATE_NOT_STARTED:
            self.prompt.write(_('Downloading new packages...'), tag='downloading')

        # Same behavior for running or success
        if sync_report.packages_state in (constants.STATE_RUNNING, constants.STATE_SUCCESS):
            items_done = sync_report.packages_finished_count + sync_report.packages_error_count
            items_total = sync_report.packages_total_count
            item_type = _('package')

            self._render_itemized_in_progress_state(items_done, items_total, item_type,
                self.sync_packages_bar, sync_report.packages_state)

        # The only state left to handle is if it failed
        else:
            self.prompt.render_failure_message(_('... failed'))
            self.prompt.render_spacer()
            self._render_error(sync_report.packages_error_message,
                               sync_report.packages_exception,
                               sync_report.packages_traceback)

        # Regardless of success or failure, display any individual package errors
        # if the new state is complete
        if sync_report.packages_state in constants.COMPLETE_STATES:
            self._render_package_errors(sync_report.packages_individual_errors)

        # Before finishing update the state
        self.sync_packages_last_state = sync_report.packages_state

    def _display_publish_packages_step(self, publish_report):

        # Do nothing if it hasn't started yet or has already finished
        if publish_report.packages_state == constants.STATE_NOT_STARTED or \
           self.publish_packages_last_state in constants.COMPLETE_STATES:
            return

        # Only render this on the first non-not-started state
        if self.publish_packages_last_state == constants.STATE_NOT_STARTED:
            self.prompt.write(_('Publishing packages...'), tag='publishing')

        # Same behavior for running or success
        if publish_report.packages_state in (constants.STATE_RUNNING, constants.STATE_SUCCESS):
            items_done = publish_report.packages_finished_count + publish_report.packages_error_count
            items_total = publish_report.packages_total_count
            item_type = _('package')

            self._render_itemized_in_progress_state(items_done, items_total, item_type,
                self.publish_packages_bar, publish_report.packages_state)

        # The only state left to handle is if it failed
        else:
            self.prompt.render_failure_message(_('... failed'))
            self.prompt.render_spacer()
            self._render_error(publish_report.packages_error_message,
                               publish_report.packages_exception,
                               publish_report.packages_traceback)

        # Regardless of success or failure, display any individual package errors
        # if the new state is complete
        if publish_report.packages_state in constants.COMPLETE_STATES:
            self._render_package_errors(publish_report.packages_individual_errors)

        # Before finishing update the state
        self.publish_packages_last_state = publish_report.packages_state

    def _display_publish_metadata_step(self, publish_report):

        # Do nothing if it hasn't started yet or has already finished
        if publish_report.metadata_state == constants.STATE_NOT_STARTED or \
           self.publish_metadata_last_state in constants.COMPLETE_STATES:
            return

        # Only render this on the first non-not-started state
        if self.publish_metadata_last_state == constants.STATE_NOT_STARTED:
            self.prompt.write(_('Generating repository metadata...'), tag='generating')

        if publish_report.metadata_state == constants.STATE_RUNNING:
            self.publish_metadata_spinner.next()

        elif publish_report.metadata_state == constants.STATE_SUCCESS:
            self.publish_metadata_spinner.next(finished=True)
            self.prompt.write(_('... completed'), tag='completed')
            self.prompt.render_spacer()

        elif publish_report.metadata_state == constants.STATE_FAILED:
            self.publish_metadata_spinner.next(finished=True)
            self.prompt.render_failure_message(_('... failed'))
            self.prompt.render_spacer()
            self._render_error(publish_report.packages_error_message,
                               publish_report.packages_exception,
                               publish_report.packages_traceback)

        self.publish_metadata_last_state = publish_report.metadata_state

    def _display_publish_http_https_step(self, publish_report):

        # -- HTTP --------
        if publish_report.publish_http != constants.STATE_NOT_STARTED and \
           self.publish_http_last_state not in constants.COMPLETE_STATES:

            self.prompt.write(_('Publishing repository over HTTP...'))

            if publish_report.publish_http == constants.STATE_SUCCESS:
                self.prompt.write(_('... completed'), tag='http-completed')
            elif publish_report.publish_http == constants.STATE_SKIPPED:
                self.prompt.write(_('... skipped'), tag='http-skipped')
            else:
                self.prompt.write(_('... unknown'), tag='http-unknown')

            self.publish_http_last_state = publish_report.publish_http

            self.prompt.render_spacer()

        # -- HTTPS --------
        if publish_report.publish_https != constants.STATE_NOT_STARTED and \
           self.publish_https_last_state not in constants.COMPLETE_STATES:

            self.prompt.write(_('Publishing repository over HTTPS...'))

            if publish_report.publish_https == constants.STATE_SUCCESS:
                self.prompt.write(_('... completed'), tag='https-completed')
            elif publish_report.publish_https == constants.STATE_SKIPPED:
                self.prompt.write(_('... skipped'), tag='https-skipped')
            else:
                self.prompt.write(_('... unknown'), tag='https-unknown')

            self.publish_https_last_state = publish_report.publish_https

    def _render_itemized_in_progress_state(self, items_done, items_total, type_name,
                                           progress_bar, current_state):
        """
        This is a pretty ugly way of reusing similar code between the publish
        steps for packages and distributions. There might be a cleaner way
        but I was having trouble updating the correct state variable and frankly
        I'm out of time. Feel free to fix this if you are inspired.
        """

        # For the progress bar to work, we can't write anything after it until
        # we're completely finished with it. Assemble the download summary into
        # a string and let the progress bar render it.

        message_data = {
            'name': type_name.title(),
            'items_done': items_done,
            'items_total': items_total,
            }

        template = _('%(name)s: %(items_done)s/%(items_total)s items')
        bar_message = template % message_data

        # If there's nothing to download in this step, flag the bar as complete
        if items_total is 0:
            items_total = items_done = 1

        progress_bar.render(items_done, items_total, message=bar_message)

        if current_state == constants.STATE_SUCCESS:
            self.prompt.write(_('... completed'))
            self.prompt.render_spacer()

    def _render_package_errors(self, individual_errors):
        """
        :param individual_errors:   dictionary where keys are package names and
                                    values are dicts with keys 'exception' and
                                    'traceback'.
        :type  individual_errors:   dict
        """

        if individual_errors:
            # TODO: read this from config
            display_error_count = 20

            self.prompt.render_failure_message(_('Could not import the following packages:'))

            for package_name in individual_errors.keys()[:display_error_count]:
                self.prompt.write(package_name, color=COLOR_FAILURE)

            self.prompt.render_spacer()

    def _render_error(self, error_message, exception, traceback):
        msg = _('The following error was encountered during the previous '
                'step. More information can be found in %(log)s')
        self.prompt.render_failure_message(msg % {'log': self.context.config['logging']['filename']})
        self.prompt.render_spacer()
        self.prompt.render_failure_message('  %s' % error_message)

        self.context.logger.error(error_message)
        self.context.logger.error(exception)
        self.context.logger.error(traceback)
