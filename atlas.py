from datetime import datetime
import os
import re
import numpy as np
from shutil import copyfile
import subprocess
import time
from scipy.optimize import brentq
import scipy.constants as spc
import warnings
import copy

from settings import Settings
import templates

from threading import Thread

# Custom Thread() class that returns information on exceptions raised by the thread to the main program
class ExceptionHandlingThread(Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._exception = None

    def run(self):
        try:
            super().run()
        except Exception as e:
            self._exception = e

    @property
    def exception(self):
        return self._exception

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
        raise ValueError('Command {} returned an error: {}'.format(command, stderr))

def bin_spec(wl, flux, num_bins = 1000):
    """
    Bin a given spectrum ("wl" and "flux") into a given number of bins
    """
    hist_sum = np.histogram(wl, bins = num_bins, weights = flux)
    hist_count = np.histogram(wl, bins = num_bins)
    return np.array(hist_sum[1][1:] + hist_sum[1][:-1])[hist_count[0] > 0] / 2.0, hist_sum[0][hist_count[0] > 0] / hist_count[0][hist_count[0] > 0]

def blackbody(nu, T):
    """
    Implementation of Planck's law in SI for frequency "nu" (in Hz) and temperature "T" (in K)
    """
    if spc.h * nu / spc.k / T < 675 and np.e ** (spc.h * nu / spc.k / T) - 1 > 0.0:
        return 2 * spc.h * nu ** 3.0 / spc.c ** 2.0 / (np.e ** (spc.h * nu / spc.k / T) - 1)
    else:
        return 0.0

def blackbody_peak(T):
    """
    Find the peak frequency and value of blackbody() using Wien's displacement law for a given temperature "T" (in K)
    """
    max_nu = 5.8789232e10 * T
    max_fun = blackbody(max_nu, T)
    return max_nu, max_fun

def blackbody_dBdT(nu, T):
    """
    Implementation of the derivative of Planck's law with respect to temperature in SI for a grid of frequencies "nu"
    (in Hz) and temperature "T" (in K)
    """
    if spc.h * nu / spc.k / T < 350 and np.e ** (spc.h * nu / spc.k / T) - 1 > 0:
        return 2 * spc.h ** 2.0 * nu ** 4.0 / (spc.c ** 2.0 * spc.k * T ** 2.0) * np.e ** (spc.h * nu / spc.k / T) / (np.e ** (spc.h * nu / spc.k / T) - 1) ** 2.0
    else:
        return 0.0

def blackbody_dBdT_peak(T):
    """
    Find the peak frequency and value of blackbody() using Wien's displacement law equivalent
    for dB/dT for a given temperature "T"

    The constant used here (3.8300160963) is a numerical solution to:
        x^2 * coth(x / 2) == 4x
    """
    max_nu = 3.8300160963 / spc.h * spc.k * T
    max_fun = blackbody_dBdT(max_nu, T)
    return max_nu, max_fun

def atlas_converged(run_dir, print_result = False, silent = False, niter = 0):
    """
    Evaluate the convergence parameters and extract the best iteration for a completed or ongoing ATLAS run

    The function evaluates all available iterations and determines the maximum flux error and maximum flux
    derivative error for each. It then determines what the best iteration is, and extracts it into the file
    output_last_iteration.out, which is subsequently used by other functions

    For all iterations where the chemical equilibrium could not be found, the maximum errors are set to 88888.888,
    so they are not considered in selecting the best iteration (unless all other iterations are extremely bad)

    If the ATLAS run is ongoing (i.e. fort.7 is present in the run directory), the function will place the atmospheric
    structure of the best iteration into it

    The expected maximum number of iterations in the run can be provided in "niter". Then, if the run has fewer iterations,
    the function will attempt to determine the reason why it stopped prematurely, and raise an exception if the reason is
    unknown

    arguments:
        run_dir      :         Output directory of the ATLAS run
        print_result :         If True, will display the number of the best iteration, the total number of iterations,
                               the convergence parameters of the best iteration, and potentially warn the user if the
                               run terminated prematurely due to an issue with the model (the latter would only work
                               if "niter" is specified)
        silent       :         Do not print status messages. Must be set to False for "print_result" to display
                               notifications
        niter        :         Maximum number of iterations in the run. Required to determine if the run terminated
                               prematurely

    returns:
        err          :         Array of flux errors in the best iteration
        de           :         Array of flux derivative errors in the best iteration
    """
    # Read the main output file
    file = open(run_dir + '/output_main.out', 'r')
    convergence = file.read()
    file.close()

    # Break the output into iterations and get the maximum flux error and maximum flux error derivative in each
    iterations = re.findall('START TABLE.+?END TABLE', convergence, re.DOTALL)
    cursor = 0
    max_err = []; max_de = []
    for i, iteration in enumerate(iterations):

        # Determine where this iteration starts and ends
        end = convergence.find('END TABLE', cursor)
        cursor = end + 1
        start = convergence.rfind('END TABLE', 0, cursor)
        if start == -1:
            start = 0

        # Check that the chemical equilibrium calculation finished successfully
        if convergence[start:end].find('CHEMFAIL') != -1:
            max_err += [88888.888]
            max_de += [88888.888]
            continue

        # Remove header and footer
        s = iteration.split('\n')[4:-1]
        assert(len(s) == 72)
        s = '\n'.join(s)

        err, de = np.loadtxt(s.split('\n'), unpack = True, usecols = [11, 12])
        max_err += [np.max(np.abs(err))]
        max_de += [np.max(np.abs(de))]

    if len(max_err) == 0:
        raise ValueError('The model diverged immediately: no iterations could be completed')

    # Decide on the best iteration
    max_err = np.array(max_err); max_de = np.array(max_de)
    gold = (max_err < 1.0) & (max_de < 10.0)
    silver = (max_err < 10.0) & (max_de < 100.0)
    bronze = (max_err < 1000.0)
    unconv = (~gold) & (~silver) & (~bronze)
    if np.count_nonzero(gold) > 0:
        best = np.arange(len(max_err))[gold][np.argmin(max_err[gold])]; conv = 'GOLD'
    elif np.count_nonzero(silver) > 0:
        best = np.arange(len(max_err))[silver][np.argmin(max_err[silver])]; conv = 'SILVER'
    elif np.count_nonzero(bronze) > 0:
        best = np.arange(len(max_err))[bronze][np.argmin(max_err[bronze])]; conv = 'BRONZE'
    else:
        best = np.arange(len(max_err))[unconv][np.argmin(max_err[unconv])]; conv = 'UNCONVERGED'
    if print_result:
        notify('Total iterations: {} | Best iteration: {}'.format(len(max_de), best + 1), silent)
        notify('For the best iteration: max[|err|] = {} | max[|de|] = {} | convergence class: {}'.format(max_err[best], max_de[best], conv), silent)

    # Save the best iteration in a separate file and get its errors
    file = open(run_dir + '/output_last_iteration.out', 'w')
    file.write('\n'.join(iterations[best].split('\n')[4:-1]))
    file.close()
    err, de = np.loadtxt(run_dir + '/output_last_iteration.out', unpack = True, usecols = [11, 12])


    # If fort.7 exists, remove all iterations from it except for the best one
    if os.path.isfile(run_dir + '/fort.7'):
        file = open(run_dir + '/fort.7', 'r')
        content = file.read()
        file.close()
        content = content.split('\n==========\n')[:-1]
        assert len(content) == len(max_err)
        file = open(run_dir + '/fort.7', 'w')
        file.write(content[best])
        file.close()

    # Determine if this run was successful (we also consider failed models that terminated with definitive error codes successful)
    success = False
    if (niter == 0) or (niter == len(max_err)):
        success = True
    if convergence.find('REACHED GOLD TOLERANCES') != -1:
        success = True
    if convergence.find('MODEL DIVERGED') != -1 or convergence.find('INVALID STRUCTURE') != -1:
        success = True
        if print_result: notify('**WARNING:** Model terminated due to divergence', silent)
    if convergence.find('HYDROFAIL') != -1:
        success = True
        if print_result: notify('**WARNING:** Model terminated due to hydrostatic failure', silent)
    if not success:
        raise ValueError('Model terminated due to unknown reason')

    return err, de

def atlas(output_dir, settings = Settings(), restart = 'auto', niter = 450, ODF = python_path + '/data/solar_ODF', molecules = True, silent = False, tio = 6.87):
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
        niter          :     Maximum number of iterations. Iterations will be carried out in batches of 15, and may be
                             stopped before reaching this number if the final iteration in a batch meets the gold
                             convergence requirement (max[|err|] < 1 and max[|de|] < 10)
        ODF            :     Output directory of a DFSYNTHE run with required Opacity Distribution Functions and Rosseland
                             mean opacities
        molecules      :     If True (default), model formation of molecules. When set to False, atomic number densities
                             are evaluated by solving the Saha equation exactly and may therefore be more precise
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
    prepare_restart(restart, output_dir + '/restart.dat', teff = settings.teff, logg = settings.logg, zscale = settings.effective_zscale(), silent = silent)
    
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
      'enable_molecules': ['OFF', 'ON'][molecules],
      'tio': tio,
    }
    for z, abundance in enumerate(settings.atlas_abun()):
        cards['element_' + str(z)] = abundance
    cards['element_1'] = settings.atlas_abun()[1]
    cards['element_2'] = settings.atlas_abun()[2]
    cards.update({'iterations': templates.atlas_iterations.format(iterations = '15') * int(np.floor(int(niter) / 15))})
    if int(niter) % 15 != 0:
        cards['iterations'] += templates.atlas_iterations.format(iterations = str(int(niter) % 15))
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
    cmd('bash {}/atlas_control.com'.format(output_dir))
    notify("ATLAS-9 halted", silent)

    # atlas_converged() will extract the best iteration and print its convergence parameters
    atlas_converged(output_dir, True, silent, niter)

    cmd('bash {}/atlas_control_end.com'.format(output_dir))
    if not (os.path.isfile(cards['output_1']) and os.path.isfile(cards['output_2'])):
        raise ValueError("ATLAS-9 did not output expected files")

    validate_run(output_dir, silent = silent)

    # ATLAS carries out all frequency integrations over a fixed range of wavelengths that may not be large enough to accommodate
    # very high temperatures (>200 kK). Here we check if the frequency range is appropriate for the entire temperature run of the model
    # and display an error if it is not
    frequencies = []
    reading = False
    with open(cards['output_1']) as f:
        for line in f:
            if line.find('0FREQID') != -1:
                reading = True
                continue
            if reading and len(line) < 60:
                break
            if reading:
                # Minus signs in integration coefficients break the output format. Under normal circumstances
                # all integration coefficients should be positive, but the first coefficient may be negative if
                # the frequency grid has been artificially extended short of ~8 nm as ATLAS will assume 8 nm
                # to be the shortest wavelength regardless
                line = line.replace('-', ' -')
                frequencies += list(np.loadtxt([line])[1::3])
    frequencies = np.array(sorted(frequencies))
    structure, units = read_structure(output_dir)
    for temperature in [np.min(structure['temperature']), np.max(structure['temperature'])]:
        for nu in [np.min(frequencies), np.max(frequencies)]:
            planck_peak = blackbody_peak(temperature)[1]
            planck_dT_peak = blackbody_dBdT_peak(temperature)[1]
            if blackbody(nu, temperature) > 1e-3 * planck_peak:
                warnings.warn('Planck\'s law in one of the layers at temperature {} K does not vanish at the frequency grid bound {} Hz. The result may be inaccurate!'.format(temperature, nu))
            if blackbody_dBdT(nu, temperature) > 1e-3 * planck_dT_peak:
                warnings.warn('Derivative of Planck\'s law (dB/dT) in one of the layers at temperature {} K does not vanish at the frequency grid bound {} Hz. The result may be inaccurate!'.format(temperature, nu))

    # Also check that the temperatures in all layers are within the ODF range
    ODF_temps = []
    ODF_pres = []
    reading = False
    with open(ODF + '/xnfdf.com') as f:
        for line in f:
            if line.find('RHOX,T,P,XNE,ABROSS,ACCRAD,VTURB,CONVFRAC,VCONV') != -1:
                reading = True
                continue
            if len(line) < 10:
                reading = False
                continue
            if reading:
                line = np.loadtxt([line])
                ODF_temps += [line[1]]
                ODF_pres += [line[2]]
    for temperature in [np.min(structure['temperature']), np.max(structure['temperature'])]:
        if temperature < np.min(ODF_temps) or temperature > np.max(ODF_temps):
            warnings.warn('Gas temperature {} K  in one of the layers falls outside the ODF range [{}, {}]. The result may be inaccurate!'.format(temperature, np.min(ODF_temps), np.max(ODF_temps)))

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

def synthe(output_dir, min_wl, max_wl, res = 600000.0, vturb = 1.5, abun_adjust = {}, C12C13 = False, linelist = 'BasicATLAS', buffsize = 2010001, overwrite_prev = False, air_wl = False, silent = False, progress = True, tio = 6.87):
    """
    Run SYNTHE to calculate the emergent spectrum corresponding to an existing ATLAS model

    arguments:
        output_dir     :     Directory to store the output. Must contain the output of a previously executed ATLAS run
        min_wl         :     Minimum wavelength of the calculation (nm)
        max_wl         :     Maximum wavelength of the calculation (nm)
        res            :     Sampling resolution (lambda / delta_lambda)
        vturb          :     Turbulent velocity [km/s] (defaults to 1.5 km/s as per the average value measured by APOGEE
                             (III/284/allstars)). Note that ATLAS and DFSYNTHE have their own vturb values
        abun_adjust    :     Adjust abundances of specific elements for this spectral synthesis. The argument must be
                             a dictionary, keyed by element names (e.g. 'Fe') with values corresponding to the adjustments
                             in dex, compared to the chemical composition of the model atmosphere. The effect of adjusted
                             abundances on the structure of the atmosphere will not be accounted for; however, said
                             effect can be small in many cases. Maintaining the same structure and changing abundances
                             only in the spectral synthesis is far more efficient than recalculating the entire model
        C12C13         :     Carbon-12 to carbon-13 ratio to be used when evaluating the opacities of molecular species.
                             Defaults to the value hard-coded in rmolecasc.for (10^-0.005 / 10^-1.955 ~ 89 at the time
                             of writing)
        linelist       :     Atomic line list to use in spectral synthesis. See data/linelists/README.txt for a discussion
                             of available options. Defaults to the recommended line list
        buffsize       :     Maximum allowed number of wavelength points per calculation. If the required number of points
                             exceeds this value, the calculation will be split into multiple batches. This argument is
                             introduced as SYNTHE allocates a buffer of finite size and cannot handle more wavelength
                             points than that. The default value, 2010001, corresponds to the default buffer size in
                             synthe.for
        overwrite_prev :     If True, will remove any output of previous SYNTHE runs in the run directory before startup.
                             If False (default), an error is thrown when a previous SYNTHE run is discovered
        air_wl         :     If True, save output in AIR wavelengths. If False (default), use VACUUM wavelengths
        silent         :     Do not print status messages
        progress       :     If True (default), show progress of the run. Progress is inferred from the progress.dat file,
                             created by patched synthe.for at the beginning of processing each atmospheric layer. The feature
                             requires the tqdm module
    """
    startTime = datetime.now()

    # Check that the ATLAS-9 run exists
    output_dir = os.path.realpath(output_dir)
    if not (os.path.isfile(output_dir + '/output_last_iteration.out') and os.path.isfile(output_dir + '/output_summary.out')):
        raise ValueError('ATLAS run output not found in {}'.format(output_dir))

    # Check that SYNTHE has not already ran
    if os.path.isdir(output_dir + '/synthe_1'):
        if not overwrite_prev:
            raise ValueError('Previous SYNTHE run output found in {}. To overwrite, set overwrite_prev=True'.format(output_dir))
        else:
            file = open(output_dir + '/synthe_cleanup.com', 'w')
            file.write(templates.synthe_cleanup.format(output_dir = output_dir))
            file.close()
            cmd('bash {}/synthe_cleanup.com'.format(output_dir))
            notify("Removed the output of a previous SYNTHE run", silent)

    # Prepare a SYNTHE friendly file
    file = open(output_dir + '/output_summary.out', 'r')
    model = file.read()
    file.close()
    # Remove ATLAS turbulent velocity from the output
    model = model.split('\n')
    in_output = False
    for i, line in enumerate(model):
        if line.find('FLXRAD,VCONV,VELSND') != -1:
            in_output = True
            continue
        if line.find('PRADK') != -1:
            in_output = False
            continue
        if in_output:
            model[i] = line[:-40] + ' {:9.3E}'.format(0) + line[-30:]
    model = '\n'.join(model)
    file = open(output_dir + '/output_synthe.out', 'w')
    file.write(templates.synthe_prependix + model)
    file.close()
    notify("Adapted the ATLAS-9 model to SYNTHE in output_synthe.out", silent)

    # Adjust abundances in spectral synthesis
    if len(abun_adjust) != 0:
        elements, params = parse_atlas_abundances(output_dir + '/output_synthe.out', lookbehind = 1, params = ['ABUNDANCE SCALE'])
        settings = Settings().abun_atlas_to_std(elements, np.log10(params['ABUNDANCE SCALE']))
        for element in abun_adjust:
            if element not in settings['abun']:
                settings['abun'][element] = 0
            settings['abun'][element] += abun_adjust[element]
        elements = Settings().abun_std_to_atlas(**settings)
        template = templates.atlas_control
        template = template[template.find('ABUNDANCE SCALE'):template.find('\n', template.find('ABUNDANCE CHANGE 99'))]
        sub = {'element_{}'.format(i): elements[i] for i in range(1, 100)}
        template = template.format(abundance_scale = 10 ** settings['zscale'], **sub)
        f = open(output_dir + '/output_synthe.out', 'r')
        content = f.read()
        f.close()
        start = content.find('ABUNDANCE SCALE')
        end = content.find('\n', content.find('ABUNDANCE CHANGE 99'))
        content = content[:start] + template + content[end:]
        f = open(output_dir + '/output_synthe.out', 'w')
        f.write(content)
        f.close()
        notify("Updated abundances in output_synthe.out for spectral synthesis", silent)

    # Make sure the requested atomic line list exists
    linelist = os.path.realpath(python_path + '/data/synthe_files/{}.dat'.format(linelist))
    if not os.path.isfile(linelist):
        raise ValueError('Linelist {} not found'.format(linelist))

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

        # C12/C13 ratio
        if type(C12C13) is not bool:
            C13 = 1 / (C12C13 + 1)
            C12 = 1 - C13
            C12C13_line = 'echo "{} {}" > c12c13.dat'.format(np.log10(C12), np.log10(C13))
        else:
            C12C13_line = 'rm -f c12c13.dat'

        # Generate a launcher command file
        cards = {
          's_files': python_path + '/data/synthe_files/',
          'd_files': python_path + '/data/dfsynthe_files/',
          'synthe_suite': python_path + '/bin/',
          'airorvac': ['VAC', 'AIR'][air_wl],
          'wlbeg': float(current_min_wl),
          'wlend': float(current_max_wl),
          'resolu': float(res),
          'turbv': float(vturb),
          'ifnlte': 0,
          'linout': -1,
          'cutoff': 0.0001,
          'ifpred': 1,
          'nread': 0,
          'synthe_solar': output_dir + '/output_synthe.out',
          'output_dir': output_dir,
          'synthe_num': synthe_num,
          'C12C13': C12C13_line,
          'linelist': linelist,
          'tio': tio,
        }
        file = open(output_dir + '/synthe_launch.com', 'w')
        file.write(templates.synthe_control.format(**cards))
        file.close()
        notify("Launcher created for wavelength range ({}, {}), batch {}. Expected number of points: {} (buffer {})".format(current_min_wl, current_max_wl, synthe_num, synbeg(current_min_wl, current_max_wl, res), buffsize), silent)

        # Run SYNTHE
        args = ['bash {}/synthe_launch.com'.format(output_dir)]
        if not progress:
            cmd(*args)
        else:
            thread = ExceptionHandlingThread(target = cmd, args = args)
            thread.start()
            import tqdm
            pbar = tqdm.tqdm(total = 100)
            while thread.is_alive():
                time.sleep(2)
                if not os.path.isfile(progress_fn := output_dir + '/synthe_{}/progress.dat'.format(synthe_num)):
                    progress = 0
                else:
                    f = open(progress_fn, 'r')
                    progress = f.read().strip().split('\n')[-1].split('/')
                    progress = (int(progress[0].strip()) - 1) / int(progress[1].strip())
                    f.close()
                pbar.update(np.round(progress * 100) - pbar.n)
            pbar.update(100)
            pbar.close()
            if thread.exception is not None:
                raise thread.exception
        if not (os.path.isfile(output_dir + '/synthe_{}/spectrum.asc'.format(cards['synthe_num']))):
            raise ValueError("SYNTHE did not output expected files")
        notify("SYNTHE halted", silent)
        validate_run(output_dir, silent = silent)

        current_min_wl = current_max_wl

    # Merge all output files and save the data as ASCII file
    data = np.empty([4, 0])
    for i in range(1, synthe_num + 1):
        data = np.append(data, np.loadtxt(output_dir + '/synthe_{}/spectrum.asc'.format(i), unpack = True, skiprows = 2), axis = 1)
    notify("Total data points: " + str(len(data[0])), silent)
    np.savetxt(output_dir + '/spectrum.dat', data.T, delimiter = ',', header = 'Wavelength [A],Line intensity [erg s^-1 cm^-2 A^-1 strad^-1],Continuum intensity [erg s^-1 cm^-2 A^-1 strad^-1],Intensity ratio')
    notify("Saved the spectrum in spectrum.dat", silent)

    notify("Finished running SYNTHE in " + str(datetime.now() - startTime) + " s", silent)


def dfsynthe(output_dir, settings, parallel = False, silent = False, tio = 6.87):
    """
    Run DFSYNTHE and KAPPAROS to calculate Opacity Distribution Functions (ODFs) and Rosseland mean opacities for a given
    set of chemical abundances
    The calculation is carried out for 5 turbulent velocities (0, 1, 2, 4 and 8 km/s)

    arguments:
        output_dir     :     Directory to store the output. Must NOT exist
        settings       :     Object of class Settings() with required chemical abundances
        parallel       :     If True, run DFSYNTHE for all temperatures in parallel using concurrent.futures
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
      's_files': python_path + '/data/synthe_files/',
      'abundance_scale': 10 ** settings.zscale,
      'dfsynthe_suite': python_path + '/bin/',
      'output_dir': output_dir,
      'tio': tio,
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
    notify('Will run DFSYNTHE to tabulate the ODFs (Opacity Distribution Functions)', silent)
    def process_dft(i):
        dft_cards = copy.deepcopy(cards)
        dft_cards['dft'] = str(int(float(dfts[i])))
        dft_cards['dfsynthe_control_cards'] = '0' * i + '1' + '0' * (len(dfts) - 1 - i)
        dft_cards['output_dir'] = '{}/dft_{}/'.format(output_dir, i)
        os.mkdir(dft_cards['output_dir'])
        file = open(filename := (output_dir + '/dft_{}/dfp.com'.format(i)), 'w')
        file.write(templates.dfsynthe_control_start.format(**dft_cards))
        file.write(templates.dfsynthe_control.format(**dft_cards))
        file.write(templates.dfsynthe_control_end.format(**dft_cards))
        file.close()
        cmd('bash {}'.format(filename))
        notify(str(float(dfts[i])) + ' K done! (' + str(i+1) + '/' + str(len(dfts)) + ')', silent)
    if parallel:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(process_dft, range(len(dfts)))
    else:
        for i in range(len(dfts)):
            process_dft(i)

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
    validate_run(output_dir, silent = silent)

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
    elif os.path.isfile(run_dir + '/output_summary.out'):
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
            res          :       Resolution of the spectrum (lambda/delta_lambda)
            synthe_vturb :       Turbulent velocity in SYNTHE [km/s]. Returns False if the velocity varies
                                 across layers
            medium       :       Whether the output wavelengths are quoted in vacuum or air
    """
    elements_received, params_received = parse_atlas_abundances(run_dir + '/output_summary.out', classic_style = True, lookbehind = 4, params = ['ABUNDANCE SCALE', 'TEFF', 'GRAVITY'])
    output = Settings().abun_atlas_to_std(elements_received, np.log10(params_received['ABUNDANCE SCALE']))
    output['teff'] = params_received['TEFF']
    output['logg'] = params_received['GRAVITY']
    vturb = read_structure(run_dir)[0]['turbulent_velocity'][0]
    output['vturb'] = vturb * 1e-5
    output['type'] = 'ATLAS'

    if os.path.isfile(run_dir + '/synthe_launch.com'):
        output['type'] = 'SYNTHE'
        synthe_params = validate_run(run_dir, return_received_synthe = True)
        output['res'] = synthe_params['resolu']
        synthe_vturb = synthe_params['turbv']   # SYNTHE turbulent velocity parameter
        # By default, SYNTHE adds its own VTURB to ATLAS output in quadrature. synthe() should suppress that behavior by resetting the ATLAS
        # turbulent velocities to 0 when adapting the ATLAS model for the SYNTHE run; however, if that does not happen, we must do that
        # quadrature addition here
        f = open(run_dir + '/output_synthe.out', 'r')
        content = f.read()
        content = content[content.find('\n', content.find('FLXRAD,VCONV,VELSND')) + 1 : content.rfind('\n', 0, content.find('PRADK'))].strip()
        atlas_vturb = np.array(list(map(lambda x: float(x[-40:-30].strip()), content.split('\n')))) * 1e-5
        f.close()
        if np.alltrue(atlas_vturb[0] == atlas_vturb):
            output['synthe_vturb'] = np.sqrt(atlas_vturb[0] ** 2.0 + synthe_vturb ** 2.0)
        else:
            output['synthe_vturb'] = False
        # Figure out if the wavelengths are vacuum or air
        f = open(run_dir + '/synthe_launch.com')
        content = f.read()
        f.close()
        if content.find('\nAIR ') != -1:
            output['medium'] = 'air'
        elif content.find('\nVAC ') != -1:
            output['medium'] = 'vacuum'
        else:
            output['medium'] = 'unknown'
        # Determine any abundance adjustments in SYNTHE
        output['abun_adjust'] = {}
        elements, params = parse_atlas_abundances(run_dir + '/output_synthe.out', lookbehind = 1, params = ['ABUNDANCE SCALE'])
        synthe_abun = Settings().abun_atlas_to_std(elements, np.log10(params['ABUNDANCE SCALE']))
        for element in list(synthe_abun['abun'].keys()) + list(output['abun'].keys()):
            if (element in synthe_abun['abun']) and (element not in output['abun']):
                output['abun_adjust'][element] = synthe_abun['abun'][element]
            elif (element not in synthe_abun['abun']) and (element in output['abun']):
                output['abun_adjust'][element] = -output['abun'][element]
            elif (adjustment := np.round(synthe_abun['abun'][element] - output['abun'][element], 2)) != 0:
                output['abun_adjust'][element] = adjustment

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
        # Small correction to make sure a space is present after 0XSCALE and TEFF when the number that follows is too long
        content = content.replace('0XSCALE', '0XSCALE ')
        content = content.replace('TEFF', 'TEFF ')

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
        if start == -1:
            start = 0
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

def validate_run(run_dir, return_received_synthe = False, silent = False):
    """
    Confirm that the input values provided to ATLAS/SYNTHE/DFSYNTHE in a given run match the ATLAS/SYNTHE/DFSYNHTE's
    interpretation of them. Due to the explicit formatting requirements, sometimes this is not the case. The run
    of interest is specified in "run_dir" (type is identified automatically). Returns True when the validation
    passes and raises an exception when it does not

    arguments:
        run_dir                  :           Directory with output of the run requiring validation
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
        vturb_received = read_structure(run_dir)[0]['turbulent_velocity']
        assert np.all(vturb_received[0] == vturb_received)
        vturb_received = vturb_received[0]

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
    data = data[data.rfind('RHOX'):data.rfind('PRADK')]
    data = data.replace('E-', 'E=').replace('-', ' -').replace('E=', 'E-')
    data = np.loadtxt(data.split('\n'), unpack = True, skiprows = 1)
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

    # Replace all "*" with 9s. "*" are returned when the number cannot be represented otherwise
    f = open(run_dir + '/output_last_iteration.out', 'r')
    data = f.read().replace('*', '9')
    f.close()
    # Backwards compatibility with old output_last_iteration.out format
    if data.strip().find('TEFF') == 0:
        data = np.loadtxt(data.split('\n'), skiprows = 3, unpack = True)
    else:
        data = np.loadtxt(data.split('\n'), unpack = True)
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
    if not os.path.isfile(spec_filename := (run_dir + '/spectrum.dat')):
        if not os.path.isfile(spec_filename := (run_dir + '/spectrum.dat.gz')):
            raise ValueError('Run directory {} does not contain SYNTHE output!'.format(run_dir))

    structure = {}
    units = {}

    wl, flux, cont, line = np.loadtxt(spec_filename, delimiter = ',', unpack = True)
    if num_bins > 0:
        wl_binned, flux = bin_spec(wl, flux, num_bins = num_bins)
        wl_binned, cont = bin_spec(wl, cont, num_bins = num_bins)
        wl, line = bin_spec(wl, line, num_bins = num_bins)

    return {'wl': wl, 'flux': flux, 'cont': cont, 'line': line}

__load_restarts_cache = {}
def load_restarts(discard_cache = False):
    """
    Collect effective temperatures, gravities and metallicities of all restart models available to
    the autoselection routine. The paths where such models are stored are listed in restart_paths
    which by default only includes restarts/, i.e. the restart files that come with BasicATLAS.

    The function recognizes both individual model files (of output_summary.out style) and ATLAS
    run directories. All files/directories that do not comply with either of the two formats are
    disregarded

    For efficiency, the function implements static caching

    arguments:
        discard_cache        :     Set to True to disable static caching (defaults to False)

    returns:
        Dictionary with the following keys:
            restarts          :           List of all found restarts (files or directories)
            teff              :           Corresponding effective temperatures [K]
            logg              :           Corresponding surface gravities [log10(CGS)]
            zscale            :           Corresponding metallicities [M/H] in dex
    """
    # Try loading the result from cache
    cache_key = '&'.join(restart_paths)
    if cache_key in __load_restarts_cache and (not discard_cache):
        return __load_restarts_cache[cache_key]

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

    __load_restarts_cache[cache_key] = {'restarts': np.array(restarts), 'teff': np.array(teff), 'logg': np.array(logg), 'zscale': np.array(zscale)}
    return __load_restarts_cache[cache_key]

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
        notify('Automatically chosen restart: {}'.format(best_restart), silent)
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

def synphot(run_dir, mag_system, reddening = 0.0, Rv = 3.1, filters_dir = python_path + '/data/filters/', spectrum = False, max_spill = 1e-5, silent = False):
    """
    Carry out synthetic photometry for a given SYNTHE model and return bolometric corrections in various filters
    
    arguments:
        run_dir        :     Output directory of the SYNTHE run of interest
        mag_system     :     Desired magnitude system ('VEGAMAG' or 'ABMAG')
        reddening      :     Optical reddening to the source (E(B-V)). Defaults to no reddening (0.0). Extinction is calculated
                             using the Gordon et al. (2023) extinction law, implemented in the dust_extinction module.
                             The value may be a single number or a 1D array of reddenings for batch calculations
        Rv             :     Total-to-selective extinction ratio (Rv). Defaults to the standard Milky Way value of 3.1
        filters_dir    :     Directory with filter transmission profiles. Alternatively, list of filenames of individual filters to
                             include in the calculation. Each transmission profile file must be a space-separated two-column text file
                             with wavelengths (in A) in column 1 and transmission fraction (between 0 and 1) in column 2
        spectrum       :     As an alternative to providing the SYNTHE output directory in "run_dir", the spectrum and effective
                             temperature may be provided in this parameter directly. Must be a dictionary with three keys: "teff"
                             [in K], "wl" [in A] and "flux" [in erg s^-1 cm^-2 A^-1 strad^-1]
        max_spill      :     If the band extends beyond the wavelength range of the provided spectrum, this parameter determines the
                             maximum fraction of the band throughput that is allowed to be outside said wavelength range. If the
                             actual spill fraction exceeds this value, the resulting bolometric correction is set to nan. Otherwise,
                             the spilled transmission is ignored
        silent         :     Do not print status messages
        
    returns:
        Dictionary of bolometric corrections keyed by filter filename
    """
    # @TODO
    #
    # 1) Add support for redshift
    # 2) Add direct calculation of apparent and absolute magnitudes given luminosity and distance
    # 3) Add a tutorial notebook for it all

    BC_dict = {}

    # Equation 5 from Gerasimov+2022. Note that 71.197425 is the IAU constant approximately equaling M_bol_Sun + 2.5 * np.log10(Lsun in Watts)
    C = 71.197425 - 2.5 * np.log10(4 * np.pi * spc.sigma * (10 * spc.parsec) ** 2.0 * 1000 ** 4.0)
    c = spc.c * 1e+10

    if type(spectrum) != bool:
        teff = spectrum['teff']
    else:
        teff = meta(run_dir)['teff']
        spectrum = read_spectrum(run_dir)

    if type(filters_dir) is str:
        filters = list(map(lambda fn: os.path.join(filters_dir, fn), os.listdir(filters_dir)))
    else:
        filters = filters_dir

    for filename in filters:
        filter_wl, filter_t = np.loadtxt(filename, unpack = True)

        if type(filters_dir) is str:
            filename = os.path.basename(filename)

        if mag_system == 'VEGAMAG':
            f_ref_wl, f_ref_flux = np.loadtxt(python_path + '/data/vega_bohlin_2004.dat', unpack = True, delimiter = ',')

            if filter_wl.max() > f_ref_wl.max() or filter_wl.min() < f_ref_wl.min():
                notify('Filter {} has exceed the wavelength range of the reference Vega spectrum'.format(filename), silent)
                BC_dict[filename] = np.nan
                continue

            sort = np.argsort(filter_wl)
            filter_t_vega = np.interp(f_ref_wl, filter_wl[sort], filter_t[sort], left = 0, right = 0)

        elif mag_system == 'ABMAG':
            # Equation 7 from Gerasimov+2022
            f_ref_flux = (3631 * 1e-23 * c) / (spectrum['wl'] ** 2)

        else:
            raise ValueError('Unknown magnitude system {}'.format(mag_system))

        if filter_wl.max() > spectrum['wl'].max() or filter_wl.min() < spectrum['wl'].min():
            # Evaluate the fraction of throughput beyond the wavelength range of the model
            inside = (filter_wl >= spectrum['wl'].min()) & (filter_wl <= spectrum['wl'].max())
            norm = np.trapz(filter_t, filter_wl)
            spill = (norm - np.trapz(filter_t[inside], filter_wl[inside])) / norm
            if spill > max_spill:
                notify('Filter {} has exceed the wavelength range of the model spectrum'.format(filename), silent)
                BC_dict[filename] = np.nan
                continue
 
        sort = np.argsort(filter_wl)
        filter_t = np.interp(spectrum['wl'], filter_wl[sort], filter_t[sort], left = 0, right = 0)

        # Vectorization for reddening
        if len(BC_dict) == 0:
            reddening_is_array = True
        try:
            reddening[0]
        except:
            reddening_is_array = False
            reddening = [reddening]
        for E in reddening:

            # Calculate interstellar extinction
            if E != 0.0:
                try:
                    from dust_extinction.parameter_averages import G23
                    from astropy import units as u
                    extmod = G23(Rv = Rv)
                except:
                    raise ValueError('Could not import the dust_extinction module. For extinguished photometry, make sure the module is installed ( https://dust-extinction.readthedocs.io/en/latest/ ).')
                def extinction_law(wl):
                    result = np.zeros(len(wl))
                    wl_min = 912
                    wl_max = 320000
                    mask = (wl > wl_min) & (wl < wl_max)
                    result[mask] = extmod(np.array(wl)[mask]  * u.Angstrom) * E * Rv
                    return result
                A = extinction_law(spectrum['wl'])
            else:
                A = 0.0

            # Equation 6 from Gerasimov+2022
            f1 = spectrum['wl'] * spectrum['flux'] * filter_t * 10 ** (-A / 2.5) * np.pi
            a = np.trapz(f1, spectrum['wl'])
            if mag_system == 'VEGAMAG':
                f2 = f_ref_wl * f_ref_flux * filter_t_vega
                b = np.trapz(f2, f_ref_wl)
            elif mag_system == 'ABMAG':
                f2 = spectrum['wl'] * f_ref_flux * filter_t
                b = np.trapz(f2, spectrum['wl'])
            ratio = a / b

            if filename not in BC_dict:
                BC_dict[filename] = np.array([])

            # Equation 4 from Gerasimov+2022
            BC_dict[filename] = np.append(BC_dict[filename], 2.5 * np.log10(ratio) - 10 * np.log10(teff / 1000) + C)

    # Match the shape of the output to the shape of "reddening"
    for filename in BC_dict:
        if reddening_is_array:
            try:
                BC_dict[filename][0]
            except:
                BC_dict[filename] = np.full([len(reddening)], BC_dict[filename])
        else:
            try:
                BC_dict[filename] = BC_dict[filename][0]
            except:
                pass

    return BC_dict
