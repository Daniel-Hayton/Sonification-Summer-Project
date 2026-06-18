import strauss
from strauss.sonification import Sonification
from strauss.sources import Events, Objects
from strauss.score import Score
from strauss.generator import Sampler, Synthesizer
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
plt.show()

duration = 30
Nsamp = duration * 5  # Number of discrete events (clicks/notes) to generate

# Ticker works by sampling the growth of the integral
# of the input function by even increments

# first get the simple integral by just using a cumulative sum
ycum = np.cumsum(y)
ycum /= ycum.max()

# now set up the uniform increments
incs = np.linspace(0, 1, Nsamp + 1)
incs = incs[:-1] + np.diff(incs) * 0.5

# now interpolate for the times between (0,1) for each of the N_samp ticks
event_times = np.interp(incs, ycum, x)

# Setup Score and Generator
score = Score([['A4']], duration)
synth = Synthesizer()
synth.load_preset('pitch_mapper')
# Fast attack/decay for "click-like" sounds
synth.modify_preset({'note_length': 0.15,
                     'oscillators': {'osc1': {'form': 'sine'}},
                     'volume_envelope': {'use': 'on', 'A': 0.001, 'D': 0.1, 'S': 0., 'R': 0.05}})

# 3. Map parameters
maps = {
    'time': event_times,
    'pitch': np.ones(Nsamp),  # Randomize pitch slightly,
}

lims = {'time': ('0%', 1)}

sources = Events(maps.keys())
sources.fromdict(maps)
sources.apply_mapping_functions(map_lims=lims)

# 4. Render and Save
soni_bhar = Sonification(score, sources, synth, 'stereo')
soni_bhar.render()
# soni_bhar.save('method1_bhar_ticks.wav', master_volume=0.5)
soni_bhar.hear()

soni1p5 = strauss.sonify(event_times, np.ones(Nsamp), style='clickStyle.yml', duration=30)
soni1p5.render()
soni1p5.hear()
strauss.close()

strauss.sonify(event_times, np.ones(Nsamp), style="clickStyle.yml", duration=30)
strauss.sonify(event_times, np.ones(Nsamp), style="highClick.yml", duration=30)
strauss.save("simultaneousClicks.wav")
strauss.close()

strauss.sonify(event_times, np.ones(Nsamp), style="clickStyle.yml", duration=30)
strauss.sonify(event_times + (0.15/2), np.ones(Nsamp), style="highClick.yml", duration=30)
strauss.save("sequentialClicks.wav")
strauss.close()
