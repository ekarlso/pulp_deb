import codecs
import copy
from debian.deb822 import Packages
import gzip

from pulp.common.compat import json

from pulp_deb.common import constants


UNIT_KEYS = ['package', 'version', 'maintainer']


class Repository(object):

    def __init__(self):
        self.packages = []

    def _read(self, f):
        if not type(f) == file and type(f) == str:
            fh = open(f)
            if f.endswith('.gz'):
                fh = gzip.GzipFile(fileobj=fh)
        elif type(f) == file:
            fh = f
        else:
            raise RuntimeError('Need to pass either a path or a file')
        return fh.readlines()

    def _update(self, data, **kw):
        for pkg in data:
            pkg.update(kw)

            deb = DebianPackage(pkg)
            self.packages.append(deb)

    def update_from_packages(self, packages_file, **kw):
        """
        Updates this instance with packages in the given Packages file.

        :return: object representing the repository and all it's packages
        :rtype: Repository
        """
        try:
            lines = self._read(packages_file)
        except RuntimeError:
            raise
        self._update(Packages.iter_paragraphs(lines), **kw)

    def update_from_resources(self, resources):
        for resource in resources:
            # NOTE: Store dist and component also
            data = dict([(k, resource[k]) for k in ['dist', 'component']])
            self.update_from_packages(resource['resource'][len('file://'):], **data)

    def update_from_json(self, json_string, **kw):
        """
        Updates this metadata instance with packages found in the given JSON
        document. This can be called multiple times to merge multiple
        repository metadata JSON documents into this instance.

        :return: object representing the repository and all of its packages
        :rtype:  Repository
        """
        parsed = json.loads(json_string)
        self._update(parsed, **kw)

    def to_json(self):
        """
        Serialize this repo to JSON
        """
        package_dicts = [m.to_dict() for m in self.packages]
        serialized = json.dumps(package_dicts)
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
        Parses the given snippet of package metadata into an object
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

    def to_dict(self, full=True):
        """
        Returns a dict view on the package in the same format as was parsed from
        update_from_dict.

        :return: dict view on the package
        :rtype: dict
        """
        data = dict([(self.lowered_key(k), v) for k, v in self._obj.items()])
        if not full:
            return data

        data.update({
            'prefix': self.prefix()
        })
        return data

    def update_from_json(self, json):
        """
        Takes the package's metadata in JSON format and merges it into this
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

        :return: object representation of the given package
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
        Returns the unit key for this package that will uniquely identify
        it in Pulp. This is the unique key for the inventoried package in Pulp.
        """
        data = self.to_dict()
        return self.generate_unit_key(*[data[key] for key in UNIT_KEYS])

    def unit_metadata(self):
        """
        Returns all non-unit key metadata that should be stored in Pulp
        for this package. This is how the package will be inventoried in Pulp.
        """
        data = self.to_dict()
        metadata = [(k, v) for k, v in data.items() if k not in UNIT_KEYS]
        return metadata

    def prefix(self):
        pkg = self._obj.get('package')
        prefix = pkg[0:4] if pkg.startswith('lib') else pkg[0]
        return prefix

    def filename(self):
        """
        Generates the filename for the given package.

        :return: package standard filename for this package
        :rtype: str
        """
        return self.filename_from_deb822() or self.filename_from_data()

    def filename_from_deb822(self):
        return self._obj.get('filename')

    def filename_from_data(self, data={}):
        data_ = self.to_dict()
        data_.update(data)
        return constants.DEB_FILENAME % data_

    def filename_short(self):
        return self.filename().split('/')[-1]
