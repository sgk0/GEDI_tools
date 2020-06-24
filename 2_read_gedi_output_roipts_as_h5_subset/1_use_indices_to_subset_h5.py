import os, h5py, csv
import numpy as np
import matplotlib.pyplot as plt

#-------------------bookkeeping----------------#
cwd = os.getcwd()
idxfn = sorted([f for f in os.listdir('.') if f.startswith('GEDI02') and f.endswith('_indices.csv')])
glon = '/geolocation/longitude_1gfit'
glat = '/geolocation/latitude_1gfit'
lstree = '/land_cover_data/landsat_treecover'
tree = '/land_cover_data/modis_treecover'
treesd = '/land_cover_data/modis_treecover_sd'

#-------------------read in the indices of the data falling into the roi (from prior processing step: 0_read_gedi_get_indices_for_subset.py----------------#
#please note: these indices correspond to points falling in roi based on the lon, lat corresponding to the center of a single gaussian fit to the waveform. 
for num, val in enumerate(idxfn):
    readix = []
    with open(val, "r", newline="") as f:
        reader = csv.reader(f, delimiter=',') #quotechar = '|'
        for row in reader:
            readix.append(list(map(int,row)))
#-------------------define the data fields we want to extract----------------#
    #June-6: consider adding sensitivity, degrade flag ; degrade need be zero; sensitivity should be > 0.9 or even higher for dense forest

    bml = ['BEAM0000', 'BEAM0001', 'BEAM0010', 'BEAM0011', 'BEAM0101', 'BEAM0110', 'BEAM1000', 'BEAM1011']
    qual = [[] for f in bml]
    sens = [[] for f in bml]
    degrade = [[] for f in bml]
    shotn = [[] for f in bml]
    desc = [[] for f in bml]
    lons_c = [[] for f in bml] #corresponding to center of gaussian fit to the waveform
    lats_c = [[] for f in bml] #corresponding to center of gaussian fit to the waveform

    #dem
    dem = [[] for f in bml]

    #lowestmode
    elev_lm = [[] for f in bml]
    lons_lm = [[] for f in bml]
    lats_lm = [[] for f in bml]

    #highestreturn
    elev_hr = [[] for f in bml]
    lons_hr = [[] for f in bml]
    lats_hr = [[] for f in bml]

    #land_cover_data
    ls_tree = [[] for f in bml]
    mod_tree = [[] for f in bml]
    mod_tree_sd = [[] for f in bml]

    #rh values
    rh_arr = [[] for f in bml]

#-------------------read the GEDI02_A h5 files----------------#
    print('Reading file %s' %(val[:-12]+'.h5'))
    with h5py.File(val[:-12]+'.h5', 'r') as f:
        #f.visit(print) #this also prints the datasets like h5ls -r
        for num2, val2 in enumerate(bml):
            shotn[num2] = f[bml[num2]+'/shot_number'][readix[num2]]
            qual[num2] = f[bml[num2]+'/quality_flag'][readix[num2]]
            degrade[num2] = f[bml[num2]+'/degrade_flag'][readix[num2]]
            sens[num2] = f[bml[num2]+'/sensitivity'][readix[num2]]
            lons_c[num2] = f[bml[num2]+glon][readix[num2]]
            lats_c[num2] = f[bml[num2]+glat][readix[num2]]
            dem[num2] = f[bml[num2]+'/digital_elevation_model'][readix[num2]]
            elev_lm[num2] = f[bml[num2]+'/elev_lowestmode'][readix[num2]]
            lons_lm[num2] = f[bml[num2]+'/lon_lowestmode'][readix[num2]]
            lats_lm[num2] = f[bml[num2]+'/lat_lowestmode'][readix[num2]]
            elev_hr[num2] = f[bml[num2]+'/elev_highestreturn'][readix[num2]]
            lons_hr[num2] = f[bml[num2]+'/lon_highestreturn'][readix[num2]]
            lats_hr[num2] = f[bml[num2]+'/lat_highestreturn'][readix[num2]]
            ls_tree[num2] = f[bml[num2]+lstree][readix[num2]]
            mod_tree[num2] = f[bml[num2]+tree][readix[num2]]
            mod_tree_sd[num2] = f[bml[num2]+treesd][readix[num2]]
            rh_arr[num2] = f[bml[num2]+'/rh'][readix[num2]]
            
#            if num == 0:
            for num3, val3 in enumerate(bml):
                desc[num3] = f[val3].attrs['description']
                #Therefore, beams 4,5,6,7 are best as they are full power rather than coverage

#-------------------write subset to h5----------------#
    #note that we've read the different beams into lists of numpy arrays, it is a little more convenient for data operation.
    #But hdf5 only works on the arrays, so one needs to add another dimenstion to the array, for each dataset

    #save as hdf5
    print('Writing file %s' %(val[:-12]+'_subset.h5'))
    with h5py.File(val[:-12]+'_subset.h5', 'w') as f:
        for num, val in enumerate(bml):
            f.create_dataset(val+'/description', data = desc[num])
            f.create_dataset(val+'/shot_number', data = shotn[num])
            f.create_dataset(val+'/quality_flag', data = qual[num])
            f.create_dataset(val+'/degrade_flag', data = degrade[num])
            f.create_dataset(val+'/sensitivity', data = sens[num])
            f.create_dataset(val+'/longitude_1gfit', data = lons_c[num])
            f.create_dataset(val+'/latitude_1gfit', data = lats_c[num])
            f.create_dataset(val+'/digital_elevation_model', data = dem[num])
            f.create_dataset(val+'/elev_lowestmode', data = elev_lm[num])
            f.create_dataset(val+'/lon_lowestmode', data = lons_lm[num])
            f.create_dataset(val+'/lat_lowestmode', data = lats_lm[num])
            f.create_dataset(val+'/elev_highestreturn', data = elev_hr[num])
            f.create_dataset(val+'/lon_highestreturn', data = lons_hr[num])
            f.create_dataset(val+'/lat_highestreturn', data = lats_hr[num])
            f.create_dataset(val+'/landsat_treecover', data = ls_tree[num])
            f.create_dataset(val+'/modis_treecover', data = mod_tree[num])
            f.create_dataset(val+'/rh', data = rh_arr[num])
