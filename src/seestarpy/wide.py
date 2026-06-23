"""S30 / S30 Pro wide-angle (second) camera helpers.

Reference implementations:

- **seestar_alp** ``front/app.py`` — settings POST with ``wide_cam``,
  ``wide_focal_pos``, live toggle at ``/live/wide-cam``.
- **Seestar APK** — ``SwitchSecondaryCmd`` sends ``set_setting`` with
  ``wide_cam: index`` (0 = telephoto, 1 = wide).  ``SetSelectedCamCmd``
  sends ``selected_cam: "View" | "SecondView"``.

On firmware 7.75 (S30 Pro tested 2026-06) note that ``get_setting()`` may
still report ``wide_cam: false`` after a successful ``set_setting(wide_cam=True)``.
Use :func:`get_app_state` / :func:`get_second_view_state` to see whether
the wide pipeline is actually running (``SecondView`` RTSP in scenery,
``ContinuousExposure`` in star mode).
"""

import time

from . import raw
from .connection import multiple_ips

CAM_TELE = 0
"""Live camera index for the telephoto (main) sensor."""

CAM_WIDE = 1
"""Live camera index for the wide-angle (second) sensor."""

VIEW_TELE = "View"
"""App-state key for the main (telephoto) view pipeline."""

VIEW_WIDE = "SecondView"
"""App-state key for the wide-angle view pipeline."""


@multiple_ips
def get_product_model():
    """Return ``product_model`` from :func:`raw.get_device_state`."""
    device = raw.get_device_state().get("result", {}).get("device", {})
    return device.get("product_model") or device.get("user_product_model")


@multiple_ips
def has_wide_camera(model=None):
    """Return ``True`` if *model* looks like an S30-family dual-camera device."""
    if model is None:
        model = get_product_model()
    return bool(model) and "S30" in model


@multiple_ips
def get_app_state():
    """Shortcut for ``iscope_get_app_state()['result']``."""
    return raw.iscope_get_app_state().get("result", {})


@multiple_ips
def get_second_view_state():
    """Return the ``SecondView`` sub-dict from app state, if present."""
    return get_app_state().get(VIEW_WIDE, {})


@multiple_ips
def get_selected_camera():
    """Return ``selected_cam`` from app state (``View`` or ``SecondView``)."""
    return get_app_state().get("selected_cam")


@multiple_ips
def enable_wide_camera(enabled=True):
    """Enable or disable the wide-angle camera hardware setting.

    Maps to ``set_setting(wide_cam=<bool>)`` as used by seestar_alp's
    settings page and live wide-cam toggle.

    Notes
    -----
    On some firmware builds ``get_setting()['wide_cam']`` does not reflect
    the value after a successful write.  Treat ``code == 0`` as success.
    """
    if not has_wide_camera():
        raise RuntimeError("Wide camera helpers require an S30-family device")
    return raw.set_setting(wide_cam=bool(enabled))


@multiple_ips
def switch_live_camera(index):
    """Switch the live-view camera index (tele vs wide).

    Sends ``set_setting(wide_cam=<index>)`` matching APK
    ``SwitchSecondaryCmd`` — *index* 0 selects telephoto, 1 selects wide.

    Separate calls are required: the device rejects batched
    ``selected_cam`` + ``wide_cam`` in one ``set_setting``.
    """
    if index not in (CAM_TELE, CAM_WIDE):
        raise ValueError("index must be CAM_TELE (0) or CAM_WIDE (1)")
    return raw.set_setting(wide_cam=index)


@multiple_ips
def select_camera(view):
    """Select which view pipeline is active (``View`` or ``SecondView``).

    Matches APK ``SetSelectedCamCmd``.
    """
    if view not in (VIEW_TELE, VIEW_WIDE):
        raise ValueError(f"view must be {VIEW_TELE!r} or {VIEW_WIDE!r}")
    return raw.set_setting(selected_cam=view)


@multiple_ips
def get_wide_focal_position():
    """Return wide focuser position from ``second_camera.focal_pos``."""
    setting = raw.get_setting().get("result", {})
    second = setting.get("second_camera", {})
    pos = second.get("focal_pos")
    if pos is None:
        pos = setting.get("wide_focal_pos")
    return pos


@multiple_ips
def set_wide_focal_position(position):
    """Set wide focuser position via ``wide_focal_pos`` (ALP convention)."""
    return raw.set_setting(wide_focal_pos=int(position))


@multiple_ips
def start_scenery_view(target_name="Unknown", lp_filter=False):
    """Start scenery mode with the wide camera enabled.

    After a few seconds ``SecondView`` should reach ``stage: RTSP`` with
    live video on RTSP port 4555.  Capture frames with
    :func:`seestarpy.stream.capture_rtsp_frame`.
    """
    enable_wide_camera(True)
    return raw.iscope_start_view(
        mode="scenery", target_name=target_name, lp_filter=lp_filter,
    )


@multiple_ips
def prepare_star_wide(wait_seconds=2.0):
    """Prepare star-mode live view for wide binary stream (port 4804).

    Sequence (mirrors in-app dual-camera star mode):

    1. ``enable_wide_camera(True)``
    2. ``iscope_start_view(mode='star')`` if not already exposing
    3. ``select_camera('SecondView')``
    4. ``switch_live_camera(CAM_WIDE)``

    Returns the ``SecondView`` app-state dict after *wait_seconds*.
    """
    enable_wide_camera(True)

    view = get_app_state().get(VIEW_TELE, {})
    ce = view.get("ContinuousExposure", {})
    if ce.get("state") != "working":
        raw.iscope_start_view(mode="star")

    select_camera(VIEW_WIDE)
    switch_live_camera(CAM_WIDE)

    if wait_seconds:
        time.sleep(wait_seconds)
    return get_second_view_state()
