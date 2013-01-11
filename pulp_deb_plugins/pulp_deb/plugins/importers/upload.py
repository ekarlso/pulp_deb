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

import copy
import shutil

from pulp_deb.common import constants
from pulp_deb.common.model import Package
# from pulp_deb.plugins.importers import metadata as metadata_parser

def handle_uploaded_unit(repo, type_id, unit_key, metadata, file_path, conduit):
    """
    Handles an upload unit request to the importer. This call is responsible
    for moving the unit from its temporary location where Pulp stored the
    upload to the final storage location (as dictated by Pulp) for the unit.
    This call will also update the database in Pulp to reflect the unit
    and its association to the repository.

    :param repo: repository into which the unit is being uploaded
    :type  repo: pulp.plugins.model.Repository
    :param type_id: type of unit being uploaded
    :type  type_id: str
    :param unit_key: unique identifier for the unit
    :type  unit_key: dict
    :param metadata: extra data about the unit
    :type  metadata: dict
    :param file_path: temporary location of the uploaded file
    :type  file_path: str
    :param conduit: for calls back into Pulp
    :type  conduit: pulp.plugins.conduit.upload.UploadConduit
    """

    if type_id != constants.TYPE_DEB:
        raise NotImplementedError()

    # Create a deb out of the uploaded metadata
    combined = copy.copy(unit_key)
    combined.update(metadata)
    deb = Package.from_dict(combined)

    # Extract the metadata from the package
    # FIXME: What does this do?
    metadata_parser.extract_metadata(package, file_path, repo.working_dir)

    # Create the Pulp unit
    type_id = constants.TYPE_DEB
    unit_key = deb.unit_key()
    unit_metadata = deb.unit_metadata()
    relative_path = constants.STORAGE_DEB_RELATIVE_PATH % deb.filename()

    unit = conduit.init_unit(type_id, unit_key, unit_metadata, relative_path)

    # Copy from the upload temporary location into where Pulp wants it to live
    shutil.copy(file_path, unit.storage_path)

    # Save the unit into the destination repository
    conduit.save_unit(unit)


