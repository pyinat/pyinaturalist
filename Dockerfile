# Dockerfile used for running pyinaturalist-notebook with Binder
FROM  jxcook/pyinaturalist-notebook:0.14
COPY . ${HOME}
USER root
RUN chown -R ${NB_UID} ${HOME}
USER $NB_UID
WORKDIR $HOME
