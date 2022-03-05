import numpy as np
from napari_plugin_engine import napari_hook_implementation
from qtpy.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLayout, QLabel, QTabWidget, QScrollArea
from qtpy.QtWidgets import QFileDialog
from qtpy.QtWidgets import QSpacerItem, QSizePolicy
from qtpy.QtCore import QTimer, Qt
from napari_tools_menu import register_dock_widget

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('Qt5Agg')

import pickle
import networkx as nx


# From https://stackoverflow.com/questions/28001655/draggable-line-with-draggable-points
class ClickableNodes():

    def __init__(self, canvas, positions, viewer, radius=200, transparent=False):

        self.invalid_color = [1, 0, 1, 1]
        self.valid_color = [0, 1, 0, 1]
        self.ec_inactive = [0, 0, 0, 1]
        self.ec_active = [1, 1, 1, 1]
        self.viewer = viewer
        
        self.positions = positions
        self.x = [positions[key][0] for key in positions.keys()]
        self.y = [positions[key][1] for key in positions.keys()]
        
        self.canvas = canvas
        self.points = self.canvas.axes.scatter(self.x, self.y, picker=True, s=radius,
                                               facecolor=[self.valid_color] * len(self.x),
                                               edgecolor=[self.ec_inactive] * len(self.x))
        
        self.edgecolors = self.points.get_edgecolors()
        self.background = None
        
        self.canvas.mpl_connect('pick_event', self.on_pick)

    def toggle(self, index):
        """Turn this point on and off"""
        
        edgecolors = self.edgecolors.copy()
        edgecolors[index] = self.ec_active
        self.points.set_edgecolors(edgecolors)
        self.canvas.draw()
        
        keys = list(self.positions.keys())
        index = index[0]
        if keys[index] in self.viewer.layers:
            layer = self.viewer.layers[keys[index]]
            self.viewer.layers.selection = {layer}

    def on_pick(self, event):
        self.toggle(event.ind)
        
    def validate(self, node_name, state):
        for idx, key in enumerate(self.positions.keys()):
            if key == node_name:
                facecolors = self.points.get_facecolors()
                
                if state == 'invalid':
                    facecolors[idx] = self.invalid_color
                elif state == 'valid':
                    facecolors[idx] = self.valid_color
                    
                self.points.set_facecolors(facecolors)
                self.canvas.draw()
                
            
    def disconnect(self):
        'disconnect all the stored connection ids'

        self.point.figure.canvas.mpl_disconnect(self.cidpress)


# Adapted from https://github.com/jo-mueller/RadiAiDD/blob/master/RadiAIDD/Backend/UI/_matplotlibwidgetFile.py
class MplCanvas(FigureCanvas):
    """
    Defines the canvas of the matplotlib window
    """

    def __init__(self):
        self.fig = Figure()                         # create figure
        self.axes = self.fig.add_subplot(111)       # create subplot
        self.fig.subplots_adjust(left=0.04, bottom=0.04, right=0.97,
                                 top=0.96,  wspace=None, hspace=None)

        self.fig.patch.set_facecolor('#262930')
        self.axes.set_facecolor('#262930')

        FigureCanvas.__init__(self, self.fig)  # initialize canvas
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


class matplotlibWidget(QWidget):
    """
    The matplotlibWidget class based on QWidget
    """

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        # save canvas and toolbar
        self.canvas = MplCanvas()
        self.toolbar = NavigationToolbar(self.canvas, self)
        # set layout and add them to widget
        self.vbl = QVBoxLayout()
        self.vbl.addWidget(self.toolbar)
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)

@register_dock_widget(menu="Visualization > Workflow Inspector")
class WorkflowWidget(QWidget):

    def __init__(self, napari_viewer):
        super().__init__()
        self._viewer = napari_viewer

        self.graphwidget = matplotlibWidget()
        self.graph = nx.DiGraph()

        self.graph_layout = None
        self.idfg_edges = None
        self.idfg_statii = None

        lbl_from_roots = QLabel("")
        lbl_from_leafs = QLabel("")
        lbl_raw = QLabel("")
        scroll_area_raw = QScrollArea()
        scroll_area_raw.setWidget(lbl_raw)

        tabs = QTabWidget()
        tabs.addTab(self.graphwidget, "Image data flow graph")
        tabs.addTab(lbl_from_roots, "From source")
        tabs.addTab(lbl_from_leafs, "From target")
        tabs.addTab(scroll_area_raw, "Raw")

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(tabs)

        try:
            import napari_script_editor
            btn_generate_code = QPushButton("Generate code")
            btn_export_workflow = QPushButton("Export workflow")

            btn_generate_code.clicked.connect(self._generate_code)
            btn_export_workflow.clicked.connect(self._export_code)
            self.layout().addWidget(btn_generate_code)
            self.layout().addWidget(btn_export_workflow)
        except ImportError:
            pass

        verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout().addItem(verticalSpacer)


        self.timer = QTimer()
        self.timer.setInterval(200)


        @self.timer.timeout.connect
        def update_layer(*_):
            from napari_workflows import WorkflowManager
            from napari_workflows._workflow import _layer_invalid, _viewer_has_layer
            workflow = WorkflowManager.install(napari_viewer).workflow
            roots = workflow.roots()

            self._counter = 0
            self._edges = []
            self._names = []
            self._statii = []

            def build_output(list_of_items, func_to_follow, level=0, parent=-1):
                output = ""
                for i in list_of_items:
                    if _viewer_has_layer(self._viewer, i):
                        layer = self._viewer.layers[i]

                        if layer.name in roots:
                            status = "#dddddd"
                        elif _layer_invalid(layer):
                            status = "#dd0000"
                        else:
                            status = "#00dd00"

                        output = output + '<font color="' + status + '">'
                        output = output + ("   " * level) + "-> " + i + "\n"
                        output = output + '</font>'

                        if i in self._names:
                            index = self._names.index(i)
                        else:
                            self._names.append(i)
                            self._statii.append(status)
                            index = len(self._names) - 1

                        if parent > -1:
                            new_edge = (parent, index)
                            if not new_edge in self._edges:
                                self._edges.append(new_edge)


                        output = output + build_output(func_to_follow(i), func_to_follow, level + 1, index)
                return output

            def html(text):
                return "<html><pre>" + text + "</pre></html>"

            lbl_from_roots.setText(html(build_output(workflow.roots(), workflow.followers_of)))

            new_graph = self._create_nx_graph_from_workflow(workflow)
            # replace old graph instance only when nodes or edges have changed
            if new_graph.nodes != self.graph.nodes or new_graph.edges != self.graph.edges:

                self.graph = new_graph
                self._draw_nx_graph(self.graph)
                
            self._update_nx_graph()

            lbl_from_leafs.setText(html(build_output(workflow.leafs(), workflow.sources_of)))
            lbl_raw.setText(str(workflow))
            lbl_raw.setMinimumSize(1000, 1000)
            lbl_raw.setAlignment(Qt.AlignTop)


        self.timer.start()

    def _export_code(self):

        fileName, _ = QFileDialog.getSaveFileName(self)

        graph = {
            'counter': self._counter,
            'edges': self._edges,
            'names': self._names,
            'statii': self._statii}

        with open(fileName, 'wb') as pickleobj:
            pickle.dump(pickleobj, fileName)

    def _generate_code(self):
        from napari_workflows import WorkflowManager

        complete_code = WorkflowManager.install(self._viewer).to_python_code()

        print(complete_code)

        import napari_script_editor
        editor = napari_script_editor.ScriptEditor.get_script_editor_from_viewer(self._viewer)
        editor.set_code(complete_code)

    def _create_nx_graph_from_workflow(self, workflow):
        """Consume a workflow object and return an directed nx graph"""
        G = nx.DiGraph()

        # add all images as nodes
        for key in workflow._tasks.keys():
            G.add_node(key)

        # Traverse workflow and connect nodes
        nodes = workflow.roots()
        for node in nodes:

            followers = workflow.followers_of(node)

            for follower in followers:
                G.add_edge(node, follower)
                nodes.append(follower)

        return G

    def _draw_nx_graph(self, G):

        ax = self.graphwidget.canvas.axes
        ax.clear()

        # get positions for drawing
        self.positions = nx.drawing.layout.kamada_kawai_layout(G)
        
        nx.draw_networkx_edges(G, pos=self.positions, ax=self.graphwidget.canvas.axes,
                               width=2, edge_color='white')
        self.graph_drawing = ClickableNodes(self.graphwidget.canvas, self.positions,
                                            self._viewer)
        
        props = dict(boxstyle='round', facecolor='white', alpha=0.2)
        nx.draw_networkx_labels(G, pos=self.positions, ax=self.graphwidget.canvas.axes,
                                font_color='white', bbox=props,
                                verticalalignment='bottom')
        
        ax.set_facecolor('#262930')
        self.graphwidget.canvas.draw()
        
    def _update_nx_graph(self):
        "Check if layers are valid and changes points accordingly."
        from napari_workflows._workflow import _layer_invalid, _viewer_has_layer
        
        for node in self.graph.nodes:
            if _viewer_has_layer(self._viewer, node):
                layer = self._viewer.layers[node]
                if _layer_invalid(layer):
                    self.graph_drawing.validate(node, state='invalid')
                else:
                    self.graph_drawing.validate(node, state='valid')


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    # you can return either a single widget, or a sequence of widgets
    return [WorkflowWidget]
