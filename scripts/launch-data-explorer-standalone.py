# add the directory containing modules to the path
import sys
sys.path.append('../modules')

from ephyviewer import mkQApp
from Standalone import DataExplorer

app = mkQApp()
win = DataExplorer(lazy=True, support_increased_line_width=False)
win.show()
app.exec_()
