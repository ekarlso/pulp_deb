import copy
from debian.deb822 import Packages, Sources
import gzip
import re

from pulp.common.compat import json
from pulp_deb.common import constants


UNIT_KEYS = ['package', 'version', 'maintainer']


RESOURCE_TYPES = {
    'sources': Sources,
    'packages': Packages
}


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


class Model(object):
    def __init__(self, **kw):
        self.data = kw

    def update(self, data):
        """
        Updates the instance variables with the values in the given dict.
        """
        self.data.update(data)

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __contains__(self, key):
        return key.lower() in self.data

    @staticmethod
    def lowered_key(key):
        return key.lower()

    @staticmethod
    def uppered_key(key):
        return '-'.join([i.title() for i in key.split("-")])

    @classmethod
    def from_dict(cls, data):
        """
        Parses the given snippet of model data into an object
        representation. This call assumes the JSON has already been parsed

        :return: object representation of the given data
        :rtype:  Model
        """
        return cls(data)

    def to_dict(self, exclude=[], **kw):
        data = self.data.copy()
        data = dict([(k, v) for k, v in data.items() if not k in exclude])
        data.update(kw)
        return data

    def serialize(self, exclude=[], **kw):
        """
        Serializes a Model

        :return: dict repr of the Model
        :rtype: dict
        """
        data = self.to_dict(**kw)

        def _dictable(obj):
            if hasattr(obj, 'to_dict'):
                print "DICTABLE", obj
                return True
            else:
                return False

        def _list(values):
            data = []
            for obj in values:
                i = _dict(obj)
                if type(i) == dict:
                    i = _dict(i)
                data.append(i)
            return data

        def _dict(values):
            if type(values) in (list, set):
                data = _list(values)
            elif type(values) == dict:
                data = dict([(k, _dict(v)) for k, v in values.items()])
            else:
                if _dictable(values):
                    data = values.to_dict(exclude=exclude)
                else:
                    data = values
            return data

        return _dict(data)

    def update_from_json(self, json_str):
        data = json.loads(json_str)
        self.update_from_dict(data)

    def to_json(self, **kw):
        return json.dumps(self.serialize())


class Distribution(Model):
    """
    A distribution - typically in pulp sense a repo
    """
    def __init__(self, **kw):
        components = list()
        for values in kw.get('components', {}):
            cmpt = Component(
                dist=self,
                **values)
            if values['name'] in components:
                raise ValueError('Multiple components with the same name is now allowed')
            components.append(cmpt)
        kw['components'] = components
        super(Distribution, self).__init__(**kw)

    def get_component(self, name):
        for c in self.data['components']:
            if c['name'] == name:
                return c

    def add_package(self, component_name, package):
        component = self.get_component(component_name)
        component.add_package(package)

    def add_packages(self, component_name, packages):
        for pkg in packages:
            self.add_package(component_name, pkg)



class Component(Model):
    """
    The Component sits under a repository holding the packages
    """
    def __init__(self, dist=None, **kw):
        self.dist = dist
        super(Component, self).__init__(**kw)
        self.data['packages'] = []

    def add_package(self, package):
        """
        Adds a package to this Component
        """
        self.data['packages'].append(Package(**package))

    def add_packages(self, packages):
        for p in packages:
            self.add_package(p)

    def update_from_index(self, index, **kw):
        """
        Updates this instance with packages in the given Packages file.

        :return: object representing the repository and all it's packages
        :rtype: Repository
        """
        lines = _read(index)
        if re.match(index, 'Sources'):
            data = Sources.iter_paragraphs(lines)
        elif re.match(index, 'Packages'):
            data = Packages.iter_paragraphs(lines)
        else:
            raise RuntimeError('Must be either Sources or Packages')

        self.add_packages(data)

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


class Package(Model):
    """
    A Pulp object sitting ontop of a deb822 object
    """
    def __init__(self, deb=None, **kw):
        if isinstance(deb, Packages):
            self.data = deb
        else:
            self.data = Packages(kw)

    def to_dict(self, full=True, **kw):
        """
        Returns a dict view on the package in the same format as was parsed from
        update_from_dict.

        :return: dict view on the package
        :rtype: dict
        """
        data = super(Package, self).to_dict(**kw)
        data = dict([(self.lowered_key(k), v) for k, v in data.items()])

        if not full:
            return data

        data.update({
            'prefix': self.prefix(),
            'filename_short': self.filename().split('/')[-1]
        })
        return data

    @classmethod
    def from_unit(cls, pulp_unit):
        """
        Converts a Pulp unit into a Deb representation.

        :param pulp_unit: unit returned from the Pulp conduit
        :type  pulp_unit: pulp.plugins.model.Unit

        :return: object representation of the given package
        :rtype:  Package
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
        pkg = self.data.get('package')
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
        """
        Get the filename from the self.data

        :return: package standard filename for this package
        :rtype: str
        """
        return self.data.get('filename')

    def filename_from_data(self, data={}):
        """
        Construct the filename from our own data

        :return: package standard filename for this package
        :rtype: str
        """
        data_ = self.to_dict()
        data_.update(data)
        return constants.DEB_FILENAME % data_

    def filename_short(self):
        """
        :return: Only the filename of this package
        :rtype: str
        """
        return self.filename().split('/')[-1]

    def key(self):
        """
        Get the key representing this package
        """
        return constants.DEB_KEY % self.to_dict()
