import sys
import glob
import re
import os
import random
import numpy as np
import png
import pexpect
import operator
from datetime import datetime
import time

import templates
import settings
import wavelength

####     DATA FILES    (absolute or relative to the pipeline)   ####
kapp00         = '../../atmos_files_jon/Lines_AT9/kapp00.ros'
p00big2        = '../../atmos_files_jon/Lines_AT9/p00big2.bdf'
molecules      = '../../atmos_files_jon/Lines_AT9/molecules.dat'
s_data         = '../../atmos_files_jon/Lines_SYNTHE'
d_data         = '../dfsynthe_files'
s_molecules    = '../../atmos_files_jon/Molecules_SYNTHE'
atlas_init     = '../initial_models/*.*'                         # ATLAS-9 initial models directory
atlas_exe      = '../compiled/atlas9mem.exe'                     # ATLAS-9 compiled executable
synthe_suite   = '../compiled'                                   # SYNTHE compiled executables
dfsynthe_suite = '../compiled'                                   # DFSYNTHE compiled executables
default_vega   = '../std_spectra/vega_bohlin_2004.dat'           # Default Vega spectrum to use for bolometric corrections
trans_dir      = '../filters/*.*'                                # Directory for filter transmission profiles for bolometry


python_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(python_path)

def bolometry(run, mag = -1.0, std_spectrum = default_vega):
	"""
	Compute bolometric corrections for the spectrum in run "run" for passbands in trans_dir.
	Use Vega-based magnitudes system where Vega is given by the spectrum in std_spectrum and assumed
	to have magnitude 0 in every passband. If mag (bolometric absolute) is provided, also compute
	absolute magnitudes in every passband. Print the results out into the terminal and a text file.
	"""
	sf = 5.670367e-8 * 4 * np.pi  # Stefan-Boltzmann * 4 pi (SI)
	pc = 3.086e+16                # Parsec in m
	c  = 299792458e10             # Speed of light (A/s)
	
	# Check that the SYNTHE run exists
	path = 'run_' + run
	if not (os.path.isfile(path + '/spectrum.dat')):
		print "Cannot find the run!"
		return
	
	# Checking the Vega spectrum is available
	if not (os.path.isfile(std_spectrum)):
		print "Cannot load the standard spectrum"
		return

	files = glob.glob(trans_dir)   # Load filter transmissions

	print ""
	print "BOLOMETRIC CORRECTIONS FOR TRANSMISSION BANDPASSES IN", trans_dir
	print ""
	print "{:30}".format("FILENAME"), '|', "{:15}".format("PIVOT [nm]"), '|', "{:20}".format("ZERO-POINT (VEGA)"), '|', "{:20}".format("BC (VEGA)"),
	print '|', "{:20}".format("ABS MAG (VEGA)"), '|', "{:20}".format("BC (AB)"), '|', "{:20}".format("ABS MAG (AB)")
	print '-' * 160
	
	wl_ref, flux_ref = np.loadtxt(std_spectrum, unpack = True, delimiter = ',', usecols = [0, 1])
	wl, flux = np.loadtxt(path + '/spectrum.dat', unpack = True, delimiter = ',', usecols = [0, 1])
	
	# Get the effective temperature of the model from the ATLAS-9 output
	file = open(path + '/output_summary.out', 'r')
	T = file.readline()
	file.close()
	T = float(''.join(list(T)[T.find('TEFF') + 4:T.find('GRAVITY')]).replace(' ', ''))
	
	output = []
	for transmission in files:
		# Read the zero-point of the filter
		file = open(transmission, 'r')
		zero = file.readline()
		file.close()
		if zero.find('<zero>') != -1 and zero.find('</zero>') != -1:
			zero = float(''.join(list(zero)[zero.find('<zero>') + 6:zero.find('</zero>')]).replace(' ', ''))
		else:
			zero = 0.0

		wl_t, t  = np.loadtxt(transmission, unpack = True, delimiter = ',')
		
		# Account for possible ways in which the transmission profile can be "broken"
		if np.max(wl_t) < 3000:   # Check it is in A and not nm
			wl_t *= 10
		if np.max(t) > 1:         # Check it is a fraction (0..1) and not a percentage (0..100)
			t /= 100.0
		t[t <= 0] = 0.0           # Kill off negative transmission values
		# Sort by wavelength ascending. Otherwise, NumPy can't interpolate over.
		L = sorted(zip(wl_t, t), key=operator.itemgetter(0))
		wl_t, t = np.array(zip(*L))
		
		# Calculate pivot wavelength
		pivot = np.sqrt(np.trapz(t, x = wl_t) / np.trapz(t * wl_t**(-2), x = wl_t))

		# Load Vega
		t_ref = np.interp(wl_ref, wl_t, t)
		t = np.interp(wl, wl_t, t)

		# Integrate transmission profile over source and Vega spectra, converting from energy-counting to photon-counting
		integral_ref = np.trapz(flux_ref * t_ref * wl_ref, x = wl_ref)
		integral     = np.trapz(flux * t * wl, x = wl) * np.pi # The extra factor of pi to remove steradian dependence from SYNTHE model
		integral_ab  = np.trapz(3631e-23 * t * wl * c / (wl ** 2.0), x = wl)

		# Compute bolometric correction (Vega).
		bc    = 4.74 + 2.5*np.log10(3.828e26 / (((10 * pc) ** 2.0) * sf * (T ** 4.0))) + 2.5 * np.log10(integral / integral_ref) - zero
		# Compute bolometric correction (AB)
		bc_ab = 4.74 + 2.5*np.log10(3.828e26 / (((10 * pc) ** 2.0) * sf * (T ** 4.0))) + 2.5 * np.log10(integral / integral_ab)
		# If absolute bolometric magnitude is given, compute absolute magnitudes for all passbands. Save '---' otherwise.
		abs_mag = '---'
		abs_mag_ab = '---'
		if float(mag) != -1.0:
			abs_mag = str(float(mag) - float(bc))
			abs_mag_ab = str(float(mag) - float(bc_ab))
		
		output += [[os.path.basename(transmission), str(np.round(pivot / 10.0, 3)), str(zero), str(bc), abs_mag, str(bc_ab), abs_mag_ab]]
		print "{:30}".format(os.path.basename(transmission)), '|', "{:15}".format(str(np.round(pivot / 10.0, 3))), '|', "{:20}".format(str(zero)),
		print '|', "{:20}".format(str(bc)), '|', "{:20}".format(abs_mag), '|', "{:20}".format(str(bc_ab)), '|', "{:20}".format(str(abs_mag_ab))
	
	header = 'Filter filename,Pivot wavelength [nm],Zero-point [vegamag],Bolometric correction [vegamag],Absolute magnitude [vegamag],Bolometric correction [AB],Absolute magnitude [AB]'
	np.savetxt(path + '/bolometry.dat', np.array(output), delimiter = ',', fmt = '%s', header = header)
	print ""
	print "The corrections were also saved in", path + '/bolometry.dat'
	print "Absolute magnitudes are computed only when the absolute bolometric magnitude is provided in the second argument"
	print "Zero-points for filters can be specified in the first line of the transmission file between <zero> and </zero>"
	print std_spectrum, "was used as the standard Vega spectrum. The third argument can be used to specify a different standard."

def visualize_spectrum(run, width = 800, height = 100):
	"""
	Render a PNG visualization of the spectrum, previously generated in run "run" using SYNTHE. The width
	and the height arguments specify the desired dimensions of the image in pixels. Relies on an external script
	"wavelength.py", featuring a function to convert a wavelength of visible light into RGB.
	"""
	# Check that the SYNTHE run exists
	path = 'run_' + run
	if not (os.path.isfile(path + '/spectrum.dat')):
		print "Cannot find the run!"
		return
	
	# Generate the PNG
	wl, fluxl, fluxc, residual = np.loadtxt(path + '/spectrum.dat', unpack = True, delimiter = ',')
	wl = wl / 10.0

	floor = -1
	ceil = -1
	width = int(width)
	height = int(height)

	if (floor < 0):
		floor = min(fluxl)
	if (ceil < 0):
		ceil = max(fluxl)
	px = np.linspace(max(min(wl), 380), min(750, max(wl)), width)
	interp = np.interp(px, wl, fluxl)
	output = np.zeros([width, 3, height])
	for index, column in enumerate(output):
		value = interp[index]
		if (value > ceil):
			value = ceil
		if (value < floor):
			value = floor
		r, g, b = wavelength.wavelength_to_rgb(px[index])
		value = map(int, map(round, np.array([r, g, b]) * (value - floor) / (ceil - floor)))
		output[index][0] = [value[0]] * len(output[index][0])
		output[index][1] = [value[1]] * len(output[index][1])
		output[index][2] = [value[2]] * len(output[index][2])

	f = open(path + '/spectrum.png', 'wb')
	output = np.reshape(output, [width * 3, height])
	w = png.Writer(width, height)
	w.write(f, output.T)
	f.close()
	
	print "Exported the spectrum as PNG in spectrum.png"
	return

def show_models(pickone = False, teff = "0", gravity = "0"):
	""" Show all available initial ATLAS-9 models
	    If pickone is True, instead of showing the models, the function will choose one that is closest
		to the current settings and return it. If the optional arguments, "teff" and "gravity" are provided,
		the search for the closest model will be done for the given values of effective temperature and gravity
		instead of the ones saved in the settings. The metallicity will still be taken from the settings regardless.
	"""
	if (not pickone):
		print ""
		print "MODELS FOUND IN ", atlas_init
		print ""
		print "{:30}".format("NAME"), "{:10}".format("TEFF"), "{:10}".format("GRAVITY"), "{:10}".format("METALLICITY")
	config = settings.atlas_settings()
	if teff != "0":
		config['teff'] = float(teff)
	if gravity != "0":
		config['gravity'] = float(gravity)
	temps = []
	gravs = []
	metals = []
	models = []
	files = glob.glob(atlas_init)
	for filename in files:
		file = open(filename, 'r')
		temp = 0
		grav = 0
		metallicity = 0
		for line in file:
			if (line.find('TEFF') != -1):
				match = re.search('TEFF +?([0-9.]+)', line)
				if match != None:
					temp = float(match.groups()[0])
			if (line.find('GRAVITY') != -1):
				match = re.search('GRAVITY +?([0-9.]+)', line)
				if match != None:
					grav = float(match.groups()[0])
			if (line.find('ABUNDANCE SCALE') != -1):
				match = re.search('ABUNDANCE SCALE +?([0-9.]+)', line)
				if match != None:
					metallicity = float(match.groups()[0])
			if (temp != 0 and grav != 0 and metallicity != 0):
				temps += [temp]
				gravs += [grav]
				metals += [metallicity]
				models += [filename]
				if (not pickone):
					print "{:30}".format(os.path.basename(file.name)), "{:10}".format(str(temp)), "{:10}".format(str(grav)), "{:10}".format(str(round(np.log10(metallicity),2)))
				break
		file.close()
	if pickone:
		temps = np.array(temps)
		gravs = np.array(gravs)
		metals = np.log10(np.array(metals))
		ideal_temp = (config['teff'] - np.min(temps)) / (np.max(temps) - np.min(temps))
		ideal_grav = (config['gravity'] - np.min(gravs)) / (np.max(gravs) - np.min(gravs))
		config['abundance_scale'] = np.log10(config['abundance_scale'])
		ideal_metal = (config['abundance_scale'] - np.min(metals)) / (np.max(metals) - np.min(metals))
		temps = (temps - np.min(temps)) / (np.max(temps) - np.min(temps))
		gravs = (gravs - np.min(gravs)) / (np.max(gravs) - np.min(gravs))
		metals = (metals - np.min(metals)) / (np.max(metals) - np.min(metals))
		distance = np.sqrt((ideal_temp - temps) ** 2.0 + (ideal_grav - gravs) ** 2.0 + (ideal_metal - metals) ** 2.0)
		return os.path.basename(models[np.where(distance == np.min(distance))[0][0]])
	return

def initialize(run = -1):
	""" Create a new directory to store all the output """
	if run == -1:
		run = str(random.randint(1000, 9999))
	path = 'run_' + run
	os.makedirs(path)
	print "Initiated", path
	
	print "Run DFSYNTHE and save the relevant ODF tables as odf_9.bdf in the run directory. Compute Rosseland mass absorption coefficients and store them as odf_1.ros in the run directory."
	return

def dfsynthe(run):
	""" Generate opacity distribution tables for the current abundances saved in the settings and save in the run directory """
	startTime = datetime.now()

    # Standard temperatures
	dfts = ["1995.","2089.","2188.","2291.","2399.","2512.","2630.","2754.","2884.","3020.","3162.","3311.","3467.","3631.","3802.","3981.","4169.","4365.","4571.",
	        "4786.","5012.","5370.","5754.","6166.","6607.","7079.","7586.","8128.","8710.","9333.","10000.","11220.","12589.","14125.","15849.","17783.","19953.",
			"22387.","25119.","28184.","31623.","35481.","39811.","44668.","50119.","56234.","63096.","70795.","79433.","89125.","100000.","112202.","125893.","141254.",
			"158489.","177828.","199526."]
	# Standard turbulent velocities
	vs = ['0', '1', '2', '4', '8']

	# Check input
	path = 'run_' + run
	if not (os.path.isdir(path)):
		print "Cannot find the run!"
		return
	
	# Generate the XNFDF command file
	config = settings.atlas_settings()
	cards = {
	  'd_data': os.path.realpath(d_data),
	  'abundance_scale': str(float(config['abundance_scale'])),
	  'teff': str(float(config['teff'])),
	  'gravity': str(float(config['gravity'])),
	  'dfsynthe_suite': os.path.realpath(dfsynthe_suite),
	}
	for z, abundance in enumerate(config['elements']):
		cards['element_' + str(z)] = str(float(abundance))
	file = open(path + '/xnfdf.com', 'w')
	file.write(templates.xnfdf_control_start.format(**cards))
	for dft in dfts:
		cards['dft'] = dft
		file.write(templates.xnfdf_control.format(**cards))
	file.write(templates.xnfdf_control_end.format(**cards))
	file.close()
	print "Will run XNFDF to tabulate atomic and molecular number densities"
	print "Launcher created for " + str(len(dfts)) + " temperatures from " + str(min(map(float, dfts))) + " K to " + str(max(map(float, dfts))) + " K"
	
	# Run XNFDF
	os.chdir(path)
	os.system('source ./xnfdf.com')
	os.chdir(python_path)
	if (not (os.path.isfile(path + '/xnfpdf.dat'))) or (not (os.path.isfile(path + '/xnfpdfmax.dat'))):
	 	print "XNFDF did not output expected files"
	 	return
	print "XNFDF halted"
	
	# Run DFSYNTHE
	file = open(path + '/dfp00_start.com', 'w')
	file.write(templates.dfsynthe_control_start.format(**cards))
	file.close()
	file = open(path + '/dfp00_end.com', 'w')
	file.write(templates.dfsynthe_control_end.format(**cards))
	file.close()
	print "Will run DFSYNTHE to tabulate the ODFs (opacity density functions)"
	os.chdir(path)
	os.system('source ./dfp00_start.com')
	os.chdir(python_path)
	for i, dft in enumerate(dfts):
		cards['dft'] = str(int(float(dft)))
		cards['dfsynthe_control_cards'] = '0' * i + '1' + '0' * (len(dfts) - 1 - i)
		file = open(path + '/dfp00.com', 'w')
		file.write(templates.dfsynthe_control.format(**cards))
		file.close()
		os.chdir(path)
		os.system('source ./dfp00.com')
		os.chdir(python_path)
		print str(float(dft)) + " K done! (" + str(i+1) + "/" + str(len(dfts)) + ")"
	os.chdir(path)
	os.system('source ./dfp00_end.com')
	os.chdir(python_path)
	
	# Run SEPARATEDF
	print "Will run SEPARATEDF to merge the output in a single file for every standard turbulent velocity (0, 1, 2, 4 and 8 km/s)"
	for j, v in enumerate(vs):
		cards['v'] = v
		file = open(path + '/separatedf.com', 'w')
		for i, dft in enumerate(dfts):
			cards['dft'] = str(int(float(dft)))
			cards['serial'] = str(i + 10)
			file.write(templates.separatedf_control.format(**cards))
		file.write(templates.separatedf_control_end.format(**cards))
		file.close()
		os.chdir(path)
		os.system('source ./separatedf.com')
		os.chdir(python_path)
		if (not (os.path.isfile(path + '/p00big' + v + '.bdf'))) or (not (os.path.isfile(path + '/p00lit' + v + '.bdf'))):
			print "SEPARATEDF did not output expected files"
			return
		print v + " km/s done! (" + str(j+1) + "/" + str(len(vs)) + ")"
	print "SEPARATEDF halted"
	print "The ODFs are saved in p00bigV.bdf and p00litV.bdf where V is the turbulent velocity"
	print "Finished running DFSYNTHE in", datetime.now() - startTime, "s" 

def kapparos(run):
	""" Generate Rosseland mean opacities for the current abundances saved in the settings and save in the run directory """
	# Standard turbulent velocities
	vs = ['0', '1', '2', '4', '8']
	
	# Check that the DFSYNTHE run exists
	path = 'run_' + run
	for v in vs:
		if not (os.path.isfile(path + '/p00big' + v + '.bdf')):
			print "Cannot find the run!"
			return
	
	# Set up launchers for KAPPA9 and run them
	config = settings.atlas_settings()
	cards = {
	  'd_data': os.path.realpath(d_data),
	  'abundance_scale': str(float(config['abundance_scale'])),
	  'teff': str(float(config['teff'])),
	  'gravity': str(float(config['gravity'])),
	  'dfsynthe_suite': os.path.realpath(dfsynthe_suite),
	}
	for z, abundance in enumerate(config['elements']):
		cards['element_' + str(z)] = str(float(abundance))
	print "Will run KAPPA9 for every standard turbulent velocity"
	for i, v in enumerate(vs):
		cards['v'] = v
		file = open(path + '/kappa9v' + v + '.com', 'w')
		file.write(templates.kappa9_control.format(**cards))
		file.close()
		os.chdir(path)
		os.system('source ./kappa9v' + v + '.com')
		os.chdir(python_path)
		print v + " km/s done! (" + str(i+1) + "/" + str(len(vs)) + ")"
	
	# Run KAPREADTS
	file = open(path + '/kapreadts.com', 'w')
	file.write(templates.kapreadts_control.format(**cards))
	file.close()
	os.chdir(path)
	os.system('source ./kapreadts.com')
	os.chdir(python_path)
	print "Merged all velocities in a single table. Final output saved in kappa.ros"

def synthe(run, min_wl, max_wl):
	""" Run SYNTHE and save the results in spectrum.dat
        The spectrum is computed between min_wl and max_wl
	"""
	startTime = datetime.now()

	# Check that the ATLAS-9 run exists
	path = 'run_' + run
	if not (os.path.isfile(path + '/output_main.out') and os.path.isfile(path + '/output_summary.out')):
		print "Cannot find the run!"
		return
	
	# Prepare a SYNTHE friendly file
	if not (os.path.isfile(path + '/output_synthe.out')):
		file = open(path + '/output_summary.out', 'r')
		model = file.read()
		file.close()
		file = open(path + '/output_synthe.out', 'w')
		file.write(templates.synthe_prependix + model)
		file.close()
		print "Adapted the ATLAS-9 model to SYNTHE in output_synthe.out"
	else:
		print "The ATLAS-9 model has already been adapted to SYNTHE"
	
	# Generate a launcher command file
	cards = {
	  's_molecules': os.path.realpath(s_molecules),
	  's_data': os.path.realpath(s_data),
	  'synthe_suite': os.path.realpath(synthe_suite),
	  'min_wl': str(float(min_wl)),
	  'max_wl': str(float(max_wl)),
	  'synthe_solar': os.path.realpath(path + '/output_synthe.out')
	}
	file = open(path + '/synthe_launch.com', 'w')
	file.write(templates.synthe_control.format(**cards))
	file.close()
	print "Launcher created"
	
	# Run SYNTHE
	os.chdir(path)
	os.system('source ./synthe_launch.com')
	os.chdir(python_path)
	if not (os.path.isfile(path + '/f7000-7210vr2br48000ap04t4970g46k1at12.asc')):
		print "SYNTHE did not output expected files"
		return
	print "SYNTHE halted"
	
	# Save data in a NumPy friendly format
	data = np.loadtxt(path + '/f7000-7210vr2br48000ap04t4970g46k1at12.asc', unpack = True, skiprows = 2)
	print "Total data points:", len(data[0])
	np.savetxt(path + '/spectrum.dat', data.T, delimiter = ',', header = 'Wavelength [A],Line intensity [erg s^-1 cm^-2 A^-1 strad^-1],Continuum intensity [erg s^-1 cm^-2 A^-1 strad^-1],Intensity ratio')
	print "Saved the spectrum in spectrum.dat"
	
	print "Finished running SYNTHE in", datetime.now() - startTime, "s" 
	
	return

def atlas_converged(python_path, path, output):
	""" Check an ATLAS-9 model for convergence. Make sure the home directory is set to the run directory in the end
	    python_path: The path where this script lives
		path:        The run directory
		output:      The output file of ATLAS-9 (main)
	"""
	os.chdir(python_path)
	# Read the main output file
	file = open(output, 'r')
	convergence = file.read()
	file.close()
	# Find the table with convergence parameters of the last iteration. The table would contain the word "TEFF" somewhere
	# in its header. It would also be the last thing in the output file, so it is safe to assume that the lines following
	# the last mention of "TEFF" in the file are the table we need.
	file = open(path + '/output_last_iteration.out', 'w')
	
	# The table is generally space-separated, but negative signs can occasionally overflow the columns and replace the separating
	# spaces, which will confuse np.loadtxt() that I intend to use later. We want to replace all "-" with " -" to ensure that there
	# is a space in front of every number. However, "-" are also present in the scientific notation (e.g. 1.0E-10), which do not need
	# to be replaced. My bodge here is to first replace all exponents with something temporary that does not contain "-" (in my case, "E="),
	# then replace all "-" with " -" and finally bring all the exponents back.
	s = convergence[convergence.rfind('TEFF'):].replace('E-', 'E=')
	s = s.replace('-', ' -')
	s = s.replace('E=', 'E-')
	
	# If numbers are too large, they get replaced with "*********", which can also confuse np.loadtxt(). Here, we replace all those masked
	# numbers with the maximum supported number (99999.999). We are not introducing any errors here, because those numbers are only used to
	# test for convergence and whether the number is 99999.999 or something larger does not matter, as both indicate non-convergence.
	s = s.replace('*********', '99999.999')
	
	# Finally,  we run the two regular expression searches below to fix excessively long numbers that are clashing with each other. We use the
	# fact that ATLAS always outputs 3 decimal places of precision and two digits in the exponent.
	s = re.sub('(\.[0-9]{3})([0-9])', r'\1 \2', s)
	s = re.sub('(E.[0-9]{2})', r'\1 ', s)
	file.write(s)
	file.close()
	
	# Now that the last iteration table is properly formatted and available in a separate file, we can simply read it with np.loadtxt()
	# and get the convergence parameters.
	err, de = np.loadtxt(path + '/output_last_iteration.out', skiprows = 3, unpack = True, usecols = [11, 12])
	os.chdir(path)
	return err, de

def atlas(run, initial_model, iterations, vturb = '2', teff = "0", gravity = "0"):
	""" Run ATLAS-9 and save the results in model.dat
	    initial_model: the filename of the initial model in the initial models directory, "auto" for automatic.
		iterations:    total number of iterations to run. 0 for automatic
		vturb:         turbulent velocity in km/s. Must match the ODF provided.
		teff, gravity: use those values for effective temperature and gravity when provided instead of the settings.
		               This is primarily introduced for parallel processing (e.g. using TORQUE), where multiple instances
					   of ATLAS are running simultaneously on the same settings file, but with different temperatures and gravities.
	"""
	startTime = datetime.now()
	
	# Validate vturb
	vturb = str(int(vturb))
	if int(vturb) not in [0, 1, 2, 4, 8]:
		print "The Vturb value given ({}) does not appear to be valid. Vturb must be one of 0, 1, 2, 4 or 8 km/s".format(vturb)
		return
	print "Computation will be done for Vturb {} km/s".format(vturb)
	print "It is assumed (but not verified!) that a compatible ODF table is provided"
	
	# Check that the DFSYNTHE and KAPPAROS runs exist
	path = 'run_' + run
	if not (os.path.isfile(path + '/odf_1.ros') and os.path.isfile(path + '/odf_9.bdf')):
		print "Cannot find the run!"
		return
	
	# Check that the initial model is set
	if (initial_model == 'auto'):
		initial_model = show_models(True, teff, gravity)
		print "Automatically chosen initial model:", initial_model
	found = False
	files = glob.glob(atlas_init)
	for file in files:
		if file.find(initial_model) == len(file) - len(initial_model):
			initial_model = file
			found = True
			break
	if not found:
		print "Cannot find the initial model!"
		return
	
	# Generate a launcher command file
	config = settings.atlas_settings()
	if teff != "0":
		config['teff'] = teff
	if gravity != "0":
		config['gravity'] = gravity
	cards = {
	  'kapp00': os.path.realpath(kapp00),
	  'p00big2': os.path.realpath(p00big2),
	  'molecules': os.path.realpath(molecules),
	  'initial_model': os.path.realpath(initial_model),
	  'output_1': os.path.realpath(path + '/output_main.out'),
	  'output_2': os.path.realpath(path + '/output_summary.out'),
	  'atlas_exe': os.path.realpath(atlas_exe),
	  'abundance_scale': str(float(config['abundance_scale'])),
	  'teff': str(float(config['teff'])),
	  'gravity': str(float(config['gravity'])),
	  'vturb': vturb,
	}
	for z, abundance in enumerate(config['elements']):
		cards['element_' + str(z)] = str(float(abundance))
	cards.update({'iterations': templates.atlas_iterations.format(iterations = '15') * int(np.floor(int(iterations) / 15))})
	if int(iterations) % 15 != 0:
		cards['iterations'] += templates.atlas_iterations.format(iterations = str(int(iterations) % 15))
	file = open(path + '/atlas_control_start.com', 'w')
	file.write(templates.atlas_control_start.format(**cards))
	file.close()
	file = open(path + '/atlas_control.com', 'w')
	file.write(templates.atlas_control.format(**cards))
	file.close()
	file = open(path + '/atlas_control_end.com', 'w')
	file.write(templates.atlas_control_end.format(**cards))
	file.close()
	print "Launcher created"
	
	# Run ATLAS
	last_line = '[ ]+72[ ]+[^\n ]+[ ]+[^\n ]+[ ]+[^\n ]+[ ]+[^\n ]+[ ]+[^\n ]+[ ]+[^\n ]+[ ]+[^\n ]+[ ]+[^\n ]+[ ]+[^\n ]+[ ]+[^\n ]+.{21}' # This regex should match the final line in the output of a successful ATLAS-9 run (72nd layer)
	os.chdir(path)
	os.system('source ./atlas_control_start.com')
	
	# We will allow 20 minutes of processing for every 15 iterations before automatic timeout.
	# This should be more than enough.
	if (int(iterations) == 0):
		timeout = 1200
	else:
		timeout = int(1200 * int(iterations) / 15.0)
	process = pexpect.spawnu(cards['atlas_exe'], timeout = timeout)  # Launch the ATLAS executable
	process.logfile = open(cards['output_1'], "w")                   # Direct the output into a file
	# For a manual number of iterations, atlas_control.com will contain everything we want to feed into ATLAS (except the termination command, "END").
	# For an automatic number of iterations, we still want to run everything that is in this file, but we will have to iterate manually in the end.
	with open('./atlas_control.com') as f:
		content = f.readlines()
	# Feed every line from the file into the running instance of ATLAS
	for line in content:
		line = line.rstrip("\n\r")
		if line == '':
			continue
		process.sendline(line)
	if (int(iterations) == 0):
		print "Starting automatic iterations..."
		# Do 15 iterations
		process.send(templates.atlas_iterations.format(iterations = 15))
		# Wait for ATLAS to begin the last of the 15 iterations
		process.expect(unicode('ITERATION 15'))
		# Wait for ATLAS to end the 15th iteration
		process.expect(unicode(last_line))
		# Check for covergence
		err, de = atlas_converged(python_path, path, cards['output_1'])
		print "15 iterations completed: max[abs(err)] =", np.max(np.abs(err)), "| max[abs(de)] =", np.max(np.abs(de))
		max_i = 30
		i = 0
		# Keep going until converged, or until some limit is reached
		while (np.max(np.abs(err)) > 1) or (np.max(np.abs(de)) > 10):
			i += 1
			if i == max_i:
				print "Exceeded the maximum number of iterations ;("
				break
			process.send(templates.atlas_iterations.format(iterations = 15))
			process.expect(unicode('ITERATION 15'))
			process.expect(unicode(last_line))
			err_old = np.max(np.abs(err))
			de_old = np.max(np.abs(de))
			err, de = atlas_converged(python_path, path, cards['output_1'])
			print str(i * 15 + 15) + " iterations completed: max[abs(err)] =", np.max(np.abs(err)), "| max[abs(de)] =", np.max(np.abs(de))
			if (err_old - np.max(np.abs(err)) + de_old - np.max(np.abs(de))) < 0.1 and (i > 10):
				print "The model is unlikely to converge any better ;("
				break
		process.logfile = None   # This is necessary, so that our "END" does not show up in the output.
	# Terminate ATLAS
	process.sendline('END')
	process.expect(pexpect.EOF)
	print "ATLAS-9 halted"
	
	os.system('source ./atlas_control_end.com')
	os.chdir(python_path)
	if not (os.path.isfile(cards['output_1']) and os.path.isfile(cards['output_2'])):
		print "ATLAS-9 did not output expected files"
		return

	# Check convergence
	err, de = atlas_converged(python_path, path, cards['output_1'])
	print ""
	print "Final convergence: max[abs(err)] =", np.max(np.abs(err)), "| max[abs(de)] =", np.max(np.abs(de))
	if (np.max(np.abs(err)) > 1) or (np.max(np.abs(de)) > 10):
		print "Failed to converge"
	
	# Save data in a NumPy friendly format
	os.chdir(python_path)
	file = open(path + '/output_summary.out', 'r')
	data = file.read()
	file.close()
	file = open(path + '/model.dat', 'w')
	file.write(data[data.rfind('RHOX'):data.rfind('PRADK')])
	file.close()
	data = np.loadtxt(path + '/model.dat', unpack = True, skiprows = 1, usecols = [0, 1, 2])
	data[2] = 0.000001 * data[2]    # Bars conversion
	np.savetxt(path + '/model.dat', data.T, delimiter = ',', header = 'Mass Column Density [g cm^-2],Temperature [K],Pressure [Bar]')
	print "Saved the model in model.dat"
	
	print "Finished running ATLAS-9 in", datetime.now() - startTime, "s" 
	return

	
def test_setup():
	""" Automatic detection of issues with the ATLAS/SYNTHE setup. The function will check that all the necessary files
	    are in place and the command line environment is appropriate. If the function runs with no output, everything is good
		to go. Otherwise, identified problems will be shown.
	"""
	files = {}
	# Supporting Python scripts
	files[0] = ['settings.py', 'templates.py', 'wavelength.py']
	# ATLAS files
	files[1] = [molecules]
	# SYNTHE files
	files[2] = np.core.defchararray.add(s_data + '/', ['continua.dat', 'fchighlines.bin', 'fclowlines.bin', 'he1tables.dat', 'molecules.dat'])
	# DFSYNTHE files
	files[3] = np.core.defchararray.add(d_data + '/', ['continua.dat', 'molecules.dat', 'pfiron.dat', 'repacked_lines/diatomicsdf.bin',
	                                                   'repacked_lines/h2olinesdf.bin', 'repacked_lines/highlinesdf.bin',
													   'repacked_lines/lowlinesdf.bin', 'repacked_lines/nltelinesdf.bin', 'repacked_lines/tiolinesdf.bin'])
	# SYNTHE molecules
	files[4] = np.core.defchararray.add(s_molecules + '/', ['c2ax.asc', 'c2ba.asc', 'c2ba.dat', 'c2da.dat', 'c2dabrookek.asc', 'c2ea.asc',
	                                                        'c2ea.dat', 'chbx.dat', 'chcx.dat', 'chmasseron.asc', 'cnax.dat', 'cnaxbrookek.asc',
															'cnbx.dat', 'cnbxbrookek.asc', 'cnxx12brooke.asc', 'coax.asc', 'coax.dat', 'coxx.asc',
															'eschwenke.bin', 'h2.asc', 'h2bx.dat', 'h2ofastfix.bin', 'h2xx.asc', 'hdxx.asc',
															'mgh.asc', 'mghbx.dat', 'nh.asc', 'nhax.dat', 'nhca.dat', 'ohupdate.asc', 'sihax.asc',
															'sihax.dat', 'sioax.asc', 'sioex.asc', 'sioxx.asc', 'tioschwenke.bin', 'vo.asc',
															'vo.readme', 'vomyt.asc'])
	# Executables
	files[5] = [atlas_exe]
	files[6] = np.core.defchararray.add(synthe_suite + '/', ['broaden.exe', 'converfsynnmtoa.exe',
	                                                        'fluxaverage1a_nmtoa.exe',
															'rgfalllinesnew.exe', 'rh2ofast.exe', 'rmolecasc.exe', 'rotate.exe', 'rpredict.exe',
															'rschwenk.exe', 'spectrv.exe', 'synbeg.exe', 'synthe.exe',
															'xnfpelsyn.exe'])
	files[7] = np.core.defchararray.add(dfsynthe_suite + '/', ['dfsortp.exe', 'dfsynthe.exe', 'kappa9.exe', 'kapreadts.exe',
															   'separatedf.exe', 'xnfdf.exe'])
	# Default Vega spectrum
	files[8] = [default_vega]
	
	file_errors = {
	  0: "Download from BasicATLAS repository and save in the same directory as basic.py",
	  1: "Molecular table for ATLAS-9. Point the 'molecules' variable to it in basic.py",
	  2: "SYNTHE file. Point 's_data' to its directory in basic.py",
	  3: "DFSYNTHE file. Point 'd_data' to its directory in basic.py",
	  4: "SYNTHE molecules. Point 's_molecules' to its directory in basic.py",
	  5: "Main ATLAS-9 executable. Compile and point 'atlas_exe' to it in basic.py",
	  6: "SYNTHE executable. Point 'synthe_suite' to its directory in basic.py",
	  7: "DFSYNTHE executable. Point 'dfsynthe_suite' to its directory in basic.py",
	  8: "Download from BasicATLAS repository and point 'default_vega' to it in basic.py",
	}
	
	for filetype in files.keys():
		for file in files[filetype]:
			if not os.path.isfile(file):
				print "{} not found: {}".format(file, file_errors[filetype])
	
	# Litmus test for a Linux-like shell
	if os.popen('echo "test" | grep "test"').read().strip() != 'test':
		print "The command line environment does not seem to understand Linux commands. On Windows, use CygWin"
	
	if len(glob.glob(atlas_init)) == 0:
		"Cannot find any initial models for ATLAS-9. Point 'atlas_init' to their directory in basic.py"
	
	if len(glob.glob(trans_dir)) == 0:
		"Cannot find any filter transmission functions. Point 'trans_dir' to their directory in basic.py"
	
	return


if len(sys.argv) <= 1:
	print "Function name expected"
else:
	getattr(sys.modules[__name__], sys.argv[1])(*sys.argv[2:])
