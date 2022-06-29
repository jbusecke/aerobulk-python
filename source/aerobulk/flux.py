import aerobulk.aerobulk.mod_aerobulk_wrap_noskin as aeronoskin
import aerobulk.aerobulk.mod_aerobulk_wrap_skin as aeroskin
import numpy as np
import xarray as xr

VALID_ALGOS = ["coare3p0", "coare3p6", "ecmwf", "ncar", "andreas"]
VALID_ALGOS_SKIN = ["coare3p0", "coare3p6", "ecmwf"]


def _check_algo(algo, valids):
    if algo not in valids:
        raise ValueError(f"Algorithm {algo} not valid. Choose from {valids}.")


# Unshrink the data (i.e. put land NaN values back in their correct locations)
def unshrink_arr(shrunk_array, shape, ocean_index):
    unshrunk_array = np.full(shape, np.nan)
    unshrunk_array[ocean_index] = np.squeeze(shrunk_array)
    return unshrunk_array


def noskin_np(
    sst,
    t_zt,
    hum_zt,
    u_zu,
    v_zu,
    slp,
    algo,
    zt,
    zu,
    niter,
):
    """Python wrapper for aerobulk without skin correction.
    !ATTENTION If input not provided in correct units, will crash.
    !ATTENTION Missing values taken from NaN values in sst field. No input variables may have NaN values that are not reflected in the sst.

    Parameters
    ----------
    sst : numpy.array
        Bulk sea surface temperature [K]
    t_zt : numpy.array
        Absolute air temperature at height zt [K]
    hum_zt : numpy.array
        air humidity at zt, can be given as:
            - specific humidity                   [kg/kg]
            - dew-point temperature                   [K]
            - relative humidity                       [%]
            => type should normally be recognized based on value range
    u_zu : numpy.array
        zonal wind speed at zu                    [m/s]
    v_zu : numpy.array
        meridional wind speed at zu               [m/s]
    slp : numpy.array, optional
        mean sea-level pressure                   [Pa] ~101000 Pa,
        by default 101000.0
    algo : str
        Algorithm, can be one of: "coare3p0", "coare3p6", "ecmwf", "ncar", "andreas",
    zt : int
        height for temperature and spec. hum. of air           [m],
    zu : int
        height for wind (10m = traditional anemometric height  [m],
    niter : int
        Number of iteration steps used in the algorithm,

    Returns
    -------
    ql : numpy.array
        Latent heat flux                                     [W/m^2]
    qh : numpy.array
        Sensible heat flux                                   [W/m^2]
    taux : numpy.array
        zonal wind stress                                    [N/m^2]
    tauy : numpy.array
        meridional wind stress                                    [N/m^2]
    evap : numpy.array
        evaporation         [mm/s] aka [kg/m^2/s] (usually <0, as ocean loses water!)
    """

    # Define the land mask from the native SST land mask
    ocean_index = np.where(~np.isnan(sst))

    # Shrink the input data (i.e. remove all land points)
    args_shrunk = tuple(
        np.atleast_3d(a[ocean_index]) for a in (sst, t_zt, hum_zt, u_zu, v_zu, slp)
    )

    out_data = aeronoskin.mod_aerobulk_wrapper_noskin.aerobulk_model_noskin(
        algo, zt, zu, *args_shrunk, niter
    )

    return tuple(unshrink_arr(o, sst.shape, ocean_index) for o in out_data)


def skin_np(
    sst,
    t_zt,
    hum_zt,
    u_zu,
    v_zu,
    rad_sw,
    rad_lw,
    slp,
    algo,
    zt,
    zu,
    niter,
):
    """Python wrapper for aerobulk with skin correction.
    !ATTENTION If input not provided in correct units, will crash.
    !ATTENTION Missing values taken from NaN values in sst field. No input variables may have NaN values that are not reflected in the sst.

    Parameters
    ----------
    sst : numpy.array
        Bulk sea surface temperature [K]
    t_zt : numpy.array
        Absolute air temperature at height zt [K]
    hum_zt : numpy.array
        air humidity at zt, can be given as:
            - specific humidity                   [kg/kg]
            - dew-point temperature                   [K]
            - relative humidity                       [%]
            => type should normally be recognized based on value range
    u_zu : numpy.array
        zonal wind speed at zu                    [m/s]
    v_zu : numpy.array
        meridional wind speed at zu               [m/s]
    rad_sw : numpy.array
        downwelling shortwave radiation at the surface (>0)   [W/m^2]
    rad_lw : numpy.array
        rad_lw : downwelling longwave radiation at the surface  (>0)   [W/m^2]
    slp : numpy.array, optional
        mean sea-level pressure                   [Pa] ~101000 Pa,
        by default 101000.0
    algo : str
        Algorithm, can be one of: "coare3p0", "coare3p6", "ecmwf",
    zt : int
        height for temperature and spec. hum. of air           [m],
    zu : int
        height for wind (10m = traditional anemometric height  [m],
    niter : int
        Number of iteration steps used in the algorithm,

    Returns
    -------
    ql : numpy.array
        Latent heat flux                                     [W/m^2]
    qh : numpy.array
        Sensible heat flux                                   [W/m^2]
    taux : numpy.array
        zonal wind stress                                    [N/m^2]
    tauy : numpy.array
        meridional wind stress                                    [N/m^2]
    t_s : numpy.array
        skin temperature    [K]    (only when l_use_skin_schemes=TRUE)
    evap : numpy.array
        evaporation         [mm/s] aka [kg/m^2/s] (usually <0, as ocean loses water!)
    """
    # Define the land mask from the native SST land mask
    ocean_index = np.where(~np.isnan(sst))

    # Shrink the input data (i.e. remove all land points)
    args_shrunk = tuple(
        np.atleast_3d(a[ocean_index])
        for a in (sst, t_zt, hum_zt, u_zu, v_zu, slp, rad_sw, rad_lw)
    )

    out_data = aeroskin.mod_aerobulk_wrapper_skin.aerobulk_model_skin(
        algo, zt, zu, *args_shrunk, niter
    )

    return tuple(unshrink_arr(o, sst.shape, ocean_index) for o in out_data)


def noskin(
    sst, t_zt, hum_zt, u_zu, v_zu, slp=101000.0, algo="coare3p0", zt=2, zu=10, niter=6
):
    """xarray wrapper for aerobulk without skin correction.

    Warnings
    --------
    !ATTENTION If input not provided in the units shown in [] below the code will crash.
    !ATTENTION Missing values taken from NaN values in sst field. No input variables may have NaN values that are not reflected in the sst.

    Parameters
    ----------
    sst : xarray.DataArray
        Bulk sea surface temperature [K]
    t_zt : xarray.DataArray
        Absolute air temperature at height zt [K]
    hum_zt : xarray.DataArray
        air humidity at zt, can be given as:
            - specific humidity                   [kg/kg]
            - dew-point temperature                   [K]
            - relative humidity                       [%]
            => type should normally be recognized based on value range
    u_zu : xarray.DataArray
        zonal wind speed at zu                    [m/s]
    v_zu : xarray.DataArray
        meridional wind speed at zu               [m/s]
    slp : xarray.DataArray, optional
        mean sea-level pressure                   [Pa] ~101000 Pa,
        by default 101000.0
    algo : str, optional
        Algorithm, can be one of: "coare3p0", "coare3p6", "ecmwf", "ncar", "andreas",
        by default "coare3p0"
    zt : int, optional
        height for temperature and spec. hum. of air           [m],
        by default 2
    zu : int, optional
        height for wind (10m = traditional anemometric height  [m],
        by default 10
    niter : int, optional
        Number of iteration steps used in the algorithm,
        by default 6

    Returns
    -------
    ql : xarray.DataArray
        Latent heat flux                                     [W/m^2]
    qh : xarray.DataArray
        Sensible heat flux                                   [W/m^2]
    taux : xarray.DataArray
        zonal wind stress                                    [N/m^2]
    tauy : xarray.DataArray
        meridional wind stress                                    [N/m^2]
    evap : xarray.DataArray
        evaporation         [mm/s] aka [kg/m^2/s] (usually <0, as ocean loses water!)
    """
    _check_algo(algo, VALID_ALGOS)

    sst, t_zt, hum_zt, u_zu, v_zu, slp = xr.broadcast(
        sst, t_zt, hum_zt, u_zu, v_zu, slp
    )

    out_vars = xr.apply_ufunc(
        noskin_np,
        sst,
        t_zt,
        hum_zt,
        u_zu,
        v_zu,
        slp,
        input_core_dims=[()] * 6,
        output_core_dims=[()] * 5,
        dask="parallelized",
        kwargs=dict(
            algo=algo,
            zt=zt,
            zu=zu,
            niter=niter,
        ),
        output_dtypes=[sst.dtype]
        * 5,  # deactivates the 1 element check which aerobulk does not like
    )

    if not isinstance(out_vars, tuple) or len(out_vars) != 5:
        raise TypeError("F2Py returned unexpected types")

    return out_vars


def skin(
    sst,
    t_zt,
    hum_zt,
    u_zu,
    v_zu,
    rad_sw,
    rad_lw,
    slp=101000.0,
    algo="coare3p0",
    zt=2,
    zu=10,
    niter=6,
):

    """xarray wrapper for aerobulk with skin correction.

    Warnings
    --------
    !ATTENTION If input not provided in the units shown in [] below the code will crash.
    !ATTENTION Missing values taken from NaN values in sst field. No input variables may have NaN values that are not reflected in the sst.

    Parameters
    ----------
    sst : xr.DataArray
        Bulk sea surface temperature [K]
    t_zt : xr.DataArray
        Absolute air temperature at height zt [K]
    hum_zt : xr.DataArray
        air humidity at zt, can be given as:
            - specific humidity                   [kg/kg]
            - dew-point temperature                   [K]
            - relative humidity                       [%]
            => type should normally be recognized based on value range
    u_zu : xr.DataArray
        zonal wind speed at zu                    [m/s]
    v_zu : xr.DataArray
        meridional wind speed at zu               [m/s]
    rad_sw : xr.DataArray
        downwelling shortwave radiation at the surface (>0)   [W/m^2]
    rad_lw : xr.DataArray
        rad_lw : downwelling longwave radiation at the surface  (>0)   [W/m^2]
    slp : xr.DataArray, optional
        mean sea-level pressure                   [Pa] ~101000 Pa,
        by default 101000.0
    algo : str, optional
        Algorithm, can be one of: "coare3p0", "coare3p6", "ecmwf",
        by default "coare3p0"
    zt : int, optional
        height for temperature and spec. hum. of air           [m],
        by default 2
    zu : int, optional
        height for wind (10m = traditional anemometric height  [m],
        by default 10
    niter : int, optional
        Number of iteration steps used in the algorithm,
        by default 6

    Returns
    -------
    ql : xr.DataArray
        Latent heat flux                                     [W/m^2]
    qh : xr.DataArray
        Sensible heat flux                                   [W/m^2]
    taux : xr.DataArray
        zonal wind stress                                    [N/m^2]
    tauy : xr.DataArray
        meridional wind stress                                    [N/m^2]
    t_s : xr.DataArray
        skin temperature    [K]    (only when l_use_skin_schemes=TRUE)
    evap : xr.DataArray
        evaporation         [mm/s] aka [kg/m^2/s] (usually <0, as ocean loses water!)
    """

    _check_algo(algo, VALID_ALGOS_SKIN)

    sst, t_zt, hum_zt, u_zu, v_zu, rad_sw, rad_lw, slp = xr.broadcast(
        sst, t_zt, hum_zt, u_zu, v_zu, rad_sw, rad_lw, slp
    )

    out_vars = xr.apply_ufunc(
        skin_np,
        sst,
        t_zt,
        hum_zt,
        u_zu,
        v_zu,
        rad_sw,
        rad_lw,
        slp,
        input_core_dims=[()] * 8,
        output_core_dims=[()] * 6,
        dask="parallelized",
        kwargs=dict(
            algo=algo,
            zt=zt,
            zu=zu,
            niter=niter,
        ),
        output_dtypes=[sst.dtype]
        * 6,  # deactivates the 1 element check which aerobulk does not like
    )

    if not isinstance(out_vars, tuple) or len(out_vars) != 6:
        raise TypeError("F2Py returned unexpected types")

    return out_vars
