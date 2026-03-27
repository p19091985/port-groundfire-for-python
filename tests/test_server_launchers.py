import os
import unittest

from tests.support import PROJECT_ROOT


class ServerLauncherScriptsTests(unittest.TestCase):
    def test_server_launcher_scripts_exist_and_target_standalone_server(self):
        expected = {
            "run_server.sh": "interface_net.server.demo",
            "run_server.ps1": "interface_net.server.demo",
            "run_server.bat": "interface_net.server.demo",
        }

        for file_name, marker in expected.items():
            path = os.path.join(PROJECT_ROOT, file_name)
            self.assertTrue(os.path.exists(path), file_name)
            with open(path, "r", encoding="utf-8") as handle:
                contents = handle.read()
            self.assertIn(marker, contents)


if __name__ == "__main__":
    unittest.main()
