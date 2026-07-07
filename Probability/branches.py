import strauss as sts
from time import sleep
import numpy as np
from pygame import mixer as mx

mx.init()
soniChannel = mx.Channel(1)

keys = ["A", "B", "C", "D", "E", "F", "G"]
notes = []
for i in range(len(keys)):
    for j in range(len(keys)):
        notes.append(keys[j] + str(i + 1))

soniLength = 5

x = np.linspace(0, 5, 10)
y = np.ones(10)

initOutcomes = 2
for i in range(len(keys)):
    fig = sts.AudioFigure(system='stereo', length=soniLength)
    curOutcomes = initOutcomes ** i
    audioSep = 1 / (curOutcomes + 1)
    noteSep = len(notes) // (curOutcomes + 1)
    for j in range(curOutcomes):
        audioCoordinates = audioSep * (j + 1)
        notePos = noteSep * (j + 1)
        soniNote = notes[notePos]

        probStyle = f"""name: 'prob'

description: ''

sources: 'objects'

generator:
  type: 'synthesizer'
  preset: 'pitch_mapper'

map:
  - output: 'time_evo'
  - output: 'pitch_shift'

notes: ['{soniNote}']"""
        with open('prob.yml', 'w') as f:
            f.write(probStyle)

        sts.sonify(x, y, fix_pan=audioCoordinates, style="prob.yml")

    sts.save("prob.wav")
    sts.close()
    probSoni = mx.Sound("prob.wav")
    soniChannel.play(probSoni)
    sleep(soniLength)
