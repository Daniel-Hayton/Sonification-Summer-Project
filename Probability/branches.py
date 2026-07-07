import strauss as sts
from pygame.time import wait
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

probject = input("Do you want to listen to the probability branches of a fair\n1\tDice\n2\tCoin\n\t-> ")

if probject == "1":
    initOutcomes = int(input("How many sides do you want your dice to have? "))
else:
    print("Coin it is.")
    initOutcomes = 2

for i in range(len(notes)):
    fig = sts.AudioFigure(system='stereo')
    curOutcomes = initOutcomes ** i
    if curOutcomes > len(notes) and (initOutcomes ** (i - 1)) > len(notes):
        print("Too many outcomes to output")
        break
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

        fig.sonify(x, y, fix_pan=audioCoordinates, style="prob.yml", duration=soniLength)

    fig.save("prob.wav")
    fig.render()
    sts.close()
    probSoni = mx.Sound("prob.wav")
    while mx.get_busy():
        wait(100)
    probSoni.set_volume(0.2)
    soniChannel.play(probSoni)

