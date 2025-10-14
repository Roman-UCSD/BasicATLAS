### TEMPLATES OF CONTROL FILES ###

atlas_restart = """TEFF  {teff:<6.0f}  GRAVITY 0.00000 LTE 
TITLE  Restart                                   
 OPACITY IFOP 1 1 1 1 1 1 1 1 1 1 1 1 1 0 1 0 0 0 0 0
 CONVECTION ON   0.00 TURBULENCE OFF  0.00  0.00  0.00  0.00
ABUNDANCE SCALE   0.00000 ABUNDANCE CHANGE 1 0.00000 2 0.00000
 ABUNDANCE CHANGE  3  00.00  4  00.00  5  00.00  6  00.00  7  00.00  8  00.00
 ABUNDANCE CHANGE  9  00.00 10  00.00 11  00.00 12  00.00 13  00.00 14  00.00
 ABUNDANCE CHANGE 15  00.00 16  00.00 17  00.00 18  00.00 19  00.00 20  00.00
 ABUNDANCE CHANGE 21  00.00 22  00.00 23  00.00 24  00.00 25  00.00 26  00.00
 ABUNDANCE CHANGE 27  00.00 28  00.00 29  00.00 30  00.00 31  00.00 32  00.00
 ABUNDANCE CHANGE 33  00.00 34  00.00 35  00.00 36  00.00 37  00.00 38  00.00
 ABUNDANCE CHANGE 39  00.00 40  00.00 41  00.00 42  00.00 43  00.00 44  00.00
 ABUNDANCE CHANGE 45  00.00 46  00.00 47  00.00 48  00.00 49  00.00 50  00.00
 ABUNDANCE CHANGE 51  00.00 52  00.00 53  00.00 54  00.00 55  00.00 56  00.00
 ABUNDANCE CHANGE 57  00.00 58  00.00 59  00.00 60  00.00 61  00.00 62  00.00
 ABUNDANCE CHANGE 63  00.00 64  00.00 65  00.00 66  00.00 67  00.00 68  00.00
 ABUNDANCE CHANGE 69  00.00 70  00.00 71  00.00 72  00.00 73  00.00 74  00.00
 ABUNDANCE CHANGE 75  00.00 76  00.00 77  00.00 78  00.00 79  00.00 80  00.00
 ABUNDANCE CHANGE 81  00.00 82  00.00 83  00.00 84  00.00 85  00.00 86  00.00
 ABUNDANCE CHANGE 87  00.00 88  00.00 89  00.00 90  00.00 91  00.00 92  00.00
 ABUNDANCE CHANGE 93  00.00 94  00.00 95  00.00 96  00.00 97  00.00 98  00.00
 ABUNDANCE CHANGE 99  00.00
READ DECK6 72 RHOX,T,P,XNE,ABROSS,ACCRAD,VTURB, FLXCNV,VCONV,VELSND
{structure}
PRADK 0.0000E+00
BEGIN                    ITERATION  15 COMPLETED
"""

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
cd {output_dir}
{atlas_exe}<<"EOF">{output_1}
READ KAPPA
READ PUNCH
MOLECULES {enable_molecules}
READ MOLECULES
FREQUENCIES 337 1 337 BIG
VTURB {vturb}.0E+5
CONVECTION OVER 1.25 0 36  
TITLE  BasicATLAS
SCALE 72 -6.875 0.125 {teff:<6.0f} {gravity:<7.4f}
ABUNDANCE SCALE {abundance_scale:>9.6f} ABUNDANCE CHANGE 1 {element_1:>7.5f} 2 {element_2:>7.5f}
 ABUNDANCE CHANGE  3 {element_3:>6.2f}  4 {element_4:>6.2f}  5 {element_5:>6.2f}  6 {element_6:>6.2f}  7 {element_7:>6.2f}  8 {element_8:>6.2f}
 ABUNDANCE CHANGE  9 {element_9:>6.2f} 10 {element_10:>6.2f} 11 {element_11:>6.2f} 12 {element_12:>6.2f} 13 {element_13:>6.2f} 14 {element_14:>6.2f}
 ABUNDANCE CHANGE 15 {element_15:>6.2f} 16 {element_16:>6.2f} 17 {element_17:>6.2f} 18 {element_18:>6.2f} 19 {element_19:>6.2f} 20 {element_20:>6.2f}
 ABUNDANCE CHANGE 21 {element_21:>6.2f} 22 {element_22:>6.2f} 23 {element_23:>6.2f} 24 {element_24:>6.2f} 25 {element_25:>6.2f} 26 {element_26:>6.2f}
 ABUNDANCE CHANGE 27 {element_27:>6.2f} 28 {element_28:>6.2f} 29 {element_29:>6.2f} 30 {element_30:>6.2f} 31 {element_31:>6.2f} 32 {element_32:>6.2f}
 ABUNDANCE CHANGE 33 {element_33:>6.2f} 34 {element_34:>6.2f} 35 {element_35:>6.2f} 36 {element_36:>6.2f} 37 {element_37:>6.2f} 38 {element_38:>6.2f}
 ABUNDANCE CHANGE 39 {element_39:>6.2f} 40 {element_40:>6.2f} 41 {element_41:>6.2f} 42 {element_42:>6.2f} 43 {element_43:>6.2f} 44 {element_44:>6.2f}
 ABUNDANCE CHANGE 45 {element_45:>6.2f} 46 {element_46:>6.2f} 47 {element_47:>6.2f} 48 {element_48:>6.2f} 49 {element_49:>6.2f} 50 {element_50:>6.2f}
 ABUNDANCE CHANGE 51 {element_51:>6.2f} 52 {element_52:>6.2f} 53 {element_53:>6.2f} 54 {element_54:>6.2f} 55 {element_55:>6.2f} 56 {element_56:>6.2f}
 ABUNDANCE CHANGE 57 {element_57:>6.2f} 58 {element_58:>6.2f} 59 {element_59:>6.2f} 60 {element_60:>6.2f} 61 {element_61:>6.2f} 62 {element_62:>6.2f}
 ABUNDANCE CHANGE 63 {element_63:>6.2f} 64 {element_64:>6.2f} 65 {element_65:>6.2f} 66 {element_66:>6.2f} 67 {element_67:>6.2f} 68 {element_68:>6.2f}
 ABUNDANCE CHANGE 69 {element_69:>6.2f} 70 {element_70:>6.2f} 71 {element_71:>6.2f} 72 {element_72:>6.2f} 73 {element_73:>6.2f} 74 {element_74:>6.2f}
 ABUNDANCE CHANGE 75 {element_75:>6.2f} 76 {element_76:>6.2f} 77 {element_77:>6.2f} 78 {element_78:>6.2f} 79 {element_79:>6.2f} 80 {element_80:>6.2f}
 ABUNDANCE CHANGE 81 {element_81:>6.2f} 82 {element_82:>6.2f} 83 {element_83:>6.2f} 84 {element_84:>6.2f} 85 {element_85:>6.2f} 86 {element_86:>6.2f}
 ABUNDANCE CHANGE 87 {element_87:>6.2f} 88 {element_88:>6.2f} 89 {element_89:>6.2f} 90 {element_90:>6.2f} 91 {element_91:>6.2f} 92 {element_92:>6.2f}
 ABUNDANCE CHANGE 93 {element_93:>6.2f} 94 {element_94:>6.2f} 95 {element_95:>6.2f} 96 {element_96:>6.2f} 97 {element_97:>6.2f} 98 {element_98:>6.2f}
 ABUNDANCE CHANGE 99 {element_99:>6.2f}
{iterations}
EOF
"""

kappa9_control = """
cd {output_dir}
cp {d_data}/molecules.dat fort.2
mv ./p00big{v}.bdf fort.9
{dfsynthe_suite}/kappa9.exe<<EOF>kapm40k2.out
MOLECULES ON
READ MOLECULES
FREQUENCIES 337 1 337 BIG
ITERATIONS 1 PRINT 1 PUNCH 0 
TITLE ROSSELAND OPACITY
 OPACITY IFOP 1 1 1 1 1 1 1 1 1 1 1 1 1 0 1 0 0 0 0 0
 CONVECTION ON   1.25 TURBULENCE OFF  0.00  0.00  0.00  0.00
TEFF   5777.  GRAVITY 4.43770 LTE
ABUNDANCE SCALE {abundance_scale:>9.6f} ABUNDANCE CHANGE 1 {element_1:>7.5f} 2 {element_2:>7.5f}
 ABUNDANCE CHANGE  3 {element_3:>6.2f}  4 {element_4:>6.2f}  5 {element_5:>6.2f}  6 {element_6:>6.2f}  7 {element_7:>6.2f}  8 {element_8:>6.2f}
 ABUNDANCE CHANGE  9 {element_9:>6.2f} 10 {element_10:>6.2f} 11 {element_11:>6.2f} 12 {element_12:>6.2f} 13 {element_13:>6.2f} 14 {element_14:>6.2f}
 ABUNDANCE CHANGE 15 {element_15:>6.2f} 16 {element_16:>6.2f} 17 {element_17:>6.2f} 18 {element_18:>6.2f} 19 {element_19:>6.2f} 20 {element_20:>6.2f}
 ABUNDANCE CHANGE 21 {element_21:>6.2f} 22 {element_22:>6.2f} 23 {element_23:>6.2f} 24 {element_24:>6.2f} 25 {element_25:>6.2f} 26 {element_26:>6.2f}
 ABUNDANCE CHANGE 27 {element_27:>6.2f} 28 {element_28:>6.2f} 29 {element_29:>6.2f} 30 {element_30:>6.2f} 31 {element_31:>6.2f} 32 {element_32:>6.2f}
 ABUNDANCE CHANGE 33 {element_33:>6.2f} 34 {element_34:>6.2f} 35 {element_35:>6.2f} 36 {element_36:>6.2f} 37 {element_37:>6.2f} 38 {element_38:>6.2f}
 ABUNDANCE CHANGE 39 {element_39:>6.2f} 40 {element_40:>6.2f} 41 {element_41:>6.2f} 42 {element_42:>6.2f} 43 {element_43:>6.2f} 44 {element_44:>6.2f}
 ABUNDANCE CHANGE 45 {element_45:>6.2f} 46 {element_46:>6.2f} 47 {element_47:>6.2f} 48 {element_48:>6.2f} 49 {element_49:>6.2f} 50 {element_50:>6.2f}
 ABUNDANCE CHANGE 51 {element_51:>6.2f} 52 {element_52:>6.2f} 53 {element_53:>6.2f} 54 {element_54:>6.2f} 55 {element_55:>6.2f} 56 {element_56:>6.2f}
 ABUNDANCE CHANGE 57 {element_57:>6.2f} 58 {element_58:>6.2f} 59 {element_59:>6.2f} 60 {element_60:>6.2f} 61 {element_61:>6.2f} 62 {element_62:>6.2f}
 ABUNDANCE CHANGE 63 {element_63:>6.2f} 64 {element_64:>6.2f} 65 {element_65:>6.2f} 66 {element_66:>6.2f} 67 {element_67:>6.2f} 68 {element_68:>6.2f}
 ABUNDANCE CHANGE 69 {element_69:>6.2f} 70 {element_70:>6.2f} 71 {element_71:>6.2f} 72 {element_72:>6.2f} 73 {element_73:>6.2f} 74 {element_74:>6.2f}
 ABUNDANCE CHANGE 75 {element_75:>6.2f} 76 {element_76:>6.2f} 77 {element_77:>6.2f} 78 {element_78:>6.2f} 79 {element_79:>6.2f} 80 {element_80:>6.2f}
 ABUNDANCE CHANGE 81 {element_81:>6.2f} 82 {element_82:>6.2f} 83 {element_83:>6.2f} 84 {element_84:>6.2f} 85 {element_85:>6.2f} 86 {element_86:>6.2f}
 ABUNDANCE CHANGE 87 {element_87:>6.2f} 88 {element_88:>6.2f} 89 {element_89:>6.2f} 90 {element_90:>6.2f} 91 {element_91:>6.2f} 92 {element_92:>6.2f}
 ABUNDANCE CHANGE 93 {element_93:>6.2f} 94 {element_94:>6.2f} 95 {element_95:>6.2f} 96 {element_96:>6.2f} 97 {element_97:>6.2f} 98 {element_98:>6.2f}
 ABUNDANCE CHANGE 99 {element_99:>6.2f}
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
rm -r dft_*
rm *.bin
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

xnfdf_control = """TEFF   5777.  GRAVITY 4.43770 LTE
TITLE TEMPERATUES AND PRESSURES FOR DISTRIBUTION FUNCTION CALCULATION
 OPACITY IFOP 1 1 1 1 1 1 1 1 1 1 1 1 1 0 1 0 0 0 0 0
 CONVECTION ON   1.25 TURBULENCE OFF  0.00  0.00  0.00  0.00
ABUNDANCE SCALE {abundance_scale:>9.6f} ABUNDANCE CHANGE 1 {element_1:>7.5f} 2 {element_2:>7.5f}
 ABUNDANCE CHANGE  3 {element_3:>6.2f}  4 {element_4:>6.2f}  5 {element_5:>6.2f}  6 {element_6:>6.2f}  7 {element_7:>6.2f}  8 {element_8:>6.2f}
 ABUNDANCE CHANGE  9 {element_9:>6.2f} 10 {element_10:>6.2f} 11 {element_11:>6.2f} 12 {element_12:>6.2f} 13 {element_13:>6.2f} 14 {element_14:>6.2f}
 ABUNDANCE CHANGE 15 {element_15:>6.2f} 16 {element_16:>6.2f} 17 {element_17:>6.2f} 18 {element_18:>6.2f} 19 {element_19:>6.2f} 20 {element_20:>6.2f}
 ABUNDANCE CHANGE 21 {element_21:>6.2f} 22 {element_22:>6.2f} 23 {element_23:>6.2f} 24 {element_24:>6.2f} 25 {element_25:>6.2f} 26 {element_26:>6.2f}
 ABUNDANCE CHANGE 27 {element_27:>6.2f} 28 {element_28:>6.2f} 29 {element_29:>6.2f} 30 {element_30:>6.2f} 31 {element_31:>6.2f} 32 {element_32:>6.2f}
 ABUNDANCE CHANGE 33 {element_33:>6.2f} 34 {element_34:>6.2f} 35 {element_35:>6.2f} 36 {element_36:>6.2f} 37 {element_37:>6.2f} 38 {element_38:>6.2f}
 ABUNDANCE CHANGE 39 {element_39:>6.2f} 40 {element_40:>6.2f} 41 {element_41:>6.2f} 42 {element_42:>6.2f} 43 {element_43:>6.2f} 44 {element_44:>6.2f}
 ABUNDANCE CHANGE 45 {element_45:>6.2f} 46 {element_46:>6.2f} 47 {element_47:>6.2f} 48 {element_48:>6.2f} 49 {element_49:>6.2f} 50 {element_50:>6.2f}
 ABUNDANCE CHANGE 51 {element_51:>6.2f} 52 {element_52:>6.2f} 53 {element_53:>6.2f} 54 {element_54:>6.2f} 55 {element_55:>6.2f} 56 {element_56:>6.2f}
 ABUNDANCE CHANGE 57 {element_57:>6.2f} 58 {element_58:>6.2f} 59 {element_59:>6.2f} 60 {element_60:>6.2f} 61 {element_61:>6.2f} 62 {element_62:>6.2f}
 ABUNDANCE CHANGE 63 {element_63:>6.2f} 64 {element_64:>6.2f} 65 {element_65:>6.2f} 66 {element_66:>6.2f} 67 {element_67:>6.2f} 68 {element_68:>6.2f}
 ABUNDANCE CHANGE 69 {element_69:>6.2f} 70 {element_70:>6.2f} 71 {element_71:>6.2f} 72 {element_72:>6.2f} 73 {element_73:>6.2f} 74 {element_74:>6.2f}
 ABUNDANCE CHANGE 75 {element_75:>6.2f} 76 {element_76:>6.2f} 77 {element_77:>6.2f} 78 {element_78:>6.2f} 79 {element_79:>6.2f} 80 {element_80:>6.2f}
 ABUNDANCE CHANGE 81 {element_81:>6.2f} 82 {element_82:>6.2f} 83 {element_83:>6.2f} 84 {element_84:>6.2f} 85 {element_85:>6.2f} 86 {element_86:>6.2f}
 ABUNDANCE CHANGE 87 {element_87:>6.2f} 88 {element_88:>6.2f} 89 {element_89:>6.2f} 90 {element_90:>6.2f} 91 {element_91:>6.2f} 92 {element_92:>6.2f}
 ABUNDANCE CHANGE 93 {element_93:>6.2f} 94 {element_94:>6.2f} 95 {element_95:>6.2f} 96 {element_96:>6.2f} 97 {element_97:>6.2f} 98 {element_98:>6.2f}
 ABUNDANCE CHANGE 99 {element_99:>6.2f}
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
ln -s ../xnfpdf.dat fort.10
ln -s ../xnfpdfmax.dat fort.22
ln -s {d_data}/lowlinesdf.bin fort.11
ln -s {d_data}/highlinesdf.bin fort.21
ln -s {d_data}/diatomicsdf.bin fort.31
ln -s {d_data}/tiolinesdf.bin fort.41
ln -s {d_data}/h2olinesdf.bin fort.43
ln -s {d_data}/nltelinesdf.bin fort.51
"""

dfsynthe_control_end = """
cd {output_dir}
rm fort.10
rm fort.22
rm fort.11
rm fort.21
rm fort.31
rm fort.41
rm fort.43
rm fort.51
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
mv fort.2 ../dfp00t{dft}vt0sortp.asc
mv fort.1 ../dfp00t{dft}vt0.bin

mv dfp00t{dft}vt1.bin fort.1
{dfsynthe_suite}/dfsortp.exe>dfsortp.out
mv fort.2 ../dfp00t{dft}vt1sortp.asc
mv fort.1 ../dfp00t{dft}vt1.bin

mv dfp00t{dft}vt2.bin fort.1
{dfsynthe_suite}/dfsortp.exe>dfsortp.out
mv fort.2 ../dfp00t{dft}vt2sortp.asc
mv fort.1 ../dfp00t{dft}vt2.bin

mv dfp00t{dft}vt4.bin fort.1
{dfsynthe_suite}/dfsortp.exe>dfsortp.out
mv fort.2 ../dfp00t{dft}vt4sortp.asc
mv fort.1 ../dfp00t{dft}vt4.bin

mv dfp00t{dft}vt8.bin fort.1
{dfsynthe_suite}/dfsortp.exe>dfsortp.out
mv fort.2 ../dfp00t{dft}vt8sortp.asc
mv fort.1 ../dfp00t{dft}vt8.bin
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
PUNCH 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
BEGIN                    ITERATION  10 COMPLETED
"""

synthe_prependix = """SURFACE FLUX
ITERATIONS 1 PRINT 2 PUNCH 2
CORRECTION OFF
PRESSURE OFF
READ MOLECULES
MOLECULES ON
"""

synthe_control = """cd {output_dir}
mkdir -p synthe_{synthe_num}
cd synthe_{synthe_num}/
ln -s {s_files}/molecules.dat fort.2
ln -s {s_files}/continua.dat fort.17

# xnfpelsyn.exe computes the chemical equilibrium
{synthe_suite}/xnfpelsyn.exe< {synthe_solar}>xnfpelsyn.out
mv fort.10 xnfpelsyn.dat
rm fort.*

# synberg.exe initializes the computation
{synthe_suite}/synbeg.exe<<"EOF">synbeg.out
{airorvac:<3s}       {wlbeg:<10.4f}{wlend:<10.4f}{resolu:<9.2f} {turbv:<10.4f}{ifnlte:<3d}{linout:<7d}{cutoff:<10.5f}{ifpred:<5d}{nread:<5d}
AIRorVAC  WLBEG     WLEND     RESOLU    TURBV  IFNLTE LINOUT CUTOFF        NREAD
EOF

# Import atomic lines
ln -s {linelist} fort.11
{synthe_suite}/rgfalllinesnew.exe>rgfalllinesnew.out
rm fort.11

# Set the C12/C13 ratio
{C12C13}

# Import diatomic molecular lines
ln -s  {s_files}/chmasseron_corrected.asc fort.11
{synthe_suite}/rmolecasc.exe>chmasseron.out
rm fort.11
ln -s {s_files}/mgh_exomol.asc fort.11
{synthe_suite}/rmolecasc.exe>mgh.out
rm fort.11
ln -s {s_files}/nh.asc fort.11
{synthe_suite}/rmolecasc.exe>nh.out
rm fort.11
ln -s  {s_files}/ohupdate.asc fort.11
{synthe_suite}/rmolecasc.exe>oh.out
rm fort.11
ln -s  {s_files}/sihax.asc fort.11
{synthe_suite}/rmolecasc.exe>sihax.out
rm fort.11
ln -s {s_files}/h2.asc fort.11
{synthe_suite}/rmolecasc.exe>h2.out
rm fort.11
ln -s {s_files}/h2xx.asc fort.11
{synthe_suite}/rmolecasc.exe>h2xx.out
rm fort.11
ln -s {s_files}/hdxx.asc fort.11
{synthe_suite}/rmolecasc.exe>hdxx.out
rm fort.11
ln -s {s_files}/c2ax.asc fort.11
{synthe_suite}/rmolecasc.exe>c2ax.out
rm fort.11
ln -s {s_files}/c2ba.asc fort.11
{synthe_suite}/rmolecasc.exe>c2ba.out
rm fort.11
ln -s {s_files}/c2dabrookek.asc fort.11
{synthe_suite}/rmolecasc.exe>c2da.out
rm fort.11
ln -s  {s_files}/c2ea.asc fort.11
{synthe_suite}/rmolecasc.exe>c2ea.out
rm fort.11
ln -s {s_files}/cnaxbrookek.asc fort.11
{synthe_suite}/rmolecasc.exe>cnax.out
rm fort.11
ln -s {s_files}/cnbxbrookek.asc fort.11
{synthe_suite}/rmolecasc.exe>cnbx.out
rm fort.11
ln -s {s_files}/cnxx12brooke.asc fort.11
{synthe_suite}/rmolecasc.exe>cnxx12.out
rm fort.11
ln -s {s_files}/coax.asc fort.11
{synthe_suite}/rmolecasc.exe>coax.out
rm fort.11
ln -s {s_files}/coxx.asc fort.11
{synthe_suite}/rmolecasc.exe>coxx.out
rm fort.11
ln -s {s_files}/sioax.asc fort.11
{synthe_suite}/rmolecasc.exe>sioax.out
rm fort.11
ln -s {s_files}/sioex.asc fort.11
{synthe_suite}/rmolecasc.exe>sioex.out
rm fort.11
ln -s {s_files}/sioxx.asc fort.11
{synthe_suite}/rmolecasc.exe>sioxx.out
rm fort.11

# Import TiO lines
ln -s {s_files}/tiototo.asc fort.11
{synthe_suite}/rmolecasc.exe>tio.out
rm fort.11

# Import H2O lines
ln -s {d_files}/h2ofastfix.bin fort.11
{synthe_suite}/rh2ofast.exe>h2ofastfix.out
rm fort.11

# synthe.exe computes line opacities
ln xnfpelsyn.dat fort.10
ln -s {s_files}/he1tables.dat fort.18
{synthe_suite}/synthe.exe>synthe.out

# spectrv.exe computes the synthetic spectrum
ln -s {s_files}/molecules.dat fort.2
cat <<"EOF" >fort.25
0.0       0.        1.        0.        0.        0.        0.        0.
0.
RHOXJ     R1        R101      PH1       PC1       PSI1      PRDDOP    PRDPOW
EOF
{synthe_suite}/spectrv.exe<"{synthe_solar}">spectrv.out

mv fort.7 spectrum.bin
rm fort.*

# Finally, converfsynnmtoa.exe converts the output spectrum in binary into a text file

ln -s spectrum.bin fort.1
{synthe_suite}/converfsynnmtoa.exe > converfsynnmtoa.out
mv fort.2 spectrum.asc

rm fort.*
rm xnfpelsyn.dat
rm spectrum.bin
"""

synthe_cleanup = """cd {output_dir}
rm -f output_synthe.out
rm -f synthe_launch.com
rm -f spectrum.dat
rm -rf synthe_*
"""
