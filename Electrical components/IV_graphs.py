import strauss as sts
import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt

# Set up parameters for figure plotting
mpl.use("tkagg", force=True)
plt.style.use("dark_background")


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
    return I


# Repeated loop until user wants to stop program
while True:
    try:

        component = input("Which component would you like to hear? ").lower()

        # Terminates code
        if component == "quit":
            break

        # Define the voltage range
        maxV = float(input("How high do you want the voltage to go? "))
        minV = float(input("How low would you like the voltage to start from? "))

        dataPoints = 1000
        voltage = np.linspace(minV, maxV, dataPoints)

        # Set up for volume manipulation
        maskPoints = int(dataPoints * 0.2)
        varRes = np.ones(dataPoints)

        # Calculating current from set up parameters
        match component:
            case "resistor":
                resistance = float(input("How many Ohms (Ω) of resistance do you want? "))
                current = resistor(voltage, resistance)
            case "lamp":
                resistance = float(input("How many Ohms (Ω) of cold resistance do you want? "))
                current = lamp(voltage, resistance)

            case "diode":
                current = diode(voltage)

        # User chooses the style they would like to use
        styleNo = int(input("In which way would you like to hear the graph"
                            "\n1\tBased on a synthesizer\n2\tBased on a song\nEnter 1 or 2\n-> "))

        if styleNo == 1:
            soundStyle = "sparky"

            highResMask = current >= current[np.argsort(current)][-maskPoints]
            varRes[highResMask] = np.arange(0, maskPoints) % 2
        elif styleNo == 2:
            soundStyle = "electricSong"
            varRes = current
        else:
            soundStyle = "pump"
            highResMask = current < current[np.argsort(current)][-maskPoints]
            varRes[highResMask] = np.arange(0, dataPoints - maskPoints) % 2


        # Generating the figure
        plt.figure()
        plt.plot(voltage, current)

        # Styling the graph
        plt.title("IV graph for a " + component)
        plt.xlabel("Potential Difference, V (V)")
        plt.ylabel("Current, I (A)")
        plt.grid(color="grey")
        plt.show()

        # Sonification of the graph
        soni = sts.sonify(voltage, current, varRes,
                          duration=20,
                          system="mono",
                          style=soundStyle + ".yml")
        soni.render()
        soni.hear()

        # Close for next loop
        sts.close()
        plt.close()
    except ValueError:
        print("Oh no, sorry. Something went wrong try again.")

print("Thanks for listening")
