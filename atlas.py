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

def atlas(output_dir, settings = Settings(), restart = python_path + '/restarts/ap00t5750g45k2.dat', niter = 0, ODF = python_path + '/data/solar_ODF', silent = False):
    """
    Run ATLAS-9 to calculate a model stellar atmosphere

    arguments:
        output_dir     :     Directory to store the output. Must NOT exist
        settings       :     Object of class Settings() with atmosphere parameters
        restart        :     Initial model to jump start the calculation. This can point either to a file of type
                             "output_summary.out" (e.g. from restarts/) or the output directory of an existing ATLAS run
        niter          :     Number of iterations. Use 0 to iterate until convergence
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

    # Check restart file
    if os.path.isfile(restart):
        copyfile(restart, output_dir + '/restart.dat')
    else:
        raise ValueError('Restart file {} not found'.format(restart))
    
    # Generate a launcher command file
    cards = {
      'molecules': python_path + '/data/atlas_files/molecules.dat',
      'initial_model': output_dir + '/restart.dat',
      'output_1': output_dir + '/output_main.out',
      'output_2': output_dir + '/output_summary.out',
      'atlas_exe': python_path + '/bin/atlas9mem.exe',
      'abundance_scale': str(10 ** float(settings.zscale)),
      'teff': str(float(settings.teff)),
      'gravity': str(float(settings.logg)),
      'vturb': str(settings.vturb),
      'output_dir': output_dir,
    }
    for z, abundance in enumerate(settings.atlas_abun()):
        cards['element_' + str(z)] = str(round(float(abundance), 2))
    cards['element_1'] = str(float(settings.atlas_abun()[1]))
    cards['element_2'] = str(float(settings.atlas_abun()[2]))
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
      'abundance_scale': str(float(10 ** settings.zscale)),
      'teff': str(float(settings.teff)),
      'gravity': str(float(settings.logg)),
      'dfsynthe_suite': python_path + '/bin/',
      'output_dir': output_dir,
    }
    for z, abundance in enumerate(settings.atlas_abun()):
        cards['element_' + str(z)] = str(round(float(abundance), 2))
    cards['element_1'] = str(float(settings.atlas_abun()[1]))
    cards['element_2'] = str(float(settings.atlas_abun()[2]))
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

def meta(run_dir):
    """
    Get meta data for an output directory (ATLAS, SYNTHE of DFSYNTHE)

    arguments:
        run_dir        :     Output directory of interest
    """
    if not os.path.isdir(run_dir):
        raise ValueError('Run directory {} not found!'.format(run_dir))
    if os.path.isfile(run_dir + '/xnfdf.com'):
        return meta_dfsynthe(run_dir)
    elif os.path.isfile(run_dir + '/output_summary.out'):
        return meta_atlas(run_dir)
    else:
        raise ValueError('Run {} type unknown!'.format(run_dir))

def meta_dfsynthe(run_dir):
    """
    Get meta data for an output directory of a DFSYNTHE run

    arguments:
        run_dir        :     Output directory of interest
    """
    file = open(run_dir + '/xnfdf.com', 'r')
    content = file.read()
    file.close()
    elements = list(range(100))
    matches = re.findall('ABUNDANCE +?CHANGE((?: +?[0-9]{1,2} +?[0-9.-]+)+)', content)
    for match in matches:
        match = re.findall('[0-9.-]+', match)
        for element, abun in zip(match[::2], match[1::2]):
            elements[int(element.strip())] = float(abun.strip())
    zscale = np.log10(float(re.findall('ABUNDANCE +?SCALE +?([0-9.-eEdD]+)', content)[0]))
    meta = Settings().abun_atlas_to_std(elements, zscale)
    meta['type'] = 'DFSYNTHE'
    return meta

def reg_search(content, regex, fail_if_not_found = False, return_all = False):
    """
    Search for matches to a regular expression in a file

        content             :     File content or filename
        regex               :     Regular expression
        fail_if_not_found   :     Throw an error when no matches are found (defaults to False)
        return_all          :     Return all matches (otherwise, return the first match only) (defaults to False)

    returns:
        result              :     If "return_all", returns a list of all matched substrings. Otherwise, the first substring only
        content             :     Content of the file that was searched
    """
    if os.path.isfile(content):
        f = open(content, 'r')
        content = f.read()
        f.close()
    result = re.findall(regex, content)
    if len(result) == 0:
        if fail_if_not_found:
            raise ValueError('Broken file!')
        else:
            return False, content
    if not return_all:
        result = result[0]
    return result, content

def meta_atlas(run_dir):
    """
    Get meta data for an output directory of an ATLAS/SYNTHE run

    arguments:
        run_dir        :     Output directory of interest
    """
    # Composition
    file = open(run_dir + '/output_summary.out', 'r')
    content = file.read()
    file.close()
    elements = list(range(100))
    matches = re.findall('ABUNDANCE +?CHANGE((?: +?[0-9]{1,2} +?[0-9.-]+)+)', content)
    for match in matches:
        match = re.findall('[0-9.-]+', match)
        for element, abun in zip(match[::2], match[1::2]):
            elements[int(element.strip())] = float(abun.strip())
    zscale = np.log10(float(re.findall('ABUNDANCE +?SCALE +?([0-9.-eEdD]+)', content)[0]))
    meta = Settings().abun_atlas_to_std(elements, zscale)

    # Initial model
    result, content = reg_search(run_dir + '/atlas_control_start.com', 'ln -s (.+) fort.3')
    meta['restart'] = result

    # ATLAS parameters
    result, content = reg_search(run_dir + '/atlas_control.com', 'FREQUENCIES *([0-9]+) *([0-9]+) *([0-9]+) *(.+)', return_all = True)
    meta['ODF_frequency_points'] = int(result[0][0])
    meta['ODF_start'] = int(result[0][1])
    meta['ODF_end'] = int(result[0][2])
    meta['ODF_type'] = result[0][3]
    result, content = reg_search(content, '\nMOLECULES *(.+)')
    if result == 'ON':
        meta['molecules'] = True
    else:
        meta['molecules'] = False
    result, content = reg_search(content, '\nVTURB *(.+)')
    meta['vturb'] = float(result.lower().replace('D', 'E')) / 1e5
    result, content = reg_search(content, '\nCONVECTION *([^ ]+) *([^ ]+) *([^ ]+) *(.+)', return_all = True)
    meta['convection'] = result[0][0]
    if meta['convection'] == 'OVER':
        'MLT with overshoot'
    elif meta['convection'] == 'ON':
        'MLT without overshoot'
    elif meta['convection'] == 'OFF':
        'No convection'
    else:
        raise ValueError('Broken convection mode!')
    meta['mixlen'] = float(result[0][1])
    meta['overshoot'] = float(result[0][2])
    meta['nconv'] = int(result[0][3])
    result, content = reg_search(content, '\nSCALE *([^ ]+) *([^ ]+) *([^ ]+) *([^ ]+) *(.+)', return_all = True)
    meta['nrhox'] = int(result[0][0])
    meta['tau_min'] = float(result[0][1])
    meta['tau_step'] = float(result[0][2])
    meta['teff'] = float(result[0][3])
    meta['logg'] = float(result[0][4])
    meta['type'] = 'ATLAS'

    # SYNTHE parameters
    if not os.path.isfile(run_dir + '/spectrum.dat'):
        return meta
    result, content = reg_search(run_dir + '/synthe_launch.com', '\n(AIR|VAC) +([^ ]{,10}) *([^ ]{,10}) *([^ ]{,10}) *([^ ]{,10}) *([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+) +(.+)', return_all = True)
    if result[0][0] == 'AIR':
        meta['synthe_mode'] = 'Air'
    elif result[0][0] == 'VAC':
        meta['synthe_mode'] = 'Vacuum'
    else:
        raise ValueError('Broken SYNTHE mode!')
    meta['wl_res'] = float(result[0][3])
    meta['synthe_vturb'] = float(result[0][4])
    if int(result[0][5]) == 1:
        meta['synthe_nlte'] = True
    else:
        meta['synthe_nlte'] = False
    meta['synthe_cutoff'] = float(result[0][7])
    result, content = reg_search(run_dir + '/synthe_1/synthe.out', 'NLINES= +([0-9]+)')
    meta['synthe_lines'] = int(result)
    meta['type'] = 'SYNTHE'

    return meta

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
