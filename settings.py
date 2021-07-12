import numpy as np
from collections import OrderedDict
import os

python_path = os.path.dirname(os.path.realpath(__file__))

class Settings:
    def abun_atlas_to_std(self, elements, zscale):
        # Get atomic numbers, weights and symbols of all chemical elements
        Z, A = np.loadtxt(python_path + '/data/solar.csv', usecols = [0, 1], unpack = True, delimiter = ',')
        symbol = np.loadtxt(python_path + '/data/solar.csv', usecols = [5], unpack = True, delimiter = ',', dtype = str)

        # Load solar abundances
        solar = self.abun_solar()

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
                abun[symbol[Z == i][0]]
            total_mass += 10 ** (atlas_abun + solar[symbol[Z == i][0]]) * A[Z == i][0]

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
        # Calculate solar Y
        Z, A = np.loadtxt(python_path + '/data/solar.csv', usecols = [0, 1], unpack = True, delimiter = ',')
        symbol = np.loadtxt(python_path + '/data/solar.csv', usecols = [5], unpack = True, delimiter = ',', dtype = str)
        solar = self.abun_solar()
        total_mass = 0.0
        for element in solar:
            total_mass += 10 ** solar[element] * A[symbol == element][0]
        Y_solar = 10 ** solar['He'] * A[symbol == 'He'][0] / total_mass
        if self.Y < 0.0 or self.Y > 1.0:
            Y = Y_solar
        else:
            Y = self.Y

        if ODF['zscale'] != self.zscale:
            raise ValueError('Incomplatible ODF: ODF calculated for zscale={} as opposed to {}'.format(ODF['zscale'], self.zscale))
        if not np.isclose(ODF['Y'], Y):
            raise ValueError('Incomplatible ODF: ODF calculated for Y={} as opposed to {}'.format(ODF['Y'], Y))
        if ODF['abun'] != self.abun:
            raise ValueError('Incomplatible ODF: ODF calculated for enhancements {} as opposed to {}'.format(dict(ODF['abun']), dict(self.abun)))

    def __init__(self):
        self.teff = 5770.0
        self.logg = 4.44
        self.zscale = 0.0
        self.Y = -0.1
        self.vturb = 2
        self.abun = {}

