from datetime import datetime
import os
import re
import numpy as np
from shutil import copyfile
import subprocess
import time
from scipy.optimize import brentq

from settings import Settings
import templates

# Path to the home directory of the library
python_path = os.path.dirname(os.path.realpath(__file__))

# Where to look for restart files
restart_paths = [python_path + '/restarts']

def notify(message, silent):
    """
    Print message "message" if "silent" is True. This function is used in place of prints throughout the code to allow
    us to easily silence them all
    """
    if not silent:
        print(message)

def cmd(command):
    """
    Run a shell command and, if any output is produced, print it including both STDOUT and STDERR
    """
    session = subprocess.Popen(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
    stdout, stderr = session.communicate()
    stdout = stdout.decode().strip()
    stderr = stderr.decode().strip()
    if stdout != '':
        print(stdout)
    if stderr != '':
        print(stderr)

def bin_spec(wl, flux, num_bins = 1000):
    """
    Bin a given spectrum ("wl" and "flux") into a given number of bins
    """
    hist_sum = np.histogram(wl, bins = num_bins, weights = flux)
    hist_count = np.histogram(wl, bins = num_bins)
    return np.array(hist_sum[1][1:] + hist_sum[1][:-1])[hist_count[0] > 0] / 2.0, hist_sum[0][hist_count[0] > 0] / hist_count[0][hist_count[0] > 0]

def atlas_converged(run_dir):
    """
    Calculate convergence parameters for a completed or an ongoing ATLAS run.

    arguments:
        run_dir      :         Output directory of the ATLAS run
    """
    # Read the main output file
    file = open(run_dir + '/output_main.out', 'r')
    convergence = file.read()
    file.close()
    # Find the table with convergence parameters of the last iteration. The table would contain the word "TEFF" somewhere
    # in its header. It would also be the last thing in the output file, so it is safe to assume that the lines following
    # the last mention of "TEFF" in the file are the table we need.
    file = open(run_dir + '/output_last_iteration.out', 'w')

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
    s = s.replace('E=', 'E-')

    # Finally,  we run the two regular expression searches below to fix excessively long numbers that are clashing with each other. We use the
    # fact that ATLAS always outputs 3 decimal places of precision and two digits in the exponent.
    s = re.sub('(\.[0-9]{3})([0-9])', r'\1 \2', s)
    s = re.sub('(E.[0-9]{2})', r'\1 ', s)
    file.write('\n'.join(s.strip().split('\n')[:-1]))
    file.close()

    # Now that the last iteration table is properly formatted and available in a separate file, we can simply read it with np.loadtxt()
    # and get the convergence parameters.
    try:
        err, de = np.loadtxt(run_dir + '/output_last_iteration.out', skiprows = 3, unpack = True, usecols = [11, 12])
    except:
        err = 99999.999
        de = 99999.999
    return err, de

def atlas(output_dir, settings = Settings(), restart = 'auto', niter = 0, ODF = python_path + '/data/solar_ODF', silent = False):
    """
    Run ATLAS-9 to calculate a model stellar atmosphere

    arguments:
        output_dir     :     Directory to store the output. Must NOT exist
        settings       :     Object of class Settings() with atmosphere parameters
        restart        :     Initial guess for the temperature profile (restart). This can point either to a file of type
                             "output_summary.out" (e.g. from restarts/) or the output directory of an existing ATLAS run.
                             Set to "auto" to select the closest restart file (by teff, logg, zscale) from the library
                             of available restarts in atlas.restart_paths. Alternatively, set to "grey" to use a grey
                             atmosphere profile under the two-stream approximation
        niter          :     Number of iterations. Use 0 to iterate until convergence (or lack of progress)
        ODF            :     Output directory of a DFSYNTHE run with required Opacity Distribution Functions and Rosseland
                             mean opacities
        silent         :     Do not print status messages
    """
    startTime = datetime.now()
    
    # Organize the working directory
    if os.path.isdir(output_dir):
        raise ValueError('Directory {} already exists'.format(output_dir))
    else:
        os.mkdir(output_dir)
        output_dir = os.path.realpath(output_dir)

    # Validate the provided ODF
    ODF_meta = meta(ODF)
    if ODF_meta['type'] != 'DFSYNTHE':
        raise ValueError('Directory {} does not have ODFs'.format(ODF))
    settings.check_ODF(ODF_meta)

    # Prepare ODF
    if os.path.isfile(ODF + '/p00big{}.bdf'.format(settings.vturb)):
        copyfile(ODF + '/p00big{}.bdf'.format(settings.vturb), output_dir + '/odf_9.bdf')
        copyfile(ODF + '/kappa.ros'.format(settings.vturb), output_dir + '/odf_1.ros')
    else:
        vturb_available = [i for o in map(lambda x: re.findall('p00big([0-9]+)\.bdf', x), os.listdir(ODF)) for i in o]
        raise ValueError('ODF not calculated for vturb={}. Available vturb: {}'.format(settings.vturb, vturb_available))

    # Prepare restart
    prepare_restart(restart, output_dir + '/restart.dat', teff = settings.teff, logg = settings.logg, zscale = settings.zscale)
    
    # Generate a launcher command file
    cards = {
      'molecules': python_path + '/data/atlas_files/molecules.dat',
      'initial_model': output_dir + '/restart.dat',
      'output_1': output_dir + '/output_main.out',
      'output_2': output_dir + '/output_summary.out',
      'atlas_exe': python_path + '/bin/atlas9mem.exe',
      'abundance_scale': 10 ** float(settings.zscale),
      'teff': settings.teff,
      'gravity': settings.logg,
      'vturb': str(int(settings.vturb)),
      'output_dir': output_dir,
    }
    for z, abundance in enumerate(settings.atlas_abun()):
        cards['element_' + str(z)] = abundance
    cards['element_1'] = settings.atlas_abun()[1]
    cards['element_2'] = settings.atlas_abun()[2]
    if niter != 0:
        cards.update({'iterations': templates.atlas_iterations.format(iterations = '15') * int(np.floor(int(niter) / 15))})
        if int(niter) % 15 != 0:
            cards['iterations'] += templates.atlas_iterations.format(iterations = str(int(niter) % 15))
    else:
        cards.update({'iterations': templates.atlas_iterations.format(iterations = '15')})
    file = open(output_dir + '/atlas_control_start.com', 'w')
    file.write(templates.atlas_control_start.format(**cards))
    file.close()
    file = open(output_dir + '/atlas_control.com', 'w')
    file.write(templates.atlas_control.format(**cards))
    file.close()
    file = open(output_dir + '/atlas_control_end.com', 'w')
    file.write(templates.atlas_control_end.format(**cards))
    file.close()
    notify("Launcher created", silent)

    # Run ATLAS
    cmd('bash {}/atlas_control_start.com'.format(output_dir))

    # For a manual number of iterations, it is sufficient to source atlas_control.com
    # For an automatic number of iterations, we will source atlas_control.com multiple times replacing the initial model with the output each time
    cmd('bash {}/atlas_control.com'.format(output_dir))
    if (int(niter) == 0):
        notify("Starting automatic iterations...", silent)
        # Check for covergence
        err, de = atlas_converged(output_dir)
        notify("15 iterations completed: max[abs(err)] = " + str(np.max(np.abs(err))) + " | max[abs(de)] = " + str(np.max(np.abs(de))), silent)
        max_i = 30
        i = 0
        # Keep going until converged, or until some limit is reached
        while (np.max(np.abs(err)) > 1) or (np.max(np.abs(de)) > 10):
            i += 1
            if i == max_i:
                notify("Exceeded the maximum number of iterations ;(", silent)
                break
            # Replace initial model with output
            os.rename(output_dir + '/fort.7', output_dir + '/fort.3')

            cmd('bash {}/atlas_control.com'.format(output_dir))
            err_old = np.max(np.abs(err))
            de_old = np.max(np.abs(de))
            err, de = atlas_converged(output_dir)
            notify(str(i * 15 + 15) + " iterations completed: max[abs(err)] = " + str(np.max(np.abs(err))) + " | max[abs(de)] = " + str(np.max(np.abs(de))), silent)
            if (err_old - np.max(np.abs(err)) + de_old - np.max(np.abs(de))) < 0.1 and (i > 10):
                notify("The model is unlikely to converge any better ;(", silent)
                break
    notify("ATLAS-9 halted", silent)
    validate_run(output_dir)
    
    cmd('bash {}/atlas_control_end.com'.format(output_dir))
    if not (os.path.isfile(cards['output_1']) and os.path.isfile(cards['output_2'])):
        raise ValueError("ATLAS-9 did not output expected files")

    # Check convergence
    err, de = atlas_converged(output_dir)
    notify("\nFinal convergence: max[abs(err)] = " + str(np.max(np.abs(err))) + " | max[abs(de)] = " + str(np.max(np.abs(de))), silent)
    if (np.max(np.abs(err)) > 1) or (np.max(np.abs(de)) > 10):
        notify("Failed to converge", silent)

    # Save data in a NumPy friendly format
    file = open(cards['output_2'], 'r')
    data = file.read()
    file.close()
    file = open(output_dir + '/model.dat', 'w')
    file.write(data[data.rfind('RHOX'):data.rfind('PRADK')])
    file.close()
    data = np.loadtxt(output_dir + '/model.dat', unpack = True, skiprows = 1, usecols = [0, 1, 2])
    data[2] = 0.000001 * data[2]    # Bars conversion
    np.savetxt(output_dir + '/model.dat', data.T, delimiter = ',', header = 'Mass Column Density [g cm^-2],Temperature [K],Pressure [Bar]')
    notify("Saved the model in model.dat", silent)

    notify("Finished running ATLAS-9 in " + str(datetime.now() - startTime) + " s", silent)

def synbeg(min_wl, max_wl, res):
    """
    Calculate the total number of wavelength points in a given region at given resolution. The function mimics the
    calculation carried out by synbeg.for and should produce the same output

    arguments:
        min_wl         :     Minimum wavelength of the calculation (nm)
        max_wl         :     Maximum wavelength of the calculation (nm)
        res            :     Sampling resolution (lambda / delta_lambda)
    """
    ratio = 1.0 + 1.0 / res
    ratiolg = np.log(ratio)
    ixwlbeg = int(np.log(min_wl) / ratiolg)
    wbegin = np.e ** (ixwlbeg * ratiolg)
    if (wbegin < min_wl):
        ixwlbeg += 1
        wbegin = np.e ** (ixwlbeg * ratiolg)
    ixwlend = int(np.log(max_wl) / ratiolg)
    wllast = np.e ** (ixwlend * ratiolg)
    if (wllast > max_wl):
        ixwlend -= 1
        wllast = np.e ** (ixwlend * ratiolg)
    return int(ixwlend - ixwlbeg + 1)

def synthe(output_dir, min_wl, max_wl, res = 600000.0, vturb = 0.0, buffsize = 2010001, silent = False):
    """
    Run SYNTHE to calculate the emergent spectrum corresponding to an existing ATLAS model

    arguments:
        output_dir     :     Directory to store the output. Must contain the output of a previously executed ATLAS run
        min_wl         :     Minimum wavelength of the calculation (nm)
        max_wl         :     Maximum wavelength of the calculation (nm)
        res            :     Sampling resolution (lambda / delta_lambda)
        vturb          :     Turbulent velocity [km/s]
        buffsize       :     Maximum allowed number of wavelength points per calculation. If the required number of points
                             exceeds this value, the calculation will be split into multiple batches. This argument is
                             introduced as SYNTHE allocates a buffer of finite size and cannot handle more wavelength
                             points than that. The default value, 2010001, corresponds to the default buffer size in
                             synthe.for
        silent         :     Do not print status messages
    """
    startTime = datetime.now()

    # Check that the ATLAS-9 run exists
    output_dir = os.path.realpath(output_dir)
    if not (os.path.isfile(output_dir + '/output_main.out') and os.path.isfile(output_dir + '/output_summary.out')):
        raise ValueError('ATLAS run output not found in {}'.format(output_dir))

    # Prepare a SYNTHE friendly file
    if not (os.path.isfile(output_dir + '/output_synthe.out')):
        file = open(output_dir + '/output_summary.out', 'r')
        model = file.read()
        file.close()
        file = open(output_dir + '/output_synthe.out', 'w')
        file.write(templates.synthe_prependix + model)
        file.close()
        notify("Adapted the ATLAS-9 model to SYNTHE in output_synthe.out", silent)
    else:
        notify("The ATLAS-9 model has already been adapted to SYNTHE", silent)

    synthe_num = 0            # Batch number
    completed = False         # The last batch sets this flag to True
    current_min_wl = min_wl   # Start wavelength of the current batch
    while not completed:
        synthe_num += 1

        # Determine the end wavelength
        if synbeg(current_min_wl, max_wl, res) > buffsize:
            current_max_wl = int(brentq(lambda x: synbeg(current_min_wl, x, res) - buffsize, current_min_wl, max_wl))
            if current_max_wl == current_min_wl:
                raise ValueError('Requested resolution too high for buffer size')
        else:
            current_max_wl = max_wl
            completed = True

        # Generate a launcher command file
        cards = {
          's_files': python_path + '/data/synthe_files/',
          'd_files': python_path + '/data/dfsynthe_files/',
          'synthe_suite': python_path + '/bin/',
          'airorvac': 'AIR',
          'wlbeg': float(current_min_wl),
          'wlend': float(current_max_wl),
          'resolu': float(res),
          'turbv': float(vturb),
          'ifnlte': 0,
          'linout': 30,
          'cutoff': 0.0001,
          'ifpred': 1,
          'nread': 0,
          'synthe_solar': output_dir + '/output_synthe.out',
          'output_dir': output_dir,
          'synthe_num': synthe_num,
        }
        file = open(output_dir + '/synthe_launch.com', 'w')
        file.write(templates.synthe_control.format(**cards))
        file.close()
        notify("Launcher created for wavelength range ({}, {}), batch {}. Expected number of points: {} (buffer {})".format(current_min_wl, current_max_wl, synthe_num, synbeg(current_min_wl, current_max_wl, res), buffsize), silent)

        # Run SYNTHE
        cmd('bash {}/synthe_launch.com'.format(output_dir))
        if not (os.path.isfile(output_dir + '/synthe_{}/spectrum.asc'.format(cards['synthe_num']))):
            raise ValueError("SYNTHE did not output expected files")
        notify("SYNTHE halted", silent)
        validate_run(output_dir)

        current_min_wl = current_max_wl

    # Merge all output files and save the data as ASCII file
    data = np.empty([4, 0])
    for i in range(1, synthe_num + 1):
        data = np.append(data, np.loadtxt(output_dir + '/synthe_{}/spectrum.asc'.format(i), unpack = True, skiprows = 2), axis = 1)
    notify("Total data points: " + str(len(data[0])), silent)
    np.savetxt(output_dir + '/spectrum.dat', data.T, delimiter = ',', header = 'Wavelength [A],Line intensity [erg s^-1 cm^-2 A^-1 strad^-1],Continuum intensity [erg s^-1 cm^-2 A^-1 strad^-1],Intensity ratio')
    notify("Saved the spectrum in spectrum.dat", silent)

    notify("Finished running SYNTHE in " + str(datetime.now() - startTime) + " s", silent)


def dfsynthe(output_dir, settings, silent = False):
    """
    Run DFSYNTHE and KAPPAROS to calculate Opacity Distribution Functions (ODFs) and Rosseland mean opacities for a given
    set of chemical abundances
    The calculation is carried out for 5 turbulent velocities (0, 1, 2, 4 and 8 km/s)

    arguments:
        output_dir     :     Directory to store the output. Must NOT exist
        settings       :     Object of class Settings() with required chemical abundances
        silent         :     Do not print status messages
    """
    startTime = datetime.now()

    # Standard temperatures
    dfts = ["1995.","2089.","2188.","2291.","2399.","2512.","2630.","2754.","2884.","3020.","3162.","3311.","3467.","3631.","3802.","3981.","4169.","4365.","4571.",
            "4786.","5012.","5370.","5754.","6166.","6607.","7079.","7586.","8128.","8710.","9333.","10000.","11220.","12589.","14125.","15849.","17783.","19953.",
            "22387.","25119.","28184.","31623.","35481.","39811.","44668.","50119.","56234.","63096.","70795.","79433.","89125.","100000.","112202.","125893.","141254.",
            "158489.","177828.","199526."]
    # Standard turbulent velocities
    vs = ['0', '1', '2', '4', '8']

    # Organize the working directory
    if os.path.isdir(output_dir):
        raise ValueError('Directory {} already exists'.format(output_dir))
    else:
        os.mkdir(output_dir)
        output_dir = os.path.realpath(output_dir)

    # Generate the XNFDF command file
    cards = {
      'd_data': python_path + '/data/dfsynthe_files/',
      'abundance_scale': 10 ** settings.zscale,
      'dfsynthe_suite': python_path + '/bin/',
      'output_dir': output_dir,
    }
    for z, abundance in enumerate(settings.atlas_abun()):
        cards['element_' + str(z)] = float(abundance)
    cards['element_1'] = settings.atlas_abun()[1]
    cards['element_2'] = settings.atlas_abun()[2]
    file = open(output_dir + '/xnfdf.com', 'w')
    file.write(templates.xnfdf_control_start.format(**cards))
    for dft in dfts:
        cards['dft'] = dft
        file.write(templates.xnfdf_control.format(**cards))
    file.write(templates.xnfdf_control_end.format(**cards))
    file.close()
    notify('Will run XNFDF to tabulate atomic and molecular number densities', silent)
    notify('Launcher created for ' + str(len(dfts)) + ' temperatures from ' + str(min(map(float, dfts))) + ' K to ' + str(max(map(float, dfts))) + ' K', silent)
    
    # Run XNFDF
    cmd('bash {}/xnfdf.com'.format(output_dir))
    print(output_dir + '/xnfpdf.dat')
    if (not (os.path.isfile(output_dir + '/xnfpdf.dat'))) or (not (os.path.isfile(output_dir + '/xnfpdfmax.dat'))):
         raise ValueError('XNFDF did not output expected files')
    notify('XNFDF halted', silent)
    
    # Run DFSYNTHE
    file = open(output_dir + '/dfp_start.com', 'w')
    file.write(templates.dfsynthe_control_start.format(**cards))
    file.close()
    file = open(output_dir + '/dfp_end.com', 'w')
    file.write(templates.dfsynthe_control_end.format(**cards))
    file.close()
    notify('Will run DFSYNTHE to tabulate the ODFs (Opacity Distribution Functions)', silent)
    cmd('bash {}/dfp_start.com'.format(output_dir))
    for i, dft in enumerate(dfts):
        cards['dft'] = str(int(float(dft)))
        cards['dfsynthe_control_cards'] = '0' * i + '1' + '0' * (len(dfts) - 1 - i)
        file = open(output_dir + '/dfp.com', 'w')
        file.write(templates.dfsynthe_control.format(**cards))
        file.close()
        cmd('bash {}/dfp.com'.format(output_dir))
        notify(str(float(dft)) + ' K done! (' + str(i+1) + '/' + str(len(dfts)) + ')', silent)
    cmd('bash {}/dfp_end.com'.format(output_dir))
    
    # Run SEPARATEDF
    notify('Will run SEPARATEDF to merge the output in a single file for every standard turbulent velocity (0, 1, 2, 4 and 8 km/s)', silent)
    for j, v in enumerate(vs):
        cards['v'] = v
        file = open(output_dir + '/separatedf.com', 'w')
        for i, dft in enumerate(dfts):
            cards['dft'] = str(int(float(dft)))
            cards['serial'] = str(i + 10)
            file.write(templates.separatedf_control.format(**cards))
        file.write(templates.separatedf_control_end.format(**cards))
        file.close()
        cmd('bash {}/separatedf.com'.format(output_dir))
        if (not (os.path.isfile(output_dir + '/p00big' + v + '.bdf'))) or (not (os.path.isfile(output_dir + '/p00lit' + v + '.bdf'))):
            raise ValueError('SEPARATEDF did not output expected files')
        notify(v + " km/s done! (" + str(j+1) + "/" + str(len(vs)) + ")", silent)
    notify('SEPARATEDF halted', silent)
    notify("Finished running DFSYNTHE in " + str(datetime.now() - startTime) + ' s', silent)
        
    # Run KAPPAROS
    notify('Will run KAPPA9 for every standard turbulent velocity', silent)
    for i, v in enumerate(vs):
            cards['v'] = v
            file = open(output_dir + '/kappa9v' + v + '.com', 'w')
            file.write(templates.kappa9_control.format(**cards))
            file.close()
            cmd('bash {}/kappa9v'.format(output_dir) + v + '.com')
            notify(v + ' km/s done! (' + str(i+1) + '/' + str(len(vs)) + ')', silent)
    
    # Run KAPREADTS
    file = open(output_dir + '/kapreadts.com', 'w')
    file.write(templates.kapreadts_control.format(**cards))
    file.close()
    cmd('bash {}/kapreadts.com'.format(output_dir))
    notify('Merged all velocities in a single table. Final output saved in kappa.ros', silent)
    validate_run(output_dir)

def meta(run_dir):
    """
    Get meta data for an output directory (ATLAS, SYNTHE of DFSYNTHE)

    arguments:
        run_dir        :     Output directory of interest
    """
    if not os.path.isdir(run_dir):
        raise ValueError('Run directory {} not found!'.format(run_dir))
    if os.path.isfile(run_dir + '/xnfdf.out'):
        return meta_dfsynthe(run_dir)
    elif os.path.isfile(run_dir + '/output_main.out'):
        return meta_atlas(run_dir)
    else:
        raise ValueError('Run {} type unknown!'.format(run_dir))

def meta_dfsynthe(run_dir):
    """
    Get meta data for an output directory (DFSYNTHE)

    arguments:
        run_dir        :     Output directory of interest

    returns:
        A dictionary of meta data with the following keys:
            abun         :       Enhancements of individual chemical elements [dex over solar]
            Y            :       Helium mass fraction
            zscale       :       Metallicity, [M/H] [dex over solar]
            type         :       Set to "DFSYNTHE" for a DFSYNTHE run
    """
    elements_received, params_received = parse_atlas_abundances(run_dir + '/xnfdf.out', classic_style = False, lookbehind = 1, params = ['0XSCALE'])
    output = Settings().abun_atlas_to_std(elements_received, np.log10(params_received['0XSCALE']))
    output['type'] = 'DFSYNTHE'
    return output

def meta_atlas(run_dir):
    """
    Get meta data for an output directory (ATLAS, SYNTHE)

    arguments:
        run_dir        :     Output directory of interest

    returns:
        A dictionary of meta data with the following keys:
            abun         :       Enhancements of individual chemical elements [dex over solar]
            Y            :       Helium mass fraction
            zscale       :       Metallicity, [M/H] [dex over solar]
            teff         :       Effective temperature [K]
            logg         :       Surface gravity [log10(CGS)]
            vturb        :       Turbulent velocity [km/s]
            type         :       Set to "ATLAS" for a pure ATLAS-9 run or "SYNTHE" for an ATLAS/SYNTHE run
            res          :       If synthe == True, resolution of the spectrum (lambda/delta_lambda)
            synthe_vturb :       Turbulent velocity in SYNTHE [km/s]
    """
    elements_received, params_received = parse_atlas_abundances(run_dir + '/output_main.out', classic_style = False, lookbehind = 2, params = ['0XSCALE', 'TEFF', 'LOG G'])
    output = Settings().abun_atlas_to_std(elements_received, np.log10(params_received['0XSCALE']))
    output['teff'] = params_received['TEFF']
    output['logg'] = params_received['LOG G']
    vturb = validate_run(run_dir, return_received_vturb = True)
    output['vturb'] = vturb * 1e-5
    output['type'] = 'ATLAS'

    if os.path.isfile(run_dir + '/synthe_launch.com'):
        output['type'] = 'SYNTHE'
        synthe_params = validate_run(run_dir, return_received_synthe = True)
        output['res'] = synthe_params['resolu']
        output['synthe_vturb'] = synthe_params['turbv']

    return output

def parse_atlas_abundances(file, classic_style = True, lookahead = 0, lookbehind = 0, params = [], to_float = True):
    """
    Load chemical abundances as well as other auxiliary parameters from one of the ATLAS/SYNTHE/DFSYNTHE files

    arguments:
        file              :         File to read abundances from
        classic_style     :         If True, the "classic" style of abundance listing is assumed, i.e. the one with
                                    "ABUNDANCE CHANGE" and "ABUNDANCE SCALE". E.g. in atlas_control.com. Otherwise,
                                    the explicit style is assumed with symbols of chemical elements such as the one
                                    in output_main.out
        lookahead         :         Auxiliary parameter definitions will be searched within the lines of the abundance
                                    listing as well as this many lines after the abundance listing
        lookbehind        :         Auxiliary parameter definitions will be searched within the lines of the abundance
                                    listing as well as this many lines behind the abundance listing
        params            :         Names of auxiliary parameters to search for. For example, "TEFF". If a parameter
                                    has multiple values (e.g. "SCALE 72 -6.875 0.125 6000   6.00000"), the numerical
                                    index of the required value must be specified after "/". E.g. "SCALE/1" for 72,
                                    "SCALE/2" for -6.875 etc
        to_float          :         Typecast retrieved values of auxiliary parameters to float
    """
    f = open(file, 'r')
    content = f.read()
    f.close()
    elements = [0]

    if not classic_style:
        # Small correction to make sure a space is present after 0XSCALE when the number that follows is too long
        content = content.replace('0XSCALE', '0XSCALE ')

        symbols = Settings().abun_solar().keys()
        start = re.search('LI[0-9 .-]+BE[0-9 .-]+B', content).span()[0]
        end = re.search('BK[0-9 .-]+CF[0-9 .-]+ES[0-9 .-]+', content).span()[1]
        start = content[:content[:start].rfind('\n')].rfind('\n')
        element_listing = content[start : end]
        for symbol in symbols:
            elements += [float(re.findall('[^A-Z]{}([0-9 .-]+)'.format(symbol.upper() + ' ' * (2 - len(symbol))), element_listing)[0].strip())]
    else:
        start = re.search('ABUNDANCE CHANGE +3 +[0-9.-]+ +4 +[0-9.-]+ +5 +', content).span()[0]
        end = re.search('ABUNDANCE CHANGE +99 +[0-9.-]+ ?', content).span()[1]
        start = content[:content[:start].rfind('\n')].rfind('\n')
        element_listing = content[start:end]
        for i in range(1, 100):
            elements += [float(re.findall('[^0-9]{} +([0-9-]+\.[0-9]+)'.format(i), element_listing)[0].strip())]

    if len(params) != 0:
        for i in range(lookbehind):
            start = content[:start].rfind('\n')
        for i in range(lookahead):
            end += content[end:].find('\n') + 1
        listing = content[start:end]

        output_params = {}
        for param in params:
            regex = '{} +([^ \\n]+)'
            if len(param.split('/')) == 2:
                depth = int(param.split('/')[1])
                regex = regex.format(param.split('/')[0])
                for i in range(depth - 1):
                    regex = regex.replace('(', '').replace(')', '') + ' +([^ \\n]+)'
            else:
                regex = regex.format(param)
            output_params[param] = re.findall(regex, listing)[0]
            if to_float:
                output_params[param] = float(output_params[param])
        return elements, output_params

    return elements

def validate_run(run_dir, return_received_vturb = False, return_received_synthe = False, silent = False):
    """
    Confirm that the input values provided to ATLAS/SYNTHE/DFSYNTHE in a given run match the ATLAS/SYNTHE/DFSYNHTE's
    interpretation of them. Due to the explicit formatting requirements, sometimes this is not the case. The run
    of interest is specified in "run_dir" (type is identified automatically). Returns True when the validation
    passes and raises an exception when it does not

    arguments:
        run_dir                  :           Directory with output of the run requiring validation
        return_received_vturb    :           If the run is an ATLAS run, abort validation and return the value of
                                             VTURB received by ATLAS
        return_received_synthe   :           If the run is a SYNTHE run, abort validation and return the values of
                                             all parameters received by SYNTHE as a dictionary
        silent                   :           Do not print status messages (none will be printed regardless if
                                             return_received_vturb or return_received_synthe is set to True)
    """
    if not os.path.isdir(run_dir):
        raise ValueError('Run directory {} not found!'.format(run_dir))

    # ATLAS run
    if os.path.isfile(run_dir + '/atlas_control.com'):
        elements_requested, params_requested = parse_atlas_abundances(run_dir + '/atlas_control.com', lookbehind = 4, params = ['VTURB', 'ABUNDANCE SCALE', 'SCALE 72/3', 'SCALE 72/4'])
        elements_received, params_received = parse_atlas_abundances(run_dir + '/output_main.out', classic_style = False, lookbehind = 2, params = ['0XSCALE', 'TEFF', 'LOG G'])

        # Determine the received value of VTURB
        f = open(run_dir + '/output_main.out', 'r')
        content = f.read()
        f.close()
        start = content.find('RHOX         T        P        XNE')
        start = content[start:].find('\n') + start
        end = start
        for i in range(2):
            end += content[end:].find('\n') + 1
        vturb_received = float(np.loadtxt([content[start:end].strip()], dtype = str)[7])
        if return_received_vturb:
            return vturb_received

        # Check for matches and raise exceptions
        for i in range(len(elements_requested)):
            if elements_requested[i] != elements_received[i]:
                raise ValueError('Element {} requested/received mismatch: {} vs {}'.format(i, elements_requested[i], elements_received[i]))
        if params_requested['ABUNDANCE SCALE'] != params_received['0XSCALE']:
            raise ValueError('Metallicity requested/received mismatch: {} vs {}'.format(params_requested['ABUNDANCE SCALE'], params_received['0XSCALE']))
        if params_requested['SCALE 72/3'] != params_received['TEFF']:
            raise ValueError('Teff requested/received mismatch: {} vs {}'.format(params_requested['SCALE 72/3'], params_received['TEFF']))
        if params_requested['SCALE 72/4'] != params_received['LOG G']:
            raise ValueError('Log(g) requested/received mismatch: {} vs {}'.format(params_requested['SCALE 72/4'], params_received['LOG G']))
        if params_requested['VTURB'] != vturb_received:
            raise ValueError('Vturb requested/received mismatch: {} vs {}'.format(params_requested['VTURB'], vturb_received))
        if not return_received_synthe:
            notify('ATLAS requested/received validation for {} successful'.format(run_dir), silent)

    # SYNTHE run
    if os.path.isfile(run_dir + '/synthe_launch.com'):
        # Read the requested values
        f = open(run_dir + '/synthe_launch.com', 'r')
        content = f.read()
        f.close()
        start = content.find('AIRorVAC  WLBEG     WLEND     RESOLU    TURBV  IFNLTE')
        for i in range(2):
            start = content[:start].rfind('\n')
        end = start + content[start + 1:].find('\n') + 1
        content = content[start:end].strip()
        params_requested = {
            'wlbeg': float(content[10:20].strip()),
            'wlend': float(content[20:30].strip()),
            'resolu': float(content[30:40].strip()),
            'turbv': float(content[40:50].strip()),
            'ifnlte': float(content[50:53].strip()),
            'linout': float(content[53:60].strip()),
            'cutoff': float(content[60:70].strip()),
            'ifpred': float(content[70:75].strip()),
            'nread': float(content[75:80].strip()),
        }

        # Determine the index of the most recent SYNTHE run
        synthe_index = 1
        while os.path.isdir(run_dir + '/synthe_{}'.format(synthe_index + 1)):
            synthe_index += 1

        # Get received values from the most recent SYNTHE run
        f = open(run_dir + '/synthe_{}/synbeg.out'.format(synthe_index), 'r')
        content = f.read()
        f.close()
        params_received = {}
        for param in params_requested:
            params_received[param] = float(re.findall('{}={{0,1}} *([^ \\n]+)'.format(param.upper()), content)[0])
            if params_requested[param] != params_received[param]:
                raise ValueError('{} requested/received mismatch: {} vs {}'.format(param, params_requested[param], params_received[param]))
        if return_received_synthe:
            return params_received
        notify('SYNTHE requested/received validation for {} successful'.format(run_dir), silent)

    # DFSYNTHE run
    if os.path.isfile(run_dir + '/xnfdf.com'):
        for requested_file, received_file in zip(['xnfdf.com', 'kappa9v0.com'], ['xnfdf.out', 'kapm40k2.out']):
            elements_requested, params_requested = parse_atlas_abundances(run_dir + '/{}'.format(requested_file), lookbehind = 1, params = ['ABUNDANCE SCALE'])
            elements_received, params_received = parse_atlas_abundances(run_dir + '/{}'.format(received_file), classic_style = False, lookbehind = 1, params = ['0XSCALE'])
            for i in range(len(elements_requested)):
                if elements_requested[i] != elements_received[i]:
                    raise ValueError('Element {} requested/received mismatch: {} vs {}'.format(i, elements_requested[i], elements_received[i]))
            if params_requested['ABUNDANCE SCALE'] != params_received['0XSCALE']:
                raise ValueError('Metallicity requested/received mismatch: {} vs {}'.format(params_requested['ABUNDANCE SCALE'], params_received['0XSCALE']))
        notify('DFSYNTHE requested/received validation for {} successful'.format(run_dir), silent)

    return True

def read_structure(run_dir):
    """
    Parse the output of ATLAS-9 for profiles of physical properties such as temperature and pressure

    arguments:
        run_dir        :     Output directory of the ATLAS-9 run of interest

    returns:
        structure      :     Profiles of physical properties, keyed by a short description of the property,
                             in each layer starting with the outermost layer
        units          :     Dictionary with the same keys as "structure" specifying the units of each
                             profile
    """
    if not os.path.isdir(run_dir):
        raise ValueError('Run directory {} not found!'.format(run_dir))
    if (not os.path.isfile(run_dir + '/output_last_iteration.out')) or (not os.path.isfile(run_dir + '/output_summary.out')):
        raise ValueError('Run directory {} does not contain ATLAS-9 output!'.format(run_dir))

    structure = {}
    units = {}

    file = open(run_dir + '/output_summary.out', 'r')
    data = file.read()
    file.close()
    data = np.loadtxt(data[data.rfind('RHOX'):data.rfind('PRADK')].split('\n'), unpack = True, skiprows = 1)
    structure['layer'] = np.arange(1, np.shape(data)[1] + 1)
    units['layer'] = ''
    structure['temperature'] = data[1]
    units['temperature'] = 'K'
    structure['gas_pressure'] = data[2]
    units['gas_pressure'] = 'Ba'
    structure['electron_number_density'] = data[3]
    units['electron_number_density'] = 'cm^-3'
    structure['rosseland_opacity'] = data[4]
    units['rosseland_opacity'] = 'cm^2 g^-1'
    structure['radiative_acceleration'] = data[5]
    units['radiative_acceleration'] = 'cm s^-2'
    structure['turbulent_velocity'] = data[6]
    units['turbulent_velocity'] = 'cm s^-1'
    structure['radiative_flux'] = data[7]
    units['radiative_flux'] = 'erg cm^-2 s^-1'
    structure['convective_speed'] = data[8]
    units['convective_speed'] = 'cm s^-1'
    structure['speed_of_sound'] = data[9]
    units['speed_of_sound'] = 'cm s^-1'

    data = np.loadtxt(run_dir + '/output_last_iteration.out', skiprows = 3, unpack = True)
    structure['mass_column_density'] = data[1]
    units['mass_column_density'] = 'g cm^-2'
    structure['density'] = data[5]
    units['density'] = 'g cm^-3'
    structure['physical_depth'] = data[7]
    units['physical_depth'] = 'km'
    structure['rosseland_optical_depth'] = data[8]
    units['rosseland_optical_depth'] = ''
    structure['convective_flux'] = data[9]
    units['convective_flux'] = 'erg cm^-2 s^-1'
    structure['radiation_pressure'] = data[10]
    units['radiation_pressure'] = 'Ba'
    structure['flux_error'] = data[11]
    units['flux_error'] = 'percent'
    structure['flux_error_derivative'] = data[12]
    units['flux_error_derivative'] = 'percent'

    return structure, units

def read_spectrum(run_dir, num_bins = -1):
    """
    Parse the output of SYNTHE for synthetic spectrum

    arguments:
        run_dir        :     Output directory of the SYNTHE run of interest
        num_bins       :     If positive, bin the data into this number of wavelength bins

    returns:
        Dictionary of four keys. "wl" is the wavelength in A, "flux" is the synthetic flux in
        erg s^-1 cm^-2 A^-1 strad^-1, "cont" is the continuum of the spectrum in the same units
        as "flux" and "line" is the ratio between the two
    """
    if not os.path.isdir(run_dir):
        raise ValueError('Run directory {} not found!'.format(run_dir))
    if not os.path.isfile(run_dir + '/spectrum.dat'):
        raise ValueError('Run directory {} does not contain SYNTHE output!'.format(run_dir))

    structure = {}
    units = {}

    wl, flux, cont, line = np.loadtxt(run_dir + '/spectrum.dat', delimiter = ',', unpack = True)
    if num_bins > 0:
        wl_binned, flux = bin_spec(wl, flux, num_bins = num_bins)
        wl_binned, cont = bin_spec(wl, cont, num_bins = num_bins)
        wl, line = bin_spec(wl, line, num_bins = num_bins)

    return {'wl': wl, 'flux': flux, 'cont': cont, 'line': line}

def load_restarts():
    """
    Collect effective temperatures, gravities and metallicities of all restart models available to
    the autoselection routine. The paths where such models are stored are listed in restart_paths
    which by default only includes restarts/, i.e. the restart files that come with BasicATLAS.

    The function recognizes both individual model files (of output_summary.out style) and ATLAS
    run directories. All files/directories that do not comply with either of the two formats are
    disregarded
    
    returns:
        Dictionary with the following keys:
            restarts          :           List of all found restarts (files or directories)
            teff              :           Corresponding effective temperatures [K]
            logg              :           Corresponding surface gravities [log10(CGS)]
            zscale            :           Corresponding metallicities [M/H] in dex
    """
    # First collect paths to all files in the listed restart directories
    files = []
    for restart_path in set(restart_paths):
        files += list(np.char.add(restart_path + '/', os.listdir(restart_path)))
    teff = []; logg = []; zscale = []; restarts = []

    for file in files:
        restarts += [file]
        # If the restart is a run directory...
        if os.path.isdir(file) and os.path.isfile(file + '/output_summary.out'):
            model_meta = meta(file)
            teff += [model_meta['teff']]
            logg += [model_meta['logg']]
            zscale += [model_meta['zscale']]
        # If the restart is an output_summary.out style model file
        elif os.path.isfile(file):
            try:
                f = open(file, 'r')
                content = f.read()
                f.close()
            except:
                restarts = restarts[:-1]
                continue
            model_meta = [re.findall('TEFF *([0-9.eE-]+)', content), re.findall('ABUNDANCE SCALE *([0-9.eE-]+)', content), re.findall('GRAVITY *([0-9.eE-]+)', content)]
            if len(model_meta[0]) == 1 and len(model_meta[1]) == 1 and len(model_meta[2]) == 1:
                teff += [float(model_meta[0][0])]
                logg += [float(model_meta[2][0])]
                zscale += [np.log10(float(model_meta[1][0]))]
            else:
                restarts = restarts[:-1]
        else:
            restarts = restarts[:-1]

    return {'restarts': np.array(restarts), 'teff': np.array(teff), 'logg': np.array(logg), 'zscale': np.array(zscale)}

def prepare_restart(restart, save_to, teff, logg = 0.0, zscale = 0.0, silent = False):
    """
    Prepare a restart model for an ATLAS run. The function can take a calculated model as input,
    autoselect a model from the available library of restarts or compile a grey atmosphere restart

    arguments:
        restart        :         To choose a specific restart model, insert the path to the model here.
                                 The model may be a single model file in output_summary.out style or an
                                 entire run directory of a previous ATLAS run. To autoselect a model from
                                 the available library set to "auto". To initialize a grey atmosphere,
                                 set to "grey"
        save_to        :         Path to save the restart file
        teff           :         Target effective temperature. In case of grey atmosphere, the parameter
                                 is necessary to calculate the temperature profile. Otherwise, ATLAS needs
                                 to know this parameter to properly scale the trial temperature profile
        logg           :         Only necessary if restart=="auto" to choose an appropriate restart model
                                 from the library
        zscale         :         Likewise, needed to choose the most appropriate restart from library
        silent         :         Do not print status messages
    """
    # The "standard" grid of optical depth points (Rosseland) spanning accross 72 layers between 1e-6.875 and
    # 1e2. Note that the number of layers and the outer bound can in principle be changed in ATLAS configuration;
    # however the values are hard-coded in the BasicATLAS dispatcher template and hard-coded here as well
    tau_std = np.logspace(-6.875, 2.0, 72)

    if restart == 'grey' or restart == 'gray':                  # Allow both spellings
        temp = teff * ((3/4) * (tau_std + (2/3))) ** (1/4)      # Two-stream approximation grey atmosphere
        tau = tau_std

    elif restart == 'auto':
        restarts = load_restarts()
        # Distance formula to be minimized for the best choice of model
        distance = ((teff - restarts['teff']) / (10000 - 3000)) ** 2.0 + ((logg - restarts['logg']) / (6.0 - 0.0)) ** 2.0 + ((zscale - restarts['zscale']) / (4.0 - (-4.0))) ** 2.0
        best_restart = restarts['restarts'][distance == np.min(distance)][0]
        notify('Automatically chosen restart: {}'.format(best_restart), False)
        # Call ourselves recursively but with "auto" replaced with the chosen model
        return prepare_restart(restart = best_restart, save_to = save_to, teff = teff, logg = logg, zscale = zscale, silent = silent)

    elif os.path.isdir(restart):
        structure, units = read_structure(restart)
        teff = meta(restart)['teff']
        tau = structure['rosseland_optical_depth']
        temp = structure['temperature']

    elif os.path.isfile(restart):
        f = open(restart, 'r')
        content = f.read()
        f.close()
        teff = re.findall('TEFF *([0-9.eE-]+)', content)
        content = re.findall('FLX...,VCONV,VELSND(.+)PRADK', content, re.DOTALL)
        if len(content) != 1 or len(teff) != 1:
            raise ValueError('{} is not a valid restart file'.format(restart))
        teff = float(teff[0])
        # output_summary.out style model files do not provide optical depth. Instead it must be
        # calculated from mass column density and Rosseland opacity which are provided
        rhox, temp, kappa = np.loadtxt(content[0].split('\n'), unpack = True, usecols = [0, 1, 4])
        dtau = (kappa[1:] + kappa[:-1]) / 2.0 * np.diff(rhox)
        tau = np.cumsum(np.r_[rhox[0] * kappa[0], dtau])
    else:
        raise ValueError('{} is an invalid choice of restart'.format(restart))

    # Interpolate the temperature profile to the standard grid
    temp = np.interp(tau_std, tau, temp)
    tau = tau_std
    # ATLAS requires mass column density and Rosseland opacity in every layer instead of optical depth
    # as the independent variable in the trial temperature profile. What it will be ultimately using is
    # however the optical depth, so we can give ATLAS any values for both variables as long as together
    # they are consistent with the right grid of optical depths. Below we just set all opacities to unity
    # and then calculate the right mass column density
    kappa = np.ones(np.shape(tau))
    drhox = np.diff(tau) / (kappa[1:] + kappa[:-1]) * 2.0
    rhox = np.cumsum(np.r_[tau[0] / kappa[0], drhox])

    # Generate the restart file in the appropriate format and save it
    structure = ''
    for i in range(len(tau)):
        structure += ('{:>15.8E}{:>9.1f}' + '{:>10.3E}' * 8).format(rhox[i], temp[i], 0.0, 0.0, kappa[i], 0.0, 0.0, 0.0, 0.0, 0.0) + '\n'
    f = open(save_to, 'w')
    f.write(templates.atlas_restart.format(structure = ' ' + structure.strip(), teff = teff))
    f.close()
