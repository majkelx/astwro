from __future__ import absolute_import, division, print_function
__metaclass__ = type
# see https://wiki.python.org/moin/PortingToPy3k/BilingualQuickRef
from .DAORunner import DAORunner
from .OutputProviders import *
from .config import find_opt_file


class Allstar(DAORunner):
    """ `daophot` runner

    Object of this class maintains single process of `allstar` and it's working directory.

    Instance attributes:
    :var str allstaropt:   allstar.opt file to be copied into runner dir
    :var DPOP_OPtion  OPtion_result:     initial options reported by `allstar`
    :var DPOP_ATtach  ATtach_result:     results of command ATtach
    :var str image:  image which will be automatically used if not provided in `ALlstars` command
    :var dict options: options which will be automatically set as OPTION command before every run,
                    can be either:
                                dictionary:
                                                        >>> dp = Allstar()
                                                        >>> dp.options = {'PROFILE ERROR': 5, 'FI': '6.0'}
                                iterable of tuples:
                                                        >>> dp.options = [('PR', 5.0), ('FITTING RADIUS', 6.0)]
    """

    def __init__(self, dir=None, image=None, allstaropt=None, options=None, batch=False):
        # type: ([str,object], [str], [str], [list,dict], bool) -> Allstar
        """
        :param [str] dir:          pathname or TmpDir object - working directory for daophot,
                                   if None temp dir will be used and deleted on `Allstar.close()`
        :param [str] image:        if provided this file will be used if not provided in `ALlstars` command
                                   setting image property has same effect
        :param [str] allstaropt:   allstar.opt file, if None build in default file will be used, can be added later
                                   by `Runner.copy_to_runner_dir(file, 'allstar.opt')`
        :param [list,dict] options: if provided options will be set on beginning of each process
                                   list of tuples or dict
        :param bool batch:         whether Allstar have to work in batch mode. 
        """
        if allstaropt is not None:
            self.allstaropt = allstaropt
        else:
            self.allstaropt = find_opt_file('allstar.opt')

        self.image = image
        self.options = {'WA': 0}  # suppress animations
        if options:
            self.options.update(dict(options))

        super(Allstar, self).__init__(dir=dir, batch=batch)
        # base implementation of __init__ calls `_reset` also
        self._update_executable('allstar')

    def _reset(self):
        super(Allstar, self)._reset()
        self.OPtion_result = None
        self.ALlstars_result = None


    def __deepcopy__(self, memo):
        from copy import deepcopy
        new = super(Allstar, self).__deepcopy__(memo)

        new.allstaropt = deepcopy(self.allstaropt, memo)

        # new.OPtion_result = deepcopy(self.OPtion_result, memo)
        # new.ALlstars_result = deepcopy(self.ALlstars_result, memo)

        new.image = deepcopy(self.image, memo)
        new.options = deepcopy(self.options, memo)
        return new

    def _pre_run(self, wait):
        if not self.ALlstars_result:
            raise Allstar.RunnerException('Add ALlstar command before run.')
        super(Allstar, self)._pre_run(wait)
        # set options, and prepare options parser
        commands = ''
        if self.options:  # set options before
            options = self.options
            if isinstance(options, dict):
                options = options.items()  # options is dict
            # else options is list of pairs
            commands += ''.join('%s=%.2f\n' % (k, float(v)) for k, v in options if v is not None)
        commands += '\n'
        processor = AsOp_opt()
        self.OPtion_result = processor
        self._insert_processing_step(commands, output_processor=processor, on_beginning=True)

    def _init_workdir_files(self, dir):
        super(Allstar, self)._init_workdir_files(dir)
        self.link_to_runner_dir(self.allstaropt, 'allstar.opt')

    def set_options(self, options, value=None):
        # type: ([str,dict,list], [str,float]) -> None
        """set option(s) before run. 
        
        Options can be either:
                dictionary:             `dp.OPtion({'GAIN': 9, 'FI': '6.0'})`
                iterable of tuples:     `dp.OPtion([('GA', 9.0), ('FITTING RADIUS', '6.0')])`
                option key, followed by value in 'value' parameter:
                                        `dp.OPtion('GA', 9.0)`
                filename string of allstar.opt-formatted file (file will be symlinked as `allstar.opt`):
                                        `dp.OPtion('opts/newallstar.opt')`
        Once set, options will stay set in next runs, set option to `None` to unset
                """
        if isinstance(options, str) and value is None:  # filename
            # allstar operates in his tmp dir and has limited buffer for file path
            # so symlink file to its working dir
            self.link_to_runner_dir(options, 'allstar.opt')
        else:
            if self.options is None:
                self.options = {}
            if value is not None:  # single value
                options = {options:value}
            elif isinstance(options, list):
                options = dict(options)
            self.options.update(options)

    def ALlstar(self, image_file=None, psf_file='i.psf', stars='i.ap', profile_photometry_file='i.als', subtracted_image_file=None):
        # type: ([str], str, [str,object], str, str) -> AsOp_result
        """
        Runs (or adds to execution queue in batch mode) daophot PICK command. 
        :param [str] image_file: input image filepath, if None, one set in constructor or 'i.fits' will be used
        :param str psf_file: input file with psf from daophot PSF command
        :param str stars: input magnitudes file, e.g. from aperture photometry done by :func:`Daophot.PHotometry`.
        :param str profile_photometry_file: output file with aperture photometry results, default: i.als 
        :param str subtracted_image_file: output file with subtracted FITS image, default: do not generate image
        :return: results object also accessible as :var:`Allstar.ALlstars_result` property
        :rtype: AsOp_result
        """
        self._get_ready_for_commands()  # wait for completion before changes in working dir

        if not image_file:
            image_file = self.image
        if not image_file:
            image_file = 'i.fits'

        l_img, a_img = self._prepare_input_file(image_file)
        l_psf, a_psf = self._prepare_input_file(psf_file)
        l_pht, a_pht = self._prepare_input_file(stars)
        l_als, a_als = self._prepare_output_file(profile_photometry_file)
        l_sub, a_sub = self._prepare_output_file(subtracted_image_file)

        commands = '{}\n{}\n{}\n{}\n{}'.format(l_img, l_psf, l_pht, l_als, l_sub)
        if l_sub:
            commands += '\n'  # if subtracted image not needed, EOF (without new line) should be answer for it (allstar)

        processor = AsOp_result(profile_photometry_file=a_als, subtracted_image_file=a_sub)
        self._insert_processing_step(commands, output_processor=processor)
        self.ALlstars_result = processor
        if not self.batch_mode:
            self.run()
        return processor
