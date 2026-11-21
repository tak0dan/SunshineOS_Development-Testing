# Solutions

*   **Resolution:**  Disables `systemd-networkd` and `wait-online` via a `10-sunshine.preset` file, ensuring it runs *after* `90-systemd.preset`.
*   **Resolution:**  Implemented a `--ignore` flag to retain the kernel and headers packages during the update process.
*   **Resolution:**  Added `theme-wallpapers` to the list of tools staged by `stage-src.sh` and implemented a check to prevent `Exec` paths from pointing to non-existent tools.
