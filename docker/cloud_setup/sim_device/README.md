# Measurement Simulator
In order to test developed grid protection schemes, a simple measurement simulator is provided. The simulator generates sinus wave based measurement points for each registered measurement node dependent on a given sampling rate.

Furthermore, one can set the period of time in which the set sine wave is intentionally deviated from in order to deliberately simulate a current drain and thus an error. This deviation is implemented as an increasing offset in the angle. In a endless loop, time span with abnormal measurement is following a time span with normal measurement.

So far the setpoints are hard-coded, but in a future feature release it is intended to add the possibility to load setpoints and tuning parameter via json file.
