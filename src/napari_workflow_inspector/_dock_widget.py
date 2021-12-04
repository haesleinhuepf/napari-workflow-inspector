import numpy as np
from napari_plugin_engine import napari_hook_implementation
from qtpy.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLayout, QLabel, QTabWidget, QScrollArea
from qtpy.QtWidgets import QSpacerItem, QSizePolicy
from qtpy.QtCore import QTimer, Qt
from magicgui import magic_factory
from napari_tools_menu import register_dock_widget
import napari

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('Qt5Agg')

# Adapted from https://github.com/BiAPoL/napari-clusters-plotter/blob/main/napari_clusters_plotter/_plotter.py
class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=7, height=4):
        self.fig = Figure(figsize=(width, height))

        # changing color of axis background to napari main window color
        self.fig.patch.set_facecolor('#262930')
        self.axes = self.fig.add_subplot(111)

        super(MplCanvas, self).__init__(self.fig)

@register_dock_widget(menu="Visualization > Workflow Inspector")
class WorkflowWidget(QWidget):

    def __init__(self, napari_viewer):
        super().__init__()
        self._viewer = napari_viewer

        igraphwidget = MplCanvas()
        self.graph_layout = None
        self.idfg_edges = None
        self.idfg_statii = None

        lbl_from_roots = QLabel("")
        lbl_from_leafs = QLabel("")
        lbl_raw = QLabel("")
        scroll_area_raw = QScrollArea()
        scroll_area_raw.setWidget(lbl_raw)

        tabs = QTabWidget()
        tabs.addTab(igraphwidget, "Image data flow graph")
        tabs.addTab(lbl_from_roots, "From source")
        tabs.addTab(lbl_from_leafs, "From target")
        tabs.addTab(scroll_area_raw, "Raw")

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(tabs)

        try:
            import napari_script_editor
            btn_generate_code = QPushButton("Generate code")
            btn_generate_code.clicked.connect(self._generate_code)
            self.layout().addWidget(btn_generate_code)
        except ImportError:
            pass

        verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout().addItem(verticalSpacer)


        self.timer = QTimer()
        self.timer.setInterval(200)

        @self.timer.timeout.connect
        def update_layer(*_):
            from napari_time_slicer._workflow import WorkflowManager, _layer_invalid, _viewer_has_layer
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

            if len(self._edges) > 0:

                import igraph
                idfg = igraph.Graph(self._edges)

                def redraw():
                    igraph.plot(idfg,
                                target=igraphwidget.axes,
                                vertex_label=["   " + name for name in self._names],
                                vertex_color=self._statii,
                                vertex_label_color = self._statii,
                                vertex_size = 10,
                                vertex_label_dist = 10,
                                vertex_label_size = 10,
                                edge_color = "#dddddd",
                                layout=self.graph_layout)


                if not (np.array_equal(self.idfg_edges, np.asarray(self._edges)) and self.idfg_statii == str(self._statii)):

                    if self.graph_layout is None:
                        self.graph_layout = idfg.layout_auto()

                    # workaround as vertex_label_color above doesn't work :-(
                    matplotlib.rcParams['text.color'] = '#dddddd'

                    igraphwidget.axes.clear()
                    igraphwidget.axes.axis('off')

                    if not np.array_equal(self.idfg_edges, np.asarray(self._edges)):
                        self.graph_layout = idfg.layout_auto()

                    redraw()

                    self.idfg_edges = np.asarray(self._edges)
                    self.idfg_statii = str(self._statii)
                    igraphwidget.draw()
            else:
                igraphwidget.axes.clear()

            lbl_from_leafs.setText(html(build_output(workflow.leafs(), workflow.sources_of)))
            lbl_raw.setText(str(workflow))
            lbl_raw.setMinimumSize(1000, 1000)
            lbl_raw.setAlignment(Qt.AlignTop)


        self.timer.start()

    def _generate_code(self):
        imports = []
        code = []

        from napari_time_slicer._workflow import WorkflowManager, _layer_invalid, _viewer_has_layer
        workflow = WorkflowManager.install(self._viewer).workflow
        roots = workflow.roots()

        def better_str(value):
            if isinstance(value, str):
                value = value.replace("[", "_")\
                    .replace("]", "_")\
                    .replace(" ", "_")\
                    .replace("(", "_")\
                    .replace(")", "_")\
                    .replace(".", "_")\
                    .replace("-", "_")
                if value[0] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                    value = "img_" + value
            return str(value)

        def build_output(list_of_items, func_to_follow):
            for key in list_of_items:
                result_name = better_str(key)
                try:
                    task = workflow.get_task(key)
                    print("TASK", task)
                    function = task[0]
                    arguments = task[1:]
                    if arguments[-1] is None:
                        arguments = arguments[:-1]
                    new_import = "import " + function.__module__.split(".")[0]
                    if new_import not in imports:
                        imports.append(new_import)
                    arg_str = ", ".join([better_str(a) for a in arguments])

                    code.append("# ## " + function.__name__.replace("_", " "))
                    code.append(f"{result_name} = {function.__module__}.{function.__name__}({arg_str})")
                    if _viewer_has_layer(self._viewer, key):
                        if isinstance(self._viewer.layers[key], napari.layers.Labels):
                            code.append(f"viewer.add_labels({result_name}, name='{key}')")
                        else:
                            code.append(f"viewer.add_image({result_name}, name='{key}')")
                except KeyError:
                    code.append(f"{result_name} = viewer.layers['{key}'].data")
                code.append("")
                build_output(func_to_follow(key), func_to_follow)


        build_output(workflow.roots(), workflow.followers_of)
        from textwrap import dedent

        preamble = dedent("""
            import napari

            if 'viewer' not in globals():
                viewer = napari.Viewer()
            """).strip()

        complete_code = "\n".join(imports) + "\n" + preamble + "\n\n" + "\n".join(code) + "\n"
        print(complete_code)

        import napari_script_editor
        editor = napari_script_editor.ScriptEditor.get_script_editor_from_viewer(self._viewer)
        editor.set_code(complete_code)



@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    # you can return either a single widget, or a sequence of widgets
    return [WorkflowWidget]