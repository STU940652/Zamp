# -*- mode: python -*-
import sys
import subprocess
import re

block_cipher = None

# Build version string
version = '0.8'

svn_info = subprocess.check_output('svn info', shell=True).decode('utf-8')
svn_match = re.search("Last Changed Rev: *([0-9]+)", svn_info)
if svn_match:
    version += '.'+svn_match.group(1)

with open ("version.iss", "wt") as f:
    f.write('#define MyAppVersion "%s"\n' % version)
with open ("version", "wt") as f:
    f.write(version)
with open ("version.py", "wt") as f:
    f.write("VERSION=' %s'" % version)

icon = None

if sys.platform.startswith('win'):
    icon='../dist/Win64/ext/Icon.ico'
    
if sys.platform.startswith('darwin'):
    icon='../dist/Mac64/ext/Icon.icns'

a = Analysis(['Zamp.py'],
             pathex=[os.getcwd()],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='Zamp',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon=icon)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Zamp')
               
if sys.platform.startswith('darwin'):
    app = BUNDLE(coll,
                 name='Zamp.app',
                 icon=icon,
                 bundle_identifier=None)
