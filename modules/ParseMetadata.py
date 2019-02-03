#!/usr/bin/env python

'''
Import metadata about experimental data
'''

import os
import re
import yaml
import ipywidgets

def _defaults_for_key(key):
    '''

    '''

    defaults = {
        # store the key with the metadata
        'key': key,

        # description of data set
        'description': None,

        # the relative path of the directory containing the data
        'data_dir': None,

        # the ephys data file
        'data_file': None,

        # digital filters to apply before analysis and plotting
        # 0 <= highpass <= lowpass < sample_rate/2
        # - e.g. [{'channel': 'Channel A', 'highpass': 0, 'lowpass': 50}, ...]
        'filters': None,

        # the annotations file
        'annotations_file': None,

        # the epoch encoder file
        'epoch_encoder_file': None,

        # list of labels for epoch encoder
        'epoch_encoder_possible_labels': ['Type 1', 'Type 2', 'Type 3'],

        # list of dicts giving name, channel, amplitude window, epoch window for each unit
        # - e.g. [{'name': 'Unit X', 'channel': 'Channel A', 'amplitude': [75, 150], 'epoch': 'Type 1'}, ...]
        'amplitude_discriminators': None,

        # the output file of a tridesclous spike sorting analysis
        'tridesclous_file': None,

        # dict mapping spike ids to lists of channel indices
        # - e.g. {0: ['Channel A'], 1: ['Channel A'], ...} to indicate clusters 0 and 1 are both on channel A
        # - e.g. {0: ['Channel A', 'Channel B'], ...} to indicate cluster 0 is on both channels A and B
        'tridesclous_channels': None,

        # list of lists of spike ids specifying how to merge clusters
        # - e.g. [[0, 1, 2], [3, 4]] to merge clusters 1 and 2 into 0, merge 4 into 3, and discard all others
        # - e.g. [[0], [1], [2], [3], [4]] to keep clusters 0-4 as they are and discard all others
        'tridesclous_merge': None,

        # the video file
        'video_file': None,

        # the video time offset in seconds
        'video_offset': None,

        # list the channels in the order they should be plotted
        # - e.g. [{'channel': 'Channel A', 'ylabel': 'My channel', 'ylim': [-120, 120], 'units': 'uV'}, ...]
        'plots': None,
    }

    return defaults

def LoadMetadata(file = 'metadata.yml', local_data_root = '..'):
    '''

    '''

    # load metadata from file
    with open(file) as f:
        md = yaml.safe_load(f)

    # iterate over all data sets
    for key in md:

        # fill in missing metadata with default values
        if md[key] is None:
            md[key] = {}
        defaults = _defaults_for_key(key)
        for k in defaults:
            md[key].setdefault(k, defaults[k])

        # determine the absolute path of the local data directory
        # - if provided, use:   abs_local_data_dir
        # - otherwise, use:     local_data_root + data_dir
        if 'abs_local_data_dir' in md[key]:
            abs_local_data_dir = md[key]['abs_local_data_dir']
        elif 'data_dir' in md[key]:
            abs_local_data_dir = os.path.abspath(os.path.join(local_data_root, md[key]['data_dir']))
        else:
            raise ValueError('Neither "data_dir" nor "abs_local_data_dir" was found for "{}"'.format(key))
        abs_local_data_dir = os.path.normpath(abs_local_data_dir)
        md[key]['abs_local_data_dir'] = abs_local_data_dir

        # prepend the absolute path of the local data directory to file paths
        for file in [k for k in md[key] if k.endswith('_file')]:
            rel_file_path = md[key][file]
            if rel_file_path is not None:
                md[key][file] = os.path.normpath(os.path.join(abs_local_data_dir, rel_file_path))

    return md

class MetadataSelector(ipywidgets.Select):
    '''
    Interactive list box for Jupyter notebooks that allows the user to select
    which metadata set they would like to work with.

    >>> metadata = MetadataSelector()
    >>> display(metadata)

    After clicking on an item in the list, the selected metadata set is
    accessible at `metadata.selected_metadata`, e.g.

    >>> metadata.selected_metadata['data_file']

    A compact indexing method is implemented that allows the selected metadata
    set to be accessed directly, e.g.

    >>> metadata['data_file']
    '''

    def __init__(self, file = 'metadata.yml', local_data_root = '..', initial_selection = None):
        '''
        Initialize a new MetadataSelector. The metadata file is read at
        initialization.
        '''

        # initialize the selector
        super(ipywidgets.Select, self).__init__()

        # read the metadata file
        self.all_metadata = LoadMetadata(file, local_data_root)

        # create display text for the selector from keys and descriptions
        longest_key_length = max([len(k) for k in self.all_metadata.keys()])
        self.options = [(k.ljust(longest_key_length + 4) + str(self.all_metadata[k]['description'] if self.all_metadata[k]['description'] else ''), k) for k in self.all_metadata.keys()]

        # validate and set initial selection
        if initial_selection is None:
            self.value = list(self.all_metadata)[0]
        elif initial_selection not in self.all_metadata:
            raise ValueError('{} was not found in {}'.format(initial_selection, file))
        else:
            self.value = initial_selection

        # set other selector display options
        self.description = 'Data set:'
        self.rows = 10
        self.layout = ipywidgets.Layout(width = '100%')
        self.style = {'description_width': 'initial'}

        # configure the _on_select function to be called whenever the selection changes
        self.observe(self._on_select, names = 'value')
        self._on_select({'new': self.value}) # run now on initial selection

    def _on_select(self, change):
        '''
        Run each time the selection changes.
        '''

        # warn if video_offset is not set
        if self.selected_metadata['video_offset'] is None:
            print('Warning: Video sync may be incorrect! video_offset not set for {}'.format(self.value))

    @property
    def selected_metadata(self):
        '''
        The access point for the selected metadata set.
        '''
        return self.all_metadata[self.value]

    def __iter__(self, *args):
        '''
        Pass-through method for using __iter__ on the selected metadata set.
        '''
        return self.selected_metadata.__iter__(*args)

    def __getitem__(self, *args):
        '''
        Pass-through method for using __getitem__ on the selected metadata set.
        '''
        return self.selected_metadata.__getitem__(*args)

    def __setitem__(self, *args):
        '''
        Pass-through method for using __setitem__ on the selected metadata set.
        '''
        return self.selected_metadata.__setitem__(*args)

    def __delitem__(self, *args):
        '''
        Pass-through method for using __delitem__ on the selected metadata set.
        '''
        return self.selected_metadata.__delitem__(*args)

    def get(self, *args):
        '''
        Pass-through method for using get() on the selected metadata set.
        '''
        return self.selected_metadata.get(*args)

    def setdefault(self, *args):
        '''
        Pass-through method for using setdefault() on the selected metadata set.
        '''
        return self.selected_metadata.setdefault(*args)
