Auri

By Thinkpad-Ultra7

Auri is an advanced system tool inspired by Garuda Rani, designed for CachyOS. It provides a TUI (terminal user interface) to manage system maintenance, updates, snapshots, keyrings, and more.

Features

System update with mirror optimization

Keyring repair and update

Snapshots management via Snapper

Cache and orphan cleanup

Wine installer for x86, x64, or both

Virtualization tools installation and setup

Fully batch-capable with scheduler (systemd timer)

Lightweight TUI using curses, no heavy GUI required

Installation

1. Clone the repository:
git clone https://github.com/archuser231/Auri.git

2. Enter the directory:
cd Auri

3. Build and install the package:
makepkg -si

4. Launch Auri:
auri

After installation, a systemd timer is automatically enabled to run batch actions weekly.

Batch Configuration (/etc/auri/batch.json)

The default batch file is generated automatically at install:

{ "actions": [ "remove_lock", "mirror_optimizer", "update_system", "remove_orphans", "clean_cache" ], "frequency": "weekly" }

You can edit this file to customize which actions run automatically.

Usage

Launch from terminal:

auri

Or access it from menu launcher 

Navigate the TUI with arrow keys, select actions, or run batch mode via scheduler.

License

This project is licensed under GPLv3. See the LICENSE file for full details.
