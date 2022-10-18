# Advanced features
## Disclaimer
The aim of `BasicATLAS` is to make the *basic* functionality of `ATLAS` and satellite software readily accessible through straightforward Python functions. The most commonly used settings can be altered through the arguments of said functions while the most commonly required physical quantities may be read from an `ATLAS` model using `atlas.read_structure()` in `BasicATLAS`. However, the settings and quantities accessible via `BasicATLAS` are but a small subset of the input flags and intermediate output scattered throughout some $20000$ lines of the original Fortran code.

This document is my personal collection of notes on accessing the features of `ATLAS` beyond the ones offered in `BasicATLAS`. The approaches presented here will require direct editing of the `ATLAS` source code and would be likely considered exceptionally ugly by most, which is the main reason why these features are not implemented in `BasicATLAS` directly. Furthermore, the source code of `ATLAS` has very few comments and a lot of redundancy, which means that I am unable to guarantee that anything in this document is correct, although I took care to test the results where possible. A reader with a better understanding of `ATLAS` than my own is encouraged to check this document for mistakes and open GitHub issues to report their findings.
## Editing ATLAS
The download script (`download.com`) places the source code of `ATLAS-9` in `src/atlas9mem.for`. However, the actual code used by `BasicATLAS` is a modified version of the original stored in `src/atlas9mem.patched.for`. To customize your copy of `ATLAS`, first carry out the necessary edits in the patched file. The file must then be compiled into `bin/atlas9mem.exe` (check `compile.com` for the most up-to-date compiler instruction):
```bash
gfortran -o bin/atlas9mem.exe src/atlas9mem.patched.for -finit-local-zero -fno-automatic -w -std=legacy
```
The source code can be reset either by a complete re-install:
```
source clean.com
source download.com
source compile.com
```
or by re-applying the patch manually: see the block of instructions in `compile.com` immediately above the compiler instruction for `src/atlas9mem.patched.for`.
## Extending the wavelength grid
`ATLAS` carries out all frequency integrals over a grid of $337$ wavelength points between $~9\ \mathrm{nm}$ and $160\ \mathrm{micron}$ (this is the so-called *big* grid: a finer *little* grid is also available). At very high temperatures, a significant fraction of the radiation field may fall below the short cut-off, making the output inaccurate. `BasicATLAS` checks for this after every calculation and displays the following error whenever it believes the wavelength grid to be inappropriate:
```
Planck's law / derivative of Planck's law in one of the layers at temperature *** K does not vanish at the frequency grid bound *** Hz. The result may be inaccurate!
```
However, `BasicATLAS` does not offer any solution to this issue. The grid points are stored in the variables `WBIG1`, `WBIG2` and `WBIG3`, defined in `SUBROUTINE BLOCKR`. When changing the grid points, I strongly recommend keeping the total number of points unchanged ($337$) as this dimension is hard-coded all over the place. I wrote the following Python code for myself that generates the Fortran definitions of `WBIG*`:
```python
template = '      DATA WBIG1/\n     1{},{},{},{},{},{},{},{},\n     2{},{},{},{},{},{},{},{},\n     3{},{},{},{},{},{},{},{},\n     4{},{},{},{},{},{},{},{},\n     5{},{},{},{},{},{},{},{},\n     6{},{},{},{},{},{},{},{},\n     7{},{},{},{},{},{},{},{},\n     8{},{},{},{},{},{},{},{},\n     9{},{},{},{},{},{},{},{},\n     A{},{},{},{},{},{},{},{},\n     1{},{},{},{},{},{},{},{},\n     2{},{},{},{},{},{},{},{},\n     3{},{},{},{},{},{},{},{},\n     4{},{},{},{},{},{},{},{},\n     5{},{},{},{},{},{},{},{},\n     6{},{},{},{},{},{},{},{},\n     7{},{},{},{},{},{},{},{},\n     8{},{},{},{},{},{},{},{},\n     9{},{},{},{},{},{},{},{}/\n      DATA WBIG2/\n     1{},{},{},{},{},{},{},{},\n     2{},{},{},{},{},{},{},{},\n     3{},{},{},{},{},{},{},{},\n     4{},{},{},{},{},{},{},{},\n     5{},{},{},{},{},{},{},{},\n     6{},{},{},{},{},{},{},{},\n     7{},{},{},{},{},{},{},{},\n     8{},{},{},{},{},{},{},{},\n     9{},{},{},{},{},{},{},{},\n     A{},{},{},{},{},{},{},{},\n     1{},{},{},{},{},{},{},{},\n     2{},{},{},{},{},{},{},{},\n     3{},{},{},{},{},{},{},{},\n     4{},{},{},{},{},{},{},{},\n     5{},{},{},{},{},{},{},{},\n     6{},{},{},{},{},{},{},{},\n     7{},{},{},{},{},{},{},{},\n     8{},{},{},{},{},{},{},{},\n     9{},{},{},{},{},{},{},{}/\n      DATA WBIG3/\n     1{},{},{},{},{},{},{},{},\n     2{},{},{},{},{},{},{},{},\n     3{},{},{},{},{},{},{},{},\n     4{},{},{},\n     5{},{},{},{},{},{}/'
wls = ['   9.09', '   9.35', '   9.61', '   9.77', '   9.96', '  10.20', '  10.38', '  10.56', '  10.77', '  11.04', '  11.40', '  11.78', '  12.13', '  12.48', '  12.71', '  12.84', '  13.05', '  13.24', '  13.39', '  13.66', '  13.98', '  14.33', '  14.72', '  15.10', '  15.52', '  15.88', '  16.20', '  16.60', '  17.03', '  17.34', '  17.68', '  18.02', '  18.17', '  18.61', '  19.10', '  19.39', '  19.84', '  20.18', '  20.50', '  21.05', '  21.62', '  21.98', '  22.30', '  22.68', '  23.00', '  23.40', '  24.00', '  24.65', '  25.24', '  25.68', '  26.00', '  26.40', '  26.85', '  27.35', '  27.85', '  28.40', '   29.0', '   29.6', '   30.1', '   30.8', '   31.8', '   32.8', '   33.8', '   34.8', '   35.7', '   36.6', '   37.5', '   38.5', '   39.5', '   40.5', '   41.4', '   42.2', '   43.0', '   44.1', '   45.1', '   46.0', '   47.0', '   48.0', '   49.0', '   50.0', '   50.6', '   51.4', '   53.0', '   55.0', '   56.7', '   58.5', '   60.5', '   62.5', '   64.5', '   66.3', '   68.0', '   70.0', '   71.6', '   73.0', '   75.0', '   77.0', '   79.0', '   81.0', '   83.0', '   85.0', '   87.0', '   89.0', '   90.6', '   92.6', '   96.0', '  100.0', '  104.0', '  108.0', '  111.5', '  114.5', '  118.0', '  122.0', '  126.0', '  130.0', '  134.0', '  138.0', '  142.0', '  146.0', '  150.0', '  154.0', '  160.0', '  165.0', '  169.0', '  173.0', '  177.5', '  182.0', '  186.0', '  190.5', '  195.0', '  200.0', '  204.5', '  208.5', '  212.5', '  217.5', '  222.5', '  227.5', '  232.5', '  237.5', '  242.5', '  248.0', '  253.0', '  257.5', '  262.5', '  267.5', '  272.5', '  277.5', '  282.5', '  287.5', '  295.0', '  305.0', '  315.0', '  325.0', '  335.0', '  345.0', '  355.0', '  362.0', '  367.0', '  375.0', '  385.0', '  395.0', '  405.0', '  415.0', '  425.0', '  440.0', '  455.0', '  465.0', '  475.0', '  485.0', '  495.0', '  505.0', '  515.0', '  525.0', '  535.0', '  545.0', '  555.0', '  565.0', '  575.0', '  585.0', '  595.0', '  605.0', '  615.0', '  625.0', '  635.0', '  645.0', '  655.0', '  665.0', '  675.0', '  685.0', '  695.0', '  705.0', '  715.0', '  725.0', '  735.0', '  745.0', '  755.0', '  765.0', '  775.0', '  785.0', '  795.0', '  805.0', '  815.0', '  825.0', '  835.0', '  845.0', '  855.0', '  865.0', '  875.0', '  885.0', '  895.0', '  905.0', '  915.0', '  925.0', '  935.0', '  945.0', '  955.0', '  965.0', '  975.0', '  985.0', '  995.0', ' 1012.5', ' 1037.5', ' 1062.5', ' 1087.5', ' 1112.5', ' 1137.5', ' 1162.5', ' 1187.5', ' 1212.5', ' 1237.5', ' 1262.5', ' 1287.5', ' 1312.5', ' 1337.5', ' 1362.5', ' 1387.5', ' 1412.5', ' 1442.0', ' 1467.0', ' 1487.5', ' 1512.5', ' 1537.5', ' 1562.5', ' 1587.5', ' 1620.0', ' 1660.0', ' 1700.0', ' 1740.0', ' 1780.0', '  1820.', '  1860.', '  1900.', '  1940.', '  1980.', '  2025.', '  2075.', '  2125.', '  2175.', '  2225.', '  2265.', '  2290.', '  2325.', '  2375.', '  2425.', '  2475.', '  2525.', '  2575.', '  2625.', '  2675.', '  2725.', '  2775.', '  2825.', '  2875.', '  2925.', '  2975.', '  3025.', '  3075.', '  3125.', '  3175.', '  3240.', '  3340.', '  3450.', '  3550.', '  3650.', '  3750.', '  3850.', '  3950.', '  4050.', '  4150.', '  4250.', '  4350.', '  4450.', '  4550.', '  4650.', '  4750.', '  4850.', '  4950.', '  5050.', '  5150.', '  5250.', '  5350.', '  5450.', '  5550.', '  5650.', '  5750.', '  5850.', '  5950.', '  6050.', '  6150.', '  6250.', '  6350.', '  6500.', '  6700.', '  6900.', '  7100.', '  7300.', '  7500.', '  7700.', '  7900.', '  8100.', '  8300.', '  8500.', '  8700.', '  8900.', '  9100.', '  9300.', '  9500.', '  9700.', '  9900.', ' 10000.', ' 20000.', ' 40000.', ' 60000.', ' 80000.', '100000.', '120000.', '140000.', '160000.']

wls = ['   8.00', '   7.00', '   6.00', '   5.00', '   4.00', '   3.00', '   2.00', '   1.00', '    0.1'][::-1] + wls[:-9]
new_grid = template.format(*wls)

print(new_grid)
```
Here, the grid is extended by 9 points to $0.1\ \mathrm{nm}$ at the expense of the 9 longest wavelengths in the original grid that are removed to maintain the total number of points.

`ATLAS` stores frequency weights that are used to evaluate the integration coefficients for each frequency bin in the `RCOSET` variable (here `FRESET` are the integration frequencies in Hz):

```fortran
      DO 2222 NU=2,NUMNU-1
 2222 RCOSET(NU)=(FRESET(NU-1)-FRESET(NU+1))/2.
      RCOSET(1)=(2.997925D17/8.97666-FRESET(2))/2.
      RCOSET(NUMNU)=FRESET(NUMNU-1)/2.
```
Note that the first weight (`RCOSET(1)`) is calculated from the hard-coded shortest wavelength of $8.97666\ \mathrm{nm}$. This wavelength appears to be a residual from some old wavelength grid defined in `SUBROUTINE BLOCKBIG` that is no longer used. I am not sure if this is a mistake in the code. While, in principle, one could change the hard-coded wavelength to the actual shortest wavelength in the grid, the contribution of the corresponding frequency bin is usually not significant. It does however lead to a negative integration coefficient when the grid is extended beyond the hard-coded wavelength, which may cause some confusion.
## Extending the ODF temperature range
The opacity distribution functions (ODFs) are pre-tabulated by `BasicATLAS` at $57$ temperatures from $1995\ \mathrm{K}$ to $199526\ \mathrm{K}$ according to the "new" ODF format by Fiorella Castelli. The full set of temperatures is hard-coded in `BasicATLAS` in the `dfts` variable within `atlas.dfsynthe()`. As with the wavelength grid, ultrahigh or ultralow temperature atmospheres may be exceeding the ODF temperature range, in which case `BasicATLAS` should report the following error:

```
Gas temperature *** K  in one of the layers falls outside the ODF range [***, ***]. The result may be inaccurate!
```
As before, the solution involves editing the source code. First, change the definition of `dfts` in `BasicATLAS` to include new temperature points but keep the length of the list the same ($57$). I usually add a few extra temperatures at the end and remove the same number of temperatures from the beginning of the list. When choosing the step size between the new temperature points, you may adopt the same uniform logarithmic sampling as the default set at the high temperature end: each subsequent temperature is $12.2\%$ ($0.05\ \mathrm{dex}$) higher than the previous one.

Once the new temperature grid is in place, the ODFs may be re-calculated as usual with `atlas.dfsynthe()`. Now we must carry over the new temperatures into `ATLAS`. All ODF temperatures are stored in the `TABT`, defined inside `SUBROUTINE LINOP`. The default definition looks as follows:
```fortran
      DATA TABT/3.30,3.32,3.34,3.36,3.38,3.40,3.42,3.44,3.46,3.48,3.50,
	1 3.52,
     1 3.54,3.56,3.58,3.60,3.62,3.64,3.66,3.68,3.70,3.73,3.76,3.79,3.82,
     2 3.85,3.88,3.91,3.94,3.97,4.00,4.05,4.10,4.15,4.20,4.25,4.30,4.35,
     3 4.40,4.45,4.50,4.55,4.60,4.65,4.70,4.75,4.80,4.85,4.90,4.95,5.00,
     4 5.05,5.10,5.15,5.20,5.25,5.30/
```
All $57$ temperatures are listed as base-10 logarithms of their Kelvin values. You must make sure that the values match your ODFs. Note that `BasicATLAS` does not check whether the temperature grid in the ODF matches the one expected by `ATLAS`: the results will be wrong if they do not!
## Retrieving ATLAS spectra
While `ATLAS` is not designed for calculating synthetic spectra (`SYNTHE` is), a low-resolution version of the radiation field is calculated in every layer as part of the model calculation. A low-resolution emergent spectrum may be retrieved by extracting the flux in the outermost layer of the star. I personally resort to this approach whenever I am trying to understand how a particular parameter (e.g. certain opacity type being on or off) affects the final spectrum without having to wait for the `SYNTHE` calculation each time and, more importantly, without having to figure out how to apply the same parameter to the `SYNTHE` calculation which I find to be a much harder code to read than `ATLAS`.

The radiation field in `ATLAS` is computed by `SUBROUTINE JOSH`. The subroutine is called from line 348 as follows:
```fortran
C
   60 N=0
      CALL KAPP(N,NSTEPS,STEPWT)
c      do 7000 j=1,nrhox
c      write(6,6663)j,acont(j),scont(j),aline(j),sline(j),sigmac(j),
c     1 sigmal(j) 
c 6663 format(1x,i5,1p6e10.3)
c 7000 continue
      CALL JOSH(IFSCAT,IFSURF,freq)
```
Immediately after the subroutine call, add the following line of Fotran:
```fortran
      write(*,*) 'otgn_flx',freq,HNU(1)
```
Here, we are writing into the main output file a string of characters (I chose `otgn_flx` here, but could be anything) as a marker to find this output later, followed by the frequency point being evaluated, followed by the surface Eddington flux $H_\nu$. After re-compiling `ATLAS` and running your model, you may use the following Python code to extract the emergent spectrum:
```python
f = open('path_to_your_run_dir/output_main.out', 'r')
content = f.readlines()
f.close()
spectrum = []
for line in content[::-1]:
    if line.find('otgn_flx') == -1:
        if len(spectrum) == 337:
            break
        else:
            continue
    spectrum += [line]
freq, surfi = np.loadtxt(spectrum, usecols = [1, 2], unpack = True)
wl = spc.c / freq
flux = spc.c / (wl ** 2.0) * surfi
sort = np.argsort(wl)
wl = wl[sort] * 1e10; flux = flux[sort] * 4e-10
```
The code uses our marker (`otgn_flx`) to find the output of the newly added line, loads it in with `np.loadtxt()` and carries out some algebra to convert the spectrum from frequency to wavelength and to express it in the same units as the output of `atlas.read_spectrum()` (wavelength in Angstroms, flux in CGS per Angstrom per steradian; technically, this is specific intensity).

The resultant spectrum will only include continuum features and may not match the output of `SYNTHE` perfectly; however, it should capture the basic energy distribution across the wavelength range which is often sufficient.
## Toggling opacities
Individual opacity contributions can be toggled on and off. Find the following code in `SUBROUTINE TURB`:

```fortran
IF(IFOP(1).EQ.1)CALL HOP
IF(IFOP(2).EQ.1)CALL H2PLOP
IF(IFOP(3).EQ.1)CALL HMINOP
IF(IFOP(4).EQ.1)CALL HRAYOP
IF(IFOP(5).EQ.1)CALL HE1OP
IF(IFOP(6).EQ.1)CALL HE2OP
IF(IFOP(7).EQ.1)CALL HEMIOP
IF(IFOP(8).EQ.1)CALL HERAOP
IF(IFOP(9).EQ.1)CALL COOLOP
IF(IFOP(10).EQ.1)CALL LUKEOP
IF(IFOP(11).EQ.1)CALL HOTOP
IF(IFOP(12).EQ.1)CALL ELECOP
IF(IFOP(13).EQ.1)CALL H2RAOP
IF(IFOP(14).EQ.1.AND.N.GT.0)CALL HLINOP
IF(IFOP(15).EQ.1.AND.N.GT.0)CALL LINOP(N,NSTEPS,STEPWT)
IF(IFOP(16).EQ.1.AND.N.GT.0)CALL LINSOP(N,NSTEPS,STEPWT)
IF(IFOP(17).EQ.1.AND.N.GT.0)CALL XLINOP
IF(IFOP(18).EQ.1.AND.N.GT.0)CALL XLISOP
IF(IFOP(19).EQ.1)CALL XCONOP
IF(IFOP(20).EQ.1)CALL XSOP
```

Each line corresponds to a particular opacity contribution. For example, `HOP` is responsible for the bound-free and free-free hydrogen opacities, `HE1OP` for the bound-free and free-free neutral helium opacities, `ELECOP` is Thomson scattering etc. The full list may be found in section 5 of the [ATLAS manual](https://ui.adsabs.harvard.edu/abs/1970SAOSR.309.....K/abstract). Note that the manual is slightly outdated as it does not cover any of the ODF-drived opacities. To disable any particular opacity, simply comment out or remove the corresponding line. In principle, this may also be accomplished by setting the `IFOP` flags in the main input. If more precision is required (e.g. we may only want to disable free-free hydrogen opacity but not bound-free), feel free to look at the individual opacity subroutines in detail. For example, the following is a snippet from `SUBROUTINE HOP`:

```fortran
      DO 15 J=1,NRHOX
      DO 11 N=1,8
   11 BOLT(J,N)=EXP(-(13.595-13.595/DFLOAT(N*N))/TKEV(J))*2.*
     1DFLOAT(N*N)*XNFPH(J,1)/RHO(J)
      DO 12 N=1,6
   12 BOLT(J,N)=BOLT(J,N)*BHYD(J,N)
      FREET(J)=XNE(J)*XNFH(J,2)/RHO(J)/SQRT(T(J))
      XR=XNFPH(J,1)*(2./2./13.595)*TKEV(J)/RHO(J)
      BOLTEX(J)=EXP(-13.427/TKEV(J))*XR
   15 EXLIM(J)=EXP(-13.595/TKEV(J))*XR
   20 DO 21 N=1,8
C   21 CONT(N)=COULX(N,FREQ,1.D0)
   21 CONT(N)=XKARSAS(FREQ,1.D0,N,N)
      FREQ3=FREQ**3
      CFREE=3.6919D8/FREQ3
      C=2.815D29/FREQ3
      DO 32 J=1,NRHOX
      EX=BOLTEX(J)
      IF(FREQ.LT.4.05933D13)EX=EXLIM(J)/EHVKT(J)
      H=(CONT(7)*BOLT(J,7)+CONT(8)*BOLT(J,8)+(EX-EXLIM(J))*C+
     1COULFF(J,1)*FREET(J)*CFREE)*STIM(J)
      S=H*BNU(J)
      DO 31 N=1,6
      H=H+CONT(N)*BOLT(J,N)*(1.-EHVKT(J)/BHYD(J,N))
   31 S=S+CONT(N)*BOLT(J,N)*BNU(J)*STIM(J)/BHYD(J,N)
      AHYD(J)=H
   32 SHYD(J)=S/H
      RETURN
```
The final opacity is saved in the `H` variable and is made of three contributions. Here `BOLT(J,N)` controls the bound-free hydrogen opacity from the energy level `N`. To disable, for example, the Balmer break in the spectrum, we may add
```fortran
BOLT(J,2)=0.0
```
before the term is added to `H`. Bound-free opacities for levels higher than $8$ are computed as a single integral, modulated by `(EX-EXLIM(J))*C`. Multiplying this quantity by some small number (e.g. $0.001$) would disable this opacity as well. Finally, the free-free opacity is modulated by `COULFF(J,1)`. As before, multiplying the corresponding term in `H` by a small number would disable the free-free opacity as well. Note that multiplying terms by small numbers of setting them to zero is sometimes preferred as null opacities may cause errors further down the line. Refer to the `ATLAS` manual to work out which part of the code controls which opacity source.
## Retrieving the source function
The source function ($S_\nu$) is the main measure of interaction between radiation and matter and is defined at all frequencies and in every layer of the atmosphere (i.e. it is a $337\times72$ matrix, where $337$ is the number of frequencies in the *big* grid and $72$ is the number of layers in the stratification). In LTE, $S_\nu$ follows Planck's law ($S_\nu=B_\nu$); however, at shallow optical depths and high effective temperatures, prominent departures from LTE may be observed due to the scattering contribution to $S_\nu$. I like looking at the source function of my models to get an idea for how exactly radiation flows through the atmosphere.

Retrieving the source function can be accomplished with the same trick we used to extract the emergent spectrum. Add the following line after `JOSH`:

```fortran
write(*,*) 'src_fctn',freq,SNU
```

This is the same line as before, except the marker text is now set to `src_fctn` and instead of printing the Eddington flux, we are printing the source function (`SNU`). You may then use the following Python code to load the source function in:
```python
f = open('path_to_your_run_dir/output_main.out', 'r')
content = f.readlines()
f.close()
spectrum = []
for line in content[::-1]:
    if line.find('src_fctn') == -1:
        if len(spectrum) == 337:
            break
        else:
            continue
    spectrum += [line]
snu = np.loadtxt(spectrum, unpack = True, dtype = str)
freq = snu[1].astype(float)
snu = snu[2:74].astype(float)
wl = spc.c / freq
flux = spc.c / (wl ** 2.0) * snu
sort = np.argsort(wl)
wl = wl[sort] * 1e10; flux = flux.T[sort].T * 1e-10
```
As before, the code merely reads the output of the new line identified by the marker text and then converts the units into CGS per Angstrom. The output is stored in the `flux` variable that is a matrix with the correct dimensions.
