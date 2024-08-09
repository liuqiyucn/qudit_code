import numpy as np
import matplotlib.pyplot as plt

# Define the Lorentzian function
def lorentzian(f, f0, gamma):
    return (gamma/2)**2 / ((f - f0)**2 + (gamma/2)**2)

# First set of parameters
frequencies_1 = np.linspace(6.750, 6.764, 1000)
f0_1a = 6.7560  # center frequency in GHz
f0_1b = 6.7569  # center frequency in GHz
gamma_1 = 6e-3  # linewidth in GHz (6 MHz)
lorentzian_1a = lorentzian(frequencies_1, f0_1a, gamma_1)
lorentzian_1b = lorentzian(frequencies_1, f0_1b, gamma_1)

# Second set of parameters
frequencies_2 = np.linspace(6.750, 6.764, 1000)
f0_2a = 6.7560  # center frequency in GHz
f0_2b = 6.7572  # center frequency in GHz
gamma_2 = 3e-3  # linewidth in GHz (3 MHz)
lorentzian_2a = lorentzian(frequencies_2, f0_2a, gamma_2)
lorentzian_2b = lorentzian(frequencies_2, f0_2b, gamma_2)

# Plotting the subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))

# First subplot
ax1.plot(frequencies_1, lorentzian_1a, label='Lorentzian at 6.756 GHz')
ax1.plot(frequencies_1, lorentzian_1b, label='Lorentzian at 6.749 GHz')
ax1.set_xlabel('Frequency (GHz)')
ax1.set_ylabel('Intensity')
ax1.set_title('900 KHz Shift | 6 GHz linewidth')
ax1.legend()
ax1.grid(True)

# Second subplot
ax2.plot(frequencies_2, lorentzian_2a, label='Lorentzian at 6.759 GHz')
ax2.plot(frequencies_2, lorentzian_2b, label='Lorentzian at 6.749 GHz')
ax2.set_xlabel('Frequency (GHz)')
ax2.set_ylabel('Intensity')
ax2.set_title('1.2 MHz Shift | 3 GHz linewidth')
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.savefig('cavity_comparison.jpg')
