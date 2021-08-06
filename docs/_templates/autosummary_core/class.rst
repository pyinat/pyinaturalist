
{# Automodapi class template for data models #}
{{ objname }}
{{ underline }}

{# Increase the max content width, since we won't have a local ToC to the right #}
.. raw:: html

   <style>div.content{width: 60em}</style>

.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}
   :show-inheritance:

   {% block attributes_summary %}
   {% if attributes %}
   .. rubric:: Attributes

   .. csv-table::
      :class: docutils
      :header: "Name", "Type", "Description"
      :widths: 12 12 76
      :file: {{ '../models/' + objname + '.csv' }}

   {% endif %}
   {% endblock %}

   {% block methods %}
   {% if methods %}
   .. rubric:: Methods

   {% for item in methods %}
   .. automethod:: {{ item }}
   {%- endfor %}

   {% endif %}
   {% endblock %}
