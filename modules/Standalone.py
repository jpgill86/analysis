#!/usr/bin/env python

'''

'''

import quantities as pq
import elephant
from ephyviewer import QT

from ParseMetadata import LoadMetadata, _selector_labels
from ImportData import LoadAndPrepareData
from EphyviewerConfigurator import EphyviewerConfigurator

class DataExplorer(QT.QMainWindow):

    def __init__(self, lazy=True, projector_mode=False, support_increased_line_width=False):

        QT.QMainWindow.__init__(self)

        self.setWindowTitle('Data Explorer')
        self.resize(600, 300)

        # lazy loading using Neo RawIO
        self.lazy = lazy

        # - projector_mode=False uses "dark mode" colors (light traces on a
        #   dark background), which look good on screens
        # - projector_mode=True uses "light mode" colors (dark traces on a
        #   light background), which show up better on projectors, and
        #   antialiasing is turned on
        self.projector_mode = projector_mode

        # support_increased_line_width=True eliminates the extremely poor
        # performance associated with TraceViewer's line_width > 1.0, but it
        # also degrades overall performance somewhat and uses a mode of
        # pyqtgraph that is reportedly unstable
        self.support_increased_line_width = support_increased_line_width

        # windows are appended to this list so that they persist after the
        # function that spawned them returns
        self.windows = []

        # initialize metadata list to empty
        self.all_metadata = {}

        # metadata selector
        self.data_set_selector = QT.QListWidget()
        self.data_set_selector.setSelectionMode(QT.QListWidget.SingleSelection)
        self.data_set_selector.setStyleSheet('font: 9pt Courier;')
        self.setCentralWidget(self.data_set_selector)

        self.createMenus()

    def createMenus(self):

        self.file_menu = self.menuBar().addMenu(self.tr('&File'))

        do_open_metadata = QT.QAction('&Open metadata', self, shortcut = 'Ctrl+O')
        do_open_metadata.triggered.connect(self.open_metadata)
        self.file_menu.addAction(do_open_metadata)

        do_launch = QT.QAction('&Launch', self, shortcut = 'Return')
        do_launch.triggered.connect(self.launch)
        self.file_menu.addAction(do_launch)

        self.options_menu = self.menuBar().addMenu(self.tr('&Options'))

        do_toggle_lazy = QT.QAction('&Fast loading (disables filters, spike detection, RAUC)', self, shortcut = 'Ctrl+F')
        do_toggle_lazy.setCheckable(True)
        do_toggle_lazy.setChecked(self.lazy)
        do_toggle_lazy.triggered.connect(self.toggle_lazy)
        self.options_menu.addAction(do_toggle_lazy)

        do_toggle_projector_mode = QT.QAction('&Projector mode (dark traces on light background)', self, shortcut = 'Ctrl+P')
        do_toggle_projector_mode.setCheckable(True)
        do_toggle_projector_mode.setChecked(self.projector_mode)
        do_toggle_projector_mode.triggered.connect(self.toggle_projector_mode)
        self.options_menu.addAction(do_toggle_projector_mode)

        do_toggle_support_increased_line_width = QT.QAction('&Thick traces (worse performance)', self, shortcut = 'Ctrl+T')
        do_toggle_support_increased_line_width.setCheckable(True)
        do_toggle_support_increased_line_width.setChecked(self.support_increased_line_width)
        do_toggle_support_increased_line_width.triggered.connect(self.toggle_support_increased_line_width)
        self.options_menu.addAction(do_toggle_support_increased_line_width)

    def open_metadata(self):

        filename, _ = QT.QFileDialog.getOpenFileName(
            parent=self,
            caption='Open metadata',
            directory=None,
            filter='YAML files (*.yml *.yaml)')

        if filename:
            try:
                self.all_metadata = LoadMetadata(filename)
                if self.all_metadata:
                    self.data_set_selector.clear()
                    all_labels = _selector_labels(self.all_metadata)
                    for i, key in enumerate(self.all_metadata):
                        item = QT.QListWidgetItem(all_labels[i], self.data_set_selector)
                        item.setData(QT.StatusTipRole, key) # use of StatusTipRole is hacky
            except AssertionError as e:
                print('Bad metadata file!', e)

    def launch(self):

        try:
            key = self.data_set_selector.currentItem().data(QT.StatusTipRole)
        except AttributeError:
            # nothing selected yet
            return

        metadata = self.all_metadata[key]

        blk = LoadAndPrepareData(metadata, lazy=self.lazy)

        rauc_sigs = []
        if not self.lazy:
            for sig in blk.segments[0].analogsignals:
                rauc = elephant.signal_processing.rauc(sig, bin_duration = 0.1*pq.s)
                rauc.name = sig.name + ' RAUC'
                rauc_sigs.append(rauc)

        ephyviewer_config = EphyviewerConfigurator(metadata, blk, rauc_sigs, self.lazy)
        ephyviewer_config.enable_all()

        win = ephyviewer_config.create_ephyviewer_window(projector_mode=self.projector_mode, support_increased_line_width=self.support_increased_line_width)
        self.windows.append(win)
        win.show()

    def toggle_lazy(self, checked):
        self.lazy = checked

    def toggle_projector_mode(self, checked):
        self.projector_mode = checked

    def toggle_support_increased_line_width(self, checked):
        self.support_increased_line_width = checked
