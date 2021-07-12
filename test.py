import os
import hashlib

python_path = os.path.dirname(os.path.realpath(__file__))

# Check these files for presence
no_hash = ['bin/atlas9mem.exe', 'bin/dfsortp.exe', 'bin/dfsynthe.exe', 'bin/kappa9.exe', 'bin/kapreadts.exe', 'bin/separatedf.exe', 'bin/xnfdf.exe']

# Check these files for MD5 hashes
hash = {
    'data/dfsynthe_files/continua.dat': '6caf77e029712caa1d074337c6c9b540',
    'data/dfsynthe_files/molecules.dat': '4afed2ab0b4fc9cc324ad28781c650d8',
    'data/dfsynthe_files/pfiron.dat': '75543d433e8ee2fd7cc89268d916ad69',
    'data/dfsynthe_files/diatomicsdf.bin': '3495207f6f2b52cfda67c1965350b559',
    'data/dfsynthe_files/h2olinesdf.bin': '4187af1837de526a5da981711641e739',
    'data/dfsynthe_files/highlinesdf.bin': '56552d9ce268897f8d0177c77425d654',
    'data/dfsynthe_files/lowlinesdf.bin': '349cfd5d90e52c28ad75a305301ecd59',
    'data/dfsynthe_files/nltelinesdf.bin': 'fd7fb0ef7c20e258e5f4ee6af7654298',
    'data/dfsynthe_files/tiolinesdf.bin': '0170def19d7ab7794263b2922bbf402a',
 
    'data/atlas_files/molecules.dat': 'a13345627ab05e39c8c366b23bfb4f53',
}


for file in no_hash:
    if not os.path.isfile(python_path + '/' + file):
        print('File {} is missing'.format(file))

for file in hash:
    if not os.path.isfile(python_path + '/' + file):
        print('File {} is missing'.format(file))
    elif hashlib.md5(open(file,'rb').read()).hexdigest() != hash[file]:
        print('File {} has unexpected hash: {}. Expected {}'.format(file, hashlib.md5(open(file,'rb').read()).hexdigest(), hash[file]))