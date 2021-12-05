# napari-workflow-inspector

[![License](https://img.shields.io/pypi/l/napari-workflow-inspector.svg?color=green)](https://github.com/haesleinhuepf/napari-workflow-inspector/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-workflow-inspector.svg?color=green)](https://pypi.org/project/napari-workflow-inspector)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-workflow-inspector.svg?color=green)](https://python.org)
[![tests](https://github.com/haesleinhuepf/napari-workflow-inspector/workflows/tests/badge.svg)](https://github.com/haesleinhuepf/napari-workflow-inspector/actions)
[![codecov](https://codecov.io/gh/haesleinhuepf/napari-workflow-inspector/branch/main/graph/badge.svg)](https://codecov.io/gh/haesleinhuepf/napari-workflow-inspector)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-workflow-inspector)](https://napari-hub.org/plugins/napari-workflow-inspector)

Inspect relationships between napari-plugins in active workflows. Open the inspector by clicking the menu `Tools > Visualization > Workflow Inspector`.

![img_1.png](https://github.com/haesleinhuepf/napari-workflow-inspector/raw/main/docs/screenshot_graph.png)

Also install the [napari-script-editor](https://www.napari-hub.org/plugins/napari-script-editor) 
to generate code from active workflows.

![img_2.png](https://github.com/haesleinhuepf/napari-workflow-inspector/raw/main/docs/screenshot_script_editor.png)

For recording workflows, all napari image processing plugins that use the `@time_slicer` interface are supported. See
[napari-time-slicer](https://www.napari-hub.org/plugins/napari-time-slicer) for a list. More to come, stay tuned.

----------------------------------

This [napari] plugin was generated with [Cookiecutter] using [@napari]'s [cookiecutter-napari-plugin] template.

## Installation

You can install `napari-workflow-inspector` via [pip]:

    pip install napari-workflow-inspector



To install latest development version :

    pip install git+https://github.com/haesleinhuepf/napari-workflow-inspector.git


## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## License

Distributed under the terms of the [BSD-3] license,
"napari-workflow-inspector" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin

[file an issue]: https://github.com/haesleinhuepf/napari-workflow-inspector/issues

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
