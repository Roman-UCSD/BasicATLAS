#############################################################
#                                                           #
#                          PyTLAS                           #
#                                                           #
#  PyTLAS (Python ATLAS) is a sub-module within BasicATLAS  #
#  that uses a modified SYNTHE suite (XNFPELSYN, SYNTHE,    #
#  SPECTRV) that runs entirely in memory and is compiled    #
#  as Shared Object (*.so) libraries that can be accessed   #
#  from Python (using the Python functions defined in this  #
#  script, PyTLAS.py). This modified SYNTHE suite is        #
#  significantly faster than the original codes and can be  #
#  used in spectral fitting.                                #
#                                                           #
#############################################################

import numpy as np
import ctypes
import types
import os
import scipy.constants as spc

python_path = os.path.dirname(os.path.realpath(__file__))

# Check that all SO libraries are available
required = ['bin/xnfpelsyn.so', 'bin/synthe.so', 'bin/spectrv.so']
for filename in required:
    if not os.path.isfile('{}/{}'.format(python_path, filename)):
        raise ValueError('{} not compiled. Run compile.com first'.format(filename))

# Check that all data files are available
required = ['../data/synthe_files/continua.dat', '../data/synthe_files/molecules.dat', '../data/synthe_files/he1tables.dat']
for filename in required:
    if not os.path.isfile('{}/{}'.format(python_path, filename)):
        raise ValueError('{} not found. Check BasicATLAS installation'.format(filename))

def load_text(filename, maxlen = 80):
    """Load a text file as array of bytes
    
    The output dimensions are MxN where M is the number of lines in the text file and N
    is the fixed number of characters per line specified in `maxlen`. All lines shorter than
    `maxlen` are padded with trailing spaces, and all lines longer than `maxlen` are truncated
    
    Parameters
    ----------
    filename : str
        Path to the text file
    maxlen : number, optional
        Fixed number of characters per line (defaults to 80, which is the value in ATLAS7V)
    
    Returns
    -------
    array_like
        Array of bytes
    """
    f = open(filename, 'r')
    lines = f.read().strip().split('\n')
    f.close()
    content = np.full((len(lines), maxlen), ord(' '), dtype = np.byte, order = 'F')
    for i, line in enumerate(lines):
        content[i,:min(len(line), content.shape[1])] = list(line.encode('ascii')[:content.shape[1]])
    return content

def load_f2(filename):
    """Load the chemical constants table (fort.2) from a text file
    
    Each line in the file is assumed to follow the F18.2,F7.3,6E11.4, where the first value is the
    Kurucz code of the species, the second value is the ionization potential and the rest of the
    values are the polynomial correction coefficients. Blank values are replaced with zeros. The output
    shape is MxN where M is the number of species and N is 8 corresponding to the format above
    
    Parameters
    ----------
    filename : str
        Path to the chemical constants file
    
    Returns
    -------
    array_like
        Double precision array of loaded values
    """
    def nanfloat(s):
        try:
            return float(s)
        except:
            return 0.0

    f = open(filename, 'r')
    lines = f.read().strip().split('\n')
    f.close()
    content = np.zeros((len(lines), 8), dtype = np.float64, order = 'F')
    for i, line in enumerate(lines):
        content[i,0] = nanfloat(line[:18])
        content[i,1] = nanfloat(line[18:25])
        for j in range(2, 8):
            content[i,j] = nanfloat(line[25 + (j - 2) * 11:25 + (j - 1) * 11])
    return content

def load_f18(filename):
    """Load the helium Stark broadening table (fort.2) from a text file
    
    Each line in the file is assumed to follow the 1X,F5.1,F8.2,8F7.3. The output
    shape is MxN where M is the number of species and N is 10 corresponding to the format above
    
    Parameters
    ----------
    filename : str
        Path to the table file
    
    Returns
    -------
    array_like
        Single precision array of loaded values
    """
    def nanfloat(s):
        try:
            return float(s)
        except:
            return np.nan

    f = open(filename, 'r')
    lines = f.read().strip().split('\n')
    f.close()
    content = np.zeros((len(lines), 10), dtype = np.float32, order = 'F')
    for i, line in enumerate(lines):
        content[i,0] = nanfloat(line[1:6])
        content[i,1] = nanfloat(line[6:14])
        for j in range(2, 10):
            content[i,j] = nanfloat(line[14 + (j - 2) * 7:14 + (j - 1) * 7])
    return content

def init_xnfpelsyn():
    """Initialize XNFPELSYN
    
    The XNFPELSYN code calculates the chemical equilibrium and continuum opacity in the atmosphere. The
    only input is the ATLAS model in the standard Kurucz format.

    This function loads the XNFPELSYN library, makes the necessary data files (fort.2 and fort.17) available
    to it, defines a structure to store the output and binds methods to push the ATLAS structure into the
    library and to run XNFPELSYN calculations
    
    Returns
    -------
    ctypes.CDLL
        XNFPELSYN library with `.load_structure()` and `.run()` methods bound to it
    """
    # Load the library
    lib = ctypes.CDLL('{}/{}'.format(python_path, 'bin/xnfpelsyn.so'))

    # Load continua.dat (fort.17)
    lib.f17 = load_text('{}/{}'.format(python_path, '../data/synthe_files/continua.dat'))
    lib.set_f17.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    pointer = lib.f17.ctypes.data_as(ctypes.c_void_p)
    lib.set_f17(pointer, lib.f17.shape[0], lib.f17.shape[1])

    # Load molecules.dat (fort.2)
    lib.f2 = load_f2('{}/{}'.format(python_path, '../data/synthe_files/molecules.dat'))
    lib.set_f2.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    pointer = lib.f2.ctypes.data_as(ctypes.c_void_p)
    lib.set_f2(pointer, lib.f2.shape[0], lib.f2.shape[1])

    # Link output arrays for XNFPELSYN
    lib.xnfpelsyn_output = {
        'teff_logg': np.zeros(2, dtype = np.float64, order = 'F'),
        'frqedg': np.zeros(344, dtype = np.float64, order = 'F'),
        'wledge': np.zeros(344, dtype = np.float64, order = 'F'),
        'cmedge': np.zeros(344, dtype = np.float64, order = 'F'),
        'idmol': np.zeros(100, dtype = np.float64, order = 'F'),
        'momass': np.zeros(100, dtype = np.float64, order = 'F'),
        'freqset': np.zeros(1029, dtype = np.float64, order = 'F'),
        'structure': np.zeros([16, 99], dtype = np.float64, order = 'F'),
        'continall': np.zeros([72, 1131], dtype = np.float64, order = 'F'),
        'contabs': np.zeros([72, 1131], dtype = np.float64, order = 'F'),
        'contscat': np.zeros([72, 1131], dtype = np.float64, order = 'F'),
        'xnfpel': np.zeros([72,139,6], dtype = np.float64, order = 'F'),
        'dopple': np.zeros([72,139,6], dtype = np.float64, order = 'F'),
    }
    lib.run_xnfpelsyn.argtypes = []
    for arg in lib.xnfpelsyn_output:
        lib.run_xnfpelsyn.argtypes += [np.ctypeslib.ndpointer(dtype = lib.xnfpelsyn_output[arg].dtype, ndim = lib.xnfpelsyn_output[arg].ndim, flags = 'F_CONTIGUOUS')]
    lib.run_xnfpelsyn.restype = None

    # Flag to check if XNFPELSYN has run
    lib.has_run = False

    # Bound method to load the ATLAS model into XNFPELSYN
    def load_structure(self, filename):
        self.f5 = load_text(filename)
        self.set_f5.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        pointer = self.f5.ctypes.data_as(ctypes.c_void_p)
        self.set_f5(pointer, self.f5.shape[0], self.f5.shape[1])
    lib.load_structure = types.MethodType(load_structure, lib)

    # Bound method to run XNFPELSYN
    def run(self):
        try:
            self.f5
        except:
            raise ValueError('XNFPELSYN does not have structure. Structure must be loaded with load_structure() first')
        self.run_xnfpelsyn(*[self.xnfpelsyn_output[field] for field in self.xnfpelsyn_output])
        lib.has_run = True
        self.xnfpelsyn_output
    lib.run = types.MethodType(run, lib)

    return lib

def load_linelist(linelist_dir):
    """Load the pre-computed linelist into memory
    
    This function loads the main linelist (fort.12, previously calculated with RGFALLLINESNEW, RMOLECASC and RH2OFAST),
    the NLTE linelist (fort.19) and the run meta data (fort.93, previously produced with SYNBEG) into memory
    
    Parameters
    ----------
    linelist_dir : str
        Path to the directory with fort.12, fort.19 and fort.93
    
    Returns
    -------
    f12: array_like
        Main line list
    f19: array_like
        NLTE line list
    meta : dict
        Dictionary of run meta data
    """
    # Load the linelist (fort.12)
    f = open('{}/fort.12'.format(linelist_dir), 'rb')
    dt = np.dtype('V4,i4,f4,i4,f4,f4,f4,f4,f4,V4')
    f12 = np.fromfile(f, dtype = dt, count = -1)
    f.close()

    # Load the NLTE linelist (fort.19)
    f = open('{}/fort.19'.format(linelist_dir), 'rb')
    dt = np.dtype('V4,i4,i4,f4,f4,i4,i4,i4,i4,i4,i4,f4,f4,f4,f4,i4,i4,V4')
    f19 = np.fromfile(f, dtype = dt, count = -1)
    f.close()

    f = open('{}/fort.93'.format(linelist_dir), 'rb')
    dt = np.dtype('V4,i4,i4,i4,i4,i4,f4,V2772,i4,f8,f8,f8,f8,f8,f4,i4,V4')
    meta = np.fromfile(f, dtype = dt, count = 1)
    f.close()
    assert meta['f4'][0] == 0         # Check that NLTE is disabled (SYNTHE does not do NLTE)
    assert meta['f8'][0] == 1         # Check that all lines are included
    assert meta['f15'][0] == -1       # Check that line output is disabled
    assert meta['f1'][0] == len(f12)  # Check the number of lines matches
    assert meta['f5'][0] == len(f19)  # Check the number of NLTE lines matches
    meta = {'n_lines': meta['f1'][0], 'n_wl': meta['f2'][0], 'ifvac': meta['f3'][0], 'n_lines_f19': meta['f5'][0],
            'wl_start': meta['f9'][0], 'wl_end': meta['f10'][0], 'res': meta['f11'][0], 'ratio': meta['f12'][0],
            'ratiolg': meta['f13'][0], 'cutoff': meta['f14'][0]}

    return f12, f19, meta

def init_synthe():
    """Initialize SYNTHE
    
    The SYNTHE code calculates the line opacity throughout the atmosphere. The code requires the output of XNFPELSYN
    as well as the linelist and the meta data. The linelist is made of two files: fort.12 that stores LTE lines and
    fort.19 that stores NLTE lines (usually hydrogen lines). Note that SYNTHE does not actually support NLTE, so both
    lists are treated the same way. The meta data includes the number of lines in both lists, the wavelength sampling
    parameters (start, end, step) and other settings including the turbulent velocity. The meta data (fort.93) is usually
    calculated at the same time as the linelist using the SYNBEG utility. In general, it does not make sense to update
    any of the meta data without recalculating the linelist, so we treat all three files (fort.12, fort.19 and fort.93)
    as a single linelist entity with one exception: the turbulent velocity must be specified by the user at the time
    when the linelist is being made available to SYNTHE using the bound `load_linelist()` method. This is because the
    turbulent velocity often needs to be adjusted from run to run without recalculating the linelist

    This function loads the SYNTHE library and binds methods to push the linelist and the XNFPELSYN output into the
    library, as well as a method to run the SYNTHE calculation
    
    Returns
    -------
    ctypes.CDLL
        SYNTHE library with `.load_linelist()`, `.load_xnfpelsyn()` and `.run()` methods bound to it
    """
    # Load the library
    lib = ctypes.CDLL('{}/{}'.format(python_path, 'bin/synthe.so'))

    # Flag to track if SYNTHE has run
    lib.has_run = False

    # Load he1tables.dat (fort.18)
    lib.f18 = load_f18('{}/{}'.format(python_path, '../data/synthe_files/he1tables.dat'))
    lib.set_f18.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    pointer = lib.f18.ctypes.data_as(ctypes.c_void_p)
    lib.set_f18(pointer, lib.f18.shape[0], lib.f18.shape[1])

    # Bound method to make the linelist (previously loaded with load_linelist()) and turbulent velocity available to SYNTHE
    def load_linelist(self, f12, f19, meta, vturb):
        self.f12 = f12
        pointer = self.f12.ctypes.data_as(ctypes.c_void_p)
        self.set_f12.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.set_f12(pointer, self.f12.shape[0])
        self.f19 = f19
        pointer = self.f19.ctypes.data_as(ctypes.c_void_p)
        self.set_f19.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.set_f19(pointer, self.f19.shape[0])
        self.meta = meta
        self.vturb = np.float32(vturb)
        self.set_f93.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_double, ctypes.c_double,
                                 ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_float, ctypes.c_float]
        self.set_f93(*[self.meta[key] for key in self.meta], self.vturb)

        # Now that we have access to the run meta data, we can create an appropriately sized output array for SYNTHE
        self.asynth = np.zeros([self.meta['n_wl'], 72], dtype = np.float32, order = 'F')
        self.set_asynth.argtypes = [ctypes.c_void_p, ctypes.c_int]
        pointer = self.asynth.ctypes.data_as(ctypes.c_void_p)
        self.set_asynth(pointer, self.meta['n_wl'])
    lib.load_linelist = types.MethodType(load_linelist, lib)

    # Bound method to make the output of XNFPELSYN available to SYNTHE
    def load_xnfpelsyn(self, xnfpelsyn):
        if not xnfpelsyn.has_run:
            raise ValueError('XNFPELSYN has not run yet')
        self.xnfpelsyn_output = xnfpelsyn.xnfpelsyn_output
        self.set_f10.argtypes = [ctypes.c_void_p for field in self.xnfpelsyn_output]
        self.set_f10(*[self.xnfpelsyn_output[field].ctypes.data_as(ctypes.c_void_p) for field in self.xnfpelsyn_output])
    lib.load_xnfpelsyn = types.MethodType(load_xnfpelsyn, lib)

    # Bound method to run SYNTHE
    def run(self):
        try:
            self.xnfpelsyn_output
        except:
            raise ValueError('SYNTHE does not have XNFPELSYN output')
        try:
            self.f12
        except:
            raise ValueError('SYNTHE does not have the linelist')
        self.run_synthe()
        lib.has_run = True
    lib.run = types.MethodType(run, lib)

    return lib

def init_spectrv():
    """Initialize SPECTRV
    
    The SPECTRV code takes the continuum opacity calculated with XNFPELSYN and the line opacity calculated with
    SYNTHE, and produces the final emergent spectrum

    This function loads the SPECTRV library and binds methods to push the XNFPELSYN/SYNTHE output into the library,
    to run SPECTRV, and to retrieve the emergent spectrum in standard units
    
    Returns
    -------
    ctypes.CDLL
        SPECTRV library with `.load_xnfpelsyn()`, `.load_synthe()`, `.run()` and `get_spectrum()` methods bound to it
    """
    # Load the library
    lib = ctypes.CDLL('{}/{}'.format(python_path, 'bin/spectrv.so'))

    # Flag to track if SPECTRV has run
    lib.has_run = False

    # Bound method to make the output of XNFPELSYN available to SPECTRV
    def load_xnfpelsyn(self, xnfpelsyn):
        if not xnfpelsyn.has_run:
            raise ValueError('XNFPELSYN has not run yet')

        # Make the structure in XNFPELSYN available to SPECTRV
        self.f5 = xnfpelsyn.f5
        self.set_f5.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        pointer = self.f5.ctypes.data_as(ctypes.c_void_p)
        self.set_f5(pointer, self.f5.shape[0], self.f5.shape[1])

        # Make the chemical constants table loaded in XNFPELSYN available to SPECTRV
        self.f2 = xnfpelsyn.f2
        self.set_f2.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        pointer = self.f2.ctypes.data_as(ctypes.c_void_p)
        self.set_f2(pointer, self.f2.shape[0], self.f2.shape[1])

        # Make XNFPELSYN output available to SPECTRV
        self.xnfpelsyn_output = xnfpelsyn.xnfpelsyn_output
        self.set_f10.argtypes = [ctypes.c_void_p for field in self.xnfpelsyn_output]
        self.set_f10(*[self.xnfpelsyn_output[field].ctypes.data_as(ctypes.c_void_p) for field in self.xnfpelsyn_output])
    lib.load_xnfpelsyn = types.MethodType(load_xnfpelsyn, lib)

    # Bound method to make the output of SYNTHE available to SPECTRV
    def load_synthe(self, synthe):
        if not synthe.has_run:
            raise ValueError('SYNTHE has not run yet')

        # Make the meta data in SYNTHE available to SPECTRV
        self.meta = synthe.meta
        self.vturb = synthe.vturb
        self.set_f93.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_double, ctypes.c_double,
                                ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_float, ctypes.c_float]
        self.set_f93(*[self.meta[key] for key in self.meta], self.vturb)

        # Make the SYNTHE output available to SPECTRV
        self.asynth = synthe.asynth
        self.set_asynth.argtypes = [ctypes.c_void_p, ctypes.c_int]
        pointer = self.asynth.ctypes.data_as(ctypes.c_void_p)
        self.set_asynth(pointer, self.meta['n_wl'])

        # Create an array to store the output spectrum
        self.spectrum = np.zeros([self.meta['n_wl'], 2], dtype = np.float64, order = 'F')
        self.set_spectrum.argtypes = [ctypes.c_void_p, ctypes.c_int]
        pointer = self.spectrum.ctypes.data_as(ctypes.c_void_p)
        self.set_spectrum(pointer, self.meta['n_wl'])
    lib.load_synthe = types.MethodType(load_synthe, lib)

    # Bound method to run SYNTHE
    def run(self):
        try:
            self.xnfpelsyn_output
        except:
            raise ValueError('SPECTRV does not have XNFPELSYN output')
        try:
            self.asynth
        except:
            raise ValueError('SPECTRV does not have SYNTHE output')
        self.run_spectrv()
        self.has_run = True
    lib.run = types.MethodType(run, lib)

    # Bound method to generate the final spectrum in standard units
    def get_spectrum(self):
        if not self.has_run:
            raise ValueError('SPECTRV has not run yet')

        # Recover the wavelength array
        wbegin = ctypes.c_double.in_dll(self, 'wbegin').value
        deltaw = ctypes.c_double.in_dll(self, 'deltaw').value
        numnu = ctypes.c_int.in_dll(self, 'numnu').value
        wl = 10 ** (np.log10(wbegin) + np.arange(numnu) * np.log10(1 + 1 / deltaw)) * 10

        # Compute the intensities
        flux = 4.0 * self.spectrum[:,0] * spc.c * 1e10 / (wl ** 2.0)
        cont = 4.0 * self.spectrum[:,1] * spc.c * 1e10 / (wl ** 2.0)

        return wl, flux, cont, flux / cont
    lib.get_spectrum = types.MethodType(get_spectrum, lib)

    return lib
