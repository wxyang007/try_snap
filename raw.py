import asf_search
import os
import numpy as np
import matplotlib.pyplot as plt
import snappy
from snappy import ProductIO

p = ProductIO.readProduct(r'C:\Users\wyang80\AppData\Local\conda\conda\envs\flood36\Lib\site-packages\snappy\testdata\MER_FRS_L1B_SUBSET.dim')
list(p.getBandNames())

band = p.getBand('radiance_3')
w = p.getSceneRasterWidth()
h = p.getSceneRasterHeight()

band_data = np.zeros(w * h, np.float32)
band.readPixels(0, 0, w, h, band_data)
band_data.shape = h, w

plt.figure(figsize=(18,10))
plt.imshow(band_data, cmap = plt.cm.binary)
plt.show()