import os
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

    def __init__(self, stream=None):
        self.stream = stream

    def get_output_stream(self):
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

    def process_line(self, line):
        """ processes line by line output
            return True if it's last line.
            To be overridden """
        return True

    def consume(self):
        rd = self.stream.read()
        rd = os.read(self.stream.fileno(), 1000)
        print(rd)
        rd = os.read(self.stream.fileno(), 1000)
        print(rd)
        for line in self.stream.xreadlines():
            debug("Output line: " + line)
            last_one = self.process_line(line)
            if last_one:
                debug("Was last line")
                return


class OutputBufferedProcessor(OutputLinesProcessor):
    buffer = ''

    def process_line(self, line):
        """ processes line by line output
            return True if it's last line.
            If overridden, this base impl should be called """
        self.buffer += line
        return self.is_last_one(line)

    def is_last_one(self, line):
        """ return True if it's last line.
            To be overridden """

    def get_buffer(self):
        self.get_output_stream()  # tigers processing
        debug("Buffer of output obtained: "+self.buffer)
        return self.buffer

# Daophot regexps:
# regexp for 'Command:' like
r_command = re.compile('Command:')
# regexp for 'Picture size:   1250  1150' like
r_pic_size = re.compile('(?<=Picture size:\s\s\s)([0-9]+)\s+([0-9]+)')


class DaophotCommandOutputProcessor(OutputBufferedProcessor):

    def is_last_one(self, line):
        return r_command.search(line) is not None


class DaophotAttachOP(DaophotCommandOutputProcessor):

    def get_picture_size(self):
        """returns tuple with (x,y) size of pic returned by 'attach' """
        buf = self.get_buffer()
        match = r_pic_size.search(buf)
        if match is not None:
            return int(match.group(1)), int(match.group(2))
