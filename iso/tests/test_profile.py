from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

PROFILE = Path(__file__).resolve().parents[1] / "profile" / "sunshine"


class ProfileTests(unittest.TestCase):
    def test_profiledef_declares_bootable_image(self):
        path = PROFILE / "profiledef.sh"
        self.assertTrue(path.is_file())
        text = path.read_text()
        for token in ('iso_name="sunshineos"', 'install_dir="sunshine"',
                      "bootmodes=", "bios.syslinux", "uefi.systemd-boot",
                      'airootfs_image_type="squashfs"', "file_permissions="):
            self.assertIn(token, text)
        if shutil.which("bash"):
            proc = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_boot_loaders_use_archiso_placeholders(self):
        boot_files = [
            PROFILE / "syslinux/archiso_sys-linux.cfg",
            PROFILE / "efiboot/loader/entries/01-sunshine-linux.conf",
        ]
        for path in boot_files:
            self.assertTrue(path.is_file(), path)
            text = path.read_text()
            self.assertIn("%INSTALL_DIR%", text)
            self.assertIn("%ARCHISO_UUID%", text)
            self.assertIn("vmlinuz-linux", text)
            self.assertIn("cow_spacesize=4G", text)

    def test_serial_console_autologin_is_configured(self):
        dropin = PROFILE / "airootfs/etc/systemd/system/serial-getty@.service.d/10-autologin.conf"
        self.assertTrue(dropin.is_file())
        self.assertIn("--autologin root", dropin.read_text())
        for path in (PROFILE / "syslinux/archiso_sys-linux.cfg",
                     PROFILE / "efiboot/loader/entries/01-sunshine-linux.conf"):
            text = path.read_text()
            self.assertIn("systemd.firstboot=no", text, path)
            self.assertIn("console=ttyS0,115200n8", text, path)

    def test_gui_console_autologin_is_configured(self):
        dropin = PROFILE / "airootfs/etc/systemd/system/getty@tty1.service.d/10-autologin.conf"
        self.assertTrue(dropin.is_file())
        self.assertIn("--autologin root", dropin.read_text())
        permissions = (PROFILE / "profiledef.sh").read_text()
        self.assertIn('/etc/systemd/system/getty@tty1.service.d/10-autologin.conf', permissions)

    def test_live_console_identity_is_sunshineos(self):
        issue = PROFILE / "airootfs/etc/issue"
        self.assertTrue(issue.is_file())
        text = issue.read_text()
        self.assertIn("SunshineOS", text)
        self.assertNotIn("Arch Linux", text)
        hostname = PROFILE / "airootfs/etc/hostname"
        self.assertTrue(hostname.is_file())
        self.assertEqual(hostname.read_text().strip(), "sunshineos")
        permissions = (PROFILE / "profiledef.sh").read_text()
        self.assertIn('["/etc/issue"]="0:0:644"', permissions)
        self.assertIn('["/etc/hostname"]="0:0:644"', permissions)

    def test_pacman_configurations_declare_architecture(self):
        for path in (PROFILE / "pacman.conf", PROFILE / "airootfs/etc/pacman.conf"):
            self.assertTrue(path.is_file(), path)
            self.assertIn("Architecture = auto", path.read_text())

    def test_boot_loader_entry_points_exist(self):
        loader = PROFILE / "efiboot/loader/loader.conf"
        self.assertTrue(loader.is_file())
        self.assertIn("default 01-sunshine-linux.conf", loader.read_text())
        syslinux = PROFILE / "syslinux/syslinux.cfg"
        self.assertTrue(syslinux.is_file())
        self.assertIn("INCLUDE archiso_sys-linux.cfg", syslinux.read_text())

    def test_packages_include_build_and_repair_dependencies(self):
        packages = {line.strip() for line in (PROFILE / "packages.x86_64").read_text().splitlines()
                    if line.strip() and not line.startswith("#")}
        required = {"base", "linux", "mkinitcpio", "mkinitcpio-archiso", "syslinux",
                    "btrfs-progs", "snapper", "python3", "pacman-contrib", "arch-install-scripts",
                    "squashfs-tools", "openssh"}
        self.assertTrue(required.issubset(packages), sorted(required - packages))

    def test_airootfs_identity_and_startup_assessment(self):
        identity = PROFILE / "airootfs/usr/share/sunshine/os-release"
        self.assertTrue(identity.is_file())
        self.assertIn('ID=sunshine', identity.read_text())
        hook = PROFILE / "airootfs/etc/pacman.d/hooks/99-sunshine-identity.hook"
        self.assertTrue(hook.is_file())
        self.assertIn("remove from airootfs", hook.read_text())
        service = PROFILE / "airootfs/etc/systemd/system/sunshine-startup-assessment.service"
        self.assertTrue(service.is_file())
        self.assertIn("sunshine-report", service.read_text())
        link = PROFILE / "airootfs/etc/systemd/system/multi-user.target.wants/sunshine-startup-assessment.service"
        self.assertTrue(link.is_symlink())
        self.assertTrue(link.resolve().is_file())


if __name__ == "__main__":
    unittest.main()
