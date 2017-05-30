import os

def get_stream(file, mode):
    to_close = []
    if isinstance(file, str):
        file = os.path.expanduser(file)
        f = open(file, mode)
        to_close.append(f)
    else:
        f = file
    return f, to_close


def close_files(to_close):
    for f in to_close:
        f.close()
