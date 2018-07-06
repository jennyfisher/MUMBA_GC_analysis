# -*- coding: utf-8 -*-
"""
Created on Tue May 16 2018

@author: jennyf
"""

import pandas as pd
import numpy  as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import datetime as dt
import gc

from read_mumba import *
from read_gc import *

def mumba_gc_ts(varname,cat=None,lon=None,lat=None,
                alldates=False,daterange=None,
                mindata=None,maxdata=None,sim=None,shift=None,
                MUMBA=True, diurnal=False):

    # Set up figure
    fig, ax = plt.subplots()

    # Want to skip red in default colour cycling so can use for base
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    del colors[2]
    ax.set_prop_cycle('color',colors)

    # Try to read MUMBA data for this variable; plot if found
    if MUMBA:
        try: 
            dfm = read_mumba(varname)
        except KeyError:
            print("No MUMBA data for species "+varname)
        else:
            # For diurnal cycle, calculate hourly averages
            if diurnal:
               dfm_std = dfm.groupby(dfm.index.hour).std()
               dfm = dfm.groupby(dfm.index.hour).mean()
        
            # Plot MUMBA timeseries
            if varname.upper() == 'NOX':
                ax.plot(dfm.index,dfm[gcname_to_mumbaname('NO')]+dfm[gcname_to_mumbaname('NO2')],
                        color='k',linewidth=2,label='Obs')
            else:
                ax.plot(dfm.index,dfm[gcname_to_mumbaname(varname)],
                        color='k',linewidth=2,label='Obs')
    
    # Pick lat and lon - if not specified use MUMBA values
    if lat == None:
        lat = -34.397200
    if lon == None:
        lon = 150.899600

    # Shift gridbox by one?
    if shift is not None:
        if 'W' in shift.upper():
           lon = lon-.3125
        elif 'E' in shift.upper():
           lon = lon+.3125
        if 'S' in shift.upper():
           lat = lat-.25
        elif 'N' in shift.upper():
           lat = lat+.25

    # Pick GC filename - allow overplotting multiple runs
    sims=[]
    if ( sim == None):
       sim = 'base'
    if type(sim) is str:
       sims.append(sim)
    else:
       for s in sim:
           sims.append(s)

    for s in sims:
        # Read dataframe
        gc_directory, filename = get_dir_and_file_names(s,'ts',daterange=daterange)
        dfg = read_gc(filename,varname,gc_dir=gc_directory,cat=cat)
        dfg1d = dfg.sel(lat=lat,lon=lon,method='nearest')

        # Plot timeseries - MUMBA time = UTC+10
        gctime = pd.to_datetime(dfg1d.time.values) + dt.timedelta(hours=10)
        gcdata = xr.Dataset.to_array(dfg1d).values

        # Convert from ppbC to ppbv for some species and reshape array
        conv = get_unit_conversion(dfg, varname)
        gcdata = np.reshape(gcdata,gcdata.shape[1]) / conv

        # Temperature? Convert units to C
        if varname == 'TMPU':
           gcdata = gcdata - 273.15

        # Convert to pandas dataframe
        gcdata = pd.DataFrame(gcdata,index=gctime)

        # For diurnal cycle, calculate hourly averages
        if diurnal:
            gcdata_std = gcdata.groupby(gcdata.index.hour).std()
            gcdata = gcdata.groupby(gcdata.index.hour).mean()

        # Make sure 'base' is red, otherwise just cycle colours
        if s == 'base':
            ax.plot(gcdata.index,gcdata,label=s,color='r')
        else:
            ax.plot(gcdata.index,gcdata,label=s)

    # Add plot parameters
    ax.legend(loc='best')
    plt.ylabel(varname.upper())

    # Plot all dates or just GC time frame?
    if not diurnal:
        if daterange is not None:
            plt.xlim(pd.Timestamp(daterange[0]),pd.Timestamp(daterange[-1]))
        elif not alldates:
            plt.xlim(gctime.min(),gctime.max())
    
        # Should find a way to show hours instead if <= 24 hours...
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate()

    # Set y-axis range?
    if maxdata is not None:
        if mindata is None:
           mindata=0
        plt.ylim(mindata,maxdata)

    plt.show()

    return

def gc_map(varname,cat=None,lon=None,lat=None,lev=0,
                alldates=False,daterange=None,
                maxdata=None,sim=None):

    # Set up figure & map projection
    fig = plt.figure()
    ax = fig.add_subplot(111, projection=ccrs.PlateCarree())

    # Pick lat and lon bounds - if not specified use SE region
    if lat == None:
        lat = [-40,-30]
    if lon == None:
        lon = [145,155]

    # Pick GC filename - one run for map or two for difference plot
    sims=[]
    if ( sim == None):
       sim = 'base'
    if type(sim) is str:
       sims.append(sim)
    else:
       for s in sim:
           sims.append(s)

    if len(sim) == 1:
       print("Plotting map from run "+sim[0])
    elif len(sim) == 2:
       print("Plotting difference map: "+sim[1]+"-"+sim[0])
    else:
       raise RuntimeError("Only one or two runs allowed for maps")

    for i,s in enumerate(sims):

        # Read dataframe
        gc_directory, filename = get_dir_and_file_names(s,'map',daterange=daterange)
        dfg = read_gc(filename,varname,gc_dir=gc_directory,cat=cat)
    
        # Conversion from ppbC to ppbv for some species
        conv = get_unit_conversion(dfg, varname)
    
        # Average over time
        dfg = dfg.mean('time')
    
        # Cut to requested level(s) and average over levels if needed
        try:
            dfg = dfg.isel(lev=lev).mean('lev')
        except :
            dfg = dfg.isel(lev=lev)
    
        # Extract data
        gclon = dfg.lon.values
        gclat = dfg.lat.values
        gcdata = dfg['IJ_AVG_S_'+varname].values
    
        # Convert units from ppbC to ppbv for some species
        gcdata = gcdata / conv

        # Save into separate array if first run
        if i == 0:
           gcdata_orig = gcdata

    # If there are two sims we need to take the difference
    if len(sims) == 2:
       gcdata = gcdata - gcdata_orig
       cmap = 'coolwarm'
       if maxdata is None:
          maxdata = np.max(abs(gcdata))
       mindata = -1.*maxdata
    else:
       cmap = 'viridis'
       mindata = 0.

    # Temperature? Convert units to C
    if varname == 'TMPU':
       gcdata = gcdata - 273.15

    # Make map here - must transpose data for correct shape
    # Set colorbar range?
    if maxdata is not None:
       im = ax.pcolormesh(gclon, gclat, gcdata.T,
                          vmin = mindata, vmax = maxdata,
                          cmap=plt.get_cmap(cmap))
    else:
       im = ax.pcolormesh(gclon, gclat, gcdata.T,
                          cmap=plt.get_cmap(cmap))
    cb = fig.colorbar(im, ax=ax, orientation='horizontal')

    # Add map features
    ax.coastlines(resolution='50m', color='k',linewidth=1)
    ax.set_extent([lon[0],lon[1],lat[0],lat[1]],ccrs.PlateCarree())
    ocean = cfeature.NaturalEarthFeature('physical','ocean','50m',edgecolor='k',facecolor=cfeature.COLORS['water'])
    ax.add_feature(ocean)

    # Add title
    if daterange is None:
       title=varname
    else:
       title=varname+': '+daterange[0]+' to '+daterange[1]
    plt.title(title)

    plt.show()

    return

