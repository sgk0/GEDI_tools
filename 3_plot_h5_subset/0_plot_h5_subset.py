import os, h5py
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
from shapely.geometry import mapping, Point, Polygon, shape #to create the geomoetries for gpd

#-------------------------------User set these--------------------------------------#
use_qualflag = 1   #filter data according to quality flag yes/no
sens_thr = 0.90    #filter data according to sensitivity value ... dense tree recommend >=0.95
degrade_thr = 0.0  #filter data according to degrade flag, only keep entries less or equal to degrade_thr
rhpctl = 10        #only select every xxth percentile ... 10 will extract rh_values for 11 fields, 0, 10, 20 ... 100. 
hgt_thr = 30       #make a cloud mask, if terrarsarx dem is different from lowest return by XX m
#-----------------------------------------------------------------------------------#

#---------------------------------bookkeeping
bml = ['BEAM0000', 'BEAM0001', 'BEAM0010', 'BEAM0011', 'BEAM0101', 'BEAM0110', 'BEAM1000', 'BEAM1011'] #the root dir in the h5, datasets are grouped by beam
cwd = os.getcwd()
h5sfn = sorted([f for f in os.listdir('.') if f.endswith('_subset.h5')])

#----------------------read _subset.h5 fields for each h5
for num, val in enumerate(h5sfn):
    print('Working on file %s' %(val))
    #-------------create lists to hold the h5 data, one for each beam
    qual = [[] for f in bml]
    sens = [[] for f in bml]
    degrade = [[] for f in bml]
    shotn = [[] for f in bml]
    desc = [[] for f in bml]
    lons_c = [[] for f in bml]   
    lats_c = [[] for f in bml]   #c is corresponding to center of gaussian fit to the waveform
    dem = [[] for f in bml]
    elev_lm = [[] for f in bml]  #lm is lowestmode
    lons_lm = [[] for f in bml]
    lats_lm = [[] for f in bml]
    elev_hr = [[] for f in bml]  #hr is highestreturn
    lons_hr = [[] for f in bml]
    lats_hr = [[] for f in bml]
    ls_tree = [[] for f in bml]  #ls is landsat
    mod_tree = [[] for f in bml] #mod is modis
    rh_arr = [[] for f in bml]   #the 101 hr values from 0 to 100 inclusive
    #------------------------------
    with h5py.File(val, 'r') as f:
        for num2, val2 in enumerate(bml):
            qual[num2] = f[bml[num2]+'/quality_flag'][()]
            sens[num2] = f[bml[num2]+'/sensitivity'][()]
            degrade[num2] = f[bml[num2]+'/degrade_flag'][()]
            shotn[num2] = f[bml[num2]+'/shot_number'][()]
            desc[num2] = f[bml[num2]+'/description'][()]
            lons_c[num2] = f[bml[num2]+'/longitude_1gfit'][()]
            lats_c[num2] = f[bml[num2]+'/latitude_1gfit'][()]
            dem[num2] = f[bml[num2]+'/digital_elevation_model'][()]
            elev_lm[num2] = f[bml[num2]+'/elev_lowestmode'][()]
            lons_lm[num2] = f[bml[num2]+'/lon_lowestmode'][()]
            lats_lm[num2] = f[bml[num2]+'/lat_lowestmode'][()]
            elev_hr[num2] = f[bml[num2]+'/elev_highestreturn'][()]
            lons_hr[num2] = f[bml[num2]+'/lon_highestreturn'][()]
            lats_hr[num2] = f[bml[num2]+'/lat_highestreturn'][()]
            ls_tree[num2] = f[bml[num2]+'/landsat_treecover'][()]
            mod_tree[num2] = f[bml[num2]+'/modis_treecover'][()]
            rh_arr[num2] = f[bml[num2]+'/rh'][()]
        #---------all data, for all beams in h5 are read

    #--------------------goal is to take 10 - 20 rh categories for each beam and import them to a geopandas df for plotting/exporting
    nb = np.int(101/rhpctl)+1                  #number of bins
    rhhead = ['rh_'+str(i) for i in range(nb)] #list of headers for the rh value, for pandas
    rhcats = [[] for f in bml]                 #this is needed as we build lists for all the beams, and later iterate over each beam

    for num2, val2 in enumerate(rhcats):
        rhcats[num2]=[[] for f in rhhead]

    for num2, val2 in enumerate(rh_arr):
        for num3, val3 in enumerate(val2):
            for i in range(nb):
                rhcats[num2][i].append(val3[i*rhpctl])
                if num2 == 0 and num3 == 0:
                    print('Selected rh percentile bins %s' %(i*rhpctl))

    #in this scheme, rhcats[beam#][percentile_bin][point_number] ; this ordering is done because #beams (8) and # percentile bins (set by user) are constant, but #points is beam dependent
    #so for example rhcats[0][0] could be a list of 88 points. The points will be indices of the dataframe, and with 'rhpctl=10', rhcats[0][0] is the rh_0 column, rhcats[0][1] is the rh_10 column, etc..

    #---------------loop over beams
    for num2, val2 in enumerate(bml): #instead of num2 put num2
        print('Working on beam %s' %(num2))
        #print('shotn ', len(shotn[num2]))
        #print('qual ', len(qual[num2]))
        #print('sens ', len(sens[num2]))
        #print('degrade ', len(degrade[num2]))
        #print('desc ', len(desc[num2]))
        #print(desc[num2])
        #print('lons_c', len(lons_c[num2]))

        gpdhead = {'shotn_'+str(num2): shotn[num2], 'qual_'+str(num2): qual[num2], 'sens_'+str(num2): sens[num2], 'degrade_'+str(num2): degrade[num2], 'desc_'+str(num2): desc[num2], 'lons_c_'+str(num2): lons_c[num2], 'lats_c_'+str(num2): lats_c[num2], 'dem_'+str(num2): dem[num2], 'elev_lm_'+str(num2): elev_lm[num2], 'lons_lm_'+str(num2): lons_lm[num2], 'lats_lm_'+str(num2): lats_lm[num2], 'elev_hr_'+str(num2): elev_hr[num2], 'lons_hr_'+str(num2): lons_hr[num2], 'lats_hr_'+str(num2): lats_hr[num2], 'ls_tree_'+str(num2): ls_tree[num2], 'mod_tree_'+str(num2): mod_tree[num2]}
        geoml = []

        xx = pd.DataFrame(data=gpdhead)
        for num3, val3 in enumerate(rhcats[num2]):
            xx['rh_'+str(num3*rhpctl)] = val3 

        tmptst = (hgt_thr-(abs(xx['elev_lm_'+str(num2)] - xx['dem_'+str(num2)])) < 0)*1
        xx['cloud'] = tmptst

        for num3, (v0, v1) in enumerate(zip(lons_lm[num2], lats_lm[num2])): #replace if want lons_c, lons_lm, lons_hr ... in the gedi-example lat lon for lowestmode are used
            pt = Point(v0, v1)
            geoml.append(pt)
            
        xx['geometry'] = geoml

        xx = gpd.GeoDataFrame(xx, crs  ={'init': 'epsg:4326'}) 

        #---filter the data frame according to poor quality values
        if use_qualflag == 1:
            xx = xx.where(xx['qual_'+str(num2)].eq(1))

        xx = xx.where(xx['sens_'+str(num2)].ge(sens_thr))
        xx = xx.where(xx['degrade_'+str(num2)].le(degrade_thr))
        xx = xx.where(xx['cloud'].eq(0))
        xx = xx.dropna()
        
        if not xx.empty:
            #---output the filtered dataframe to a csv file
            #xx.to_csv(val[:-3]+'_bmn_'+str(num2)+'.csv', sep = ',', header = True, index = True) #commented, because this information is replicated in the shapefile and .csv is probably not needed
            #---output the filtered dataframe to a shapefile
            xx=xx.to_crs(epsg=3857)
            xx.to_file((val[:-3]+'_map_bmn_'+str(num2)+'.shp'))

            #----------plot canopy height for a beam
            ax, fig = plt.subplots()
            for num3, val3 in enumerate(rhcats[num2]):
                plt.plot(xx['rh_'+str(num3*rhpctl)], label='rh_'+str(num3*rhpctl), marker = 'o', linestyle='', markersize = 2)#, color = 'g', alpha = 0.2)

            plt.ylim([0,50])
            plt.title('Beam Number %s' %(str(num2)) + '\n' + val, fontsize = 10)
            plt.legend(ncol = 6, fontsize = 7, frameon=False)
            plt.ylabel('rh [m]')
            plt.xlabel('Shot number [-]')
            plt.ylim([0, 30])
            plt.savefig(val[:-3]+'_trans_'+str(num2)+'.png',dpi = 300, format = 'png', bbox_inches='tight')
            plt.close('all')
