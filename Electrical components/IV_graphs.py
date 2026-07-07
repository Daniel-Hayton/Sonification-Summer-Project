import strauss as sts
import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt
from pygame import mixer as mx

# Set up parameters for figure plotting
mpl.use("tkagg", force=True)
plt.style.use("dark_background")

# Initialising sound tools
mx.init()
soniChannel = mx.Channel(1)

keys = ["A", "B", "C", "D", "E", "F", "G"]
notes = []
for i in range(len(keys)):
    for j in range(5):
        notes.append(keys[j] + str(i + 1))


# Define the governing equation for each component
def resistor(V, R):
    return V / R


def lamp(V, R):
    alpha = 0.08  # Bend rate
    n = 1.5  # Bend shape

    return V \
        / (R * (1 + alpha * np.abs(V) ** n))


def diode(V):
    # Realistic Shockley Diode approximation
    Is = 1e-9  # Saturation current
    I = Is * (np.exp(26 * V) - 1)

    # Keep reverse current at 0 for standard visualization
    I[V < 0] = 0

    I += 1e-3
    return I


# Finds the minimum and maximum values for current across all curves
def extremeFinder(data, lastMin, lastMax):
    # Finds current min and max
    curMin = np.min(data)
    curMax = np.max(data)

    # Compares to previous min and max
    if curMin < lastMin:
        newMin = curMin
    else:
        newMin = lastMin

    if curMax > lastMax:
        newMax = curMax
    else:
        newMax = lastMax

    return newMin, newMax


# Repeated loop until user wants to stop program
while True:
    # try:

    componentNo = input("How many components would you like to hear at once? ")
    # Terminates code
    if componentNo == "quit":
        break
    else:
        componentNo = int(componentNo)

    # Generating the figure
    plt.figure()

    # Define the voltage range
    maxV = float(input("How high do you want the voltage to go? "))
    minV = float(input("How low would you like the voltage to start from? "))
    maxI = 0
    minI = 0

    dataPoints = 1000
    voltage = np.linspace(minV, maxV, dataPoints)
    ogVoltage = voltage  # TTo be used as temporary storage for diode case
    diodeVolts = np.linspace(minV, 1, dataPoints)
    diodeing = False

    for i in range(componentNo):

        # Validating input
        accepted = False
        component = ""
        while not accepted:
            accepted = True
            component = input("Which component would you like to have as component #" + str(i + 1) + " ? ").lower()
            if component == "diode" and (i + 1) != componentNo:
                print("Sorry, you can only have a diode as your last component")
                accepted = False

        # Set up for volume manipulation
        maskPoints = int(dataPoints * 0.2)
        varRes = np.ones(dataPoints)

        # Calculating current from set up parameters
        match component:
            case "resistor":
                resistance = float(input("How many Ohms (Ω) of resistance do you want? "))
                current = resistor(voltage, resistance)
                component = str(resistance) + "Ω " + component
                minI, maxI = extremeFinder(current, minI, maxI)
            case "lamp":
                resistance = float(input("How many Ohms (Ω) of cold resistance do you want? "))
                current = lamp(voltage, resistance)
                component = str(resistance) + "Ω " + component
                minI, maxI = extremeFinder(current, minI, maxI)
            case "diode":
                diodeing = True
                ogVoltage = voltage
                voltage = diodeVolts
                current = diode(voltage)

        # User chooses the style they would like to use
        styleNo = int(input("In which way would you like to hear the graph"
                            "\n1\tBased on a synthesizer\n2\tBased on a song\nEnter 1 or 2\n-> "))

        if styleNo == 1:
            # Calculates the separation between the notes that will be played and the notes for this component
            noteSep = len(notes) // (componentNo + 1)
            notePos = noteSep * (i + 1)
            soniNote = notes[notePos]
            print(soniNote)
            sparkyStyle = f"""name: 'sparky'

description: 'Electrical crackle'

sources: 'objects'

generator:
  type: 'synthesizer'
  preset: 'default'
  mods:

    filter: 'on'
    filter_type: 'HPF1'
    cutoff: 0.2

    oscillators:

      osc1:
        form: 'square'
        level: 0.4

      osc2:
        form: 'noise'
        level: 0.8
     
      osc3:
        form: "square"
        level: 0.25
        detune: 0.5

    pitch_lfo:
      use: 'on'
      wave: 'noise'
      amount: 0.15
      freq: 15
      level: 1

    volume_lfo:
      use: 'on'
      wave: 'noise'
      amount: 1.0
      freq: 30
      level: 1

map:
  - output: 'time_evo'
    input_range: [{minV}, {maxV}]
  - output: 'pitch_shift'
  - output: 'volume'

notes: ['{soniNote}']"""
            with open('sparky.yml', 'w') as f:
                f.write(sparkyStyle)

            soundStyle = "sparky"

            # highResMask = current >= current[np.argsort(current)][-maskPoints]
            # varRes[highResMask] = np.arange(0, maskPoints) % 2

        elif styleNo == 2:
            soundStyle = "electricSong"
            # varRes = current
        else:
            soundStyle = "pump"
            highResMask = current < current[np.argsort(current)][-maskPoints]
            varRes[highResMask] = np.arange(0, dataPoints - maskPoints) % 2

        # Visual and audio generation of the line of the graph for this component
        plt.plot(voltage, current, label=component)
        if diodeing:  # Plot and sonification needs to be handled differently for diodes
            voltage = ogVoltage
            current = diode(voltage)
            current[current > maxI] = 0
        sts.sonify(voltage, current, current,
                   duration=20,
                   system="mono",
                   style=soundStyle + ".yml")

    # Saves the sonification for display
    sts.save("electrifying.wav")

    # Loads and plays the sonification using pygame sound objects
    ivSoni = mx.Sound("electrifying.wav")
    soniChannel.play(ivSoni)

    # Fixes the parameters for display if graph includes a diode
    if diodeing and maxI > 0:
        maxI *= 1.2
        plt.ylim(minI, maxI)

    # Styling the graph
    plt.title("IV graph")
    plt.legend()
    plt.xlabel("Potential Difference, V (V)")
    plt.ylabel("Current, I (A)")
    plt.grid(color="grey")
    plt.show()

    # Close for next loop
    sts.close()
    plt.close()
    # except ValueError:
        # print("Oh no, sorry. Something went wrong try again.")

print("Thanks for listening")
