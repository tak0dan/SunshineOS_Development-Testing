import unittest
import sys
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE_ROOT))

from src.evolution.tools.ci_policy import audit_workflow  # noqa: E402


class CachyOSCiPolicyTests(unittest.TestCase):
    def test_CI_CACHYOS_001_flags_mutable_actions_images_and_unsafe_build_flags(self):
        workflow = """name: build
jobs:
  build:
    runs-on: ubuntu-latest
    container: cachyos/cachyos:latest
    steps:
      - uses: actions/checkout@v4
      - run: echo 'builder ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers
      - run: makepkg --skippgpcheck
"""
        codes = [finding.code for finding in audit_workflow(workflow)]
        self.assertEqual(codes.count("CI_ACTION_NOT_IMMUTABLE"), 1)
        self.assertEqual(codes.count("CI_CONTAINER_MUTABLE"), 1)
        self.assertIn("CI_UNRESTRICTED_SUDO", codes)
        self.assertIn("CI_SIGNATURE_CHECK_BYPASS", codes)
        self.assertIn("CI_PERMISSIONS_UNSCOPED", codes)

    def test_CI_CACHYOS_002_reports_privileged_pull_request_trigger(self):
        findings = audit_workflow("on:\n  pull_request_target:\n    types: [opened]\n")
        self.assertIn("CI_PRIVILEGED_PULL_REQUEST", {item.code for item in findings})

    def test_CI_CACHYOS_003_accepts_sha_pinned_action_and_digest_container(self):
        sha = "0123456789abcdef0123456789abcdef01234567"
        workflow = f"""permissions:
  contents: read
jobs:
  build:
    container: cachyos/cachyos@sha256:{'a' * 64}
    steps:
      - uses: actions/checkout@{sha}
"""
        self.assertEqual(audit_workflow(workflow), ())


class OmarchyCiPolicyTests(unittest.TestCase):
    def test_CI_OMARCHY_001_flags_mutable_docker_image_across_shell_continuation(self):
        workflow = """jobs:
  test:
    steps:
      - run: |
          docker run --rm --device /dev/kvm \\
            ghcr.io/archlinux/archlinux:latest bash -euo pipefail -c 'echo test'
"""
        findings = audit_workflow(workflow)
        finding = next(item for item in findings if item.code == "CI_DOCKER_IMAGE_MUTABLE")
        self.assertEqual(finding.line, 5)

    def test_CI_OMARCHY_002_accepts_version_or_digest_pinned_docker_images(self):
        for image in (
            "ghcr.io/archlinux/archlinux:2026.11.01",
            "ghcr.io/archlinux/archlinux@sha256:" + "a" * 64,
        ):
            with self.subTest(image=image):
                workflow = f"docker run --rm {image} bash -c 'echo test'\n"
                self.assertNotIn(
                    "CI_DOCKER_IMAGE_MUTABLE",
                    {item.code for item in audit_workflow(workflow)},
                )


if __name__ == "__main__":
    unittest.main()
