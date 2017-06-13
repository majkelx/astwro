import re
from logging import *
import astwro.starlist
from astwro.starlist import read_dao_file

# TODO: check for failure on all providers (raise_if_error)

class AbstractOutputProvider(object):
    # Abstract class (interface) for chained stream processing
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
    # Base class for elements of stream processors chain
    #    also can be used as dummy processor in chain

    def __init__(self, prev_in_chain=None):
        self.__stream = None
        self._prev_in_chain = prev_in_chain # previous output provider
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

    @property
    def success(self):
        """True if command succeed and output is ready """
        try:
            self.raise_if_error()
        except:
            return False
        else:
            return True

    def raise_if_error(self):
        """ Should raise exception if not properly processed:
            - command did not run
            - buffer analysis indicates error
            - no output value found...
            User can call it to check if command was successful
            To be overridden """
        pass




class OutputLinesProcessor(OutputProvider):
    # Base for line-by-line processing

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
r_psf = re.compile(r'Chi {4}Parameters...\n>* +(-?\d+\.\d*) +(-?\d+\.\d*) +(-?\d+\.\d*)')
r_psf_errors = re.compile(r' (\d+) +(\d+.\d+) ([ ?*])')
r_psf_failed_to_converge = re.compile(r'Failed to converge')
#    for GRoup
r_grp = re.compile(r'(\d+) +(\d+)')
r_grp_summ = re.compile(r'(\d+) +stars in (\d+) +groups.')

# Allstar regexp
r_alls_separator = re.compile(r'Input image name:')
r_alls_opt = r_opt
r_alls = re.compile(r'(\d+) +(\d+) +(\d+) +(\d+).*\n')


#  DAOPHOT

class DaophotCommandOutputProcessor(OutputBufferedProcessor):

    def _is_last_one(self, line, counter):
        return r_command.search(line) is not None

class DPOP_ATtach(DaophotCommandOutputProcessor):
    """Results of `ATTACH` daophot command"""
    @property
    def picture_size(self):
        """tuple with (x,y) size of pic returned by 'ATTACH' """
        buf = self.get_buffer()
        match = r_pic_size.search(buf)
        if match is None:
            raise Exception('daophot failed to attach image file. Output buffer:\n ' + buf)
        return int(match.group(1)), int(match.group(2))

    def raise_if_error(self):
        _ = self.picture_size


class DPOP_OPtion(DaophotCommandOutputProcessor):
    """Results of `OPTION` daophot command, or initial daophot options"""
    __options = None

    @property
    def options(self):
        """Dictionary of options: XX: 'nnn.dd'
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
        """single option"""
        return float(self.options[key[:2].upper()])

    def raise_if_error(self):
        _ = self.options

class DpOp_FInd(DaophotCommandOutputProcessor):
    """Results of `FIND` daophot command"""
    def __init__(self, prev_in_chain=None, starlist_file=None):
        self.__data = None
        self.__starlist = None
        self.starlist_file = starlist_file  #: Patch to output file with found stars
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
        """StarList with found stars"""
        if self.__starlist is None and self.starlist_file:
            self.__starlist = read_dao_file(self.starlist_file)
        return self.__starlist

    @property
    def sky(self):
        """Sky estimation"""
        return float(self.data[0])

    @property
    def skydev(self):
        """Standart deviation of :var sky"""
        return float(self.data[1])

    @property
    def mean(self):
        """Mean of image"""
        return float(self.data[2])

    @property
    def median(self):
        """Median of image"""
        return float(self.data[3])

    @property
    def pixels(self):
        """Number of analyzed pixels"""
        t = self.data[4]
        if t is None or t == '':
            t = 0
        else:
            t = int(t) * 1000
        return int(self.data[5]) + t

    @property
    def err(self):
        """Error estimation"""
        return self.data[6]

    @property
    def stars(self):
        """Number of found stars"""
        return self.data[7]

class DpOp_PHotometry(DaophotCommandOutputProcessor):
    """Results of `PHOTOMETRY` daophot command"""
    def __init__(self, prev_in_chain=None, photometry_file=None):
        self.__data = None
        self.__starlist = None
        self.photometry_file = photometry_file  #: Patch to output file with aperture photometry
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
        """StarList with photometry

        :rtype: astwro.starlist.StarList 
        """
        if self.__starlist is None and self.photometry_file:
            self.__starlist = read_dao_file(self.photometry_file)
        return self.__starlist


class DpOp_PIck(DaophotCommandOutputProcessor):
    """Results of `PICK` daophot command"""
    def __init__(self, prev_in_chain=None, picked_stars_file=None):
        self.__stars = None
        self.__starlist = None
        self.picked_stars_file = picked_stars_file  #: Patch to output file with picked stars
        super(DpOp_PIck, self).__init__(prev_in_chain=prev_in_chain)

    @property
    def stars(self):
        """Number of picked stars"""
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
        """StarList with picked stars"""
        if self.__starlist is None and self.picked_stars_file:
            self.__starlist = read_dao_file(self.picked_stars_file)
        return self.__starlist



class DpOp_PSf(DaophotCommandOutputProcessor):
    """Results of `PSF` daophot command"""
    def __init__(self, prev_in_chain=None, psf_file=None, nei_file=None, err_file=None):
        self.__data = None
        self.__errors = None
        self.__neilist = None
        self.psf_file = psf_file  #: Patch to output file with PSF function
        self.nei_file = nei_file  #: Patch to output neighbours file 
        self.err_file = err_file  #: Patch to output errors file
        super(DpOp_PSf, self).__init__(prev_in_chain=prev_in_chain)

    @property
    def nei_starlist(self):
        """StarList with neighbours stars"""
        if self.__neilist is None and self.nei_file:
            self.__neilist = read_dao_file(self.nei_file)
        return self.__neilist

    @property
    def converged(self):
        """False if daophot PSF routine does not produced result, e.g. 'Failed to converge'"""
        return self.__get_data() is not None

    @property
    def errors(self):
        """StarList (pandas.DataFrame) of PSF stars with errors and flags ('?', '*' or ' ')
        
        This information is identical to i.err file, but obtained directly from daophot output"""
        if self.__errors is None:
            buf = self.get_buffer()
            lst = [(int(star), float(err), flag) for star, err, flag in r_psf_errors.findall(buf)]
            sl = astwro.starlist.StarList(lst)
            sl.columns = ['id','psf_err','flag']
            sl.index = sl.id
            self.__errors = sl
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
        """Chi error estimation"""
        return float(self.data[0])

    @property
    def hwhm_xy(self):
        """tuple (x,y) of halfwidth's of PSF function"""
        return float(self.data[1]), float(self.data[2])

    def __get_data(self):
        if self.__data is None:
            buf = self.get_buffer()
            match = r_psf.search(buf)
            if match is not None:
                self.__data = match.groups()
        return self.__data

    def raise_if_error(self):
        if not self.converged:
            raise Exception('PSF not converged')


class DpOp_SUbstar(DaophotCommandOutputProcessor):
    """Results of `SUBSTAR` daophot command"""
    def __init__(self, prev_in_chain=None, subtracted_image_file=None):
        self.subtracted_image_file = subtracted_image_file  #: Patch to output fits image
        super(DpOp_SUbstar, self).__init__(prev_in_chain=prev_in_chain)

class DpOp_GRoup(DaophotCommandOutputProcessor):
    """Results of `GROUP` daophot command"""
    def __init__(self, prev_in_chain=None, groups_file=None):
        self.__data = None
        self.__grouphist = None
        self.groups_file = groups_file  #: Patch to output file with groups
        super(DpOp_GRoup, self).__init__(prev_in_chain=prev_in_chain)

    @property
    def groups_histogram(self):
        """List of tuples: (size_of_group, number_of_groups)"""
        if self.__grouphist is None:
            buf = self.get_buffer()
            self.__grouphist = [(int(size), int(count)) for size, count in r_grp.findall(buf)]
        return self.__grouphist

    @property
    def data(self):
        if self.__data is None:
            buf = self.get_buffer()
            match = r_grp_summ.search(buf)
            if match is not None:
                self.__data = match.groups()
        return self.__data

    @property
    def stars(self):
        """Number of grouped stars reported by daophot `GROUP` command"""
        return float(self.data[0])

    @property
    def groups(self):
        """Number of groups"""
        return float(self.data[1])


class DpOp_NEda(DaophotCommandOutputProcessor):
    def __init__(self, prev_in_chain=None, neda_file=None):
        self.neda_file = neda_file #: Patch to output file with NEDA photometry
        self.__nedalist = None
        super(DpOp_NEda, self).__init__(prev_in_chain=prev_in_chain)

    @property
    def neda_starlist(self):
        """stars list with neda photometry"""
        if self.__nedalist is None and self.neda_file:
            self.__nedalist = read_dao_file(self.neda_file)
        return self.__nedalist



class DpOp_SOrt(DaophotCommandOutputProcessor):
    pass


#  ALLSTARS

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

    def raise_if_error(self):
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
        # type: () -> {astwro.starlist.StarList}
        """StarList of stars with profile photometry results        """
        if self.__als_stars is None and self.profile_photometry_file:
            self.__als_stars = read_dao_file(self.profile_photometry_file)
        return self.__als_stars


    @property
    def stars_no(self):
        # type: () -> (int,int)
        """tuple: (converged_stars, disappeared_stars)"""
        if self.__stars is None:
            buf = self.get_buffer()
            match = r_alls.findall(buf)
            if len(match) < 1:
                self.__stars = 0, 0  # error or sth
            else:
                res = match[-1][-2:]  # last occurrence, two last values
                self.__stars = int(res[1]), int(res[0])
        return self.__stars

    def raise_if_error(self):
        if not self.stars_no[0] > 0:
            raise Exception('allstar: No stars')
