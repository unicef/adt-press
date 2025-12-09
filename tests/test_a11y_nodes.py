import json
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from adt_press.nodes import a11y_nodes


class A11yNodesTests(unittest.TestCase):
    def test_package_json_created_when_missing(self):
        run_dir = Path("/tmp/test_run_dir")
        work_dir = run_dir / ".a11y_runner"

        with mock.patch("adt_press.nodes.a11y_nodes.subprocess.run") as run_mock:
            run_mock.side_effect = [mock.Mock(stdout="", stderr="", returncode=0), mock.Mock(stdout="", stderr="", returncode=0)]

            with (
                mock.patch("pathlib.Path.mkdir"),
                mock.patch("pathlib.Path.write_text") as wt,
                mock.patch("pathlib.Path.exists", side_effect=[False, False, False, False, False, False]),
                mock.patch("tempfile.NamedTemporaryFile") as ntf,
            ):
                ntf.return_value.__enter__.return_value.name = str(work_dir / "temp.mjs")
                a11y_nodes.adt_a11y_results(str(run_dir), "done")

            first_call = run_mock.call_args_list[0]
            self.assertEqual(first_call.args[0], ["npm", "install"])
            self.assertEqual(Path(first_call.kwargs.get("cwd")).resolve(), work_dir.resolve())
            self.assertTrue(wt.called)

    def test_returns_error_when_node_fails(self):
        with mock.patch("adt_press.nodes.a11y_nodes.subprocess.run") as run_mock:
            run_mock.side_effect = [
                mock.Mock(stdout="", stderr="", returncode=0),
                subprocess.CalledProcessError(1, ["node"], stderr="boom"),
            ]
            with (
                mock.patch("tempfile.NamedTemporaryFile") as ntf,
                mock.patch("pathlib.Path.exists", return_value=True),
                mock.patch("pathlib.Path.read_text", return_value=json.dumps({"files": []})),
            ):
                ntf.return_value.__enter__.return_value.name = "/tmp/run/tmp.mjs"
                result = a11y_nodes.adt_a11y_results("/tmp/run", "done")
        self.assertIn("error", result)
        self.assertIn("boom", result["error"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
