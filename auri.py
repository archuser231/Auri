#!/usr/bin/env python3
import curses
import subprocess
import os
import sys
import json
import shutil
import datetime
import tempfile

PACMAN_LOCK = "/var/lib/pacman/db.lck"
LOG_FILE = "/var/log/auri.log"
BATCH_CONFIG = "/etc/auri/batch.json"
SCHEDULER_CONFIG = "/etc/auri/scheduler.json"
LINES_PER_PAGE = 20

# -----------------------------
# CORE HELPERS
# -----------------------------
def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.datetime.now()} :: {msg}\n")

def safe_addstr(stdscr, txt):
    try:
        stdscr.addstr(txt)
    except curses.error:
        pass

def run(cmd, stdscr=None):
    log(f"RUN: {cmd}")
    p = subprocess.Popen(
        cmd, shell=True, executable="/bin/bash",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    if not stdscr:
        p.wait()
        return p.returncode

    count = 0
    for line in p.stdout:
        safe_addstr(stdscr, line)
        count += 1
        if count % LINES_PER_PAGE == 0:
            safe_addstr(stdscr, "\n--More--")
            stdscr.getch()
            safe_addstr(stdscr, "\n")
        stdscr.refresh()
    p.wait()
    if p.returncode != 0:
        safe_addstr(stdscr, f"\n❌ Command failed ({p.returncode})\n")
    return p.returncode

def header(stdscr, title):
    stdscr.clear()
    safe_addstr(stdscr, f"Auri the Garuda rani for cachy-os by thinkpad_ultra7 @archuser231 :: {title}\n")
    safe_addstr(stdscr, "="*40 + "\n\n")

def confirm(stdscr, msg):
    safe_addstr(stdscr, f"{msg}\nType YES to continue: ")
    curses.echo()
    ans = stdscr.getstr(0,30).decode().strip()
    curses.noecho()
    return ans == "YES"

def ensure_batch_config():
    if not os.path.exists(BATCH_CONFIG):
        os.makedirs(os.path.dirname(BATCH_CONFIG), exist_ok=True)
        with open(BATCH_CONFIG,"w") as f:
            json.dump({"actions":["remove_lock","dns_reset","mirror_optimizer","update_system"]}, f, indent=4)

def ensure_scheduler_config():
    if not os.path.exists(SCHEDULER_CONFIG):
        os.makedirs(os.path.dirname(SCHEDULER_CONFIG), exist_ok=True)
        with open(SCHEDULER_CONFIG,"w") as f:
            json.dump({"actions":[],"enabled":False,"interval":"weekly"}, f, indent=4)

# -----------------------------
# SNAPSHOT MANAGER
# -----------------------------
def snapshot(stdscr,label="snapshot"):
    header(stdscr,f"Snapshot: {label}")
    run(f"snapper create -d 'auri {label}'", stdscr)
    safe_addstr(stdscr,"\nPress any key...")
    stdscr.getch()

# -----------------------------
# ACTIONS
# -----------------------------
def remove_lock(stdscr):
    header(stdscr,"Remove pacman lock")
    run("rm -f /var/lib/pacman/db.lck", stdscr)
    safe_addstr(stdscr,"\nPress any key...")
    stdscr.getch()

def mirror_optimizer(stdscr):
    header(stdscr,"Mirror Optimizer")
    run("reflector --latest 20 --protocol https --sort rate --save /etc/pacman.d/mirrorlist", stdscr)
    safe_addstr(stdscr,"\nPress any key...")
    stdscr.getch()

def update_system(stdscr):
    header(stdscr,"Update System")
    run("pacman -Syu --noconfirm --needed --overwrite '*'", stdscr)
    safe_addstr(stdscr,"\nPress any key...")
    stdscr.getch()

def full_fix(stdscr):
    header(stdscr,"Full System Fix")
    run("pacman -Syu --noconfirm --needed --overwrite '*'", stdscr)
    safe_addstr(stdscr,"\nPress any key...")
    stdscr.getch()

def reinstall_all(stdscr):
    header(stdscr,"Reinstall ALL packages")
    if not confirm(stdscr,"⚠️ This will reinstall everything"):
        return
    run("pacman -Qnq | pacman -S --noconfirm --needed -", stdscr)
    safe_addstr(stdscr,"\nPress any key...")
    stdscr.getch()

def remove_orphans(stdscr):
    header(stdscr,"Remove Orphans")
    run("pacman -Qdtq | pacman -Rns --noconfirm -", stdscr)
    safe_addstr(stdscr,"\nPress any key...")
    stdscr.getch()

def clean_cache(stdscr):
    header(stdscr,"Clean Cache")
    run("pacman -Sc --noconfirm", stdscr)
    safe_addstr(stdscr,"\nPress any key...")
    stdscr.getch()

def sound_fix(stdscr):
    header(stdscr,"Sound Fix")
    run("pacman -S --noconfirm pipewire pipewire-alsa pipewire-pulse wireplumber", stdscr)
    run("systemctl --user enable --now pipewire pipewire-pulse wireplumber", stdscr)
    safe_addstr(stdscr,"\nPress any key...")
    stdscr.getch()

def reset_snapper(stdscr):
    header(stdscr,"Reset Snapper")
    if not confirm(stdscr,"⚠️ Reset Snapper config?"):
        return
    run("snapper -c root delete-config", stdscr)
    run("snapper -c root create-config /", stdscr)
    safe_addstr(stdscr,"\nPress any key...")
    stdscr.getch()

def dns_reset(stdscr):
    header(stdscr,"DNS Reset")
    run("""
rm -f /etc/resolv.conf
ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
systemctl restart systemd-resolved
systemctl restart NetworkManager
resolvectl flush-caches || true
resolvectl status || true
""", stdscr)
    safe_addstr(stdscr,"\nPress any key...")
    stdscr.getch()

def kernel_manager(stdscr):
    curses.endwin()
    os.system("cachyos-kernel-manager || cachyos-settings || echo 'No kernel manager'")
    input("Press Enter...")
    curses.initscr()

def virtualization(stdscr):
    header(stdscr,"Virtualization Stack")
    run("""
pacman -S --noconfirm qemu virt-manager virt-viewer dnsmasq vde2 bridge-utils \
openbsd-netcat ebtables iptables libguestfs fuse2 gtkmm linux-headers pcsclite \
libcanberra
systemctl enable --now libvirtd
usermod -aG libvirt $(logname)
""", stdscr)
    safe_addstr(stdscr,"\nPress any key...")
    stdscr.getch()

# -----------------------------
# KEYRING & REPOS
# -----------------------------
OFFICIAL_REPOS = {"core","extra","community","multilib","cachyos"}
OPTIONAL_REPOS = {"chaotic","blackarch","archstrike"}
KNOWN_KEYRINGS = {
    "arch":"archlinux-keyring",
    "cachyos":"cachyos-keyring",
    "chaotic":"chaotic-keyring",
    "blackarch":"blackarch-keyring",
    "archstrike":"archstrike-keyring"
}

def manage_repos_and_keyrings(stdscr):
    header(stdscr,"Repos & Keyrings")
    active = []
    with open("/etc/pacman.conf","r") as f:
        for line in f:
            line=line.strip()
            if line.startswith("[") and line.endswith("]"):
                active.append(line[1:-1].lower())

    to_update = []
    for r in active:
        kr = KNOWN_KEYRINGS.get(r)
        if kr:
            if stdscr: safe_addstr(stdscr,f"Update keyring for {r}? (y/n): ")
            ans = "y" if stdscr is None else stdscr.getstr(0,3).decode().strip().lower()
            if ans=="y": to_update.append(kr)

    if to_update:
        run("pacman -Sy --noconfirm " + " ".join(to_update), stdscr)
        run("pacman-key --init", stdscr)
        for kr in to_update: run(f"pacman-key --populate {kr.split('-keyring')[0]}", stdscr)
        run("pacman-key --refresh-keys", stdscr)
    safe_addstr(stdscr,"\nPress any key...")
    stdscr.getch()

# -----------------------------
# WINE INSTALL
# -----------------------------
def wine_install(stdscr, mode):
    header(stdscr, f"Wine Install: {mode}")
    
    cmd = ""
    if mode == "x86": cmd = "pacman -S --noconfirm --needed wine lib32-wine winetricks zenity"
    elif mode == "x64": cmd = "pacman -S --noconfirm --needed wine winetricks zenity"
    elif mode == "work": cmd = "pacman -S --noconfirm --needed wine-cachyos lib32-wine-cachyos winetricks zenity"
    elif mode == "both": cmd = "pacman -S --noconfirm --needed wine lib32-wine winetricks zenity"
    elif mode == "test": cmd = "pacman -S --noconfirm --needed wine lib32-wine winetricks zenity"

    ret = run(cmd, stdscr)
    
    if ret != 0:
        safe_addstr(stdscr, "\n" + "!"*50 + "\n")
        safe_addstr(stdscr, "❌ INSTALLATION FAILED!\n")
        safe_addstr(stdscr, "It might be because [multilib] is not enabled.\n\n")
        safe_addstr(stdscr, "TO CHECK/ENABLE MULTILIB:\n")
        safe_addstr(stdscr, "1. Run: sudo nano /etc/pacman.conf\n")
        safe_addstr(stdscr, "2. Find the [multilib] section.\n")
        safe_addstr(stdscr, "3. Uncomment (remove #) [multilib] and the Include line.\n")
        safe_addstr(stdscr, "4. Save & Exit: Press Ctrl+X, then Y, then Enter.\n")
        safe_addstr(stdscr, "5. Run: sudo pacman -Syu\n")
        safe_addstr(stdscr, "!"*50 + "\n")

    safe_addstr(stdscr, "\nPress any key to return...")
    stdscr.getch()
# -----------------------------
# ACTIONS LIST
# -----------------------------
ACTIONS = [
    ("Remove pacman lock", remove_lock),
    ("DNS Reset", dns_reset),
    ("Optimize Mirrors", mirror_optimizer),
    ("Update System", update_system),
    ("Snapshot pre-update", lambda s: snapshot(s,"pre-update")),
    ("Snapshot post-update", lambda s: snapshot(s,"post-update")),
    ("Full System Fix", full_fix),
    ("Reinstall ALL Packages", reinstall_all),
    ("Remove Orphan Packages", remove_orphans),
    ("Clean Pacman Cache", clean_cache),
    ("Sound Fix", sound_fix),
    ("Reset Snapper", reset_snapper),
    ("Kernel Manager", kernel_manager),
    ("Install Virtualization Stack", virtualization),
    ("Repos & Keyrings", manage_repos_and_keyrings),
    ("Wine x86", lambda s: wine_install(s,"x86")),
    ("Wine x64", lambda s: wine_install(s,"x64")),
    ("Wine WORK", lambda s: wine_install(s,"work")),
    ("Wine both", lambda s: wine_install(s,"both")),
    ("Wine test", lambda s: wine_install(s,"test"))
]

# -----------------------------
# BATCH MODE
# -----------------------------
def batch_menu(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    ensure_batch_config()
    with open(BATCH_CONFIG) as f:
        cfg = json.load(f)
    selected = {fn.__name__: (fn.__name__ in cfg.get("actions", [])) for label, fn in ACTIONS}

    options = [(label, fn.__name__) for label, fn in ACTIONS]
    cur = 0
    while True:
        stdscr.clear()
        safe_addstr(stdscr,"Batch Mode Selection\n====================\nArrow keys: move | SPACE: toggle | ENTER: save\n\n")
        for i, (label, act_name) in enumerate(options):
            mark = "[X]" if selected[act_name] else "[ ]"
            if i==cur: stdscr.addstr(f"> {mark} {label}\n", curses.A_REVERSE)
            else: safe_addstr(stdscr,f"  {mark} {label}\n")
        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")) and cur>0: cur-=1
        elif key in (curses.KEY_DOWN, ord("j")) and cur<len(options)-1: cur+=1
        elif key==ord(" "):
            act_name = options[cur][1]
            selected[act_name] = not selected[act_name]
        elif key in (10,13):
            actions_to_run = [act for act,sel in selected.items() if sel]
            os.makedirs(os.path.dirname(BATCH_CONFIG), exist_ok=True)
            with open(BATCH_CONFIG,"w") as f:
                json.dump({"actions": actions_to_run},f,indent=4)
            safe_addstr(stdscr,"\n✅ Batch config saved!\n")
            stdscr.getch()
            break

# -----------------------------
# SCHEDULER MENU
# -----------------------------
INTERVALS = ["on-boot","hourly","daily","weekly","monthly"]
def scheduler_menu(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    ensure_scheduler_config()
    with open(SCHEDULER_CONFIG) as f:
        cfg = json.load(f)
    selected = {fn.__name__: (fn.__name__ in cfg.get("actions", [])) for label, fn in ACTIONS}
    cur = 0
    interval_idx = INTERVALS.index(cfg.get("interval","weekly")) if cfg.get("interval") in INTERVALS else 3
    enabled = cfg.get("enabled",False)
    options = [(label, fn.__name__) for label, fn in ACTIONS]

    while True:
        stdscr.clear()
        safe_addstr(stdscr,"Scheduler Configuration\n======================\nArrow: move | SPACE: toggle | i: interval | e: enable | ENTER: save\n\n")
        safe_addstr(stdscr,f"Enabled: {'ON' if enabled else 'OFF'}\nInterval: {INTERVALS[interval_idx]}\n\n")
        for i,(label, act_name) in enumerate(options):
            mark = "[X]" if selected[act_name] else "[ ]"
            if i==cur: stdscr.addstr(f"> {mark} {label}\n", curses.A_REVERSE)
            else: safe_addstr(stdscr,f"  {mark} {label}\n")
        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")) and cur>0: cur-=1
        elif key in (curses.KEY_DOWN, ord("j")) and cur<len(options)-1: cur+=1
        elif key==ord(" "):
            act_name = options[cur][1]
            selected[act_name] = not selected[act_name]
        elif key==ord("i"):
            interval_idx = (interval_idx+1)%len(INTERVALS)
        elif key==ord("e"):
            enabled = not enabled
        elif key in (10,13):
            # save config
            actions_to_run = [act for act,sel in selected.items() if sel]
            os.makedirs(os.path.dirname(SCHEDULER_CONFIG), exist_ok=True)
            with open(SCHEDULER_CONFIG,"w") as f:
                json.dump({"actions":actions_to_run,"enabled":enabled,"interval":INTERVALS[interval_idx]},f,indent=4)
            # create systemd service/timer
            timer_path = "/etc/systemd/system/auri.timer"
            service_path = "/etc/systemd/system/auri.service"
            with open(service_path,"w") as f:
                f.write(f"""[Unit]
Description=Auri Scheduled Service
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/auri --batch
""")
            oncalendar = {"on-boot":"OnBootSec=1min",
                          "hourly":"OnCalendar=hourly",
                          "daily":"OnCalendar=daily",
                          "weekly":"OnCalendar=weekly",
                          "monthly":"OnCalendar=monthly"}[INTERVALS[interval_idx]]
            with open(timer_path,"w") as f:
                f.write(f"""[Unit]
Description=Auri Scheduled Timer

[Timer]
{oncalendar}
Persistent=true

[Install]
WantedBy=timers.target
""")
            subprocess.call("systemctl daemon-reload", shell=True)
            if enabled:
                subprocess.call("systemctl enable --now auri.timer", shell=True)
            else:
                subprocess.call("systemctl disable --now auri.timer", shell=True)
            safe_addstr(stdscr,"\n✅ Scheduler saved!\n")
            stdscr.getch()
            break

# -----------------------------
# MAIN MENU
# -----------------------------
MAIN_ACTIONS = ACTIONS + [
    ("Batch Mode / Scheduler", batch_menu),
    ("Configure Scheduler / Timer", scheduler_menu),
    ("Exit", None)
]

def menu(stdscr):
    curses.curs_set(0)
    cur = 0
    while True:
        stdscr.clear()
        safe_addstr(stdscr,"Auri :: Advanced System Tool\n")
        safe_addstr(stdscr,"="*40 + "\n\n")
        for i,(label,_) in enumerate(MAIN_ACTIONS):
            if i==cur: stdscr.addstr("> " + label + "\n", curses.A_REVERSE)
            else: safe_addstr(stdscr,"  " + label + "\n")
        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")) and cur>0: cur-=1
        elif key in (curses.KEY_DOWN, ord("j")) and cur<len(MAIN_ACTIONS)-1: cur+=1
        elif key in (10,13):
            if MAIN_ACTIONS[cur][1] is None: break
            MAIN_ACTIONS[cur][1](stdscr)

# -----------------------------
# MAIN
# -----------------------------
def main():
    if os.geteuid()!=0:
        print("Run Auri as root.")
        sys.exit(1)
    ensure_batch_config()
    ensure_scheduler_config()
    if "--batch" in sys.argv:
        with open(BATCH_CONFIG) as f:
            cfg=json.load(f)
        for act_name in cfg.get("actions",[]):
            for _,fn in ACTIONS:
                if fn and fn.__name__==act_name: fn(None)
    else:
        curses.wrapper(menu)

if __name__=="__main__":
    main()
