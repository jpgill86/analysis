# add the directory containing modules to the path
import sys
sys.path.append('../modules')

from ephyviewer import mkQApp
from Standalone import DataExplorer

app = mkQApp()
win = DataExplorer()
win.show()
print('Ready')
app.exec_()
