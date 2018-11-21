#!/usr/bin/env python

'''
Import metadata about experimental data
'''

import os
import re
import yaml
import ipywidgets

def _defaults_for_key(key, data_root_dir):
    '''

    '''

    # key should have the form 'YYYY-MM-DD_TAG 000'
    prefix, _ = key.split()
    year = prefix[:4]

    defaults = {
        # store the key with the metadata
        'key': key,

        # description of data set
        'description': None,

        # the directory containing the data
        'data_dir': os.path.join(data_root_dir, year, prefix),

        # the AxoGraph data file (regex)
        'data_file': key + '.axgd',

        # digital filters to apply before analysis and plotting
        # 0 <= highpass <= lowpass < sample_rate/2
        # - e.g. [{'channel': 'Channel A', 'highpass': 0, 'lowpass': 50}, ...]
        'filters': None,

        # the annotations file (regex)
        'annotations_file': key + ' ANNOTATIONS.csv',

        # the epoch encoder file (regex)
        'epoch_encoder_file': key + ' EPOCH-ENCODER.csv',

        # list of labels for epoch encoder
        'epoch_encoder_possible_labels': ['Type 1', 'Type 2', 'Type 3'],

        # list of dicts giving name, channel, amplitude window, epoch window for each unit
        # - e.g. [{'name': 'Unit X', 'channel': 'Channel A', 'amplitude': [75, 150], 'epoch': 'Type 1'}, ...]
        'amplitude_discriminators': None,

        # the output file of a tridesclous spike sorting analysis (regex)
        'tridesclous_file': key + ' SPIKES.csv',

        # dict mapping spike ids to lists of channel indices
        # - e.g. {0: ['Channel A'], 1: ['Channel A'], ...} to indicate clusters 0 and 1 are both on channel A
        # - e.g. {0: ['Channel A', 'Channel B'], ...} to indicate cluster 0 is on both channels A and B
        'tridesclous_channels': None,

        # list of lists of spike ids specifying how to merge clusters
        # - e.g. [[0, 1, 2], [3, 4]] to merge clusters 1 and 2 into 0, merge 4 into 3, and discard all others
        # - e.g. [[0], [1], [2], [3], [4]] to keep clusters 0-4 as they are and discard all others
        'tridesclous_merge': None,

        # the video file (regex)
        'video_file': key + '.(mp4|mov)',

        # the video time offset in seconds
        'video_offset': None,

        # list the channels in the order they should be plotted
        # - e.g. [{'channel': 'Channel A', 'ylabel': 'My channel', 'ylim': [-120, 120], 'units': 'uV'}, ...]
        'plots': None,
    }

    return defaults

def LoadMetadata(file = 'metadata.yml', data_root_dir = '..'):
    '''

    '''

    # load metadata from file
    md = yaml.safe_load(open(file))

    # fill in missing metadata with default values
    for key in md:
        if md[key] is None:
            md[key] = {}
        defaults = _defaults_for_key(key, data_root_dir)
        for k in defaults:
            md[key].setdefault(k, defaults[k])

    # check for missing files and construct file paths
    md_with_file_paths = md.copy()
    for key in md:
        dir = md[key]['data_dir']
        if not os.path.isdir(dir):
            # delete entries for which data_dir cannot be found
            print('Removing "{}" because directory is missing: "{}"'.format(key, dir))
            del md_with_file_paths[key]
        else:
            # prepend data_dir to file paths unless None was explicitly given
            for file in [k for k in md[key] if k.endswith('_file')]:
                regex = md[key][file]
                if regex is not None:
                    matching_files = [file for file in os.listdir(dir) if re.fullmatch(regex, file)]
                    md_with_file_paths[key][file] = os.path.join(dir, matching_files[0]) if matching_files else None

    return md_with_file_paths

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

    def __init__(self, file = 'metadata.yml', data_root_dir = '..', initial_selection = None):
        '''
        Initialize a new MetadataSelector. The metadata file is read at
        initialization.
        '''

        # initialize the selector
        super(ipywidgets.Select, self).__init__()

        # read the metadata file
        self.all_metadata = LoadMetadata(file, data_root_dir)

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
