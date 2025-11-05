@echo off
chcp 65001 > nul
echo =========================================
echo 통합형 C++ 코드 리뷰어 빌드
echo =========================================
echo.

:: Python 찾기
set "PYTHON_PATH="

for %%P in (
    "C:\Python39"
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python39"
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python310"
) do (
    if exist %%P\python.exe (
        set "PYTHON_PATH=%%~P"
        echo Python 발견: %%~P
        goto :found
    )
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_PATH=python"
    goto :found
)

echo ERROR: Python을 찾을 수 없습니다
pause
exit /b 1

:found
echo.

:: 패키지 확인
echo 필요한 패키지 확인 중...
"%PYTHON_PATH%\python.exe" -m pip install --quiet --no-input pyinstaller openai

:: 빌드
echo.
echo 빌드 중...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

"%PYTHON_PATH%\python.exe" -m PyInstaller --onefile ^
    --name CPPCodeReviewer ^
    --clean ^
    CodeReviewer.py

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: 빌드 실패!
    pause
    exit /b 1
)

:: 복사
if exist "dist\CPPCodeReviewer.exe" (
    copy /y "dist\CPPCodeReviewer.exe" "CPPCodeReviewer.exe"
    echo.
    echo =========================================
    echo ✅ 빌드 성공!
    echo =========================================
    echo.
    echo 실행 파일: CPPCodeReviewer.exe
    echo.
    echo config.json을 같은 폴더에 준비하세요!
    echo.
) else (
    echo ERROR: exe 생성 실패
    pause
    exit /b 1
)

pause