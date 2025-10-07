@echo off

set VENV_DIR=venv
set INSTALLED_MARKER=%VENV_DIR%\installed_requirements.txt

if not exist %VENV_DIR% (
    echo 仮想環境を作成しています...
    python -m venv %VENV_DIR%
)

echo 仮想環境を有効化しています...
call %VENV_DIR%\Scripts\activate.bat

if not exist "%INSTALLED_MARKER%" (
    echo 必要な依存関係を初めてインストールしています...
    pip install -r requirements.txt
    copy /Y requirements.txt "%INSTALLED_MARKER%" > nul
) else (
    fc /b requirements.txt "%INSTALLED_MARKER%" > nul
    if errorlevel 1 (
        echo 依存関係を更新しています...
        pip install -r requirements.txt
        copy /Y requirements.txt "%INSTALLED_MARKER%" > nul
    ) else (
        echo 依存関係は最新です。
    )
)

echo セットアップが完了しました。プログラムを起動します...
python main.py

deactivate
