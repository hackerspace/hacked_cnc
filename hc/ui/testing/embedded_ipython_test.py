#!/usr/bin/python

# !! this doesn't work more often then it does
# it would be nice to have ipython widget but it seems rather hard to debug

import os

from IPython.frontend.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.frontend.qt.manager import QtKernelManager
from IPython.frontend.qt.inprocess import QtInProcessKernelManager
from IPython.kernel.zmq.ipkernel import Kernel
from IPython.kernel.inprocess.ipkernel import InProcessKernel
from IPython.lib import guisupport


def print_process_id():
    print 'Process ID is:', os.getpid()


def main():
    # Print the ID of the main process
    print_process_id()

    app = guisupport.get_app_qt4()


    # Create an in-process kernel
    # >>> print_process_id()
    # will print the same process ID as the main process
    kernel = InProcessKernel(gui='qt4')
    kernel.shell.push({'foo': 43, 'print_process_id': print_process_id})
    kernel_manager = QtInProcessKernelManager(kernel=kernel)

    # Uncomment these lines to use a kernel on a separate process
    # >>> import os; print os.getpid()
    # will give a different process ID
    #kernel = Kernel(gui='qt4')
    #kernel_manager = QtKernelManager(kernel=kernel)

    kernel_manager.start_kernel()
    kernel_manager.start_channels()

    def stop():
        kernel_manager.shutdown_kernel()
        kernel_manager.stop_channels()
        app.exit()

    control = RichIPythonWidget()
    control.kernel_manager = kernel_manager
    control.exit_requested.connect(stop)
    control.show()

    guisupport.start_event_loop_qt4(app)


if __name__ == '__main__':
    main()

