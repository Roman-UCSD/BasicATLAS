# BasicATLAS

## Introduction

**ATLAS-9** is a Fortran stellar modelling code published by RL Kurucz in 1993. The purpose of the package is to iteratively determine profiles of atmospheric parameters such as temperature and pressure for a star of given physical characteristics. **ATLAS-9** is normally used in conjunction with other related codes, most notably including:

* **SYNTHE**. A suite of programs for calculating a model spectrum for an ATLAS atmosphere.
* **DFSYNTHE**. A code to pre-compute opacity distribution functions which are required for any ATLAS run.
* **KAPPAROS**. A calculator for Rosseland mass absorption coefficients, also required for any ATLAS run.

Most of the source code as well as necessary supporting files can be downloaded from [Fiorella Castelli's website](http://wwwuser.oats.inaf.it/castelli/). The website also accumulates the most essential installation instructions. The [ATLAS cookbook](http://wwwuser.oats.inaf.it/castelli/) is another web resource, covering a complete ATLAS run in its pure form.

Unfortunately, even the most basic ATLAS model requires arduous preparation and is incredibly hard to troubleshoot. The package relies on control scripts with unobvious structures and often fails to deliver a meaningful error report when it crashes.

**BasicATLAS** is a Python script that was written to simplify the process and run the entire ATLAS pipeline (**DFSYNTHE**, **KAPPAROS** followed by **ALAS-9** and **SYNTHE**) with very little preparation and in a few simple terminal commands. Of course, this simplicity comes at a cost of limiting an otherwise powerful package to a handful of most basic cases.

## Requirements

* A Linux-like shell environment (on Windows, use [CygWin](https://www.cygwin.com/)).
* Fully downloaded and compiled copies of **ATLAS-9**, **SYNTHE**, **DFSYNTHE** and **KAPPAROS**. **BasicATLAS** comes with a routine to check the setup completeness automatically.
* Python 2.7 with **PExpect** and **PyPNG**.

## Installation

1. Download `basic.py`, `settings.py`, `templates.py` and `wavelength.py` and save them all in a single directory.
2. Edit `basic.py` and change the values of the variables defined at the top of the file (`molecules`, `s_data`, `d_data` etc) to point to the corresponding parts of the local ATLAS setup. If this step is unclear, run the automated completeness test in step 3 first.
3. Navigate the directory of `basic.py` in a Linux-like terminal and run a completeness test with `python basic.py test_setup`. The command should return no output if the setup is complete. Otherwise, follow the instructions in the output to fix. Note that this test is experimental and may both show issues that are not important or fail to show those that are. There is no harm in trying to run ATLAS even if the test is not passed.

## Running ATLAS

1. Edit `settings.py` and find `atlas_settings()`. It should look similar to below:

```python
	config['teff']             =    5400
	config['gravity']          =    4.75
	config['abundance_scale']  =    10.0 ** (-1.7)
	config['elements'][1]      =    0.8528
	config['elements'][2]      =    0.1459
	config['elements'][6]     +=    -0.65
	config['elements'][7]     +=    +1.45
	config['elements'][8]     +=    -0.1
```

2. Edit the settings as necessary. `config['teff']` sets the temperature of the atmosphere. ATLAS may not work for stars cooler than 4000 K. `config['gravity']` and `config['abundance_scale']` set the surface gravity (log(g)) and metallicity. Individual abundances of elements follow, where hydrogen and helium are expressed as particle number fractions and the rest are specified with respect to solar abundances on a logarithmic scale.

3. Navigate your terminal to the directory of `basic.py`.
4. Initiate a new ATLAS run with `basic.py initialize 1000`, where `1000` is any unique number. A new folder called `run_1000` should appear in the directory.
5. Run **DFSYNTHE** to generate opacity distribution functions with `python basic.py dfsynthe 1000`, where `1000` is the run number. When finished, the ODF will be saved in `p00bigV.bdf` inside the run directory.
6. Run **KAPPAROS**. `python basic.py kapparos 1000`. When finished, the output will be saved in `kappa.ros`. Both steps 5 and 6 only need to be done once for every set of abundances.
7. Initiate a new run with `basic.py initialize 2000`, where `2000` is a unique number, different to the one we used for **DFSYNTHE** and **KAPPAROS**.
8. Copy `p00bigV.bdf` and `kappa.ros` into the new run directory. Rename the former into `odf_9.bdf` and the latter into `odf_1.ros`.
9. Run **ATLAS** with `python basic.py 2000 auto 0`. `auto` tells **BasicATLAS** to choose the initial model automatically and `0` tells **BasicATLAS** to choose the number of iterations automatically. This command has many optional arguments that may be of interest for more advanced runs. See the docstring of `atlas()` in `basic.py` for details.
10. When finished, run **SYNTHE** with `python basic.py synthe 2000 200 1200`, where `200-1200` is the range of wavelengths of interest (in A).
11. Now the model atmosphere is in `model.dat` and the spectrum is in `spectrum.dat`. Refer to the comments at the top of those files for column names and units.
12. Generate a visual representation of the spectrum with `python basic.py visualize_spectrum 2000 800 100`, where `800` and `100` are the desired width and height. An image called `spectrum.png` will be generated in the run directory.
13. Run `python basic.py bolometry 2000` to compute the bolometric corrections for the spectrum. This function also has many optional parameters that are detailed in the associated docstring.
