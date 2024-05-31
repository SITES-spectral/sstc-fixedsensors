import pandas as pd
import numpy as np
from scipy.optimize import curve_fit






def linear_fit(x, a, b):
    return a * x + b

def calibration(
        up_channel: pd.Series, 
        dw_channel:pd.Series, 
        standard=1, 
        Threshold=0.03, 
        Iter=100, 
        speed=6):
    
    if len(up_channel) != len(dw_channel):
        print('Must be two equal length arrays')
        return
    
    dw_channel = dw_channel / standard
    XX, YY = up_channel.copy(), dw_channel.copy()

    popt, _ = curve_fit(linear_fit, up_channel, dw_channel)
    yfit = linear_fit(up_channel, *popt)
    ME = np.abs((yfit - dw_channel) / yfit)
    MaxME = np.max(ME)
    counter = 0
    
    while MaxME > Threshold:
        Ind = np.where(ME > speed * Threshold)[0]
        up_channel = np.delete(up_channel, Ind)
        dw_channel = np.delete(dw_channel, Ind)
        
        popt, _ = curve_fit(linear_fit, up_channel, dw_channel)
        yfit = linear_fit(up_channel, *popt)
        ME = np.abs(yfit - dw_channel) / np.mean(yfit)
        MaxME = np.max(ME)
        speed -= 1
        if speed < 1:
            speed = 1
        counter += 1
        print('Iteration {}, Wait...'.format(counter))
        if counter > Iter:
            print('Reach maximum iteration!')
            return
    
    print('Samples left {}.'.format(len(up_channel)))
    
    # Return the necessary data for plotting
    return XX, YY, up_channel, dw_channel, yfit
