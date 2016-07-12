import re
from logging import *


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
        self.stream = stream
        self.runner = runner

    def _get_output_stream(self):
        self.runner.wait_for_results()
        if self.stream is None:
            raise Exception('No output stream available, call run() before collecting results.')
        return self.stream


class OutputProvider(AbstractOutputProvider):
    """ Base class for elements of stream processors chain
        also can be used as dummy processor in chain"""

    # previous output provider
    _prev_in_chain = None
    __stream = None

    def __init__(self, prev_in_chain=None):
        self._prev_in_chain = prev_in_chain

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
            debug("Output line %3d: %s", counter, line)
            last_one = self._process_line(line, counter)
            if last_one:
                debug("Was last line")
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
        debug("Buffer of output obtained: " + self.__buffer)
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

# Allstar regexp
r_alls_separator = re.compile(r'Input image name:')
r_alls_opt = r_opt
r_alls = re.compile(r'(\d+) +(\d+) +(\d+) +(\d+) *\n')

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
    __data = None

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
    def sky(self):
        return float(self.data[0])

    @property
    def stddev(self):
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
        return int(self.data()[5]) + t

    @property
    def err(self):
        return self.data[6]

    @property
    def stars(self):
        return self.data[7]

class DpOp_PHotometry(DaophotCommandOutputProcessor):
    __data = None

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

class DpOp_PIck(DaophotCommandOutputProcessor):
    __stars = None

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


class DpOp_PSf(DaophotCommandOutputProcessor):
    __data = None
    __errors = None

    @property
    def errors(self):
        if self.__errors is None:
            buf = self.get_buffer()
            self.__errors = [(int(star), float(err)) for star, err in r_psf_errors.findall(buf)]
        return self.__errors

    @property
    def data(self):
        if self.__data is None:
            buf = self.get_buffer()
            match = r_psf.search(buf)
            if match is None:
                raise Exception('daophot PSF output doesnt match regexp r_psf:'
                                ' error (or regexp is wrong). Output buffer:\n ' + buf)
            self.__data = match.groups()
        return self.__data

    @property
    def chi(self):
        return float(self.data[0])

    @property
    def hwhm_xy(self):
        return float(self.data[1]), float(self.data[2])

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
    __stars = None
    def _is_last_one(self, line, counter):
        return False

    @property
    def stars_no(self):
        """returns tuple: (disappeared_stars, converged_stars)"""
        if self.__stars is None:
            buf = self.get_buffer()
            match = r_alls.search(buf)
            self.__stars = match.group(3), match.group(4)
        return self.__stars