import numpy as np
import h5py
import pickle
import os
import scipy as scp
import re

# Path to the home directory of the library
python_path = os.path.dirname(os.path.realpath(__file__))


# Template of the ATLAS format
template = ("""
TEFF {teff:6.0f}.  GRAVITY{logg:8.5f}     
TITLE   B a s i c A T L A S                                                     
 OPACITY IFOP 1 1 1 1 1 1 1 1 1 1 1 1 1 0 1 0 0 0 0 0
 CONVECTION ON   1.25 TURBULENCE OFF  0.00  0.00  0.00  0.00
ABUNDANCE SCALE {zscale:9.5f} ABUNDANCE CHANGE 1{e1:8.5f} 2{e2:8.5f}
""" + "\n".join(
    ' ABUNDANCE CHANGE ' + ' '.join('{0:2d}{{e{0}:7.2f}}'.format(i) for i in range(start, min(start + 6, 100)))
    for start in range(3, 100, 6)
) + """
READ DECK6 72 RHOX,T,P,XNE,ABROSS,ACCRAD,VTURB,         FLXRAD,VCONV,VELSND
{structure}
PRADK{pradk:11.4E}
BEGIN                    ITERATION  15 COMPLETED
""").strip()


def generate_model(structure, params, header, helium, pradk):
    """
    Generate a model atmosphere in the ATLAS format from the output of `interpolate_structure()`

    arguments:
        structure      :         Model structure. This is a (72x3) array, where the first dimension
                                 spans the plane-parallel layers of the atmosphere, and the second dimension is
                                 (mass column density, temperature, pressure), all in CGS
        params         :         Stellar parameters of model
        header         :         Restart grid header to be used in this calculation
        helium         :         The helium abundance of the model (absolute [He/H])
        pradk          :         Radiative pressure at the top of the atmosphere (in CGS)

    returns:
        Content of the generated output_summary.out model file
    """
    # Build the abundance vector of the model in the ATLAS format
    abun = np.array(header['solar'])           # Start with solar abundances
    abun[1] = helium                           # Apply the helium abundance from the header
    abun[2:] += params['zscale']               # Apply the metallicity offset
    # Apply the alpha-enhancement offsets
    abun[[7, 9, 11, 13, 15, 17, 19, 21]] += params['alpha']
    # Apply the carbon offset (note that we have to convert to [C/M] first)
    abun[5] += params['carbon'] + header['carbon_map']([params['zscale'], params['logg']])[0]
    abun = 10 ** abun / np.sum(10 ** abun)     # Normalize the abundance vector
    # Re-express metal abundances in dex and remove the metallicity offset
    abun[2:] = np.log10(abun[2:]) - params['zscale']
    # Floor all abundances at -20 dex
    abun[abun < -20] = -20

    # Fill out the template
    cards = {'e{}'.format(i + 1): abun[i] for i in range(len(abun))}
    cards = {**cards, 'teff': params['teff'], 'logg': params['logg'], 'zscale': 10 ** params['zscale'],
             'pradk': pradk}
    structure = [('{:15.8E}{:9.1f}{:10.3E}' + '       NaN' * 8).format(*line) for line in structure]
    cards['structure'] = '\n'.join(structure)
    return template.format(**cards)

def interpolate_structure(params, header = False):
    """
    Interpolate the restarts grid to a set of target stellar parameters. The output of this function
    can be used with `generate_model()` to generate the interpolated model structure in the ATLAS format

    arguments:
        params         :         Target stellar parameters. This is a dictionary that must have the following
                                 keys: teff, logg, zscale, alpha, carbon
        header         :         If the restart grid header has already been loaded, it may be provided here
                                 so it is not loaded again

    returns:
        structure      :         Interpolated model structure. This is a (72x3) array, where the first dimension
                                 spans the plane-parallel layers of the atmosphere, and the second dimension is
                                 (mass column density, temperature, pressure), all in CGS
        params         :         Stellar parameters of the interpolated model. They should match the input
        header         :         Restart grid header used in this calculation. It should also match the input if
                                 provided
        helium         :         The helium abundance of the interpolated model (absolute [He/H])
        pradk          :         Radiative pressure at the top of the atmosphere (in CGS)
    """
    if type(header) is bool:
        header = load_header()

    param_keys = ['teff', 'logg', 'zscale', 'alpha', 'carbon']
    param_values = [params[key] for key in param_keys]

    # Make sure the requested structure is within grid bounds
    for key in param_keys:
        if params[key] > np.max(header[key]) or params[key] < np.min(header[key]):
            raise ValueError('Requested restart parameters exceed grid bounds along axis {}'.format(key))

    # Identify the bounding grid points
    sides = []
    for key, value in zip(param_keys, param_values):
        if value == header[key][-1]:
            sides += [[len(header[key]) - 2, len(header[key]) - 1]]
        else:
            index = np.where(header[key] > value)[0][0]
            sides += [[index - 1, index]]

    # Load the structures at those bounding points
    indices = tuple([slice(side[0], side[1] + 1) for side in sides])
    with h5py.File(header['grid'], 'r') as f:
        rhox = f['rhox'][tuple(indices)]
        structures = f['structure'][tuple(indices)]
    structures = np.concatenate((rhox, structures), axis = -1)

    # Also get the helium abundances and PRADK at those bounding points
    helium = header['helium'][tuple(indices)]
    pradk = header['pradk'][tuple(indices)]

    # Remove all axes that only have one point
    param_keys = np.array(param_keys)[np.array(np.shape(structures))[:-2] != 1]
    param_values = np.array(param_values)[np.array(np.shape(structures))[:-2] != 1]
    structures = np.squeeze(structures)
    helium = np.squeeze(helium)
    pradk = np.squeeze(pradk)

    # Interpolate the structures
    structure = scp.interpolate.RegularGridInterpolator([[header[param_keys[i]][sides[i][0]], header[param_keys[i]][sides[i][1]]] for i in range(len(param_keys))], structures)(param_values)[0]

    # Interpolate helium abundance and PRADK
    helium = scp.interpolate.RegularGridInterpolator([[header[param_keys[i]][sides[i][0]], header[param_keys[i]][sides[i][1]]] for i in range(len(param_keys))], helium)(param_values)[0]
    pradk = scp.interpolate.RegularGridInterpolator([[header[param_keys[i]][sides[i][0]], header[param_keys[i]][sides[i][1]]] for i in range(len(param_keys))], pradk)(param_values)[0]

    return structure, params, header, helium, pradk


def load_header():
    """
    Load the header of the restart library that contains the parameters of available restart models,
    adopted solar abundances and other meta data. The header is stored as a pickled dictionary in
    a separate HDF5 dataset.

    This function will attempt to load the full grid in light.h5 and fall back to the rarefied grid
    in restarts.h5 if the full grid is not found. The filename of the loaded grid will be added
    to the returned header under the `grid` key.

    The function also converts the `carbon_map` header into a SciPy interpolator that can be used
    to evaluate the [C/M] scaling at any metallicity and gravity

    returns:
        header        :         Header of the restart library
    """
    # Find the restarts grid
    if not os.path.isfile(grid := ('{}/restarts/light.h5'.format(python_path))):
        grid = '{}/restarts/restarts.h5'.format(python_path)

    # Load the header
    with h5py.File(grid, 'r') as f:
        header = pickle.loads(bytes(f['header'][()]))

    header['grid'] = os.path.realpath(grid)

    # Convert carbon_map from individual points to regular grid interpolator
    zscale_grid = sorted(set(x for x, y in header['carbon_map']))
    logg_grid = sorted(set(y for x, y in header['carbon_map']))
    carbon_map = np.zeros([len(zscale_grid), len(logg_grid)])
    for i, x in enumerate(zscale_grid):
        for j, y in enumerate(logg_grid):
            carbon_map[i,j] = header['carbon_map'][(x, y)]
    header['carbon_map'] = scp.interpolate.RegularGridInterpolator([zscale_grid, logg_grid], carbon_map)

    return header


def prepare_restart(restart, save_to, settings):
    """
    Prepare a restart model for an ATLAS run. The function can take a calculated model as input,
    autoselect a model from the available library of restarts or compile a gray atmosphere restart

    arguments:
        restart        :         To choose a specific restart model, insert the path to the model here.
                                 The model may be a single model file in output_summary.out style or an
                                 entire run directory of a previous ATLAS run. To autoselect a model from
                                 the available library set to "auto". To initialize a gray atmosphere,
                                 set to "gray"
        save_to        :         Path to save the restart file
        settings       :         Object of class Settings() with atmosphere parameters

    returns:
        message        :         Verbal description of the provided restart model
    """
    # The "standard" grid of optical depth points (Rosseland) spanning accross 72 layers between 1e-6.875 and
    # 1e2. Note that the number of layers and the outer bound can in principle be changed in ATLAS configuration;
    # however the values are hard-coded in the BasicATLAS dispatcher template and hard-coded here as well
    tau_std = np.logspace(-6.875, 2.0, 72)

    if restart == 'grey' or restart == 'gray':                           # Allow both spellings
        temp = settings.teff * ((3/4) * (tau_std + (2/3))) ** (1/4)      # Two-stream approximation grey atmosphere
        tau = tau_std
        teff = settings.teff
        message = 'Using gray model with teff={} as restart'.format(teff)

    elif restart == 'auto':
        header = load_header()
        # Choose closest teff, logg, zscale (going by [Fe/H], not [M/H]), alpha (going by [Mg/Fe]) and the C/O ratio (going by [C/M] - [O/M])
        teff = header['teff'][np.argmin(np.abs(settings.teff - header['teff']))]
        logg = header['logg'][np.argmin(np.abs(settings.logg - header['logg']))]
        model_zscale = settings.zscale
        if 'Fe' in settings.abun:
            model_zscale += settings.abun['Fe']
        zscale = header['zscale'][np.argmin(np.abs(model_zscale - header['zscale']))]
        model_alpha = 0.0
        if 'Mg' in settings.abun:
            model_alpha += settings.abun['Mg']
        if 'Fe' in settings.abun:
            model_alpha -= settings.abun['Fe']
        alpha = header['alpha'][np.argmin(np.abs(model_alpha - header['alpha']))]
        model_CO = 0.0
        if 'C' in settings.abun:
            model_CO += settings.abun['C']
        if 'O' in settings.abun:
            model_CO -= settings.abun['O']
        CO_available = header['carbon'] + header['carbon_map']([zscale, logg])[0] - alpha
        carbon = header['carbon'][np.argmin(np.abs(model_CO - CO_available))]
        structure, params, header, helium, pradk = interpolate_structure({'teff': teff, 'logg': logg, 'zscale': zscale, 'alpha': alpha, 'carbon': carbon}, header = header)
        temp = structure[:,header['columns'].index('Temperature')]
        tau = tau_std
        message = 'Chose closest model from the restart grid with (Teff,log(g),[M/H],[a/M],[C/M])=({},{},{},{},{})'.format(teff, logg, zscale, alpha, carbon + header['carbon_map']([zscale, logg])[0])

    elif os.path.isdir(restart):
        structure, units = read_structure(restart)
        teff = meta(restart)['teff']
        tau = structure['rosseland_optical_depth']
        temp = structure['temperature']
        message = 'Using {} as restart'.format(restart)

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
        message = 'Using {} as restart'.format(restart)

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

    # Generate the restart file in the appropriate format and save it. We fill out the template as little
    # as possible. The majority of values are not used by ATLAS and can be set to NaN. PRADK and ACCRAD
    # are technically required and cannot be set to NaN, but they have very little effect on the final
    # result, so we just set them to 0
    cards = {'e{}'.format(i + 1): np.nan for i in range(99)}
    cards = {**cards, 'teff': teff, 'logg': np.nan, 'zscale': np.nan, 'pradk': 0.0}
    structure = [('{:15.8E}{:9.1f}' + '{:10.3E}' * 8).format(*([rhox[i], temp[i], np.nan, np.nan, kappa[i], 0.0] + [np.nan] * 4)) for i in range(len(tau))]
    cards['structure'] = '\n'.join(structure)
    model = template.format(**cards)
    f = open(save_to, 'w')
    f.write(model)
    f.close()

    return message
