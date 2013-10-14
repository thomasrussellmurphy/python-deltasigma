from __future__ import division
import numpy as np

from control import step
from pydelsigma.utils import lcm, rat

def pulse(S, tp=(0., 1.), dt=1., tfinal=10., nosum=False):
	""" y = pulse(S, tp=[0 1], dt=1, tfinal=10, nosum=0)
	Calculate the sampled pulse response 
	of a CT system. tp may be an array of pulse timings, one for each input.
	Outputs:
	y	The pulse response
	
	Inputs
	S	An LTI object specifying the system.
	tp	An (n, 2) array of pulse timings
	dt	The time increment
	tfinal	The time of the last desired sample
	nosum	A flag indicating that the responses are not to be summed
	"""
	tp = np.mat(np.array(tp))
	if len(tp.shape) == 1:
		if not tp.shape[0] == 2:
			raise ValueError, "tp is not (n, 2)-shaped"
		tp.reshape((1, tp.shape[0]))
	if len(tp.shape) == 2: 
		if not tp.shape[1] == 2:
			raise ValueError, "tp is not (n, 2)-shaped"
	# Check the arguments
	if S.dt != None:
	    raise VelueError, 'S must be a cts-time system.'

	# Compute the time increment
	dd = 1;
	for tpi in np.nditer(np.array(tp)):
		x, di = rat(tpi, 1e-3)
		dd = lcm(di, dd)

	x, ddt = rat(dt, 1e-3)
	x, df = rat(tfinal, 1e-3)
	delta_t = 1. / lcm(dd, lcm(ddt, df))
	delta_t = max(1e-3, delta_t)	# Put a lower limit on delta_t
	y1, T1 = step(S, T=np.arange(0., tfinal, delta_t))

	nd = np.round(dt/delta_t, 0)
	nf = np.round(tfinal/delta_t, 0)
	ndac = tp.shape[0]
	Sscipy = S.returnScipySignalLti()
	ni = len(Sscipy)
	
	if (ni % ndac) != 0:
		raise ValueError, 'The number of inputs must be divisible by the number of dac timings.'
		# Original comment from the MATLAB sources:
		# This requirement comes from the complex case, where the number of inputs
		# is 2 times the number of dac timings. I think this could be tidied up.

	nis = ni/ndac # Number of inputs grouped together with a common DAC timing
	              # (2 for the complex case)
	if not nosum: # Sum the responses due to each input set
		y = np.zeros((np.ceil(tfinal/float(dt)), len(Sscipy[0]), nis))
	else:
		y = np.zeros((np.ceil(tfinal/float(dt)), len(Sscipy[0]), ni))

	if len(y1.shape) == 1:
		y1 = y1.reshape((y1.shape[0], 1, 1))
	#y1_columns = y1.shape[1] if len(y1.shape) > 1 else 1
	for i in range(ndac):
		n1 = np.round(tp[i, 0]/delta_t, 0)
		n2 = np.round(tp[i, 1]/delta_t, 0)
		z1 = (n1, y1.shape[1], nis)
		z2 = (n2, y1.shape[1], nis)
		yy = + np.concatenate((np.zeros(z1), y1[:nf-n1, :, (i-1)*nis:i*nis+1]), axis=0) \
		     - np.concatenate((np.zeros(z2), y1[:nf-n2, :, (i-1)*nis:i*nis+1]), axis=0)
		yy = yy[::nd, :, :]
		if not nosum: # Sum the responses due to each input set
			y = y + yy
		else:
			y[:, :, i] = yy
	return y

def test_pulse():
	from control import tf
	import pkg_resources
	import scipy.io
	H = tf([1], [1, 2, 10])
	pp = pulse(H, tp=(0., 1.), dt=.1, tfinal=10., nosum=False)
	pp = pp.reshape((pp.shape[0],1))
	fname = pkg_resources.resource_filename(__name__, "test_data/test_pulse.mat")
	pp2 = scipy.io.loadmat(fname)['pp'][:100] # FIXME? pulse returns 101 points, we return 100
	assert np.allclose(pp, pp2, atol=1e-6, rtol=1e-4)
	# FIXME ALSO CHECK MIMO TFS
	
if __name__ == '__main__':
	test_pulse()