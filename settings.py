# This file stores the most important settings for ATLAS and SYNTHE. Edit here directly.
import numpy as np

def atlas_settings():
	config = atlas_default_settings()

	# Effective temperature [K] unless overridden directly
	config['teff']             =    5400
	# Surface gravity [log10(CGS)] unless overridden directly
	config['gravity']          =    4.75
	# 10^metallicity, [M/H]
	config['abundance_scale']  =    10.0 ** (-1.4)
	# Hydrogen number fraction
	config['elements'][1]      =    0.8558061523714692
	# Helium number fraction
	config['elements'][2]      =    0.14405444583578444
	# Abundance enhancements of individual elements ([A/M])
	config['elements'][6]     +=    -0.65
	config['elements'][7]     +=    +1.45
	config['elements'][8]     +=    +0.4
	config['elements'][10]    +=    +0.4
	config['elements'][12]    +=    +0.4
	config['elements'][14]    +=    +0.4
	config['elements'][16]    +=    +0.4
	config['elements'][18]    +=    +0.4
	config['elements'][20]    +=    +0.4
	config['elements'][22]    +=    +0.4


    # Since ATLAS abundances are expressed as log10(N(A)/N(H+He)) as opposed to the traditional convention, log10(N(A)/N(H)) + 12, we must introduce a correction here
	helium_correction = np.log10((config['elements'][1]+config['elements'][2])/config['elements'][1]) - np.log10((atlas_default_abundances()[1]+atlas_default_abundances()[2])/atlas_default_abundances()[1])
	for i in range(3, 100):
		if config['elements'][i] != -20.0:
			config['elements'][i] -= helium_correction

	return config
	
def atlas_default_settings():
	elements = atlas_default_abundances()
	config = {
		'abundance_scale': 1.0000,
		'teff':            5770.0,
		'gravity':         4.44,
		'elements':        elements,
	}
	return config

def atlas_default_abundances():
	'''
	  Default elemental abundances of ATLAS-9 following the convention log10(N(A)/N(H+He))
	  See http://atmos.ucsd.edu/?p=solar for original references.
	  Set any of the abundances to -20.0 to exclude the element
	'''
	elements = list(range(100))
	elements[1] = 0.9206471640943776
	elements[2] = 0.07824693927227462
	elements[3] = -8.775426229703063
	elements[4] = -10.655426229703064
	elements[5] = -9.245426229703064
	elements[6] = -3.535426229703064
	elements[7] = -4.175426229703063
	elements[8] = -3.2754262297030636
	elements[9] = -7.475426229703063
	elements[10] = -4.015426229703063
	elements[11] = -5.795426229703063
	elements[12] = -4.435426229703063
	elements[13] = -5.585426229703063
	elements[14] = -4.525426229703063
	elements[15] = -6.575426229703063
	elements[16] = -4.875426229703063
	elements[17] = -6.535426229703063
	elements[18] = -5.635426229703063
	elements[19] = -6.925426229703063
	elements[20] = -5.695426229703063
	elements[21] = -8.885426229703063
	elements[22] = -7.085426229703063
	elements[23] = -8.105426229703063
	elements[24] = -6.395426229703063
	elements[25] = -6.605426229703063
	elements[26] = -4.515426229703063
	elements[27] = -7.045426229703063
	elements[28] = -5.815426229703063
	elements[29] = -7.845426229703063
	elements[30] = -7.475426229703063
	elements[31] = -8.995426229703064
	elements[32] = -8.385426229703063
	elements[33] = -9.735426229703062
	elements[34] = -8.695426229703063
	elements[35] = -9.495426229703064
	elements[36] = -8.785426229703063
	elements[37] = -9.675426229703064
	elements[38] = -9.165426229703062
	elements[39] = -9.825426229703062
	elements[40] = -9.415426229703062
	elements[41] = -10.575426229703062
	elements[42] = -10.155426229703064
	elements[43] = -20.0
	elements[44] = -10.285426229703063
	elements[45] = -10.975426229703062
	elements[46] = -10.385426229703063
	elements[47] = -10.835426229703064
	elements[48] = -10.325426229703062
	elements[49] = -11.275426229703063
	elements[50] = -9.995426229703064
	elements[51] = -11.025426229703063
	elements[52] = -9.855426229703063
	elements[53] = -10.485426229703062
	elements[54] = -9.795426229703063
	elements[55] = -10.955426229703063
	elements[56] = -9.855426229703063
	elements[57] = -10.935426229703063
	elements[58] = -10.455426229703063
	elements[59] = -11.315426229703062
	elements[60] = -10.615426229703063
	elements[61] = -20.0
	elements[62] = -11.075426229703062
	elements[63] = -11.515426229703063
	elements[64] = -10.965426229703063
	elements[65] = -11.735426229703062
	elements[66] = -10.935426229703063
	elements[67] = -11.555426229703063
	elements[68] = -11.115426229703063
	elements[69] = -11.935426229703063
	elements[70] = -11.115426229703063
	elements[71] = -11.935426229703063
	elements[72] = -11.165426229703064
	elements[73] = -12.155426229703062
	elements[74] = -11.385426229703063
	elements[75] = -11.775426229703063
	elements[76] = -10.675426229703064
	elements[77] = -10.655426229703064
	elements[78] = -10.415426229703062
	elements[79] = -11.235426229703062
	elements[80] = -10.865426229703063
	elements[81] = -11.265426229703063
	elements[82] = -9.995426229703064
	elements[83] = -11.385426229703063
	elements[84] = -20.0
	elements[85] = -20.0
	elements[86] = -20.0
	elements[87] = -20.0
	elements[88] = -20.0
	elements[89] = -20.0
	elements[90] = -11.955426229703063
	elements[91] = -20.0
	elements[92] = -12.575426229703062
	elements[93] = -20.0
	elements[94] = -20.0
	elements[95] = -20.0
	elements[96] = -20.0
	elements[97] = -20.0
	elements[98] = -20.0
	elements[99] = -20.0
	return elements
