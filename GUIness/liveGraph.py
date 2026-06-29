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
timeRange = 60
timeCounter = 0
indexCounter = 0
A = 5
dataPoints = 100
v = np.zeros(dataPoints)

# Calculates how long a sonification will be
soniLength = 30

# Setting up the screen with its constant background name and size and hides the mouse
info = pg.display.Info()
SCREEN = pg.display.set_mode((info.current_w, info.current_h))  # Fills the entire screen
pg.display.set_caption("vt-Graph")
pg.mouse.set_visible(False)


# Function that holds the physical relation between the forces, time and velocity
def vtFunc(time, A):
    return A * np.sin(time)


# Generates and plays the sound adapted to input
def liveSound(A, time):

    # Calculating the new behaviour based on the new parameters
    projectedTime = np.linspace(time, time + timeRange, dataPoints)
    projectedVel = vtFunc(A, projectedTime)

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

    # Mask to find positve and negative gradient
    localMaxMask = secondDiff < 0

    # Loop so that only the point where the sign of the gradient changes is selected
    for i in range(diffLen):
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
    sts.sonify(event_times, np.ones(dataPoints), localMaxPos, style="railway.yml", duration=soniLength)

    # Saves the sonification and closes STRAUSS
    sts.save("vtSound.wav")
    sts.close()

    # Loads and plays the sonification using the pygame mixer
    pg.mixer.music.load("vtSound.wav")
    pg.mixer.music.play()

running = True
while running:
    timer.tick(fps)

    if indexCounter < dataPoints:
        v[indexCounter] = vtFunc(timeCounter, A)
        indexCounter += 1
        t = np.linspace(timeCounter, timeCounter + timeRange, dataPoints)
    else:
        v = np.roll(v, -1)
        v[-1] = vtFunc(timeCounter, A)
        t = np.linspace(timeCounter - timeRange, timeCounter, dataPoints)


    # Generating and saving the figure
    plt.figure()
    plt.plot(t, v, color="white", marker=".")
    plt.xlabel("time, t (s)")
    plt.ylabel("velocity, v (m/s)")
    plt.grid(color='grey')
    plt.savefig("vtFig.png")
    plt.close()

    # Loading and displaying the graph
    fig = pg.image.load("./vtFig.png")
    figPos = (0, 0)
    SCREEN.blit(fig, figPos)

    # Checks for and handles events in the event queue
    for event in pg.event.get():
        # Quits the game when the window is closed
        if event.type == pg.QUIT:
            running = False
            pg.quit()
            sys.exit()
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_UP:
                A += 1
            elif event.key == pg.K_DOWN:
                A -= 1

            # Regenerates the sound when a key is pressed
            liveSound(A, timeCounter)

    # Update screen and increment counter
    pg.display.update()
    timeCounter += 1 / 15

