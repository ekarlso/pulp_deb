import gzip


def _read(f, empty_on_io=False):
    """
    Read a file to a string or a list

    :param f: Either a 'file' object or a filename
    :type f: str or file

    :param empty_on_io: Return empty on IOError
    :type empty_on_io: bool

    :param as_list: Return contents as a list
    :type as_list: boo

    :return: list or string of the file contents
    :rtype: list or string
    """
    try:
        fh = None
        if isinstance(f, basestring):
            fh = open(f)

        if fh is not None and f.endswith('.gz'):
            fh = gzip.GzipFile(fileobj=fh)
        elif isinstance(f, file):
            fh = f
        else:
            raise RuntimeError('Need to pass either a path or a file')
    except IOError:
        if empty_on_io:
            return []
        else:
            raise
    return fh.readlines()
