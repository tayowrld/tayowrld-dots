#!/usr/bin/env python3
"""Build original OPENWRLD pixel assets (Pillow needed only to rebuild)."""
from pathlib import Path
import io
import struct
import zipfile
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
NAME='OPENWRLD_Seaside_2003'
P={'ink':'#554c5d','muted':'#8c7e8d','paper':'#fff6ef','lilac':'#dad5e7','rose':'#eed2d0','line':'#957c9c','yellow':'#eee2b4','sea':'#b9d7d0','red':'#a95464'}
assets={}
def save(name,im):
 b=io.BytesIO(); im.save(b,format='PNG'); assets[name+'.png']=b.getvalue()
def panel(name,w,h,c,accent=False):
 im=Image.new('RGBA',(w+2,h+2)); d=ImageDraw.Draw(im)
 d.rectangle((1,1,w,h),fill=c,outline=P['line'])
 d.line((2,2,w-1,2),fill=P['paper'])
 if accent: d.rectangle((2,3,4,h-1),fill=P['rose'])
 # Nine-slice markers keep pixel bevels intact.
 d.line((0,0,6,0),fill='#ff00ff'); d.line((0,0,0,6),fill='#ff00ff')
 d.line((w-5,h+1,w+1,h+1),fill='#ff00ff'); d.line((w+1,h-5,w+1,h+1),fill='#ff00ff')
 save(name,im)
font=ImageFont.load_default(size=10)
def button(name,glyph,on=False,w=24,h=22):
 im=Image.new('RGBA',(w*3,h)); d=ImageDraw.Draw(im)
 for s in range(3):
  x=w*s; bg=P['rose'] if on else [P['paper'],P['yellow'],P['lilac']][s]
  d.rectangle((x,0,x+w-1,h-1),fill=bg,outline=P['line'])
  d.line((x+1,1,x+w-2,1),fill='white')
  cx=x+w//2; cy=h//2; col=P['red'] if on else P['ink']
  if glyph=='play': d.polygon([(cx-3,cy-5),(cx-3,cy+5),(cx+5,cy)],fill=col)
  elif glyph=='stop': d.rectangle((cx-4,cy-4,cx+4,cy+4),fill=col)
  elif glyph=='rec': d.ellipse((cx-4,cy-4,cx+4,cy+4),fill=col)
  elif glyph=='pause':
   for dx in (-4,2): d.rectangle((cx+dx,cy-5,cx+dx+2,cy+5),fill=col)
  elif glyph=='heart':
   for yy,row in enumerate(['0110110','1111111','1111111','0111110','0011100','0001000']):
    for xx,v in enumerate(row):
     if v=='1': d.rectangle((cx-7+xx*2,cy-6+yy*2,cx-6+xx*2,cy-5+yy*2),fill=col)
  else:
   box=d.textbbox((0,0),glyph,font=font); d.text((cx-(box[2]-box[0])//2,cy-7),glyph,font=font,fill=col)
 save(name,im)
for name in ('tcp_bg','tcp_mainbg','envcp_bg','mcp_bg','mcp_mainbg'):
 panel(name,100,100,P['paper'],True); panel(name+'sel',100,100,P['lilac'],True)
for name in ('tcp_namebg','mcp_namebg','tcp_main_namebg','mcp_main_namebg','transport_edit_bg','transport_bpm','transport_status_bg','mcp_fxlist_bg','mcp_sendlist_bg'):
 panel(name,80,24,P['paper'])
for name in ('transport_bg','toolbar_blank','gen_volbg','gen_panbg','tcp_volbg','tcp_panbg','mcp_panbg'):
 panel(name,80,24,P['lilac'])
for prefix in ('track','tcp','mcp'):
 for stem,glyph in [('mute','M'),('solo','S'),('recarm','rec'),('recmon','>'),('fx','FX'),('env','~'),('io','IO'),('phase','O')]:
  for state in ('off','on'):
   button(prefix+'_'+stem+'_'+state,glyph,state=='on')
 for stem,glyph in [('io','IO'),('fx','FX'),('env','~'),('folder','+'),('folder_end','-'),('recmode','IN'),('recinput','IN')]: button(prefix+'_'+stem,glyph)
for stem,glyph in [('play','play'),('stop','stop'),('pause','pause'),('record','rec'),('repeat','heart'),('rew','<<'),('fwd','>>')]:
 for suffix,on in [('',False),('_on',True),('_off',False)]: button('transport_'+stem+suffix,glyph,on,w=30,h=28)
for stem,glyph in [('new','+'),('open','OP'),('save','SV'),('undo','<<'),('redo','>>'),('grid_on','#'),('grid_off','#'),('snap_on','S'),('snap_off','S'),('metronome_on','!'),('metronome_off','!'),('autoxfade_on','X'),('autoxfade_off','X'),('group_on','G'),('group_off','G'),('ripple_off','R'),('ripple_one','R'),('ripple_all','R'),('env','~'),('routing','IO'),('lock_off','L'),('lock_on','L')]: button('toolbar_'+stem,glyph,stem.endswith('_on'))
for name in ('tcp_volthumb','tcp_panthumb','mcp_panthumb','gen_volthumb','gen_panthumb'): panel(name,12,18,P['rose'])
panel('mcp_volthumb',28,12,P['rose']); panel('mcp_volbg',28,140,P['lilac'])
# Original hand-pixelled cassette / sakura / headphones track icons.
patterns={
 'sakura':['00010001000','00111011100','00111111100','00011111000','11111111111','01111111110','00111111100','01110101110','00100000100','00000100000','00000100000'],
 'cassette':['11111111111','10000000001','10111011101','10101010101','10111011101','10000000001','10011111001','10100000101','11111111111'],
 'headphones':['00011111000','00110001100','01100000110','01000000010','11000000011','11100000111','11100000111','11100000111','01100000110'],
 'keys':['11111111111','10101010101','10101010101','10101010101','10000000001','10101010101','10101010101','11111111111']}
for name,pat in patterns.items():
 im=Image.new('RGBA',(48,48)); d=ImageDraw.Draw(im)
 for y,row in enumerate(pat):
  for x,v in enumerate(row):
   if v=='1': d.rectangle((7+x*3,7+y*3,9+x*3,9+y*3),fill=P['line'] if name!='sakura' else P['red'])
 target=ROOT/'config/REAPER/Data/track_icons/OPENWRLD'; target.mkdir(parents=True,exist_ok=True); im.save(target/(name+'.png'))
for name,glyph in [('transport_home','<<'),('transport_end','>>'),('transport_previous','<<'),('transport_next','>>'),('toolbar_load','OP'),('toolbar_projprop','PR'),('toolbar_revert','SV'),('toolbar_metro_on','!'),('toolbar_metro_off','!'),('toolbar_xfade_on','X'),('toolbar_xfade_off','X'),('toolbar_envitem_on','~'),('toolbar_envitem_off','~')]:
 button(name,glyph,name.endswith('_on'),w=30 if name.startswith('transport') else 24,h=28 if name.startswith('transport') else 22)
# Additional native button names used by REAPER's TCP/MCP engine.
for name in ('track_fx_norm','track_fx_empty','track_fx_in_norm','track_fx_in_empty','track_fxon_h','track_fxon_v','track_fxempty_h','track_fxempty_v','mcp_fx_norm','mcp_fx_empty','mcp_fx_in_norm','mcp_fx_in_empty'):
 button(name,'FX')
for name in ('track_fx_dis','track_fxoff_h','track_fxoff_v','mcp_fx_dis'): button(name,'FX',True)
for state in ('off','on','auto'): button('track_monitor_'+state,'>',state=='on')
for name in ('tcp_recinput','mcp_recinput'):
 panel(name,80,22,P['paper'])
# Fader thumbs do not use background nine-slice metadata.
for name,w,h in [('tcp_volthumb',12,18),('tcp_panthumb',12,18),('mcp_panthumb',12,18),('gen_volthumb',12,18),('gen_panthumb',12,18),('mcp_volthumb',28,12)]:
 im=Image.new('RGBA',(w,h),P['rose']); d=ImageDraw.Draw(im)
 d.rectangle((0,0,w-1,h-1),outline=P['line']); d.line((1,1,w-2,1),fill=P['paper']); save(name,im)
# Segmented pastel LED meters, including dim and lit stereo/RMS states.
for name,slices in [('mcp_vu',4),('mcp_master_vu',8)]:
 im=Image.new('RGBA',(12*slices,192)); d=ImageDraw.Draw(im)
 for part in range(slices):
  lit=part>=slices//2
  for y in range(192):
   col=P['rose'] if y<32 else P['yellow'] if y<75 else P['sea']
   if not lit: col=P['lilac']
   d.line((part*12,y,part*12+11,y),fill=P['paper'] if y%5==0 else col)
 save(name,im)
im=Image.new('RGBA',(160,48)); d=ImageDraw.Draw(im)
for part in range(8):
 for x in range(160):
  col=P['lilac'] if part%4<2 else P['sea'] if x<100 else P['yellow'] if x<128 else P['rose']
  d.line((x,part*6,x,part*6+5),fill=P['paper'] if x%5==0 else col)
save('tcp_vu',im)
# An original tiny anime producer portrait: lavender hair, headphones, sailor collar.
face=['000000111111000000','000011111111110000','000111111111111000','001111111111111100','011111111111111110','011122222222111110','331122222222211133','331222422422221133','331222422422221133','331222222222221133','033122225522211330','000112222222110000','000001266210000000','000033366333000000','000333366333300000','000333333333300000']
cs={'1':P['line'],'2':P['paper'],'3':P['lilac'],'4':P['ink'],'5':P['rose'],'6':P['sea']}
im=Image.new('RGBA',(48,48)); d=ImageDraw.Draw(im)
for y,row in enumerate(face):
 for x,v in enumerate(row):
  if v!='0': d.rectangle((6+x*2,6+y*2,7+x*2,7+y*2),fill=cs[v])
im.save(ROOT/'config/REAPER/Data/track_icons/OPENWRLD/anime-producer.png')
# Fully original color definitions; COLORREF byte order is BBGGRR.
colors={}
def put(keys,color):
 r,g,b=bytes.fromhex(P.get(color,color).lstrip('#')); value=r+(g<<8)+(b<<16)
 for key in keys.split(): colors[key]=value
put('col_main_bg col_main_bg2 col_mixerbg col_tracklistbg col_arrangebg col_trans_bg col_tl_bg region_lane_bg marker_lane_bg ts_lane_bg docker_bg windowtab_bg','paper')
put('col_main_text col_main_text2 col_tcp_text col_tcp_textsel col_tl_fg col_tl_fg2 col_mi_label col_mi_label_sel col_trans_fg col_toolbar_text col_toolbar_text_on docker_text docker_text_sel region_lane_text marker_lane_text ts_lane_text','ink')
put('col_tr1_bg','paper'); put('col_tr2_bg','#f4eee9')
put('selcol_tr1_bg selcol_tr2_bg col_seltrack col_seltrack2 docker_selface col_tl_bgsel col_tl_bgsel2','lilac')
put('col_main_3dhl col_main_editbk col_transport_editbk genlist_bg midieditorlist_bg midi_pkey1','paper')
put('col_main_3dsh col_main_resize col_main_resize2 col_toolbar_frame col_tr1_divline col_tr2_divline','line')
put('col_tr1_itembg col_tr2_itembg col_mi_bg col_mi_bg2','sea')
put('col_tr1_itembgsel col_tr2_itembgsel','rose')
put('col_tr1_peaks col_tr2_peaks col_tr1_ps2 col_tr2_ps2 col_peaksedge col_peaksedge2 col_peaksedgesel col_peaksedgesel2','ink')
put('col_cursor col_cursor2 playcursor_color midi_editcurs marker col_vuclip','red')
put('col_gridlines col_gridlines2 col_gridlines3 midi_grid1 midi_grid2 midi_grid3 midi_gridh midi_gridhc','lilac')
put('midi_trackbg1 midi_inline_trackbg1 midi_rulerbg midi_leftbg midi_trackbg_outer1 midi_trackbg_outer2','paper')
put('midi_trackbg2 midi_inline_trackbg2 midi_pkey3 midi_selbg','lilac')
put('midi_pkey2 midi_rulerfg midi_notefg midi_notebg genlist_fg midieditorlist_fg midifont_col_dark midifont_col_dark_unsel','ink')
put('midi_ofsn midi_ofsnsel region col_vubot','sea'); put('col_vumid','yellow'); put('col_vutop','rose')
put('col_vudoint col_vuintcol','lilac')
put('genlist_selbg midieditorlist_selbg','lilac'); put('genlist_selfg midieditorlist_selfg mcp_fx_normal mcp_sends_normal mcp_sends_levels mcp_fxparm_normal','ink')
put('mcp_fx_bypassed mcp_fx_offlined mcp_sends_muted','muted')
for i,col in enumerate(['rose','lilac','sea','yellow','line','red']):
 put('col_env'+str(i+1),col)
for i in range(64): put('group_'+str(i),['rose','lilac','sea','yellow','line','red'][i%6])
colors.update(col_gridlines1dm=196608,col_gridlines2dm=163840,col_gridlines3dm=131072,itembg_drawmode=196608,timesel_drawmode=135424,col_nodarkmodemiscwnd=1)
def logfont(size=13):
 data=struct.pack('<5i8B32s',-size,0,0,0,400,0,0,0,0,3,2,1,49,b'3270 Nerd Font Mono'); return (data+bytes([sum(data)&255])).hex().upper()
theme='[color theme]\n'+''.join(f'{k}={v}\n' for k,v in colors.items())+'\n[REAPER]\nui_img='+NAME+'\n'
for k in ('tl_font','mi_font','lb_font','lb_font2','trans_font','user_font1','user_font2','user_font3'): theme+=k+'='+logfont(14 if k=='trans_font' else 12)+'\n'
rt='''version 6.0
use_pngs 1
tinttcp 0
peaksedges 0
tcp_showborders 0
mcp_showborders 0
transport_showborders 0
tcp_heights 4 28 76 96
mcp_min_height 280
envcp_min_height 42
tcp_folderindent 12
clear tcp.*
set tcp.size [320 96 180 28]
set tcp.label [34 5 186 22 0 0 1 0]
set tcp.label.color [85 76 93]
set tcp.label.margin [6 0 3 0]
set tcp.recarm [6 5 24 22]
set tcp.mute [228 5 24 22 1 0 1 0]
set tcp.solo [256 5 24 22 1 0 1 0]
set tcp.meter [288 5 24 84 1 0 1 1]
set tcp.volume h<52 [0] [8 36 154 18 0 0 1 0]
set tcp.volume.fadermode [-1]
set tcp.volume.label h<52 [0] [166 34 54 22 1 0 1 0]
set tcp.volume.label.color [85 76 93]
set tcp.pan h<52 [0] [228 34 52 18 1 0 1 0]
set tcp.pan.fadermode [-1]
set tcp.fx h<76 [0] [8 64 32 22]
set tcp.io h<76 [0] [44 64 32 22]
set tcp.env h<76 [0] [80 64 28 22]
set tcp.recmon h<76 [0] [112 64 24 22]
set tcp.recinput h<76 [0] [142 64 138 22 0 0 1 0]
set tcp.recinput.color [85 76 93]
set tcp.trackidx [0]
clear mcp.*
set mcp.size [100 400 100 280]
set mcp.label [6 373 88 22 0 1 0 1]
set mcp.label.color [85 76 93]
set mcp.label.margin [4 0 4 0 0.5]
set mcp.recarm [6 6 24 22]
set mcp.fx [34 6 28 22]
set mcp.io [66 6 28 22]
set mcp.extmixer.mode [1]
set mcp.extmixer.position h<360 [0] [6 36 88 76 0 0 0 1]
set compactvolh - h 160
set mcp.pan h<360 [10 34 80 18] [10 122 80 18 0 1 0 1]
set mcp.pan.fadermode [-1]
set mcp.volume h<360 [12 64 28 compactvolh] [12 152 28 156 0 1 0 1]
set mcp.volume.fadermode [-1]
set mcp.meter h<360 [52 64 36 compactvolh] [52 152 36 156 0 1 0 1]
set mcp.volume.label [6 312 88 18 0 1 0 1]
set mcp.volume.label.color [85 76 93]
set mcp.mute [8 340 36 22 0 1 0 1]
set mcp.solo [54 340 36 22 0 1 0 1]
clear master.mcp.*
set master.mcp.size [112 400 112 280]
set master.mcp.label [6 373 100 22 0 1 0 1]
set master.mcp.label.color [85 76 93]
set master.mcp.fx [8 6 40 22]
set master.mcp.io [58 6 44 22]
set master.mcp.volume h<360 [12 64 28 compactvolh] [12 152 28 156 0 1 0 1]
set master.mcp.volume.fadermode [-1]
set master.mcp.meter h<360 [52 64 48 compactvolh] [52 152 48 156 0 1 0 1]
set master.mcp.volume.label [6 312 100 18 0 1 0 1]
set master.mcp.volume.label.color [85 76 93]
set master.mcp.mute [8 340 40 22 0 1 0 1]
set master.mcp.solo [58 340 44 22 0 1 0 1]
clear envcp.*
set envcp.size [320 48 180 42]
set envcp.label [8 3 180 20 0 0 1 0]
set envcp.label.color [85 76 93]
set envcp.fader [8 27 160 16 0 0 1 0]
set envcp.fader.fadermode [-1]
set envcp.arm [228 8 24 22 1 0 1 0]
set envcp.bypass [256 8 24 22 1 0 1 0]
clear trans.*
set trans.size [1000 52]
set trans.size.dockedheight [52]
set trans.rew [8 12 30 28]
set trans.stop [42 12 30 28]
set trans.play [76 12 30 28]
set trans.pause [110 12 30 28]
set trans.rec [144 12 30 28]
set trans.repeat [180 12 30 28]
set trans.fwd [214 12 30 28]
set trans.status [260 8 280 36]
set trans.status.color [85 76 93]
set trans.bpm.edit w<740 [0] [564 14 64 24]
set trans.bpm.edit.color [85 76 93]
set trans.curtimesig w<740 [0] [640 14 48 24]
set trans.curtimesig.color [85 76 93]
set trans.rate w<880 [0] [708 14 76 24]
set trans.rate.color [85 76 93]
'''
rt+='\ncustom trans.custom.brand "OPENWRLD / 2003"\nset trans.custom.brand w<1100 [0] [824 14 166 24]\nset trans.custom.brand.color [149 124 156]\n'
rt+='\nclear master.tcp.*\nset master.tcp.size [320 76 180 28]\n'
for el in ('label','label.color','label.margin','mute','solo','meter','volume','volume.fadermode','volume.label','volume.label.color','pan','pan.fadermode','fx','io','env'):
 rt+=f'set master.tcp.{el} tcp.{el}\n'
for ctx in ('tcp','master.tcp','mcp','master.mcp'):
 rt+=f'\nset {ctx}.meter.readout.color [85 76 93 255 169 84 100 255]\nset {ctx}.meter.rmsreadout.color [85 76 93 255]\n'
 for state in ('lit.bottom','lit.top','unlit.bottom','unlit.top'):
  rt+=f'set {ctx}.meter.scale.color.{state} [85 76 93 255 255 246 239 0]\n'
assets['rtconfig.txt']=rt.encode()
out=ROOT/'config/REAPER/ColorThemes'/f'{NAME}.ReaperThemeZip'; out.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for name,data in sorted({NAME+'.ReaperTheme':theme.encode(),**{NAME+'/'+k:v for k,v in assets.items()}}.items()):
  info=zipfile.ZipInfo(name,(2003,7,7,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o644<<16; z.writestr(info,data)
print(out, len(assets),'original assets')
