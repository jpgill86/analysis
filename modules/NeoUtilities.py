#!/usr/bin/env python

'''
Tools for working with Neo objects
'''

import numpy as np
import quantities as pq
import neo
import elephant

def NeoAnalogSignalDerivative(sig):
    '''
    Calculate the derivative of a Neo AnalogSignal

    Parameters:
        sig (neo.AnalogSignal)
            The signal to differentiate. If sig contains more than one channel,
            each is differentiated separately.

    Returns:
        neo.AnalogSignal
            The returned object is an AnalogSignal containing the differences
            between each successive sample value of the input signal divided by
            the sampling period. The output signal will have the same number of
            channels as the input signal.
    '''

    if not isinstance(sig, neo.AnalogSignal):
        raise TypeError('sig must be an AnalogSignal: {}'.format(sig))

    derivative_sig = neo.AnalogSignal(
        np.diff(sig.as_quantity(), axis=0) / sig.sampling_period,
        t_start = sig.t_start,
        sampling_period = sig.sampling_period,
    )

    return derivative_sig

def NeoAnalogSignalRAUC(sig, bin_duration = None, baseline = None, t_start = None, t_stop = None):
    '''
    Calculate the rectified area under the curve (RAUC) for a Neo AnalogSignal

    The signal is optionally divided into bins with duration bin_duration, and
    the rectified signal (absolute value) is integrated within each bin to find
    the area under the curve. By default, the mean of the signal is subtracted
    before rectification. If the number of bins is 1 (default), a single value
    is returned for each channel in the input signal. Otherwise, an AnalogSignal
    containing the values for each bin is returned along with the times of the
    centers of the bins.

    Parameters:
        sig (neo.AnalogSignal)
            The signal to integrate. If sig contains more than one channel, each
            is integrated separately.
        bin_duation (quantities.Quantity)
            The length of time that each integration should span. If None
            (default), there will be only one bin spanning the entire signal
            duration. If bin_duration does not divide evenly into the signal
            duration, the end of the signal is padded with zeros to accomodate
            the final, overextending bin.
        baseline (quantities.Quantity)
            A factor to subtract from the signal before rectification. If None
            (default), the mean value of the entire signal is used.
        t_start, t_stop (quantities.Quantity)
            Times to start and end the algorithm. The signal is cropped using
            sig.time_slice(t_start, t_stop) after baseline removal. Useful
            if you want the RAUC for a short section of the signal but want the
            automatic mean calculation (baseline=None) to use the entire signal
            for better baseline estimation.

    Returns:
        quantities.Quantity or neo.AnalogSignal
            If the number of bins is 1, the returned object is a scalar or
            vector Quantity containing a single RAUC value for each channel.
            Otherwise, the returned object is an AnalogSignal containing the
            RAUC(s) for each bin stored as a sample, with times corresponding to
            the center of each bin. The output signal will have the same number
            of channels as the input signal.
    '''

    if not isinstance(sig, neo.AnalogSignal):
        raise TypeError('sig must be an AnalogSignal: {}'.format(sig))

    if baseline is not None:
        # subtract arbitrary baseline
        if isinstance(baseline, pq.Quantity):
            sig = sig - baseline
        else:
            raise TypeError('baseline must be a Quantity: {}'.format(baseline))
    else:
        # subtract mean from each channel
        sig = sig - sig.mean(axis = 0)

    # slice the signal after subtracting baseline
    sig = sig.time_slice(t_start, t_stop)

    if bin_duration is not None:
        # from an arbitrary bin duration, determine samples per bin and number of bins
        if isinstance(bin_duration, pq.Quantity):
            samples_per_bin = int(np.round(bin_duration.rescale('s') / sig.sampling_period.rescale('s')))
            n_bins = int(np.ceil(sig.shape[0] / samples_per_bin))
        else:
            raise TypeError('bin_duration must be a Quantity: {}'.format(bin_duration))
    else:
        # all samples in one bin
        samples_per_bin = sig.shape[0]
        n_bins = 1

    # store the actual bin duration
    bin_duration = samples_per_bin * sig.sampling_period.rescale('s')

    # reshape into equal size bins, padding the end with zeros if necessary
    n_channels = sig.shape[1]
    sig_binned = sig.as_quantity().copy()
    sig_binned.resize(n_bins * samples_per_bin, n_channels)
    sig_binned = sig_binned.reshape(n_bins, samples_per_bin, n_channels)

    # rectify and integrate over each bin
    rauc = np.trapz(np.abs(sig_binned), dx = sig.sampling_period, axis = 1)

    if n_bins == 1:
        # return a single value for each channel
        return rauc.squeeze()

    else:
        # return an AnalogSignal with times corresponding to the center of each bin
        rauc_sig = neo.AnalogSignal(
            rauc,
            t_start = sig.t_start.rescale('s') + bin_duration/2,
            sampling_period = bin_duration,
        )
        return rauc_sig

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
