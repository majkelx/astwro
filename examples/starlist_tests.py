from __future__ import print_function
from astwro.pydaophot import daophot
import astwro.starlist as sl
import sys

s = sl.starlist_from_file('i.lst')
print (s)

sl.write_file(s, sys.stdout, sl.DAO.LST_FILE)