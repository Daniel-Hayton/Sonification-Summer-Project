import strauss as sts
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

sampOnes = np.ones(Nsamp)

soni1p5 = sts.sonify(event_times, sampOnes, style='highClick.yml', duration=30)
soni1p5.render()
# soni1p5.hear()
sts.close()

timeSort = np.argsort(event_times)
# event_times = event_times[timeSort]


sts.sonify(event_times, sampOnes, style="lowClick.yml", duration=30)
sts.sonify(event_times, sampOnes, style="highClick.yml", duration=30)
sts.save("test1.wav")
sts.close()

displacement = -0.15
sts.sonify(event_times, sampOnes, style="lowClick.yml", duration=30)
sts.sonify(event_times + displacement, sampOnes, style="highClick.yml", duration=30)
sts.sonify(np.linspace(0, 30, len(event_times)), sampOnes, style="metro.yml", duration=30)
sts.save("test2.wav")
sts.close()

sts.sonify(event_times[::2], sampOnes[::2], style="lowClick.yml", duration=30)
sts.sonify(event_times[1::2], sampOnes[1::2], style="highClick.yml", duration=30)
sts.save("test3.wav")
sts.close()

sts.sonify(event_times, sampOnes, style="lowClick.yml", duration=30)
sts.sonify(highTime, sampOnes, style="highClick.yml", duration=30)
sts.save("test4.wav")
sts.close()

x = np.linspace(0, 10, 9) * 0.5
x2 = np.linspace(0, 10, 3)
sts.sonify(x, np.ones(len(x)), style='lowClick.yml', duration=10, system='mono')
sts.sonify(x2, np.ones(len(x2)), style='highClick.yml', duration=10, system='mono')
sts.save("test5.wav")
sts.close()

length = 30
x = np.linspace(0, 10, length)
y = np.arange(length) % 2

sts.sonify(x, y, style='clickStyle.yml', duration=20)
sts.save("test6.wav")
sts.close()

altPitch = np.arange(len(event_times)) % 2
sts.sonify(event_times, altPitch, style="clickStyle.yml", duration=30, system='mono')
sts.save("test7.wav")
sts.close()

afterTheEvent = event_times[:-1] + (np.diff(event_times) / 2)
sts.sonify(event_times[:-1], np.ones(Nsamp - 1), style="lowClick.yml", duration=30, system='mono')
sts.sonify(afterTheEvent, np.ones(Nsamp - 1), style='highClick.yml', duration=30, system='mono')
sts.save("test8.wav")
sts.close()

sts.sonify(x, y, style="metro.yml", duration=length, system="stereo", level="-20 db")
sts.sonify(event_times, sampOnes, style="lowClick.yml", duration=length, system="mono")
sts.sonify(afterTheEvent, sampOnes[:-1], style="highClick.yml", system="mono", duration=length)
sts.save("test9.wav")
sts.close()
