# FROM: Thinkpad-Ultra7
pkgname=auri
pkgver=1.0
pkgrel=1
pkgdesc="Auri :: Advanced System Tool for CachyOS/Arch Linux"
arch=('x86_64')
license=('GPL3')
depends=('python' 'bash' 'ncurses' 'pacman')
optdepends=(
    'reflector: Mirror optimization'
    'snapper: Snapshots'
    'pipewire: Sound fix'
)
source=('auri.py')
sha256sums=('SKIP')

package() {
    install -Dm755 "$srcdir/auri.py" "$pkgdir/usr/bin/auri"
    
    # Desktop entry
    install -Dm644 /dev/null "$pkgdir/usr/share/applications/auri.desktop"
    cat > "$pkgdir/usr/share/applications/auri.desktop" << EOF
[Desktop Entry]
Name=Auri
Comment=Advanced System Tool
Exec=sudo /usr/bin/auri
Terminal=true
Type=Application
Categories=Utility;System;
Icon=utilities-system
EOF

    # Systemd service & timer
    install -Dm644 /dev/null "$pkgdir/usr/lib/systemd/system/auri.service"
    cat > "$pkgdir/usr/lib/systemd/system/auri.service" << 'EOF'
[Unit]
Description=Auri Scheduler Service
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/auri --batch
EOF

    install -Dm644 /dev/null "$pkgdir/usr/lib/systemd/system/auri.timer"
    cat > "$pkgdir/usr/lib/systemd/system/auri.timer" << 'EOF'
[Unit]
Description=Auri Weekly Maintenance

[Timer]
OnCalendar=weekly
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Safe batch config
    install -Dm644 /dev/null "$pkgdir/etc/auri/batch.json"
    cat > "$pkgdir/etc/auri/batch.json" << 'EOF'
{
    "actions": [
        "remove_lock",
        "mirror_optimizer", 
        "update_system",
        "remove_orphans",
        "clean_cache"
    ],
    "frequency": "weekly"
}
EOF
}

post-install() {
    systemctl daemon-reload
    systemctl enable --now auri.timer 2>/dev/null || true
}

post-remove() {
    systemctl disable --now auri.timer 2>/dev/null || true
}

