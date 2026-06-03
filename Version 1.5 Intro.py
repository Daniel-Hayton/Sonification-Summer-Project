"""# Styles and High-level Interface

In `strauss` v2 we present an accessible, high-level interface.

To demonstrate this we implement the `style` interface for making sonifications, as well as a new `AudioFigure` wrapper that strauss monitors. This allows us to use a `matplotlib`-style approach to making and combining sonifications.
"""

import strauss
import numpy as np
import matplotlib.pyplot as plt

"""First Generate some artificial data, *`x`*, *`y`* and *`z`*"""

x = np.linspace(0, 90, 400)
y = np.sin(x / 2)
z = 0.1 * x ** 2 - x - 5
plt.xlabel('Parameter #1 (x)')
plt.ylabel('Parameter #2 (y)')
plt.plot(x, y)
plt.show()

"""## Trying some indivdual styles

The new `strauss.sonify()` method will sonify the input arguments based on a 'style' keyword

By default at the moment this is the basic pitch mapping, can try:
- **`'default'`**: Default style continuosly maps pitch against `y` over time `x` using a simple triangle carrier tone and a two-octave range  
- **`'stars_appearing'`**: Style for the flagship *'Stars Appearing'* event-type sonification. `x` is time, `y` is pitch, `z` is volume.
- **`'mallets'`**: Major scale pitch mapping of individuated mallet sounds `y` over time `x`
- **`'windy'`**: Textural mapping of low-pass filter cutoff `y` continuosly with time `x` using a white-noise carrier wave for a wind effect.
- **`'flute_section'`**: Tonal mapping of low-pass filter cutoff `y` continuosly with time `x` using 5 flute voices to articulat a musical chord.

Lets try some out...
"""

windy = strauss.sonify(x, y, style='flute_section')
windy.render()
windy.hear()

"""The strauss figure can then be closed for a fresh sonification."""

strauss.close()

"""The plan for mappings is to have these inputs in priority order, where the first (`x`) is always time, and subsequent arguments are in some 'priority' order. As with `matplotlib`, we can even have a single mapping, which assumes time (the "`x`") is uniformly spaced, and then maps the `y` parameter.

Let's try some other styles, for example the default (either writing `style='default'` or specifying no style at all):
"""

windy = strauss.sonify(x, y, style='default')
strauss.hear()
strauss.close()

"""Or other styles. Some styles pull resources from online, and store these in the cache, for example the `mallets`, which uses a directory of indivdual struck samples, and maps y onto a serious of harmonious notes:"""

windy = strauss.sonify(x, y, style='mallets')
strauss.hear()
strauss.close()

"""...or `flute_section`, which makes use of a _Soundfont_ file (`.sf2` extension), that contains audio samples of flutes. Here we hold a harmonious chord and the cutoff frequency changes the _timbre_ of the sound:"""

windy = strauss.sonify(x, y, style='flute_section')
strauss.hear()
strauss.close()

"""## Combining sonifications

Sonifications can be combined together, and mixed. This is the default behaviour, alloweing you to build complex, multi-element sonifications.

Let's set this up so we use the default and `windy` styles together to represent the sin wave in phase and anti-phase.
"""

strauss.sonify(x, y)
strauss.sonify(x, -y, style='windy')
strauss.hear()
strauss.close()

"""Individual sonifications can be given names, and have volume levels set to allow tweaking of the different elements"""

strauss.sonify(x, y, name='sin(x)', level='-20 db')
strauss.sonify(x, -y, style='windy', name='-sin(x)', level='0 db')
strauss.hear()

"""...and adjusted after the fact"""

strauss.set_level('sin(x)', '0 dB')
strauss.set_level('-sin(x)', '-10 dB')

strauss.hear()
strauss.close()

"""## Fixed Properties

We can also fix properties of our choice. This can be set inside the style file using the `fixed` parameters (more about the style files below), but also using key-word arguments to `strauss.sonify`, using the syntax `fix_<param>` where `param` is one of STRAUSS' mappable parameters - for example to pan sonifications:
"""

strauss.sonify(x, y, name='sin(x)', fix_pan=0.3)
strauss.sonify(x, -y, style='windy', name='-sin(x)', fix_pan=0.7)
strauss.hear()
strauss.close()

"""Fixed values ae generally set using a ***fractional*** value (i.e. between 0 and 1), with the exception of 3D angles, `azimuth` and `polar` which expect values in degrees - from 0° to 360° and 0° to 180°, respectively:"""

soni = strauss.sonify(x, -y, fix_azimuth=90, fix_polar=80)
soni.hear()
strauss.close()

"""## Finishing up my sonification

I can also save my audio figure to a sound file, when I'm happy. Either as a `.wav`, natively:
"""

strauss.sonify(x, y, name='sin(x)', level='-10 db')
strauss.sonify(x, -y, style='windy', name='-sin(x)', level='0 db')
strauss.save('my_sonification.wav')

"""Or using another common extension provided `ffmpeg` is available:"""

strauss.save('my_sonification.mp3')
# strauss.save('my_sonification.aac')
# strauss.save('my_sonification.ogg')

"""## Under the hood

There are a number of under-the-hood changes here going on to make all this work. The styles are managed using a `pydantic` object with rigorous type-checking, following the *[Sonification Suite](https://github.com/gcaselton/sonification-toolkit.git)*.

There is also an asset manager that keeps track of our curated sound assets for built-in styles; like soundfonts, samples, etc. This stores in the user's cache. This is opted for instead of a dedicated directory in home (e.g. `~/.strauss`) as this is harder to make flexible and maintain, however the trade off is that cache is more liable to be cleared, so the asset manager needs to re-download these if that happens. This is all done behind the scenes.

### Writing your own styles

We can provide and modify our own style files. These are in the [YAML format](https://yaml.org/about/). First let's close any open sonifications and inspect the `'flute_section'` style file, reproduced here:
"""

strauss.close()
fs_style = strauss.get_style('flute_section', print_style=True)

"""we can save this as our own style locally:"""

with open('test.yml', 'w') as f:
    f.write(fs_style)
windy = strauss.sonify(x, y, style='test.yml')
windy.hear()
strauss.close()

"""We can try modifying this style, for example the notes (to `['G2', 'D3', 'Bb3', 'F4', 'Bb4']`), for a minor sound:"""

fs_style = """
name: 'Flute Section'

description: ''

generator:
  type: 'sampler'
  sample: 'flute'
  mods:
    filter: "on"
    looping: 'forwardback'
    loop_start: 0.1
    loop_end:  2.1

sources: 'objects'

map:
  - output: 'time_evo'
  - output: 'cutoff'
    output_range: [0.4, 0.95]
  - output: 'pan'
    fixed: 0.25

notes: ['G2', 'D3', 'Bb3', 'F4', 'Bb4']
"""

with open('test.yml', 'w') as f:
    f.write(fs_style)
windy = strauss.sonify(x, y, style='test.yml')
windy.here()
strauss.close()
