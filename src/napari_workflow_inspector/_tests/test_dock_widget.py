import napari_workflow_inspector
import pytest

# this is your plugin name declared in your napari.plugins entry point
MY_PLUGIN_NAME = "napari-workflow-inspector"
# the name of your widget(s)
MY_WIDGET_NAMES = ["Workflow Widget"]


@pytest.mark.parametrize("widget_name", MY_WIDGET_NAMES)
def test_something_with_viewer(widget_name, make_napari_viewer, napari_plugin_manager):
    napari_plugin_manager.register(napari_workflow_inspector, name=MY_PLUGIN_NAME)
    viewer = make_napari_viewer()
    num_dw = len(viewer.window._dock_widgets)
    viewer.window.add_plugin_dock_widget(
        plugin_name=MY_PLUGIN_NAME, widget_name=widget_name
    )
    assert len(viewer.window._dock_widgets) == num_dw + 1




def test_optimizer_with_assistant(make_napari_viewer):
    viewer = make_napari_viewer()

    # Add Assistant and configure workflow
    from napari_pyclesperanto_assistant import Assistant
    assistant = Assistant(viewer)

    num_dw = len(viewer.window._dock_widgets)
    viewer.window.add_dock_widget(assistant)
    assert len(viewer.window._dock_widgets) == num_dw + 1

    import numpy as np
    image = np.asarray([
        [0, 0, 0, 0, 0, 0, 0],
        [1, 1, 1, 0, 0, 1, 1],
        [1, 2, 1, 0, 0, 1, 2],
        [1, 1, 1, 0, 0, 1, 1],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 1, 2, 1, 0, 0],
    ])

    viewer.add_image(image)

    from napari_pyclesperanto_assistant._categories import CATEGORIES
    assistant._activate(CATEGORIES.get("Label"))

    # Add optimizer and optimize workflow
    from napari_workflow_inspector._dock_widget import WorkflowWidget
    inspector_gui = WorkflowWidget(viewer)

    num_dw = len(viewer.window._dock_widgets)
    viewer.window.add_dock_widget(inspector_gui)
    assert len(viewer.window._dock_widgets) == num_dw + 1

    inspector_gui.timer.stop()
    del inspector_gui.timer
