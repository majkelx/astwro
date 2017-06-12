from __future__ import print_function
import astwro.starlist as sl
import sys

s = sl.read_dao_file('i.lst')
print (s)

sl.write_dao_file(s, sys.stdout, sl.DAO.LST_FILE)