#!/usr/bin/env python

'''
Import metadata about experimental data
'''

import os
import urllib
import yaml
import ipywidgets

from Downloads import safe_download


def abs_path(metadata, file):
    '''
    Convert the relative path of file to an absolute path using data_dir
    '''
    if metadata[file] is None:
        return None
    else:
        return os.path.normpath(os.path.join(metadata['data_dir'], metadata[file]))


def abs_url(metadata, file):
    '''
    Convert the relative path of file to a full URL using remote_data_dir
    '''
    if metadata[file] is None or metadata['remote_data_dir'] is None:
        return None
    else:
        file_path = metadata[file].replace(os.sep, '/')
        url = '/'.join([metadata['remote_data_dir'], file_path])
        # url = urllib.parse.unquote(url)
        # url = urllib.parse.quote(url, safe='/:')
        return url


def is_url(url):
    '''
    Returns True only if the parameter begins with the form <scheme>://<netloc>
    '''
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def DownloadAllDataFiles(metadata):
    '''
    Download all files associated with metadata
    '''

    if not is_url(metadata['remote_data_dir']):
        print('metadata[remote_data_dir] is not a full URL')
        return

    for file in [k for k in metadata if k.endswith('_file')]:
        if metadata[file]:

            # create directories if necessary
            if not os.path.exists(os.path.dirname(abs_path(metadata, file))):
                os.makedirs(os.path.dirname(abs_path(metadata, file)))

            # download the file only if it does not already exist
            safe_download(abs_url(metadata, file), abs_path(metadata, file))


def _defaults_for_key(key):
    '''

    '''

    defaults = {
        # store the key with the metadata
        'key': key,

        # description of data set
        'description': None,

        # the path of the directory containing the data on the local system
        # - this may be an absolute or relative path, but not None since data
        #   must be located locally
        # - if it is a relative path, it will be interpreted by LoadMetadata as
        #   relative to local_data_root and will be converted to an absolute
        #   path
        'data_dir': None,

        # the path of the directory containing the data on a remote server
        # - this may be a full URL or a relative path, or None if there exists
        #   no remote data store
        # - if it is a relative path, it will be interpreted by LoadMetadata as
        #   relative to remote_data_root and will be convered to a full URL
        'remote_data_dir': None,

        # the ephys data file
        # - path relative to data_dir and remote_data_dir
        'data_file': None,

        # digital filters to apply before analysis and plotting
        # 0 <= highpass <= lowpass < sample_rate/2
        # - e.g. [{'channel': 'Channel A', 'highpass': 0, 'lowpass': 50}, ...]
        'filters': None,

        # the annotations file
        # - path relative to data_dir and remote_data_dir
        'annotations_file': None,

        # the epoch encoder file
        # - path relative to data_dir and remote_data_dir
        'epoch_encoder_file': None,

        # list of labels for epoch encoder
        'epoch_encoder_possible_labels': ['Type 1', 'Type 2', 'Type 3'],

        # list of dicts giving name, channel, amplitude window, epoch window for each unit
        # - e.g. [{'name': 'Unit X', 'channel': 'Channel A', 'amplitude': [75, 150], 'epoch': 'Type 1'}, ...]
        'amplitude_discriminators': None,

        # the output file of a tridesclous spike sorting analysis
        # - path relative to data_dir and remote_data_dir
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
        # - path relative to data_dir and remote_data_dir
        'video_file': None,

        # the video time offset in seconds
        'video_offset': None,

        # list the channels in the order they should be plotted
        # - e.g. [{'channel': 'Channel A', 'ylabel': 'My channel', 'ylim': [-120, 120], 'units': 'uV'}, ...]
        'plots': None,
    }

    return defaults

def LoadMetadata(file = 'metadata.yml', local_data_root = '.', remote_data_root = None):
    '''
    Read metadata stored in a YAML file about available collections of data,
    assign defaults to missing values, and resolve absolute paths for local
    data stores and full URLs for remote data stores.

    The "data_dir" property must be provided for every data set and specifies
    the directory on the local system containing the data files. "data_dir" may
    be an absolute path or a relative path with respect to `local_data_root`.
    If it is a relative path, it will be converted to an absolute path.

    The "remote_data_dir" property is optional and specifies the directory on a
    remote server containing the data files. "remote_data_dir" may be a full
    URL or a relative path with respect to `remote_data_root`, which must be a
    full URL. If it is a relative path, it will be converted to a full URL.

    File paths (e.g., "data_file", "video_file") are assumed to be relative to
    both "data_dir" and "remote_data_dir" (i.e., the local and remote data
    stores mirror one another) and can be resolved with `abs_path` or
    `abs_url`.
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
        if md[key]['data_dir'] is not None:
            # data_dir is either an absolute path already or is specified
            # relative to local_data_root
            if os.path.isabs(md[key]['data_dir']):
                dir = md[key]['data_dir']
            else:
                dir = os.path.abspath(os.path.join(local_data_root, md[key]['data_dir']))
        else:
            # data_dir is a required property
            raise ValueError('"data_dir" missing for "{}"'.format(key))
        md[key]['data_dir'] = os.path.normpath(dir)

        # determine the full URL to the remote data directory
        if md[key]['remote_data_dir'] is not None:
            # remote_data_dir is either a full URL already or is specified
            # relative to remote_data_root
            if is_url(md[key]['remote_data_dir']):
                url = md[key]['remote_data_dir']
            elif is_url(remote_data_root):
                url = '/'.join([remote_data_root, md[key]['remote_data_dir']])
            else:
                url = None
        else:
            # there is no remote data store
            url = None
        md[key]['remote_data_dir'] = url

    return md

class MetadataSelector(ipywidgets.VBox):
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

    def __init__(self, file = 'metadata.yml', local_data_root = '.', remote_data_root = None, initial_selection = None):
        '''
        Initialize a new MetadataSelector. The metadata file is read at
        initialization.
        '''

        # initialize the box
        super(ipywidgets.VBox, self).__init__()

        # create the selector
        self.selector = ipywidgets.Select()

        # read the metadata file
        self.all_metadata = LoadMetadata(file, local_data_root, remote_data_root)

        # create display text for the selector from keys and descriptions
        longest_key_length = max([len(k) for k in self.all_metadata.keys()])
        self.selector.options = [(k.ljust(longest_key_length + 4) + str(self.all_metadata[k]['description'] if self.all_metadata[k]['description'] else ''), k) for k in self.all_metadata.keys()]

        # validate and set initial selection
        if initial_selection is None:
            self.selector.value = list(self.all_metadata)[0]
        elif initial_selection not in self.all_metadata:
            raise ValueError('{} was not found in {}'.format(initial_selection, file))
        else:
            self.selector.value = initial_selection

        # set other selector display options
        self.selector.description = 'Data set:'
        self.selector.rows = 10
        self.selector.layout = ipywidgets.Layout(width = '99%')
        self.selector.style = {'description_width': 'initial'}

        # configure the _on_select function to be called whenever the selection changes
        self.selector.observe(self._on_select, names = 'value')
        self._on_select({'new': self.selector.value}) # run now on initial selection

        # create the download button
        # self.download_button = ipywidgets.Button(icon='download', description='Download', layout=ipywidgets.Layout(height='auto'), disabled=False)
        # self.download_button.on_click(self._on_download_clicked)

        # populate the box
        # self.children = [self.selector, self.download_button]
        self.children = [self.selector]

    def _on_select(self, change):
        '''
        Run each time the selection changes.
        '''

        # warn if video_offset is not set
        if self.selected_metadata['video_offset'] is None:
            print('Warning: Video sync may be incorrect! video_offset not set for {}'.format(self.selector.value))

    # def _on_download_clicked(self, button):
    #     '''
    #     Run each time the download button is clicked.
    #     '''
    #     DownloadAllDataFiles(self.selected_metadata)

    @property
    def selected_metadata(self):
        '''
        The access point for the selected metadata set.
        '''
        return self.all_metadata[self.selector.value]

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
