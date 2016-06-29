import async

class IncrementalStream(object):
    """Stream, which does not block until EOF"""
    fd = None
    def __init__(self, stream=None, fd = None):
        """Provide stream or fd parameter"""
        if stream is not None:
            self.fd = stream.fileno()
        elif fd is not None:
            self.fd = fd

