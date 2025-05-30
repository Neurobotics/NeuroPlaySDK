from scipy.fft import fft, fftfreq, ifft
import numpy as np

class SpectrumCalc :

  def __init__(self):
    self.window = 4 # seconds
    self.overlap = 0.2 # seconds
    self.samplingRate = 125 # Hz
    self.data = [] # type: ignore
    self.index = 0
    self.callback = None

    self.N = self.window * self.samplingRate
    self.T = 1.0 / self.samplingRate

    self.frequencies = fftfreq(self.N, self.T)[:self.N//2]

    self.L = len(self.frequencies)

    self.spectrum = []
    for i in range(self.L):
      self.spectrum.append(0)

    self.hann = np.hanning(self.N)  

  def addData(self, sample):
    self.data.append(sample)
    if len(self.data) >= (self.samplingRate * self.window) :
      signal = []
      for i in range(self.N):
        signal.append(self.data[i])

      original_spectrum = fft(signal * self.hann)
      self.spectrum = 2.0/self.N * np.abs(original_spectrum[0:self.N//2])

      if self.callback:
        self.callback(self.index, self.spectrum)

      i = self.overlap * self.samplingRate
      while i > 0:
        self.data.pop(0)
        i-=1

