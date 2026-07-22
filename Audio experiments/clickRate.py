"""Series of tests on tempo mapping with event source types, test outcomes labeled Pass or Fail"""

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
# y = x**3
# y = np.sin(x)

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

# Layering 2 sonifications (Pass)
sts.sonify(event_times, sampOnes, style="lowClick.yml", duration=30)
sts.sonify(event_times, sampOnes, style="highClick.yml", duration=30)
# sts.save("test1.wav")
sts.close()

# Trying basic off set for timing (Fail)
displacement = -0.15
sts.sonify(event_times, sampOnes, style="lowClick.yml", duration=30)
sts.sonify(event_times + displacement, sampOnes, style="highClick.yml", duration=30)
sts.sonify(np.linspace(0, 30, len(event_times)), sampOnes, style="metro.yml", duration=30)
# sts.save("test2.wav")
sts.close()

# Trying to have different tone for every other beat bby selecting the half the time events from the array (Fail)
sts.sonify(event_times[::2], sampOnes[::2], style="lowClick.yml", duration=30)
sts.sonify(event_times[1::2], sampOnes[1::2], style="highClick.yml", duration=30)
# sts.save("test3.wav")
sts.close()

# Change the coding of the graph by a fixed off set (Fail)
sts.sonify(event_times, sampOnes, style="lowClick.yml", duration=30)
sts.sonify(highTime, sampOnes, style="highClick.yml", duration=30)
# sts.save("test4.wav")
sts.close()

# Trying out regular beats
# x = np.linspace(0, 10, 9) * 0.5
# x2 = np.linspace(0, 10, 3)
# sts.sonify(x, np.ones(len(x)), style='lowClick.yml', duration=10, system='mono')
# sts.sonify(x2, np.ones(len(x2)), style='highClick.yml', duration=10, system='mono')
# sts.save("test5.wav")
# sts.close()

# Testing switching between beat types by pitch marker (Pass)
length = 30
# x = np.linspace(0, 10, length)
# y = np.arange(length) % 2
#
# sts.sonify(x, y, style='clickStyle.yml', duration=20)
# sts.save("test6.wav")
# sts.close()

# Having alternative pitches for the time events (Pass)
altPitch = np.arange(len(event_times)) % 2
sts.sonify(event_times, altPitch, style="clickStyle.yml", duration=30, system='mono')
# sts.save("test7.wav")
sts.close()

# Tempo type 2 with pared beats using difference in beat times (Pass)
betweenTimes = np.diff(event_times)
afterTheEvent = event_times[:-1] + (betweenTimes / 2)
sts.sonify(event_times[:-1], np.ones(Nsamp - 1), style="lowClick.yml", duration=30, system='mono')
sts.sonify(afterTheEvent, np.ones(Nsamp - 1), style='highClick.yml', duration=30, system='mono')
# sts.save("test8.wav")
sts.close()


# Tempo type 2 with counter
def timeKeeper(clicksPerSec):
    totalClicks = clicksPerSec * length
    sts.sonify(np.linspace(0, 10, totalClicks), np.arange(totalClicks) % 2, style="metro.yml", duration=length,
               system="stereo", level="-10 db")


timeKeeper(1)
sts.sonify(event_times, sampOnes, style="lowClick.yml", duration=length, system="mono")
sts.sonify(afterTheEvent, sampOnes[:-1], style="highClick.yml", system="mono", duration=length)
# sts.save("test9.wav")
sts.close()

# Tempo type 3 distance from a base line (Fail)
nTempo = Nsamp - 1
tempoOnes = np.ones(nTempo)

baseInc = np.max(betweenTimes) / 2
base = np.arange(0, baseInc * nTempo, baseInc)

tempoHit = base + (betweenTimes / 4)

length = 30
sts.sonify(base, tempoOnes, style="lowClick.yml", duration=length)
sts.sonify(tempoHit, tempoOnes, style='highClick.yml', duration=length)
# sts.sonify(event_times, sampOnes, style="highClick.yml", duration=length)
# sts.save("test10.wav")
sts.close()

# Tempo type 1 same as test 7 but with sound font (Pass)
sts.sonify(event_times, altPitch, style="metro.yml", duration=length)
# sts.save("test11.wav")
sts.close()

# Tempo type 3 but sound font, you guessed it (Fail)
sts.sonify(base, np.zeros(len(base)), style="metro.yml", duration=length)
sts.sonify(base + betweenTimes, np.ones(len(base)), style="metro.yml", duration=length)
# sts.save("test12.wav")
sts.close()


# Mapping a sine to frequency (code lifted from black hole show)
def freqMap():
    extfac = 1.05

    # Using phase_vis, dt_anim, and num_frames from the previous animation script
    cycles = np.floor(event_times / (2 * np.pi))

    # Find the indices where the cycle count increases
    trigger_indices = np.where(np.diff(cycles) > 0)[0]

    # Convert those indices into exact timestamps (in seconds)
    trigger_times = trigger_indices

    norm_times = (duration * extfac)

    base_note = 'F2'
    semitone_range = [0, 24]
    ring_frac = 0.001

    # Create cutoff LFO data
    t = np.linspace(0, norm_times[-1], 2000)  # high resolution time array
    orbit_index = np.arange(len(norm_times))

    # interpolate fractional orbit count
    orbit_progress = np.interp(t, norm_times, orbit_index)

    phase = np.pi * orbit_progress
    lfo = np.sin(phase)
    sts.sonify(t, lfo, style="style_train.yml", duration=(duration * (1 + ring_frac)), system="stereo")


# Tempo type 1 mapping
sts.sonify(event_times, sampOnes, style="train.yml", duration=length)

# Code to find turning points and add them to the sonification by volume on off mapping (Pass) but inefficient
secondDiff = np.diff(betweenTimes)
diffLen = len(secondDiff)

localMaxMask = secondDiff < 0
localMinMask = secondDiff > 0
for i in range(diffLen - 1):
    if localMaxMask[i] == localMaxMask[i + 1]:
        localMaxMask[i] = False

    if localMinMask[i] == localMinMask[i + 1]:
        localMinMask[i] = False

localMaxPos = np.zeros(diffLen)
localMinPos = np.zeros(diffLen)

localMaxs = localMaxPos[localMaxMask]
localMins = localMinPos[localMinMask]

numMax = len(localMaxs)
numMin = len(localMins)

localMaxPos[localMaxMask] = np.ones(numMax)
localMinPos[localMinMask] = np.ones(numMin)

offSet = Nsamp - diffLen
for i in range(offSet):
    localMaxPos = np.append(localMaxPos, [0])
    localMinPos = np.append(localMinPos, [0])

sts.sonify(event_times, sampOnes, localMaxPos, style="whistle2.yml", duration=length)
sts.sonify(event_times, sampOnes, localMinPos, style="whistle1.yml", duration=length)
timeKeeper(1)

# sts.save("test13.wav")
sts.close()

# Tempo type 1 mapping with tie keeping (Pass)
sts.sonify(event_times, sampOnes, style="lowClick.yml", duration=length)
timeKeeper(1)
# sts.save("test14.wav")
