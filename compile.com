# Compile DFSYNTHE and satellite packages
ifort -o bin/xnfdf.exe src/xnfdf.for -save
ifort -o bin/dfsynthe.exe src/dfsynthe.for -save
ifort -o bin/separatedf.exe src/separatedf.for -save
ifort -o bin/dfsortp.exe src/dfsortp.for -save

# Compile KAPPAROS
ifort -o bin/kappa9.exe src/kappa9.for -save
ifort -o bin/kapreadts.exe src/kapreadts.for -save

# Repack DFSYNTHE lines
ifort -o bin/repackdi.exe src/repackdi.for
ln -s data/dfsynthe_files/diatomicsiwl.bin fort.11
bin/repackdi.exe
mv fort.12 data/dfsynthe_files/diatomicsdf.bin
rm fort.*
ifort -o bin/repacklow.exe src/repacklow.for
ln -s data/dfsynthe_files/lowlines.bin fort.11
bin/repacklow.exe
mv fort.12 data/dfsynthe_files/lowlinesdf.bin
rm fort.*
ifort -o bin/repackhi.exe src/repackhi.for
ln -s data/dfsynthe_files/highlines.bin fort.11
bin/repackhi.exe
mv fort.12 data/dfsynthe_files/highlinesdf.bin
rm fort.*
ifort -o bin/repacktio.exe src/repacktio.for
ln -s data/dfsynthe_files/tioschwenke.bin fort.11
bin/repacktio.exe
mv fort.12 data/dfsynthe_files/tiolinesdf.bin
rm fort.*
ifort -o bin/repackh2o.exe src/repackh2o.for
ln -s data/dfsynthe_files/h2ofastfix.bin fort.11
bin/repackh2o.exe
mv fort.12 data/dfsynthe_files/h2olinesdf.bin
rm fort.*
ifort -o bin/repacknlte.exe src/repacknlte.for
ln -s data/dfsynthe_files/nltelines.asc fort.11
bin/repacknlte.exe>repacknlte.out
mv fort.19 data/dfsynthe_files/nltelinesdf.bin
rm fort.*
rm repacknlte.out

# Compile ATLAS-9
gfortran -o bin/atlas9mem.exe src/atlas9mem.for -finit-local-zero -fno-automatic -w
