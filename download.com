# Check that the required commands are available
required=("gzip" "wget")
for c in "${required[@]}"; do
    if ! command -v "$c" &>/dev/null; then
        echo "ERROR: Command ${c} not available"
        return 1
    fi
done

# Prompt the user to download the full grid of restart models
FILENAME="restarts/light.h5"
if [[ ! -f "$FILENAME" ]]; then
    read -p "BasicATLAS is shipped with a reduced grid of restart files. Downloading the full grid is recommended. Would you like to do that? (y/n)" answer
    if [[ ! "$answer" =~ ^[Nn]$ ]]; then
        echo "The full grid (light.h5) is available on Google Drive: https://drive.google.com/file/d/1xBhLEdUBZTjtHHg110FVH6G-rYFaPHTk/view?usp=sharing"
        echo "Download the grid and save it in restarts/light.h5, then re-run this script"
        return 1
    fi
fi

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


wget -nc -nv -O data/synthe_files/nh.asc http://kurucz.harvard.edu/linelists/linesmol/nh.asc
wget -nc -nv -O data/synthe_files/ohupdate.asc http://kurucz.harvard.edu/molecules/oh/ohupdate.asc
wget -nc -nv -O data/synthe_files/sihax.asc http://kurucz.harvard.edu/molecules/sih/sihax.asc
wget -nc -nv -O data/synthe_files/h2.asc http://kurucz.harvard.edu/linelists/linesmol/h2.asc
wget -nc -nv -O data/synthe_files/h2xx.asc http://kurucz.harvard.edu/molecules/h2/h2xx.asc
wget -nc -nv -O data/synthe_files/hdxx.asc http://kurucz.harvard.edu/molecules/h2/hdxx.asc
wget -nc -nv -O data/synthe_files/c2ax.asc http://kurucz.harvard.edu/linelists/linesmol/c2ax.asc
wget -nc -nv -O data/synthe_files/c2ba.asc http://kurucz.harvard.edu/linelists/linesmol/c2ba.asc
wget -nc -nv -O data/synthe_files/c2dabrookek.asc http://kurucz.harvard.edu/molecules/c2/c2dabrookek.asc
wget -nc -nv -O data/synthe_files/c2ea.asc http://kurucz.harvard.edu/linelists/linesmol/c2ea.asc
wget -nc -nv -O data/synthe_files/cnaxbrookek.asc http://kurucz.harvard.edu/molecules/cn/cnaxbrookek.asc
wget -nc -nv -O data/synthe_files/cnbxbrookek.asc http://kurucz.harvard.edu/molecules/cn/cnbxbrookek.asc
wget -nc -nv -O data/synthe_files/cnxx12brooke.asc http://kurucz.harvard.edu/molecules/cn/cnxx12brooke.asc
wget -nc -nv -O data/synthe_files/coax.asc http://kurucz.harvard.edu/molecules/co/coax.asc
wget -nc -nv -O data/synthe_files/coxx.asc http://kurucz.harvard.edu/linelists/linesmol/coxx.asc
wget -nc -nv -O data/synthe_files/sioax.asc http://kurucz.harvard.edu/linelists/linesmol/sioax.asc
wget -nc -nv -O data/synthe_files/sioex.asc http://kurucz.harvard.edu/linelists/linesmol/sioex.asc
wget -nc -nv -O data/synthe_files/sioxx.asc http://kurucz.harvard.edu/linelists/linesmol/sioxx.asc
wget -nc -nv -O data/synthe_files/tiototo.asc http://kurucz.harvard.edu/molecules/tio/tiototo.asc

wget -nc -nv -O data/synthe_files/gfall08oct17.dat http://kurucz.harvard.edu/linelists/gfnew/gfall08oct17.dat

wget -nc -nv -O data/synthe_files/molecules.dat http://kurucz.harvard.edu/programs/synthe/molecules.dat
wget -nc -nv -O data/synthe_files/continua.dat http://kurucz.harvard.edu/programs/synthe/continua.dat
wget -nc -nv -O data/synthe_files/he1tables.dat https://wwwuser.oats.inaf.it/castelli/sources/synthe/he1tables.dat


wget -nc -nv -O src/xnfpelsyn.for http://wwwuser.oats.inaf.it/castelli/sources/syntheg/xnfpelsyn.for
wget -nc -nv -O src/atlas7v.for http://wwwuser.oats.inaf.it/castelli/sources/syntheg/atlas7v.for
wget -nc -nv -O src/synbeg.for http://wwwuser.oats.inaf.it/castelli/sources/syntheg/synbeg.for
wget -nc -nv -O src/rgfalllinesnew.for http://wwwuser.oats.inaf.it/castelli/sources/syntheg/rgfalllinesnew.for
wget -nc -nv -O src/rpredict.for http://wwwuser.oats.inaf.it/castelli/sources/syntheg/rpredict.for
wget -nc -nv -O src/rmolecasc.for http://wwwuser.oats.inaf.it/castelli/sources/syntheg/rmolecasc.for
wget -nc -nv -O src/rh2ofast.for http://wwwuser.oats.inaf.it/castelli/sources/syntheg/rh2ofast.for
wget -nc -nv -O src/synthe.for http://wwwuser.oats.inaf.it/castelli/sources/syntheg/synthe.for
wget -nc -nv -O src/spectrv.for http://wwwuser.oats.inaf.it/castelli/sources/syntheg/spectrv.for


cp data/linelists/*.gz data/synthe_files/
gzip -d data/synthe_files/*.gz
