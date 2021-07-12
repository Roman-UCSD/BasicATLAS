### TEMPLATES OF CONTROL FILES ###

atlas_control_start = """
cd {output_dir}
ln -s odf_1.ros fort.1
ln -s odf_9.bdf fort.9
ln -s {molecules} fort.2
ln -s {initial_model} fort.3 
"""

atlas_control_end = """
cd {output_dir}
mv fort.7 {output_2}
rm fort.*
"""

atlas_control = """
READ KAPPA
READ PUNCH
MOLECULES ON
READ MOLECULES
FREQUENCIES 337 1 337 BIG
VTURB {vturb}.0E+5
CONVECTION OVER 1.25 0 36  
TITLE  [0.0] VTURB={vturb}  L/H=1.25 NOVER NEW ODF 
SCALE 72 -6.875 0.125 {teff} {gravity}
ABUNDANCE SCALE   {abundance_scale} ABUNDANCE CHANGE 1 {element_1} 2 {element_2}
 ABUNDANCE CHANGE  3 {element_3}  4 {element_4}  5  {element_5}  6  {element_6}  7  {element_7}  8  {element_8}
 ABUNDANCE CHANGE  9  {element_9} 10  {element_10} 11  {element_11} 12  {element_12} 13  {element_13} 14  {element_14}
 ABUNDANCE CHANGE 15  {element_15} 16  {element_16} 17  {element_17} 18  {element_18} 19  {element_19} 20  {element_20}
 ABUNDANCE CHANGE 21  {element_21} 22  {element_22} 23  {element_23} 24  {element_24} 25  {element_25} 26  {element_26}
 ABUNDANCE CHANGE 27  {element_27} 28  {element_28} 29  {element_29} 30  {element_30} 31  {element_31} 32  {element_32}
 ABUNDANCE CHANGE 33  {element_33} 34  {element_34} 35  {element_35} 36  {element_36} 37  {element_37} 38  {element_38}
 ABUNDANCE CHANGE 39  {element_39} 40  {element_40} 41 {element_41} 42 {element_42} 43 {element_43} 44 {element_44}
 ABUNDANCE CHANGE 45 {element_45} 46 {element_46} 47 {element_47} 48 {element_48} 49 {element_49} 50 {element_50}
 ABUNDANCE CHANGE 51 {element_51} 52  {element_52} 53 {element_53} 54  {element_54} 55 {element_55} 56  {element_56}
 ABUNDANCE CHANGE 57 {element_57} 58 {element_58} 59 {element_59} 60 {element_60} 61 {element_61} 62 {element_62}
 ABUNDANCE CHANGE 63 {element_63} 64 {element_64} 65 {element_65} 66 {element_66} 67 {element_67} 68 {element_68}
 ABUNDANCE CHANGE 69 {element_69} 70 {element_70} 71 {element_71} 72 {element_72} 73 {element_73} 74 {element_74}
 ABUNDANCE CHANGE 75 {element_75} 76 {element_76} 77 {element_77} 78 {element_78} 79 {element_79} 80 {element_80}
 ABUNDANCE CHANGE 81 {element_81} 82 {element_82} 83 {element_83} 84 {element_84} 85 {element_85} 86 {element_86}
 ABUNDANCE CHANGE 87 {element_87} 88 {element_88} 89 {element_89} 90 {element_90} 91 {element_91} 92 {element_92}
 ABUNDANCE CHANGE 93 {element_93} 94 {element_94} 95 {element_95} 96 {element_96} 97 {element_97} 98 {element_98}
 ABUNDANCE CHANGE 99 {element_99}
{iterations}
"""

kappa9_control = """
cd {output_dir}
mv {d_data}/molecules.dat fort.2
mv ./p00big{v}.bdf fort.9
{dfsynthe_suite}/kappa9.exe<<EOF>kapm40k2.out
MOLECULES ON
READ MOLECULES
FREQUENCIES 337 1 337 BIG
ITERATIONS 1 PRINT 1 PUNCH 0 
TITLE ROSSELAND OPACITY
 OPACITY IFOP 1 1 1 1 1 1 1 1 1 1 1 1 1 0 1 0 0 0 0 0
 CONVECTION ON   1.25 TURBULENCE OFF  0.00  0.00  0.00  0.00
TEFF   {teff}  GRAVITY {gravity} LTE 
ABUNDANCE SCALE   {abundance_scale} ABUNDANCE CHANGE 1 {element_1} 2 {element_2}
 ABUNDANCE CHANGE  3 {element_3}  4 {element_4}  5  {element_5}  6  {element_6}  7  {element_7}  8  {element_8}
 ABUNDANCE CHANGE  9  {element_9} 10  {element_10} 11  {element_11} 12  {element_12} 13  {element_13} 14  {element_14}
 ABUNDANCE CHANGE 15  {element_15} 16  {element_16} 17  {element_17} 18  {element_18} 19  {element_19} 20  {element_20}
 ABUNDANCE CHANGE 21  {element_21} 22  {element_22} 23  {element_23} 24  {element_24} 25  {element_25} 26  {element_26}
 ABUNDANCE CHANGE 27  {element_27} 28  {element_28} 29  {element_29} 30  {element_30} 31  {element_31} 32  {element_32}
 ABUNDANCE CHANGE 33  {element_33} 34  {element_34} 35  {element_35} 36  {element_36} 37  {element_37} 38  {element_38}
 ABUNDANCE CHANGE 39  {element_39} 40  {element_40} 41 {element_41} 42 {element_42} 43 {element_43} 44 {element_44}
 ABUNDANCE CHANGE 45 {element_45} 46 {element_46} 47 {element_47} 48 {element_48} 49 {element_49} 50 {element_50}
 ABUNDANCE CHANGE 51 {element_51} 52  {element_52} 53 {element_53} 54  {element_54} 55 {element_55} 56  {element_56}
 ABUNDANCE CHANGE 57 {element_57} 58 {element_58} 59 {element_59} 60 {element_60} 61 {element_61} 62 {element_62}
 ABUNDANCE CHANGE 63 {element_63} 64 {element_64} 65 {element_65} 66 {element_66} 67 {element_67} 68 {element_68}
 ABUNDANCE CHANGE 69 {element_69} 70 {element_70} 71 {element_71} 72 {element_72} 73 {element_73} 74 {element_74}
 ABUNDANCE CHANGE 75 {element_75} 76 {element_76} 77 {element_77} 78 {element_78} 79 {element_79} 80 {element_80}
 ABUNDANCE CHANGE 81 {element_81} 82 {element_82} 83 {element_83} 84 {element_84} 85 {element_85} 86 {element_86}
 ABUNDANCE CHANGE 87 {element_87} 88 {element_88} 89 {element_89} 90 {element_90} 91 {element_91} 92 {element_92}
 ABUNDANCE CHANGE 93 {element_93} 94 {element_94} 95 {element_95} 96 {element_96} 97 {element_97} 98 {element_98}
 ABUNDANCE CHANGE 99 {element_99}
READ DECK6 72 RHOX,T,P,XNE,ABROSS,ACCRAD,VTURB
 5.12838287E-04   3709.1 1.405E+01 2.797E+09 2.600E-04 7.028E-02 1.500E+05 0.000E+00 0.000E+00
 6.71148215E-04   3732.6 1.839E+01 3.602E+09 3.019E-04 7.387E-02 1.500E+05 0.000E+00 0.000E+00
 8.53583147E-04   3754.9 2.339E+01 4.517E+09 3.483E-04 7.641E-02 1.500E+05 0.000E+00 0.000E+00
 1.06469772E-03   3778.6 2.917E+01 5.568E+09 4.009E-04 7.802E-02 1.500E+05 0.000E+00 0.000E+00
 1.30968473E-03   3803.4 3.588E+01 6.782E+09 4.596E-04 7.825E-02 1.500E+05 0.000E+00 0.000E+00
 1.59577136E-03   3828.9 4.372E+01 8.192E+09 5.233E-04 7.674E-02 1.500E+05 0.000E+00 0.000E+00
 1.93076383E-03   3853.7 5.290E+01 9.828E+09 5.962E-04 7.544E-02 1.500E+05 0.000E+00 0.000E+00
 2.32272392E-03   3877.9 6.364E+01 1.173E+10 6.797E-04 7.446E-02 1.500E+05 0.000E+00 0.000E+00
 2.78100631E-03   3901.7 7.619E+01 1.392E+10 7.755E-04 7.381E-02 1.500E+05 0.000E+00 0.000E+00
 3.31641180E-03   3924.9 9.086E+01 1.647E+10 8.855E-04 7.356E-02 1.500E+05 0.000E+00 0.000E+00
 3.94186646E-03   3947.9 1.080E+02 1.941E+10 1.010E-03 7.334E-02 1.500E+05 0.000E+00 0.000E+00
 4.67302051E-03   3970.8 1.280E+02 2.283E+10 1.152E-03 7.318E-02 1.500E+05 0.000E+00 0.000E+00
 5.52856151E-03   3993.7 1.515E+02 2.679E+10 1.312E-03 7.309E-02 1.500E+05 0.000E+00 0.000E+00
 6.53054813E-03   4016.5 1.789E+02 3.139E+10 1.494E-03 7.303E-02 1.500E+05 0.000E+00 0.000E+00
 7.70352445E-03   4039.3 2.111E+02 3.673E+10 1.703E-03 7.337E-02 1.500E+05 0.000E+00 0.000E+00
 9.07514808E-03   4062.0 2.486E+02 4.292E+10 1.943E-03 7.406E-02 1.500E+05 0.000E+00 0.000E+00
 1.06774833E-02   4085.1 2.925E+02 5.010E+10 2.219E-03 7.515E-02 1.500E+05 0.000E+00 0.000E+00
 1.25488575E-02   4108.9 3.438E+02 5.843E+10 2.533E-03 7.610E-02 1.500E+05 0.000E+00 0.000E+00
 1.47351857E-02   4133.5 4.037E+02 6.811E+10 2.891E-03 7.695E-02 1.500E+05 0.000E+00 0.000E+00
 1.72881496E-02   4158.4 4.736E+02 7.934E+10 3.303E-03 7.816E-02 1.500E+05 0.000E+00 0.000E+00
 2.02692929E-02   4184.1 5.553E+02 9.239E+10 3.770E-03 7.923E-02 1.500E+05 0.000E+00 0.000E+00
 2.37530891E-02   4210.6 6.508E+02 1.076E+11 4.302E-03 8.011E-02 1.500E+05 0.000E+00 0.000E+00
 2.78229282E-02   4237.5 7.623E+02 1.252E+11 4.913E-03 8.119E-02 1.500E+05 0.000E+00 0.000E+00
 3.25736063E-02   4264.9 8.924E+02 1.456E+11 5.614E-03 8.251E-02 1.500E+05 0.000E+00 0.000E+00
 3.81169004E-02   4292.8 1.044E+03 1.694E+11 6.416E-03 8.394E-02 1.500E+05 0.000E+00 0.000E+00
 4.45872937E-02   4321.3 1.222E+03 1.970E+11 7.328E-03 8.527E-02 1.500E+05 0.000E+00 0.000E+00
 5.21389910E-02   4349.7 1.428E+03 2.289E+11 8.376E-03 8.716E-02 1.500E+05 0.000E+00 0.000E+00
 6.09518129E-02   4378.4 1.670E+03 2.660E+11 9.568E-03 8.930E-02 1.500E+05 0.000E+00 0.000E+00
 7.12439100E-02   4407.3 1.952E+03 3.090E+11 1.092E-02 9.155E-02 1.500E+05 0.000E+00 0.000E+00
 8.32644240E-02   4436.2 2.281E+03 3.588E+11 1.247E-02 9.432E-02 1.500E+05 0.000E+00 0.000E+00
 9.72971259E-02   4465.0 2.666E+03 4.165E+11 1.425E-02 9.770E-02 1.500E+05 0.000E+00 0.000E+00
 1.13672868E-01   4493.8 3.114E+03 4.834E+11 1.629E-02 1.018E-01 1.500E+05 0.000E+00 0.000E+00
 1.32786810E-01   4523.1 3.638E+03 5.610E+11 1.860E-02 1.062E-01 1.500E+05 0.000E+00 0.000E+00
 1.55098562E-01   4552.3 4.249E+03 6.509E+11 2.126E-02 1.115E-01 1.500E+05 0.000E+00 0.000E+00
 1.81139153E-01   4581.5 4.963E+03 7.549E+11 2.428E-02 1.176E-01 1.500E+05 0.000E+00 0.000E+00
 2.11544893E-01   4611.0 5.796E+03 8.755E+11 2.773E-02 1.244E-01 1.500E+05 0.000E+00 0.000E+00
 2.47052781E-01   4640.6 6.768E+03 1.015E+12 3.167E-02 1.323E-01 1.500E+05 0.000E+00 0.000E+00
 2.88507698E-01   4670.5 7.904E+03 1.177E+12 3.617E-02 1.414E-01 1.500E+05 0.000E+00 0.000E+00
 3.36895159E-01   4701.0 9.230E+03 1.365E+12 4.133E-02 1.520E-01 1.500E+05 0.000E+00 0.000E+00
 3.93366856E-01   4732.7 1.078E+04 1.584E+12 4.723E-02 1.642E-01 1.500E+05 0.000E+00 0.000E+00
 4.59259744E-01   4765.8 1.258E+04 1.839E+12 5.398E-02 1.782E-01 1.500E+05 0.000E+00 0.000E+00
 5.36129287E-01   4800.8 1.469E+04 2.136E+12 6.171E-02 1.943E-01 1.500E+05 0.000E+00 0.000E+00
 6.25814366E-01   4838.3 1.715E+04 2.484E+12 7.053E-02 2.122E-01 1.500E+05 0.000E+00 0.000E+00
 7.30438050E-01   4879.0 2.001E+04 2.893E+12 8.064E-02 2.328E-01 1.500E+05 0.000E+00 0.000E+00
 8.52425560E-01   4924.1 2.335E+04 3.376E+12 9.225E-02 2.564E-01 1.500E+05 0.000E+00 0.000E+00
 9.94567773E-01   4974.7 2.725E+04 3.951E+12 1.056E-01 2.834E-01 1.500E+05 0.000E+00 0.000E+00
 1.16008551E+00   5032.4 3.178E+04 4.641E+12 1.210E-01 3.143E-01 1.500E+05 0.000E+00 0.000E+00
 1.35274770E+00   5099.6 3.706E+04 5.480E+12 1.387E-01 3.498E-01 1.500E+05 0.000E+00 0.000E+00
 1.57666446E+00   5177.6 4.320E+04 6.515E+12 1.593E-01 3.908E-01 1.500E+05 0.000E+00 0.000E+00
 1.83606723E+00   5269.2 5.030E+04 7.829E+12 1.838E-01 4.392E-01 1.500E+05 0.000E+00 0.000E+00
 2.13471080E+00   5375.8 5.848E+04 9.551E+12 2.139E-01 4.990E-01 1.500E+05 1.240E-09 0.000E+00
 2.47332025E+00   5504.6 6.776E+04 1.198E+13 2.545E-01 5.827E-01 1.500E+05 3.933E-08 0.000E+00
 2.84881471E+00   5650.2 7.805E+04 1.554E+13 3.098E-01 7.002E-01 1.500E+05 3.308E-06 0.000E+00
 3.24852750E+00   5843.7 8.900E+04 2.190E+13 4.021E-01 9.037E-01 1.500E+05 5.162E-04 0.000E+00
 3.63863046E+00   6100.3 9.968E+04 3.491E+13 5.768E-01 1.244E+00 1.500E+05 1.547E-02 1.626E+03
 3.99186702E+00   6359.7 1.094E+05 5.674E+13 8.514E-01 1.662E+00 1.500E+05 8.664E-02 2.998E+03
 4.32516876E+00   6560.2 1.185E+05 8.310E+13 1.163E+00 2.017E+00 1.500E+05 1.667E-01 5.056E+03
 4.64876290E+00   6778.0 1.274E+05 1.237E+14 1.621E+00 2.550E+00 1.500E+05 2.433E-01 2.240E+04
 4.95288884E+00   7030.4 1.357E+05 1.908E+14 2.340E+00 3.362E+00 1.500E+05 3.121E-01 5.586E+04
 5.23070832E+00   7308.0 1.433E+05 2.979E+14 3.453E+00 4.545E+00 1.500E+05 3.719E-01 8.952E+04
 5.47879852E+00   7619.0 1.501E+05 4.727E+14 5.229E+00 6.441E+00 1.500E+05 4.181E-01 1.403E+05
 5.68988391E+00   7981.7 1.559E+05 7.723E+14 8.308E+00 8.682E+00 1.500E+05 5.058E-01 2.085E+05
 5.87591173E+00   8275.3 1.610E+05 1.118E+15 1.195E+01 8.487E+00 1.500E+05 6.602E-01 2.211E+05
 6.05637485E+00   8508.5 1.659E+05 1.478E+15 1.586E+01 7.902E+00 1.500E+05 7.612E-01 2.254E+05
 6.23957016E+00   8729.1 1.709E+05 1.901E+15 2.059E+01 7.414E+00 1.500E+05 8.290E-01 2.261E+05
 6.43191469E+00   8918.9 1.762E+05 2.343E+15 2.570E+01 6.910E+00 1.500E+05 8.718E-01 2.240E+05
 6.63749632E+00   9111.8 1.818E+05 2.874E+15 3.200E+01 6.559E+00 1.500E+05 9.031E-01 2.216E+05
 6.86094505E+00   9283.7 1.880E+05 3.433E+15 3.879E+01 6.111E+00 1.500E+05 9.250E-01 2.180E+05
 7.10613604E+00   9466.6 1.947E+05 4.118E+15 4.724E+01 5.827E+00 1.500E+05 9.417E-01 2.148E+05
 7.37808777E+00   9631.9 2.021E+05 4.840E+15 5.619E+01 5.417E+00 1.500E+05 9.541E-01 2.106E+05
 7.68129689E+00   9813.4 2.104E+05 5.740E+15 6.752E+01 5.181E+00 1.500E+05 9.638E-01 2.072E+05
 8.02184660E+00   9977.4 2.197E+05 6.688E+15 7.936E+01 5.099E+00 1.500E+05 9.695E-01 2.027E+05
PRADK 1.4828E+00
VTURB {v}.0E5
BEGIN                    ITERATION  15 COMPLETED
END
EOF
mv fort.2 {d_data}/molecules.dat
mv fort.9 ./p00big{v}.bdf
mv fort.7 kapk{v}.dat
"""

kapreadts_control = """
cd {output_dir}
mv kapk0.dat fort.11
mv kapk1.dat fort.12
mv kapk2.dat fort.13
mv kapk4.dat fort.14
mv kapk8.dat fort.15
{dfsynthe_suite}/kapreadts.exe
mv fort.2 kappa.ros
rm fort.*
"""

xnfdf_control_start = """cd {output_dir}
cp {d_data}/molecules.dat fort.2
cp {d_data}/pfiron.dat fort.4
cp {d_data}/continua.dat fort.17
{dfsynthe_suite}/xnfdf.exe<<EOF>xnfdf.out
READ MOLECULES
MOLECULES ON
ITERATIONS 1 PRINT 0 PUNCH 0
READ FREQUENCIES 1 1 1 TEST
1 1 1
"""

xnfdf_control_end = """END
EOF
mv fort.10  xnfpdf.dat
mv fort.11 xnfpdfmax.dat
rm fort.*
"""

xnfdf_control = """TEFF   {teff}  GRAVITY {gravity} LTE
TITLE TEMPERATUES AND PRESSURES FOR DISTRIBUTION FUNCTION CALCULATION
 OPACITY IFOP 1 1 1 1 1 1 1 1 1 1 1 1 1 0 1 0 0 0 0 0
 CONVECTION ON   1.25 TURBULENCE OFF  0.00  0.00  0.00  0.00
ABUNDANCE SCALE   {abundance_scale} ABUNDANCE CHANGE 1 {element_1} 2 {element_2}
 ABUNDANCE CHANGE  3 {element_3}  4 {element_4}  5  {element_5}  6  {element_6}  7  {element_7}  8  {element_8}
 ABUNDANCE CHANGE  9  {element_9} 10  {element_10} 11  {element_11} 12  {element_12} 13  {element_13} 14  {element_14}
 ABUNDANCE CHANGE 15  {element_15} 16  {element_16} 17  {element_17} 18  {element_18} 19  {element_19} 20  {element_20}
 ABUNDANCE CHANGE 21  {element_21} 22  {element_22} 23  {element_23} 24  {element_24} 25  {element_25} 26  {element_26}
 ABUNDANCE CHANGE 27  {element_27} 28  {element_28} 29  {element_29} 30  {element_30} 31  {element_31} 32  {element_32}
 ABUNDANCE CHANGE 33  {element_33} 34  {element_34} 35  {element_35} 36  {element_36} 37  {element_37} 38  {element_38}
 ABUNDANCE CHANGE 39  {element_39} 40  {element_40} 41 {element_41} 42 {element_42} 43 {element_43} 44 {element_44}
 ABUNDANCE CHANGE 45 {element_45} 46 {element_46} 47 {element_47} 48 {element_48} 49 {element_49} 50 {element_50}
 ABUNDANCE CHANGE 51 {element_51} 52  {element_52} 53 {element_53} 54  {element_54} 55 {element_55} 56  {element_56}
 ABUNDANCE CHANGE 57 {element_57} 58 {element_58} 59 {element_59} 60 {element_60} 61 {element_61} 62 {element_62}
 ABUNDANCE CHANGE 63 {element_63} 64 {element_64} 65 {element_65} 66 {element_66} 67 {element_67} 68 {element_68}
 ABUNDANCE CHANGE 69 {element_69} 70 {element_70} 71 {element_71} 72 {element_72} 73 {element_73} 74 {element_74}
 ABUNDANCE CHANGE 75 {element_75} 76 {element_76} 77 {element_77} 78 {element_78} 79 {element_79} 80 {element_80}
 ABUNDANCE CHANGE 81 {element_81} 82 {element_82} 83 {element_83} 84 {element_84} 85 {element_85} 86 {element_86}
 ABUNDANCE CHANGE 87 {element_87} 88 {element_88} 89 {element_89} 90 {element_90} 91 {element_91} 92 {element_92}
 ABUNDANCE CHANGE 93 {element_93} 94 {element_94} 95 {element_95} 96 {element_96} 97 {element_97} 98 {element_98}
 ABUNDANCE CHANGE 99 {element_99}
READ DECK6 25 RHOX,T,P,XNE,ABROSS,ACCRAD,VTURB,CONVFRAC,VCONV
   1.000E-4   {dft}  1.000E-4  0 0 0 0 0
   3.162E-4   {dft}  3.162E-4  0 0 0 0 0
   1.000E-3   {dft}  1.000E-3  0 0 0 0 0
   3.162E-3   {dft}  3.162E-3  0 0 0 0 0
   1.000E-2   {dft}  1.000E-2  0 0 0 0 0
   3.162E-2   {dft}  3.162E-2  0 0 0 0 0
   1.000E-1   {dft}  1.000E-1  0 0 0 0 0
   3.162E-1   {dft}  3.162E-1  0 0 0 0 0
   1.000E-0   {dft}  1.000E-0  0 0 0 0 0
   3.162E-0   {dft}  3.162E-0  0 0 0 0 0
   1.000E+1   {dft}  1.000E+1  0 0 0 0 0
   3.162E+1   {dft}  3.162E+1  0 0 0 0 0
   1.000E+2   {dft}  1.000E+2  0 0 0 0 0
   3.162E+2   {dft}  3.162E+2  0 0 0 0 0
   1.000E+3   {dft}  1.000E+3  0 0 0 0 0
   3.162E+3   {dft}  3.162E+3  0 0 0 0 0
   1.000E+4   {dft}  1.000E+4  0 0 0 0 0
   3.162E+4   {dft}  3.162E+4  0 0 0 0 0
   1.000E+5   {dft}  1.000E+5  0 0 0 0 0
   3.162E+5   {dft}  3.162E+5  0 0 0 0 0
   1.000E+6   {dft}  1.000E+6  0 0 0 0 0
   3.162E+6   {dft}  3.162E+6  0 0 0 0 0
   1.000E+7   {dft}  1.000E+7  0 0 0 0 0
   3.162E+7   {dft}  3.162E+7  0 0 0 0 0
   1.000E+8   {dft}  1.000E+8  0 0 0 0 0
 1
BEGIN
"""

dfsynthe_control_start = """
cd {output_dir}
mv ./xnfpdf.dat fort.10
mv ./xnfpdfmax.dat fort.22
mv {d_data}/lowlinesdf.bin fort.11
mv {d_data}/highlinesdf.bin fort.21
mv {d_data}/diatomicsdf.bin fort.31
mv {d_data}/tiolinesdf.bin fort.41
mv {d_data}/h2olinesdf.bin fort.43
mv {d_data}/nltelinesdf.bin fort.51
"""

dfsynthe_control_end = """
cd {output_dir}
mv fort.10 ./xnfpdf.dat
mv fort.22 ./xnfpdfmax.dat
mv fort.11 {d_data}/lowlinesdf.bin
mv fort.21 {d_data}/highlinesdf.bin
mv fort.31 {d_data}/diatomicsdf.bin
mv fort.41 {d_data}/tiolinesdf.bin
mv fort.43 {d_data}/h2olinesdf.bin
mv fort.51 {d_data}/nltelinesdf.bin
"""

dfsynthe_control = """
cd {output_dir}
{dfsynthe_suite}/dfsynthe.exe<<EOF>dfp00t{dft}.out 
{dfsynthe_control_cards}
EOF
mv fort.15 dfp00t{dft}vt0.bin
mv fort.16 dfp00t{dft}vt1.bin
mv fort.17 dfp00t{dft}vt2.bin
mv fort.18 dfp00t{dft}vt4.bin
mv fort.20 dfp00t{dft}vt8.bin

mv dfp00t{dft}vt0.bin fort.1
{dfsynthe_suite}/dfsortp.exe>dfsortp.out
mv fort.2 dfp00t{dft}vt0sortp.asc
mv fort.1 dfp00t{dft}vt0.bin

mv dfp00t{dft}vt1.bin fort.1
{dfsynthe_suite}/dfsortp.exe>dfsortp.out
mv fort.2 dfp00t{dft}vt1sortp.asc
mv fort.1 dfp00t{dft}vt1.bin

mv dfp00t{dft}vt2.bin fort.1
{dfsynthe_suite}/dfsortp.exe>dfsortp.out
mv fort.2 dfp00t{dft}vt2sortp.asc
mv fort.1 dfp00t{dft}vt2.bin

mv dfp00t{dft}vt4.bin fort.1
{dfsynthe_suite}/dfsortp.exe>dfsortp.out
mv fort.2 dfp00t{dft}vt4sortp.asc
mv fort.1 dfp00t{dft}vt4.bin

mv dfp00t{dft}vt8.bin fort.1
{dfsynthe_suite}/dfsortp.exe>dfsortp.out
mv fort.2 dfp00t{dft}vt8sortp.asc
mv fort.1 dfp00t{dft}vt8.bin
"""

separatedf_control = """mv {output_dir}/dfp00t{dft}vt{v}sortp.asc {output_dir}/fort.{serial}
"""

separatedf_control_end = """cd {output_dir}
{dfsynthe_suite}/separatedf.exe
mv fort.2 p00big{v}.bdf
mv fort.3 p00lit{v}.bdf
rm fort.*
"""


atlas_iterations = """ITERATIONS {iterations} PRINT 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
PUNCH 0 1 0 0 0 0 0 0 0 0 0 0 0 0 1
BEGIN                    ITERATION  10 COMPLETED
"""

synthe_prependix = """SURFACE FLUX
ITERATIONS 1 PRINT 2 PUNCH 2
CORRECTION OFF
PRESSURE OFF
READ MOLECULES
MOLECULES ON
"""

synthe_control = """
# SYNTHE test run for a near-solar model

ln -s {s_data}/molecules.dat fort.2
ln -s {s_data}/continua.dat fort.17

# synthe_solar contains the ATLAS-9 output near-solar model with a few additional commands prepended
# First, run xnfpelsyn.exe which takes the model and atomic and molecular densities (whatever that means)
{synthe_suite}/xnfpelsyn.exe< {synthe_solar}>xnfpelsyn.out
mv fort.10 xnft4950g46k1at12.dat
rm fort.*

# synberg.exe initializes the computation. It feeds on the computation parameters such as the wavelength range
# (WLBEG to WLEND), resolution and more...
{synthe_suite}/synbeg.exe<<"EOF">synbeg.out
AIR       {min_wl}{max_wl}600000.     0.00    0     30    .0001     1    0
AIRorVAC  WLBEG     WLEND     RESOLU    TURBV  IFNLTE LINOUT CUTOFF        NREAD
EOF

# Below we import all the spectral lines that we want. Ultimately, it is just a tonne of files with line parameters
# each subsequently fed into rgfalllinesnew.exe for atoms and rmolecasc.exe for molecules
ln -s {s_data}/gf0800.100 fort.11
{synthe_suite}/rgfalllinesnew.exe>gf0800.out
rm fort.11
ln -s {s_data}/gf1200.100 fort.11
{synthe_suite}/rgfalllinesnew.exe>gf1200.out
rm fort.11
ln -s {s_data}/gf0200.100 fort.11
{synthe_suite}/rgfalllinesnew.exe>gf0200.out
rm fort.11
ln -s {s_data}/gf0300.100 fort.11
{synthe_suite}/rgfalllinesnew.exe>gf0300.out
rm fort.11
ln -s {s_data}/gf0400.100 fort.11
{synthe_suite}/rgfalllinesnew.exe>gf0400.out
rm fort.11
ln -s {s_data}/gf0500.100 fort.11
{synthe_suite}/rgfalllinesnew.exe>gf0500.out
rm fort.11
ln -s {s_data}/gf0600.100 fort.11
{synthe_suite}/rgfalllinesnew.exe>gf0600.out
rm fort.11
ln -s {s_data}/gf3000.100 fort.11
{synthe_suite}/rgfalllinesnew.exe>gf3000.out
rm fort.11
ln -s  {s_molecules}/chmasseron.asc fort.11
{synthe_suite}/rmolecasc.exe>chmasseron.out
rm fort.11
ln -s {s_molecules}/mgh.asc fort.11
{synthe_suite}/rmolecasc.exe>mgh.out
rm fort.11
ln -s {s_molecules}/nh.asc fort.11
{synthe_suite}/rmolecasc.exe>nh.out
rm fort.11
ln -s  {s_molecules}/ohupdate.asc fort.11
{synthe_suite}/rmolecasc.exe>oh.out
rm fort.11
ln -s  {s_molecules}/sihax.asc fort.11
{synthe_suite}/rmolecasc.exe>sihax.out
rm fort.11
ln -s {s_molecules}/h2.asc fort.11
{synthe_suite}/rmolecasc.exe>h2.out
rm fort.11
ln -s {s_molecules}/h2xx.asc fort.11
{synthe_suite}/rmolecasc.exe>h2xx.out
rm fort.11
ln -s {s_molecules}/hdxx.asc fort.11
{synthe_suite}/rmolecasc.exe>hdxx.out
rm fort.11
ln -s {s_molecules}/c2ax.asc fort.11
{synthe_suite}/rmolecasc.exe>c2ax.out
rm fort.11
ln -s {s_molecules}/c2ba.asc fort.11
{synthe_suite}/rmolecasc.exe>c2ba.out
rm fort.11
ln -s {s_molecules}/c2dabrookek.asc fort.11
{synthe_suite}/rmolecasc.exe>c2da.out
rm fort.11
ln -s  {s_molecules}/c2ea.asc fort.11
{synthe_suite}/rmolecasc.exe>c2ea.out
rm fort.11
ln -s {s_molecules}/cnaxbrookek.asc fort.11
{synthe_suite}/rmolecasc.exe>cnax.out
rm fort.11
ln -s {s_molecules}/cnbxbrookek.asc fort.11
{synthe_suite}/rmolecasc.exe>cnbx.out
rm fort.11
ln -s {s_molecules}/cnxx12brooke.asc fort.11
{synthe_suite}/rmolecasc.exe>cnxx12.out
rm fort.11
ln -s {s_molecules}/coax.asc fort.11
{synthe_suite}/rmolecasc.exe>coax.out
rm fort.11
ln -s {s_molecules}/coxx.asc fort.11
{synthe_suite}/rmolecasc.exe>coxx.out
rm fort.11
ln -s {s_molecules}/sioax.asc fort.11
{synthe_suite}/rmolecasc.exe>sioax.out
rm fort.11
ln -s {s_molecules}/sioex.asc fort.11
{synthe_suite}/rmolecasc.exe>sioex.out
rm fort.11
ln -s {s_molecules}/sioxx.asc fort.11
{synthe_suite}/rmolecasc.exe>sioxx.out
rm fort.11

# weird stuff: to be figured out...
ln -s {s_data}/fclowlines.bin fort.11
{synthe_suite}/rpredict.exe>predictedlow.out
rm fort.11
ln -s {s_data}/fchighlines.bin fort.11
{synthe_suite}/rpredict.exe>predicthigh.out
rm fort.11


# rschwenk.exe adds Titanium Oxide to the model (TiO) and requires two input databases
ln -s {s_molecules}/tioschwenke.bin fort.11
ln -s {s_molecules}/eschwenke.bin fort.48
{synthe_suite}/rschwenk.exe>rschwenk.out
rm fort.11
rm fort.48

# rh2ofast.exe does the same for water
ln -s {s_molecules}/h2ofastfix.bin fort.11
{synthe_suite}/rh2ofast.exe>h2ofastfix.out
rm fort.11

# synthe.exe requires the previously calculated atomic and molecular densities (by xnfpelsyn.exe) and computes line opacities
ln xnft4950g46k1at12.dat fort.10
ln -s {s_data}/he1tables.dat fort.18
{synthe_suite}/synthe.exe>synthe.out

# spectrv.exe computes the synthetic spectrum. I don't know what these parameters mean just yet.
ln -s {s_data}/molecules.dat fort.2
cat <<"EOF" >fort.25
0.0       0.        1.        0.        0.        0.        0.        0.
0.
RHOXJ     R1        R101      PH1       PC1       PSI1      PRDDOP    PRDPOW
EOF
{synthe_suite}/spectrv.exe<"{synthe_solar}">spectrv.out

# Below we are supposed to be rotating and broadening the spectrum. This does not work and gives NaNs all over the resulting spectrum
# leaving it commented out for now.
# 
# mv fort.7 i7000-7210.dat
# ln -s i7000-7210.dat fort.1
# {synthe_suite}/rotate.exe<<"EOF">rotate.out
#     1
# 0.
# EOF
# mv ROT1 f7000-7210vr2.dat
# ln -s f7000-7210vr2.dat fort.21
# {synthe_suite}/broaden.exe<<"EOF">broaden.out
# GAUSSIAN  48000.    RESOLUTION
# EOF
# mv fort.22 f7000-7210vr2br48000ap04t4970g46k1at12.bin
mv fort.7 f7000-7210vr2br48000ap04t4970g46k1at12.bin
rm fort.*

# Finally, converfsynnmtoa.exe converts the output spectrum in binary into a text file

ln -s f7000-7210vr2br48000ap04t4970g46k1at12.bin fort.1
{synthe_suite}/converfsynnmtoa.exe > converfsynnmtoa.out
mv fort.2 f7000-7210vr2br48000ap04t4970g46k1at12.asc

rm fort.*
rm xnft4950g46k1at12.dat
rm f7000-7210vr2br48000ap04t4970g46k1at12.bin    # Remove binaries
"""
