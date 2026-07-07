import sys
import strauss as sts
import numpy as np
import pygame as pg
from matplotlib import pyplot as plt
from gtts import gTTS
from time import sleep

# Presets for graphing and initialising modules
plt.style.use("dark_background")
pg.init()

# Initialising sound tools
pg.mixer.init()
speechChannel = pg.mixer.Channel(0)
soniChannel = pg.mixer.Channel(1)

# setting the frequency of the running loop
fps = 60
timer = pg.time.Clock()

# Indexing parameters
dataPoints = 500
lim = 1e-3

# Initialising time variables
playBackSpeed = 1
timeRange = 60
timeInc = (timeRange / dataPoints) * playBackSpeed
timeCounter = 0
soniLength = (dataPoints * timeInc) // 2
soniTimer = 0

# Physical properties presets
m = 1e5  # kg
forceInc = 10000  # N
v = np.zeros(dataPoints)
t = np.zeros(dataPoints)
drivingForces = np.zeros(dataPoints)
breakForces = np.zeros(dataPoints)
netForces = np.zeros(dataPoints)

# Initialising forces
drivingForce = 0
breakForce = 0
friction = 0
netForce = 0

# Storing the constant colours that will be used
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Global boolean variables
internetWasConnected = True
wasPlaying = False
frictionless = False
sonification = True

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


# Simple quadratic friction calculator
def fricCalc(velocity):
    return -np.sign(velocity) * (velocity ** 2) * 80


# Function to update the values in a force array
def rollUpdate(array, curVal):
    array = np.roll(array, -1)
    array[-1] = curVal
    return array


# Generates and plays sonification of data a few seconds after the data was created and displayed on the graph
def delayedSoni(times, velocities, drvforces, brkForces, netForces):
    global frictionless

    soniSample = dataPoints // 2

    velSoni = velocities[-soniSample:]
    tSoni = np.linspace(0, soniLength, soniSample)
    drvSoni = drvforces[-soniSample:]
    brkSoni = brkForces[-soniSample:]
    netSoni = netForces[-soniSample:]
    if not frictionless:
        fricSoni = fricCalc(velocities)
        sts.sonify(times, fricSoni, style="windy", duration=timeRange, system='mono')

    # Saves the sonification and closes STRAUSS
    sts.save("vtSound.wav")
    sts.close()

    # Loads and plays the sonification using pygame sound objects
    vtSoni = pg.mixer.Sound("vtSound.wav")
    soniChannel.play(vtSoni)


# Generates and plays the sound adapted to input
def liveSound(time, v, netForce):
    global wasPlaying
    global vtSoni

    # Calculating the new behaviour based on the new parameters
    projectedTime = np.linspace(time, time + timeRange, dataPoints)
    projectedVel = vtFunc(projectedTime, v[-1], netForce)
    projectedFric = fricCalc(projectedVel)

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

    # Masks to find positive and negative gradient
    localMaxMask = secondDiff < 0
    localMinMask = secondDiff > 0

    # Loop so that only the point where the sign of the gradient changes is selected
    for i in range(diffLen - 1):
        if localMaxMask[i] == localMaxMask[i + 1]:
            localMaxMask[i] = False

        if localMinMask[i] == localMinMask[i + 1]:
            localMinMask[i] = False

    # Assigns a volume for the points where the gradient changes sign
    localMaxPos = np.zeros(diffLen)
    localMinPos = np.zeros(diffLen)

    localMaxs = localMaxPos[localMaxMask]
    localMins = localMinPos[localMinMask]

    numMax = len(localMaxs)
    numMin = len(localMins)

    localMaxPos[localMaxMask] = np.ones(numMax)
    localMinPos[localMinMask] = np.ones(numMin)

    # Pads arrays so they match the length of the original dataset
    offSet = dataPoints - diffLen
    for i in range(offSet):
        localMaxPos = np.append(localMaxPos, [0])
        localMinPos = np.append(localMinPos, [0])

    # Generates the sonification for the local maximums and minimums
    sts.sonify(event_times, np.ones(dataPoints), localMinPos,
               style="whistle1.yml", duration=soniLength)
    sts.sonify(event_times, np.ones(dataPoints), localMaxPos,
               style="whistle2.yml", duration=soniLength)

    # Saves the sonification and closes STRAUSS
    sts.save("vtSound.wav")
    sts.close()

    # Loads and plays the sonification using pygame sound objects
    vtSoni = pg.mixer.Sound("vtSound.wav")
    soniChannel.play(vtSoni)


# A procedure which takes string input and uses gtts to generate and play the string as spoken content
def speak(text):
    global internetWasConnected

    # Generates speech if there is an internet connection or plays an error message
    try:
        # Generates speech using gtts
        speech = gTTS(text=text.lower(), lang="en", slow=False)
        speech.save("currentItem.mp3")

        # Loads and plays speech with pygame mixer
        speech = pg.mixer.Sound("currentItem.mp3")
        internetWasConnected = True

    except:
        if internetWasConnected:
            # Play error message using pygame mixer
            speech = pg.mixer.Sound("noInternet.mp3")
            internetWasConnected = False

    speechChannel.play(speech)
    sleep(speech.get_length())


# Presents all the forces on the right of the figure
def displayForces(forces):
    forceNames = ["Driving Force", "Break Force", "Net Force", "Friction"]

    for i in range(0, len(forces)):
        # Making the force ready for display with directional arrows
        arrow = ""
        if forces[i] > 0:
            arrow = "->"
        elif forces[i] < 0:
            arrow = "<-"

        displayForce = round(forces[i] / 1000, 1)
        forceInfo = forceNames[i] + ": " + str(displayForce) + " kN " + arrow

        # Rendering and displaying the text
        forceText = forceFont.render(forceInfo, True, WHITE)
        textX = (SCREEN.get_width() // 2) - (forceText.get_width() // 4)
        textY = (SCREEN.get_height() // 4) + (i * (forceText.get_height() + 20))
        SCREEN.blit(forceText, (textX, textY))


running = True
while running:

    # Refresh the screen
    timer.tick(fps)
    SCREEN.fill(BLACK)

    # Define the time axis and increment for the loop
    t = rollUpdate(t, timeCounter)

    # Updating the velocity array
    v = np.roll(v, -1)
    v[-1] = vtFunc(timeInc, v[-2], netForce)

    # Implements friction if activated
    if not frictionless:
        friction = fricCalc(v[-1])
    else:
        friction = 0

    # Resolves the forces
    netForce = drivingForce + breakForce + friction

    # Makes sure the break force behaves physically
    if abs(breakForce) > abs(drivingForce):
        if np.sign(v[-2]) != np.sign(v[-1]):
            v[-1] = 0

        if abs(v[-1]) <= lim:
            netForce = 0

    # Updating the arrays which store the forces
    drivingForces = rollUpdate(drivingForces, drivingForce)
    breakForces = rollUpdate(breakForces, breakForce)
    netForces = rollUpdate(netForces, netForce)

    # Regenerates the sound when a the current sonification runs out
    if sonification and soniTimer >= timeRange:
        delayedSoni(t, v, drivingForces, breakForces, netForces)
        soniTimer = 0
    soniTimer += 1 / fps

    # Generating and plotting the figure
    plt.figure()
    plt.plot(t, v, color="white", marker=".", linestyle="none")

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

    # Display the forces acting on the graph
    actingForces = [drivingForce, breakForce, netForce]
    if not frictionless:
        actingForces.append(friction)
    displayForces(actingForces)

    # Checks for and handles events in the event queue
    for event in pg.event.get():
        # Quits the game when the window is closed
        if event.type == pg.QUIT:
            running = False
            pg.quit()
            sys.exit()
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_UP:
                if int(drivingForce) < 2e5:
                    drivingForce += forceInc
            elif event.key == pg.K_DOWN:
                if int(drivingForce) > -2e5:
                    drivingForce -= forceInc
            elif event.key == pg.K_LEFT:
                if abs(breakForce) <= 0:
                    breakForce = 0
                else:
                    breakForce = int(abs(breakForce) - forceInc)
            elif event.key == pg.K_RIGHT:
                breakForce = int(abs(breakForce) + forceInc)
            elif event.key == pg.K_r:
                drivingForce = 0
                breakForce = 0
            elif event.key == pg.K_s:
                message = "Driving force " + str(drivingForce) + " Newtons. Break force " + str(breakForce) \
                          + " Newtons. Net force " + str(netForce) + " Newtons."

                if not frictionless:
                    message = message + "Frictional Force " + str(round(friction, 1)) + "Newtons."

                speak(message)
            elif event.key == pg.K_d:
                speak("Driving force " + str(drivingForce) + " Newtons.")
            elif event.key == pg.K_b:
                speak("Break force " + str(breakForce) + "Newtons.")
            elif event.key == pg.K_n:
                speak("Net force " + str(netForce) + " Newtons.")
            elif event.key == pg.K_v:
                speak("The current velocity is " + str(round(v[-1], 1)) + "metres per second")
            elif event.key == pg.K_f:
                speak("Frictional Force " + str(round(friction, 1)) + "newtons")
            elif event.key == pg.K_TAB:
                frictionless = not frictionless
                if not frictionless:
                    speak("Friction activated")
                else:
                    speak("Friction deactivated")
                    friction = 0
            elif event.key == pg.K_BACKSPACE:
                drivingForce = - drivingForce
            elif event.key == pg.K_SPACE:
                sonification = not sonification
                if sonification:
                    speak("Sonification activated")
                else:
                    speak("Sonification deactivated")
                    pg.mixer.stop()
            elif event.key == pg.K_q:
                running = False
                pg.quit()
                sys.exit()

            # Ensures opposition to the direction of motion
            if drivingForce != 0:
                breakForce = int(-np.sign(drivingForce) * abs(breakForce))
            elif v[-1] != 0:
                breakForce = int(-np.sign(v[-1]) * abs(breakForce))

    # Update screen and increment counter
    pg.display.update()
    timeCounter += timeInc
