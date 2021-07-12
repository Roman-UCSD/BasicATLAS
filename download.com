wget -nc -nv -O data/dfsynthe_files/continua.dat  http://kurucz.harvard.edu/programs/newdf/continua.dat
wget -nc -nv -O data/dfsynthe_files/molecules.dat http://wwwuser.oats.inaf.it/castelli/sources/dfsynthe/molecules.dat
wget -nc -nv -O data/dfsynthe_files/pfiron.dat http://kurucz.harvard.edu/atoms/pf/pfiron.dat


wget -nc -nv -O src/xnfdf.for http://wwwuser.oats.inaf.it/castelli/sources/dfsynthe/xnfdf.for
wget -nc -nv -O src/dfsynthe.for http://wwwuser.oats.inaf.it/castelli/sources/dfsynthe/dfsynthe.for
wget -nc -nv -O src/dfsortp.for http://wwwuser.oats.inaf.it/castelli/sources/dfsynthe/dfsortp.for
wget -nc -nv -O src/separatedf.for http://wwwuser.oats.inaf.it/castelli/sources/dfsynthe/separatedf.for


wget -nc -nv -O data/dfsynthe_files/diatomicsiwl.bin http://wwwuser.oats.inaf.it/castelli/linelists/diatomicsiwl.bin
wget -nc -nv -O src/repackdi.for http://wwwuser.oats.inaf.it/castelli/sources/dfsynthe/repackdi.for
wget -nc -nv -O data/dfsynthe_files/lowlines.bin http://kurucz.harvard.edu/linelists/linescd/fclowlines.bin
wget -nc -nv -O src/repacklow.for http://wwwuser.oats.inaf.it/castelli/sources/dfsynthe/repacklow.for
wget -nc -nv -O data/dfsynthe_files/highlines.bin http://kurucz.harvard.edu/linelists/linescd/fchighlines.bin
wget -nc -nv -O src/repackhi.for http://wwwuser.oats.inaf.it/castelli/sources/dfsynthe/repackhi.for
wget -nc -nv -O data/dfsynthe_files/tioschwenke.bin http://kurucz.harvard.edu/molecules/tio/tioschwenke.bin
wget -nc -nv -O src/repacktio.for http://wwwuser.oats.inaf.it/castelli/sources/dfsynthe/repacktio.for
wget -nc -nv -O data/dfsynthe_files/h2ofastfix.bin http://kurucz.harvard.edu/molecules/h2o/h2ofastfix.bin
wget -nc -nv -O src/repackh2o.for http://wwwuser.oats.inaf.it/castelli/sources/dfsynthe/repackh2o.for
wget -nc -nv -O data/dfsynthe_files/nltelines.asc http://kurucz.harvard.edu/linelists/linescd/nltelines.asc
wget -nc -nv -O src/repacknlte.for http://wwwuser.oats.inaf.it/castelli/sources/dfsynthe/repacknlte.for


wget -nc -nv -O src/kappa9.for https://wwwuser.oats.inaf.it/castelli/sources/kappa9/kappa9.for
wget -nc -nv -O src/kapreadts.for https://wwwuser.oats.inaf.it/castelli/sources/kappa9/kapreadts.for


wget -nc -nv -O data/atlas_files/molecules.dat https://wwwuser.oats.inaf.it/castelli/sources/atlas9/molecules.dat


wget -nc -nv -O src/atlas9mem.for https://wwwuser.oats.inaf.it/castelli/sources/atlas9g/atlas9mem.for
