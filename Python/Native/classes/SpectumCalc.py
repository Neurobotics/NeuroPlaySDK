from scipy.fft import fft, fftfreq, ifft
import numpy as np

class SpectrumCalc :

  def __init__(self):
    self.window = 4 # seconds
    self.overlap = 0.2 # seconds
    self.samplingRate = 125 # Hz
    self.data = [] # type: ignore
    self.index = 0
    self.callback =  None

    N = self.window * self.samplingRate
    T = 1.0 / self.samplingRate

    self.N = N
    self.T = T

    self.timeX = fftfreq(N, T)[:N//2]

    self.spectrum = []
    for i in range(len(self.timeX)):
      self.spectrum.append(0)

    # self.timeX = []
    # msPerSample = 1.0 / self.samplingRate
    # for i in range(self.window * self.samplingRate):
    #   self.timeX.append(i * msPerSample)

    print(self.spectrum)
    print(self.timeX)

  def addData(self, sample):
    self.data.append(sample)
    # print("Spec len", self.index, len(self.data))
    if len(self.data) >= (self.samplingRate * self.window) :
      print("spectum reached", self.index)

      original_spectrum = fft(self.data)
      self.spectrum = 2.0/self.N * np.abs(original_spectrum[0:self.N//2]) # "реальные" значения спектра

      print(self.spectrum)

      # for i in range(len(self.data)):
      #   self.spectrum[i] = self.data[i]

      if self.callback:
        self.callback(self.index, self.spectrum)

      i = self.overlap * self.samplingRate
      while i > 0:
        self.data.pop(0)
        i-=1

