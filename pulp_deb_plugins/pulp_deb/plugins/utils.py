from pulp_deb.common import constants, model


def dist_from_config(config):
    return model.Distribution(**config.get(constants.CONFIG_DIST))
