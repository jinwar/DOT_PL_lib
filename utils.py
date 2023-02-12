import matplotlib.pyplot as plt
import numpy as np


class FiberMapping:
    THIN_V = 42.0
    FLAT_V = 70.0
    THICK_V = 143.0
    STRAIGHT_V = 176.0
    HELICAL_V = 558.0
    V_LOCS = (THIN_V,FLAT_V,THICK_V,STRAIGHT_V,HELICAL_V)

    

class PlotFunctions:

    def __init__(self):
        pass

    @staticmethod
    def plot_vsections(horizontal=True,color='k',style='--'):
        for loc in FiberMapping.V_LOCS:
            if horizontal:
                plt.axhline(y=loc, color=color,linestyle=style)
            else:
                plt.axvline(y=loc, color=color,linestyle=style)
