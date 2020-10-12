from os.path import abspath, dirname
from unittest.case import TestCase
from unittest.mock import call, Mock

from monitor.monitor import Monitor


class MonitorTest(TestCase):
    def setUp(self) -> None:
        self._monitor = Monitor("ws://test.com", "eth9", "user", "pass", True)
        self._monitor._update_output = Mock()

    def test_single_frame_message(self):
        self._monitor.on_ws_message(self._read_sample("single_frame_message.txt"))
        self._monitor._update_output.assert_called_once()
        self._monitor._update_output.assert_called_with(27296, 27832, '13.123.123.123')

    def test_single_frame_multi_message(self):
        self._monitor.on_ws_message(self._read_sample("single_frame_multi_message.txt"))
        self._monitor._update_output.assert_has_calls(
            [call(27296, 27832, '13.123.123.123'), call(27304, 27760, '13.123.123.123')]
        )

    def test_multiple_frame_message(self):
        self._monitor.on_ws_message(self._read_sample("multi_frame_message_1.txt"))
        self._monitor.on_ws_message(self._read_sample("multi_frame_message_2.txt"))
        self._monitor._update_output.assert_called_once()
        self._monitor._update_output.assert_called_with(1978872, 208192, '13.123.123.123')

    def test_multiple_frame_with_naked_header(self):
        self._monitor.on_ws_message(self._read_sample("multi_frame_message_naked_1.txt"))
        self._monitor.on_ws_message(self._read_sample("multi_frame_message_naked_2.txt"))
        self._monitor._update_output.assert_called_once()
        self._monitor._update_output.assert_called_with(570848, 51624, '13.123.123.123')

    def test_human_rates(self):
        self.assertEqual(self._monitor._human_bps(123), "123 bps")
        self.assertEqual(self._monitor._human_bps(1250), "1.2 Kbps")
        self.assertEqual(self._monitor._human_bps(12500), "12.5 Kbps")
        self.assertEqual(self._monitor._human_bps(125000), "125.0 Kbps")
        self.assertEqual(self._monitor._human_bps(1250000), "1.2 Mbps")
        self.assertEqual(self._monitor._human_bps(12500000), "12.5 Mbps")
        self.assertEqual(self._monitor._human_bps(125000000), "125.0 Mbps")
        self.assertEqual(self._monitor._human_bps(1250000000), "1.2 Gbps")

    def _read_sample(self, file_name: str) -> str:
        abs_path = f"{dirname(abspath(__file__))}/{file_name}"
        with open(abs_path, "r") as file:
            return file.read()
