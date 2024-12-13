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

# Patch ATLAS-9 to
#   (1) Save additional output in the iteration summary table
#   (2) Reformat the iteration summary table to output more decimal places, separate columns with spaces and clearly mark the start and the end of the table
#   (3) Remove unnecessary output
#   (4) Implement maximum number of iterations in chemical equilibrium and report when the limit is reached
#   (5) Stop iterations automatically once the gold convergence has been reached
#   (6) Stop and report when hydrostatic solver fails
#   (7) Stop and report when NaNs appear in the temperature structure
#   (8) Stop and report if the model is clearly diverging
patch -o src/atlas9mem.patched.for src/atlas9mem.for <<EOF
@@ -530,7 +530,7 @@ C     SUM OVER STEPS AND STEP DEPENDENT QUANTITIES
   301 SURFIN(MU)=SURFIN(MU)+SURFI(MU)*STEPWT
       IF(IFPRNT(ITER).EQ.0)RETURN
       IF(NSTEPS.EQ.1)GO TO 310
-      IF(IFHEAD.EQ.0)WRITE(6,101)
+C      IF(IFHEAD.EQ.0)WRITE(6,101)
       IFHEAD=1
 C     IF(N.EQ.1)WRITE(6,303)
       IF(N.EQ.1.AND.IFPRNT(ITER).GT.1)WRITE(6,303)
@@ -549,7 +549,8 @@ C     RHOX1=DLOG10(RHOX1)
 C     IDUM=MAP1(TAUNU,RHOX,NRHOX,1.D0,RHOX1,1)
 cc      TAUEND=DLOG10(TAUNU(NRHOX))
       IF(IFPRNT(ITER).GT.1)
-     1WRITE(6,305)STEPWT,HNU(1),HNULG,HNUMG,RESID,JTAU1,TAUEND
+C     1WRITE(6,305)STEPWT,HNU(1),HNULG,HNUMG,RESID,JTAU1,TAUEND
+     1CONTINUE
 c  305 FORMAT(61X,F10.8,1PE13.4,0PF12.5,F10.3,F9.5,I6,F6.2)
   305 FORMAT(1X,F10.7,1PE13.4,0PF12.5,F10.3,F9.5,I6,F6.2)
   310 IF(IFPRNT(ITER).EQ.4)GO TO 320
@@ -593,7 +594,7 @@ C     RHOX1=DLOG10(RHOX1)
       IF(NSTEPS.GT.1)JTAU1=0
       IF(NSTEPS.GT.1)TAUEND=0.
       IF(IFSURF.NE.0.AND.IFSURF.NE.1)GO TO 405
-      IF(IFHEAD.EQ.0)WRITE(6,101)
+C      IF(IFHEAD.EQ.0)WRITE(6,101)
   101 FORMAT(1H1/////10X,4HWAVE,7X,7HHLAMBDA,7X,5HLOG H,7X,3HMAG,
      1 10X,9HFREQUENCY,8X,3HHNU,10X,5HLOG H,7X,3HMAG,10X,6HTAUONE,
      2 6H TAUNU)
@@ -636,35 +637,58 @@ C
 C     SUMMARIES
   500 IF(IFPRNT(ITER).EQ.0)GO TO 550
 C      IF(IFPRNT(ITER).EQ.1)GO TO 540
-      WRITE(6,501)(J,RHOX(J),PTOTAL(J),PTURB(J),GRDADB(J),DLTDLP(J),
-     1VELSND(J),DLRDLT(J),HEATCP(J),HSCALE(J),VCONV(J),FLXCNV(J),
-     2J=1,NRHOX)
+C      WRITE(6,501)(J,RHOX(J),PTOTAL(J),PTURB(J),GRDADB(J),DLTDLP(J),
+C     1VELSND(J),DLRDLT(J),HEATCP(J),HSCALE(J),VCONV(J),FLXCNV(J),
+C     2J=1,NRHOX)
   501 FORMAT(1H1/////132H        RHOX       PTOTAL     PTURB      GRDADB+
      1     DLTDLP     VELSND     DLRDLT     HEATCP     HSCALE     VCONV +
      2     FLXCNV            /(I4,1P11E11.3))
       WRITE(6,502)FLUX
   502 FORMAT(1H0,108X,4HFLUX,1PE12.4)
-      WRITE(6,503)(J,XNATOM(J),RADEN(J),PRADK(J),XNFPH(J,1),XNFPH(J,2),
-     1XNFPHE(J,1),XNFPHE(J,2),XNFPHE(J,3),VTURB(J),
-     2FLXCNV0(J),FLXCNV1(J),J=1,NRHOX)
+C      WRITE(6,503)(J,XNATOM(J),RADEN(J),PRADK(J),XNFPH(J,1),XNFPH(J,2),
+C     1XNFPHE(J,1),XNFPHE(J,2),XNFPHE(J,3),VTURB(J),
+C     2FLXCNV0(J),FLXCNV1(J),J=1,NRHOX)
   503 FORMAT(1H1/////132H       XNATOM      RADEN      PRADK     XNFPH1 +
      1    XNFPH2     XNFPHE1    XNFPHE2    XNFPHE3     VTURB            +
      2                       /(I4,1P11E11.3))
       CALL W('PRADK0',PRADK0,1)
- 540  WRITE(6,541)TEFF,GLOG,TITLE,ITER
-  541 FORMAT(1H1//////5H TEFF,F8.0,8H   LOG G,F9.5,10X,74A1,2X,
+      DO J=1,NRHOX
+      IF((T(J).NE.T(J)).OR.(FLXERR(J).NE.FLXERR(J)).OR.
+     1 (FLXDRV(J).NE.FLXDRV(J)).OR.(RHOX(J).NE.RHOX(J)))THEN
+      WRITE(*,*) 'NAN DETECTED'
+      STOP
+      ENDIF
+      ENDDO
+ 540  WRITE(*,*) 'START TABLE'
+      WRITE(6,541)TEFF,GLOG,TITLE,ITER
+  541 FORMAT(5H TEFF,F8.0,8H   LOG G,F9.5,10X,74A1,2X,
      1 9HITERATION,I3)
       DO 539 J=1,NRHOX
       IF(IFCORR.EQ.0)FLXRAD(J)=FLUX-FLXCNV(J)
   539 FLXCNVratio(J)=FLXCNV(J)/(FLXCNV(J)+FLXRAD(J))
       WRITE(6,542)(J,RHOX(J),T(J),P(J),XNE(J),RHO(J),ABROSS(J),
-     1HEIGHT(J),TAUROS(J),FLXCNVratio(J),ACCRAD(J),FLXERR(J),FLXDRV(J),
+     1HEIGHT(J),TAUROS(J),FLXCNV(J),PRADK(J),FLXERR(J),FLXDRV(J),
      2J=1,NRHOX)
+      WRITE(*,*) 'END TABLE'
   542 FORMAT(132H0                                    ELECTRON          +
-     1   ROSSELAND    HEIGHT   ROSSELAND   FRACTION  RADIATIVE        PE
+     1   ROSSELAND    HEIGHT   ROSSELAND             RADIATION        PE
      2R CENT FLUX /132H        RHOX      TEMP    PRESSURE    NUMBER    D
-     3ENSITY      MEAN       (KM)      DEPTH    CONV FLUX  ACCELERATION +
-     4   ERROR    DERIV/(I4,1PE10.3,0PF9.1,1P8E11.3,0PF12.3,F9.3))
+     3ENSITY      MEAN       (KM)      DEPTH    CONV FLUX  PRESSURE     +
+     4   ERROR    DERIV/(I4,1X,1PE17.5,1X,0PE17.5,1X,1P8E17.5,1X,
+     5 0PE15.3,1X,E15.3))
+
+C Stop if gold tolerances have been reached
+      AMAXERR=0.0
+      AMAXDER=0.0
+      DO J=1,NRHOX
+      IF(ABS(FLXERR(J)).GT.AMAXERR)THEN
+      AMAXERR=ABS(FLXERR(J))
+      ENDIF
+      IF(ABS(FLXDRV(J)).GT.AMAXDER)THEN
+      AMAXDER=ABS(FLXDRV(J))
+      ENDIF
+      ENDDO
+
   550 IF(IFPNCH(ITER).EQ.0)RETURN
 C
 C     PUNCHOUT
@@ -680,9 +704,9 @@ C    1TRBPOW,TRBSND,TRBCON,XSCALE,(IZ,ABUND(IZ),IZ=1,2)
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
@@ -695,7 +719,18 @@ C    1NU=1,NUMNU)
 C 562 FORMAT(16HREAD FREQUENCIES3I4,3X6A1/(I5,1P2E17.8,I5,2E17.8))
   570 WRITE(7,571)ITER
   571 FORMAT(5HBEGIN,20X,10HITERATION I3,10H COMPLETED )
-      CLOSE(UNIT=7)
+      WRITE(7,9998)
+ 9998 FORMAT(10H==========)
+C      CLOSE(UNIT=7)
+      IF((MOD(ITER,15).EQ.0).AND.(AMAXDER.LT.10).AND.
+     1 (AMAXERR.LT.1))THEN
+      WRITE(*,*) 'REACHED GOLD TOLERANCES'
+      STOP
+      ENDIF
+      IF((MOD(ITER,15).EQ.0).AND.(AMAXDER.GT.100000))THEN
+      WRITE(*,*) 'MODEL DIVERGED'
+      STOP
+      ENDIF
       RETURN
       END
       SUBROUTINE TCORR(MODE,RCOWT)
@@ -917,8 +952,8 @@ C
    50 T1(J)=DTFLUX(J)+DTLAMB(J)+DTSURF(J)
 C     IF(IFPRNT(ITER).LE.1)GO TO 60
       IF(IFPRNT(ITER).EQ.0)GO TO 60
-      WRITE(6,100) (J,RHOX(J),T(J),DTLAMB(J),DTSURF(J),DTFLUX(J),T1(J),
-     1HRATIO(J),FLXERR(J),FLXDRV(J),J=1,NRHOX)
+C      WRITE(6,100) (J,RHOX(J),T(J),DTLAMB(J),DTSURF(J),DTFLUX(J),T1(J),
+C     1HRATIO(J),FLXERR(J),FLXDRV(J),J=1,NRHOX)
   100 FORMAT(1H1///95H0         RHOX        T      DTLAMB   DTSURF   DTF
      1LUX      T1   CONV/TOTAL      ERROR     DERIV/
      2(I4,1PE12.4,0PF10.1,4F9.1,1X,1PE11.3,1X,0P2F10.3))
@@ -1232,7 +1267,7 @@ C
   110 FORMAT (6X21F6.2)
   120 CONTINUE
 C
-  160 WRITE (6,170)(J,RHOX(J),(BHYD(J,I),I=1,6),J=1,NRHOX)
+C  160 WRITE (6,170)(J,RHOX(J),(BHYD(J,I),I=1,6),J=1,NRHOX)
   170 FORMAT(1H1/////30X36HSTATISTICAL EQUILIBRIUM FOR HYDROGEN/
      1 15X4HRHOX,10X2HB1,8X2HB2,8X2HB3,8X2HB4,8X2HB5,8X2HB6/
      2(8XI2,1PE11.4,1X0P6F10.4))
@@ -1546,7 +1581,7 @@ C     THACHER, MATH. OF COMP.,22,641(1968)
       PARAMETER (kw=99)
       DIMENSION B(1)
       character*6 A
-      WRITE(6,100)A,(B(I),I=1,N)
+C      WRITE(6,100)A,(B(I),I=1,N)
   100 FORMAT(1H0,A6,1P10E12.4/(7X,10E12.4))
       RETURN
       END
@@ -3308,6 +3343,7 @@ C     T(1)=T1
       CALL W('PTURB ',PTURB,J)
       CALL W('ABSTD ',ABSTD,J)
       CALL W('ERROR ',ERROR,1)
+      WRITE(*,*) 'HYDROFAIL'
       CALL EXIT
       END
       SUBROUTINE BLOCKE
@@ -4721,7 +4757,7 @@ C      IF(ITEMP.GT.0)RETURN
 C      IF(IFMOL.EQ.0)RETURN
 C      IF(IFPRES.EQ.0)RETURN
 C      OPEN(UNIT=2,STATUS='OLD',SHARED,READONLY)
-      WRITE(6,10)
+C      WRITE(6,10)
    10 FORMAT(16H1MOLECULES INPUT)
       DO 11 I=1,101
    11 IFEQUA(I)=0
@@ -4733,7 +4769,7 @@ C     IF IFEQUA=1 AN EQUATION MUST BE SET UP FOR ELEMENT I
       READ(2,13)C,E1,E2,E3,E4,E5,E6
    13 FORMAT(F18.2,F7.3,5E11.4)
       IF(C.EQ.0.)GO TO 23
-      WRITE(6,14)JMOL,C,E1,E2,E3,E4,E5,E6
+C      WRITE(6,14)JMOL,C,E1,E2,E3,E4,E5,E6
    14 FORMAT(I5,F18.2,F7.3,1P5E11.4)
       DO 15 II=1,8
       IF(C.GE.XCODE(II))GO TO 16
@@ -13727,7 +13763,9 @@ C     2 106.206*T10000**5-30.8720*T10000**6-1.5*TLOG(J))
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
@@ -13817,7 +13855,12 @@ cc      XN(K)=XNEQ
       GO TO 105
 C 102 XN(K)=XN100
   105 EQOLD(K)=EQ(K)
+      IF(NCHEMITER.LT.20000)THEN
       IF(IFERR.EQ.1)GO TO 50
+      ENDIF
+      IF(NCHEMITER.GE.20000)THEN
+      WRITE(*,*) 'CHEMFAIL'
+      ENDIF
 C
       DO 107 K=1,NEQUA
   107 XNZ(J,K)=XN(K)
@@ -13842,16 +13885,17 @@ C
       DO 1111 J=1,NRHOX
  1111 XNSAVE(J,K)=XNZ(J,K)
       IF(ITER.LT.NUMITS)GO TO 120
-      WRITE(6,112)(J,RHOX(J),T(J),P(J),XNE(J),XNATOM(J),RHO(J),
-     1J=1,NRHOX)
+C      WRITE(6,112)(J,RHOX(J),T(J),P(J),XNE(J),XNATOM(J),RHO(J),
+C     1J=1,NRHOX)
   112 FORMAT(1H1,10X,4HRHOX,9X,1HT,11X,1HP,10X,3HXNE,8X,6HXNATOM,
      1 8X,3HRHO/(I5,1P6E12.3))
       NN=(NUMMOL/10)*10
       IF(NN.LT.NUMMOL)NN=NN+10
       DO 111 JMOL1=1,NN,10
       JMOL10=JMOL1+9
-  111 WRITE(6,113)(CODE(JMOL),JMOL=JMOL1,JMOL10),(J,(XNMOL(J,JMOL),
-     1JMOL=JMOL1,JMOL10),J=1,NRHOX)
+  111 CONTINUE
+C  111 WRITE(6,113)(CODE(JMOL),JMOL=JMOL1,JMOL10),(J,(XNMOL(J,JMOL),
+C     1JMOL=JMOL1,JMOL10),J=1,NRHOX)
   113 FORMAT(1H1,49X,26HMOLECULAR NUMBER DENSITIES/5X,10F12.2/
      1(I5,1P10E12.3))
   120 IF(MODE.EQ.2.OR.MODE.EQ.12)GO TO 149
EOF

# Compile patched ATLAS-9
gfortran -o bin/atlas9mem.exe src/atlas9mem.patched.for -ffpe-summary=none -finit-local-zero -fno-automatic -w -std=legacy

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
