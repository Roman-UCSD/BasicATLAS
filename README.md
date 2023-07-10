# BasicATLAS

This project is a simple Python wrapper for the **ATLAS** LTE stellar modelling code by [Robert L Kurucz](http://kurucz.harvard.edu/) as well as satellite utilities including the spectral synthesis library **SYNTHE** and opacity distribution (ODF) calculator **DFSYNTHE**. Refer to the literature references below:

* [Kurucz (1970)](https://ui.adsabs.harvard.edu/abs/1970SAOSR.309.....K/abstract): detailed description of an older version of the code (version 5)
* [Kurucz et al. (1974)](https://ui.adsabs.harvard.edu/abs/1974bmae.book.....K/abstract): more on opacity distribution functions
* [Kurucz & Avrett (1981)](https://ui.adsabs.harvard.edu/abs/1981SAOSR.391.....K/abstract): standard reference for the **SYNTHE** code
* [Castelli & Kurucz (2003)](https://ui.adsabs.harvard.edu/abs/2003IAUS..210P.A20C/abstract): description of the "new" ODF format, currently used by **ATLAS**
* [Castelli (2005)](https://ui.adsabs.harvard.edu/abs/2005MSAIS...8...34C/abstract): user guide to **DFSYNTHE**
* [Kurucz (2005a)](https://ui.adsabs.harvard.edu/abs/2005MSAIS...8...14K/abstract): more information on modern versions of **ATLAS** as well as **SYNTHE**
* [Kurucz 2005b](https://ui.adsabs.harvard.edu/abs/2005MSAIS...8...86K/abstract): bound-bound (line) opacity treatment in the code and line lists
* [Kurucz (2014)](https://ui.adsabs.harvard.edu/abs/2014dapb.book...39K/abstract): brief overview of the modern versions of the code (9 and 12)

Also see the websites of [Robert L Kurucz](http://kurucz.harvard.edu/programs.html) and [Fiorella Castelli](https://wwwuser.oats.inaf.it/castelli/).

**ATLAS 9** and **ATLAS 12** differ in the opacity sampling method (opacity distribution functions vs direct sampling) which results in the former being considerably faster and, in principle, somewhat less accurate although (to my understanding) the significance of the uncertainty introduced by the chosen opacity treatment is not well established. **BasicATLAS** works with **ATLAS 9** (support for **ATLAS 12** may be added in the future).

If you are using **BasicATLAS** in your research, please cite [Larkin et al. (2022)](https://arxiv.org/abs/2210.09185)

## Contributors

* Roman Gerasimov (University of California San Diego)
* Mikaela Larkin (University of California San Diego)
* Tianxing Zhou (University of California San Diego)
* Philipp Edelmann (Los Alamos National Laboratory) @ [AAS 242](https://aas.org/meetings/aas242) Hack Together
* Paul Barrett (George Washington University) @ [AAS 242](https://aas.org/meetings/aas242) Hack Together

## Installation

This repository does not contain the source code of **ATLAS** or any of the required data files (e.g. line lists). Both must be downloaded from the websites listed above. A download script is provided using `wget` that works at the time of writing (10/21/2022). A test script is provided to ensure that all the necessary files are present and have correct MD5 checksums.

After cloning the repository, confirm that both GNU and Intel Fortran compilers are available in your environment.

```bash
$ ifort --version
ifort (IFORT) 2021.3.0 20210609
Copyright (C) 1985-2021 Intel Corporation.  All rights reserved.

$ gfortran --version
GNU Fortran (Ubuntu 7.4.0-1ubuntu1~18.04.1) 7.4.0
Copyright (C) 2017 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
```

Intel compilers are currently available as a part of the [oneAPI HPC Toolkit](https://software.intel.com/content/www/us/en/develop/tools/oneapi/hpc-toolkit/download.html) for all major operating systems (I have even been fully successful running **ATLAS-9** on Windows).

In the directory of the repository, first run the download script to fetch all data files and missing source code:

```bash
source download.com
```

The download involves multiple gigabytes of data and may take a few minutes. Please check that no errors are reported in the process. When the download completes, compile all Fortran source code with:

```bash
source compile.com
```

The script will also carry out a few necessary rearrangements ("[repacking](https://wwwuser.oats.inaf.it/castelli/sources/dfsynthe.html)") of line lists.

Finally, run the test script to make sure the installation was successful:

```bash
python test.py
```

The test is clean if no output is produced.

## Examples

* [Constructing the simplest model with solar parameters](https://github.com/Roman-UCSD/BasicATLAS/blob/master/examples/sun_model.ipynb)
* [Interpreting the detailed output of ATLAS and SYNTHE](https://github.com/Roman-UCSD/BasicATLAS/blob/master/examples/output.ipynb)
* [Calculating opacity distribution functions and using them for non-solar abundances](https://github.com/Roman-UCSD/BasicATLAS/blob/master/examples/custom_abun.ipynb)
* [Managing restart files to improve model convergence](https://github.com/Roman-UCSD/BasicATLAS/blob/master/examples/restarts.ipynb)
* [Advanced features and settings](https://github.com/Roman-UCSD/BasicATLAS/blob/master/examples/advanced.md)

## MacOS Installation

In order to use Intel Fortran, both the [oneAPI Base Toolkit](https://software.intel.com/content/www/us/en/develop/tools/oneapi/base-toolkit/download.html) and the [oneAPI HPC Toolkit](https://software.intel.com/content/www/us/en/develop/tools/oneapi/hpc-toolkit/download.html) will need to be installed first.

After following the installation steps, the toolkits will need to be initialized using:

```bash
. /opt/intel/oneapi/setvars.sh
```

Homebrew will then need to be installed in order to use GNU Fortran:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

The terminal will then prompt you to input your password before beginning the download. 

Once Homebrew has finished downloading, install GNU Fortran using:

```bash
brew install gcc
```

Before continuing on to downloading scripts, `wget` will also need to be installed with Homebrew:

```bash
brew install wget
```

The download and compilation scripts should then be able to run as shown above.

## Windows OS Installation

To install BasicATLAS on Windows, it is recommended that you install and work in the [Windows Ubuntu app](https://apps.microsoft.com/store/detail/ubuntu/9PDXGNCFSCZV). After installing, you will need to install the Intel Fortran compiler (ifort) specifically for Ubuntu. To do this, you can refer to the provided [steps](https://gist.github.com/SomajitDey/aeb6eb4c8083185e06800e1ece4be1bd) for guidance on installing ifort on Ubuntu. In case the link does not work, here are the following instructions:

1. `curl -Lo- https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB | sudo gpg --dearmor -o /usr/share/keyrings/oneapi-archive-keyring.gpg`
2. `sudo tee /etc/apt/sources.list.d/oneAPI.list <<< "deb [signed-by=/usr/share/keyrings/oneapi-archive-keyring.gpg] https://apt.repos.intel.com/oneapi all main"`
3. `sudo apt update`
4. `sudo apt install intel-oneapi-compiler-fortran`
5. Optional: `sudo apt install intel-oneapi-mkl`
6. In `~/.bashrc`: `source /opt/intel/oneapi/setvars.sh > /dev/null`

Once you have successfully completed these installation steps for ifort, you can start with the cloning repository of the installation section and continue with the rest of the steps.
