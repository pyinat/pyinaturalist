(examples)=
# {fa}`laptop-code` Examples
Below are some examples of building data visualizations and other neat things using
iNaturalist data. These can also be found in the
[examples/](https://github.com/pyinat/pyinaturalist/tree/main/examples) folder on GitHub.

## Notebooks
Example Jupter notebooks. Click the badge below to try them out in your browser using Binder:

```{image} https://mybinder.org/badge_logo.svg
:target: https://mybinder.org/v2/gh/pyinat/pyinaturalist/main?filepath=examples
```

This uses the
[pyinaturalist-notebook](https://github.com/JWCook/pyinaturalist-notebook)
Docker image, which you can also use to run these examples on a local Jupyter server.

```{toctree}
:maxdepth: 2

examples/Tutorial_1_Observations.ipynb
examples/Tutorial_2_Taxa.ipynb
examples/Tutorial_3_Data_Visualizations.ipynb
examples/Data Visualizations - Regional Activity Report.ipynb
examples/Data Visualizations - Regional Observation Stats.ipynb
examples/Data Visualizations - Seaborn.ipynb
examples/Data Visualizations - Matplotlib.ipynb
```

<!--
TODO: Can't generate thumbnails for Altair visualizations
.. nbgallery::
:caption: This is a thumbnail gallery
:name: nb-gallery
-->


## Scripts

### Convert observations to GPX
```{eval-rst}
.. include:: ../examples/observations_to_gpx.py
    :start-line: 2
    :end-line: 6
```

:::{admonition} Example code
:class: toggle

```{literalinclude} ../examples/observations_to_gpx.py
:lines: 1,8-
```
:::

### Observation photo metadata
```{eval-rst}
.. include:: ../examples/observation_photo_metadata.py
    :start-line: 2
    :end-line: 17
```

:::{admonition} Example code
:class: toggle

```{literalinclude} ../examples/observation_photo_metadata.py
:lines: 1,19-
```
:::
