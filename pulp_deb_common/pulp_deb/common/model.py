import copy
from debian.deb822 import Packages

from pulp.common.compat import json

from pulp_deb.common import constants


UNIT_KEYS = ['package', 'version', 'maintainer']


class RepositoryMetadata(object):

    def __init__(self):
        self.packages = []

    def _fh(self, f):
        if not type(f) == file:
            return open(f)
        elif type(f) == file:
            return f
        else:
            raise RuntimeError('Need to pass either a path or a file')

    def _update(self, data):
        for pkg in data:
            deb = DebianPackage(pkg)
            self.packages.append(deb)

    def update_from_packages(self, packages_file):
        """
        Updates this instance with packages in the given Packages file.

        :return: object representing the repository and all it's packages
        :rtype: RepositoryMetadata
        """
        try:
            f = self._fh(packages_file)
        except RuntimeError:
            raise
        self._update(Packages.iter_paragraphs(f))

    def update_from_json(self, json_string):
        """
        Updates this metadata instance with modules found in the given JSON
        document. This can be called multiple times to merge multiple
        repository metadata JSON documents into this instance.

        :return: object representing the repository and all of its modules
        :rtype:  RepositoryMetadata
        """
        parsed = json.loads(json_string)
        self._update(parsed)

    def to_json(self):
        """
        Serialize this repo to JSON
        """
        module_dicts = [m.to_dict() for m in self.modules]
        serialized = json.dumps(module_dicts)
        return serialized


class DebianPackage(object):
    """
    A Pulp object sitting ontop of a deb822 object
    """
    def __init__(self, data):
        if isinstance(data, Packages):
            self._obj = data
        else:
            self._obj = Packages(data)

    @staticmethod
    def lowered_key(key):
        return key.lower()

    @staticmethod
    def uppered_key(key):
        return '-'.join([i.title() for i in key.split("-")])

    @classmethod
    def from_dict(cls, data):
        """
        Parses the given snippet of module metadata into an object
        representation. This call assumes the JSON has already been parsed

        :return: object representation of the given deb
        :rtype:  DebianPackage
        """
        return cls(data)

    def update_from_dict(self, data):
        """
        Updates the instance variables with the values in the given dict.
        """
        self._obj.update(data)

    def to_dict(self):
        """
        Returns a dict view on the module in the same format as was parsed from
        update_from_dict.

        :return: dict view on the module
        :rtype: dict
        """
        return dict([(self.lowered_key(k), v) for k, v in self._obj.items()])

    def update_from_json(self, json):
        """
        Takes the module's metadata in JSON format and merges it into this
        instance.

        :param json: Package metadata in JSON
        :type  json: str
        """
        parsed = json.loads(json)
        self.update_from_dict(parsed)

    @classmethod
    def from_unit(cls, pulp_unit):
        """
        Converts a Pulp unit into a Deb representation.

        :param pulp_unit: unit returned from the Pulp conduit
        :type  pulp_unit: pulp.plugins.model.Unit

        :return: object representation of the given module
        :rtype:  DebianPackage
        """
        unit_as_dict = copy.copy(pulp_unit.unit_key)
        unit_as_dict.update(pulp_unit.metadata)
        return cls.from_dict(unit_as_dict)

    @staticmethod
    def generate_unit_key(package, version, maintainer):
        # FIXME: Make this aligned with UNIT_KEYS stuff?
        return {
            'package': package,
            'version': version,
            'maintainer': maintainer
        }

    def unit_key(self):
        """
        Returns the unit key for this module that will uniquely identify
        it in Pulp. This is the unique key for the inventoried module in Pulp.
        """
        data = self.to_dict()
        return self.generarte_unit_key(*[data[key] for key in UNIT_KEYS])

    def unit_metadata(self):
        """
        Returns all non-unit key metadata that should be stored in Pulp
        for this module. This is how the module will be inventoried in Pulp.
        """
        data = self.to_dict()
        metadata = [(k, v) for k, v in data.items() if k not in UNIT_KEYS]
        return metadata

    def filename(self):
        """
        Generates the filename for the given module.

        :return: puppet standard filename for this module
        :rtype: str
        """
        data = self.to_dict()
        f = constants.DEB_FILENAME % data
        return f
