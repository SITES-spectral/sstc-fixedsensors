import numpy as np
import matplotlib.pyplot as plt


def calibration(IN, OUT, standard=1, Threshold=0.03, Iter=100, speed=6):
    # Validate input dimensions
    if IN.ndim != 1 or OUT.ndim != 1:
        print('NOT work on matrix data!')
        return
    if IN.size != OUT.size:
        print('Must be two equal length arrays')
        return

    # Standardize OUT
    OUT = OUT / standard
    XX = IN.copy()
    YY = OUT.copy()
    
    # Fit initial model
    p = np.polyfit(IN, OUT, 1) # Linear fit
    yfit = np.polyval(p, IN)
    ME = np.abs((yfit - OUT) / yfit)
    MaxME = np.max(ME)
    counter = 0

    # Call the iterative calibration process
    IN, OUT, counter, MaxME, speed = iterate_calibration(IN, OUT, p, Threshold, Iter, speed, counter)

    # Plot final result
    plt.figure()
    plt.plot(XX, YY, 'o', markersize=4, label='Original Data')
    plt.plot(IN, np.polyval(p, IN), label='Calibrated Fit')
    plt.legend()
    plt.show()

def iterate_calibration(IN, OUT, p, Threshold, Iter, speed, counter):
    while True:
        plt.figure(1)
        plt.plot(IN, OUT, 'o', markersize=4)
        plt.draw()
        plt.pause(0.5)

        yfit = np.polyval(p, IN)
        ME = np.abs((yfit - OUT) / np.mean(yfit))
        MaxME = np.max(ME)
        
        if MaxME <= Threshold or counter >= Iter:
            break
        
        # Find indices of points to remove based on error threshold
        Ind = np.where(ME > speed * Threshold)[0]
        IN = np.delete(IN, Ind)
        OUT = np.delete(OUT, Ind)

        # Refit model
        p = np.polyfit(IN, OUT, 1)
        
        speed = max(speed - 1, 1) # Ensure speed does not drop below 1
        counter += 1

        # Display iteration progress
        print(f'Iteration {counter}, Wait...')

    if counter >= Iter:
        print('Reached maximum iteration!')

    return IN, OUT, counter, MaxME, speed

# Example usage
#IN = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
#OUT = np.array([2.1, 3.9, 6.0, 8.1, 9.8, 11.9, 14.1, 15.9, 18.0, 19.9])
#calibration(IN, OUT)
