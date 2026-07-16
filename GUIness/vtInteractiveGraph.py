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

# Setting the frequency of the running loop
fps = 10
timer = pg.time.Clock()

# Indexing parameters
playBack = 6
dataPoints = int((playBack * 10 * fps) / 6)  # Multiple of 60 ensuring integer divisions with frames per second
lim = 1e-3

# Initialising time variables
timeRange = 60
timeInc = timeRange / dataPoints
timeCounter = 0

# Sonification parameters
soniLength = dataPoints / (2 * fps)
soniSample = dataPoints // 2
soniFiller = np.ones(soniSample)

# Physical properties presets
m = 1e5  # kg
forceInc = 10000  # N
speedLimit = 50  # m/s
v = np.zeros(dataPoints)
t = np.zeros(dataPoints)
drivingForces = np.zeros(dataPoints)
breakForces = np.zeros(dataPoints)
netForces = np.zeros(dataPoints)
frictions = np.zeros(dataPoints)

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

print("Play back speed is x" + str(timeInc * fps))

# Reset the audio file before entering the loop to prevent previous data being outputted
sts.sonify(t[-soniSample:], soniFiller, style="style_balanced.yml", duration=soniLength)
sts.save("audio_vtSound.wav")
sts.close()

# Outputs the initial audio
initSoni = pg.mixer.Sound("audio_vtSound.wav")
soniChannel.play(initSoni)


# Function that holds the physical relation between the forces, time and velocity
def vtFunc(t, u, F):
    a = F / m
    return a * t + u


# Simple quadratic friction calculator
def fricCalc(velocity):
    speedLimitFactor = speedLimit / 50
    return -np.sign(velocity) * ((velocity / speedLimitFactor) ** 2) * 80


# Function to update the values in a force array
def rollUpdate(array, curVal):
    array = np.roll(array, -1)
    array[-1] = curVal
    return array


# Converts the sign of each element for an audio location
def panHandling(array):
    return (np.sign(array) + 1) / 2


# Plays the sonification of the processed data on the left of the graph and process the data for the right side
def delayedSoni(times, velocities, drvforces, brkForces, netForces, fricForces):
    global frictionless

    # Loads and plays the sonification of the previously processed data using pygame sound objects
    vtSoni = pg.mixer.Sound("audio_vtSound.wav")
    soniChannel.play(vtSoni)

    # Sampling and processing the data while current sonification is playing
    velSoni = velocities[-soniSample:]
    tSoni = times[-soniSample:]
    drvSoni = drvforces[-soniSample:]
    brkSoni = brkForces[-soniSample:]
    netSoni = netForces[-soniSample:]
    fricSoni = fricForces[-soniSample:]

    # Generates the audio figure which the sonification will be layered on to
    fig = sts.AudioFigure(system='stereo')

    # Computes the difference in velocities and the sign change
    velDiff = np.diff(velSoni)
    signDiff = np.sign(velDiff)

    # Change in sign
    signChange = np.diff(signDiff)

    # Finds the local maxima and minima
    maxMask = np.where(signChange < 0)[0] + 1
    minMask = np.where(signChange > 0)[0] + 1

    # Base values needed to pad out the sonification
    soniMaxs = np.zeros(soniSample)
    soniMins = np.zeros(soniSample)

    # Sets volumes only for indexes with maxima or minima
    soniMins[minMask] = np.abs(velSoni[minMask] + 1)
    soniMaxs[maxMask] = np.abs(velSoni[maxMask] + 1)

    # Generates the sonification for the local maximums and minimums
    if len(minMask) > 0:
        fig.sonify(tSoni, soniFiller, soniMins, style="style_whistle1.yml", duration=soniLength)
    if len(maxMask) > 0:
        fig.sonify(tSoni, soniFiller, soniMaxs, style="style_whistle2.yml", duration=soniLength,
                   fix_pan=1)

    # Cutoff sonification for frictional forces
    if not frictionless:
        fig.sonify(tSoni, np.abs(fricSoni), panHandling(fricSoni),
                   style="style_fricWind.yml", duration=soniLength)

    # Rhythmic mapping for driving force
    absDrv = np.abs(drvSoni)
    if np.max(absDrv) > 0:
        fig.sonify(tSoni, absDrv, panHandling(drvSoni), np.sign(absDrv),
                   style="style_chuff.yml", duration=soniLength)

    # Pitch mapping for the break force
    absBrk = np.abs(brkSoni)
    if np.max(absBrk) > 0:
        fig.sonify(tSoni, absBrk, panHandling(brkSoni), np.sign(absBrk), style="style_squeaky.yml", duration=soniLength)

    # Stops code running when velocity is entirely zero
    absVel = np.abs(velSoni)
    if np.max(absVel) > 0:
        # Gets the integral by using a cumulative sum
        displacement = np.cumsum(absVel)
        displacement /= (2 * speedLimit * soniSample)  # Reduces the frequency of clicks and maps them to the range

        # Sets up uniform increments
        incs = np.linspace(0, 1, soniSample + 1)
        incs = incs[:-1] + np.diff(incs) * 0.5

        # Interpolation for each sample between 0 and 1
        eventTimes = np.interp(incs, displacement, tSoni)

        # Calculates gaps between trigger times based on velocity, acceleration and jolt
        velSep = np.diff(eventTimes)
        accelSep = np.diff(velSep)

        # Calculates the trigger times based on the separations
        accelTimes = eventTimes[:-2] + accelSep

        # Reducing the event times to fit the graph region
        maxTime = np.max(eventTimes)
        eventTimes /= maxTime
        accelTimes /= maxTime

        # Mapping parameters which are the same for these pares of sonifications
        velPan = panHandling(velSoni)
        velVol = np.sign(absVel)

        # Tempo mapping for velocity and acceleration
        fig.sonify(eventTimes, soniFiller, velPan, velVol,
                   style="style_clickety.yml", duration=soniLength)
        # fig.sonify(accelTimes, soniFiller[:-2], velPan[:-2], velVol[:-2],
        #            style="style_clack.yml", duration=soniLength)
    absNet = np.abs(netSoni)
    if np.min(absNet) < 1:
        netVol = 1 - absNet
        fig.sonify(tSoni, netVol, style="style_balanced.yml", duration=soniLength)

    # Saves the sonification and closes STRAUSS
    fig.save("audio_vtSound.wav")
    sts.close()


# A procedure which takes string input and uses gtts to generate and play the string as spoken content
def speak(text):
    global internetWasConnected

    # Generates speech if there is an internet connection or plays an error message
    try:
        # Generates speech using gtts
        speech = gTTS(text=text.lower(), lang="en", slow=False)
        speech.save("audio_speech.mp3")

        # Loads and plays speech with pygame mixer
        speech = pg.mixer.Sound("audio_speech.mp3")
        internetWasConnected = True

    except:
        if internetWasConnected:
            # Play error message using pygame mixer
            speech = pg.mixer.Sound("audio_noInternet.mp3")
            internetWasConnected = False

    speechChannel.play(speech)
    sleep(speech.get_length())


# Returns the forces in a format ready to be given to speak
def utterable(force):
    return 1000 * round(force / 1000, 1)


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

    # Update the time axis with the new time counter value
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
    if np.abs(breakForce) > np.abs(drivingForce):
        if np.sign(v[-2]) != np.sign(v[-1]):
            v[-1] = 0

        if np.abs(v[-1]) <= lim:
            netForce = 0

    # Updating the arrays which store the forces
    drivingForces = rollUpdate(drivingForces, drivingForce)
    breakForces = rollUpdate(breakForces, breakForce)
    netForces = rollUpdate(netForces, netForce)
    frictions = rollUpdate(frictions, friction)

    # Regenerates the sound when a the current sonification runs out
    if sonification and not soniChannel.get_busy():
        delayedSoni(t, v, drivingForces, breakForces, netForces, frictions)

    # Generating and plotting the figure
    plt.figure()
    plt.plot(t, v, color="white", marker=".", linestyle="none")

    # Determine the range of y based on sign of values
    if np.min(v) < 0 < np.max(v):
        plt.ylim(-speedLimit, speedLimit)
    elif np.min(v) < 0:
        plt.ylim(-speedLimit, 0)
    else:
        plt.ylim(0, speedLimit)

    # Adding Labels to the figure
    plt.xlabel("time, t (s)")
    plt.ylabel("velocity, v (m/s)")
    plt.grid(color='grey')

    # Save the figure to be displayed and close pyplot for next loop
    plt.savefig("img_vtFig.png")
    plt.close()

    # Loading and displaying the graph
    figImg = pg.image.load("img_vtFig.png")
    figPos = (0, 0)
    SCREEN.blit(figImg, figPos)

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
        if event.type == pg.KEYDOWN and timeCounter > timeRange:
            if event.key == pg.K_UP:
                if int(drivingForce) < 2e5:
                    drivingForce += forceInc
            elif event.key == pg.K_DOWN:
                if int(drivingForce) > -2e5:
                    drivingForce -= forceInc
            elif event.key == pg.K_LEFT:
                if np.abs(breakForce) <= 0:
                    breakForce = 0
                else:
                    breakForce = int(np.abs(breakForce) - forceInc)
            elif event.key == pg.K_RIGHT:
                if np.abs(breakForce) < 2.5e5:
                    breakForce = int(np.abs(breakForce) + forceInc)
            elif event.key == pg.K_r:
                drivingForce = 0
                breakForce = 0
            elif event.key == pg.K_s:
                message = f"Driving force {drivingForce} Newtons. Break force {breakForce} Newtons. Net force {utterable(netForce)} Newtons."

                if not frictionless:
                    message = message + f"Frictional Force {utterable(friction)} Newtons."

                speak(message)
            elif event.key == pg.K_d:
                speak("Driving force " + str(drivingForce) + " Newtons.")
            elif event.key == pg.K_b:
                speak("Break force " + str(breakForce) + "Newtons.")
            elif event.key == pg.K_n:
                speak(f"Net force {utterable(netForce)} Newtons.")
            elif event.key == pg.K_v:
                speak(f"The current velocity is {v[-1]:.3g} metres per second")
            elif event.key == pg.K_f:
                speak(f"Frictional Force {utterable(friction)} newtons")
            elif event.key == pg.K_TAB:
                frictionless = not frictionless
                if not frictionless:
                    speak("Friction activated")
                else:
                    speak("Friction deactivated")
                    friction = 0
            elif event.key == pg.K_BACKSPACE:
                drivingForce = - drivingForce
            elif event.key == pg.K_LSHIFT:
                drivingForce = 0
            elif event.key == pg.K_RSHIFT:
                breakForce = 0
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
                breakForce = int(-np.sign(drivingForce) * np.abs(breakForce))
            elif v[-1] != 0:
                breakForce = int(-np.sign(v[-1]) * np.abs(breakForce))

    # Update screen and increment counter
    pg.display.update()
    timeCounter += timeInc
