import copy
from debian.deb822 import Packages, Sources

from pulp.common.compat import json
from pulp_deb.common import constants, utils


UNIT_KEYS = ['package', 'version', 'maintainer']


SUPPORTED = {
    'Packages': Packages,
    'Sources': Sources}


KEY_TO_NAME = [('Source', 'Packages'), ('Binary', 'Sources')]


def _type(obj):
    key = None
    if isinstance(obj, basestring):
        key = obj.split('/')[-1][:-len('.gz')]
    elif type(obj) == dict:
        for name, key in KEY_TO_NAME:
            if name in [k.lower() for k in obj.keys()]:
                key = k
                break

    if key not in SUPPORTED:
        msg = 'Can\'t get class for data: %s' % obj
        raise RuntimeError(msg)
    return SUPPORTED[key]


def _iter_paragraphs_path(index, empty_on_io=False):
    # NOTE: Add exception here?
    type_cls = _type(index)
    lines = utils._read(index, empty_on_io=empty_on_io)
    return type_cls.iter_paragraphs(lines)


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
        return cls(**data)

    def data_to_dict(self):
        """
        Some models doesn't have a working .copy() method.
        """
        return self.data.copy()

    def to_dict(self, exclude=[], **kw):
        data = self.data_to_dict()
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

    def update_from_resources(self, resources):
        """
        Update each component in this Distribution from it's own indexes
        """
        for resource in resources:
            cmpt_name = resource['component']
            cmpt = self.get_component(cmpt_name)
            cmpt.update_from_index(resource['path'])

    def get_package_resources(self):
        data = []
        for cmpt in self.components:
            data.extend(cmpt.get_package_resources())
        return data

    @property
    def components(self):
        return self.data['components']

    @property
    def packages(self):
        data = []
        for cmpt in self.components:
            data.extend(cmpt.packages)
        return data

    def get_indexes(self):
        """
        Get the indexes that represents this Distribution from the underlying
        Components

        :return: List of indexes
        :rtype: list
        """
        indexes = []
        for c in self.components:
            indexes.extend(c.get_indexes())
        return indexes

    def get_component(self, name):
        """
        Get a component by name

        :return: A Component object representing the wanted component
        :rtype: Component
        """
        for cmpt in self.components:
            if cmpt['name'] == name:
                return cmpt

    def add_package(self, component_name, package):
        """
        Add a package to a component

        :param component_name: The component
        :param package: The package as a dict, may have deb822=Package
                        if it's already a deb822 object
        """
        component = self.get_component(component_name)
        component.add_package(package)

    def add_packages(self, component_name, packages):
        """
        Add multiple Packages to a component

        :param component_name: The component
        :param packages: A list of Package
        """
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

    @property
    def packages(self):
        return self.data['packages']

    def add_package(self, package):
        """
        Adds a package to this Component
        """
        obj = package if isinstance(package, Package) else Package(**package)
        self.data['packages'].append(obj)

    def add_packages(self, packages):
        for p in packages:
            self.add_package(p)

    def update_from_index(self, index, empty_on_io=False):
        """
        Updates this instance with packages in the given Packages file.

        :return: object representing the repository and all it's packages
        :rtype: Repository
        """
        data = _iter_paragraphs_path(index, empty_on_io=empty_on_io)
        self.add_packages([{'deb822': p} for p in data])

    def update_from_indexes(self, indexes, empty_on_io=False):
        """
        Update from a list of indexes
        """
        for index in indexes:
            self.update_from_index(index, empty_on_io=empty_on_io)

    def get_indexes(self):
        """
        Return all indexes related to this Component under a Distribution
        """
        r = []
        data = dict(
            url=self.dist.data['url'],
            dist=self.dist.data['name'],
            component=self.data['name'])

        def _r(t, **kw):
            d = data.copy()
            d.update(kw)
            url = constants.URLS[t] % d
            d['url'] = url
            d['source'] = url[len('file://'):]
            d['type'] = t
            return d

        r.append(_r('sources'))

        for arch in self.data['arch']:
            r.append(_r('packages', arch=arch))
        return r

    def update_from_json(self, json_string):
        """
        Updates this metadata instance with packages found in the given JSON
        document. This can be called multiple times to merge multiple
        repository metadata JSON documents into this instance.

        :return: object representing the repository and all of its packages
        :rtype:  Repository
        """
        parsed = json.loads(json_string)
        self.add_packages(parsed.pop('packages', []))
        self.data(parsed)

    def get_package_resources(self):
        resources = []
        for pkg in self.packages:
            url = self.dist['url'] + '/' + pkg.filename()
            data = {
                'url': url,
                'source': url[len('file://'):],
                'component': self['name'],
                'dist': self.dist['name'],
                'type': 'package'
            }
            resources.append(data)
        return resources


class Package(Model):
    """
    A Pulp object sitting ontop of a deb822 object
    """
    def __init__(self, deb822=None, **kw):
        if isinstance(deb822, (Packages, Sources)):
            self.data = deb822
        else:
            type_cls = _type(kw)
            self.data = type_cls(kw)

    def data_to_dict(self):
        return dict(self.data)

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
