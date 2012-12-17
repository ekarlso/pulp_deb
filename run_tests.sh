# Please keep the following in alphabetical order so it's easier to determine
# if something is in the list

PACKAGES="pulp_deb"

# Test Directories
TESTS="pulp_deb_common/test/unit pulp_deb_extensions_admin/test/unit pulp_deb_plugins/test/unit"

nosetests --with-coverage --cover-html --cover-erase --cover-package $PACKAGES $TESTS
