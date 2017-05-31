import re
from logging import *
from astwro.starlist import read_dao_file


class AbstractOutputProvider(object):
    """ Abstract class (interface) for chained stream processing """
    def _get_output_stream(self):
        """To be overridden"""
        pass


class StreamKeeper(AbstractOutputProvider):
    """First in the chain, just keeps stream handler"""
    stream = None
    runner = None

    def __init__(self, runner=None, stream=None):
        super(StreamKeeper, self).__init__()
        self.stream = stream
        self.runner = runner

    def _get_output_stream(self):
        if self.stream is None:
            raise Exception('No output stream available, call run() before collecting results.')
        return self.stream


class OutputProvider(AbstractOutputProvider):
    """ Base class for elements of stream processors chain
        also can be used as dummy processor in chain"""

    # previous output provider

    def __init__(self, prev_in_chain=None):
        self.__stream = None
        self._prev_in_chain = prev_in_chain
        self.logger = getLogger('ResultParser')

    def _consume(self, stream):
        """ to be overridden
        :param stream:
        """
        pass

    def _get_output_stream(self):
        if self.__stream is None:
            self.__stream = self._prev_in_chain._get_output_stream()
            self._consume(self.__stream)
        return self.__stream


class OutputLinesProcessor(OutputProvider):
    """ Base for line-by-line processing"""

    def _process_line(self, line, counter):
        """ processes line by line output
            return True if it's last line.
            To be overridden """
        return True

    def _consume(self, stream):
        counter = 0
        for line in stream:
            counter += 1
            self.logger.debug("Output line %3d: %s", counter, line)
            last_one = self._process_line(line, counter)
            if last_one:
                self.logger.debug("Was last line")
                return


class OutputBufferedProcessor(OutputLinesProcessor):
    __buffer = ''

    def _process_line(self, line, counter):
        """ processes line-by-line output
            return True if it's last line.
            If overridden, this base impl should be called """
        self.__buffer += line
        return self._is_last_one(line, counter)

    def _is_last_one(self, line, counter):
        """ return True if it's last line.
            To be overridden """

    def raise_if_error(self, line):
        """ Should raise exception if not properly processed:
            - command did not run
            - buffer analysis indicates error
            - no output value found...
            User can call it to check if command was successful
            To be overridden """

    def get_buffer(self):
        self._get_output_stream()  # tigers processing
        self.logger.debug("Buffer of output obtained: " + self.__buffer)
        return self.__buffer

# Daophot regexps:
#     for 'Command:' like
r_command = re.compile(r'Command:')
#     for 'Picture size:   1250  1150' like
r_pic_size = re.compile(r'(?<=Picture size:\s\s\s)([0-9]+)\s+([0-9]+)')
#     for options listing like FWHM OF OBJECT =     5.00   THRESHOLD (in sigmas) =     3.50
r_opt = re.compile(r'\b(\w\w)[^=\n]*=\s*(\-?[0-9]+\.[0-9]*)')
#     for FInd:
r_find = re.compile(
    r'Sky mode and standard deviation = +(-?\d+\.\d*) +(-?\d+\.\d*)\n+ +'
    r'Clipped mean and median = +(-?\d+\.\d*)\s+(-?\d+\.\d*)\n +'
    r'Number of pixels used \(after clip\) = (\d*),?(\d+)\n +'
    r'Relative error = +(-?\d+\.\d*)(?:\n.*)+\s'
    r'(\d+) stars'
)
#    for PHotometry
r_phot = re.compile(r'Estimated magnitude limit \(Aperture 1\): +(-?\d+\.\d*) +\+- +(-?\d+\.\d*) +per star')
#    for PIck
r_pick = re.compile(r'(\d+) +suitable candidates')
#    for PSf
r_psf = re.compile(r'Chi    Parameters...\n>* +(-?\d+\.\d*) +(-?\d+\.\d*) +(-?\d+\.\d*)')
r_psf_errors = re.compile(r' (\d+) +(\d+.\d+) [ ?*]')
r_psf_failed_to_converge = re.compile(r'Failed to converge')

# Allstar regexp
r_alls_separator = re.compile(r'Input image name:')
r_alls_opt = r_opt
r_alls = re.compile(r'(\d+) +(\d+) +(\d+) +(\d+).*\n')

class DaophotCommandOutputProcessor(OutputBufferedProcessor):

    def _is_last_one(self, line, counter):
        return r_command.search(line) is not None

class DPOP_ATtach(DaophotCommandOutputProcessor):

    @property
    def picture_size(self):
        """returns tuple with (x,y) size of pic returned by 'attach' """
        buf = self.get_buffer()
        match = r_pic_size.search(buf)
        if match is None:
            raise Exception('daophot failed to attach image file. Output buffer:\n ' + buf)
        return int(match.group(1)), int(match.group(2))

    def raise_if_error(self, line):
        _ = self.picture_size


class DPOP_OPtion(DaophotCommandOutputProcessor):
    __options = None

    @property
    def options(self):
        """returns dictionary of options: XX: 'nnn.dd'
           keys are two letter option names
           values are strings"""
        if self.__options is None:
            buf = self.get_buffer()
            match = dict(r_opt.findall(buf))
            if 'RE' not in match:  # RE not found - sth wrong, found, suppose is OK
                raise Exception('daophot failed to present options. Output buffer:\n ' + buf)
            self.__options = match
        return self.__options

    def get_option(self, key):
        return float(self.options[key[:2].upper()])

    def raise_if_error(self, line):
        _ = self.options

class DpOp_FInd(DaophotCommandOutputProcessor):
    def __init__(self, prev_in_chain=None, starlist_file=None):
        self.__data = None
        self.__starlist = None
        self.starlist_file = starlist_file
        super(DpOp_FInd, self).__init__(prev_in_chain=prev_in_chain)

    @property
    def data(self):
        if self.__data is None:
            buf = self.get_buffer()
            match = r_find.search(buf)
            if match is None:
                raise Exception('daophot find output doesnt match regexp r_find:'
                                ' error (or regexp is wrong). Output buffer:\n ' + buf)
            self.__data = match.groups()
        return self.__data

    @property
    def found_starlist(self):
        if self.__starlist is None and self.starlist_file:
            self.__starlist = read_dao_file(self.starlist_file)
        return self.__starlist

    @property
    def sky(self):
        return float(self.data[0])

    @property
    def skydev(self):
        """Standart deviation of :var sky"""
        return float(self.data[1])

    @property
    def mean(self):
        return float(self.data[2])

    @property
    def median(self):
        return float(self.data[3])

    @property
    def pixels(self):
        t = self.data[4]
        if t is None or t == '':
            t = 0
        else:
            t = int(t) * 1000
        return int(self.data[5]) + t

    @property
    def err(self):
        return self.data[6]

    @property
    def stars(self):
        return self.data[7]

class DpOp_PHotometry(DaophotCommandOutputProcessor):

    def __init__(self, prev_in_chain=None, photometry_file=None):
        self.__data = None
        self.__starlist = None
        self.photometry_file = photometry_file
        super(DpOp_PHotometry, self).__init__(prev_in_chain=prev_in_chain)

    @property
    def data(self):
        if self.__data is None:
            buf = self.get_buffer()
            match = r_phot.search(buf)
            if match is None:
                raise Exception('daophot PH output doesnt match regexp r_phot:'
                                ' error (or regexp is wrong). Output buffer:\n ' + buf)
            self.__data = match.groups()
        return self.__data

    @property
    def mag_limit(self):
        return float(self.data[0])

    @property
    def mag_err(self):
        return float(self.data[1])

    @property
    def photometry_starlist(self):
        if self.__starlist is None and self.photometry_file:
            self.__starlist = read_dao_file(self.photometry_file)
        return self.__starlist


class DpOp_PIck(DaophotCommandOutputProcessor):

    def __init__(self, prev_in_chain=None, picked_stars_file=None):
        self.__stars = None
        self.__starlist = None
        self.picked_stars_file = picked_stars_file
        super(DpOp_PIck, self).__init__(prev_in_chain=prev_in_chain)

    @property
    def stars(self):
        if self.__stars is None:
            buf = self.get_buffer()
            match = r_pick.search(buf)
            if match is None:
                raise Exception('daophot PIck output doesnt match regexp r_pick:'
                                ' error (or regexp is wrong). Output buffer:\n ' + buf)
            self.__stars = int(match.group(1))
        return self.__stars

    @property
    def picked_starlist(self):
        if self.__starlist is None and self.picked_stars_file:
            self.__starlist = read_dao_file(self.picked_stars_file)
        return self.__starlist



class DpOp_PSf(DaophotCommandOutputProcessor):
    def __init__(self, prev_in_chain=None, psf_file=None, nei_file=None, err_file=None):
        self.__data = None
        self.__errors = None
        self.psf_file = psf_file
        self.nei_file = nei_file
        self.err_file = err_file
        super(DpOp_PSf, self).__init__(prev_in_chain=prev_in_chain)

    @property
    def converged(self):
        """False if daophot PSF routine does not produced result, e.g. 'Failed to converge'"""
        return self.__get_data() is not None

    @property
    def errors(self):
        if self.__errors is None:
            buf = self.get_buffer()  # TODO: implement 'saturated'
            self.__errors = [(int(star), float(err)) for star, err in r_psf_errors.findall(buf)]
        return self.__errors

    @property
    def data(self):
        d = self.__get_data()
        if d is None:
            raise Exception('daophot PSF output doesnt match regexp r_psf:'
                            ' PDF failed to converge?. Output buffer:\n ' + self.get_buffer())
        return d

    @property
    def chi(self):
        return float(self.data[0])

    @property
    def hwhm_xy(self):
        return float(self.data[1]), float(self.data[2])

    def __get_data(self):
        if self.__data is None:
            buf = self.get_buffer()
            match = r_psf.search(buf)
            if match is not None:
                self.__data = match.groups()
        return self.__data


class DpOp_SUbstar(OutputBufferedProcessor):
    def __init__(self, prev_in_chain=None, subtracted_image_file=None):
        self.subtracted_image_file = subtracted_image_file
        super(DpOp_SUbstar, self).__init__(prev_in_chain=prev_in_chain)



class DpOp_SOrt(OutputBufferedProcessor):
    pass


class AsOp_opt(OutputBufferedProcessor):
    __options = None

    def _is_last_one(self, line, counter):
        return r_alls_separator.search(line) is not None

    @property
    def options(self):
        """returns dictionary of options: XX: 'nnn.dd'
           keys are two letter option names
           values are strings"""
        if self.__options is None:
            buf = self.get_buffer()
            match = dict(r_opt.findall(buf))
            if 'WA' not in match:  # WA not found - sth wrong, found, suppose is OK
                raise Exception('allstar failed to present options. Output buffer:\n ' + buf)
            self.__options = match
        return self.__options

    def get_option(self, key):
        return float(self.options[key[:2].upper()])

    def raise_if_error(self, line):
        _ = self.options

class AsOp_result(OutputBufferedProcessor):
    def __init__(self, prev_in_chain=None, profile_photometry_file=None, subtracted_image_file=None):
        self.__stars = None
        self.__als_stars = None
        self.profile_photometry_file = profile_photometry_file
        self.subtracted_image_file = subtracted_image_file
        super(AsOp_result, self).__init__(prev_in_chain=prev_in_chain)

    def _is_last_one(self, line, counter):
        return False

    @property
    def als_stars(self):
        """returns StarList of stars with profile photometry results"""
        if self.__als_stars is None and self.profile_photometry_file:
            self.__als_stars = read_dao_file(self.profile_photometry_file)
        return self.__als_stars


    @property
    def stars_no(self):
        """returns tuple: (disappeared_stars, converged_stars)"""
        if self.__stars is None:
            buf = self.get_buffer()
            match = r_alls.findall(buf)
            if len(match) == 1:
                self.__stars = 0, 0  # error or sth
            else:
                res = match[-1][-2:]  # last occurrence, two last values
                self.__stars = int(res[0]), int(res[1])
        return self.__stars

