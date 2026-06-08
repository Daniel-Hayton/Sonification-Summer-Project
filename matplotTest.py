from strauss.generator import Synthesizer

import matplotlib

print("Before:", matplotlib.get_backend())

matplotlib.use("TkAgg", force=True)

import matplotlib.pyplot as plt

print("After:", matplotlib.get_backend())

plt.plot([1, 2, 3], [1, 4, 9])
plt.show()