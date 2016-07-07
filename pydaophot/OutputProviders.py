import re
from logging import *


class AbstractOutputProvider(object):
    """ Abstract class (interface) for chained stream processing """
    def get_output_stream(self):
        """To be overridden"""
        pass


class StreamKeeper(AbstractOutputProvider):
    """First in the chain, just keeps stream handler"""
    stream = None
    runner = None

    def __init__(self, runner=None, stream=None):
        self.stream = stream
        self.runner = runner

    def get_output_stream(self):
        self.runner.wait_for_results()
        if self.stream is None:
            raise Exception('No output stream available, call run() before collecting results.')
        return self.stream


class OutputProvider(AbstractOutputProvider):
    """ Base class for elements of stream processors chain
        also can be used as dummy processor in chain"""

    # previous output provider
    prev_in_chain = None
    stream = None

    def __init__(self, prev_in_chain=None):
        self.prev_in_chain = prev_in_chain

    def consume(self):
        """ to be overridden """
        pass

    def get_output_stream(self):
        if self.stream is None:
            self.stream = self.prev_in_chain.get_output_stream()
            self.consume()
        return self.stream


class OutputLinesProcessor(OutputProvider):
    """ Base for line-by-line processing"""

    def process_line(self, line, counter):
        """ processes line by line output
            return True if it's last line.
            To be overridden """
        return True

    def consume(self):
        counter = 0
        for line in self.stream:
            counter += 1
            debug("Output line %3d: %s", counter, line)
            last_one = self.process_line(line, counter)
            if last_one:
                debug("Was last line")
                return


class OutputBufferedProcessor(OutputLinesProcessor):
    buffer = ''

    def process_line(self, line, counter):
        """ processes line-by-line output
            return True if it's last line.
            If overridden, this base impl should be called """
        self.buffer += line
        return self.is_last_one(line, counter)

    def is_last_one(self, line, counter):
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
        self.get_output_stream()  # tigers processing
        debug("Buffer of output obtained: "+self.buffer)
        return self.buffer

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



class DaophotCommandOutputProcessor(OutputBufferedProcessor):

    def is_last_one(self, line, counter):
        return r_command.search(line) is not None

class DPOP_ATtach(DaophotCommandOutputProcessor):

    def get_picture_size(self):
        """returns tuple with (x,y) size of pic returned by 'attach' """
        buf = self.get_buffer()
        match = r_pic_size.search(buf)
        if match is None:
            raise Exception('daophot failed to attach image file. Output buffer:\n ' + buf)
        return int(match.group(1)), int(match.group(2))

    def raise_if_error(self, line):
        self.get_picture_size()


class DPOP_OPtion(DaophotCommandOutputProcessor):
    options = None
    def get_options(self):
        """returns dictionary of options: XX: 'nnn.dd'
           keys are two letter option names
           values are strings"""
        if self.options is None:
            buf = self.get_buffer()
            match = dict(r_opt.findall(buf))
            if 'RE' not in match:  # RE not found - sth wrong, found, suppose is OK
                raise Exception('daophot failed to present options. Output buffer:\n ' + buf)
            self.options = match
        return self.options

    def get_option(self, key):
        return float(self.get_options()[key[:2].upper()])

    def raise_if_error(self, line):
        self.get_options()

class DpOp_FInd(DaophotCommandOutputProcessor):
    data = None
    def get_data(self):
        if self.data is None:
            buf = self.get_buffer()
            match = r_find.search(buf)
            if match is None:
                raise Exception('daophot find output doesnt match regexp r_find:'
                                ' error (or regexp is wrong). Output buffer:\n ' + buf)
            self.data = match.groups()
        return self.data

    def get_sky(self):
        return float(self.get_data()[0])

    def get_stddev(self):
        return float(self.get_data()[1])

    def get_mean(self):
        return float(self.get_data()[2])

    def get_median(self):
        return float(self.get_data()[3])

    def get_pixels(self):
        t = self.get_data()[4]
        if t is None or t == '':
            t = 0
        else:
            t = int(t) * 1000
        return int(self.get_data()[5]) + t

    def get_err(self):
        return self.get_data()[6]

    def get_stars(self):
        return self.get_data()[7]

class DpOp_PHotometry(DaophotCommandOutputProcessor):
    data = None
    def get_data(self):
        if self.data is None:
            buf = self.get_buffer()
            match = r_phot.search(buf)
            if match is None:
                raise Exception('daophot PH output doesnt match regexp r_phot:'
                                ' error (or regexp is wrong). Output buffer:\n ' + buf)
            self.data = match.groups()
        return self.data

    def get_mag_limit(self):
        return float(self.get_data()[0])

    def get_mag_err(self):
        return float(self.get_data()[1])

class DpOp_PIck(DaophotCommandOutputProcessor):
    stars = None
    def get_stars(self):
        if self.stars is None:
            buf = self.get_buffer()
            match = r_pick.search(buf)
            if match is None:
                raise Exception('daophot PIck output doesnt match regexp r_pick:'
                                ' error (or regexp is wrong). Output buffer:\n ' + buf)
            self.stars = int(match.group(1))
        return self.stars


class DpOp_PSf(DaophotCommandOutputProcessor):
    data = None
    errors = None

    def get_errors(self):
        if self.errors is None:
            buf = self.get_buffer()
            self.errors = [(int(star), float(err)) for star, err in r_psf_errors.findall(buf)]
        return self.errors


    def get_data(self):
        if self.data is None:
            buf = self.get_buffer()
            match = r_psf.search(buf)
            if match is None:
                raise Exception('daophot PSF output doesnt match regexp r_psf:'
                                ' error (or regexp is wrong). Output buffer:\n ' + buf)
            self.data = match.groups()
        return self.data

    def get_chi(self):
        return float(self.get_data()[0])

    def get_hwhm_xy(self):
        return float(self.get_data()[1]), float(self.get_data()[2])


