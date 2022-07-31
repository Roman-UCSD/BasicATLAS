import numpy as np
from collections import OrderedDict
import os

python_path = os.path.dirname(os.path.realpath(__file__))

class Settings:
    def abun_atlas_to_std(self, elements, zscale):
        """
        Convert ATLAS format abundances to the standard format. See abun_std_to_atlas() for the details of each
        format

        While carrying out the conversion, the method uses abun_solar() to retrieve standard solar abundances

        arguments:
            elements          :  List of ATLAS abundances with 100 elements. The 0th element is not used (set to 0.0).
                                 The rest of the elements have indices corresponding to the atomic number (e.g. 1 for hydrogen)
            zscale     :         Metallicity in dex ([M/H]). Defaults to 0.0 (solar)

        returns:
            A dictionary with keys corresponding to the arguments of abun_std_to_atlas()
        """
        # Get atomic numbers, weights and symbols of all chemical elements
        Z, A = np.loadtxt(python_path + '/data/solar.csv', usecols = [0, 1], unpack = True, delimiter = ',')
        symbol = np.loadtxt(python_path + '/data/solar.csv', usecols = [5], unpack = True, delimiter = ',', dtype = str)

        # Load solar abundances
        solar = self.abun_solar()

        # Calculate standard abundances
        abun = OrderedDict()
        total_mass = 0.0
        for i in range(3, 100):
            if solar[symbol[Z == i][0]] < -90.0 and elements[i] <= -20.0:
                atlas_abun = 0.0
            elif solar[symbol[Z == i][0]] < -90.0 and elements[i] > -20.0:
                raise ValueError('No solar abundance for element {}'.format(symbol[Z == i][0]))
            else:
                atlas_abun = np.round(elements[i] + np.log10((elements[1] + elements[2])) - np.log10(elements[1]) + 12.0 - solar[symbol[Z == i][0]], 2)
            if atlas_abun != 0.0:
                abun[symbol[Z == i][0]] = atlas_abun
            total_mass += 10 ** (atlas_abun + solar[symbol[Z == i][0]] + zscale) * A[Z == i][0]

        # Calculate Helium mass fraction
        helium_mass = elements[2] / (elements[1] / 1e12) * A[Z == 2][0]
        total_mass = total_mass + 1e12 * A[Z == 1][0] + helium_mass
        Y = helium_mass / total_mass

        return {'abun': abun, 'Y': Y, 'zscale': zscale}

    def abun_std_to_atlas(self, Y = -0.1, zscale = 0.0, abun = {}):
        """
        Convert standard chemical abundances to the ATLAS format. Standard abundances are specified in terms
        of the helium mass fraction (Y), metallicity ([M/H]) and enhancements of individual elements ([A/M]),
        where [x/y] = log10(N(x) / N(y)) - log10(N(x)_solar / N(y)_solar). ATLAS abundances of hydrogen and
        helium are provided explicitly as number fractions, while all metal abundances are provided as
        log10(N(A)) - log10(N(H) + N(He)). ATLAS hydrogen and helium abundances are provided absolutely,
        while ATLAS metal abundances are given before the metallicity enhancement.

        While carrying out the conversion, the method uses abun_solar() to retrieve standard solar abundances

        arguments:
            Y          :         Helium mass fraction (between 0.0 and 1.0). Any number outside the valid range
                                 loads the solar value. Defaults to -0.1 (i.e. solar)
            zscale     :         Metallicity in dex ([M/H]). Defaults to 0.0 (solar)
            abun       :         Enhancements of individual elements in dex ([A/M]), specified as a dictionary
                                 keyed by chemical symbols. E.g. {'C': +0.2, 'U': -2.0}. All unspecified elements
                                 are set to solar

        returns:
            List of ATLAS abundances with 100 elements. The 0th element is not used (set to 0.0). The rest of
            the elements have indices corresponding to the atomic number (e.g. 1 for hydrogen)
        """
        # Get atomic numbers, weights and symbols of all chemical elements
        Z, A = np.loadtxt(python_path + '/data/solar.csv', usecols = [0, 1], unpack = True, delimiter = ',')
        symbol = np.loadtxt(python_path + '/data/solar.csv', usecols = [5], unpack = True, delimiter = ',', dtype = str)

        # Load solar abundances and apply enhancements
        solar = self.abun_solar()
        for key in abun:
            if key not in solar.keys():
                raise ValueError('Unknown element: {}'.format(key))
            if key == 'H':
                raise ValueError('Cannot set H abundance directly: it is calculated automatically from other abundances')
            if key == 'He':
                raise ValueError('Cannot set He abundance directly: use helium mass fraction (Y) instead')
            solar[key] = solar[key] + abun[key]

        # Convert enhanced solar abundances into vectors of values, atomic numbers and atomic weights
        N_array = []; A_array = []; Z_array = []
        for key in solar:
            N_array += [solar[key] + zscale * (Z[symbol == key][0] > 2.0)] # Apply metallicity enhancement to metals
            A_array += [A[symbol == key][0]]
            Z_array += [Z[symbol == key][0]]
        N_array = 10 ** np.array(N_array); A_array = np.array(A_array); Z_array = np.array(Z_array)

        # If Y is provided, alter the helium abundance to match it
        if Y >= 0.0 and Y <= 1.0:
            N_array[Z_array == 2] = - np.sum(N_array[Z_array != 2] * A_array[Z_array != 2]) * Y / (A_array[Z_array == 2][0] * Y - A_array[Z_array == 2][0])

        # Generate ATLAS abundances
        elements = list(range(100))      # 0th element is not used, 1st element refers to H, 2nd to He etc up to 99th element
        # Hydrogen and helium abundances are simply number fractions
        elements[1] = N_array[Z_array == 1][0] / np.sum(N_array)
        elements[2] = N_array[Z_array == 2][0] / np.sum(N_array)
        # The rest are log10(N(A) / (N(H) + N(He))) *before* the metallicity enhancement
        for i in range(3, 100):
            elements[i] = np.log10(N_array[Z_array == i][0] / (N_array[Z_array == 1][0] + N_array[Z_array == 2][0])) - zscale
            # ATLAS behaves weirdly when abundances are given below -20.0. At -20.0 the element effectively does not exist
            if elements[i] < -20.0:
                elements[i] = -20.0

        if float('{:>7.5f}'.format(elements[1])) == 0.0:
            raise ValueError('Underflow in Y value. Hydrogen abundance cannot be zero!')

        return elements

    def abun_solar(self):
        """
        Load standard solar abundances.

        returns
            Standard solar abundances as log10(N(A)/N(H)) + 12.0, keyed by chemical symbols (e.g. "He" for helium)
        """
        N = np.loadtxt(python_path + '/data/solar.csv', usecols = [2], unpack = True, delimiter = ',')
        symbol = np.loadtxt(python_path + '/data/solar.csv', usecols = [5], unpack = True, delimiter = ',', dtype = str)
        return OrderedDict(zip(symbol, N))

    def atlas_abun(self):
        """
        Get ATLAS abundances for this instance of settings. See Settings.abun_std_to_atlas() for details of the output
        format
        """
        return self.abun_std_to_atlas(self.Y, self.zscale, self.abun)

    def check_ODF(self, ODF):
        """
        Check that a given ODF is compatible with the current settings. "ODF" must be the output of meta(). The function
        runs silently with no returned value if the ODF is compatible, but throws an exception otherwise
        """
        # Calculate solar Y
        Z, A = np.loadtxt(python_path + '/data/solar.csv', usecols = [0, 1], unpack = True, delimiter = ',')
        symbol = np.loadtxt(python_path + '/data/solar.csv', usecols = [5], unpack = True, delimiter = ',', dtype = str)
        solar = self.abun_solar()
        total_mass = 0.0
        for element in solar:
            total_mass += 10 ** (solar[element] + self.zscale * (Z[symbol == element][0] > 2.0)) * A[symbol == element][0]
        Y_solar = 10 ** solar['He'] * A[symbol == 'He'][0] / total_mass
        if self.Y < 0.0 or self.Y > 1.0:
            Y = Y_solar
        else:
            Y = self.Y

        if np.abs(ODF['zscale'] - self.zscale) > 0.01:
            raise ValueError('Incomplatible ODF: ODF calculated for zscale={} as opposed to {}'.format(ODF['zscale'], self.zscale))
        if np.abs(ODF['Y'] - Y) > 0.001:
            raise ValueError('Incomplatible ODF: ODF calculated for Y={} as opposed to {}'.format(ODF['Y'], Y))
        atlas_abun = self.abun_std_to_atlas(ODF['Y'], ODF['zscale'], ODF['abun'])
        for element in solar:
            if element == 'H' or element == 'He':
                continue
            if element in ODF['abun']:
                ODF_value = ODF['abun'][element]
            else:
                ODF_value = 0.0
            if element in self.abun:
                self_value = self.abun[element]
            else:
                self_value = 0.0
            # We have to be careful here as sometimes discrepancies are due to the ODF abundance being floored (cannot go below -20 in ATLAS format)
            if ODF_value != self_value and not (atlas_abun[int(Z[symbol == element][0])] == -20.0 and ODF_value > self_value):
                raise ValueError('Incomplatible ODF: ODF calculated for enhancements {} as opposed to {}'.format(dict(ODF['abun']), dict(self.abun)))

    def mass_fractions(self):
        """
        Calculate the X, Y and Z mass fractions (hydrogen, helium and metals) for the current abundance settings
        """
        # Get atomic numbers, weights and symbols of all chemical elements
        Z, A = np.loadtxt(python_path + '/data/solar.csv', usecols = [0, 1], unpack = True, delimiter = ',')
        symbol = np.loadtxt(python_path + '/data/solar.csv', usecols = [5], unpack = True, delimiter = ',', dtype = str)

        elements = self.atlas_abun()
        metal_mass = 0.0
        for i, element in enumerate(elements):
            if i > 2:
                metal_mass += 10 ** (element + self.zscale) * (1e12 + 1e12 * (elements[2] / elements[1])) * A[Z == i][0]
        hydrogen_mass = 1e12 * A[Z == 1][0]
        helium_mass = 1e12 * (elements[2] / elements[1]) * A[Z == 2][0]
        total_mass = metal_mass + hydrogen_mass + helium_mass
        return hydrogen_mass / total_mass, helium_mass / total_mass, metal_mass / total_mass

    def effective_zscale(self):
        """
        Calculate the "effective" metallicity of the current settings, i.e. the value of metallicity, [M/H], that would result
        in the same hydrogen, helium and metal mass fractions (see mass_fractions()) under purely (scaled) solar abundances
        """
        # Get atomic numbers, weights and symbols of all chemical elements
        Z, A = np.loadtxt(python_path + '/data/solar.csv', usecols = [0, 1], unpack = True, delimiter = ',')
        symbol = np.loadtxt(python_path + '/data/solar.csv', usecols = [5], unpack = True, delimiter = ',', dtype = str)
        mass_fractions = self.mass_fractions()

        elements = self.abun_solar()
        metal_mass = 0.0
        for element in elements:
            if element != 'H' and element != 'He':
                metal_mass += A[symbol == element][0] * 10 ** (elements[element])
        hydrogen_mass = 10 ** elements['H'] * A[symbol == 'H'][0]

        return np.log10((hydrogen_mass * mass_fractions[2]) / (metal_mass * mass_fractions[0]))

    @property
    def zscale(self):
        return self._zscale

    # ATLAS takes metallicity on linear scale in the 9.5F format (9 spaces, 5 decimal places). We must make sure that the provided
    # value of metallicity can be accurately represented in this format
    @zscale.setter
    def zscale(self, d):
        formatted = '{:>9.5f}'.format(10 ** d)
        if len(formatted) > 9:
            raise ValueError('Overflow in zscale value')
        formatted = float(formatted)
        if formatted == 0.0 or np.abs(np.log10(formatted) - d) > 0.01:
            raise ValueError('Underflow in zscale value')
        self._zscale = d

    def __init__(self):
        self.teff = 5770.0
        self.logg = 4.44
        self.zscale = 0.0
        self.Y = -0.1
        self.vturb = 2
        self.abun = {}

