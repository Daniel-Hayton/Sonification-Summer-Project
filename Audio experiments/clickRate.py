import strauss
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.use("tkagg")
plt.style.use("dark_background")

N = 500
x = np.linspace(0, 1, N)
y = 2 ** (np.sin(x * 8 * np.pi) * 3)
# y = x
# y = 1-np.log(x+0.1)


# and plot...
plt.plot(x, y)
plt.ylabel(f"y")
plt.xlabel("time")
# plt.show()

duration = 30
Nsamp = duration * 5  # Number of discrete events (clicks/notes) to generate

# Ticker works by sampling the growth of the integral
# of the input function by even increments

# first get the simple integral by just using a cumulative sum
ycum = np.cumsum(y)
ycum /= ycum.max()

yCumHigh = np.cumsum(y - 0.1)
yCumHigh /= yCumHigh.max()

# now set up the uniform increments
incs = np.linspace(0, 1, Nsamp + 1)
incs = incs[:-1] + np.diff(incs) * 0.5

# now interpolate for the times between (0,1) for each of the N_samp ticks
event_times = np.interp(incs, ycum, x)
highTime = np.interp(incs, yCumHigh, x)

soni1p5 = strauss.sonify(event_times, np.ones(Nsamp), style='highClick.yml', duration=30)
soni1p5.render()
# soni1p5.hear()
strauss.close()

timeSort = np.argsort(event_times)
# event_times = event_times[timeSort]


strauss.sonify(event_times, np.ones(Nsamp), style="clickStyle.yml", duration=30)
strauss.sonify(event_times, np.ones(Nsamp), style="highClick.yml", duration=30)
# strauss.save("test1.wav")
strauss.close()

strauss.sonify(event_times, np.ones(Nsamp), style="clickStyle.yml", duration=30)
strauss.sonify(event_times + (0.15/2), np.ones(Nsamp), style="highClick.yml", duration=30)
# strauss.save("test2.wav")
strauss.close()

strauss.sonify(event_times[::2], np.ones(Nsamp)[::2], style="clickStyle.yml", duration=30)
strauss.sonify(event_times[1::2], np.ones(Nsamp)[1::2], style="highClick.yml", duration=30)
# strauss.save("test3.wav")
strauss.close()

strauss.sonify(event_times, np.ones(Nsamp), style="clickStyle.yml", duration=90)
strauss.sonify(highTime, np.ones(Nsamp), style="highClick.yml", duration=90)
strauss.save("test4.wav")
strauss.close()
