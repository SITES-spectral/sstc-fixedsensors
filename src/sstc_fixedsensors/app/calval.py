import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt



def calibration(IN, OUT, standard=1, Threshold=0.03, Iter=100, speed=6):
    if IN.ndim != 1 or OUT.ndim != 1:
        print('NOT work on matrix data!')
        return
    
    if len(IN) != len(OUT):
        print('Must be two equal length arrays')
        return
    
    OUT = OUT / standard
    XX, YY = IN.copy(), OUT.copy()
    
    def linear_fit(x, a, b):
        return a * x + b
    
    popt, _ = curve_fit(linear_fit, IN, OUT)
    yfit = linear_fit(IN, *popt)
    ME = np.abs((yfit - OUT) / yfit)
    MaxME = np.max(ME)
    counter = 0
    
    while MaxME > Threshold:
        plt.figure(1)
        plt.plot(IN, OUT, 'o', markersize=4)
        plt.draw()
        plt.pause(0.5)
        
        Ind = np.where(ME > speed * Threshold)[0]
        IN = np.delete(IN, Ind)
        OUT = np.delete(OUT, Ind)
        
        popt, _ = curve_fit(linear_fit, IN, OUT)
        yfit = linear_fit(IN, *popt)
        ME = np.abs(yfit - OUT) / np.mean(yfit)
        MaxME = np.max(ME)
        speed -= 1
        if speed < 1:
            speed = 1
        counter += 1
        print('Iteration {}, Wait...'.format(counter))
        if counter > 100:
            print('Reach maximum iteration!')
            return
    
    print('Samples left {}.'.format(len(IN)))
    plt.figure(1)
    plt.plot(XX, YY, 'o', color=[0.7, 0.7, 0.7], markersize=4)
    plt.plot(IN, OUT, 'o', markersize=4)
    plt.plot(IN, yfit, 'r-')
    plt.xlabel('In (mV)')
    plt.ylabel('Out (mV)')
    plt.show()
    return linear_fit