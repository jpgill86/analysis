#!/usr/bin/env python

'''

'''

import os

import quantities as pq
import elephant
from ephyviewer import QT

from .ParseMetadata import MetadataManager, _selector_labels
from .ImportData import LoadAndPrepareData
from .EphyviewerConfigurator import EphyviewerConfigurator


class MetadataSelectorQt(MetadataManager, QT.QListWidget):

    def __init__(self):
        MetadataManager.__init__(self)
        QT.QListWidget.__init__(self)

        self.setSelectionMode(QT.QListWidget.SingleSelection)
        self.setStyleSheet('font: 9pt Courier;')

        self.currentRowChanged.connect(self._on_select)

    def _on_select(self, currentRow):

        if currentRow >= 0:
            self._selection = list(self.all_metadata)[currentRow]
        else:
            self._selection = None

    def load(self):

        # remember the current selection
        old_selection = self._selection

        try:
            MetadataManager.load(self)
        except AssertionError as e:
            print('Bad metadata file!', e)

        if self.all_metadata is not None:

            # clear and repopulate the list,
            # which triggers the selection to change
            self.clear()
            for label in _selector_labels(self.all_metadata):
                QT.QListWidgetItem(label, self)

            if old_selection in self.all_metadata:
                # reselect the original selection if it still exists
                self.setCurrentRow(list(self.all_metadata).index(old_selection))
            else:
                # otherwise select the first item
                self.setCurrentRow(0)


class DownloadWorker(QT.QObject):

    download_finished = QT.pyqtSignal()

    def __init__(self, metadata_selector):

        QT.QObject.__init__(self)

        self.metadata_selector = metadata_selector

    def download(self):

        self.metadata_selector.download_all_data_files()
        self.download_finished.emit()


class DataExplorer(QT.QMainWindow):

    request_download = QT.pyqtSignal()

    def __init__(self, lazy=True, theme='light', support_increased_line_width=False):

        QT.QMainWindow.__init__(self)

        self.setWindowIcon(QT.QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts', 'icons', 'soundwave.png')))

        self.setWindowTitle('Data Explorer')
        self.resize(600, 300)

        # lazy loading using Neo RawIO
        self.lazy = lazy

        # available themes are 'light', 'dark', and 'original'
        self.theme = theme

        # support_increased_line_width=True eliminates the extremely poor
        # performance associated with TraceViewer's line_width > 1.0, but it
        # also degrades overall performance somewhat and uses a mode of
        # pyqtgraph that is reportedly unstable
        self.support_increased_line_width = support_increased_line_width

        # windows are appended to this list so that they persist after the
        # function that spawned them returns
        self.windows = []

        # metadata selector
        self.metadata_selector = MetadataSelectorQt()
        self.setCentralWidget(self.metadata_selector)

        # create a worker thread for downloading data
        self.download_thread = QT.QThread()
        self.download_worker = DownloadWorker(self.metadata_selector)
        self.download_worker.moveToThread(self.download_thread)
        self.request_download.connect(self.download_worker.download)
        self.download_worker.download_finished.connect(self.on_download_finished)

        # construct the menus
        self.create_menus()

        # open example metadata file
        self.metadata_selector.file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'example', 'metadata.yml')
        self.metadata_selector.load()

    def create_menus(self):

        self.file_menu = self.menuBar().addMenu(self.tr('&File'))

        do_open_metadata = QT.QAction('&Open metadata', self, shortcut = 'Ctrl+O')
        do_open_metadata.triggered.connect(self.open_metadata)
        self.file_menu.addAction(do_open_metadata)

        do_reload_metadata = QT.QAction('&Reload metadata', self, shortcut = 'Ctrl+R')
        do_reload_metadata.triggered.connect(self.metadata_selector.load)
        self.file_menu.addAction(do_reload_metadata)

        self.do_download_data = QT.QAction('&Download data', self, shortcut = 'Ctrl+D')
        self.do_download_data.triggered.connect(self.download_files)
        self.file_menu.addAction(self.do_download_data)

        do_launch = QT.QAction('&Launch', self, shortcut = 'Return')
        do_launch.triggered.connect(self.launch)
        self.file_menu.addAction(do_launch)

        self.options_menu = self.menuBar().addMenu(self.tr('&Options'))

        do_toggle_lazy = QT.QAction('&Fast loading (disables filters, spike detection, RAUC)', self)
        do_toggle_lazy.setCheckable(True)
        do_toggle_lazy.setChecked(self.lazy)
        do_toggle_lazy.triggered.connect(self.toggle_lazy)
        self.options_menu.addAction(do_toggle_lazy)

        do_toggle_support_increased_line_width = QT.QAction('&Thick traces (worse performance)', self)
        do_toggle_support_increased_line_width.setCheckable(True)
        do_toggle_support_increased_line_width.setChecked(self.support_increased_line_width)
        do_toggle_support_increased_line_width.triggered.connect(self.toggle_support_increased_line_width)
        self.options_menu.addAction(do_toggle_support_increased_line_width)

        self.theme_menu = self.menuBar().addMenu(self.tr('&Theme'))
        self.theme_group = QT.QActionGroup(self.theme_menu)

        do_select_light_theme = self.theme_menu.addAction('&Light theme')
        do_select_light_theme.setCheckable(True)
        do_select_light_theme.triggered.connect(self.select_light_theme)
        self.theme_group.addAction(do_select_light_theme)

        do_select_dark_theme = self.theme_menu.addAction('&Dark theme')
        do_select_dark_theme.setCheckable(True)
        do_select_dark_theme.triggered.connect(self.select_dark_theme)
        self.theme_group.addAction(do_select_dark_theme)

        do_select_original_theme = self.theme_menu.addAction('&Original theme')
        do_select_original_theme.setCheckable(True)
        do_select_original_theme.triggered.connect(self.select_original_theme)
        self.theme_group.addAction(do_select_original_theme)

        if self.theme == 'light':
            do_select_light_theme.setChecked(True)
        elif self.theme == 'dark':
            do_select_dark_theme.setChecked(True)
        elif self.theme == 'original':
            do_select_original_theme.setChecked(True)
        else:
            raise ValueError('theme "{}" is unrecognized'.format(self.theme))

    def open_metadata(self):

        file, _ = QT.QFileDialog.getOpenFileName(
            parent=self,
            caption='Open metadata',
            directory=None,
            filter='YAML files (*.yml *.yaml)')

        if file:
            self.metadata_selector.file = file
            self.metadata_selector.load()

    def download_files(self):

        self.download_thread.start()
        self.request_download.emit()
        self.do_download_data.setText('&Download in progress!')
        self.do_download_data.setEnabled(False)

    def on_download_finished(self):

        self.download_thread.quit()
        self.metadata_selector.load()
        self.do_download_data.setText('&Download data')
        self.do_download_data.setEnabled(True)

    def launch(self):

        metadata = self.metadata_selector.selected_metadata

        try:

            blk = LoadAndPrepareData(metadata, lazy=self.lazy)

            rauc_sigs = []
            if not self.lazy:
                for sig in blk.segments[0].analogsignals:
                    rauc = elephant.signal_processing.rauc(sig, bin_duration = 0.1*pq.s)
                    rauc.name = sig.name + ' RAUC'
                    rauc_sigs.append(rauc)

            ephyviewer_config = EphyviewerConfigurator(metadata, blk, rauc_sigs, self.lazy)
            ephyviewer_config.enable_all()

            win = ephyviewer_config.create_ephyviewer_window(theme=self.theme, support_increased_line_width=self.support_increased_line_width)
            self.windows.append(win)
            win.show()

        except FileNotFoundError as e:

            print('Some files were not found locally and may need to be downloaded')
            print(e)
            return

    def toggle_lazy(self, checked):
        self.lazy = checked

    def toggle_support_increased_line_width(self, checked):
        self.support_increased_line_width = checked

    def select_light_theme(self):
        self.theme = 'light'

    def select_dark_theme(self):
        self.theme = 'dark'

    def select_original_theme(self):
        self.theme = 'original'
