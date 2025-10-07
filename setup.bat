@echo off
setlocal

set VENV_DIR=venv

if exist %VENV_DIR% (
    echo 既存の仮想環境が見つかりました。
    set /p "CHOICE=再インストールしますか？ (y/N): "
    if /i not "%CHOICE%"=="y" (
        echo セットアップを中止します。
        exit /b
    )
    echo 既存の仮想環境を削除しています...
    rmdir /s /q %VENV_DIR%
)

echo 仮想環境を作成しています...
python -m venv %VENV_DIR%

echo 仮想環境を有効化しています...
call %VENV_DIR%\Scripts\activate.bat

echo 必要な依存関係をインストールしています...
pip install -r requirements.txt

echo セットアップが完了しました。
pause
endlocal
