import sys
import strauss as sts
import numpy as np
import pygame as pg
from matplotlib import pyplot as plt

# Presets for graphing and initialising modules
plt.style.use("dark_background")
pg.init()

# setting the frequency of the running loop
fps = 60
timer = pg.time.Clock()

# Initialising variables needed for plotting
timeRange = 120
timeCounter = 0
timeInc = 1 / fps
indexCounter = 0
m = 1e5  # kg
dataPoints = 100
v = np.zeros(dataPoints)

# Initialising forces
drivingForce = 0
resistiveForce = 0
netForce = 0
regionSign = 1

# Storing the constant colours that will be used
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Sonification parameters
soniLength = 60


def displayForces(forces):
    forceNames = ["Driving Force", "Resistive Force", "Net Force"]

    for i in range(0, len(forces)):
        # Making the force ready for display with directional arrows
        arrow = ""
        if forces[i] > 0:
            arrow = "->"
        elif forces[i] < 0:
            arrow = "<-"

        forceInfo = forceNames[i] + ": " + str(forces[i]) + "N " + arrow

        # Rendering and displaying the text
        forceText = forceFont.render(forceInfo, True, WHITE)
        textX = (SCREEN.get_width() // 2) - (forceText.get_width() // 4)
        textY = (SCREEN.get_height() // 4) + i * 60
        SCREEN.blit(forceText, (textX, textY))


# Initialise fonts for display
forceFont = pg.font.Font(None, 70)

# Setting up the screen with its constant background name and size and hides the mouse
info = pg.display.Info()
SCREEN = pg.display.set_mode((info.current_w, info.current_h))  # Fills the entire screen
pg.display.set_caption("vt-Graph")
pg.mouse.set_visible(False)


# Function that holds the physical relation between the forces, time and velocity
def vtFunc(t, u, F):
    a = F / m
    return a * t + u


# Generates and plays the sound adapted to input
def liveSound(time, v, netForce):
    # Calculating the new behaviour based on the new parameters
    projectedTime = np.linspace(time, time + timeRange, dataPoints)
    projectedVel = vtFunc(projectedTime, v[-1], netForce)

    # first get the simple integral by just using a cumulative sum
    displacement = np.cumsum(projectedVel)
    displacement /= displacement.max()

    # now set up the uniform increments
    incs = np.linspace(0, 1, dataPoints + 1)
    incs = incs[:-1] + np.diff(incs) * 0.5

    # now interpolate for the times between (0,1) for each of the N_samp ticks
    event_times = np.interp(incs, displacement, projectedTime)

    # Generates sonification for the background
    sts.sonify(event_times, np.ones(dataPoints), style="train.yml", duration=soniLength)

    # Calculates the second difference of the time intervals
    secondDiff = np.diff(np.diff(projectedTime))
    diffLen = len(secondDiff)

    # Mask to find positive and negative gradient
    localMaxMask = secondDiff < 0

    # Loop so that only the point where the sign of the gradient changes is selected
    for i in range(diffLen - 1):
        if localMaxMask[i] and localMaxMask[i + 1]:
            localMaxMask[i] = False

    # Assigns a volume for the point of the change of sign the gradient
    localMaxPos = np.zeros(diffLen)
    localMaxs = localMaxPos[localMaxMask]
    numMax = len(localMaxs)
    localMaxPos[localMaxMask] = np.ones(numMax)

    offSet = dataPoints - diffLen
    for i in range(offSet):
        localMaxPos = np.append(localMaxPos, [0])

    # Generates the sonification for the local maximums
    # sts.sonify(event_times, np.ones(dataPoints), localMaxPos, style="railway.yml", duration=soniLength)

    # Saves the sonification and closes STRAUSS
    sts.save("vtSound.wav")
    sts.close()

    # Loads and plays the sonification using the pygame mixer
    pg.mixer.music.load("vtSound.wav")
    pg.mixer.music.play(-1)  # Loops sound continuously


running = True
while running:

    # Refresh the screen
    timer.tick(fps)
    SCREEN.fill(BLACK)

    if indexCounter < dataPoints:
        v[indexCounter] = vtFunc(timeInc, v[indexCounter - 1], netForce)
        indexCounter += 1
        t = np.linspace(timeCounter, timeCounter + timeRange, dataPoints)
    else:
        v = np.roll(v, -1)
        v[-1] = vtFunc(timeInc, v[-2], netForce)
        t = np.linspace(timeCounter - timeRange, timeCounter, dataPoints)

    # Makes sure the resistive force behaves physically
    if abs(resistiveForce) > abs(drivingForce) and v[-2] <= 0:
        v[-1] = 0

    # Generating and plotting the figure
    plt.figure()
    plt.plot(t, v, color="white", marker=".")

    # Determine the range of y based on sign of values
    if np.min(v) < 0 < np.max(v):
        plt.ylim(-50, 50)
    elif np.min(v) < 0:
        plt.ylim(-50, 0)
    else:
        plt.ylim(0, 50)

    # Adding Labels to the figure
    plt.xlabel("time, t (s)")
    plt.ylabel("velocity, v (m/s)")
    plt.grid(color='grey')

    # Save the figure to be displayed and close pyplot for next loop
    plt.savefig("vtFig.png")
    plt.close()

    # Loading and displaying the graph
    fig = pg.image.load("./vtFig.png")
    figPos = (0, 0)
    SCREEN.blit(fig, figPos)

    # Determining the current region the graph is in
    if v[-1] >= 0:
        regionSign = 1
    elif v[-1] < 0:
        regionSign = -1

    # Checks for and handles events in the event queue
    for event in pg.event.get():
        # Quits the game when the window is closed
        if event.type == pg.QUIT:
            running = False
            pg.quit()
            sys.exit()
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_UP:
                drivingForce += 10
            elif event.key == pg.K_DOWN:
                drivingForce -= 10
            elif event.key == pg.K_LEFT:
                if (regionSign * resistiveForce) > 0:
                    resistiveForce = 0
                else:
                    resistiveForce += 10
            elif event.key == pg.K_RIGHT:
                resistiveForce -= 10
            elif event.key == pg.K_r:
                drivingForce = 0
                resistiveForce = 0

            # Used to check old net force against this loops net force
            newNet = drivingForce + resistiveForce

            # Regenerates the sound when a the net force changes
            if newNet != netForce:
                netForce = newNet
                if drivingForce != 0 and resistiveForce != 0:
                    liveSound(timeCounter, v, netForce)

    # Display the forces acting on the graph
    displayForces([drivingForce, resistiveForce, netForce])

    # Update screen and increment counter
    pg.display.update()
    timeCounter += timeInc
