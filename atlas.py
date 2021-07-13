from datetime import datetime
import os
import re
import numpy as np
from shutil import copyfile
import pexpect
import time

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

def atlas_converged(run_dir):
    """
    Calculate convergence parameters for a completed or an ongoing ATLAS run.

    arguments:
        run_dir      :         Output directory of the ATLAS run
    """
    # Wait a little to make sure the file system had enough time to respond (LEGACY: not really sure if this is actually necessary)
    time.sleep(5)

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
    file.write(s)
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
    last_line = '[ ]+72[- ]+[^\n ]+[ ]+[^\n ]+[ ]+[^\n ]+[ ]+[^\n ]+[ ]+[^\n ]+[ ]+[^\n ]+[ ]+[^\n ]+[ ]+[^\n ]+[ ]+[^\n ]+[ ]+[^\n ]+[ ]+([^\n ]+[ ]+.+|[0-9-]+\.[0-9-]+\.[0-9-]+)' # This regex should match the final line in the output of a successful ATLAS-9 run (72nd layer)
    os.system('bash {}/atlas_control_start.com'.format(output_dir))
    
    # We will allow 20 minutes of processing for every 15 iterations before automatic timeout.
    # This should be more than enough.
    if (int(niter) == 0):
        timeout = 1200
    else:
        timeout = int(1200 * int(niter) / 15.0)
    process = pexpect.spawnu(cards['atlas_exe'], timeout = timeout, cwd = output_dir)  # Launch the ATLAS executable
    process.logfile = open(cards['output_1'], "w")                   # Direct the output into a file
    # For a manual number of iterations, atlas_control.com will contain everything we want to feed into ATLAS (except the termination command, "END").
    # For an automatic number of iterations, we still want to run everything that is in this file, but we will have to iterate manually in the end.
    with open('{}/atlas_control.com'.format(output_dir)) as f:
        content = f.readlines()
    # Feed every line from the file into the running instance of ATLAS
    for line in content:
        line = line.rstrip("\n\r")
        if line == '':
            continue
        process.sendline(line)
    if (int(niter) == 0):
        notify("Starting automatic iterations...", silent)
        # Do 15 iterations
        process.send(templates.atlas_iterations.format(iterations = 15))
        # Wait for ATLAS to begin the last of the 15 iterations
        process.expect('ITERATION 15')
        # Wait for ATLAS to end the 15th iteration
        process.expect(last_line)
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
            process.send(templates.atlas_iterations.format(iterations = 15))
            process.expect('ITERATION 15')
            process.expect(last_line)
            err_old = np.max(np.abs(err))
            de_old = np.max(np.abs(de))
            err, de = atlas_converged(output_dir)
            notify(str(i * 15 + 15) + " iterations completed: max[abs(err)] = " + str(np.max(np.abs(err))) + " | max[abs(de)] = " + str(np.max(np.abs(de))), silent)
            if (err_old - np.max(np.abs(err)) + de_old - np.max(np.abs(de))) < 0.1 and (i > 10):
                notify("The model is unlikely to converge any better ;(", silent)
                break
        process.logfile = None   # This is necessary, so that our "END" does not show up in the output.
    # Terminate ATLAS
    process.sendline('END')
    process.expect(pexpect.EOF)
    notify("ATLAS-9 halted", silent)
    
    os.system('bash {}/atlas_control_end.com'.format(output_dir))
    if not (os.path.isfile(cards['output_1']) and os.path.isfile(cards['output_2'])):
        raise ValueError("ATLAS-9 did not output expected files")

    # Check convergence
    err, de = atlas_converged(output_dir)
    notify("\nFinal convergence: max[abs(err)] = " + str(np.max(np.abs(err))) + " | max[abs(de)] = " + str(np.max(np.abs(de))), silent)
    if (np.max(np.abs(err)) > 1) or (np.max(np.abs(de)) > 10):
        notify("Failed to converge", silent)
    
    # Save data in a NumPy friendly format
    file = open(output_dir + '/output_summary.out', 'r')
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



def dfsynthe(output_dir, settings, silent = False):
    """
    Run DFSYNTHE and KAPPAROS to calculate Opacity Distribution Functions (ODFs) and Rosseland mean opacities for a given
    set of chemical abundances
    The calculation is carried out for 5 turbulent velocities (0, 1, 2, 4 and 8 km/s)

    arguments:
        output_dir     :     Directory to store the output. Must NOT exist
        settings       :     Object of class Settings() with required chemical abundances
        restart        :     Initial model to jump start the calculation. This can point either to a file of type
                             "output_summary.out" (e.g. from restarts/) or the output directory of an existing ATLAS run
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
    os.system('bash {}/xnfdf.com'.format(output_dir))
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
    os.system('bash {}/dfp_start.com'.format(output_dir))
    for i, dft in enumerate(dfts):
        cards['dft'] = str(int(float(dft)))
        cards['dfsynthe_control_cards'] = '0' * i + '1' + '0' * (len(dfts) - 1 - i)
        file = open(output_dir + '/dfp.com', 'w')
        file.write(templates.dfsynthe_control.format(**cards))
        file.close()
        os.system('bash {}/dfp.com'.format(output_dir))
        notify(str(float(dft)) + ' K done! (' + str(i+1) + '/' + str(len(dfts)) + ')', silent)
    os.system('bash {}/dfp_end.com'.format(output_dir))
    
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
        os.system('bash {}/separatedf.com'.format(output_dir))
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
            os.system('bash {}/kappa9v'.format(output_dir) + v + '.com')
            notify(v + ' km/s done! (' + str(i+1) + '/' + str(len(vs)) + ')', silent)
    
    # Run KAPREADTS
    file = open(output_dir + '/kapreadts.com', 'w')
    file.write(templates.kapreadts_control.format(**cards))
    file.close()
    os.system('bash {}/kapreadts.com'.format(output_dir))
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
