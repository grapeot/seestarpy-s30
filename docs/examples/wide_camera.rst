S30 Wide Camera
===============

Seestar S30 / S30 Pro devices expose a second (wide-angle) camera alongside
the main telephoto sensor.  Use the :mod:`seestarpy.wide` helpers to switch
pipelines and :mod:`seestarpy.stream` to capture frames.

On firmware 7.75 the wide camera behaves differently depending on mode:

- **Scenery** — ``SecondView`` reaches ``stage: RTSP``; capture via RTSP
  port :data:`~seestarpy.stream.RTSP_PORT_WIDE` (4555).
- **Star** — binary preview/stack stream on port
  :data:`~seestarpy.stream.IMAGE_PORT_WIDE` (4804) when
  ``SecondView.ContinuousExposure`` is active.


Scenery capture (recommended)
-----------------------------

The most reliable path on current firmware:

.. code-block:: python

    from seestarpy import connection as conn, stream, wide

    conn.DEFAULT_IP = "192.168.1.246"

    wide.start_scenery_view()
    stream.get_wide_live_image(mode="scenery", filename="wide.jpg")

This starts scenery view if needed, then grabs one H.264 frame from the
wide RTSP feed (requires ``ffmpeg`` on ``PATH``).


Manual control
--------------

For finer control over the dual-camera state machine:

.. code-block:: python

    from seestarpy import wide

    wide.enable_wide_camera(True)
    wide.select_camera(wide.VIEW_WIDE)
    wide.switch_live_camera(wide.CAM_WIDE)

    state = wide.get_second_view_state()
    print(state.get("stage"))   # RTSP in scenery, ContinuousExposure in star

.. note::

   ``get_setting()['wide_cam']`` may still read ``false`` after a
   successful ``set_setting(wide_cam=True)`` on some firmware builds.
   Prefer :func:`~seestarpy.wide.get_second_view_state` to see whether the
   wide pipeline is actually running.


Star-mode binary stream (4804)
------------------------------

For 16-bit Bayer/RGB frames (same protocol as telephoto port 4800):

.. code-block:: python

    from seestarpy import stream, wide

    wide.prepare_star_wide()
    header, payload = stream.get_live_image(
        port=stream.IMAGE_PORT_WIDE,
        method="get_current_img",
        fallback=False,
    )

This requires ``SecondView`` to reach ``ContinuousExposure``.  If the device
stays in ``Sleep``, only RTSP/scenery capture is available via API alone.
