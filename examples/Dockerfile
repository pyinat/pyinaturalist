FROM jupyter/scipy-notebook
USER root

# Install a few more conda packages, and install any non-conda pip packages last
RUN conda install --quiet --yes \
    'altair=4.*' \
    'dash=1.*' \
    'pip=20.3.*' && \
    conda clean --all -f -y && \
    pip install "pyinaturalist~=0.11" && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

USER $NB_UID
WORKDIR $HOME
