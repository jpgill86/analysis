#!/usr/bin/env python

'''
Import raw data, annotations, and spike sorting results as Neo objects
'''

import numpy as np
import pandas as pd
import quantities as pq
import elephant
import neo

from ParseMetadata import abs_path
from neo.test.generate_datasets import fake_neo

def LoadAndPrepareData(metadata, fake_data_for_testing = False):
    '''

    '''

    # read in the electrophysiology data
    blk = ReadDataFile(metadata)
    # blk = CreateNeoBlockExample()

    # apply filters to signals
    blk = ApplyFilters(metadata, blk)

    # read in annotations
    annotations_dataframe = ReadAnnotationsFile(metadata)
    if annotations_dataframe is not None:
        blk.segments[0].epochs += CreateNeoEpochsFromDataframe(annotations_dataframe, metadata, abs_path(metadata, 'annotations_file'))
        blk.segments[0].events += CreateNeoEventsFromDataframe(annotations_dataframe, metadata, abs_path(metadata, 'annotations_file'))
    else:
        if fake_data_for_testing:
            blk.segments[0].epochs += [fake_neo('Epoch') for _ in range(5)]
            blk.segments[0].events += [fake_neo('Event') for _ in range(5)]

    # read in epoch encoder file
    epoch_encoder_dataframe = ReadEpochEncoderFile(metadata)
    if epoch_encoder_dataframe is not None:
        blk.segments[0].epochs += CreateNeoEpochsFromDataframe(epoch_encoder_dataframe, metadata, abs_path(metadata, 'epoch_encoder_file'))
        blk.segments[0].events += CreateNeoEventsFromDataframe(epoch_encoder_dataframe, metadata, abs_path(metadata, 'epoch_encoder_file'))

    # classify spikes by amplitude
    blk.segments[0].spiketrains += RunAmplitudeDiscriminators(metadata, blk)

    # read in spikes identified by spike sorting using tridesclous
    spikes_dataframe = ReadSpikesFile(metadata, blk)
    if spikes_dataframe is not None:
        # assuming all AnalogSignals have the same time properties
        t_start = blk.segments[0].analogsignals[0].t_start
        t_stop = blk.segments[0].analogsignals[0].t_stop
        sampling_period = blk.segments[0].analogsignals[0].sampling_period

        # read in spikes identified by spike sorting
        blk.segments[0].spiketrains += CreateNeoSpikeTrainsFromDataframe(spikes_dataframe, metadata, t_start, t_stop, sampling_period)
    else:
        # otherwise load fake data as a demo
        if fake_data_for_testing:
            blk.segments[0].spiketrains += [fake_neo('SpikeTrain') for _ in range(5)]

    return blk

def ReadDataFile(metadata):
    '''

    '''

    # read in the electrophysiology data
    io = neo.io.get_io(abs_path(metadata, 'data_file'))
    blk = io.read_block()

    return blk

def ReadAnnotationsFile(metadata):
    '''

    '''

    if metadata['annotations_file'] is None:

        return None

    else:

        # data types for each column in the file
        dtypes = {
            'Start (s)': float,
            'End (s)':   float,
            'Type':      str,
            'Label':     str,
        }

        # parse the file and create a dataframe
        df = pd.read_csv(abs_path(metadata, 'annotations_file'), dtype = dtypes)

        # increment row labels by 2 so they match the source file
        # which is 1-indexed and has a header
        df.index += 2

        # discard entries with missing or negative start times
        bad_start = df['Start (s)'].isnull() | (df['Start (s)'] < 0)
        if bad_start.any():
            print('NOTE: These rows will be discarded because their Start times are missing or negative:')
            print(df[bad_start])
            df = df[~bad_start]

        # discard entries with end time preceding start time
        bad_end = df['End (s)'] < df['Start (s)']
        if bad_end.any():
            print('NOTE: These rows will be discarded because their End times precede their Start times:')
            print(df[bad_end])
            df = df[~bad_end]

        # compute durations
        df.insert(
            column = 'Duration (s)',
            value = df['End (s)'] - df['Start (s)'],
            loc = 2, # insert after 'End (s)'
        )

        # replace some NaNs
        df.fillna({
            'Duration (s)': 0,
            'Type': 'Other',
            'Label': '',
        }, inplace = True)

        # sort entries by time
        df.sort_values([
            'Start (s)',
            'Duration (s)',
        ], inplace = True)

        # return the dataframe
        return df

def ReadEpochEncoderFile(metadata):
    '''

    '''

    if metadata['epoch_encoder_file'] is None:

        return None

    else:

        # data types for each column in the file
        dtypes = {
            'time':     float,
            'duration': float,
            'label':    str,
        }

        # parse the file and create a dataframe
        df = pd.read_csv(abs_path(metadata, 'epoch_encoder_file'), dtype = dtypes)

        # increment row labels by 2 so they match the source file
        # which is 1-indexed and has a header
        df.index += 2

        # discard entries with missing or negative start times
        bad_time = df['time'].isnull() | (df['time'] < 0)
        if bad_time.any():
            print('NOTE: These rows will be discarded because their times are missing or negative:')
            print(df[bad_time])
            df = df[~bad_time]

        # discard entries with missing or negative duration
        bad_duration = df['duration'].isnull() | (df['duration'] < 0)
        if bad_duration.any():
            print('NOTE: These rows will be discarded because their durations are missing or negative:')
            print(df[bad_duration])
            df = df[~bad_duration]

        # compute end times
        df.insert(
            column = 'End (s)',
            value = df['time'] + df['duration'],
            loc = 1, # insert after 'start'
        )

        # sort entries by time
        df.sort_values([
            'time',
            'duration',
        ], inplace = True)

        # change column names, including renaming epoch encoder's 'label' to 'Type'
        df = df.rename(
            index = str,
            columns = {'time': 'Start (s)', 'duration': 'Duration (s)', 'label': 'Type'})

        # add 'Label' column to indicate where these epochs came from
        df.insert(
            column = 'Label',
            value = '(from epoch encoder file)',
            loc = 4, # insert after 'Type'
        )

        # return the dataframe
        return df

def ReadSpikesFile(metadata, blk):
    '''
    Read in spikes identified by spike sorting with tridesclous.
    '''

    if metadata['tridesclous_file'] is None or metadata['tridesclous_channels'] is None:

        return None

    else:

        # parse the file and create a dataframe
        df = pd.read_csv(abs_path(metadata, 'tridesclous_file'), names = ['index', 'label'])

        # drop clusters with negative labels
        df = df[df['label'] >= 0]

        if metadata['tridesclous_merge']:
            # merge some clusters and drop all others
            new_labels = []
            for clusters_to_merge in metadata['tridesclous_merge']:
                new_label = clusters_to_merge[0]
                new_labels.append(new_label)
                df.loc[df['label'].isin(clusters_to_merge), 'label'] = new_label
            df = df[df['label'].isin(new_labels)]

        # return the dataframe
        return df

def CreateNeoEpochsFromDataframe(dataframe, metadata, file_origin):
    '''

    '''

    epochs_list = []

    # keep only rows with a positive duration
    dataframe = dataframe[dataframe['Duration (s)'] > 0]

    # group epochs by type
    for type_name, df in dataframe.groupby('Type'):

        # create a Neo Epoch for each type
        epoch = neo.Epoch(
            name = type_name,
            file_origin = file_origin,
            times = df['Start (s)'].values * pq.s,
            durations = df['Duration (s)'].values * pq.s,
            labels = df['Label'].values,
        )

        epochs_list.append(epoch)

    # return the list of Neo Epochs
    return epochs_list

def CreateNeoEventsFromDataframe(dataframe, metadata, file_origin):
    '''

    '''

    events_list = []

    # group events by type
    for type_name, df in dataframe.groupby('Type'):

        # create a Neo Event for each type
        event = neo.Event(
            name = type_name,
            file_origin = file_origin,
            times = df['Start (s)'].values * pq.s,
            labels = df['Label'].values,
        )

        events_list.append(event)

    # return the list of Neo Events
    return events_list

def CreateNeoSpikeTrainsFromDataframe(dataframe, metadata, t_start, t_stop, sampling_period):
    '''

    '''

    spikes_list = []

    # group spikes by cluster label
    for spike_label, df in dataframe.groupby('label'):

        # look up the channels that this unit was found on
        channels = metadata['tridesclous_channels'][spike_label]

        # create a Neo SpikeTrain for each cluster label
        st = neo.SpikeTrain(
            name = str(spike_label),
            file_origin = abs_path(metadata, 'tridesclous_file'),
            channels = channels, # custom annotation
            amplitude = None,    # custom annotation
            times = t_start + sampling_period * df['index'].values,
            t_start = t_start,
            t_stop = t_stop,
        )

        spikes_list.append(st)

    return spikes_list

def ApplyFilters(metadata, blk):
    '''

    '''

    if metadata['filters'] is not None:

        signalNameToIndex = {sig.name:i for i, sig in enumerate(blk.segments[0].analogsignals)}

        for sig_filter in metadata['filters']:

            index = signalNameToIndex.get(sig_filter['channel'], None)
            if index is None:

                print('Warning: skipping filter with channel name {} because channel was not found!'.format(sig_filter['channel']))

            else:

                high = sig_filter.get('highpass', None)
                low  = sig_filter.get('lowpass',  None)
                if high:
                    high *= pq.Hz
                if low:
                    low  *= pq.Hz
                blk.segments[0].analogsignals[index] = elephant.signal_processing.butter(  # may raise a FutureWarning
                    signal = blk.segments[0].analogsignals[index],
                    highpass_freq = high,
                    lowpass_freq  = low,
                )

    return blk

def RunAmplitudeDiscriminators(metadata, blk):
    '''

    '''

    spikes_list = []

    if metadata['amplitude_discriminators'] is not None:

        signalNameToIndex = {sig.name:i for i, sig in enumerate(blk.segments[0].analogsignals)}

        # classify spikes by amplitude
        for discriminator in metadata['amplitude_discriminators']:

            index = signalNameToIndex.get(discriminator['channel'], None)
            if index is None:

                print('Warning: skipping amplitude discriminator with channel name {} because channel was not found!'.format(discriminator['channel']))

            else:

                sig = blk.segments[0].analogsignals[index]
                spikes_above_min = elephant.spike_train_generation.peak_detection(sig, discriminator['amplitude'][0]*pq.uV, 'above', 'raw')
                spikes_above_max = elephant.spike_train_generation.peak_detection(sig, discriminator['amplitude'][1]*pq.uV, 'above', 'raw')
                spikes_between_min_and_max = np.setdiff1d(spikes_above_min, spikes_above_max)

                st = neo.SpikeTrain(
                    name = discriminator['name'],
                    channels = [discriminator['channel']],  # custom annotation
                    amplitude = discriminator['amplitude'], # custom annotation
                    times = spikes_between_min_and_max * pq.s,
                    t_start = sig.t_start,
                    t_stop  = sig.t_stop,
                )

                if 'epoch' in discriminator:

                    time_masks = []
                    if isinstance(discriminator['epoch'], str):
                        # search for matching epochs
                        ep = next((ep for ep in blk.segments[0].epochs if ep.name == discriminator['epoch']), None)
                        if ep is not None:
                            # select spike times that fall within each epoch
                            for t_start, duration in zip(ep.times, ep.durations):
                                t_stop = t_start + duration
                                time_masks.append((t_start <= st) & (st < t_stop))
                        else:
                            # no matching epochs found
                            time_masks.append([False] * len(st))
                    else:
                        # will eventually implement lists of ordered pairs, but
                        # for now raise an error
                        raise ValueError('amplitude discriminator epoch could not be handled: {}'.format(discriminator['epoch']))

                    # select the subset of spikes that fall within the epoch
                    # windows
                    st = st[np.any(time_masks, axis=0)]

                spikes_list.append(st)

    return spikes_list
