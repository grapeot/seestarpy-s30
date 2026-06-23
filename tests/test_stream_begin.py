"""Unit tests for stream.get_live_image begin_streaming lifecycle."""

import unittest
from unittest import mock

from seestarpy import stream


def _fake_header(width=100, height=50):
    return {
        "magic": stream.MAGIC_NUMBER,
        "width": width,
        "height": height,
        "length": 4,
        "img_type": stream.IMG_TYPE_PREVIEW,
    }


class TestGetLiveImageBeginStreaming(unittest.TestCase):

    def test_sends_begin_and_stop_streaming(self):
        sent = []
        sock = mock.Mock()
        sock.sendall = lambda data: sent.append(data.decode())
        sock.settimeout = mock.Mock()
        sock.close = mock.Mock()

        header = _fake_header()
        payload = b"\x00" * 4

        with mock.patch.object(stream, "_make_socket", return_value=sock), \
             mock.patch.object(stream, "_read_frame", return_value=(header, payload)):
            h, p = stream.get_live_image(ip="10.0.0.1", begin_streaming=True)

        self.assertEqual(h, header)
        self.assertEqual(p, payload)
        self.assertTrue(any('"method": "begin_streaming"' in line for line in sent))
        self.assertTrue(any('"method": "get_stacked_img"' in line for line in sent))
        self.assertTrue(any('"method": "stop_streaming"' in line for line in sent))
        sock.close.assert_called_once()

    def test_can_skip_begin_streaming(self):
        sent = []
        sock = mock.Mock()
        sock.sendall = lambda data: sent.append(data.decode())
        sock.settimeout = mock.Mock()
        sock.close = mock.Mock()

        header = _fake_header()
        payload = b"\x00" * 4

        with mock.patch.object(stream, "_make_socket", return_value=sock), \
             mock.patch.object(stream, "_read_frame", return_value=(header, payload)):
            stream.get_live_image(ip="10.0.0.1", begin_streaming=False)

        methods = [line for line in sent if '"method"' in line]
        self.assertFalse(any("begin_streaming" in m for m in methods))
        self.assertFalse(any("stop_streaming" in m for m in methods))


if __name__ == "__main__":
    unittest.main()
