import copy
from debian.deb822 import Packages, Sources

from pulp.common.compat import json
from pulp_deb.common import constants, utils


UNIT_KEYS = ['package', 'version', 'maintainer']


SUPPORTED = {
    'Packages': Packages,
    'Sources': Sources}


KEY_TO_NAME = [('source', 'Packages'), ('binary', 'Sources')]


def get_deb822_cls(obj):
    """
    Get the deb822 class to use based on obj
    """
    if isinstance(obj, basestring):
        key = obj.split('/')[-1][:-len('.gz')]
    elif isinstance(obj, dict):
        # NOTE: Support a resource object
        if 'type' in obj:
            key = obj['type'].title()
        else:
            for map_key, cls_key in KEY_TO_NAME:
                if map_key in [k.lower() for k in obj.keys()]:
                    key = cls_key
                    break
    return SUPPORTED[key]


def get_index_content(obj, **kw):
    """
    Get the index content based on obj
    """
    path = obj

    # NOTE: It's already a read content list
    if isinstance(obj, list):
        return obj
    elif isinstance(obj, dict):
        # NOTE: It's a resource with content inside...
        if 'content' in obj:
            return obj['content']
        # NOTE: It's a resource with a path that should be read.
        elif 'path' in obj:
            path = obj['path']
    # NOTE: It's just a path, read it
    return utils._read(path, **kw)


def _iter_paragraphs_path(obj, empty_on_io=False):
    # NOTE: Add exception here?
    type_cls = get_deb822_cls(obj)
    content = get_index_content(obj, empty_on_io=empty_on_io)
    return type_cls.iter_paragraphs(content)


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
            cmpt.update_from_index(resource)

    def get_package_resources(self):
        resources = []
        for cmpt in self.components:
            resources.extend(cmpt.get_package_resources())
        return resources

    @property
    def components(self):
        return self.data['components']

    @property
    def packages(self):
        data = []
        for cmpt in self.components:
            data.extend(cmpt.packages)
        return data

    def get_resource_data(self, **kw):
        """
        Get some data to use for resources

        :return: Resource dict
        :rtype: dict
        """
        data = dict(
            url=self['url'],
            dist=self['name'])
        data.update(kw)
        return data

    def get_indexes(self):
        """
        Get the indexes that represents this Distribution from the underlying
        Components

        :return: List of resources
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
        """
        Add a list of packages

        :return: A list of packages
        :rtype: list
        """
        for p in packages:
            self.add_package(p)

    def update_from_index(self, data, **kw):
        """
        Updates this instance with packages in the given Packages file.

        :return: object representing the repository and all it's packages
        :rtype: Repository
        """
        packages = _iter_paragraphs_path(data, **kw)
        self.add_packages([{'deb822': p} for p in packages])

    def update_from_indexes(self, data, **kw):
        """
        Update from a list of indexes

        :param data: Indexes from which to update from
        :type data: list
        """
        for i in data:
            self.update_from_index(i, **kw)

    def get_indexes(self):
        """
        Return all indexes related to this Component under a Distribution

        :return: A list of index resources
        :rtype: list
        """
        resources = []

        data = self.get_resource_data(type='sources')
        data['url'] = constants.URLS['sources'] % data
        resources.append(data)

        for arch in self.data['arch']:
            data = self.get_resource_data(type='packages', arch=arch)
            data['url'] = constants.URLS['packages'] % data
            resources.append(data)
        return resources

    def update_from_json(self, json_string):
        """
        Updates this metadata instance with packages found in the given JSON
        document. This can be called multiple times to merge multiple
        repository metadata JSON documents into this instance.

        :param json_string: A JSON string
        :type json_string: basestr
        """
        parsed = json.loads(json_string)
        self.add_packages(parsed.pop('packages', []))
        self.data(parsed)

    def get_resource_data(self, **kw):
        return self.dist.get_resource_data(component=self['name'], **kw)

    def get_package_resources(self):
        """
        Get a list of package resources

        :return: list of package resources
        :rtype: list
        """
        resources = []
        for pkg in self.packages:
            resource_data = self.get_resource_data()
            resources.extend(pkg.get_resources(resource_data))
        return resources


class Package(Model):
    """
    A Pulp object sitting ontop of a deb822 object
    """
    def __init__(self, deb822=None, **kw):
        if isinstance(deb822, (Packages, Sources)):
            self.data = deb822
        else:
            type_cls = get_deb822_cls(kw)
            self.data = type_cls(kw)

    @property
    def package_type(self):
        if 'source' in self:
            return 'package'
        elif 'binary' in self:
            return 'source'

    @property
    def package_source_name(self):
        return self['source'] if self.package_type == 'package' else self.name

    @property
    def name(self):
        return self['package']

    @property
    def prefix(self):
        pkg = self.name
        prefix = pkg[0:4] if pkg.startswith('lib') else pkg[0]
        return prefix

    @property
    def key(self):
        """
        Get the key representing this package
        """
        return constants.DEB_KEY % self.to_dict()

    @property
    def files(self):
        """
        Return all files associated with this package
        """
        files = []
        if self.package_type == 'package':
            file_data = dict([(k, self[k]) \
                             for k in ['size', 'sha1', 'sha256', 'md5sum']])
            file_data['name'] = self['filename'].split('/')[-1]
            files.append(file_data)
        else:
            for d in self['files']:
                file_data = d.copy()
                # Get checksum data as well...
                for key in ['sha1', 'sha256']:
                    for data in self['checksums-' + key]:
                        if file_data['name'] == data['name']:
                            file_data[key] = data[key]
                files.append(file_data)
        return files

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
        data = dict([(k.lower(), v) for k, v in data.items()])

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

    def get_resources(self, resource_data):
        """
        Get the resources for this package

        :param resource_data: Resource data to use
        :type resource_data: dict

        :return: Resource dict.
        :rtype: dict
        """
        resources = []
        for resource in self.files:
            resource.update(resource_data)

            relative_path = self.relative_path(
                resource, prefix=self.prefix, source_name=self.package_source_name)
            resource['url'] = resource['url'] + relative_path
            resources.append(resource)
        return resources

    def relative_path(self, data, **kw):
        """
        Construct a relative path based on our own data.

        :return: Relative path for this package object
        :rtype: str
        """
        path_data = data.copy()
        path_data.update(kw)
        return constants.DEB_FILENAME % path_data
