$ErrorActionPreference = 'Stop'

python -m pip install --upgrade pip
python -m pip install -e '.[local,dev]'
python -m PyInstaller --noconfirm --clean infra/FinduptoAI.spec

New-Item -ItemType Directory -Force -Path 'dist\FinduptoAI\models' | Out-Null
New-Item -ItemType Directory -Force -Path 'dist\FinduptoAI\data' | Out-Null

Write-Host 'Build complete: dist\FinduptoAI\FinduptoAI.exe'
Write-Host 'Put a GGUF model in dist\FinduptoAI\models\model.gguf or set FINDUPTO_MODEL_PATH.'
