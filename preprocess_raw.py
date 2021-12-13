# source: http://remote-sensing.org/preprocessing-of-sentinel-1-sar-data-via-snappy-python-module/

import snappy

from snappy import ProductIO
from snappy import HashMap

import os, gc
from snappy import GPF

GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
HashMap = snappy.jpy.get_type('java.util.HashMap')

path = "D:\\SENTINEL\\"
for folder in os.listdir(path):
    gc.enable()

    output = path + folder + "\\"
    timestamp = folder.split("_")[4]
    date = timestamp[:8]

    sentinel_1 = ProductIO.readProduct(output + "\\manifest.safe")
    print(sentinel_1)

    pols = ['VH', 'VV']
    for p in pols:
        polarization = p

        ### CALIBRATION

        parameters = HashMap()
        parameters.put('outputSigmaBand', True)
        parameters.put('sourceBands', 'Intensity_' + polarization)
        parameters.put('selectedPolarisations', polarization)
        parameters.put('outputImageScaleInDb', False)

        calib = output + date + "_calibrate_" + polarization
        target_0 = GPF.createProduct("Calibration", parameters, sentinel_1)
        ProductIO.writeProduct(target_0, calib, 'BEAM-DIMAP')

        ### SUBSET

        calibration = ProductIO.readProduct(calib + ".dim")
        WKTReader = snappy.jpy.get_type('com.vividsolutions.jts.io.WKTReader')

        wkt = "POLYGON((12.76221 53.70951, 12.72085 54.07433, 13.58674 54.07981,13.59605,53.70875, 12.76221,53.70951))"

        geom = WKTReader().read(wkt)

        parameters = HashMap()
        parameters.put('geoRegion', geom)
        parameters.put('outputImageScaleInDb', False)

        subset = output + date + "_subset_" + polarization
        target_1 = GPF.createProduct("Subset", parameters, calibration)
        ProductIO.writeProduct(target_1, subset, 'BEAM-DIMAP')

        ### TERRAIN CORRECTION

        parameters = HashMap()
        parameters.put('demResamplingMethod', 'NEAREST_NEIGHBOUR')
        parameters.put('imgResamplingMethod', 'NEAREST_NEIGHBOUR')
        parameters.put('demName', 'SRTM 3Sec')
        parameters.put('pixelSpacingInMeter', 10.0)
        parameters.put('sourceBands', 'Sigma0_' + polarization)

        terrain = output + date + "_corrected_" + polarization
        target_2 = GPF.createProduct("Terrain-Correction", parameters, subset)
        ProductIO.writeProduct(target_2, terrain, 'GeoTIFF')