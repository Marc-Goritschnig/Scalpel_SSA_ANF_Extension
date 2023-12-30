### Commands
C:\Users\MarcGoritschnig\venvs\Scalpel_Core_VENV\Scripts\activate

pyinstaller --noconfirm --onefile --console  "C:/Users/MarcGoritschnig/OneDrive-HTL/Dokumente/Uni/MasterThesis/Scalpel_SSA_ANF_Extension/src/scalpel/py_anf_transformer.py"

C:\Users\MarcGoritschnig\venvs\Scalpel_Core_test\Scripts\activate
cd /mnt/c/users/MarcGoritschnig/OneDrive-HTL/Dokumente/Uni/MasterThesis/Scalpel_SSA_ANF_Extension
. /mnt/c/users/MarcGoritschnig/venvs/Scalpel2_SSA_ANF_Extension/Scripts/activate
. /mnt/c/users/MarcGoritschnig/venvs/unix_venv_scalpel/bin/activate

pip install -r requirements.txt


### Navigate in Project:
cd C:\Users\MarcGoritschnig\OneDrive-HTL\Dokumente\Uni\MasterThesis\Scalpel_SSA_ANF_Extension

### Venv erzeugen:
python3 -m venv /mnt/c/users/MarcGoritschnig/venvs/unix_venv_scalpel2

### Activate Venv:
. /mnt/c/users/MarcGoritschnig/venvs/unix_venv_scalpel2/bin/activate

### Build:
cd /mnt/c/users/MarcGoritschnig/OneDrive-HTL/Dokumente/Uni/MasterThesis/Scalpel_SSA_ANF_Extension
. /mnt/c/users/MarcGoritschnig/venvs/unix_venv_scalpel2/bin/activate
PyInstaller --noconfirm --onefile --console  "/mnt/c/Users/MarcGoritschnig/OneDrive-HTL/Dokumente/Uni/MasterThesis/Scalpel_SSA_ANF_Extension/src/scalpel/py_anf_transformer.py"


### Mac:
pyinstaller --noconfirm --onefile --console  "/Users/proagent/IdeaProjects/Scalpel_SSA_ANF_Extension/src/scalpel/py_anf_transformer.py"
pyinstaller --noconfirm --onefile --console --target-arch x86_64 "/Users/proagent/IdeaProjects/Scalpel_SSA_ANF_Extension/src/scalpel/py_anf_transformer.py"
pyinstaller --noconfirm --onefile --console --target-arch arm64 "/Users/proagent/IdeaProjects/Scalpel_SSA_ANF_Extension/src/scalpel/py_anf_transformer.py"
pyinstaller --noconfirm --onefile --console --target-arch universal2 "/Users/proagent/IdeaProjects/Scalpel_SSA_ANF_Extension/src/scalpel/py_anf_transformer.py"




Install python with enable-shared:
https://medium.com/geekculture/how-to-install-and-manage-multiple-python-versions-in-wsl2-6d6ce1b6f55b