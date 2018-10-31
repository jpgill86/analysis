#!/usr/bin/env python

'''
This module implements simple functions for creating ephyviewer data sources
from Neo objects:

    - NeoAnalogSignalToInMemoryAnalogSignalSource
    - NeoEpochToInMemoryEpochSource
    - NeoEventToInMemoryEventSource
    - NeoSpikeTrainToInMemorySpikeSource

A convenience function is also implemented for creating ephyviewer data
sources from all of the children of a Neo Segment:

    - NeoSegmentToEphyviewerSources

For the purpose of demonstration, additional functions are implemented to
showcase the module:

    - CreateNeoBlockExample
    - PlotExampleWithEphyviewer

Run the module directly or execute the following to view the example:

    >>> from NeoToEphyviewerBridge import *
    >>> blk = CreateNeoBlockExample()
    >>> seg = blk.segments[0]
    >>> sources = NeoSegmentToEphyviewerSources(seg)
    >>> PlotExampleWithEphyviewer(sources)
'''

import numpy as np
import quantities as pq
import neo
import ephyviewer

def NeoSegmentToEphyviewerSources(neo_seg):
    '''
    Create ephyviewer data sources from a Neo Segment

    This convenience function calls each of the following:
        - NeoAnalogSignalToInMemoryAnalogSignalSource(neo_seg.analogsignals)
        - NeoEpochToInMemoryEpochSource(neo_seg.epochs)
        - NeoEventToInMemoryEventSource(neo_seg.events)
        - NeoSpikeTrainToInMemorySpikeSource(neo_seg.spiketrains)

    Parameters:
        neo_seg (neo.Segment)

    Returns:
        dict: Dictionary of ephyviewer sources with these key-value pairs:
            'signal':  list of ephyviewer.InMemoryAnalogSignalSource
            'epoch':   list of ephyviewer.InMemoryEpochSource
            'event':   list of ephyviewer.InMemoryEventSource
            'spike':   list of ephyviewer.InMemorySpikeSource
    '''

    sources = {'signal': [], 'epoch': [], 'event': [], 'spike': []}

    sources['signal'].append(NeoAnalogSignalToInMemoryAnalogSignalSource(neo_seg.analogsignals))
    # sources['epoch'] .append(NeoEpochToInMemoryEpochSource(neo_seg.epochs))
    sources['epoch'] .append(ephyviewer.NeoEpochSource(neo_seg.epochs))
    # sources['event'] .append(NeoEventToInMemoryEventSource(neo_seg.events))
    sources['event'] .append(ephyviewer.NeoEventSource(neo_seg.events))
    # sources['spike'] .append(NeoSpikeTrainToInMemorySpikeSource(neo_seg.spiketrains))
    sources['spike'] .append(ephyviewer.NeoSpikeTrainSource(neo_seg.spiketrains))

    return sources

def NeoAnalogSignalToInMemoryAnalogSignalSource(neo_analogsignals):
    '''
    Create ephyviewer.InMemoryAnalogSignalSource from Neo AnalogSignals

    Parameters:
        neo_analogsignals (list of neo.AnalogSignal)

    Returns:
        ephyviewer.InMemoryAnalogSignalSource
    '''

    sig_source = ephyviewer.InMemoryAnalogSignalSource(
        signals = np.concatenate([sig.magnitude for sig in neo_analogsignals], axis = 1),
        sample_rate = neo_analogsignals[0].sampling_rate.rescale('Hz').magnitude, # assuming all AnalogSignals have the same sampling rate
        t_start = neo_analogsignals[0].t_start.rescale('s').magnitude,            # assuming all AnalogSignals start at the same time
        channel_names = np.array([sig.name for sig in neo_analogsignals]),
    )

    return sig_source

def NeoEpochToInMemoryEpochSource(neo_epochs):
    '''
    Create ephyviewer.InMemoryEpochSource from Neo Epochs

    Parameters:
        neo_epochs (list of neo.Epoch)

    Returns:
        ephyviewer.InMemoryEpochSource
    '''

    all_epochs = []
    for neo_epoch in neo_epochs:
        all_epochs.append({
            'name': neo_epoch.name,
            'time': neo_epoch.times.rescale('s').magnitude,
            'duration': neo_epoch.durations.rescale('s').magnitude,
            'label': np.array(neo_epoch.labels),
        })
    epoch_source = ephyviewer.InMemoryEpochSource(all_epochs = all_epochs)

    return epoch_source

def NeoEventToInMemoryEventSource(neo_events):
    '''
    Create ephyviewer.InMemoryEventSource from Neo Events

    Parameters:
        neo_events (list of neo.Event)

    Returns:
        ephyviewer.InMemoryEventSource
    '''

    all_events = []
    for neo_event in neo_events:
        all_events.append({
            'name': neo_event.name,
            'time': neo_event.times.rescale('s').magnitude,
            'label': np.array(neo_event.labels),
        })
    event_source = ephyviewer.InMemoryEventSource(all_events = all_events)

    return event_source

def NeoSpikeTrainToInMemorySpikeSource(neo_spiketrains):
    '''
    Create ephyviewer.InMemorySpikeSource from Neo SpikeTrains

    Parameters:
        neo_spiketrains (list of neo.SpikeTrain)

    Returns:
        ephyviewer.InMemorySpikeSource
    '''

    all_spikes = []
    for neo_spiketrain in neo_spiketrains:
        all_spikes.append({
            'name': neo_spiketrain.name,
            'time': neo_spiketrain.times.rescale('s').magnitude,
        })
    spike_source = ephyviewer.InMemorySpikeSource(all_spikes = all_spikes)

    return spike_source

def CreateNeoBlockExample():
    '''
    Create a Neo Block containing fake data

    The result has the following structure:
        neo.Block
            neo.Segment
                2x neo.AnalogSignal
                2x neo.Epoch
                2x neo.Event
                2x neo.SpikeTrain

    Returns:
        neo.Block
    '''

    # create a block and segment
    blk = neo.Block()
    seg = neo.Segment()
    blk.segments.append(seg)

    # create fake signals
    sig0 = neo.AnalogSignal(name = 'signal 0', signal = np.cos(np.arange(0, 60, 0.1)) * pq.V, sampling_period = 0.1 * pq.s)
    sig1 = neo.AnalogSignal(name = 'signal 1', signal = np.sin(np.arange(0, 60, 0.1)) * pq.V, sampling_period = 0.1 * pq.s)
    seg.analogsignals.append(sig0)
    seg.analogsignals.append(sig1)

    # create fake epochs
    epoch0 = neo.Epoch(name = 'epoch set 0', labels = ['epoch 0A', 'epoch 0B', 'epoch 0C'], times = [ 0, 10, 20] * pq.s, durations = [5, 5, 5] * pq.s)
    epoch1 = neo.Epoch(name = 'epoch set 1', labels = ['epoch 1A', 'epoch 1B', 'epoch 1C'], times = [30, 40, 50] * pq.s, durations = [5, 5, 5] * pq.s)
    seg.epochs.append(epoch0)
    seg.epochs.append(epoch1)

    # create fake events
    event0 = neo.Event(name = 'event set 0', labels = ['event 0A', 'event 0B', 'event 0C'], times = [ 0, 10, 20] * pq.s)
    event1 = neo.Event(name = 'event set 1', labels = ['event 1A', 'event 1B', 'event 1C'], times = [30, 40, 50] * pq.s)
    seg.events.append(event0)
    seg.events.append(event1)

    # create fake spike trains
    st0 = neo.SpikeTrain(name = 'spike train 0', t_stop = 60 * pq.s, times = np.arange(0, 60, 2*np.pi) * pq.s)
    st1 = neo.SpikeTrain(name = 'spike train 1', t_stop = 60 * pq.s, times = np.arange(np.pi/2, 60, 2*np.pi) * pq.s)
    seg.spiketrains.append(st0)
    seg.spiketrains.append(st1)

    # create child-parent relationships
    blk.create_relationship()

    return blk

def PlotExampleWithEphyviewer(sources, xsize = 60):
    '''
    Create a minimal application for displaying ephyviewer data sources

    Parameters:
        sources (dict)
            Structured like the output of NeoSegmentToEphyviewerSources(seg)
        xsize (number)
            The amount of time to display on the x-axis
    '''

    # create a new app
    app = ephyviewer.mkQApp()

    # create a window
    win = ephyviewer.MainViewer()

    # create viewers for each data source
    for i, signal_source in enumerate(sources['signal']):
        trace_view = ephyviewer.TraceViewer(source = signal_source, name = 'trace viewer {}'.format(i))
        if i == 0:
            win.add_view(trace_view)
        else:
            win.add_view(trace_view, tabify_with = 'trace viewer 0')

    for i, epoch_source in enumerate(sources['epoch']):
        epoch_view = ephyviewer.EpochViewer(source = epoch_source, name = 'epoch viewer {}'.format(i))
        if i == 0:
            win.add_view(epoch_view)
        else:
            win.add_view(epoch_view, tabify_with = 'epoch viewer 0')

    for i, spike_source in enumerate(sources['spike']):
        spike_train_view = ephyviewer.SpikeTrainViewer(source = spike_source, name = 'spiketrain viewer {}'.format(i))
        if i == 0:
            win.add_view(spike_train_view)
        else:
            win.add_view(spike_train_view, tabify_with = 'spiketrain viewer 0')

    for i, event_source in enumerate(sources['event']):
        event_list = ephyviewer.EventList(source = event_source, name = 'event list {}'.format(i))
        if i == 0:
            win.add_view(event_list, location = 'bottom', orientation = 'horizontal')
        else:
            win.add_view(event_list, tabify_with = 'event list 0')

    # adjust plot range and scaling
    win.set_xsize(xsize)
    win.auto_scale()

    # show the app
    win.show()
    app.exec_()

if __name__ == '__main__':

    blk = CreateNeoBlockExample()
    seg = blk.segments[0]
    sources = NeoSegmentToEphyviewerSources(seg)
    PlotExampleWithEphyviewer(sources)
