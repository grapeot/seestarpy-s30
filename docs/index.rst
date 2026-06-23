.. image:: _static/seestar_py_logo_banner.png
   :alt: SeeStar-Py
   :align: center


Welcome to SeeStar-Py's Documentation!
======================================

.. danger::

   **Firmware 7.18+ requires authentication.**

   See :doc:`info/authentication` for more details and the legal basis for
   interoperability.

.. important::

   **Version compatibility.**  seestarpy **0.5.1+** targets the **Seestar
   app v3.2.0 / firmware v7.75** generation.  The onboard batch-stacking
   workflow (:mod:`~seestarpy.stack`, :mod:`~seestarpy.crowdsky`) sends
   sub-frame paths in the form firmware v7.75 requires; on **earlier
   firmware that format is not guaranteed to work**.

   If your Seestar runs firmware **earlier than v7.75** (app < v3.2.0),
   install a previous release instead:

   .. code-block:: bash

      pip install "seestarpy<0.5"

.. image:: https://img.shields.io/github/v/tag/grapeot/seestarpy-s30?label=version
   :alt: Version
   :target: https://github.com/grapeot/seestarpy-s30

**seestarpy** is a Python SDK for driving ZWO Seestar smart
telescopes over your local network.  It wraps the Seestar's JSON-RPC
command interface and binary image streaming protocol into a clean
Python API — no phone app required.

This documentation is built from
`grapeot/seestarpy-s30 <https://github.com/grapeot/seestarpy-s30>`_,
based on `astronomyk/seestarpy <https://github.com/astronomyk/seestarpy>`_.


Installation
------------

.. code-block:: bash

   pip install git+https://github.com/grapeot/seestarpy-s30.git

Getting started
---------------

The shortest path from install to imaging:

.. code-block:: python

   import seestarpy as ssp

   # 1. Connect — the Seestar is auto-discovered via mDNS
   ssp.connection.test_connection()

   # 2. Open the arm
   ssp.open()

   # 3. Goto a target (coordinates resolved automatically)
   ssp.goto_target("M42")

   # 4. Start stacking
   ssp.start_stack()

That's it — the Seestar will slew to M42, plate-solve, and begin
stacking sub-exposures.

To see what the Seestar is currently looking at, grab the latest stacked
frame and pop it up in a matplotlib window:

.. code-block:: python

   from seestarpy import stream

   stream.show_current_stack()              # one Seestar
   stream.show_current_stack(ips="all")     # all Seestars in a subplot grid

If auto-discovery doesn't find your Seestar, set the IP manually:

.. code-block:: python

   ssp.connection.DEFAULT_IP = "192.168.1.246"

You can find your Seestar's IP in the official phone app under the
station-mode settings.


Controlling multiple Seestars
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Most commands accept an ``ips`` keyword to broadcast to multiple
Seestars at once:

.. code-block:: python

   # Discover all Seestars on the network
   ssp.connection.find_available_ips(n_ip=3)

   # Open all arms simultaneously
   ssp.open(ips="all")

   # Goto the same target on all Seestars
   ssp.goto_target("M42", ips="all")

See the :doc:`examples/basic_connection` page for more details.


When you're done
^^^^^^^^^^^^^^^^

.. code-block:: python

   ssp.stop_view()
   ssp.close()


Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Tutorials

   examples/basic_connection
   examples/basic_observing
   examples/basic_status_checks
   examples/changing_seestar_settings
   examples/changing_gain
   examples/observation_plans
   examples/data_management
   examples/live_streaming
   examples/wide_camera
   examples/crowdsky_stacking

.. toctree::
   :maxdepth: 2
   :caption: Reference

   info/authentication
   info/connection_framework
   info/errors
   info/image_stream_protocol
   api/api_index


Feedback
--------

Found an issue or have a feature request?
`Open an issue on GitHub <https://github.com/grapeot/seestarpy-s30/issues>`_.
