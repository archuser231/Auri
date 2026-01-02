# Maintainer: Thinkpad-Ultra7 / archuser231
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
    # Installer le script Python
    install -Dm755 "$srcdir/auri.py" "$pkgdir/usr/bin/auri"

    # Créer les configs JSON par défaut
    mkdir -p "$pkgdir/etc/auri"
    echo '{"actions":["remove_lock","dns_reset","mirror_optimizer","update_system"]}' > "$pkgdir/etc/auri/batch.json"
    echo '{"actions":[],"enabled":false,"interval":"weekly"}' > "$pkgdir/etc/auri/scheduler.json"

    # Desktop entry
    mkdir -p "$pkgdir/usr/share/applications"
    echo '[Desktop Entry]' > "$pkgdir/usr/share/applications/auri.desktop"
    echo 'Name=Auri' >> "$pkgdir/usr/share/applications/auri.desktop"
    echo 'Comment=Advanced System Tool' >> "$pkgdir/usr/share/applications/auri.desktop"
    echo 'Exec=sudo /usr/bin/auri' >> "$pkgdir/usr/share/applications/auri.desktop"
    echo 'Terminal=true' >> "$pkgdir/usr/share/applications/auri.desktop"
    echo 'Type=Application' >> "$pkgdir/usr/share/applications/auri.desktop"
    echo 'Categories=Utility;System;' >> "$pkgdir/usr/share/applications/auri.desktop"
    echo 'Icon=utilities-system' >> "$pkgdir/usr/share/applications/auri.desktop"

    # systemd service
    mkdir -p "$pkgdir/usr/lib/systemd/system"
    echo '[Unit]' > "$pkgdir/usr/lib/systemd/system/auri.service"
    echo 'Description=Auri Scheduled Service' >> "$pkgdir/usr/lib/systemd/system/auri.service"
    echo 'After=network.target' >> "$pkgdir/usr/lib/systemd/system/auri.service"
    echo '' >> "$pkgdir/usr/lib/systemd/system/auri.service"
    echo '[Service]' >> "$pkgdir/usr/lib/systemd/system/auri.service"
    echo 'Type=oneshot' >> "$pkgdir/usr/lib/systemd/system/auri.service"
    echo 'ExecStart=/usr/bin/auri --batch' >> "$pkgdir/usr/lib/systemd/system/auri.service"

    # systemd timer
    echo '[Unit]' > "$pkgdir/usr/lib/systemd/system/auri.timer"
    echo 'Description=Auri Scheduled Timer' >> "$pkgdir/usr/lib/systemd/system/auri.timer"
    echo '' >> "$pkgdir/usr/lib/systemd/system/auri.timer"
    echo '[Timer]' >> "$pkgdir/usr/lib/systemd/system/auri.timer"
    echo 'OnCalendar=weekly' >> "$pkgdir/usr/lib/systemd/system/auri.timer"
    echo 'Persistent=true' >> "$pkgdir/usr/lib/systemd/system/auri.timer"
    echo '' >> "$pkgdir/usr/lib/systemd/system/auri.timer"
    echo '[Install]' >> "$pkgdir/usr/lib/systemd/system/auri.timer"
    echo 'WantedBy=timers.target' >> "$pkgdir/usr/lib/systemd/system/auri.timer"

    # Manpage (English)
    mkdir -p "$pkgdir/usr/share/man/man1"
    echo '.TH AURI 1 "2026-01-02" "1.0" "Auri Manual"' > "$pkgdir/usr/share/man/man1/auri.1"
    echo '.SH NAME' >> "$pkgdir/usr/share/man/man1/auri.1"
    echo 'Auri \- Advanced system management tool for CachyOS/Arch Linux' >> "$pkgdir/usr/share/man/man1/auri.1"
    echo '.SH SYNOPSIS' >> "$pkgdir/usr/share/man/man1/auri.1"
    echo 'auri [--batch] [--help]' >> "$pkgdir/usr/share/man/man1/auri.1"
    echo '.SH DESCRIPTION' >> "$pkgdir/usr/share/man/man1/auri.1"
    echo 'Auri is a terminal-based system tool for CachyOS/Arch Linux.' >> "$pkgdir/usr/share/man/man1/auri.1"
    echo 'It can update your system, manage repos, optimize mirrors, reset DNS, manage snapshots,' >> "$pkgdir/usr/share/man/man1/auri.1"
    echo 'install Wine, handle sound fixes, and more.' >> "$pkgdir/usr/share/man/man1/auri.1"
    echo '.SH OPTIONS' >> "$pkgdir/usr/share/man/man1/auri.1"
    echo '--batch      Run the batch actions automatically' >> "$pkgdir/usr/share/man/man1/auri.1"
    echo '--help       Show this manual page' >> "$pkgdir/usr/share/man/man1/auri.1"
    echo '.SH AUTHOR' >> "$pkgdir/usr/share/man/man1/auri.1"
    echo 'Thinkpad-Ultra7 <thinkpad@example.com>' >> "$pkgdir/usr/share/man/man1/auri.1"
}

post_install() {
    systemctl daemon-reload
    systemctl enable --now auri.timer 2>/dev/null || true
    echo "Auri installed! Timer enabled. Use 'man auri' for help."
}

post_remove() {
    systemctl disable --now auri.timer 2>/dev/null || true
}
