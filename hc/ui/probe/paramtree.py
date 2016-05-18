import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, registerParameterType
from PyQt5 import QtCore, QtWidgets

params = [
    {'name': 'Connection', 'type': 'group', 'children': [
        {'name': 'Host', 'type': 'str'},
        {'name': 'Port', 'type': 'str'},
        {'name': 'Connect', 'type': 'action'},
    ]},

    {'name': 'GCode', 'type': 'group', 'children': [
        {'name': 'Load G-code', 'type': 'action'},
        {'name': 'Width', 'type': 'float', 'value': 0.0, 'suffix': 'mm', 'readonly': True},
        {'name': 'Height', 'type': 'float', 'value': 0.0, 'suffix': 'mm', 'readonly': True},
        {'name': 'Min Z', 'type': 'float', 'value': 0.0, 'suffix': 'mm', 'readonly': True},
        {'name': 'Max Z', 'type': 'float', 'value': 0.0, 'suffix': 'mm', 'readonly': True},
        {'name': 'Visible', 'type': 'bool', 'value': 1},
    ]},

    {'name': 'Probe', 'type': 'group', 'children': [
        {'name': 'Rows', 'type': 'int', 'value': 5,
         'tip': 'Number of X Probe points'},
        {'name': 'Cols', 'type': 'int', 'value': 5},
        {'name': 'Width', 'type': 'float', 'value': 100.0},
        {'name': 'Height', 'type': 'float', 'value': 100.0},
        {'name': 'Margin', 'type': 'float', 'value': -1.0},
        {'name': 'Start Z', 'type': 'float', 'value': 2.0},
        {'name': 'Max Depth', 'type': 'float', 'value': -10.0},
        {'name': 'Feedrate', 'type': 'float', 'value': 100.0},
        {'name': 'Run probe', 'type': 'action'},
        {'name': 'Process', 'type': 'action'},
        {'name': 'Save processed G-code', 'type': 'action'},
    ]},

    {'name': 'Probe Result', 'type': 'group', 'children': [
        {'name': 'Last point', 'type': 'float', 'value': 0.0, 'readonly': True},
        {'name': 'Lowest point', 'type': 'float', 'value': 100.0, 'readonly': True},
        {'name': 'Highest point', 'type': 'float', 'value': -100.0, 'readonly': True},
        {'name': 'Offset', 'type': 'slider', 'value': 0.0},
        {'name': 'Multiply', 'type': 'slider', 'value': 1.0},
        {'name': 'Snap Z', 'type': 'bool', 'value': 1},
        {'name': 'Draw edges', 'type': 'bool', 'value': 0},
        {'name': 'Gradient', 'type': 'colormap'},
        {'name': 'Visible', 'type': 'bool', 'value': 1},
    ]},

    {'name': 'Grid', 'type': 'group', 'children': [
        {'name': 'Width', 'type': 'float', 'value': 100.0},
        {'name': 'Height', 'type': 'float', 'value': 100.0},
        {'name': 'Visible', 'type': 'bool', 'value': 1},
    ]},

    {'name': 'Cross', 'type': 'group', 'children': [
        {'name': 'Size', 'type': 'float', 'value': 10.0},
        {'name': 'Visible', 'type': 'bool', 'value': 1},
        {'name': 'Position', 'type': 'group', 'children': [
            {'name': 'X', 'type': 'float', 'value': 0.0},
            {'name': 'Y', 'type': 'float', 'value': 0.0},
            {'name': 'Z', 'type': 'float', 'value': 0.0},
        ]},
    ]},
]


class SliderParameterItem(pTypes.WidgetParameterItem):
    def makeWidget(self):
        self.hideWidget = False
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.sigChanged = self.slider.valueChanged
        return self.slider

    # so we don't hide displayLabel
    def treeWidgetChanged(self):
        super(SliderParameterItem, self).treeWidgetChanged()
        self.displayLabel.show()

    def showEditor(self):
        pass

    def hideEditor(self):
        pass


class SliderParameter(Parameter):
    itemClass = SliderParameterItem

registerParameterType('slider', SliderParameter, override=True)


class HCParamTree(ParameterTree):
    def __init__(self, *args, **kwargs):
        super(HCParamTree, self).__init__(*args, **kwargs)

        self.params = Parameter.create(name='params', type='group',
                                       children=params)

        self.setParameters(self.params, showTop=False)

    def changing(self, fn):
        self.change_fn = fn
        root = self.params

        def assign(root):
            root.sigValueChanging.connect(fn)
            map(assign, root.children())

        assign(root)

    def get_param(self, path):
        """
        Get tree value according to `path`

        Path matching is done on lowercased prefixes of actual names.

        """

        parts = path.split('.')
        root = self.params
        while parts:
            part = parts.pop(0)
            root = self.fuzzy_tree_child(root, part)

        return root

    def fuzzy_tree_child(self, root, name):
        c = filter(lambda x: x[0].startswith(name),
                   map(lambda x: (x[0].lower(), x[1]), root.names.items()))

        if len(c) == 1:
            return c[0][1]
        elif len(c) == 0:
            raise Exception('ParameterTree key not found {}'.format(name))
        else:
            # try exact match
            for e in c:
                if e[0] == name:
                    return e[1]

            raise Exception('Ambiguous ParameterTree key {}'.format(name))

    def collapse_group(self, name):
        root = self.itemAt(0, 0)
        for i in range(root.childCount()):
            if root.child(i).param.name().lower() == name:
                root.child(i).setExpanded(False)
                return

        raise Exception('ParameterTree group not found {}'.format(name))
