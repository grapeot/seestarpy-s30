"""Unit tests for Bayer postprocess helpers."""

import unittest
from unittest import mock

import numpy as np

from seestarpy import postprocess as pp


class TestPostprocessRaw(unittest.TestCase):

    def test_raw_duplicates_bayer_to_rgb(self):
        bayer = np.arange(12, dtype=np.uint16).reshape(3, 4)
        out = pp.postprocess_pixels(bayer, mode=pp.POSTPROCESS_RAW)
        self.assertEqual(out.shape, (3, 4, 3))
        np.testing.assert_array_equal(out[:, :, 0], bayer)
        np.testing.assert_array_equal(out[:, :, 1], bayer)
        np.testing.assert_array_equal(out[:, :, 2], bayer)

    def test_rgb_passthrough(self):
        rgb = np.ones((2, 2, 3), dtype=np.uint16)
        out = pp.postprocess_pixels(rgb, mode=pp.POSTPROCESS_DEBAYER)
        np.testing.assert_array_equal(out, rgb)


class TestPostprocessDebayer(unittest.TestCase):

    def test_debayer_calls_opencv(self):
        bayer = np.full((4, 4), 1024, dtype=np.uint16)
        fake_rgb8 = np.zeros((4, 4, 3), dtype=np.uint8)
        fake_cv2 = mock.Mock()
        fake_cv2.COLOR_BayerBG2RGB = 99
        fake_cv2.cvtColor.return_value = fake_rgb8

        with mock.patch.dict("sys.modules", {"cv2": fake_cv2}):
            out = pp.postprocess_pixels(
                bayer, mode=pp.POSTPROCESS_DEBAYER, bayer_pattern="BG",
            )

        fake_cv2.cvtColor.assert_called_once()
        self.assertEqual(out.shape, (4, 4, 3))
        self.assertEqual(out.dtype, np.uint16)

    def test_unknown_pattern_raises(self):
        bayer = np.zeros((2, 2), dtype=np.uint16)
        with self.assertRaises(ValueError):
            pp.debayer_bayer(bayer, pattern="XX")

    def test_unknown_mode_raises(self):
        bayer = np.zeros((2, 2), dtype=np.uint16)
        with self.assertRaises(ValueError):
            pp.postprocess_pixels(bayer, mode="invalid")


class TestSaveImagePostprocess(unittest.TestCase):

    def test_save_image_passes_postprocess(self):
        from seestarpy import stream

        header = {"width": 2, "height": 2, "img_type": stream.IMG_TYPE_PREVIEW}
        payload = np.zeros((2, 2), dtype=np.uint16).tobytes()

        with mock.patch.object(stream, "decode_payload", return_value=np.zeros((2, 2), dtype=np.uint16)), \
             mock.patch.object(stream, "_auto_stretch", return_value=np.zeros((2, 2, 3), dtype=np.uint8)), \
             mock.patch("seestarpy.postprocess.postprocess_pixels") as mock_pp, \
             mock.patch("PIL.Image.fromarray") as mock_fromarray:
            mock_pp.return_value = np.zeros((2, 2, 3), dtype=np.uint16)
            img = mock_fromarray.return_value
            stream.save_image(
                payload, header, "/tmp/out.png",
                postprocess=pp.POSTPROCESS_DEBAYER,
                bayer_pattern="BG",
            )

        mock_pp.assert_called_once()
        self.assertEqual(mock_pp.call_args.kwargs["mode"], pp.POSTPROCESS_DEBAYER)
        self.assertEqual(mock_pp.call_args.kwargs["bayer_pattern"], "BG")
        img.save.assert_called_once_with("/tmp/out.png")


if __name__ == "__main__":
    unittest.main()
