from .StarList import StarList
from .file_helpers import *
from .daofiles import parse_dao_hdr, write_dao_header, DAO_file_firstline
import pandas as pd
import re

_ds9_regexp = re.compile(r'[+-]? *circle[( ] *([+-]?\d+[.]?\d*) *[, ] *([+-]?\d+[.]?\d*).+#.*id *= *(\d+)')


def read_ds9_regions(file):
    # type: (object) -> StarList
    """
    Reads ds9 region
    :param file: filename or open input stream
    :return: StarList object
    """

    f, to_close = get_stream(file, 'rt')
    # s = StarList.new()
    data = []
    dao_hdr1 = None
    hdr = None
    for line in f:
        if line[0] == '#':
            if line[1:11] == DAO_file_firstline[:10]:  # dao header found in comment
                dao_hdr1 = line
                continue
            if dao_hdr1 is not None:  # second line of dao header
                hdr = parse_dao_hdr(dao_hdr1, line, '#')
        else:
            m = _ds9_regexp.search(line)
            if m is not None:  # s[id] = (id, x, y)
                data.append([int(m.group(3)), float(m.group(1)), float(m.group(2))])
        dao_hdr1 = None
    close_files(to_close)
    s = StarList(data, columns = ['id', 'x', 'y'])
    s.index = s['id']
    s.DAO_hdr = hdr
    return s


def write_ds9_regions(starlist, filename,
                      color='green', width=1, size=8, font=None, label='{id:.0f}',
                      exclude=None, indexes=None, colors=None, sizes=None, labels=None,
                      color_column=None, size_column=None,
                      comment=None, add_global=None):
    """
    Writes ds9 region file.
    Some regions can be visually distinguish by providing additional indexes to select those regions
    with specific attributes
    :param StarList starlist: StarList object to dump
    :param str filename:      output filename
    :param str color:         default color
    :param int width:         default line width
    :param int size:          default radius
    :param str font:          ds9 font specification e.g. "times 12 bold italic"
    :param str label:         format expression for label, use col names
    :param pd.Index exclude:  index of disabled regions, if None all are enabled
    :param [pd.Index] indexes: additional indexes to include specific color and size attributes
    :param [str] colors:      specific colors for indexes
    :param [int] sizes:       specific sizes for indexes
    :param [str] labels:      specific labels for indexes
    :param str color_column:  column of starlist with color values
    :param str size_column:   column of starlist with size values
    :param str add_global:    content of additional 'global' if not None
    :param str comment:       content of additional comment line if not None
    Example:
    write_ds9_regions(sl, 'i.reg', color='blue',
                        indexes=[saturated, psf],
                        colours=['yellow', 'red'],
                        sizes=[12, None],
                        labels=[None, 'PDF:{id}'],
                        exclude=faint)
    Generates regions file i.reg of blue circles, radius 8,
    objects present in index saturated will have larger yellow circles
    objects present in index psf will be red and labeled with prefix PSF:
    objects present in index faint will be disabled by '-' sign and not displayed by ds9, but can be parsed back
    """
    f, to_close = get_stream(filename, 'w')
    f.write('# Region file format: DS9 version 4.0\n')
    if starlist.DAO_hdr is not None:
        write_dao_header(starlist.DAO_hdr, f, '#')
    if comment is not None:
        f.write('#{}\n'.format(comment))
    if color is not None:
        f.write('global color={}\n'.format(color))
    if width is not None:
        f.write('global width={}\n'.format(width))
    if font is not None:
        f.write('global font={}\n'.format(font))
    if add_global is not None:
        f.write('global {}\n')
    for i, row in starlist.iterrows():
        if exclude is not None and i in exclude:
            f.write('-')
        s = size
        text = label.format(**row)
        c = ''
        if size_column is not None:
            s = row[size_column]
        if color_column is not None:
            c = row[color_column]
        if indexes is not None:
            for n in range(len(indexes)):
                if i in indexes[n]:
                    if sizes and sizes[n] is not None:
                        s = sizes[n]
                    if colors and colors[n] is not None:
                        c = ' color=' + colors[n]
                    if labels and labels[n] is not None:
                        text = labels[n].format(**row)
        f.write('circle({},{},{}) #{} text="{}" id={:d}\n'.format(row.x, row.y, s, c, text, i))
    close_files(to_close)
