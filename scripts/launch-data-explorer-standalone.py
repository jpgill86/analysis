# add the directory containing modules to the path
import sys
sys.path.append('../..')

from ephyviewer import mkQApp
from analysis.modules.Standalone import DataExplorer

app = mkQApp()
win = DataExplorer()
win.show()
print('Ready')
app.exec_()
