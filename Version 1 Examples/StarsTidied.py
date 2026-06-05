import os
from pathlib import Path
import IPython.display as ipd
import matplotlib.pyplot as plt
import numpy as np
from strauss import channels
from strauss.generator import Sampler
from strauss.score import Score
from strauss.sonification import Sonification
from strauss.sources import Events


# ==========================================
# 1. THE SCORE
# ==========================================
# Controls what notes can be played over the course of the sonification.
# Here we specify a single Db6/9 chord voicing.

chordList = [["Db3", "Gb3", "Ab3", "Eb4", "F4"]]
trackLength = "1m 30s"
starScore = Score(chordList, trackLength)


# ==========================================
# 2. THE SOURCES (DATA)
# ==========================================
# Imports the data representing the sky positions, brightness, and color of stars.
# Each row is a star and each column is a property of that star.

dataFile = Path("..", "data", "datasets", "stars_paranal.txt")

# Maps sound properties to specific data file columns
mapColumns = {"azimuth": 1, "polar": 0, "volume": 2, "time": 2, "pitch": 3}

# Functions that manipulate each column's values to yield the linear mapping
mappingFunctions = {
    "azimuth": lambda x: x,
    "polar": lambda x: 90.0 - x,
    "time": lambda x: x,
    "pitch": lambda x: -x,
    "volume": lambda x: (1 + np.argsort(x).astype(float)) ** -0.2,
}

# Limits of each mapping (absolute values for degrees, percentiles for strings)
mappingLimits = {
    "azimuth": (0, 360),
    "polar": (0, 180),
    "time": ("0%", "104%"),
    "pitch": ("0%", "100%"),
    "volume": ("0%", "100%"),
}

starEvents = Events(mapColumns.keys())
starEvents.fromfile(dataFile, mapColumns)
starEvents.apply_mapping_functions(mappingFunctions, mappingLimits)


# ==========================================
# 3. THE GENERATOR
# ==========================================
# Uses a Sampler-type generator that plays an audio sample for each note.

soundSampler = Sampler(Path("..", "data", "samples", "glockenspiels"))
soundSampler.preset_details("default")


# ==========================================
# 4. THE SONIFICATION
# ==========================================
# Consolidates the elements to generate the stereo sound track.

audioSystem = "stereo"

print("Generating 'Stars Appearing' sonification...")
starSonification = Sonification(
    starScore, starEvents, soundSampler, audioSystem
)
starSonification.render()


# ==========================================
# 5. PREVIEW AND EXPORT
# ==========================================
# Visualizes the waveform and plays the preview inside the notebook.

starSonification.hear()

# To save the output to a file, uncomment the line below:
# outputFilepath = Path('..', '..', 'rendered_stars_stereo.wav')
# starSonification.save_combined(outputFilepath, True)