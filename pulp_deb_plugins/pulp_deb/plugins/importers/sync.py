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

from datetime import datetime
from gettext import gettext as _
import logging
import ipdb
import os
import shutil
import sys

from pulp.common.util import encode_unicode
from pulp.plugins.conduits.mixins import UnitAssociationCriteria

from pulp_deb.common import constants
from pulp_deb.common.constants import (STATE_FAILED, STATE_RUNNING, STATE_SUCCESS)
from pulp_deb.common.model import Repository, Package
from pulp_deb.common.sync_progress import SyncProgressReport
from pulp_deb.plugins.importers.downloaders import factory as downloader_factory

_LOG = logging.getLogger(__name__)

# -- public classes -----------------------------------------------------------


class PackageSyncRun(object):
    """
    Used to perform a single sync of a Debian repository. This class will
    maintain state relevant to the run and should not be reused across runs.
    """

    def __init__(self, repo, sync_conduit, config, is_cancelled_call):
        self.repo = repo
        self.sync_conduit = sync_conduit
        self.config = config
        self.is_cancelled_call = is_cancelled_call

        self.progress_report = SyncProgressReport(sync_conduit)

    def perform_sync(self):
        """
        Performs the sync operation according to the configured state of the
        instance. The report to be sent back to Pulp is returned from this
        call. This call will make calls into the conduit's progress update
        as appropriate.

        This call executes serially. No threads are created by this call. It
        will not return until either a step fails or the entire sync is
        completed.

        :return: the report object to return to Pulp from the sync call
        :rtype:  pulp.plugins.model.SyncReport
        """
        _LOG.info('Beginning sync for repository <%s>' % self.repo.id)

        try:
            repo = self._get_repo_from_resources()
            if not repo:
                report = self.progress_report.build_final_report()
                return report

            self._import_packages_from_repo(repo)
        finally:
            # One final progress update before finishing
            self.progress_report.update_progress()

            report = self.progress_report.build_final_report()
            return report

    def _get_repo_from_resources(self):
        """
        Takes the necessary actions (according to the run configuration) to
        retrieve and parse the repository's resources. This call will return
        either the successfully parsed resources or None if it could not
        be retrieved or parsed. The progress report will be updated with the
        appropriate description of what went wrong in the event of an error,
        so the caller should interpet a None return as an error occuring and
        not continue the sync.

        :return: object representation of the resources
        :rtype:  Repository
        """
        _LOG.info('Beginning resources retrieval for repository <%s>' % self.repo.id)

        self.progress_report.resource_state = STATE_RUNNING
        self.progress_report.update_progress()

        start_time = datetime.now()

        # Retrieve the metadata from the source
        try:
            downloader = self._create_downloader()
            resources = downloader.retrieve_resources(self.progress_report)
        except Exception, e:
            _LOG.exception('Exception while retrieving resources for repository <%s>' % self.repo.id)
            self.progress_report.state = STATE_FAILED
            self.progress_report.error_message = _('Error downloading resources')
            self.progress_report.exception = e
            self.progress_report.traceback = sys.exc_info()[2]

            end_time = datetime.now()
            duration = end_time - start_time
            self.progress_report.execution_time = duration.seconds

            self.progress_report.update_progress()

            return None

        # Parse the retrieved resoruces documents
        try:
            repo = Repository()
            repo.update_from_resources(resources)
        except Exception, e:
            _LOG.exception('Exception parsing resources for repository <%s>' % self.repo.id)
            self.progress_report.state = STATE_FAILED
            self.progress_report.error_message = _('Error parsing repository packages resources document')
            self.progress_report.exception = e
            self.progress_report.traceback = sys.exc_info()[2]

            end_time = datetime.now()
            duration = end_time - start_time
            self.progress_report.execution_time = duration.seconds

            self.progress_report.update_progress()

            return None

        # Last update to the progress report before returning
        self.progress_report.state = STATE_SUCCESS

        end_time = datetime.now()
        duration = end_time - start_time
        self.progress_report.execution_time = duration.seconds

        self.progress_report.update_progress()

        return repo

    def _import_packages_from_repo(self, repo):
        """
        Imports each package in the repository into Pulp.

        This method is mostly just a wrapper on top of the actual logic
        of performing an import to set the stage for the progress report and
        more importantly catch any rogue exceptions that crop up.

        :param metadata: object representation of the repository metadata
               containing the packages to import
        :type  metadata: Repository
        """
        _LOG.info('Retrieving packages for repository <%s>' % self.repo.id)

        self.progress_report.packages_state = STATE_RUNNING

        # Do not send the update about the state yet. The counts need to be
        # set later once we know how many are new, so to prevent a situation
        # where the report reflectes running but does not have counts, wait
        # until they are populated before sending the update to Pulp.

        start_time = datetime.now()

        # Perform the actual logic
        try:
            self._do_import_packages_from_repo(repo)
        except Exception, e:
            _LOG.exception('Exception importing packages for repository <%s>' % self.repo.id)
            self.progress_report.packages_state = STATE_FAILED
            self.progress_report.packages_error_message = _('Error retrieving packages')
            self.progress_report.packages_exception = e
            self.progress_report.packages_traceback = sys.exc_info()[2]

            end_time = datetime.now()
            duration = end_time - start_time
            self.progress_report.packages_execution_time = duration.seconds

            self.progress_report.update_progress()

            return

        # Last update to the progress report before returning
        self.progress_report.packages_state = STATE_SUCCESS

        end_time = datetime.now()
        duration = end_time - start_time
        self.progress_report.packages_execution_time = duration.seconds

        self.progress_report.update_progress()

    def _do_import_packages_from_repo(self, repo):
        """
        Actual logic of the import. This method will do a best effort per package;
        if an individual package fails it will be recorded and the import will
        continue. This method will only raise an exception in an extreme case
        where it cannot react and continue.
        """
        downloader = self._create_downloader()

        # Ease lookup of packages
        packages_by_key = dict([(d.key(), d) for d in repo.packages])

        # Collect information about the repository's packages before changing it
        package_criteria = UnitAssociationCriteria(type_ids=[constants.TYPE_DEB])
        existing_units = self.sync_conduit.get_units(criteria=package_criteria)
        existing_packages = [Package.from_unit(u) for u in existing_units]
        existing_package_keys = [p.key() for p in existing_packages]

        new_unit_keys = self._resolve_new_units(existing_package_keys, packages_by_key.keys())
        remove_unit_keys = self._resolve_remove_units(existing_package_keys, packages_by_key.keys())

        # Once we know how many things need to be processed, we can update the
        # progress report
        self.progress_report.packages_total_count = len(new_unit_keys)
        self.progress_report.packages_finished_count = 0
        self.progress_report.packages_error_count = 0
        self.progress_report.update_progress()

        # Add new units
        for key in new_unit_keys:
            package = packages_by_key[key]
            try:
                self._add_new_package(downloader, package)
                self.progress_report.packages_finished_count += 1
            except Exception, e:
                self.progress_report.add_failed_package(package, e, sys.exc_info()[2])

            self.progress_report.update_progress()

        # Remove missing units if the configuration indicates to do so
        if self._should_remove_missing():
            existing_units_by_key = {}
            for u in existing_units:
                unit_key = Package.generate_unit_key(u.unit_key['name'], u.unit_key['version'], u.unit_key['author'])
                s = unit_key_str(unit_key)
                existing_units_by_key[s] = u

            for key in remove_unit_keys:
                doomed = existing_units_by_key[key]
                self.sync_conduit.remove_unit(doomed)

    def _add_new_package(self, downloader, package):
        """
        Performs the tasks for downloading and saving a new unit in Pulp.

        :param downloader: downloader instance to use for retrieving the unit
        :param package: package instance to download
        :type  package: Package
        """
        # Initialize the unit in Pulp
        type_id = constants.TYPE_DEB
        unit_key = package.unit_key()
        unit_metadata = {} # populated later but needed for the init call

        unit = self.sync_conduit.init_unit(type_id, unit_key, unit_metadata,
                                           package.filename())

        print "PATH", unit.storage_path
        if not self._package_exists(unit.storage_path):
            # Download the bits
            downloaded_filename = downloader.retrieve_deb(self.progress_report, package)

            # Create the relative path if it's not there..
            path = os.path.dirname(unit.storage_path)
            if not os.path.exists(path):
                os.makedirs(path)

            # Copy them to the final location
            try:
                shutil.copy(downloaded_filename, unit.storage_path)
            except Exception, e:
                _LOG.error("Error copying package to %s" % unit.storage_path)
                raise

        # NOTE: Maybe we should do this if we import a single package?
        # Extract the extra metadata into the package
        # metadata.extract_metadata(package, unit.storage_path, self.repo.working_dir)

        # Update the unit with the extracted metadata
        unit.metadata = package.unit_metadata()

        # Save the unit and associate it to the repository
        self.sync_conduit.save_unit(unit)

    def _package_exists(self, filename):
        """
        Determines if the package at the given filename is already downloaded.

        :param filename: full path to the package in Pulp
        :type  filename: str

        :return: true if the package file already exists; false otherwise
        :rtype:  bool
        """
        return os.path.exists(filename)

    def _resolve_new_units(self, existing_unit_keys, found_unit_keys):
        """
        Returns a list of unit keys that are new to the repository.

        :return: list of unit keys; empty list if none are new
        :rtype:  list
        """
        return list(set(found_unit_keys) - set(existing_unit_keys))

    def _resolve_remove_units(self, existing_unit_keys, found_unit_keys):
        """
        Returns a list of unit keys that are in the repository but not in
        the current repository metadata.

        :return: list of unit keys; empty list if none have been removed
        :rtype:  list
        """
        return list(set(existing_unit_keys) - set(found_unit_keys))

    def _create_downloader(self):
        """
        Uses the configuratoin to determine which downloader style to use
        for this run.

        :return: one of the *Downloader classes in the downloaders package
        """
        url = self.config.get(constants.CONFIG_URL)
        downloader = downloader_factory.get_downloader(url, self.repo, self.sync_conduit,
                                                       self.config, self.is_cancelled_call)
        return downloader

    def _should_remove_missing(self):
        """
        Returns whether or not missing units should be removed.

        :return: true if missing units should be removed; false otherwise
        :rtype:  bool
        """

        if constants.CONFIG_REMOVE_MISSING not in self.config.keys():
            return constants.DEFAULT_REMOVE_MISSING
        else:
            return self.config.get_boolean(constants.CONFIG_REMOVE_MISSING)
