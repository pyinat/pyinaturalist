FROM jupyter/scipy-notebook
USER root

# Install some more conda packages useful for data exploration & visualization
RUN conda install --quiet --yes \
    'altair=4.*' \
    'altair-saver' \
    'dash=1.*' \
    'gdal=3.*' \
    'geoviews' \
    'geopandas' \
    'pip=21.*' \
    'plotly=4.*' \
    'python-dateutil' \
    'python-forge' \
    'requests=2.25.*' \
    'xarray' && \
    conda clean --all -f -y && \
    # Install any non-conda pip packages last
    pip install pyinaturalist && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

USER $NB_UID
WORKDIR $HOME
