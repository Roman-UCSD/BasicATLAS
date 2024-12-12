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

# Patch ATLAS-9 to give additional output and report on the success of chemical equilibrium solver
patch -o src/atlas9mem.patched.for src/atlas9mem.for <<EOF
@@ -658,12 +658,12 @@ C      IF(IFPRNT(ITER).EQ.1)GO TO 540
       IF(IFCORR.EQ.0)FLXRAD(J)=FLUX-FLXCNV(J)
   539 FLXCNVratio(J)=FLXCNV(J)/(FLXCNV(J)+FLXRAD(J))
       WRITE(6,542)(J,RHOX(J),T(J),P(J),XNE(J),RHO(J),ABROSS(J),
-     1HEIGHT(J),TAUROS(J),FLXCNVratio(J),ACCRAD(J),FLXERR(J),FLXDRV(J),
+     1HEIGHT(J),TAUROS(J),FLXCNV(J),PRADK(J),FLXERR(J),FLXDRV(J),
      2J=1,NRHOX)
   542 FORMAT(132H0                                    ELECTRON          +
-     1   ROSSELAND    HEIGHT   ROSSELAND   FRACTION  RADIATIVE        PE
+     1   ROSSELAND    HEIGHT   ROSSELAND             RADIATION        PE
      2R CENT FLUX /132H        RHOX      TEMP    PRESSURE    NUMBER    D
-     3ENSITY      MEAN       (KM)      DEPTH    CONV FLUX  ACCELERATION +
+     3ENSITY      MEAN       (KM)      DEPTH    CONV FLUX  PRESSURE     +
      4   ERROR    DERIV/(I4,1PE10.3,0PF9.1,1P8E11.3,0PF12.3,F9.3))
   550 IF(IFPNCH(ITER).EQ.0)RETURN
 C
@@ -680,9 +680,9 @@ C    1TRBPOW,TRBSND,TRBCON,XSCALE,(IZ,ABUND(IZ),IZ=1,2)
      24F6.2/16HABUNDANCE SCALE ,F9.5,17H ABUNDANCE CHANGE,2(I2,F8.5)/
      3(17H ABUNDANCE CHANGE,6(I3,F7.2)))
       WRITE(7,554)NRHOX,(RHOX(J),T(J),P(J),XNE(J),ABROSS(J),ACCRAD(J),
-     1VTURB(J),FLXCNV(J),VCONV(J),VELSND(J),J=1,NRHOX)
+     1VTURB(J),FLXRAD(J),VCONV(J),VELSND(J),J=1,NRHOX)
   554 FORMAT('READ DECK6',I3,' RHOX,T,P,XNE,ABROSS,ACCRAD,VTURB,
-     1 FLXCNV,VCONV,VELSND'/(1PE15.8,0PF9.1,1P8E10.3))
+     1 FLXRAD,VCONV,VELSND'/(1PE15.8,0PF9.1,1P8E10.3))
       WRITE(7,555)PRADK0
   555 FORMAT(5HPRADK,1PE11.4)
       IF(NLTEON.EQ.0)GO TO 560
@@ -13727,7 +13727,9 @@ C     2 106.206*T10000**5-30.8720*T10000**6-1.5*TLOG(J))
 C
 C     SET UP 1ST ORDER EQUATIONS FOR THE CHANGE IN NUMBER DENSITY OF
 C        EACH ELEMENT.
-   50 DO 60 KL=1,NEQNEQ
+      NCHEMITER=0
+   50 NCHEMITER=NCHEMITER+1
+      DO 60 KL=1,NEQNEQ
    60 DEQ(KL)=0.
       EQ(1)=-XNTOT
       K1=1
@@ -13817,7 +13819,13 @@ cc      XN(K)=XNEQ
       GO TO 105
 C 102 XN(K)=XN100
   105 EQOLD(K)=EQ(K)
+      IF(NCHEMITER.LT.20000)THEN
       IF(IFERR.EQ.1)GO TO 50
+      WRITE(*,*) 'CHEMSUCCESS'
+      ENDIF
+      IF(NCHEMITER.GE.20000)THEN
+      WRITE(*,*) 'CHEMFAIL'
+      ENDIF
 C
       DO 107 K=1,NEQUA
   107 XNZ(J,K)=XN(K)
EOF

# Compile patched ATLAS-9
gfortran -o bin/atlas9mem.exe src/atlas9mem.patched.for -finit-local-zero -fno-automatic -w -std=legacy

# Patch RMOLECASC to allow alternative C12/C13 ratios
patch -o src/rmolecasc.patched.for src/rmolecasc.for << EOF
@@ -23,6 +23,7 @@ c      EQUIVALENCE (LINDAT8(1),WL),(LINDAT4(1),NELION)
       character*10 LABEL,LABELP,OTHER1,OTHER2
       REAL*8 RESOLU,RATIO,RATIOLG,SIGMA2,WLBEG,WLEND
       REAL*8 WL,E,EP,WLVAC,CENTER,CONCEN
+      REAL*8 C12,C13
 c      REAL*8 LABEL,LABELP,OTHER1,OTHER2
 c      CHARACTER*8 CLABELP
       CHARACTER*10 CLABELP
@@ -42,6 +43,17 @@ c      REAL*8 ISOLAB(60)
      3            '31','32','33','34','35','36','37','38','39','40',
      4            '41','42','43','44','45','46','47','48','49','50',
      5            '51','52','53','54','55','56','57','58','59','60'/
+
+ccc         OVERRIDE DEFAULT C12/C13 RATIO
+      C12=-.005d0
+      C13=-1.955d0
+      OPEN(UNIT=991, FILE='c12c13.dat', STATUS='OLD', IOSTAT=IOS)
+      IF (IOS .EQ. 0) THEN
+          READ(991, *) C12, C13
+          CLOSE(991)
+      ENDIF
+ccc         END OF OVERRIDE
+
 C      OPEN(UNIT=11,TYPE='OLD',FORM='UNFORMATTED',RECORDTYPE='FIXED',
 C     1ACCESS='DIRECT',RECL=16,READONLY,SHARED)
       OPEN(UNIT=12,STATUS='OLD',FORM='UNFORMATTED',ACCESS='APPEND')
@@ -160,7 +172,7 @@ C     CN
       FUDGE=0.00
       ISO1=12
       ISO2=14
-      X1=-.005
+      X1=C12
       X2=-.002
       GO TO 5000
   130 IF(CODE.EQ.606.)GO TO 1300
@@ -171,7 +183,7 @@ C     CN
       FUDGE=0.00
       ISO1=13
       ISO2=14
-      X1=-1.955
+      X1=C13
       X2=-.002
       GO TO 5000
 C     NH
@@ -206,7 +218,7 @@ C     CO
       FUDGE=0.00
       ISO1=12
       ISO2=17
-      X1=-.005
+      X1=C12
       X2=-3.398
       GO TO 5000
   180 IF(CODE.EQ.814.)GO TO 1800
@@ -284,16 +296,16 @@ C     C2
       FUDGE=0.00
       ISO1=13
       ISO2=13
-      X1=-1.955
-      X2=-1.955
+      X1=C13
+      X2=C13
       GO TO 5000
 C     C2
  1200 NELION=264
       FUDGE=0.00
       ISO1=12
       ISO2=12
-      X1=-.005
-      X2=-.005
+      X1=C12
+      X2=C12
       GO TO 5000
 C     CaH
   400 NELION=342
@@ -479,7 +491,7 @@ C     CO
       FUDGE=0.00
       ISO1=12
       ISO2=16
-      X1=-.005
+      X1=C12
       X2=-.001
       GO TO 5000
 C     CH
@@ -488,22 +500,22 @@ C     CH
       ISO1=1
       ISO2=12
       X1=0.
-      X2=-.005
+      X2=C12
       GO TO 5000
 C     C2
  1300 NELION=264
       FUDGE=0.00
       ISO1=12
       ISO2=13
-      X1=-.005
-      X2=-1.955
+      X1=C12
+      X2=C13
       GO TO 5000
 C     CO
  1310 NELION=276
       FUDGE=0.00
       ISO1=13
       ISO2=16
-      X1=-1.955
+      X1=C13
       X2=-.001
       GO TO 5000
 C     CH
@@ -512,14 +524,14 @@ C     CH
       ISO1=1
       ISO2=13
       X1=0.
-      X2=-1.955
+      X2=C13
       GO TO 5000
 C     CN
  1500 NELION=270
       FUDGE=0.00
       ISO1=12
       ISO2=15
-      X1=-.005
+      X1=C12
       X2=-2.444
       GO TO 5000
 C     ALO
@@ -551,7 +563,7 @@ C     CO
       FUDGE=0.00
       ISO1=12
       ISO2=18
-      X1=-.005
+      X1=C12
       X2=-2.690
       GO TO 5000
 C     ALO
EOF

# Patch SYNTHE to indicate calculation progress
patch -o src/synthe.patched.for src/synthe.for << EOF
@@ -213,7 +213,10 @@
       NLINES=NLINES+N19
       IREC=0
 C
+      OPEN(UNIT=242, FILE='progress.dat')
       DO 500 J=1,NRHOX
+      WRITE(242,*) J, '/', NRHOX
+      FLUSH(242)
       REWIND 12
 C     INITIALIZE BUFFER
       DO 210 NBUFF=1,LENGTH
@@ -371,6 +374,7 @@
       MLINEJ(J)=MLINES
       ILINES=ILINES+MLINES
   500 CONTINUE
+      CLOSE(242)
       WRITE(6,106)ILINES
   106 FORMAT(I10)
 C
EOF

# Compile SYNTHE
gfortran -fno-automatic -w -O3 -c src/xnfpelsyn.for -std=legacy
gfortran -fno-automatic -w -O3 -c src/atlas7v.for -std=legacy
gfortran xnfpelsyn.o atlas7v.o -o bin/xnfpelsyn.exe -std=legacy
gfortran -fno-automatic -w -O3 -o bin/synbeg.exe src/synbeg.for -std=legacy
gfortran -fno-automatic -w -O3 -o bin/rgfalllinesnew.exe src/rgfalllinesnew.for -std=legacy
gfortran -fno-automatic -w -O3 -o bin/rpredict.exe src/rpredict.for -std=legacy
gfortran -fno-automatic -w -O3 -o bin/rmolecasc.exe src/rmolecasc.patched.for -std=legacy
gfortran -fno-automatic -w -O3 -o bin/rschwenk.exe src/rschwenk.for -std=legacy
gfortran -fno-automatic -w -O3 -o bin/rh2ofast.exe src/rh2ofast.for -std=legacy
gfortran -fno-automatic -w -O3 -o bin/synthe.exe src/synthe.patched.for -std=legacy
gfortran -fno-automatic -w -O3 -c src/spectrv.for -std=legacy
gfortran spectrv.o atlas7v.o -o bin/spectrv.exe -std=legacy
gfortran -fno-automatic -w -O3 -o bin/converfsynnmtoa.exe src/converfsynnmtoa.for -std=legacy
rm atlas7v.o spectrv.o xnfpelsyn.o
