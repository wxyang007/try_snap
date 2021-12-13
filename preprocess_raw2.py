# source: https://thegeoict.com/blog/2019/08/22/processing-sentinel-1-sar-images-using-snappy-snap-python-interface/

import snappy
import os
from snappy import ProductIO, GPF, HashMap

HashMap = snappy.jpy.get_type('java.util.HashMap')
GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

input = 'data'
output = 'output'


def write_product(data, file_path, format=None):
    # allowed format are: GeoTIFF-BigTIFF, HDF5, Snaphu, BEAM-DIMAP, GeoTIFF+XML, PolSARPro, NetCDF-CF, NetCDF-BEAM,
    # ENVI, JP2, Generic Binary, BSQ, Gamma, CSV, NetCDF4-CF, GeoTIFF, NetCDF4-BEAM

    ProductIO.writeProduct(data, file_path, format if format else 'BEAM-DIMAP')


def apply_orbit_file(data, datestamp):
    params = HashMap()
    orbit = GPF.createProduct('Apply-Orbit-File', params, data)
    #write_product(orbit, os.path.join(output, '{}_Orb'.format(datestamp)))
    return orbit


def do_calibration(orbit, datestamp):
    params = HashMap()
    params.put('outputSigmaBand', False)
    params.put('outputGammaBand', False)
    params.put('outputBetaBand', True)
    calibration = GPF.createProduct('Calibration', params, orbit)
    #write_product(calibration, os.path.join(output, '{}_Orb_Cal'.format(datestamp)))
    return calibration


def perform_multilook(calibration, datestamp, range_look_number=3, azimuth_look_number=3):
    params = HashMap()
    params.put('nRgLooks', range_look_number)
    params.put('nAzLooks', azimuth_look_number)
    params.put('outputIntensity', True)
    params.put('grSquarePixel', True)
    multilook = GPF.createProduct('Multilook', params, calibration)
    #write_product(multilook, os.path.join(output, '{}_Orb_Cal_ML'.format(datestamp)))
    return multilook


def perform_terrain_flattening(multilook, datestamp):
    params = HashMap()
    params.put('demName', 'SRTM 1Sec HGT')
    params.put('demResamplingMethod', 'BICUBIC_INTERPOLATION')
    params.put('oversamplingMultiple', 1.5)
    params.put('additionalOverlap', 0.1)
    terrain = GPF.createProduct('Terrain-Flattening', params, multilook)
    #write_product(terrain, '{}_Orb_Cal_ML_TF'.format(datestamp)))
    return terrain


def dem_coregistration(terrain, datestamp):
    params = HashMap()
    params.put('demName', 'SRTM 1Sec HGT')
    params.put('demResamplingMethod', 'BICUBIC_INTERPOLATION')
    # not sure if BILINEAR_INTERPOLATION would produce anything different
    # worth checking
    params.put('resamplingType', 'BICUBIC_INTERPOLATION')
    params.put('tileExtensionPercent', 100)
    params.put('maskOutAreaWithoutElevation', True)
    coregistered = GPF.createProduct('DEM-Assisted-Coregistration', params, terrain)
    write_product(coregistered, os.path.join(output, '{}_Orb_Cal_ML_TF_Stack'.format(datestamp)))
    return coregistered


def speckle_reduction(data, datestamp):
    params = HashMap()
    params.put('filter', 'Lee Sigma')
    params.put('enl', 4.0)
    params.put('numLooksStr', '4')
    params.put('windowSize', '9x9')
    params.put('sigmaStr', '0.9')
    params.put('targetWindowSizeStr', '5x5')
    speckle = GPF.createProduct('Speckle-Filter', params, data)
    # write_product(speckle, os.path.join(output, '{}_Orb_Cal_ML_TF_Stack_Spk'.format(datestamp)))
    return speckle


def ellipsoid_correction(speckle, datestamp):
    params = HashMap()
    params.put('imgResamplingMethod', 'BILINEAR_INTERPOLATION')
    params.put('mapProjection', 'WGS84(DD)')
    ec = GPF.createProduct('Ellipsoid-Correction-GG', params, speckle)
    write_product(ec, os.path.join(output, '{}_Orb_Cal_ML_TF_Stack_Spk_EC'.format(datestamp)), format='GeoTIFF')
    return ec


def process(file):
    data = ProductIO.readProduct(os.path.join(input, file))
    # get the end date from the file name and get first 8 substring as YYYYmmdd
    datestamp = file.split('_')[4][:8]
    orbit = apply_orbit_file(data, datestamp)
    calibration = do_calibration(orbit, datestamp)
    multilook = perform_multilook(calibration, datestamp)
    terrain = perform_terrain_flattening(multilook, datestamp)
    # coregistered = dem_coregistration(terrain, datestamp)
    speckle = speckle_reduction(terrain, datestamp)
    final = ellipsoid_correction(speckle, datestamp)
    print('finished')
    return True


def set_path():
    os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(os.getcwd())
    os.chdir(path)
    return path


def main():
    path = set_path()
    files = [f for f in os.listdir(input) if f.endswith('.zip')]
    for file in files:
        status = process(file)


if __name__ == '__main__':
    main()