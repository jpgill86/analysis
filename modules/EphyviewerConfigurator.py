#!/usr/bin/env python

'''

'''

from collections import OrderedDict
from functools import wraps

import numpy as np
import quantities as pq
import ephyviewer
import ipywidgets

from ParseMetadata import abs_path
from NeoUtilities import EstimateVideoJumpTimes, NeoEpochToDataFrame
from MyWritableEpochSource import MyWritableEpochSource

pq.mN = pq.UnitQuantity('millinewton', pq.N/1e3, symbol = 'mN');  # define millinewton

def _fix_FrameGrabber_set_file(set_file_func):
    '''
    For some video files, ephyviewer sets the incorrect start_time for its
    FrameGrabber when the set_file method is called. This monkey patch works
    around the problem by resetting start_time to 0 after set_file is called.
    '''
    @wraps(set_file_func)
    def wrapper(*args, **kwargs):
        result = set_file_func(*args, **kwargs)
        frame_grabber = args[0]
        frame_grabber.start_time = 0
        return result
    return wrapper
ephyviewer.FrameGrabber.set_file = _fix_FrameGrabber_set_file(ephyviewer.FrameGrabber.set_file)

def defaultKeepSignal(sig):
    '''

    '''
    return (not sig.name.startswith('Analog Input #')) and (sig.name != 'Clock')

def defaultUnits(sig):
    '''

    '''

    mapping = {
        'V': 'uV', # convert voltages to microvolts
        'N': 'mN', # convert forces to millinewtons
    }
    mapping = {pq.Quantity(1, k).dimensionality.simplified: v for k, v in mapping.items()}
    return mapping.get(sig.units.dimensionality.simplified, sig.units)

def defaultYLim(sig):
    '''

    '''

    mapping = {
        'V': [-120, 120], # plot range for voltages
        'N': [ -10, 300], # plot range for forces
    }
    mapping = {pq.Quantity(1, k).dimensionality.simplified: v for k, v in mapping.items()}
    return mapping.get(sig.units.dimensionality.simplified, [-1, 1])

def setDefaultsForPlots(metadata, blk):
    '''

    '''

    sigs = blk.segments[0].analogsignals
    signalNameToIndex = {sig.name:i for i, sig in enumerate(sigs)}

    if metadata['plots'] is None:
        metadata['plots'] = [{'channel': sig.name} for sig in sigs if defaultKeepSignal(sig)]

    plots = []
    for plot in metadata['plots']:
        index = signalNameToIndex.get(plot['channel'], None)
        if index is None:
            print('Warning: removing plot with channel name "{}" because channel was not found in blk!'.format(plot['channel']))
        else:
            plot['index'] = index
            plot.setdefault('units',  defaultUnits(sigs[index]))
            plot.setdefault('ylim',   defaultYLim(sigs[index]))
            plot.setdefault('ylabel', sigs[index].name)
            plots.append(plot)
    metadata['plots'] = plots

    return metadata['plots']

class EphyviewerConfigurator(ipywidgets.HBox):
    '''

    '''

    _toggle_button_defaults = OrderedDict([
        ('traces',        {'value': True,  'icon': 'line-chart',   'description': 'Traces'}),
        ('traces_rauc',   {'value': False, 'icon': 'area-chart',   'description': 'RAUC'}),
        # ('freqs',         {'value': False, 'icon': 'wifi',         'description': 'Frequencies'}),
        ('spike_trains',  {'value': True,  'icon': 'barcode',      'description': 'Spike Trains'}),
        ('epochs',        {'value': True,  'icon': 'align-left',   'description': 'Read-Only Epochs'}),
        ('epoch_encoder', {'value': True,  'icon': 'align-left',   'description': 'Epoch Encoder'}),
        ('video',         {'value': True,  'icon': 'youtube-play', 'description': 'Video'}),
        ('event_list',    {'value': True,  'icon': 'list',         'description': 'Events'}),
        ('data_frame',    {'value': False, 'icon': 'table',        'description': 'Annotation Table'}),
    ])

    def __init__(self, metadata, blk, rauc_sigs = None, lazy = False):
        '''

        '''

        self.metadata = metadata
        self.blk = blk
        self.rauc_sigs = rauc_sigs
        self.lazy = lazy

        # initialize the box
        super(ipywidgets.HBox, self).__init__()

        # create buttons for controlling which elements to show
        self.controls = OrderedDict()
        for name, kwargs in self._toggle_button_defaults.items():
            self.controls[name] = ipywidgets.ToggleButton(**kwargs)
        controls_vbox = ipywidgets.VBox(list(self.controls.values()))

        # permanently disable controls for which inputs are missing
        if not self.rauc_sigs:
            self.controls['traces_rauc'].value = False
            self.controls['traces_rauc'].disabled = True
            self.controls['traces_rauc'].tooltip = 'Cannot enable because rauc_sigs is empty'
        if not self.blk.segments[0].spiketrains:
            self.controls['spike_trains'].value = False
            self.controls['spike_trains'].disabled = True
            self.controls['spike_trains'].tooltip = 'Cannot enable because there are no spike trains'
        if not [ep for ep in self.blk.segments[0].epochs if ep.size > 0 and '(from epoch encoder file)' not in ep.labels]:
            self.controls['epochs'].value = False
            self.controls['epochs'].disabled = True
            self.controls['epochs'].tooltip = 'Cannot enable because there are no read-only epochs'
            self.controls['data_frame'].value = False
            self.controls['data_frame'].disabled = True
            self.controls['data_frame'].tooltip = 'Cannot enable because there are no read-only epochs'
            if not [ev for ev in self.blk.segments[0].events if ev.size > 0]:
                self.controls['event_list'].value = False
                self.controls['event_list'].disabled = True
                self.controls['event_list'].tooltip = 'Cannot enable because there are no read-only epochs or events'
        if not self.metadata['epoch_encoder_file']:
            self.controls['epoch_encoder'].value = False
            self.controls['epoch_encoder'].disabled = True
            self.controls['epoch_encoder'].tooltip = 'Cannot enable because epoch_encoder_file is not set'
        if not self.metadata['video_file']:
            self.controls['video'].value = False
            self.controls['video'].disabled = True
            self.controls['video'].tooltip = 'Cannot enable because video_file is not set'

        # create the launch button
        self.launch_button = ipywidgets.Button(icon='rocket', description='Launch', layout=ipywidgets.Layout(height='auto'))
        self.launch_button.on_click(self._on_launch_clicked)

        # populate the box
        self.children = [controls_vbox, self.launch_button]

        # warn about potential video sync problems
        if metadata['video_file'] is not None and metadata['video_offset'] is None:
            print('WARNING: Your video will likely be out of sync with your')
            print('data because video_offset is unspecified! Consider adding')
            print('it to your metadata.')
        if metadata['video_file'] is not None and metadata['video_jumps'] is None:
            approx_video_jumps = EstimateVideoJumpTimes(blk)
            if approx_video_jumps:
                print('WARNING: It seems that AxoGraph was paused at least once')
                print('during data acquisition, but video_jumps is unspecified.')
                print('This will cause your video and data to get out of sync.')
                print('Consider adding the following to your metadata:')
                print('    video_jumps:')
                for t, dur in approx_video_jumps:
                    print(f'        - [{t}, {dur}]')
                print('Each ordered pair specifies the timing of a pause and')
                print('approximately how long the pause lasted in seconds. The')
                print('pause durations are only rough estimates +/- a second! You')
                print('should refine them by inspecting the video to make sure')
                print('your sync is accurate!')

    def is_enabled(self, name):
        '''

        '''
        if name in self.controls:
            return self.controls[name].value
        else:
            return False

    def enable(self, name):
        '''

        '''
        self.controls[name].value = True

    def disable(self, name):
        '''

        '''
        self.controls[name].value = False

    def enable_all(self):
        for name in self.controls:
            if not self.controls[name].disabled:
                self.enable(name)

    def disable_all(self):
        for name in self.controls:
            self.disable(name)

    def _on_launch_clicked(self, button):
        self.launch_ephyviewer()

    def launch_ephyviewer(self):
        '''

        '''

        app = ephyviewer.mkQApp()
        win = self.create_ephyviewer_window()
        win.show()
        app.exec_()

    def create_ephyviewer_window(self):
        '''

        '''

        ########################################################################
        # DATA SOURCES

        seg = self.blk.segments[0]
        sigs = seg.analogsignals

        sources = {'signal': [], 'epoch': [], 'event': [], 'spike': []}
        sources['epoch'].append(ephyviewer.NeoEpochSource(seg.epochs))
        sources['event'].append(ephyviewer.NeoEventSource(seg.events))
        sources['spike'].append(ephyviewer.NeoSpikeTrainSource(seg.spiketrains))

        # filter epoch encoder data out of read-only epoch and event lists
        # so they are not presented multiple times, and remove empty channels
        sources['epoch'][0].all = [ep for ep in sources['epoch'][0].all if len(ep['time']) > 0 and '(from epoch encoder file)' not in ep['label']]
        sources['event'][0].all = [ev for ev in sources['event'][0].all if len(ev['time']) > 0 and '(from epoch encoder file)' not in ev['label']]

        ########################################################################
        # WINDOW

        # create a window that will be populated with viewers
        win = ephyviewer.MainViewer(
            # settings_name='test2', # remember settings (e.g. xsize) between sessions
            show_auto_scale = False,
            global_xsize_zoom = True,
            play_interval = 0.1, # refresh period in seconds
        )
        win.setWindowTitle(self.metadata['key'])

        ########################################################################
        # PREPARE TRACE PARAMETERS

        setDefaultsForPlots(self.metadata, self.blk)

        plotNameToIndex = {p['channel']:i for i, p in enumerate(self.metadata['plots'])}

        ########################################################################
        # PREPARE SCATTER PLOT PARAMETERS

        if not self.lazy:
            all_times = sigs[0].times.rescale('s').magnitude # assuming all AnalogSignals have the same sampling rate and start time
            spike_indices = {}
            spike_channels = {}
            for st in seg.spiketrains:
                if 'channels' in st.annotations:
                    c = []
                    for channel in st.annotations['channels']:
                        index = plotNameToIndex.get(channel, None)
                        if index is None:
                            print('Note: Spike train {} will not be plotted on channel {} because that channel isn\'t being plotted'.format(st.name, channel))
                        else:
                            c.append(index)
                    if c:
                        spike_channels[st.name] = c
                        spike_indices[st.name] = np.where(np.isin(all_times, st.times.magnitude))[0]

        ########################################################################
        # TRACES WITH SCATTER PLOTS

        if self.is_enabled('traces'):

            if self.lazy:
                import neo
                neorawio = neo.rawio.AxographRawIO(abs_path(self.metadata, 'data_file')) # TODO detect correct RawIO automatically
                neorawio.parse_header()
                channel_indexes = [p['index'] for p in self.metadata['plots']]
                sources['signal'].append(ephyviewer.AnalogSignalFromNeoRawIOSource(neorawio, channel_indexes))
                # TODO apply ylabels
                # TODO support scatter
            else:
                sources['signal'].append(ephyviewer.AnalogSignalSourceWithScatter(
                    signals = np.concatenate([sigs[p['index']].magnitude for p in self.metadata['plots']], axis = 1),
                    sample_rate = sigs[0].sampling_rate, # assuming all AnalogSignals have the same sampling rate
                    t_start = sigs[0].t_start,           # assuming all AnalogSignals start at the same time
                    channel_names = [p['ylabel'] for p in self.metadata['plots']],
                    scatter_indexes = spike_indices,
                    scatter_channels = spike_channels,
                ))

            trace_view = ephyviewer.TraceViewer(source = sources['signal'][0], name = 'signals')
            trace_view.params['scatter_size'] = 5

            win.add_view(trace_view)

            trace_view.params['display_labels'] = True

            # select a color scheme
            trace_view.params_controller.combo_cmap.setCurrentText('Accent')
            trace_view.params_controller.on_automatic_color()

            # adjust plot range, scaling, and positioning
            trace_view.params['ylim_max'] = 0.5
            trace_view.params['ylim_min'] = -trace_view.source.nb_channel + 0.5
            trace_view.params['scale_mode'] = 'by_channel'
            for i, p in enumerate(self.metadata['plots']):
                sig_units = sigs[p['index']].units
                units_ratio = (pq.Quantity(1, p['units'])/pq.Quantity(1, sig_units)).simplified
                assert units_ratio.dimensionality.string == 'dimensionless', f"Channel \"{p['channel']}\" has units {sig_units} and cannot be converted to {p['units']}"
                ylim_span = np.ptp(p['ylim'] * units_ratio.magnitude)
                ylim_center = np.mean(p['ylim'] * units_ratio.magnitude)
                trace_view.by_channel_params['ch{}'.format(i), 'gain'] = 1/ylim_span # rescale [ymin,ymax] across a unit
                trace_view.by_channel_params['ch{}'.format(i), 'offset'] = -i - ylim_center/ylim_span # center [ymin,ymax] within the unit

        ########################################################################
        # TRACES OF RAUC

        if self.is_enabled('traces_rauc') and self.rauc_sigs is not None:

            sig_rauc_source = ephyviewer.InMemoryAnalogSignalSource(
                signals = np.concatenate([self.rauc_sigs[p['index']].as_array() for p in self.metadata['plots']], axis = 1),
                sample_rate = self.rauc_sigs[0].sampling_rate, # assuming all AnalogSignals have the same sampling rate
                t_start = self.rauc_sigs[0].t_start,           # assuming all AnalogSignals start at the same time
                channel_names = [p['ylabel'] + ' RAUC' for p in self.metadata['plots']],
            )
            sources['signal_rauc'] = [sig_rauc_source]

            trace_rauc_view = ephyviewer.TraceViewer(source = sources['signal_rauc'][0], name = 'signals rauc')

            if 'signals' in win.viewers:
                win.add_view(trace_rauc_view, tabify_with = 'signals')
            else:
                win.add_view(trace_rauc_view)

            trace_rauc_view.params['display_labels'] = True
            trace_rauc_view.params['display_offset'] = True

            # select a color scheme
            trace_rauc_view.params_controller.combo_cmap.setCurrentText('Accent')
            trace_rauc_view.params_controller.on_automatic_color()

            # adjust plot range
            trace_rauc_view.params['ylim_max'] = 0.5
            trace_rauc_view.params['ylim_min'] = -trace_rauc_view.source.nb_channel + 0.5
            trace_rauc_view.params['scale_mode'] = 'by_channel'
            for i, p in enumerate(self.metadata['plots']):
                ylim_span = np.median(self.rauc_sigs[p['index']].magnitude) * 10
                ylim_center = ylim_span / 2
                trace_rauc_view.by_channel_params['ch{}'.format(i), 'gain'] = 1/ylim_span # rescale [ymin,ymax] across a unit
                trace_rauc_view.by_channel_params['ch{}'.format(i), 'offset'] = -i - ylim_center/ylim_span # center [ymin,ymax] within the unit

        ########################################################################
        # FREQUENCY (EXPERIMENTAL AND COMPUTATIONALLY EXPENSIVE!)

        if self.is_enabled('freqs'):

            freq_view = ephyviewer.TimeFreqViewer(source = trace_view.source, name = 'timefreqs')

            freq_view.params['scale_mode'] = 'by_channel'
            freq_view.params['nb_column'] = 1
            freq_view.params['colormap'] = 'gray'
            freq_view.params.param('timefreq')['deltafreq'] = 100
            freq_view.params.param('timefreq')['f_start'] = 1
            freq_view.params.param('timefreq')['f_stop'] = 1500

            freq_view.by_channel_params['ch0', 'visible'] = False
            freq_view.by_channel_params['ch1', 'visible'] = True
            freq_view.by_channel_params['ch2', 'visible'] = True
            freq_view.by_channel_params['ch3', 'visible'] = True
            freq_view.by_channel_params['ch4', 'visible'] = False

            # freq_view.params.param('timefreq')['normalisation'] = 1.5
            freq_view.by_channel_params['ch1', 'clim'] = 3
            freq_view.by_channel_params['ch2', 'clim'] = 5
            freq_view.by_channel_params['ch3', 'clim'] = 10

            if 'signals' in win.viewers:
                win.add_view(freq_view, tabify_with = 'signals')
            elif 'signals rauc' in win.viewers:
                win.add_view(freq_view, tabify_with = 'signals rauc')
            else:
                win.add_view(freq_view)

        ########################################################################
        # SPIKE TRAINS

        if self.is_enabled('spike_trains') and sources['spike'][0].nb_channel > 0:

            spike_train_view = ephyviewer.SpikeTrainViewer(source = sources['spike'][0], name = 'spiketrains')
            win.add_view(spike_train_view)

            # select a color scheme
            spike_train_view.params_controller.combo_cmap.setCurrentText('Accent')
            spike_train_view.params_controller.on_automatic_color()

        ########################################################################
        # EPOCHS

        if self.is_enabled('epochs') and sources['epoch'][0].nb_channel > 0:

            epoch_view = ephyviewer.EpochViewer(source = sources['epoch'][0], name = 'epochs')
            win.add_view(epoch_view)

            # select a color scheme
            epoch_view.params_controller.combo_cmap.setCurrentText('Accent')
            epoch_view.params_controller.on_automatic_color()

        ########################################################################
        # EPOCH ENCODER

        if self.is_enabled('epoch_encoder') and self.metadata['epoch_encoder_file'] is not None:

            writable_epoch_source = MyWritableEpochSource(
                filename = abs_path(self.metadata, 'epoch_encoder_file'),
                possible_labels = self.metadata['epoch_encoder_possible_labels'],
            )

            epoch_encoder = ephyviewer.EpochEncoder(source = writable_epoch_source, name = 'epoch encoder')
            epoch_encoder.params['exclusive_mode'] = False
            win.add_view(epoch_encoder)

        ########################################################################
        # VIDEO

        if self.is_enabled('video') and self.metadata['video_file'] is not None:

            video_source = ephyviewer.MultiVideoFileSource(video_filenames = [abs_path(self.metadata, 'video_file')])
            if self.metadata['video_offset'] is not None:
                video_source.t_starts[0] += self.metadata['video_offset']
                video_source.t_stops[0]  += self.metadata['video_offset']
                video_source._t_start = max(min(video_source.t_starts), 0)
                video_source._t_stop  = max(video_source.t_stops)

            if self.metadata['video_jumps'] is not None:

                # create an unmodified video_times vector with evenly spaced times
                video_times = np.arange(video_source.nb_frames[0])/video_source.rates[0] + video_source.t_starts[0]

                # insert repeating times at pause_start to fill pause_duration
                # so that that section of the video is skipped over
                for pause_start, pause_duration in self.metadata['video_jumps']:
                    pause_start_index = np.searchsorted(video_times, pause_start)
                    pause_fill = video_times[pause_start_index] * np.ones(int(np.round(pause_duration*video_source.rates[0])))
                    video_times = np.insert(video_times, pause_start_index, pause_fill)
                    video_times = video_times[:video_source.nb_frames[0]]

                # add the modified video_times to the video_source
                video_source.video_times = [video_times]
                video_source.t_starts[0] = min(video_times)
                video_source.t_stops[0]  = max(video_times)
                video_source._t_start = max(min(video_source.t_starts), 0)
                video_source._t_stop  = max(video_source.t_stops)

            video_view = ephyviewer.VideoViewer(source = video_source, name = 'video')
            win.add_view(video_view, location = 'bottom', orientation = 'horizontal')

        ########################################################################
        # EVENTS

        if self.is_enabled('event_list') and sources['event'][0].nb_channel > 0:

            event_list = ephyviewer.EventList(source = sources['event'][0], name = 'events')
            if 'video' in win.viewers:
                win.add_view(event_list, split_with = 'video')
            else:
                win.add_view(event_list, location = 'bottom', orientation = 'horizontal')

        ########################################################################
        # DATAFRAME

        annotations_dataframe = NeoEpochToDataFrame(seg.epochs, exclude_epoch_encoder_epochs=True)
        if self.is_enabled('data_frame') and len(annotations_dataframe) > 0:

            data_frame_view = ephyviewer.DataFrameView(source = annotations_dataframe, name = 'table')
            if 'events' in win.viewers:
                win.add_view(data_frame_view, tabify_with = 'events')
            elif 'video' in win.viewers:
                win.add_view(data_frame_view, split_with = 'video')
            else:
                win.add_view(data_frame_view, location = 'bottom', orientation = 'horizontal')

        ########################################################################
        # FINAL TOUCHES

        # select first tabs
        for widget in win.children():
            if isinstance(widget, ephyviewer.PyQt5.QtWidgets.QTabBar):
                widget.setCurrentIndex(0)

        # set amount of time shown initially
        win.set_xsize(40) # seconds

        return win
