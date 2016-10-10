# -*- mode: python -*-

block_cipher = None


a = Analysis(['Zamp.py'],
             pathex=['C:\\Users\\andyndeanna\\Documents\\Projects\\zamp\\src'],
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
          console=False , icon='..\\dist\\Win64\\ext\\Icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Zamp')
