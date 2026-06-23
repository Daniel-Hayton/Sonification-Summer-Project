# import packages
from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt
import strauss
from statsmodels.distributions.empirical_distribution import ECDF
import csv
import matplotlib as mpl

mpl.use("Tkagg", force=True)
plt.style.use("dark_background")

# Formation of Star Cluster from Gas Cloud Sonification

seed = 35  # set random number generator seed so can have conistent results
sonification_length = 20  # set sonification length
fps = 30  # frames per second
events_data_output_filename = "star_formation_events.csv"

# Set Properties of Fake Data

number_stars = 100  # number of stars
time_min = 0.  # minimum formation time
time_max = sonification_length  # maximum formation time
time_width = 2.  # width of formation times distribution
x_min = 0  # minimum x location of formation
x_max = 100  # maximum x location of formation
y_min = 0  # minimum y location of formation
y_max = 100  # maximum y location of formation
x_position_width = 13  # width of distribution in x
y_position_width = 13  # width of distribution in y


# Plotting parameters
mpl.rcParams['lines.linewidth'] = 2
mpl.rcParams['lines.linestyle'] = '--'
mpl.rcParams['axes.linewidth'] = 2
mpl.rcParams['axes.labelsize'] = 15
mpl.rcParams['axes.labelweight'] = 2

mpl.rcParams['ytick.right'] = True
mpl.rcParams['ytick.direction'] = 'in'
mpl.rcParams['ytick.major.size'] = 5
mpl.rcParams['ytick.major.width'] = 2
mpl.rcParams['ytick.labelsize'] = 12

mpl.rcParams['xtick.top'] = True
mpl.rcParams['xtick.major.size'] = 5
mpl.rcParams['xtick.direction'] = 'in'
mpl.rcParams['xtick.major.width'] = 2
mpl.rcParams['xtick.labelsize'] = 12

# Universal time array (for sonification and animation)
number_frames = fps * (time_max - time_min)
time_array = np.arange(time_min, time_max, 1 / fps)


# Gaussian model for fitting distribution later
def gauss(X, C, X_mean, sigma):
    return C * np.exp(-(X - X_mean) ** 2 / (2 * sigma ** 2))


# Create Fake Data

# Formation Times
np.random.seed(seed)
formation_times = np.random.randn(number_stars) * time_width + (time_max - time_min) / 2.
formation_times.sort()

# Fit the distribution of formation times go can calculate the concurrent star formation rate
formation_times_hist, formation_times_bin_edges = np.histogram(formation_times)
n_bin_edges = len(formation_times_hist)
time_bin_values = np.zeros((n_bin_edges), dtype=float)
for ii in range(n_bin_edges):
    time_bin_values[ii] = (formation_times_bin_edges[ii + 1] + formation_times_bin_edges[ii]) / 2
mean_guess = (time_max - time_min) / 2.
sigma_guess = time_width
param_optimised, param_covariance_matrix = curve_fit(gauss, time_bin_values, formation_times_hist, p0=[max(formation_times_hist), mean_guess, sigma_guess], maxfev=5000)

# Calculate star formation rate as a function of time
formation_times_fit = gauss(time_array, *param_optimised)
star_formation_rate_fit = formation_times_fit / time_array

# Plot formation time distribution and star formation calculation (SFR)
fig, ax = plt.subplots()
ax.hist(formation_times)
ax.plot(time_array, formation_times_fit)
ax.plot(time_array, star_formation_rate_fit, label='SFR')
ax.set_xlim([time_min, time_max])
ax.set_xlabel('Time (s)')
ax.set_ylabel('Distribution of Formation Times')
plt.legend()
# plt.show()

# Need to map on to the frames of the animation

# Map everything on to the time of the nearest frame in the animation
closest_time_indices = np.zeros(number_stars, dtype=int)
frame_matched_formation_time = np.zeros(number_stars, dtype=float)
current_star_formation_rate = np.zeros(number_stars, dtype=float)
for x in range(number_stars):
    closest_time_indices[x] = (np.abs(time_array - formation_times[x])).argmin()
    frame_matched_formation_time[x] = time_array[closest_time_indices[x]]
    current_star_formation_rate[x] = star_formation_rate_fit[closest_time_indices[x]]

# Calculate Data for the Gas Cloud Conversion into Stars (Reduction in volume)

# Use the culumative distribtion of formation times (inverted)
# This effective represents volume *not* converted to stars
e = ECDF(formation_times)
cumulative_formation = np.interp(time_array, e.x, e.y)  # interpolate onto universal time array
# Adding an offset because in reality would have some gas cloud left at the end (don't want it to go to zero)
cloud_collapse = 1 - cumulative_formation + 0.2  # probably should set this as a parameter as star of code

fig, ax = plt.subplots()
ax.plot(time_array, cloud_collapse)
ax.set_xlabel('Time (s)')
ax.set_ylabel('Cumulative Formation')
ax.set_ylim([0, max(cloud_collapse) + 0.05 * max(cloud_collapse)])
# plt.show()

# Generate random positions for the location of the formed stars

x_positions = np.random.randn(number_stars) * x_position_width + (x_max - x_min) / 2.
y_positions = np.random.randn(number_stars) * y_position_width + (y_max - y_min) / 2.

fig, ax = plt.subplots()
ax.plot(x_positions, y_positions, marker='o', linestyle='none', color="orange")
ax.set_xlabel('x position')
ax.set_ylabel('y position')
ax.set_xlim([x_min, x_max])
ax.set_ylim([y_min, y_max])
# plt.show()

# Generate Final Events Data for Sonification

# Need to add a silent event at the begnning and end of the array for the event-based sonification (so the sonification goes from 0 seconds to the sonification length, and is not scaled to where only events exist). 
# Set these to have zero SFR so can have zero volume.


formation_times = np.hstack([0, np.array(formation_times), sonification_length])
closest_time_indices = np.hstack([0, np.array(closest_time_indices), len(closest_time_indices) - 1])
frame_matched_formation_time = np.hstack([0, np.array(frame_matched_formation_time), np.max(time_array)])
x_positions = np.hstack([np.min(x_positions), np.array(x_positions), np.max(x_positions)])
y_positions = np.hstack([0, np.array(y_positions), 0])
current_star_formation_rate = np.hstack([0, np.array(current_star_formation_rate), 0])

# Create Dictionary
fieldnames = ["iD", "FormationTime", "ClosestTimeIndice", "FrameMatchedFormationTime", "xPosition", "yPosition",
              "currentSFR"]
iDlist = np.arange(0, number_stars + 2, 1)
star_formation_events_data = [{
    "iD": v,
    "FormationTime": formation_times[i],
    "ClosestTimeIndice": closest_time_indices[i],
    "FrameMatchedFormationTime": frame_matched_formation_time[i],
    "xPosition": x_positions[i],
    "yPosition": y_positions[i],
    "currentSFR": current_star_formation_rate[i]
} for i, v in enumerate(iDlist)]

# Write to file
with open(events_data_output_filename, mode='w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()  # Write header row
    writer.writerows(star_formation_events_data)  # Write data rows

# Stars Forming
length = 20

# Rescale azimuth input between 0-1 for correct behaviour in STRAUSS
rescaled_x = (x_positions - np.min(x_positions)) / (np.max(x_positions) - np.min(x_positions))

# Add slight pitch variation to make same notes sound slighly different
pitch_jitter = np.random.normal(0, 0.01, len(x_positions))

strauss.sonify(formation_times,
               current_star_formation_rate,
               current_star_formation_rate,
               rescaled_x,
               pitch_jitter,
               duration=length,
               style='cluster1.yml',
               system="stereo",
               level="20 db")
# strauss.save("stars_forming v1p5.wav")
# strauss.close()

# Cloud Synth
strauss.sonify(time_array, cloud_collapse, duration=length, system="mono", style="cluster2.yml")
# strauss.save("gas_chord v1p5.wav")
# strauss.close()

# Spectraliser for gas cloud collapse

n_freqs = 1000
n_time = 1000

# frequency axis (0 → 1 normalized)
freqs = np.linspace(0, 1, n_freqs)

# set limits and choose target frequencies
min_freq = 40
max_freq = 1000

# target frequencies
f1 = 261.63
f2 = 391.99

f1 = (f1 - min_freq) / (max_freq - min_freq)
print(f1)
f2 = (f2 - min_freq) / (max_freq - min_freq)
print(f2)

# width of peaks (shrinks over time)
max_width = 0.1
min_width = 0.001

spec_stack = np.zeros((n_freqs, n_time))

cloud_norm = (cloud_collapse - cloud_collapse.min()) / (cloud_collapse.max() - cloud_collapse.min())

# Stretch to match n_time using interpolation
cloud_interp = np.interp(
    np.linspace(0, 1, n_time),
    np.linspace(0, 1, len(cloud_collapse)),
    cloud_norm
)

# Build the evolution
for t in range(n_time):
    alpha = t / (n_time - 1)  # For width narrowing
    noise_weight = cloud_interp[t]  # 1.0 → 0.0 driven by collapse data
    peak_weight = 1 - cloud_interp[t]  # 0.0 → 1.0 (inverse)

    # start wide → end narrow
    width = max_width * (1 - alpha) + min_width * alpha

    # two Gaussian peaks
    peak1 = np.exp(-0.5 * ((freqs - f1) / width) ** 2)
    peak2 = np.exp(-0.5 * ((freqs - f2) / width) ** 2)

    peaks = peak1 + peak2

    # noise component (strong at start, fades out)
    noise = np.random.rand(n_freqs)

    spectrum = noise_weight * 0.1 * noise + peak_weight * peaks

    spec_stack[:, t] = spectrum

# Plot
plt.figure(figsize=(10, 6))
plt.imshow(spec_stack, aspect='auto', origin='lower', cmap='magma')
plt.colorbar(label='Amplitude')
plt.xlabel('Time step')
plt.ylabel('Frequency bin')
plt.title('Generated Spectrum')
# plt.show()

# render and play sonification!
strauss.sonify([spec_stack.T], [1], system="stereo", style="cluster3.yml", duration=length)
# strauss.save("spectrum_shift v1p5.wav")
strauss.save('v1p5 StarClusterFormation.wav')
strauss.close()
