from pathlib import Path
from strauss.generator import Sampler
from strauss.sonification import Sonification

# ==================================================================
# Soundfont Configuration
# ==================================================================

soundfontDir = Path("..", "data", "samples", "soundfonts")

# Use filenames that clearly match their contents
fluteSoundfont = soundfontDir / "ExpressiveFluteSSO.sf2"
guitarSoundfont = soundfontDir / "GuitarsUniversal.sf2"

# Select desired guitar preset
guitarPreset = 49


def createFluteSampler():
    """Create a fresh flute sampler."""
    return Sampler(fluteSoundfont)


def createGuitarSampler():
    """Create a fresh guitar sampler."""
    return Sampler(
        guitarSoundfont,
        sf_preset=guitarPreset
    )


# ==================================================================
# First Sonification: Event-Based Notes
# ==================================================================

generator = createGuitarSampler()

generator.modify_preset({
    "note_length": 0.03,
    "volume_envelope": {
        "use": "on",
        "A": 0.01,
        "D": 0.0,
        "S": 1.0,
        "R": 0.07
    }
})

# Continue with your Events source setup:

soni = Sonification(score, sources, generator, system)
soni.render()
soni.hear()


# ==================================================================
# Second Sonification: Object-Based Evolution
# ==================================================================

generator = createFluteSampler()

generator.modify_preset({
    "filter": "on"
})

generator.modify_preset({
    "looping": "forwardback",
    "loop_start": 0.2,
    "loop_end": 0.5
})

# Continue with your Objects source setup:

soni = Sonification(score, sources, generator, system)
soni.render()
soni.hear()
