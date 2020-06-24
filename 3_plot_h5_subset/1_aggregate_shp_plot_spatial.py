import os, h5py
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
from shapely.geometry import mapping, Point, Polygon, shape #to create the geomoetries for gpd

import contextily as ctx
import matplotlib.ticker as mtick

#----------------------User Set These---------
cmap_c = 'hot_r'
vmin, vmax = 0, 30
rh_val = 'rh_90'
#--------------------------------------------

#function for plotting google sattelite tiles
def add_basemap(ax, zoom, url = 'http://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}'):#url='http://tile.stamen.com/terrain/{z}/{x}/{y}.png'):#url='http://tile.stamen.com/terrain/tileZ/tileX/tileY.png'):
    xmin, xmax, ymin, ymax = ax.axis()
    basemap, extent = ctx.bounds2img(xmin, ymin, xmax, ymax, zoom=zoom, source=url)
    ax.imshow(basemap, extent=extent, interpolation='bilinear')
    # restore original x/y limits
    ax.axis((xmin, xmax, ymin, ymax))

#aggregate shapefiles
h5fn = [f for f in os.listdir('.') if f.endswith('_subset.h5')]
shpaggl = []

for num, val in enumerate(h5fn):
    shpl = [f for f in os.listdir('.') if f.startswith(val[:-3]+'_map_bmn_') and f.endswith('.shp')]
    if len(shpl) > 0:
        shpaggl.append(shpl)

for num, val in enumerate(shpaggl):
    yy = gpd.GeoDataFrame()
    for num2, val2 in enumerate(val):
        xx = gpd.read_file(val2)
        if num2 == 0:
            tmp = list(xx)
            aa = [f[:-2] for f in tmp[0:16]]
            aa = aa + tmp[16:]
        xx.columns = aa
        yy = yy.append(xx) 
    yy.to_file(val2[:-10]+'.shp')

#cleanup
delfn = [f for f in os.listdir('.') if '_map_bmn' in f]
for num, val in enumerate(delfn):
    if os.path.isfile(val):
        os.remove(val)

#plot shapefiles
#this step needs descartes package to be installed, i.e. conda install descartes
#june - 11: consider making a quick plot of rh_90 for each h5. For this purpose, a quick and easy way is to append all of the dataframes into one and just plot x,y colored by z 

shpmapl = [f for f in os.listdir('.') if f.endswith('subset_map.shp')]

cwd = os.getcwd()
rootdir, subdir = os.path.split(cwd)
shpdir = os.path.join(rootdir, '0_shapefile')
shpfn = [f for f in os.listdir(shpdir) if f.endswith('.shp')][0]
shpfn = os.path.join(shpdir, shpfn)

for num, val in enumerate(shpmapl):
    print('Working on file %s' %(val))

    fig, ax = plt.subplots()
    fig.set_size_inches(6,6)

    xx = gpd.read_file(val) #already is 3857

    myshp = gpd.read_file(shpfn)
    myshp=myshp.to_crs(epsg=3857)

    myshp.geometry.boundary.plot(color = None, edgecolor = 'k', linewidth = 1, ax = ax)
    xx.plot(column = rh_val, marker = 's', markersize = 0.5, ax = ax, cmap = cmap_c, vmin = vmin, vmax = vmax)
    add_basemap(ax, zoom=13)

    #subset programmatically, find first and last point coordinates ... add 10% buffer

    #find min, max values:
    y2 = (max(xx.geometry.y))
    y1 = (min(xx.geometry.y))
    x2 = (max(xx.geometry.x))
    x1 = (min(xx.geometry.x))

    buffy = np.abs(np.int((y2-y1)/10))
    buffx = np.abs(np.int((x2-x1)/10))

    if y2 > y1:
        plt.ylim([y1-buffy, y2+buffy])
    else:
        plt.ylim([y1+buffy, y2-buffy])

    if x2 > x1:
        plt.xlim([x1-buffx, x2+buffx])
    else:
        plt.xlim([x1+buffx, x2-buffx])

    mf = mtick.ScalarFormatter(useOffset=False, useMathText=True)
    mf.set_powerlimits((-2,2))
    ax.xaxis.set_major_formatter(mf)
    ax.tick_params(axis='both', which='major', labelsize=10)
    leg = plt.legend(['roi', rh_val])#, frameon = False)
    leg.get_frame().set_linewidth(0.0)
    sm = plt.cm.ScalarMappable(cmap=cmap_c, norm=plt.Normalize(vmin=vmin, vmax=vmax))
    cb = fig.colorbar(sm, orientation='vertical', label = 'Tree Canopy Height ('+rh_val+') [m]', ticks = [0, 10, 20, 30], aspect = 20, shrink = 0.8)

    plt.savefig(val[:-4]+'_'+str(rh_val)+'.pdf',dpi = 300, format = 'pdf', bbox_inches='tight') #pdf, because pdf looks much better, much smaller file size
    plt.close('all')
