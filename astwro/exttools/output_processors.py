# coding=utf-8
from __future__ import absolute_import, division, print_function
from logging import *

__metaclass__ = type




class AbstractOutputProvider(object):
    # Abstract class (interface) for chained stream processing
    def get_output_stream(self):
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

    def get_output_stream(self):
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

    def get_output_stream(self):
        if self.__stream is None:
            self.__stream = self._prev_in_chain.get_output_stream()
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
        self.get_output_stream()  # tigers processing
        self.logger.debug("Buffer of output obtained: " + self.__buffer)
        return self.__buffer

