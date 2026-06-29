import strauss as sts
import numpy as np
import pygame as pg
import matplotlib as mpl
from matplotlib import pyplot as plt

# Presets for graphing
mpl.use("tkagg")
plt.style.use("dark_background")

# setting the frequency of the running loop
fps = 1
timer = pg.time.Clock()
timeRange = 60
counter = 0

# Setting up the screen with its constant background name and size and hides the mouse
SCREEN = pg.display.set_mode((640, 480))
pg.display.set_caption("vt-Graph")
pg.mouse.set_visible(False)


# Function that holds the physical relation between the forces, time and velocity
def vtFunc(time, A):
    return A * np.sin(time)


running = True
while running:
    timer.tick(fps)

    # Defining t on this loop
    t = np.linspace(counter, counter + 60, 100)
    counter += 1

    A = 5

    # Generating and saving the figure
    plt.figure()
    plt.plot(t, vtFunc(t, A))
    plt.savefig("vtFig.jpg")
