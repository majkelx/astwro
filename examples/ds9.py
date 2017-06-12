from astwro.starlist.daofiles import read_dao_file, write_dao_file
from astwro.starlist.ds9 import write_ds9_regions, read_ds9_regions
from astwro.starlist import StarList

COO = 'i.coo'
LST = 'i.lst'
REG = 'i.lst.reg'

# s0 = StarList.new()

coo = read_dao_file(COO)
psf = read_dao_file(LST)
write_ds9_regions(coo, REG, indexes=[psf.index], colors=['red'])
s2 = read_ds9_regions(REG)
print (s2)
print (s2.DAO_hdr)
