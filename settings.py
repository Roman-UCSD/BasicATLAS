# This file stores the most important settings for ATLAS and SYNTHE. Edit here directly.

def atlas_settings():
	config = atlas_default_settings()
	
	config['teff']             =    5400
	config['gravity']          =    4.75
	config['abundance_scale']  =    10.0 ** (-1.7)
	config['elements'][1]      =    0.8528
	config['elements'][2]      =    0.1459
	config['elements'][6]     +=    -0.65
	config['elements'][7]     +=    +1.45
	config['elements'][8]     +=    -0.1
	
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
	  Default elemental abundances of ATLAS-9 in its units
	'''
	elements = range(100)
	elements[1] = 0.9204
	elements[2] = 0.07834
	elements[3] = -10.94
	elements[4] = -10.64
	elements[5] = -9.49
	elements[6] = -3.52
	elements[7] = -4.12
	elements[8] = -3.21
	elements[9] = -7.48
	elements[10] = -3.96
	elements[11] = -5.71
	elements[12] = -4.46
	elements[13] = -5.57
	elements[14] = -4.49
	elements[15] = -6.59
	elements[16] = -4.71
	elements[17] = -6.54
	elements[18] = -5.64
	elements[19] = -6.92
	elements[20] = -5.68
	elements[21] = -8.87
	elements[22] = -7.02
	elements[23] = -8.04
	elements[24] = -6.37
	elements[25] = -6.65
	elements[26] = -4.54
	elements[27] = -7.12
	elements[28] = -5.79
	elements[29] = -7.83
	elements[30] = -7.44
	elements[31] = -9.16
	elements[32] = -8.63
	elements[33] = -9.67
	elements[34] = -8.63
	elements[35] = -9.41
	elements[36] = -8.73
	elements[37] = -9.44
	elements[38] = -9.07
	elements[39] = -9.80
	elements[40] = -9.44
	elements[41] = -10.62
	elements[42] = -10.12
	elements[43] = -20.00
	elements[44] = -10.20
	elements[45] = -10.92
	elements[46] = -10.35
	elements[47] = -11.10
	elements[48] = -10.27
	elements[49] = -10.38
	elements[50] = -10.04
	elements[51] = -11.04
	elements[52] = -9.80
	elements[53] = -10.53
	elements[54] = -9.87
	elements[55] = -10.91
	elements[56] = -9.91
	elements[57] = -10.87
	elements[58] = -10.46
	elements[59] = -11.33
	elements[60] = -10.54
	elements[61] = -20.00
	elements[62] = -11.03
	elements[63] = -11.53
	elements[64] = -10.92
	elements[65] = -11.69
	elements[66] = -10.90
	elements[67] = -11.78
	elements[68] = -11.11
	elements[69] = -12.04
	elements[70] = -10.96
	elements[71] = -11.98
	elements[72] = -11.16
	elements[73] = -12.17
	elements[74] = -10.93
	elements[75] = -11.76
	elements[76] = -10.59
	elements[77] = -10.69
	elements[78] = -10.24
	elements[79] = -11.03
	elements[80] = -10.91
	elements[81] = -11.14
	elements[82] = -10.09
	elements[83] = -11.33
	elements[84] = -20.00
	elements[85] = -20.00
	elements[86] = -20.00
	elements[87] = -20.00
	elements[88] = -20.00
	elements[89] = -20.00
	elements[90] = -11.95
	elements[91] = -20.00
	elements[92] = -12.54
	elements[93] = -20.00
	elements[94] = -20.00
	elements[95] = -20.00
	elements[96] = -20.00
	elements[97] = -20.00
	elements[98] = -20.00
	elements[99] = -20.00
	return elements