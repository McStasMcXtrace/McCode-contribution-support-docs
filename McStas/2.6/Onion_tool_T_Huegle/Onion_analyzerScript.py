###############################################################################
#~ Script to analyze McStas ONION type instrument simulation output
#~ Saves output images. Comment out lines containing "fig.savefig" to disable.

#~ Assumes McStas simulation is run in Mantid mode and produced a NeXus file
#~ Assumes python3 version of Mantid (e.g. 'mantidnightly-python3') 
#~ Tested using a jupyter notebook running on Ubuntu
#~ Tested using the "Mantid Workbench" on the SNS analysis cluster (https://analysis.sns.gov/)


#~ Written by: Thomas Huegle
#~ Date: July 2019
#~ Origin: ORNL
###############################################################################

# Tell python where to find python3 version of Mantid
import os
import sys
sys.path.append('/opt/mantidnightly-python3/bin')
from mantid.simpleapi import *
# Load matplotlib for plotting and numpy for math
import matplotlib.pyplot as plt
import numpy as np


def dConvertr(binning):
    # Converts Event data into d-Spacing and creates spectra
    ConvertUnits(InputWorkspace="EventData_data",OutPutWorkspace = "data_d",Target= "dSpacing",AlignBins=True)
    Rebin(InputWorkspace="data_d", OutputWorkspace="data_d_rebin", Params=binning)
    data_d_rebin = mtd['data_d_rebin']
    return data_d_rebin
    
def prepr():
    # Creates a dictionary that contains pixel coordinates and more
    preprDetWS = PreprocessDetectorsToMD(InputWorkspace="EventData_data",GetMaskState=1,GetEFixed=1)
    preprDetWSDict = preprDetWS.toDict()
    return(preprDetWSDict)
    
def pixelPlotr(path,dataDict,binnedData,binningParams,peakCenter):
    # Plots four pixels: innermost ring/forward scattering, innermost ring/backscattering, outermost ring/forward scattering, outermost ring/backscattering: 
    rList = dataDict['L2']
    # establish lists of all pixels that have min and max radii (they have to be rounded because there sometimes are small aberrations from "ideal")
    rMinList = [i for i, e in enumerate(rList) if round(e,3) == round(min(rList),3)]
    rMaxList = [i for i, e in enumerate(rList) if round(e,3) == round(max(rList),3)]
    # take lowest and highest pixelIDs of the aforementioned lists (there are probably ways to do this in one step)
    indices = [min(rMinList), max(rMinList), min(rMaxList), max(rMaxList)]
    # convert the Mantid histogram data into point data so that matplotlib can use it
    pdata = ConvertToPointData(binnedData)
    # set up plot
    fig, ax = plt.subplots(2,2, figsize=(10, 10), facecolor='w', edgecolor='k')
    fig.subplots_adjust(hspace = .2, wspace=.2)
    ax = ax.ravel()
    for i in range(4):
        ax[i].set_xlim(peakCenter*0.8, peakCenter*1.2)
        # readX(pixelID) and readY(pixelID) access Mantid spectra of individual pixels:
        ax[i].plot(pdata.readX(indices[i]), pdata.readY(indices[i]), color="red")
        ax[i].set_title('pixel id: {}'.format(indices[i]), va='bottom',size=16)
    fig.text(.5, -0.01,'rmin/fw, rmin/back, \nrmax/fw, rmax/back \nbinningParams = {}'.format(binningParams),ha='center',size= 22)
    fig.savefig(path + '/fourPixels.png')
    plt.show()  
    
def peakFindr(data_d_rebin, peakPosition):
    # Finds peaks using Mantid's FindPeaks algorithm
    FindPeaks(data_d_rebin,PeakPositions=peakPosition,PeaksList='dataPeaks',FWHM = 7,BackgroundType='Flat')
    dataPeaks=mtd['dataPeaks']
    peaksDict = dataPeaks.toDict()
    # calculate resolutions as "delta d / d"
    resList = [x / peakPosition for x in peaksDict['width']]
    peaksDict['resolution'] = resList
    return peaksDict    
    
def filterr(filteredDict):
    # if the peak width is zero, set every corresponding entry (including its radius!) in the dictionary to zero: 
    for i in np.arange(len(filteredDict['width'])):
        if filteredDict['width'][i] > 0.0:
            continue
        else: 
            for k in filteredDict.keys():
                filteredDict[k][i] = 0
    return filteredDict
    
def plotr(path,dataDict,comment,peakCenter):
    # Plots the data contained in the dataDict
    # Define data:
    r = dataDict['L2']
    theta = dataDict['TwoTheta']
    colors = dataDict['resolution']
    # Set up plot:
    fig = plt.figure(figsize=(20, 15))
    ax = plt.subplot(111, projection='polar')
    im = ax.scatter(theta, r, s=50, c=colors, cmap='hsv', alpha=.3)
    # Adjust plot specifics
    ax.tick_params(axis='both', which='major', labelsize=20)
    ax.set_rmax(4.05)
    ax.set_rticks([1, 2, 3.0, 4.0])  # less radial ticks
    ax.set_rlabel_position(-22.5)  # get radial labels away from plotted line
    ax.grid(True)
    fig.patch.set_facecolor('white')
    ax.set_title("Resolution of a ${}\AA$ peak as a function of angle and distance".format(peakCenter), va='bottom',size=22)
    # This is the lowest and highest resolution value (a.k.a. worst resolution) it will plot:
    im.set_clim(0, 0.01)
    cbar = fig.colorbar(im,ax=ax)
    cbar.ax.tick_params(labelsize=20)
    fig.text(.43, 0,'file: {}\nbinning: {}'.format(path.split('/')[-1],comment),ha='center',size= 22)
    plt.show()
    # Picture will automatically be saved:
    fig.savefig(path + '/resolutionMap_{}.png'.format(comment))

def main(path,peakCenter,binningParams):
    # Load the data (unfortunately, the "data" name is hardcoded. feel free to improve this!):
    data = LoadMcStas(path+'/mccode.h5')
    # convert to d-Spacing, make one histogramm per pixelID:
    binnedData = dConvertr(binningParams)
    # create Dictionary that contains (amongst others) geometric information (check dict keys below for more info):
    dataDict = prepr()
    # check the dictionary keys so far, just to be sure:
    print('initial data: {}\n\n'.format(dataDict.keys()))
    # plot four pixels: innermost ring/forward scattering, innermost ring/backscattering, outermost ring/forward scattering, outermost ring/backscattering: 
    pixelPlotr(path,dataDict,binnedData,binningParams,peakCenter)
    print("depending on angular coverage, sample d-spacing, or statistics some pixels might not see any counts!\n\n")
    # fit each one of the pixel spectra using Mantid's FindPeaks, attach to the data dictionary:
    dataDict.update(peakFindr(binnedData,peakCenter))
    # this should have changed the number of keys significantly, better check again:
    print('analyzed data: {}\n\n'.format(dataDict.keys()))
    # if the peak width is zero (because of noise etc.), set every corresponding entry (including its radius!) in the dictionary to zero: 
    dataDict = filterr(dataDict)
    # plot the onion! Warning: this includes a cutoff for the worst resolution
    plotr(path,dataDict,binningParams,peakCenter)

######################################################################################

# path to directory that contains the mccode.h5 output file from the McStas simulation
pathList = ['/YOUR/PATH/HERE']
for path in pathList:
    # d-Spacing of peak in simulation:	
    peakCenter = 2.0
    # binning parameters used in the analysis ([min], [bin width],[max])
    binningParams = '{},0.001,{}'.format(peakCenter*0.7,peakCenter*1.3)
    main(path,peakCenter,binningParams)

######################################################################################