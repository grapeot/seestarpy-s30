"""Display-oriented post-processing for decoded Seestar preview frames.

Preview frames from the 4800/4804 binary stream are 16-bit Bayer mosaics
(``ndim == 2``).  Stacked frames are already RGB (``ndim == 3``).

The default post-process mode (``"raw"``) duplicates the Bayer plane into
pseudo-RGB — the historical behaviour of :func:`stream.save_image`.

Use ``postprocess="debayer"`` to demosaic Bayer previews into colour RGB
before stretch/save.  Requires ``opencv-python`` or ``opencv-python-headless``.
"""

from __future__ import annotations

POSTPROCESS_RAW = "raw"
"""Duplicate single-channel Bayer into pseudo-RGB (legacy default)."""

POSTPROCESS_DEBAYER = "debayer"
"""Demosaic Bayer previews to RGB via OpenCV."""

SUPPORTED_POSTPROCESS = (POSTPROCESS_RAW, POSTPROCESS_DEBAYER)

# S30 Pro tele (IMX585) on FW 7.75: ``get_camera_info()['debayer_pattern']``
# reports ``"GR"``, but live comparison favours OpenCV BayerBG on this device.
DEFAULT_BAYER_PATTERN = "BG"

_BAYER_TO_CV2_ATTR = {
    "GR": "COLOR_BayerGR2RGB",
    "RG": "COLOR_BayerRG2RGB",
    "GB": "COLOR_BayerGB2RGB",
    "BG": "COLOR_BayerBG2RGB",
}


def debayer_bayer(bayer, pattern=DEFAULT_BAYER_PATTERN):
    """Demosaic a 16-bit Bayer array to 8-bit RGB.

    Parameters
    ----------
    bayer : numpy.ndarray
        ``(H, W)`` uint16 Bayer mosaic.
    pattern : str, optional
        One of ``"GR"``, ``"RG"``, ``"GB"``, ``"BG"`` (OpenCV naming).

    Returns
    -------
    numpy.ndarray
        ``(H, W, 3)`` uint8 RGB.

    Raises
    ------
    ValueError
        If *pattern* is unknown or *bayer* is not 2-D.
    ImportError
        If OpenCV is not installed.
    """
    import numpy as np

    bayer = np.asarray(bayer)
    if bayer.ndim != 2:
        raise ValueError(f"debayer_bayer expects 2D input, got shape {bayer.shape}")

    attr = _BAYER_TO_CV2_ATTR.get(pattern)
    if attr is None:
        raise ValueError(
            f"Unknown Bayer pattern {pattern!r}; "
            f"expected one of {sorted(_BAYER_TO_CV2_ATTR)}"
        )

    try:
        import cv2
    except ImportError as exc:
        raise ImportError(
            "debayer postprocess requires opencv-python or "
            "opencv-python-headless (uv pip install opencv-python-headless)"
        ) from exc

    code = getattr(cv2, attr)
    b8 = (bayer >> 8).astype(np.uint8)
    return cv2.cvtColor(b8, code)


def postprocess_pixels(arr, mode=POSTPROCESS_RAW, bayer_pattern=DEFAULT_BAYER_PATTERN):
    """Convert a decoded payload array into RGB uint16 for stretch/save.

    Parameters
    ----------
    arr : numpy.ndarray
        Output of :func:`stream.decode_payload` — ``(H, W)`` Bayer uint16
        or ``(H, W, 3)`` stacked RGB uint16.
    mode : str, optional
        ``"raw"`` (default) or ``"debayer"``.
    bayer_pattern : str, optional
        Bayer layout for ``mode="debayer"``.  Default
        :data:`DEFAULT_BAYER_PATTERN` (``"BG"`` on verified S30 Pro).

    Returns
    -------
    numpy.ndarray
        ``(H, W, 3)`` uint16 RGB suitable for :func:`stream._auto_stretch`.
    """
    import numpy as np

    arr = np.asarray(arr)
    if arr.ndim == 3:
        return arr

    if mode == POSTPROCESS_RAW:
        return np.stack([arr, arr, arr], axis=2)

    if mode == POSTPROCESS_DEBAYER:
        rgb8 = debayer_bayer(arr, pattern=bayer_pattern)
        return rgb8.astype(np.uint16) * 257

    raise ValueError(
        f"Unknown postprocess mode {mode!r}; "
        f"expected one of {SUPPORTED_POSTPROCESS}"
    )
