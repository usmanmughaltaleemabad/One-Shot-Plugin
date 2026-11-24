import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "block-bad-commands.sh"

class HookRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.plugin = self.root / "plugin"
        self.repo.mkdir()
        (self.plugin / ".claude-plugin").mkdir(parents=True)
        (self.plugin / ".claude-plugin" / "plugin.json").write_text('{"version":"1.2.9"}')
        (self.plugin / "CHANGELOG.md").write_text("# Changelog\n\n## v1.2.9\n")
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Hook Test")

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, capture_output=True, check=True)

    def run_hook(self, command):
        payload = json.dumps({"tool_input": {"command": command}})
        env = os.environ.copy()
        env["CLAUDE_PLUGIN_ROOT"] = str(self.plugin)
        return subprocess.run([os.environ.get("HOOK_BASH", "bash"), str(HOOK)], input=payload, text=True, cwd=self.repo,
                              env=env, capture_output=True)

    def stage(self, name, content):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        self.git("add", "--", name)

    def test_benign_commit_message_can_discuss_credentials(self):
        self.stage("docs/policy.md", "The credentials policy is documented here.\n")
        result = self.run_hook("git commit -m 'document credentials policy and secret handling'")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_high_confidence_secret_value_is_blocked_without_echo(self):
        token = "AKIA" + "1234567890ABCDEF"
        self.stage("config.txt", f"access={token}\n")
        result = self.run_hook("git commit -m 'update config documentation'")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(token, result.stderr)

    def test_staged_env_file_is_blocked(self):
        self.stage(".env", "EXAMPLE=value\n")
        result = self.run_hook("git commit -m 'update local settings'")
        self.assertEqual(result.returncode, 2)

    def test_env_example_is_allowed(self):
        self.stage(".env.example", "EXAMPLE=value\n")
        result = self.run_hook("git commit -m 'document environment setup'")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_literal_word_secret_is_not_a_credential_match(self):
        self.stage("docs/secret-management.md", "Explain how secrets are handled.\n")
        result = self.run_hook("git commit -m 'add secret-management guide'")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_explicit_env_add_remains_blocked(self):
        result = self.run_hook("git add .env")
        self.assertEqual(result.returncode, 2)

    def test_private_key_file_is_blocked(self):
        self.stage("certs/service.pem", "not-a-real-key\n")
        result = self.run_hook("git commit -m 'add certificate fixture'")
        self.assertEqual(result.returncode, 2)

if __name__ == "__main__":
    unittest.main()