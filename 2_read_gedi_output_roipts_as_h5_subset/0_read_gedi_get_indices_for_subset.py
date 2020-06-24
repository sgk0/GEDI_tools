import os, h5py, fiona, csv
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import mapping, Point, Polygon, shape #to create the geomoetries
from fiona.crs import from_epsg
{'init': 'epsg:4326', 'no_defs': True}

#bookkeeping
cwd = os.getcwd()
bml = ['BEAM0000', 'BEAM0001', 'BEAM0010', 'BEAM0011', 'BEAM0101', 'BEAM0110', 'BEAM1000', 'BEAM1011']
xdat = [[] for f in bml]
ydat = [[] for f in bml]
glon = '/geolocation/longitude_1gfit'
glat = '/geolocation/latitude_1gfit'
h5fl = sorted([f for f in os.listdir('.') if f.endswith('.h5') and not f.endswith('_subset.h5')])

cwd = os.getcwd()
rootdir, subdir = os.path.split(cwd)
shpdir = os.path.join(rootdir, '0_shapefile')
shpfn = [f for f in os.listdir(shpdir) if f.endswith('.shp')][0]
c = fiona.open(os.path.join(shpdir,shpfn))
pol = next(iter(c)) 
geom = shape(pol['geometry'])
print('Make sure the input geometry is a polygon! It is a:')
print(geom)

for num, val in enumerate(h5fl):
    print("Reading file %s" %(val))
    with h5py.File(val, 'r') as f:
        for num2, val2 in enumerate(bml):
            xdat[num2] = f[bml[num2]+glon][()]
            ydat[num2] = f[bml[num2]+glat][()]

    pipl = [[] for f in bml]
    pipixl = [[] for f in bml]

    print("Screening points in Geometry")
    for num2, val2 in enumerate(pipl):
        for num3, (v0, v1) in enumerate(zip(xdat[num2], ydat[num2])):
            pt = Point(v0, v1)
            if geom.contains(pt):
                pipl[num2].append(pt)
                pipixl[num2].append(num3)

    print("Writing shapefile and indices")
    
    #write the points locations to a shapefile
    schema = {
        'geometry': 'Point',
        'properties': {'id': 'int'},
    }

    # Write a new Shapefile
    #for each beam
    #for num2, val2 in enumerate(pipl):
    #    with fiona.open('beam_'+str(num2)+'.shp', 'w', crs=from_epsg(4326), driver='ESRI Shapefile', schema=schema) as c:
    #        ## If there are multiple geometries, put the "for" loop here
    #        for num3, val3 in enumerate(val2):
    #            c.write({
    #                'geometry': mapping(val3),
    #                'properties': {'id': 123},
    #            })
   
    #for all beams
    with fiona.open(val[:-3]+'_beams.shp', 'w', crs=from_epsg(4326), driver='ESRI Shapefile', schema=schema) as c:
            for num2, val2 in enumerate(pipl):
                for num3, val3 in enumerate(val2):
                    c.write({
                        'geometry': mapping(val3),
                        'properties': {'id': 123},
                    })

    #write the indices to a text file
    with open(val[:-3]+"_indices.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(pipixl)
