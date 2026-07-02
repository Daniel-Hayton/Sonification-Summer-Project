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
channel = pg.mixer.Channel(1)
vtSoni = pg.mixer.Sound("vtSound.wav")

# setting the frequency of the running loop
fps = 60
timer = pg.time.Clock()

# Indexing parameters
dataPoints = 500
indexCounter = 0
lim = 1e-3

# Initialising time variables
playBackSpeed = 1
timeRange = 60 * playBackSpeed
timeCounter = 0
timeInc = playBackSpeed * (timeRange / dataPoints)
soniLength = 60 / playBackSpeed

# Physical properties presets
m = 1e5  # kg
forceInc = 10000  # N
v = np.zeros(dataPoints)

# Initialising forces
drivingForce = 0
breakForce = 0
netForce = 0

# Storing the constant colours that will be used
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Global boolean variables
internetWasConnected = True
wasPlaying = False

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
    global wasPlaying
    global vtSoni

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

    # Loads and plays the sonification using pygame sound objects
    vtSoni = pg.mixer.Sound("vtSound.wav")
    channel.play(vtSoni, loops=-1)  # Loops sound continuously
    wasPlaying = True


# A procedure which takes string input and uses gtts to generate and play the string as spoken content
def speak(text):
    global internetWasConnected
    global wasPlaying
    global vtSoni

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

    channel.play(speech)

    # Restarts the sonification after the speech if it was on
    if wasPlaying:
        sleep(speech.get_length())
        channel.play(vtSoni, loops=-1)  # Loops sound continuously


# Presents all the forces on the right of the figure
def displayForces(forces):
    forceNames = ["Driving Force", "Break Force", "Net Force"]

    for i in range(0, len(forces)):
        # Making the force ready for display with directional arrows
        arrow = ""
        if forces[i] > 0:
            arrow = "->"
        elif forces[i] < 0:
            arrow = "<-"

        displayForce = int(forces[i] / 1000)
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

    if indexCounter < dataPoints:
        v[indexCounter] = vtFunc(timeInc, v[indexCounter - 1], netForce)
        indexCounter += 1
        t = np.linspace(0, timeInc * dataPoints, dataPoints)
    else:
        v = np.roll(v, -1)
        v[-1] = vtFunc(timeInc, v[-2], netForce)
        t = np.linspace(timeCounter, timeCounter + timeRange, dataPoints)

    # Used to check old net force against this loops net force
    newNet = drivingForce + breakForce

    # Makes sure the break force behaves physically
    if abs(breakForce) > abs(drivingForce):
        if np.sign(v[-2]) != np.sign(v[-1]):
            v[-1] = 0

        if abs(v[-1]) <= lim:
            newNet = 0

    # Regenerates the sound when a the net force changes
    if newNet != netForce:
        netForce = newNet
        if netForce != 0:
            liveSound(timeCounter, v, netForce)

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
    displayForces([drivingForce, breakForce, netForce])

    # Checks for and handles events in the event queue
    for event in pg.event.get():
        # Quits the game when the window is closed
        if event.type == pg.QUIT:
            running = False
            pg.quit()
            sys.exit()
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_UP:
                drivingForce += forceInc
            elif event.key == pg.K_DOWN:
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
                speak(message)
            elif event.key == pg.K_d:
                speak("Driving force " + str(drivingForce) + " Newtons.")
            elif event.key == pg.K_b:
                speak("Break force " + str(breakForce) + "Newtons.")
            elif event.key == pg.K_n:
                speak("Net force " + str(netForce) + " Newtons.")
            elif event.key == pg.K_v:
                speak("The current velocity is " + str(round(v[-1], 1)) + "metres per second")
            elif event.key == pg.K_q:
                running = False
                pg.quit()
                sys.exit()

            # Ensures opposition to the direction of motion
            if drivingForce != 0:
                breakForce = int(abs(breakForce) * -(drivingForce / abs(drivingForce)))
            elif v[-1] != 0:
                breakForce = int(abs(breakForce) * -(v[-1] / abs(v[-1])))

    # Update screen and increment counter
    pg.display.update()
    timeCounter += timeInc
