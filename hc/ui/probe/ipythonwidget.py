from IPython.qt.console.rich_ipython_widget import RichIPythonWidget


class HCIPythonWidget(RichIPythonWidget):
    editor = 'gvim'
    gui_completion = 'droplist'

    def __init__(self, *args, **kwargs):
        super(HCIPythonWidget, self).__init__(*args, **kwargs)

    def start(self):
        from IPython.qt.inprocess import QtInProcessKernelManager
        self.kernel_manager = kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel()
        kernel_manager.kernel.gui = 'qt'
        self.kernel_client = kernel_client = self._kernel_manager.client()
        kernel_client.start_channels()
        self.set_default_style(colors="linux")

        def stop():
            kernel_client.stop_channels()
            kernel_manager.shutdown_kernel()
        self.exit_requested.connect(stop)

    def push(self, variableDict):
        """
        Given a dictionary containing name / value pairs,
        push those variables to the IPython console widget
        """
        self.kernel_manager.kernel.shell.push(variableDict)

    def clear(self):
        """
        Clears the terminal
        """
        self._control.clear()

    def append(self, text):
        """
        Prints some plain text to the console
        """
        self._append_plain_text(text)
