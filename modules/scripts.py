def launch_standalone():
    from ephyviewer import mkQApp
    from .Standalone import DataExplorer

    app = mkQApp()
    win = DataExplorer()
    win.show()
    print('Ready')
    app.exec_()
