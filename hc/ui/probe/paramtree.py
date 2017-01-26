import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, registerParameterType
from pyqtgraph.widgets.SpinBox import SpinBox
from PyQt5 import QtCore, QtWidgets

params = [
    {'name': 'Connection', 'type': 'group', 'children': [
        {'name': 'Host', 'type': 'str'},
        {'name': 'Port', 'type': 'str'},
        {'name': 'Connect', 'type': 'action'},
    ]},

    {'name': 'GCode', 'type': 'group', 'children': [
        {'name': 'Load G-code', 'type': 'action'},
        {'name': 'Limits', 'type': 'group', 'children': [
            {'name': 'X min', 'type': 'float', 'value': 0.0, 'suffix': 'mm', 'readonly': True},
            {'name': 'X max', 'type': 'float', 'value': 0.0, 'suffix': 'mm', 'readonly': True},
            {'name': 'X len', 'type': 'float', 'value': 0.0, 'suffix': 'mm', 'readonly': True},
            {'name': 'Y min', 'type': 'float', 'value': 0.0, 'suffix': 'mm', 'readonly': True},
            {'name': 'Y max', 'type': 'float', 'value': 0.0, 'suffix': 'mm', 'readonly': True},
            {'name': 'Y len', 'type': 'float', 'value': 0.0, 'suffix': 'mm', 'readonly': True},
            {'name': 'Z min', 'type': 'float', 'value': 0.0, 'suffix': 'mm', 'readonly': True},
            {'name': 'Z max', 'type': 'float', 'value': 0.0, 'suffix': 'mm', 'readonly': True},
            {'name': 'Z len', 'type': 'float', 'value': 0.0, 'suffix': 'mm', 'readonly': True},
        ]},
        {'name': 'Visible', 'type': 'bool', 'value': 1},
    ]},

    {'name': 'Probe', 'type': 'group', 'children': [
        {'name': 'Rows', 'type': 'int', 'value': 5,
         'tip': 'Number of X Probe points'},
        {'name': 'Cols', 'type': 'int', 'value': 5},
        {'name': 'Width', 'type': 'float', 'value': 100.0},
        {'name': 'Height', 'type': 'float', 'value': 100.0},
        {'name': 'X Margin', 'type': 'float', 'value': -3.0},
        {'name': 'Y Margin', 'type': 'float', 'value': -3.0},
        {'name': 'Start Z', 'type': 'float', 'value': 2.0},
        {'name': 'Max Depth', 'type': 'float', 'value': -10.0},
        {'name': 'Z Feedrate', 'type': 'int', 'value': 100},
        {'name': 'Travel Feedrate', 'type': 'int', 'value': 1000},
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
        {'name': 'X origin', 'type': 'float', 'value': 0.0},
        {'name': 'Y origin', 'type': 'float', 'value': 0.0},
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


def mkOpts(opts, isInt=False):
    defs = {
        'value': 0, 'min': None, 'max': None,
        'step': 1.0, 'dec': False,
        'siPrefix': False, 'suffix': '', 'decimals': 3,
    }
    if isInt:
        defs['int'] = True
        defs['minStep'] = 1.0
    for k in defs:
        if k in opts:
            defs[k] = opts[k]
    if 'limits' in opts:
            defs['bounds'] = opts['limits']
    return defs


class IntSpinBox(SpinBox):
    def updateText(self, prev=None):
        self.skipValidate = True
        txt = ("%i %s") % (self.val, self.opts['suffix'])
        self.lineEdit().setText(txt)
        self.lastText = txt
        self.skipValidate = False

class IntParameterItem(pTypes.WidgetParameterItem):
    def makeWidget(self):
        w = IntSpinBox()
        w.setOpts(**mkOpts(self.param.opts, True))
        w.sigChanged = w.sigValueChanged
        w.sigChanging = w.sigValueChanging
        return w

class IntParameter(Parameter):
    itemClass = IntParameterItem

class FixedSpinBox(SpinBox):
    def updateText(self, prev=None):
        decimals = self.opts.get('decimals')
        self.skipValidate = True
        txt = ("%."+str(decimals)+"f %s") % (self.val, self.opts['suffix'])
        self.lineEdit().setText(txt)
        self.lastText = txt
        self.skipValidate = False

class FixedParameterItem(pTypes.WidgetParameterItem):
    def makeWidget(self):
        w = FixedSpinBox()
        w.setOpts(**mkOpts(self.param.opts))
        w.sigChanged = w.sigValueChanged
        w.sigChanging = w.sigValueChanging
        return w

class FixedParameter(Parameter):
    itemClass = FixedParameterItem

registerParameterType('slider', SliderParameter, override=True)
registerParameterType('int', IntParameter, override=True)
registerParameterType('float', FixedParameter, override=True)


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
