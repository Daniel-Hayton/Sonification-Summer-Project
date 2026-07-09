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

# Populates the notes array for note selection later
keys = ["A", "B", "C", "D", "E", "F", "G"]
notes = []
for i in range(len(keys)):
    for j in range(5):
        notes.append(keys[j] + str(i + 1))

# Define strings that will be used in input statements
styleString = "In which way would you like to hear the graph" \
              "\n1\tBased on a synthesizer\n2\tBased on a song\nEnter 1 or 2\n-> "
idString = "Do you want the components identified by a\n1\tNote range\n2\tSpacial audio\n3\tBoth\n4\tNone\n\t-> "


# Define the governing equation for each component
def resistor(V, R):
    I = V / R
    return I, np.zeros(dataPoints)


def lamp(V, R_0):
    tempCoeff = 0.08  # Bend rate
    n = 1.5  # Bend shape
    T_0 = 293  # Room temperature

    # Calculates the current profile
    I = V / (R_0 * (1 + tempCoeff * np.abs(V) ** n))
    I_max = np.argmax(I)
    I_min = np.argmin(I)
    I[I_max:] = np.max(I) + (1e-4 * V[I_max:])
    I[:I_min] = np.min(I) + (1e-4 * V[:I_min])

    # Calculates the resistance and uses this to find the temp
    R_T = V[1:] / I[1:]
    R_T = np.insert(R_T, 0, R_0)
    T = T_0 + ((R_T / R_0) - 1) / tempCoeff
    return I, T


def diode(V):
    # Realistic Shockley Diode approximation
    Is = 1e-9  # Saturation current
    I = Is * (np.exp(26 * V) - 1)

    # Keep reverse current at 0 for standard visualization
    I[V < 0] = 0

    # Have the base line just above zero so it is visible
    I += 1e-3
    return I, np.zeros(dataPoints)


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
    try:

        componentNo = input("How many components would you like to hear at once? ")

        # Terminates code
        if componentNo == "quit":
            break
        else:
            componentNo = int(componentNo)
            audioSep = 1 / (componentNo + 1)  # Gives the separation of the sonifications

        # Generating the figure
        plt.figure()

        # Define the voltage range
        maxV = float(input("How high do you want the voltage to go? "))
        minV = float(input("How low would you like the voltage to start from? "))

        # Initialising the current range
        maxI = 0
        minI = 0

        dataPoints = 1000
        voltage = np.linspace(minV, maxV, dataPoints)
        diodeVolts = np.linspace(minV, 1, dataPoints)  # Reduced range for diode
        diodeing = False

        # Resetting output parameters
        current = np.zeros(dataPoints)
        temperature = np.zeros(dataPoints)
        resistance = 0

        # User chooses the identifier style for the sonification if there is more than 1 item
        notable = False
        spacial = False
        if componentNo > 1:
            idStyle = int(input(idString))
            if idStyle == 1:
                notable = True
            elif idStyle == 2:
                spacial = True
            elif idStyle == 3:
                notable = True
                spacial = True

        for i in range(componentNo):
            # Calculates audio position for the sonification
            if spacial:
                audioPos = audioSep * (i + 1)
            else:
                audioPos = 0.5

            # Validating input
            accepted = False
            component = ""
            while not accepted:
                accepted = True
                component = input("Which component would you like to have as component #" + str(i + 1) + " ? ")

                if component.lower() == "diode" and (i + 1) != componentNo:
                    print("Sorry, you can only have a diode as your last component")
                    accepted = False

            # Calculating current from set up parameters
            match component.lower():
                case "resistor":
                    resistance = float(input("How many Ohms (Ω) of resistance do you want? "))

                    current, temperature = resistor(voltage, resistance)
                    component = str(resistance) + "Ω " + component
                    minI, maxI = extremeFinder(current, minI, maxI)
                case "lamp":
                    resistance = float(input("How many Ohms (Ω) of cold resistance do you want? "))

                    current, temperature = lamp(voltage, resistance)
                    component = str(resistance) + "Ω " + component
                    minI, maxI = extremeFinder(current, minI, maxI)
                case "diode":
                    diodeing = True
                    voltage = diodeVolts
                    current, temperature = diode(voltage)

            # Calculates the inverse of the gradient to get resistance at each point
            varRes = voltage[1:] / current[1:]
            varRes = np.insert(varRes, 0, 0)  # Prevents divide by zero error and makes it correct length
            if maxI != 0:
                varRes[current > maxI] = 0  # Stops sonification if it goes out of bounds
                maxR = np.max(varRes)
            else:
                # Gives sensible range for case
                maxV = 1
                maxR = 1

            # User chooses the style they would like to use
            styleNo = int(input(styleString))

            if styleNo == 1:
                soundStyle = "sparky.yml"

                # Calculates the separation between the notes that will be played and the notes for this component
                noteSep = len(notes) // (componentNo + 1)

                # Finds the position of the current and next note
                notePos = noteSep * (i + 1)
                nextNotePos = noteSep * (i + 2)

                # Finds the starting note and finish note
                soniNote = notes[notePos]
                nextNote = notes[nextNotePos]

                if not notable:
                    soniNote = "A1"
                    nextNote = "C4"

                updateStyle = f"""name: 'sparky'
    
description: ''

sources: 'objects'

generator:
  type: 'synthesizer'
  preset: 'default'
  mods:
  
    pitch_lfo:
      use: on
      wave: 'saw'
      amount: 0.5
      freq: 50
      phase: 'random'
      
    volume_lfo:
      use: on
      wave: 'square'
      amount: 1
      freq: 4
    
map:
  - output: 'time_evo'
    input_range: [{minV}, {maxV}]
  - output: 'pitch_shift'
  - output: 'volume_lfo/freq_shift'
  - output: 'volume'
    input_range: [0, {maxR}]

notes: ['{soniNote}', '{nextNote}']
"""

            else:
                soundStyle = "electricSong.yml"
                updateStyle = f"""name: 'electricSong'

description: ''

sources: 'objects'

generator:

  type: 'sampler'
  sample: './Songification'

map:
  - output: 'time_evo'
    input_range: [ {minV}, {maxV} ]
  - output: 'pitch_shift'
  - output: 'volume_lfo/freq_shift'
  - output: 'volume'
    input_range: [ 0, {maxR} ]
  

notes: ['E3']
"""

            # Update the external style file
            with open(soundStyle, 'w') as f:
                f.write(updateStyle)

            # Visual and audio generation of the line of the graph for this component
            plt.plot(voltage, current, label=component)
            sts.sonify(voltage, abs(current), abs(temperature), abs(varRes),
                       duration=30,
                       system="mono",
                       style=soundStyle,
                       fix_pan=audioPos)

        # Saves the sonification for display
        sts.save("electrifying.wav")

        # Loads and plays the sonification using pygame sound objects
        ivSoni = mx.Sound("electrifying.wav")
        ivSoni.set_volume(0.2)
        soniChannel.play(ivSoni)

        # Fixes the parameters for display if graph includes a diode
        if diodeing and maxI > 0:
            maxI *= 1.2
            if minI < 0:
                minI *= 1.2
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

    except ValueError:
        print("Oh no, sorry. Something went wrong try again.")

print("Thanks for listening")
