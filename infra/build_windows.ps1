$ErrorActionPreference = 'Stop'

python -m pip install --upgrade pip
python -m pip install -e '.[local,dev]'

python -m PyInstaller --noconfirm --clean --name FinduptoAI --windowed `
  --add-data 'config;config' `
  --add-data 'models;models' `
  run.py

Write-Host 'Build complete: dist/FinduptoAI/'
Write-Host 'Put a GGUF model in dist/FinduptoAI/models/ or set FINDUPTO_MODEL_PATH.'
