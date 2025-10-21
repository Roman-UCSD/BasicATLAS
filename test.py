import os
import hashlib

python_path = os.path.dirname(os.path.realpath(__file__))


# Check these files for presence
no_hash = ['bin/atlas9mem.exe', 'bin/dfsortp.exe', 'bin/dfsynthe.exe', 'bin/kappa9.exe', 'bin/kapreadts.exe', 'bin/separatedf.exe', 'bin/xnfdf.exe', 'bin/rgfalllinesnew.exe', 'bin/rmolecasc.exe',
           'bin/spectrv.exe', 'bin/synthe.exe', 'bin/xnfpelsyn.exe', 'bin/converfsynnmtoa.exe', 'bin/rh2ofast.exe', 'bin/rpredict.exe', 'bin/synbeg.exe']

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

    'data/synthe_files/c2ax.asc': '5545687ba484ec738025f1274e25f44c',
    'data/synthe_files/c2ba.asc': '2332d41064cc9d8463db09169da4025a',
    'data/synthe_files/c2dabrookek.asc': '282ddbb87a59818cc7dcf488884c59a7',
    'data/synthe_files/c2ea.asc': 'a77c438e5bfce97678b74bf17108aeef',
    'data/synthe_files/cnaxbrookek.asc': 'd8c9671b0f628d7491644c2aaecb9812',
    'data/synthe_files/cnbxbrookek.asc': '3e21095f49b9f29f1d30a725d25abc3d',
    'data/synthe_files/cnxx12brooke.asc': 'd7ac0759f7a129751ebab10ff551f20e',
    'data/synthe_files/coax.asc': '92c558cc9b23ee96dcc0e0179730faeb',
    'data/synthe_files/continua.dat': '9e317b10bd777bf997e027543aed00ac',
    'data/synthe_files/coxx.asc': '778d9fe8001ba91211ac1209702b236b',
    'data/synthe_files/gfall08oct17.dat': '32e655430d5a7ce36f556bd545167971',
    'data/synthe_files/h2.asc': '527b750951c035b5978dba1b5de38215',
    'data/dfsynthe_files/h2ofastfix.bin': 'd62e69d234182e6281f249c0ae555ce4',
    'data/synthe_files/h2xx.asc': 'ae63f1d809523ac0c92bde48280dd2ba',
    'data/synthe_files/hdxx.asc': '8a741ea1a118d7154165fded06a1d9c0',
    'data/synthe_files/he1tables.dat': '3e1aa7dd7c0f420d12f3d5d88c342342',
    'data/synthe_files/molecules.dat': 'b9dbc40dcd9c56c9f534842888488760',
    'data/synthe_files/nh.asc': 'f6888c332a313ccf2c720e2371c26836',
    'data/synthe_files/ohupdate.asc': '846cb1da995c3a39d86340d57475edcc',
    'data/synthe_files/sihax.asc': 'efc2f067a4b3102fbbec6a9d526f350b',
    'data/synthe_files/sioax.asc': '7e8de7d2eaa68c78a164d89556590119',
    'data/synthe_files/sioex.asc': '8a53e55a001cba30896a37bc07c0869d',
    'data/synthe_files/sioxx.asc': '4671eb6faecd1b320847458c54b9647c',
    'data/synthe_files/tiototo.asc': 'dac3f30e3928842e331e6540655be3e6', # This is for the reduced list with all log(gf) < -2.5 lines removed
}

# Check these files for MD5 hashes only if present
hash_optional = {
    'restarts/light.h5': '3b70fbbbc1daef3e82f3a97c81c6e4e5',
}


for file in no_hash:
    if not os.path.isfile(python_path + '/' + file):
        print('File {} is missing'.format(file))

for file in hash:
    if not os.path.isfile(python_path + '/' + file):
        print('File {} is missing'.format(file))
    elif hashlib.md5(open(file,'rb').read()).hexdigest() != hash[file]:
        print('File {} has unexpected hash: {}. Expected {}'.format(file, hashlib.md5(open(file,'rb').read()).hexdigest(), hash[file]))

for file in hash_optional:
    if os.path.isfile(python_path + '/' + file):
        if hashlib.md5(open(file,'rb').read()).hexdigest() != hash_optional[file]:
            print('File {} has unexpected hash: {}. Expected {}'.format(file, hashlib.md5(open(file,'rb').read()).hexdigest(), hash_optional[file]))
