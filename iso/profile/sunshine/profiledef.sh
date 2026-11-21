#!/usr/bin/env bash
# shellcheck disable=SC2034
# SunshineOS live/repair/migration image profile for mkarchiso.

iso_name="sunshineos"
iso_label="SUNSHINE_$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y%m)"
iso_publisher="SunshineOS <github.com/tak0dan/SunshineOS_Development-Testing>"
iso_application="SunshineOS Live Repair and Migration"
iso_version="${SUNSHINE_ISO_VERSION:-$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y.%m.%d)}"
install_dir="sunshine"
buildmodes=('iso')
bootmodes=('bios.syslinux'
           'uefi.systemd-boot')
arch="x86_64"
kernel_params="systemd.firstboot=no"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'zstd' '-Xcompression-level' '3' '-b' '1M')
bootstrap_tarball_compression=('zstd' '-c' '-T0' '--auto-threads=logical' '--long' '-19')
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/etc/gshadow"]="0:0:400"
  ["/root"]="0:0:750"
  ["/etc/pacman.d/gnupg"]="0:0:700"
  ["/etc/sunshine"]="0:0:755"
  ["/etc/sunshine/build-id"]="0:0:644"
  ["/etc/systemd/system/serial-getty@.service.d/10-autologin.conf"]="0:0:644"
  ["/usr/share/sunshine/os-release"]="0:0:644"
  ["/usr/share/sunshine/BUILD_INFO.json"]="0:0:644"
  ["/usr/local/lib/sunshine/sunshine_live.py"]="0:0:755"
  ["/usr/local/bin/sunshine-live"]="0:0:755"
  ["/usr/local/bin/sunshine-health"]="0:0:755"
  ["/usr/local/bin/sunshine-sanity"]="0:0:755"
  ["/usr/local/bin/sunshine-update"]="0:0:755"
  ["/usr/local/bin/sunshine-upgrade"]="0:0:755"
  ["/usr/local/bin/sunshine-migrate"]="0:0:755"
  ["/usr/local/bin/sunshine-repair"]="0:0:755"
  ["/usr/local/bin/sunshine-report"]="0:0:755"
  ["/opt/sunshine/evolution-engine/src/engine.py"]="0:0:755"
)
