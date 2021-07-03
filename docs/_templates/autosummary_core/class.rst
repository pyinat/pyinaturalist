
{# Automodapi class template for data models #}
{{ objname }}
{{ underline }}

.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}
   :show-inheritance:
   
   {% block attributes_summary %}
   {% if attributes %}
   .. rubric:: Attributes Summary

   .. csv-table::
      :class: docutils
      :header: "Name", "Type", "Description"
      :widths: 10, 12, 30
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
