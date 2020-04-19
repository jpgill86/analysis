# -*- coding: utf-8 -*-
"""
Tools for working with Neo objects
"""


import numpy as np
import neo
import elephant
from pylttb import lttb
import neurotic
from neurotic.gui.config import _neo_epoch_to_dataframe


class CausalAlphaKernel(neurotic._elephant_tools.CausalAlphaKernel, elephant.kernels.Kernel):
    # add elephant.kernels.Kernel as a parent class of CausalAlphaKernel so
    # that it is usable with elephant.statistics.instantaneous_rate, which
    # checks that the kernel is a subclass
    pass

def DownsampleNeoSignal(sig, decimation_factor):
    """

    """

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

def BehaviorsDataFrame(neo_epochs, behavior_query, subepoch_queries):
    """

    """

    # filter epochs to obtain the behaviors
    df = _neo_epoch_to_dataframe(neo_epochs)
    df = df.rename(columns={'Start (s)': 'Start', 'End (s)': 'End', 'Duration (s)': 'Duration'})
    df = df.query(behavior_query)
    df = df.rename(columns={'Start': 'Start (s)', 'End': 'End (s)', 'Duration': 'Duration (s)'})

    # add defaults for subepoch columns
    for col_prefix in subepoch_queries:
        df[col_prefix+' start (s)'] = np.nan
        df[col_prefix+' end (s)'] = np.nan
        df[col_prefix+' duration (s)'] = np.nan
        df[col_prefix+' type'] = ''
        df[col_prefix+' label'] = ''

    # for every behavior, identify other epochs that belong to it
    df2 = _neo_epoch_to_dataframe(neo_epochs)
    df2 = df2.rename(columns={'Start (s)': 'Start', 'End (s)': 'End', 'Duration (s)': 'Duration'})
    for i in df.index:

        # these variables are accessible within queries when the
        # @ symbol appears before their names, e.g. @behavior_start
        behavior_start    = df.loc[i, 'Start (s)']
        behavior_end      = df.loc[i, 'End (s)']
        behavior_duration = df.loc[i, 'Duration (s)']
        behavior_type     = df.loc[i, 'Type']
        behavior_label    = df.loc[i, 'Label']

        for col_prefix, query in subepoch_queries.items():

            # the query string may optionally be paired (in a tuple) with a
            # string, either 'first' or 'last', which indicates how to handle
            # multiple matching epochs -- if no such string is provided,
            # multiple matches will raise an exception
            if isinstance(query, tuple):
                query, position = query
            else:
                position = None

            df3 = df2.query(query)

            if len(df3) == 0:
                # skip if there are no matches
                continue
            elif len(df3) == 1 or position == 'first':
                matching_epoch = df3.iloc[0]
            elif position == 'last':
                matching_epoch = df3.iloc[-1]
            else:
                # error if there are multiple matches and a method for handling
                # them was not explicitly specified
                raise Exception(f'More than one epoch was found for the ' \
                                f'behavior spanning [{behavior_start}, ' \
                                f'{behavior_end}] that matches this query: ' \
                                f'{query}')

            df.loc[i, col_prefix+' start (s)'] = matching_epoch['Start']
            df.loc[i, col_prefix+' end (s)'] = matching_epoch['End']
            df.loc[i, col_prefix+' duration (s)'] = matching_epoch['Duration']
            df.loc[i, col_prefix+' type'] = matching_epoch['Type']
            df.loc[i, col_prefix+' label'] = matching_epoch['Label']

    return df
