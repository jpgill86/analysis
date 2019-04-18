#!/usr/bin/env python

'''
Tools for working with Neo objects
'''

import numpy as np
import neo
import elephant
from pylttb import lttb

class CausalAlphaKernel(elephant.kernels.AlphaKernel):
    '''
    This modified version of elephant.kernels.AlphaKernel shifts time such that
    convolution of the kernel with spike trains (as in
    elephant.statistics.instantaneous_rate) results in alpha functions that
    begin rising at the spike time, not before. The entire area of the kernel
    comes after the spike, rather than half before and half after, as in
    AlphaKernel. Consequently, CausalAlphaKernel can be used in causal filters.

    Derived from:
    '''
    __doc__ += elephant.kernels.AlphaKernel.__doc__

    def median_index(self, t):
        '''
        In CausalAlphaKernel, "median_index" is a misnomer. Instead of returning
        the index into t that gives half area above and half below (median), it
        returns the index for the first non-negative time, which always
        corresponds to the start of the rise phase of the alpha function. This
        hack ensures that, when the kernel is convolved with a spike train, the
        entire alpha function is located to the right of each spike time.

        Overrides the following:
        '''
        return np.nonzero(t >= 0)[0].min()
    median_index.__doc__ += elephant.kernels.AlphaKernel.median_index.__doc__

def DownsampleNeoSignal(sig, decimation_factor):
    '''

    '''

    assert sig.shape[1] == 1, 'Can only downsample single-channel signals'

    num_points = int(sig.shape[0] / decimation_factor)

    x_downsampled, y_downsampled = lttb(
        x=sig.times.magnitude,
        y=sig.magnitude[:, 0],
        threshold=num_points,
    )

    sig_downsampled = neo.IrregularlySampledSignal(
        times=x_downsampled,
        signal=y_downsampled,
        units=sig.units,
        time_units=sig.times.units,
    )
    return sig_downsampled
