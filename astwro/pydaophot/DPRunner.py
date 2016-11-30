import os
from .DAORunner import DAORunner, fname
from .config import get_package_config_path
from .OutputProviders import *


class DPRunner(DAORunner):
    """daophot runner"""
    daophotopt = None
    photoopt = None
    preattach_image = None
    # output processors
    OPtion_result = None
    ATtach_result = None
    FInd_result = None
    PHotometry_result = None
    PIck_result = None
    PSf_result = None
    SOrt_result = None
    SUbstar_result = None

    def __init__(self, config=None, dir=None, daophotopt=None, photoopt=None, image=None):
        """
        :param dir:         pathname or TmpDir object - working directory for daophot,
                            if None temp dir will be used and deleted on DPRunner.close()
        :param daophotopt:  daophot.opt file, if None build in default file will be used, can be added later
                            by DPRunner.copy_to_working_dir(file, fname.DAOPHOT_OPT)
        :param photoopt:    photo.opt file, if None build in default file will be used, can be added later
                            by DPRunner.copy_to_working_dir(file, fname.PHOTO_OPT)
        :param image:       if provided this file will be automatically attached (AT) as first daophot command
                            if None ATtache() should be called explicitly
        """
        self.executable = os.path.expanduser(config.get('executables', 'daophot'))
        self.daophotopt = daophotopt if daophotopt is not None else os.path.join(get_package_config_path(), fname.DAOPHOT_OPT)
        self.photoopt   = photoopt   if photoopt   is not None else os.path.join(get_package_config_path(), fname.PHOTO_OPT)
        self.preattach_image = image
        DAORunner.__init__(self, config=config, dir=dir)
        self.OPtion_result = DPOP_OPtion()
        self._insert_processing_step('', output_processor=self.OPtion_result)
        if image:
            self.ATtach(image)

    def __deepcopy__(self, memo):
        from copy import deepcopy
        new = DAORunner.__deepcopy__(self, memo)
        new.daophotopt = deepcopy(self.daophotopt, memo)
        new.photoopt = deepcopy(self.photoopt, memo)
        new.preattach_image = deepcopy(self.preattach_image, memo)
        new.OPtion_result = deepcopy(self.OPtion_result, memo)
        new.ATtach_result = deepcopy(self.ATtach_result, memo)
        new.FInd_result = deepcopy(self.FInd_result, memo)
        new.PHotometry_result = deepcopy(self.PHotometry_result, memo)
        new.PIck_result = deepcopy(self.PIck_result, memo)
        new.PSf_result = deepcopy(self.PSf_result, memo)
        new.SOrt_result = deepcopy(self.SOrt_result, memo)
        new.SUbstar_result = deepcopy(self.SUbstar_result, memo)
        return new

    def _on_exit(self):
        pass

    def _reset(self):
        DAORunner._reset(self)
        self.ATtach_result = None
        self.FInd_result = None
        self.PHotometry_result = None
        self.PIck_result = None
        self.PSf_result = None
        self.SOrt_result = None
        self.SUbstar_result = None
        self.OPtion_result = DPOP_OPtion()
        self._insert_processing_step('', output_processor=self.OPtion_result)
        if self.preattach_image:
            self.ATtach(self.preattach_image)

    def _init_workdir_files(self, dir):
        DAORunner._init_workdir_files(self, dir)
        self.copy_to_working_dir(self.daophotopt)
        self.copy_to_working_dir(self.photoopt)

    # daophot commands
    def ATtach(self, image_file = fname.FITS_FILE):
        """
        Add AT command to run queue. This should be first command. daophot crashes otherwise (at least my version).
        If image_file parameter is provided in constructor, ATtach is done there.
        :param str image_file: image to attach file will be symlinked to work dir as i.fits,
                   if None 'i.fits' (file or symlink) is expected in working dir
        :return: DPOP_ATtach instance for getting results: ATtach_result property
        """
        self._get_ready_for_commands()  # wait for completion before changes in working dir
        image_file = self._prepare_input_file(image_file, fname.FITS_FIL) #TODO: continue with 2nd par
        # self.copy_to_working_dir(image_file, fname.IMAGE_FILE)
        processor = DPOP_ATtach()
        self._insert_processing_step('ATTACH {}\n'.format(image_file), output_processor=processor)
        self.ATtach_result = processor
        return processor

    def EXit(self):
        self._insert_processing_step('EXIT\n', output_processor=DaophotCommandOutputProcessor())

    def OPtion(self, options, value=None):
        """
        Adds daophot OPTION command to execution stack.
        :param options: can be either:
                dictionary:
                                        >>> dp = DPRunner()
                                        >>> dp.OPtion({'GAIN': 9, 'FI': '6.0'})
                iterable of tuples:
                                        >>> dp.OPtion([('GA', 9.0), ('FITTING RADIUS', '6.0')])
                option key, followed by value in 'value' parameter:
                                        >>> dp.OPtion('GA', 9.0)
                filename string of daophot.opt-formatted file:
                                        >>> dp.OPtion('opts/newdaophot.opt')
        :param value: value if `options` is just single key
        :return: results object also accessible as `DPRunner.OPtion_result` property
        :rtype: DPOP_OPtion
        """
        if self.ATtach_result is None:
            warning('daophot (at least some version) crashes on ATtach after OPtion. Expect crash on next ATtach.')
        commands = 'OPT\n'
        if isinstance(options, str) and value is None:  # filename
            # daophot operates in his tmp dir and has limited buffer for file path
            # so symlink file to its working dir
            self._get_ready_for_commands()  # wait for completion before changes in working dir
            self.link_to_working_dir(options, 'tmp.opt')
            commands += 'tmp.opt\n\n'
        else:
            commands += '\n'  # answer for filename
            if value is not None:
                options = [(options,value)]
            elif isinstance(options, dict):
                options = options.items()
            commands += ''.join('%s=%.2f\n' % (k,float(v)) for k,v in options)
            commands += '\n'
        processor = DPOP_OPtion()
        self._insert_processing_step(commands, output_processor=processor)
        self.OPtion_result = processor
        return processor

    def FInd(self, frames_av = 1, frames_sum = 1, starlist_file=fname.FOUNDSTARS_FILE):
        """
        Adds daophot FIND command to execution stack.
        :param int frames_av: averaged frames in image (default: 1)
        :param int frames_sum: summed frames in image (default: 1)
        :param str starlist_file: output coo file, in most cases do not change default i.coo,
            rather copy result using
            >> d.copy_from_work_dir(fname.COO_FILE, dest)
        :return: results object also accessible as `DPRunner.FInd_result` property
        :rtype: DpOp_FInd
        """
        if self.ATtach_result is None:
            raise Exception('No imput file attached, call ATttache first.')
        self._get_ready_for_commands()  # wait for completion before changes in working dir
        self.rm_from_working_dir(starlist_file)
        commands = 'FIND\n{},{}\n{}\nyes\n'.format(frames_av, frames_sum, starlist_file)
        processor = DpOp_FInd()
        self._insert_processing_step(commands, output_processor=processor)
        self.FInd_result = processor
        return processor

    def PHotometry(self, photoopt=None, stars_file=None, photometry_file=None):
        """
        Adds daophot PHOTOMETRY command to execution stack.
        :param str photoopt: photo.opt file to be used,
                default: sample file, file set in constructor or copied into `DPRunner.dir`
        :param str stars_file: input list of stars, default: i.coo in `DPRunner.dir`
        :param str photometry_file:
        :return: results object also accessible as `DPRunner.PHotometry_result` property
        :rtype: DpOp_PHotometry
        """
        self._get_ready_for_commands()  # wait for completion before changes in working dir
        if photometry_file is None:
            self.rm_from_working_dir(fname.PHOTOMETRY_FILE)
        photoopt   = self.expand_default_file_path(photoopt)
        stars_file = self.expand_default_file_path(stars_file)
        photometry_file = self.expand_default_file_path(photometry_file)
        commands='PHOT\n{}\n\n{}\n{}\n'.format(photoopt, stars_file, photometry_file)
        processor = DpOp_PHotometry()
        self._insert_processing_step(commands, output_processor=processor)
        self.PHotometry_result = processor
        return processor

    def PIck(self, number_of_stars_to_pick=50, faintest_mag=20, photometry_file=None, psf_stars_file=None):
        self._get_ready_for_commands()  # wait for completion before changes in working dir
        if photometry_file is None:
            self.rm_from_working_dir(fname.PSF_STARS_FILE)
        photometry_file = self.expand_default_file_path(photometry_file)
        psf_stars_file = self.expand_default_file_path(psf_stars_file)
        commands = 'PICK\n{}\n{:d},{:d}\n{}\n'.format(
            photometry_file,
            number_of_stars_to_pick,
            faintest_mag,
            psf_stars_file
        )
        processor = DpOp_PIck()
        self._insert_processing_step(commands, output_processor=processor)
        self.PIck_result = processor
        return processor

    # TODO: file prameters to commands should be relative to working dir. Defaults given explicite: fname.XXX see: SUbstar
    def PSf(self, photometry_file=None, psf_stars_file=None, psf_file=None):
        self._get_ready_for_commands()  # wait for completion before changes in working dir
        if psf_file is None:
            self.rm_from_working_dir(fname.PSF_FILE)
        self.rm_from_working_dir(fname.NEI_FILE)
        self.rm_from_working_dir(fname.ERR_FILE)
        photometry_file = self.expand_default_file_path(photometry_file)
        psf_stars_file = self.expand_default_file_path(psf_stars_file)
        psf_file = self.expand_default_file_path(psf_file)
        commands = 'PSF\n{}\n{}\n{}\n'.format(
            photometry_file,
            psf_stars_file,
            psf_file
        )
        processor = DpOp_PSf()
        self._insert_processing_step(commands, output_processor=processor)
        self.PSf_result = processor
        return processor

    def SOrt(self, file, by, decreasing=None):
        """
        Adds daophot SORT command to execution stack.
        :param str file: fname.COO_FILE etc... any fname.*_FILE to sort
        :param by:  1-based column number, negative for descending order - daophot standard, or
                    one of 'id', 'x', 'y', 'mag'
        :param bool decreasing:  in not None, forces sort order
        :return: results object, also accessible as `DPRunner.SOrt_result` property
        :rtype: DpOp_Sort
        """
        self._get_ready_for_commands()  # wait for completion before changes in working dir
        if isinstance(by, str):
            by = by.lower()
            if by == 'id': by = 1
            elif by == 'x': by = 2
            elif by == 'y': by = 3
            elif by == 'mag': by = 4
            else:
                raise ValueError('parameter by, if string must be either: "id", "x", "y" or "mag"')
        if decreasing is not None:
            by = -abs(by) if decreasing else abs(by)
        raise NotImplementedError("SORT command not implemented")

    def SUbstar(self, subtract, leave_in=None, subtracted_image=fname.SUB_FILE, psf_file=fname.PSF_FILE):
        # type: (str, str, str, str) -> DpOp_SUbstar
        """
        Adds daophot SUBSTAR command to execution stack.
        :param subtract: relative to work dir pathname of stars to subtract file
        :param leave_in: relative to work dir pathname of stars to be kept file (default: None)
        :param psf_file: relative to work dir pathname of file with PSF (default i.psf)
        :param subtracted_image: relative to work dir pathname of output fits file (default is.fits)
        :return: results object, also accessible as `DPRunner.SUbstar_result` property
        """
        self._get_ready_for_commands()  # wait for completion before changes in working dir
        subtracted_image = self._prepare_output_file(subtracted_image)
        subtract = self._prepare_input_file(subtract)
        if leave_in:
            leave_in = self._prepare_input_file(leave_in)
        psf_file = self._prepare_input_file(psf_file)
        subtracted_image = self._prepare_output_file(subtracted_image)
        if leave_in:
            commands = 'SUB\n{}\n{}\ny\n{}\n{}\n'.format(
                psf_file,
                subtract,
                leave_in,
                subtracted_image
            )
        else:
            commands = 'SUB\n{}\n{}\nn\n{}\n'.format(
                psf_file,
                subtract,
                subtracted_image
            )
        processor = DpOp_SUbstar()
        self._insert_processing_step(commands, output_processor=processor)
        self.SUbstar_result = processor
        return processor

    def _process_starlist(self, s, **kwargs):
        if kwargs['add_psf_errors']:
            import pandas as pd
            err = self.PSf_result.errors
            idx = [i for i,_ in err]
            val = [v for _,v in err]
            col = pd.Series(val, index=idx)
            s['psf_err'] = col
        return s
