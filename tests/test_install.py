import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('installer',Path(__file__).resolve().parents[1]/'scripts/install.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.home=Path(self.tmp.name)
        self.env=patch.dict(os.environ,{'XDG_CONFIG_HOME':str(self.home/'.config'),'XDG_DATA_HOME':str(self.home/'.local/share'),'XDG_STATE_HOME':str(self.home/'.local/state')})
        self.env.start(); self.inst=m.Installer(self.home)
    def tearDown(self): self.env.stop(); self.tmp.cleanup()
    def test_xdg_preserves_custom_and_migrates_data(self):
        self.inst.config.mkdir()
        (self.inst.config/'user-dirs.dirs').write_text('XDG_DOCUMENTS_DIR="$HOME/Documents"\nXDG_PICTURES_DIR="$HOME/img/"\nXDG_MUSIC_DIR="$HOME"\nXDG_PROJECTS_DIR="$HOME/work/"\n')
        (self.home/'Documents').mkdir(); (self.home/'Documents/note').write_text('keep')
        self.inst.xdg()
        self.assertEqual((self.home/'docs/note').read_text(),'keep')
        self.assertTrue((self.home/'Documents').is_symlink())
        data=(self.inst.config/'user-dirs.dirs').read_text()
        for expected in ('XDG_PICTURES_DIR="$HOME/img/"','XDG_MUSIC_DIR="$HOME"','XDG_DOCUMENTS_DIR="$HOME/docs"','XDG_PROJECTS_DIR="$HOME/work/"'): self.assertIn(expected,data)
        again=m.Installer(self.home); again.xdg(); self.assertEqual(again.records,[])
    def test_conflicting_directory_is_not_merged(self):
        for name in ('Documents','docs'): (self.home/name).mkdir()
        self.inst.config.mkdir(); path=self.inst.config/'user-dirs.dirs'; path.write_text('XDG_DOCUMENTS_DIR="$HOME/Documents"\n')
        self.inst.xdg(); self.assertIn('XDG_DOCUMENTS_DIR="$HOME/Documents"',path.read_text())
    def test_install_update_preserve_local_backup_edits(self):
        self.inst.deploy(False,False)
        config=self.inst.config/'sway/config'
        self.assertNotIn('@CONFIG@',config.read_text())
        self.assertNotIn('/etc/sway',config.read_text())
        local=self.inst.config/'sway/local.conf'; local.write_text('# custom machine\n')
        again=m.Installer(self.home); again.deploy(False,False); self.assertEqual(again.records,[])
        (self.home/'.bashrc').write_text('# local changes\n')
        update=m.Installer(self.home); update.deploy(False,False)
        saved=update.backup/str(self.home/'.bashrc').lstrip('/')
        self.assertEqual(saved.read_text(),'# local changes\n')
        self.assertEqual(local.read_text(),'# custom machine\n')
    def test_replacing_symlink_does_not_modify_target(self):
        target=self.home/'personal'; target.write_text('keep')
        link=self.home/'config-link'; link.symlink_to(target)
        self.inst.put(link,b'new')
        self.assertEqual(target.read_text(),'keep'); self.assertFalse(link.is_symlink())
        self.assertTrue((self.inst.backup/str(link).lstrip('/')).is_symlink())
    def test_reaper_preserves_audio_plugins_and_license(self):
        target=self.inst.config/'REAPER'; target.mkdir(parents=True)
        ini=target/'reaper.ini'
        ini.write_text('[reaper]\nlinux_audio_srate=48000\nvstpath=/custom/plugins\nlastthemefn5=old\n[Recent]\nrecent01=/music/session.RPP\n')
        license=target/'reaper-license.rk'; license.write_text('private-license')
        self.inst.reaper()
        result=ini.read_text()
        self.assertIn('linux_audio_srate=48000',result)
        self.assertIn('vstpath=/custom/plugins',result)
        self.assertIn('recent01=/music/session.RPP',result)
        self.assertEqual(result.count('lastthemefn5='),1)
        self.assertIn('OPENWRLD_Seaside_2003.ReaperThemeZip',result)
        self.assertEqual(license.read_text(),'private-license')
        self.assertEqual((self.inst.backup/str(ini).lstrip('/')).read_text().splitlines()[1],'linux_audio_srate=48000')
        again=m.Installer(self.home); again.reaper(); self.assertEqual(again.records,[])

    def test_reaper_theme_inserts_missing_section_and_key(self):
        for original in ('','[reaper]','[reaper]\nkey=keep\n[other]\nx=1\n','[other]\nx=1'):
            with self.subTest(original=original):
                target=self.inst.config/'REAPER/reaper.ini'; target.parent.mkdir(parents=True,exist_ok=True); target.write_text(original)
                self.inst.reaper()
                import configparser
                config=configparser.ConfigParser(); config.read(target)
                self.assertTrue(config['reaper']['lastthemefn5'].endswith('.ReaperThemeZip'))
                if '[other]' in original: self.assertEqual(config['other']['x'],'1')

    def test_existing_reaper_is_not_downloaded(self):
        with patch.object(m.shutil,'which',return_value='/usr/bin/reaper'), patch.object(m.urllib.request,'urlopen') as download:
            m.install_reaper(self.inst); download.assert_not_called()

    def test_platform_matrix(self):
        for distro,family in [('arch','arch'),('archarm','arch'),('fedora','fedora')]:
            for architecture in ('x86_64','aarch64'):
                with self.subTest(distro=distro,architecture=architecture), patch.object(m.platform,'system',return_value='Linux'), patch.object(m.platform,'machine',return_value=architecture), patch.object(Path,'read_text',return_value='ID='+distro), patch.object(Path,'exists',return_value=False):
                    self.assertEqual(m.detect(),(family,False))
        with patch.object(m.platform,'system',return_value='Linux'), patch.object(m.platform,'machine',return_value='riscv64'):
            with self.assertRaises(RuntimeError): m.detect()

    def test_nonstandard_absolute_xdg_path(self):
        self.inst.config.mkdir(); p=self.inst.config/'user-dirs.dirs'
        p.write_text('XDG_DOCUMENTS_DIR="/mnt/storage/documents"\n')
        self.inst.xdg(); self.assertIn('/mnt/storage/documents',p.read_text())

if __name__=='__main__': unittest.main()
