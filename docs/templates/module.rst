{{ name | escape | underline }}

.. .. note::
    | {{ name }}
    | {{ module }}
    | {{ fullname }}

.. currentmodule:: {{ module }}

.. automodule:: {{ fullname }}

   {% block attributes -%}
   {%- if attributes -%}
   .. rubric:: {{ _('Module attributes') }}

   {{ name | escape }} defines the following attributes.

   .. autosummary::
      :toctree:
      :template: attribute.rst
   {% for item in attributes %}
      {{ item }}
   {%- endfor -%}
   {%- endif -%}
   {%- endblock %}

   {% block functions -%}
   {%- if functions -%}
   .. rubric:: {{ _('Functions') }}

   {{ name | escape }} defines the following functions.

   .. autosummary::
      :toctree:
      :template: function.rst
   {% for item in functions %}
      {{ item }}
   {%- endfor -%}
   {%- endif -%}
   {%- endblock %}

   {% block classes -%}
   {%- if classes -%}
   .. rubric:: {{ _('Classes') }}

   {{ name | escape }} defines the following classes.

   .. autosummary::
      :toctree:
      :template: class.rst
      :nosignatures:
   {% for item in classes %}
      {{ item }}
   {%- endfor -%}
   {%- endif -%}
   {%- endblock %}

   {% block exceptions -%}
   {%- if exceptions -%}
   .. rubric:: {{ _('Exceptions') }}

   {{ name | escape }} defines the following exceptions.

   .. autosummary::
      :toctree:
      :nosignatures:
   {% for item in exceptions %}
      {{ item }}
   {%- endfor -%}
   {%- endif -%}
   {%- endblock %}

    {% block modules -%}
    {%- if modules -%}
    .. rubric:: {{ _('Submodules') }}

    {{ name | escape }} contains the following sub-modules.

    .. autosummary::
      :toctree:
      :template: module.rst
      :recursive:
     {% for item in modules %}
       {{ item }}
     {%- endfor -%}
    {%- endif -%}
    {%- endblock %}
