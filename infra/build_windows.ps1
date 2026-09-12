$ErrorActionPreference = 'Stop'
python -m pip install --upgrade pip
python -m pip install -e '.[local,dev]'
python -m PyInstaller --noconfirm --clean --name FinduptoAI --windowed run.py
Write-Host 'Build complete: dist/FinduptoAI/'
Write-Host 'Place your GGUF model under the packaged models directory or set FINDUPTO_MODEL_PATH.'
