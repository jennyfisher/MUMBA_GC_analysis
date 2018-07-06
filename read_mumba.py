# -*- coding: utf-8 -*-
"""
Created on Tue May 16 2018

@author: jennyf
"""

import pandas as pd
import numpy  as np
import datetime

def read_mumba(varname):

    # MUMBA directory
    mumba_dir = '/short/m19/jaf574/data/MUMBA/'

    # Get filename
    fname = get_mumba_fname(varname)

    # Error if this is not a MUMBA species
    if fname == "error":
       raise KeyError()

    # Use filename to get header info
    n_hdr = mumba_hdr(fname)

    # Read using pandas
    df = pd.read_csv(mumba_dir+fname,sep='\t',header=n_hdr,
                     index_col=[0],parse_dates=True)

    # Fix date/time column
    #df['Date/Time'] = pd.to_datetime(df['Date/Time'])

    # Replace missing value with NaN
    df = df.resample('60min').mean()

    return df

def gcname_to_mumbaname(argument):

    """Converts from GEOS-Chem species name to MUMBA data field name"""

    # Default return original name if not found (may be special case)
    origname=argument
    switcher = {
        "CH2O"    : "HCHO [ppbv]",
        "MOH"     : "CH4O [ppbv]",
        "ALD2"    : "Acetaldehyde [ppbv]",
        "ACET"    : "Acetone [ppbv]",
        "ISOP"    : "C5H8 [ppbv]",
        "MVK_MACR": "Methacrolein + methyl vinyl ketone [ppbv]",
        "BENZ"    : "C6H6 [ppbv]",
        "TOLU"    : "C6H5CH3 [ppbv]",
        "MONOT"   : "Monoterpenes [ppbv]",
        "NO"      : "NO [ppbv]",
        "NO2"     : "NO2 [ppbv]",
        "O3"      : "O3 [ppbv] (mean of hourly O3 concentration)",
        "TMPU"    : "TTT [C]",
    }
    return switcher.get(argument.upper(), origname)

def get_mumba_fname(varname):

    """Uses a GEOS-Chem species name to pick MUMBA filename"""

    # Default return original name if not found (may be special case)
    switcher = {
        "CH2O"    : "MUMBA_PTRMS_2012-12-21_2013-02-15.tab",
        "MOH"     : "MUMBA_PTRMS_2012-12-21_2013-02-15.tab",
        "ALD2"    : "MUMBA_PTRMS_2012-12-21_2013-02-15.tab",
        "ACET"    : "MUMBA_PTRMS_2012-12-21_2013-02-15.tab",
        "ISOP"    : "MUMBA_PTRMS_2012-12-21_2013-02-15.tab",
        "MVK_MACR": "MUMBA_PTRMS_2012-12-21_2013-02-15.tab",
        "BENZ"    : "MUMBA_PTRMS_2012-12-21_2013-02-15.tab",
        "TOLU"    : "MUMBA_PTRMS_2012-12-21_2013-02-15.tab",
        "MONOT"   : "MUMBA_PTRMS_2012-12-21_2013-02-15.tab",
        "NO"      : "MUMBA_NOx_UOW_2012-11-21_2013-02-15.tab",
        "NO2"     : "MUMBA_NOx_UOW_2012-11-21_2013-02-15.tab",
        "NOX"     : "MUMBA_NOx_UOW_2012-11-21_2013-02-15.tab",
        "O3"      : "MUMBA_O3_2012-12-21_2013-02-15.tab",
        "TMPU"    : "MUMBA_MET_2012-12-21_2013-01-25.tab",
    }
    return switcher.get(varname.upper(), "error")

def mumba_hdr(fname):

    switcher = {
        "MUMBA_PTRMS_2012-12-21_2013-02-15.tab"   : 25,
        "MUMBA_NOx_UOW_2012-11-21_2013-02-15.tab" : 18,
        "MUMBA_O3_2012-12-21_2013-02-15.tab"      : 20,
        "MUMBA_MET_2012-12-21_2013-01-25.tab"     : 18,
    }
    return switcher.get(fname,"error")
