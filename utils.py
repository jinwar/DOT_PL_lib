import matplotlib.pyplot as plt
import numpy as np
import dascore
import os
from JIN_pylib import Data2D_XT,ProcessUtil,gjsignal,BasicClass    # JIN_pylib 
from dataclasses import dataclass

class FiberMapping:
    THIN_V = 42.0
    FLAT_V = 70.0
    THICK_V = 143.0
    STRAIGHT_V = 176.0
    HELICAL_V = 558.0
    V_LOCS = (THIN_V,FLAT_V,THICK_V,STRAIGHT_V,HELICAL_V)

class FiberMapping_V2:
    THIN_V = 50.0
    FLAT_V = 78.0
    THICK_V = 151.0
    STRAIGHT_V = 184.0
    HELICAL_V = 564.0
    V_LOCS = (THIN_V,FLAT_V,THICK_V,STRAIGHT_V,HELICAL_V)
    

class PlotFunctions:
    """
    This class is used to store commonly used plotting function
    """

    def __init__(self):
        pass

    @staticmethod
    def plot_vsections(horizontal=True,color='k',style='--',new_mapping=True):
        for loc in FiberMapping.V_LOCS:
            if new_mapping:
                loc = loc+8
            if horizontal:
                plt.axhline(y=loc, color=color,linestyle=style)
            else:
                plt.axvline(y=loc, color=color,linestyle=style)

class DataIO:
    
    def __init__(self, datapath, reset_index = False):
        self.datapath = datapath
        self.load_contents(reset_index)
        
    def load_contents(self,reset_index):
        if reset_index:
            index_file = self.datapath+'/.dascore_index.h5'
            try:
                os.remove(index_file)
            except:
                print('cannot find:', index_file)
        self.sp = dascore.spool(self.datapath)
        data_df = self.sp.get_contents()
        self.data_df = data_df.sort_values(by='time_min')
        
    def get_data(self,bgtime,duration:int, gauge_length=3,timezone=None):
        if timezone is not None:
            bgtime = bgtime - np.timedelta64(timezone,'h')
        edtime = bgtime + np.timedelta64(int(duration),'s')
        das_patches = self.sp.select(time = (bgtime,edtime))
        das_patch = dascore.utils.patch.merge_patches(das_patches,tolerance=5)[0]
        DASdata = Data2D_XT.Patch_to_Data2D(das_patch)
        DASdata.apply_gauge_length(gauge_length)
        return DASdata

    def get_DataSec(self,bgtime,label,**kwargs):
        datasec = DataSec(bgtime,label,**kwargs)
        kwargs.pop('timezone',None)
        kwargs.pop('duration',None)
        datasec.get_data(self,**kwargs)
        return datasec
    
    def get_spectrum(self, bgtime:str, duration:int, d_time:int=1, label:str=None,timezone=-7):
        bgtime = np.datetime64(bgtime)
        bgtime = bgtime - np.timedelta64(timezone,'h')
        edtime = bgtime + np.timedelta64(duration,'s')
        current_time = bgtime

        DASdata = self.get_data(current_time, d_time)

        dt = np.median(np.diff(DASdata.taxis))
        f0,amp = gjsignal.amp_spectrum(DASdata.data[0,:],dt)

        sp_mat = np.zeros((DASdata.data.shape[0],len(f0)))
        timeN = 0

        while current_time < edtime:

            DASdata = self.get_data(current_time, d_time)
            gjsignal.print_progress(current_time)

            for ichan in range(DASdata.data.shape[0]):
                f,amp = gjsignal.amp_spectrum(DASdata.data[ichan,:],dt)
                amp = np.interp(f0,f,amp)
                sp_mat[ichan,:] += amp

            timeN += 1
            current_time += np.timedelta64(d_time,'s')


        sp_mat = sp_mat/timeN
        spdata = Spectrum2D(data = sp_mat,
                            faxis=f0,
                            daxis=DASdata.daxis,
                            bgtime=bgtime,
                            duration=duration,
                            label=label)
        return spdata

@dataclass
class Spectrum2D(BasicClass.BasicClass):
    data: np.ndarray # 2D numpy array, first axis is distance, second axis is frequency
    faxis: np.ndarray # 1D numpy array, frequency axis
    daxis: np.ndarray # 1D numpy array, distance axis
    bgtime: np.datetime64 # beginning time of the spectrum calculation
    duration: np.int # duration in seconds of the spectrum calculation
    label: str # label of the spectrum
    
    def plot_waterfall(self):
        plt.imshow(self.data, extent=[self.faxis.min(), self.faxis.max(), self.daxis.max(), self.daxis.min()], aspect='auto',cmap='seismic')
        plt.xlabel('Frequency')
        plt.ylabel('Distance')
        plt.title(self.label)
        plt.colorbar()
    
    
    def get_dist_average_spectrum(self,begin_dist,end_dist):
        ind = (self.daxis>=begin_dist)&(self.daxis<end_dist)
        data = np.mean(self.data[ind,:],axis=0)
        trc = Spectrum1D(self.faxis,[begin_dist,end_dist],data)
        return trc
        
    def get_spe_trace(self,begin_freq,end_freq):
        ind = (self.faxis>=begin_freq)&(self.faxis<end_freq)
        data = np.mean(self.data[:,ind],axis=1)
        trc = Spectrum1D([begin_freq,end_freq],self.daxis,data)
        return trc
    
    @staticmethod
    def load_pickle(filename):
        data = Spectrum2D(None,None,None,None,None,None)
        data.load(filename)
        return data

@dataclass
class Spectrum1D:
    frequency: np.array 
    distance: np.array 
    data: np.array 
    label: str = None
    
    def plot(self):
        if len(self.frequency) == len(self.data):
            plt.plot(self.frequency,self.data,label=self.label)
            plt.xlabel('Frequency')
            plt.ylabel('Amplitude')
        else:
            plt.plot(self.distance,self.data,label=self.label)
            plt.xlabel('Distance')
            plt.ylabel('Amplitude')
    
    
class DataSec:
    
    def __init__(self,bgtime,label,duration=3,timezone=-7):
        bgtime = np.datetime64(bgtime)
        UTCtime = bgtime - np.timedelta64(timezone,'h')
        self.DASdata = None
        self.bgtime = bgtime
        self.label = label
        self.duration=duration
        self.timezone=timezone
        self.UTCtime = UTCtime
    
    
    def get_data(self,dataio,**kwargs):
        self.DASdata = dataio.get_data(self.UTCtime,self.duration, **kwargs)
    
    def make_plot(self,ylim=[200,0],clim=3e-6,new_mapping=True):
        self.DASdata.plot_waterfall()
        PlotFunctions.plot_vsections(new_mapping=new_mapping)
        plt.colorbar()
        cx = np.array([-1,1])
        plt.clim(cx*clim)
        plt.title(self.label)
        plt.xlabel('Seconds from: '+ str(self.bgtime))
        plt.ylim(ylim)

        
import re

def make_legal_filename(filename):
    """
    Converts a string to a legal filename for Linux.
    """
    # Replace whitespace with underscores
    filename = re.sub(r'\s+', '_', filename)
    
    # Remove characters that are not alphanumeric, underscores, or periods
    filename = re.sub(r'[^\w.]+', '', filename)
    
    # Remove leading and trailing periods and underscores
    filename = filename.strip('._')
    
    # Convert to lowercase
    filename = filename.lower()
    
    # Add a prefix if the filename is empty
    if not filename:
        filename = 'unnamed_file'
    
    return filename


def get_spe_filename_from_log(row):
    filename = row['Date'] + '_'
    filename += row['Experiment velocity (m/s)']
    filename += '.p'
    filename = make_legal_filename(filename)
    return filename
