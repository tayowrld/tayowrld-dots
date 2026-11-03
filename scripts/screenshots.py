#!/usr/bin/env python3
"""Compose real Alacritty/Bash windows on an isolated Sway workspace and capture it."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]

def sway(command):
    reply=json.loads(subprocess.check_output(['swaymsg','-r',command]))
    if not all(x.get('success') for x in reply): raise RuntimeError(reply)

def main():
    outputs=json.loads(subprocess.check_output(['swaymsg','-r','-t','get_outputs']))
    output=next(x for x in outputs if x.get('focused'))
    previous=output['current_workspace']; width=output['rect']['width']; height=output['rect']['height']
    tag='dots-preview-'+str(os.getpid()); processes=[]
    dest=ROOT/'screenshots'; dest.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='dots-preview-') as tmp:
        def window(name,body,x,y,w,h):
            rc=Path(tmp)/name
            rc.write_text('source "$HOME/.bashrc"\nHISTFILE=/dev/null\nset +o history\n'
                          +'cd '+shlex.quote(str(ROOT))+'\nclear\n'+body+'\n')
            app=tag+'-'+name
            proc=subprocess.Popen(['alacritty','--class',app,'--title',name,'-e','bash','--noprofile','--rcfile',str(rc),'-i'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            processes.append(proc)
            for _ in range(50):
                tree=subprocess.check_output(['swaymsg','-r','-t','get_tree']).decode()
                if app in tree: break
                time.sleep(.1)
            else: raise RuntimeError('Alacritty window did not appear')
            sway(f'[app_id="{app}"] floating enable, border normal 1')
            time.sleep(.4)
            sway(f'[app_id="{app}"] resize set width {int(w)} px height {int(h)} px')
            time.sleep(.4)
            sway(f'[app_id="{app}"] move position {int(x)} px {int(y)} px')
            time.sleep(.4)
            return app
        try:
            sway('workspace '+json.dumps(tag))
            left=window('seaside · shell',"printf '\\n  SEASIDE 2003 / tayowrld\\n\\n'\nprintf '  warm pixels, quiet desktop\\n\\n'\nls\nprintf '\\n'",width*.07,height*.14,width*.49,height*.56)
            right=window('palette · terminal',"printf '\\n  terminal palette\\n\\n'\nfor c in {0..15}; do printf '\\e[48;5;%sm    \\e[0m ' \"$c\"; (( (c+1)%4 )) || printf '\\n\\n'; done\nprintf '\\n  sway + waybar + bash\\n  gtk + kvantum + pixel icons\\n\\n'",width*.60,height*.28,width*.32,height*.43)
            time.sleep(1.2); subprocess.run(['grim','-o',output['name'],str(dest/'01-desktop.png')],check=True)
            sway(f'[app_id="{left}"] floating disable')
            sway(f'[app_id="{right}"] floating disable')
            window('config · sway',"printf '\\n  ~/.config/sway/config\\n\\n'\ncat config/sway/config\nprintf '\\n  portable profiles / aarch64 + x86_64\\n\\n'",width*.25,height*.49,width*.62,height*.38)
            time.sleep(1.2); subprocess.run(['grim','-o',output['name'],str(dest/'02-workspace.png')],check=True)
        finally:
            sway(f'[app_id="^{tag}-"] kill')
            sway('workspace '+json.dumps(previous))
            for proc in processes:
                try: proc.wait(timeout=3)
                except subprocess.TimeoutExpired: proc.terminate()
    print('Saved:',dest)

if __name__=='__main__': main()
