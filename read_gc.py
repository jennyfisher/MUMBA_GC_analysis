# -*- coding: utf-8 -*-
"""
Created on Tue May 16 2018

@author: jennyf
"""

import xarray as xr
import pandas as pd
from xbpch import open_bpchdataset
from xbpch import open_mfbpchdataset
from glob import glob

def read_gc(fname,varname,cat='IJ-AVG-$',
            gc_dir = '/short/m19/jaf574/GC.v11-01/runs.v11-02e/geosfp_025x03125_tropchem_au.base/',
            **kwargs):

    # Some species involve multiple GEOS-Chem species...
    varname_gc = gcname_to_names(varname)

    # Expand wildcard if necessary and link to directory
    if '*' in fname:
        fname = glob(gc_dir+fname)
    else:
        fname = [gc_dir + f for f in fname]
    # Put files in order!
    fname.sort()

    # Read using xbpch
    # one file
    if isinstance(fname,str):
       ds = open_bpchdataset(fname,categories=[cat,],fields=varname_gc,
                             diaginfo_file=gc_dir+'diaginfo.dat',
                             tracerinfo_file=gc_dir+'tracerinfo.dat',**kwargs)

    # multiple files
    else:
       ds = open_mfbpchdataset(fname,dask=True,categories=[cat,],fields=varname_gc,
                             diaginfo_file=gc_dir+'diaginfo.dat',
                             tracerinfo_file=gc_dir+'tracerinfo.dat',**kwargs)

    # load dataset
    ds.load()

    # extract variables
    cat=cat.replace('$','S').replace('-','_')
    dfg = ds[[cat+'_'+v for v in varname_gc]]

    # If needed, sum GEOS-Chem variables
    if len(varname_gc) > 1:
        dfg = sum_gc_vars(dfg, [cat+'_'+v for v in varname_gc],
                                varname=cat+'_'+varname)

    return dfg

def get_dir_and_file_names(sim, plot_type, daterange=None):

    gc_dir = '/short/m19/jaf574/GC.v11-01/runs.v11-02e/geosfp_025x03125_tropchem_au.'+sim+'/' 

    if plot_type == 'ts':
       prefix = 'ts'
       suffix = '.bpch'
    elif plot_type == 'map':
       prefix = 'trac_avg.geosfp_025x03125_tropchem_au.'
       suffix = '0000'
    else:
       print("Only plot types ts and map implemented!")

    # Limit dates if relevant
    if daterange is not None:
        dates = pd.date_range(start=daterange[0],end=daterange[1]).strftime("%Y%m%d")
        filename=[]
        for d in dates:
            filename.append(prefix+d+suffix)
    else:
        filename = prefix+'*'+suffix

    return gc_dir, filename

def get_unit_conversion(df, varname, cat):

    # Conversion from ppbC to ppbv for some species
    try :
       conv = df[cat.replace('$','S').replace('-','_')+'_'+varname].C
    except AttributeError:
       conv = 1.0 
       print("no C value found")

    if conv != 1.0:
       print("dividing by {} to convert from ppbC to ppbv".format(conv))

    return conv

def sum_gc_vars(ds,varname_gc,varname=None):

    # Make data array that is sum of relevant variables
    nvars = len(varname_gc)

    da = xr.DataArray(ds[varname_gc[0]].values)

    # Loop over remaining variables to add together (must be a smarter way but I don't know it!)
    for v in varname_gc[1:]:
        da = xr.DataArray(ds[v].values+da[0].values,coords=ds[v].coords,dims=ds[v].dims,attrs=ds[v].attrs)

    # Print a warning about using the attributes from the last tracer
    print("Warning! Attributes taken from GEOS-Chem species "+varname_gc[-1]+".")
    print("  Double-check that this is appropriate for your application.")

    # Name for new variable?
    if varname is None:
       varname = 'NewGCData'

    # Convert back to a dataset
    ds2 = xr.Dataset({varname: da})

    # Add attributes
    ds2.attrs = ds.attrs

    return ds2

def gcname_to_names(argument):

    """Converts from grouped species name to list of GEOS-Chem names"""

    # Default return original name if not found (may be special case)
    origname=argument
    switcher = {
        "MONOT"   : ["MTPA","LIMO","MTPO",],
        "MVK_MACR": ["MVK","MACR",],
        "NOX"     : ["NO","NO2",],
        "SOA"     : ["SOAS","SOAIE","SOAME","SOAGX","SOAMG","LVOCOA","ISN1OA","IONITA","MONITA"],
    }
    return switcher.get(argument.upper(), [origname,])

