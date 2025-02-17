|project| documentation
=======================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. relativeinclude:: ../README.md
   :parser: myst_parser.sphinx_

.. templates etc. courtesy of `James A. Leedham <https://github.com/JamesALeedham/Sphinx-Autosummary-Recursion/>`_

.. include:: stuff.md
   :parser: myst_parser.sphinx_

Module Documentation
====================

Here you can find the module documentation of the |project| project (in version |version|).

.. autosummary::
   :toctree: _generated
   :template: module.rst
   :recursive:

    github_classroom_toolkit
