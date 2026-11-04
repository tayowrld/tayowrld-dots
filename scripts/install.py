#!/usr/bin/env python3
"""Install/update Seaside dotfiles. No system configuration or driver replacement."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import tempfile
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
COMMON = 'waybar alacritty fuzzel mako swaybg grim slurp wl-clipboard jq brightnessctl playerctl upower git eza btop neovim gum xdg-user-dirs qt6ct'.split()
PACKAGES = {
    'arch': COMMON + 'alsa-lib python python-dbus python-gobject gtk3 gtk-layer-shell pkgconf gcc fontconfig libnotify libpulse kvantum breeze-icons xdg-desktop-portal-wlr xdg-desktop-portal-gtk xorg-xwayland'.split(),
    'fedora': COMMON + 'alsa-lib python3 python3-dbus python3-gobject gtk3-devel gtk-layer-shell-devel pkgconf-pkg-config gcc fontconfig libnotify pulseaudio-utils kvantum breeze-icon-theme xdg-desktop-portal-wlr xdg-desktop-portal-gtk xorg-x11-server-Xwayland'.split(),
}
DEFAULTS = {'DESKTOP':'desk', 'TEMPLATES':'templates', 'PUBLICSHARE':'public', 'DOCUMENTS':'docs',
            'DOWNLOAD':'internet', 'MUSIC':'music', 'PICTURES':'img', 'VIDEOS':'video', 'PROJECTS':'work'}
STANDARD = {'DESKTOP':'Desktop', 'TEMPLATES':'Templates', 'PUBLICSHARE':'Public', 'DOCUMENTS':'Documents',
            'DOWNLOAD':'Downloads', 'MUSIC':'Music', 'PICTURES':'Pictures', 'VIDEOS':'Videos'}

def run(args, **kw):
    print('+', shlex.join(map(str,args)), flush=True)
    return subprocess.run(list(map(str,args)), check=True, **kw)

def detect():
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64','aarch64','arm64'):
        raise RuntimeError('Supported: Linux x86_64 / aarch64 (including Asahi).')
    release = {}
    for line in Path('/etc/os-release').read_text().splitlines():
        if '=' in line:
            k,v=line.split('=',1); release[k]=v.strip('"')
    ids = (release.get('ID','')+' '+release.get('ID_LIKE','')).split()
    family = 'arch' if any(x in ids for x in ('arch','archarm')) else 'fedora' if 'fedora' in ids else None
    if not family or Path('/run/ostree-booted').exists():
        raise RuntimeError('Supported package systems: Arch/Arch ARM and non-Atomic Fedora, including Fedora Asahi Remix.')
    apple = Path('/proc/device-tree/compatible')
    asahi = apple.exists() and b'apple,' in apple.read_bytes()
    return family, asahi

class Installer:
    def __init__(self, home):
        self.home=home
        self.config=Path(os.environ.get('XDG_CONFIG_HOME',str(home/'.config')))
        self.data=Path(os.environ.get('XDG_DATA_HOME',str(home/'.local/share')))
        self.state=Path(os.environ.get('XDG_STATE_HOME',str(home/'.local/state')))/'tayowrld-dots'
        self.backup=self.state/'backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        self.records=[]
    def put(self, dst, data, mode=0o644):
        dst=Path(dst)
        if dst.is_file() and not dst.is_symlink() and dst.read_bytes()==data and dst.stat().st_mode & 0o777 == mode:
            return
        if dst.exists() or dst.is_symlink():
            if dst.is_dir(): raise RuntimeError(f'Expected file, found directory: {dst}')
            saved=self.backup/str(dst).lstrip('/')
            saved.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(dst,saved,follow_symlinks=False)
        dst.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(prefix='.dots-',dir=dst.parent)
        try:
            with os.fdopen(fd,'wb') as stream: stream.write(data)
            os.chmod(tmp,mode); os.replace(tmp,dst)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
        self.records.append(str(dst))
    def copy(self,src,dst):
        data=src.read_bytes()
        try:
            text=data.decode()
            text=text.replace('@CONFIG@',str(self.config)).replace('@HOME@',str(self.home))
            data=text.encode()
        except UnicodeDecodeError: pass
        self.put(dst,data,src.stat().st_mode & 0o777)
    def xdg(self):
        path=self.config/'user-dirs.dirs'
        old=path.read_text() if path.exists() else ''
        lines=old.splitlines(); values={}
        for line in lines:
            m=re.fullmatch(r'XDG_(\w+)_DIR="(.*)"',line)
            if m: values[m[1]]=m[2]
        for key,new in DEFAULTS.items():
            value=values.get(key)
            standard=STANDARD.get(key)
            if value is not None and (not standard or value.rstrip('/') not in ('$HOME/'+standard,str(self.home/standard))):
                continue # Preserve customized names and intentionally disabled ($HOME) dirs.
            if standard:
                source=self.home/standard; target=self.home/new
                if source.exists() or source.is_symlink():
                    if source.is_symlink() or target.exists() or target.is_symlink():
                        print(f'Preserving XDG {key}: source is a link or destination exists.')
                        continue
                    source.rename(target)
                    source.symlink_to(new, target_is_directory=True)
                    self.state.mkdir(parents=True,exist_ok=True)
                    with (self.state/'directory-moves.jsonl').open('a') as log:
                        log.write(json.dumps({'from':str(source),'to':str(target)})+'\n')
                else: target.mkdir(parents=True,exist_ok=True)
            else: (self.home/new).mkdir(parents=True,exist_ok=True)
            values[key]='$HOME/'+new
        # Keep comments and unknown XDG entries, replace known definitions only.
        out=[]; seen=set()
        for line in lines:
            m=re.match(r'XDG_(\w+)_DIR=',line)
            if m and m[1] in values:
                key=m[1]; out.append(f'XDG_{key}_DIR="{values[key]}"'); seen.add(key)
            else: out.append(line)
        for key,value in values.items():
            if key not in seen: out.append(f'XDG_{key}_DIR="{value}"')
        self.put(path, ('\n'.join(out)+'\n').encode())
    def deploy(self,asahi,corners):
        for base,dest in ((ROOT/'config',self.config),(ROOT/'share',self.data),(ROOT/'bin',self.home/'.tayowrld-bin')):
            for src in sorted(base.rglob('*')):
                if base==ROOT/'config' and src.relative_to(base).parts[0]=='REAPER': continue
                if src.is_file() and '__pycache__' not in src.parts and src.suffix != '.pyc':
                    self.copy(src,dest/src.relative_to(base))
        for src in (ROOT/'shell').iterdir(): self.copy(src,self.home/src.name)
        local=self.config/'sway/local.conf'
        if not local.exists():
            text='# Preserved during updates. Put local output/input/effect settings here.\n'
            if asahi:
                text+='output eDP-1 scale 1.5\nexec_always '+str(self.config)+'/sway/utils/lid.sh watch\n'
                if corners: text+='exec '+str(self.config)+'/sway/utils/bottom-corners\n'
            self.put(local,text.encode())
        self.reaper()
        self.xdg()
        self.state.mkdir(parents=True,exist_ok=True)
        manifest={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                  [self.config/'sway/config',self.home/'.bashrc']}
        self.put(self.state/'installed.json',(json.dumps(manifest,indent=2)+'\n').encode())
        print(f'Updated {len(self.records)} files. Backups (if needed): {self.backup}')

    def reaper(self):
        """Install theme only; merge the chosen theme into existing preferences."""
        for src in sorted((ROOT/'config/REAPER').rglob('*')):
            if src.is_file(): self.copy(src,self.config/'REAPER'/src.relative_to(ROOT/'config/REAPER'))
        ini=self.config/'REAPER/reaper.ini'
        text=ini.read_text() if ini.exists() else ''
        lines=text.splitlines(keepends=True)
        setting='lastthemefn5='+str(self.config/'REAPER/ColorThemes/OPENWRLD_Seaside_2003.ReaperThemeZip')+'\n'
        section=None; found=False; out=[]; has_section=False
        for line in lines:
            if line.strip().startswith('['):
                if section=='reaper' and not found: out.append(setting); found=True
                section=line.strip()[1:-1].lower()
                if section=='reaper': has_section=True
            if section=='reaper' and line.startswith('lastthemefn5='):
                out.append(setting); found=True
            else: out.append(line)
        if section=='reaper' and not found:
            if out and not out[-1].endswith('\n'): out[-1]+='\n'
            out.append(setting)
        elif not has_section:
            if out and not out[-1].endswith('\n'): out[-1]+='\n'
            out.extend(['\n[reaper]\n',setting])
        self.put(ini,''.join(out).encode())
        # Same desktop ID as the upstream launcher, with our original pixel icon.
        executable=shutil.which('reaper') or str(self.home/'.local/opt/REAPER/reaper')
        desktop='[Desktop Entry]\nType=Application\nName=REAPER\nComment=OPENWRLD · Seaside 2003 studio\nExec="'+executable+'" %F\nIcon=reaper\nTerminal=false\nCategories=AudioVideo;Audio;Midi;Sequencer;\nStartupWMClass=REAPER\nMimeType=application/x-reaper-project;application/x-reaper-theme;\n'
        self.put(self.data/'applications/cockos-reaper.desktop',desktop.encode())
        icon=ROOT/'share/icons/Seaside-Pixel/scalable/apps/reaper.svg'
        self.copy(icon,self.data/'icons/hicolor/scalable/apps/reaper.svg')


def reaper_running(config):
    # Ignore isolated -cfgfile preview instances in other resource directories.
    for path in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            if path.stat().st_uid!=os.getuid(): continue
            args=path.read_bytes().decode(errors='replace').strip('\0').split('\0')
            if not args or Path(args[0]).name!='reaper': continue
            if '-cfgfile' in args:
                index=args.index('-cfgfile')+1
                if index<len(args) and Path(args[index]).resolve().parent!=(config/'REAPER').resolve(): continue
            return True
        except (OSError,ValueError): continue
    return False


def install_reaper(inst):
    """Keep existing REAPER. Otherwise install official native Linux build in HOME."""
    target=inst.home/'.local/opt/REAPER/reaper'
    if shutil.which('reaper') or target.is_file():
        print('REAPER already installed; keeping existing version.')
        return
    arch={'x86_64':'x86_64','aarch64':'aarch64','arm64':'aarch64'}[platform.machine()]
    # Official stable release verified 2026-11-04. Updating is an explicit source change.
    filename=f'reaper784_linux_{arch}.tar.xz'
    url='https://www.reaper.fm/files/7.x/'+filename
    with tempfile.TemporaryDirectory(prefix='dots-reaper-') as tmp:
        archive=Path(tmp)/filename
        print('Downloading official REAPER 7.84:',url,flush=True)
        with urllib.request.urlopen(url,timeout=120) as response, archive.open('wb') as stream:
            shutil.copyfileobj(response,stream)
        hashes={'x86_64':'d87b39862bec6a82bbb530731ae1fa36bba4bc9954ff72518a187420eed9ec7d',
                'aarch64':'3ade78689bec29315c1914e3a354b450f31b7fa46ef01cb438df6d3171a7a923'}
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=hashes[arch]:
            raise RuntimeError('REAPER archive checksum mismatch')
        with tarfile.open(archive) as bundle: bundle.extractall(tmp,filter='data')
        source=Path(tmp)/f'reaper_linux_{arch}'
        run(['sh',source/'install-reaper.sh','--install',inst.home/'.local/opt','--quiet'])
    inst.put(inst.home/'.tayowrld-bin/reaper',('#!/bin/sh\nexec "'+str(target)+'" "$@"\n').encode(),0o755)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='compatibility and dependency plan, no changes')
    parser.add_argument('--no-packages',action='store_true',help='skip package installation')
    parser.add_argument('--tools',action='store_true',help='compile bundled here and tado with Cargo')
    parser.add_argument('--corners',action='store_true',help='compile MacBook corner overlay')
    parser.add_argument('--reaper-only',action='store_true',help='install REAPER and studio theme only; preserve desktop config')
    parser.add_argument('--xdg-only',action='store_true',help='normalize only standard XDG directories')
    args=parser.parse_args()
    family,asahi=detect()
    if os.geteuid()==0: raise RuntimeError('Run as the desktop user, not root; sudo is used only for packages.')
    home=Path.home()
    for value in (str(home),os.environ.get('XDG_CONFIG_HOME',''),os.environ.get('XDG_DATA_HOME','')):
        if value and (not value.startswith('/') or re.search(r'[\s\"\'`$;\\]',value)):
            raise RuntimeError('Sway templates require absolute home/XDG paths without whitespace or shell metacharacters.')
    packages=PACKAGES[family].copy()
    if not shutil.which('sway'): packages.append('sway') # Do not replace an existing SwayFX installation.
    if args.tools: packages += ['cargo','rust'] if family=='arch' else ['cargo','rust']
    print(f'Platform: {family}, {platform.machine()}, Asahi={asahi}')
    if args.check:
        print('Packages:', ' '.join(packages))
        print('REAPER: keep existing version or install official 7.84 native build in ~/.local/opt; OPENWRLD theme enabled.')
        print('Profile: portable Sway; native display modes; optional local.conf overrides.')
        return
    if not args.xdg_only and reaper_running(Path(os.environ.get('XDG_CONFIG_HOME',str(home/'.config')))):
        raise RuntimeError('Close REAPER before installing so it cannot overwrite the selected theme.')
    inst=Installer(home)
    if args.xdg_only: inst.xdg(); print('XDG directories updated; backups:',inst.backup); return
    if args.reaper_only:
        if not args.no_packages: install_reaper(inst)
        elif not (shutil.which('reaper') or (inst.home/'.local/opt/REAPER/reaper').is_file()):
            raise RuntimeError('REAPER missing: rerun without --no-packages to install it.')
        inst.reaper()
        print('REAPER theme installed. Backups:',inst.backup)
        return
    if not args.no_packages:
        manager='pacman' if family=='arch' else 'dnf'
        if not shutil.which(manager): raise RuntimeError(f'Missing {manager}')
        run(['sudo',manager]+(['-S','--needed'] if family=='arch' else ['install'])+packages)
    if not args.no_packages: install_reaper(inst)
    elif not (shutil.which('reaper') or (inst.home/'.local/opt/REAPER/reaper').is_file()):
        raise RuntimeError('REAPER missing: rerun without --no-packages to install it.')
    needed=['sway','waybar','alacritty','fuzzel','mako','swaybg','grim','slurp','wl-copy','jq','eza','gum','xdg-user-dir']
    missing=[name for name in needed if not shutil.which(name)]
    if missing: raise RuntimeError('Missing required commands: '+', '.join(missing))
    built=[]
    if args.tools:
        for name in ('here','tado'):
            target=ROOT/'.build'/name
            run(['cargo','build','--locked','--release','--manifest-path',ROOT/'tools'/name/'Cargo.toml','--target-dir',target])
            built.append((target/'release'/name,inst.home/'.tayowrld-bin'/name))
    if args.corners:
        target=ROOT/'.build/bottom-corners'; target.parent.mkdir(parents=True,exist_ok=True)
        flags=subprocess.check_output(['pkg-config','--cflags','--libs','gtk+-3.0','gtk-layer-shell-0'],text=True)
        run(['cc',ROOT/'config/sway/utils/bottom-corners.c','-o',target]+shlex.split(flags)+['-lm'])
        built.append((target,inst.config/'sway/utils/bottom-corners'))
    inst.deploy(asahi,args.corners)
    for src,dst in built: inst.copy(src,dst)
    if shutil.which('fc-cache'): run(['fc-cache', '-f', inst.data/'fonts'])
    print('Done. Log out and select Sway to activate. Repeat install.sh to update from this checkout.')

if __name__=='__main__':
    try: main()
    except (RuntimeError,OSError,subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc))
