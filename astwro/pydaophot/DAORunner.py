# coding=utf-8
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import tempfile
import random
from collections import namedtuple
from .Runner import Runner
import astwro.starlist as sl


class DAORunner(Runner):
    """base for daophot package runners runner"""

    def __init__(self, dir=None, batch=False):
        super(DAORunner, self).__init__(dir=dir, batch=batch)

    def __deepcopy__(self, memo):
        return super(DAORunner, self).__deepcopy__(memo)

    # dao files management
    def apertures_file_push(self, src_path):
        """
        Copies aperture file photo.opt into working dir. File will be used by daophot
        :param str src_path: patch to src file
        :rtype: None
        """
        self.copy_to_runner_dir(src_path, 'photo.opt')

    def apertures_file_pull(self, dst_path = '.'):
        """
        Extracts current aperture file photo.opt from working dir.
        :param dst_path: destination
        :rtype: None
        """
        self.copy_from_runner_dir('photo.opt', dst_path)

    def apertures_file_create(self, apertures, IS, OS):
        """
        Creates photo.opt in daophot working dir from list
        :param list apertures: list of apertures A1,A2... e.g. [6.0,8.0,12.0]
        :param float IS: inner radius of sky annulus
        :param float OS: outer radius of sky annulus
        :rtype: None
        """
        assert len(apertures) > 0 and len(apertures) < 13
        self.rm_from_runner_dir('photo.opt')
        with open(os.path.join(self.dir, 'photo.opt'), 'w') as f:
            f.write(''.join('A{:1X}={:.2f}\n'.format(n+1, v) for n,v in zip(range(len(apertures)), apertures)))
            f.write('IS={:.2f}'.format(IS))
            f.write('OS={:.2f}'.format(OS))

    def read_starlist(self, filepath, **kwargs):
        # type: ([str], []) -> sl.StarList
        """
        Returns `StarList` object with stars extracted from daophot files
        :param [str] filepath: source file for starlist, if filename without path is provided, runner directory is assumed.
        :param  kwargs: additional parameters for extra processing in subclasses e.g. add_psf_errors=True
        :rtype: starlist.StarList
        """
        s = sl.read_dao_file(self.absolute_path(filepath))
        return self._process_starlist(s, **kwargs)

    def write_starlist(self, stars, filename=None, dao_file_type=None):
        # type: (sl.StarList, [str], namedtuple) -> str
        """
        Writes `StarList` object to file in runner directory 
        :param  sl.StarList stars: star list to be written
        :param  filename: name of file in runner directory, default: random name with extension '.stars'
        :return name of file in runner directory
        """
        if dao_file_type is None:
            dao_file_type = stars.DAO_type
        if filename is None:
            ext = dao_file_type.extension if dao_file_type else '.stars'
            filename = self._runner_dir_file_name(signature=random.random(), suffix=ext)
        sl.write_dao_file(stars, os.path.join(str(self.dir), filename), dao_type=dao_file_type)
        return filename


    def _prepare_input_file(self, data):
        # check if input has a form of StarList
        if isinstance(data, sl.StarList):
            #TODO: provide file types and/or extensions?
            data = self.write_starlist(data)
        return super(DAORunner, self)._prepare_input_file(data)

    def _process_starlist(self, s, **kwargs):
        return s

