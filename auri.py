#!/usr/bin/env python3
import curses, subprocess, os, sys, shutil, datetime, tempfile, json

PACMAN_LOCK = "/var/lib/pacman/db.lck"
LOG_FILE = "/var/log/auri.log"
BATCH_CONFIG = "/etc/auri/batch.json"

# -----------------------------
# Helpers
# -----------------------------
def log_action(action):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.datetime.now()} :: {action}\n")

def safe_addstr(stdscr, text):
    try:
        stdscr.addstr(str(text))
    except curses.error:
        pass

def run(cmd, stdscr=None):
    log_action("RUN: " + " ".join(cmd))
    if shutil.which(cmd[0]) is None:
        log_action(f"Command not found: {cmd[0]}")
        if stdscr: safe_addstr(stdscr,f"❌ Command not found: {cmd[0]}\n")
        return 1
    if stdscr:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        count = 0
        for line in p.stdout:
            safe_addstr(stdscr,line)
            stdscr.refresh()
            count += 1
            if count % 20 == 0:  # pause toutes les 20 lignes
                safe_addstr(stdscr,"\n--More-- (press any key)")
                stdscr.getch()
        p.wait()
        returncode = p.returncode
        if returncode != 0:
            safe_addstr(stdscr,"\n❌ Command failed with code {}\n".format(returncode))
        return returncode
    else:
        p = subprocess.Popen(cmd)
        p.wait()
        return p.returncode

def header(stdscr, title):
    if stdscr: stdscr.clear(); safe_addstr(stdscr,f"== {title} ==\n\n")

def confirm(stdscr,msg):
    if stdscr:
        safe_addstr(stdscr,f"{msg}\nType YES to continue: ")
        curses.echo()
        s = stdscr.getstr(0,30).decode()
        curses.noecho()
        return s.strip() == "YES"
    return False

def safe_write(path, content):
    if os.path.exists(path): shutil.copy2(path,path+".bak")
    with tempfile.NamedTemporaryFile("w",delete=False) as tf:
        tf.write(content)
        tmpname = tf.name
    shutil.move(tmpname,path)

def ensure_batch_config():
    if not os.path.exists(BATCH_CONFIG):
        os.makedirs(os.path.dirname(BATCH_CONFIG), exist_ok=True)
        example = {
            "actions": ["remove_lock","mirror_optimizer","update_system"],
            "frequency": "weekly"
        }
        with open(BATCH_CONFIG,"w") as f:
            json.dump(example,f,indent=4)
        print(f"Created example batch config at {BATCH_CONFIG}")

# -----------------------------
# Actions
# -----------------------------
def remove_lock(stdscr=None):
    if os.path.exists(PACMAN_LOCK): os.remove(PACMAN_LOCK); log_action("pacman lock removed")
    else: log_action("no pacman lock found")
    if stdscr: safe_addstr(stdscr,"✔ pacman lock handled\nPress any key..."); stdscr.getch()

def mirror_optimizer(stdscr=None):
    if shutil.which("reflector") is None: return
    run(["reflector","--latest","20","--protocol","https","--sort","rate","--save","/etc/pacman.d/mirrorlist"],stdscr)
    if stdscr: safe_addstr(stdscr,"✔ Mirrors optimized\nPress any key..."); stdscr.getch()

def snapshot(stdscr,label="snapshot"):
    run(["snapper","create","-d",f"auri {label}"],stdscr)
    if stdscr: safe_addstr(stdscr,"Press any key..."); stdscr.getch()

def update_system(stdscr=None):
    run(["pacman","-Syu","--noconfirm","--needed","--overwrite","*"],stdscr)
    if stdscr: safe_addstr(stdscr,"✔ Update finished\nPress any key..."); stdscr.getch()

def full_fix(stdscr=None):
    run(["pacman","-Syu","--overwrite","*","--needed","--noconfirm"],stdscr)

def reinstall_all(stdscr=None):
    if stdscr and not confirm(stdscr,"⚠️ Reinstall ALL packages?"): return
    run(["bash","-c","pacman -Qnq | pacman -S --noconfirm --needed -"],stdscr)

def remove_orphans(stdscr=None):
    run(["bash","-c","pacman -Qdtq | pacman -Rns --noconfirm -"],stdscr)

def clean_cache(stdscr=None):
    run(["pacman","-Sc","--noconfirm"],stdscr)

def sound_fix(stdscr=None):
    pkgs = ["pipewire","pipewire-alsa","pipewire-pulse","wireplumber"]
    run(["pacman","-S","--noconfirm"]+pkgs,stdscr)
    for svc in pkgs[::3]: run(["systemctl","--user","enable","--now",svc],stdscr)

def reset_snapper(stdscr=None):
    if stdscr and not confirm(stdscr,"⚠️ Reset Snapper config?"): return
    run(["snapper","-c","root","delete-config"],stdscr)
    run(["snapper","-c","root","create-config","/"],stdscr)

def wine_install(stdscr,mode):
    if mode in ("x86","both"): run(["pacman","-S","--noconfirm","lib32-wine"],stdscr)
    if mode in ("x64","both"): run(["pacman","-S","--noconfirm","wine","wine-mono","wine-gecko"],stdscr)

def kernel_manager(stdscr=None):
    curses.endwin()
    print("Launching official CachyOS kernel manager...")
    if shutil.which("cachyos-kernel-manager"): subprocess.call(["cachyos-kernel-manager"])
    elif shutil.which("cachyos-settings"): subprocess.call(["cachyos-settings"])
    else: print("❌ No official kernel manager found")
    input("Press Enter...")
    curses.initscr(); curses.curs_set(0)

def install_virtualization_stack(stdscr=None):
    user = os.getlogin(); pkgs = ["qemu","virt-manager","virt-viewer","dnsmasq","vde2","bridge-utils","openbsd-netcat","ebtables","iptables","libguestfs","fuse2","gtkmm","linux-headers","pcsclite","libcanberra"]
    run(["pacman","-S","--noconfirm"]+pkgs,stdscr)
    run(["systemctl","restart","libvirtd"],stdscr)
    run(["usermod","-aG","libvirt",user],stdscr)
    run(["systemctl","enable","--now","libvirtd"],stdscr)

# -----------------------------
# Repo & Keyring
# -----------------------------
OFFICIAL_REPOS = {"core","extra","community","multilib","cachyos"}
KNOWN_KEYRINGS = {"arch":"archlinux-keyring","cachyos":"cachyos-keyring","chaotic":"chaotic-keyring","blackarch":"blackarch-keyring","archstrike":"archstrike-keyring"}
def parse_active_repos():
    repos=[]
    with open("/etc/pacman.conf","r") as f:
        for line in f:
            line=line.strip()
            if line.startswith("[") and line.endswith("]"): repos.append(line[1:-1].lower())
    return repos

def manage_repos_and_keyrings(stdscr=None):
    active=parse_active_repos()
    tier_repos=[r for r in active if r not in OFFICIAL_REPOS]
    to_update=[]
    for r in tier_repos:
        kr=KNOWN_KEYRINGS.get(r)
        if kr:
            if stdscr: safe_addstr(stdscr,f"Repo found: {r}, keyring: {kr}\nDo you want to update? (y/n): ")
            ans="y" if stdscr is None else stdscr.getstr(0,3).decode().strip().lower()
            if ans=="y": to_update.append(kr)
    if to_update:
        run(["pacman","-Sy","--noconfirm"]+to_update,stdscr)
        run(["pacman-key","--init"],stdscr)
        for kr in to_update: run(["pacman-key","--populate",kr.split("-keyring")[0]],stdscr)
        run(["pacman-key","--refresh-keys"],stdscr)

# -----------------------------
# ACTIONS DICT
# -----------------------------
ACTIONS_DICT={
    "remove_lock":remove_lock,
    "update_system":update_system,
    "mirror_optimizer":mirror_optimizer,
    "snapshot_pre":lambda s:snapshot(s,"pre-update"),
    "snapshot_post":lambda s:snapshot(s,"post-update"),
    "full_fix":full_fix,
    "reinstall_all":reinstall_all,
    "remove_orphans":remove_orphans,
    "clean_cache":clean_cache,
    "sound_fix":sound_fix,
    "reset_snapper":reset_snapper,
    "wine_x86":lambda s:wine_install(s,"x86"),
    "wine_x64":lambda s:wine_install(s,"x64"),
    "wine_both":lambda s:wine_install(s,"both"),
    "kernel_manager":kernel_manager,
    "virtualization":install_virtualization_stack,
    "repos_keyrings":manage_repos_and_keyrings
}

# -----------------------------
# BATCH MODE
# -----------------------------
def batch_mode(stdscr=None):
    header(stdscr,"Batch Mode")
    if os.path.exists(BATCH_CONFIG):
        with open(BATCH_CONFIG) as f: cfg=json.load(f)
        for act in cfg.get("actions",[]): ACTIONS_DICT[act](stdscr)
    else:
        if stdscr: safe_addstr(stdscr,"No batch config found.\nPress any key..."); stdscr.getch()

# -----------------------------
# MAIN MENU
# -----------------------------
def menu(stdscr):
    curses.curs_set(0); stdscr.keypad(True)
    options=[("Remove pacman lock",remove_lock),
             ("Manage Repos / Keyrings",manage_repos_and_keyrings),
             ("Optimize mirrors",mirror_optimizer),
             ("Pre-update snapshot",lambda s:snapshot(s,"pre-update")),
             ("Update system",update_system),
             ("Post-update snapshot",lambda s:snapshot(s,"post-update")),
             ("Full system fix",full_fix),
             ("Reinstall ALL",reinstall_all),
             ("Remove orphan packages",remove_orphans),
             ("Clean pacman cache",clean_cache),
             ("Sound fix",sound_fix),
             ("Reset Snapper",reset_snapper),
             ("Wine x86",lambda s:wine_install(s,"x86")),
             ("Wine x64",lambda s:wine_install(s,"x64")),
             ("Wine both",lambda s:wine_install(s,"both")),
             ("Kernel manager",kernel_manager),
             ("Install Virtualization stack",install_virtualization_stack),
             ("Batch Mode / Scheduler",batch_mode),
             ("Exit",None)]
    cur=0
    while True:
        stdscr.clear(); safe_addstr(stdscr,"Auri :: Advanced System Tool\n===============================\n\n")
        for i,(label,_) in enumerate(options):
            if i==cur:
                stdscr.addstr("> "+label+"\n", curses.A_REVERSE)
            else:
                safe_addstr(stdscr,"  "+label+"\n")
        k=stdscr.getch()
        if k in (curses.KEY_UP,ord("k")) and cur>0: cur-=1
        elif k in (curses.KEY_DOWN,ord("j")) and cur<len(options)-1: cur+=1
        elif k in (10,13):
            if options[cur][1] is None: break
            options[cur][1](stdscr)

# -----------------------------
# MAIN
# -----------------------------
def main():
    if os.geteuid()!=0: print("Run as root"); sys.exit(1)
    ensure_batch_config()  # <-- auto-create batch config
    if "--batch" in sys.argv: batch_mode(None)
    else: curses.wrapper(menu)

if __name__=="__main__": main()
