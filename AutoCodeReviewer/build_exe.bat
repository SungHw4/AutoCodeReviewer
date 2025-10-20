@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ===============================================
echo   Fork 사용자용 C++ 코드 리뷰어 빌드 스크립트
echo ===============================================

chcp 65001 > nul

:: 정확한 Python 및 PyInstaller 경로 설정
set "PYTHON_PATH=C:\Users\Admin\AppData\Local\Programs\Python\Python39"
set "PYTHON_CMD=%PYTHON_PATH%\python.exe"
set "SCRIPTS_PATH=%PYTHON_PATH%\Scripts"
set "PYINSTALLER_CMD=%SCRIPTS_PATH%\pyinstaller.exe"
set "PIP_CMD=%SCRIPTS_PATH%\pip.exe"

echo 📋 설정된 경로:
echo    🐍 Python: %PYTHON_CMD%
echo    📦 pip: %PIP_CMD%
echo    🔨 PyInstaller: %PYINSTALLER_CMD%

:: Python 및 패키지 확인
echo.
echo 🔍 환경 확인 중...
if not exist "%PYTHON_CMD%" (
    echo ❌ Python을 찾을 수 없습니다: %PYTHON_CMD%
    pause
    exit /b
)

:: pip 확인
if not exist "%PIP_CMD%" (
    set "PIP_CMD=%PYTHON_CMD% -m pip"
)

:: PyInstaller 확인
if not exist "%PYINSTALLER_CMD%" (
    set "PYINSTALLER_CMD=%PYTHON_CMD% -m pyinstaller"
)

:: 필요한 패키지 설치
echo 📦 필요한 패키지 확인...
"%PYTHON_CMD%" -c "import openai" >nul 2>&1 || %PIP_CMD% install openai
%PYINSTALLER_CMD% --version >nul 2>&1 || %PIP_CMD% install pyinstaller

echo ✅ 환경 준비 완료!

:: CodeReviewer.py 파일 확인
if not exist "CodeReviewer.py" (
    echo ❌ CodeReviewer.py 파일이 없습니다.
    echo    위에서 제공한 코드를 CodeReviewer.py로 저장해주세요.
    pause
    exit /b
)

:: 빌드 실행
echo.
echo 🔨 exe 파일 빌드 중...
if exist "build" rmdir /s /q "build" >nul 2>&1
if exist "dist" rmdir /s /q "dist" >nul 2>&1
if exist "*.spec" del /q "*.spec" >nul 2>&1

%PYINSTALLER_CMD% --onefile --console --name="ForkCodeReviewer" --clean CodeReviewer.py

if exist "dist\ForkCodeReviewer.exe" (
    echo ✅ exe 빌드 성공!
) else (
    echo ❌ exe 빌드 실패!
    pause
    exit /b
)

:: 배포 폴더 생성
echo 📦 배포 폴더 생성 중...
if exist "ForkCodeReview_Tool" rmdir /s /q "ForkCodeReview_Tool" >nul 2>&1
mkdir "ForkCodeReview_Tool"

copy /Y "dist\ForkCodeReviewer.exe" "ForkCodeReview_Tool\" >nul
call :CREATE_CONFIG
call :CREATE_MAIN_BAT
call :CREATE_QUICK_BAT
call :CREATE_FILE_BAT
call :CREATE_README

:: 정리
if exist "build" rmdir /s /q "build" >nul 2>&1
if exist "dist" rmdir /s /q "dist" >nul 2>&1
if exist "*.spec" del /q "*.spec" >nul 2>&1

echo.
echo ========================================
echo           🎉 빌드 완료!
echo ========================================
echo 📁 배포 폴더: ForkCodeReview_Tool
echo.
echo 📋 생성된 파일들:
dir /b ForkCodeReview_Tool
echo.
echo 📝 다음 단계:
echo    1. config.json에서 API 키 설정
echo    2. ForkCodeReview_Tool 폴더를 팀에 공유
echo    3. 사용 방법을 README.txt에서 확인
echo.
pause
exit /b

:: ===== 함수 정의 =====

:CREATE_CONFIG
(
echo {
echo   "openai_api_key": "여기에-실제-API-키-입력하세요",
echo   "model": "gpt-4",
echo   "max_tokens": 2000,
echo   "temperature": 0.3,
echo   "team_name": "Fork 사용 개발팀",
echo   "version": "Fork-Compatible"
echo }
) > "ForkCodeReview_Tool\config.json"
exit /b

:CREATE_MAIN_BAT
(
echo @echo off
echo chcp 65001 ^> nul
echo setlocal enabledelayedexpansion
echo.
echo echo ===============================================
echo echo     Fork 사용자용 C++ 코드 리뷰 도구
echo echo ===============================================
echo echo.
echo echo 📁 프로젝트 경로를 입력해주세요:
echo echo    💡 예시: C:\worker\PristontaleS\branches\HYI
echo echo    💡 예시: D:\MyProject\src
echo echo.
echo set /p workPath="📂 경로 입력: "
echo.
echo if not exist "%%workPath%%" ^(
echo     echo ❌ 입력하신 경로가 존재하지 않습니다: %%workPath%%
echo     pause
echo     exit /b
echo ^)
echo.
echo cd /d "%%workPath%%"
echo echo ✅ 경로 설정: %%workPath%%
echo echo.
echo echo 🎯 리뷰 방식을 선택하세요:
echo echo ┌─────────────────────────────────────────┐
echo echo │ 1. 전체 C++ 파일 리뷰                  │
echo echo │ 2. 최근 수정된 파일들 리뷰             │
echo echo │ 3. 특정 폴더만 리뷰                    │
echo echo │ 4. 특정 파일만 리뷰                    │
echo echo └─────────────────────────────────────────┘
echo echo.
echo set /p choice="👉 선택하세요 ^(1/2/3/4^): "
echo.
echo if "%%choice%%"=="1" ^(
echo     echo ✅ 전체 C++ 파일 리뷰 선택
echo     echo 🤖 전체 파일을 분석 중입니다...
echo     "%%~dp0ForkCodeReviewer.exe" --work-path="%%workPath%%" --mode=all-files --output=full_review
echo ^) else if "%%choice%%"=="2" ^(
echo     echo ✅ 최근 수정된 파일들 리뷰 선택
echo     echo 🤖 최근 7일 내 수정된 파일들을 분석 중입니다...
echo     "%%~dp0ForkCodeReviewer.exe" --work-path="%%workPath%%" --mode=recent-files --output=recent_review
echo ^) else if "%%choice%%"=="3" ^(
echo     echo.
echo     echo 📁 리뷰할 폴더명을 입력하세요:
echo     echo    💡 예시: src, include, Common
echo     set /p targetFolder="폴더명 입력: "
echo     echo ✅ 폴더 리뷰 선택: ^!targetFolder^!
echo     echo 🤖 폴더를 분석 중입니다...
echo     "%%~dp0ForkCodeReviewer.exe" --work-path="%%workPath%%" --mode=folder --target-folder="^!targetFolder^!" --output=folder_review
echo ^) else if "%%choice%%"=="4" ^(
echo     echo.
echo     echo 📄 리뷰할 파일 경로를 입력하세요:
echo     echo    💡 예시: src\main.cpp, include\header.h
echo     set /p targetFile="파일 경로: "
echo     
echo     if exist "%%workPath%%\^!targetFile^!" ^(
echo         echo ✅ 파일 리뷰 선택: ^!targetFile^!
echo         echo 🤖 파일을 분석 중입니다...
echo         "%%~dp0ForkCodeReviewer.exe" --work-path="%%workPath%%" --mode=single-file --target-file="^!targetFile^!" --output=file_review
echo     ^) else ^(
echo         echo ❌ 파일을 찾을 수 없습니다: %%workPath%%\^!targetFile^!
echo         pause
echo         exit /b
echo     ^)
echo ^) else ^(
echo     echo ❌ 잘못된 선택입니다. 1, 2, 3, 4 중 하나를 선택해주세요.
echo     pause
echo     exit /b
echo ^)
echo.
echo if %%errorlevel%% neq 0 ^(
echo     echo ❌ 코드 리뷰 중 오류가 발생했습니다.
echo     echo    • API 키가 올바른지 config.json에서 확인
echo     echo    • 인터넷 연결 상태 확인
echo     pause
echo     exit /b
echo ^)
echo.
echo :: 결과 파일 확인
echo for %%%%f in ^("%%workPath%%\*review.txt"^^) do ^(
echo     if exist "%%%%f" ^(
echo         echo ✅ 코드 리뷰 완료!
echo         echo 📄 결과 파일: %%%%f
echo         echo.
echo         echo 📋 리뷰 결과 미리보기:
echo         echo ┌─────────────────────────────────────────┐
echo         type "%%%%f"
echo         echo └─────────────────────────────────────────┘
echo         echo.
echo         set /p openFile="📝 전체 결과를 메모장으로 보시겠습니까? ^(y/n^): "
echo         if /i "^!openFile^!"=="y" ^(
echo             start notepad "%%%%f"
echo         ^)
echo         goto :found_result
echo     ^)
echo ^)
echo.
echo ❌ 리뷰 결과 파일이 생성되지 않았습니다.
echo.
echo :found_result
echo pause
) > "ForkCodeReview_Tool\CodeReview.bat"
exit /b

:CREATE_QUICK_BAT
(
echo @echo off
echo chcp 65001 ^> nul
echo echo ===============================================
echo echo      🚀 빠른 C++ 코드 리뷰 ^(Fork용^)
echo echo ===============================================
echo echo 📂 현재 경로: %%CD%%
echo echo 🤖 현재 위치의 최근 수정 파일들을 리뷰합니다...
echo echo.
echo "%%~dp0ForkCodeReviewer.exe" --work-path="%%CD%%" --mode=recent-files --output=quick_review
echo.
echo set "reviewFile=%%CD%%\quick_review.txt"
echo if exist "%%reviewFile%%" ^(
echo     echo ✅ 빠른 리뷰 완료!
echo     echo.
echo     echo 📋 결과:
echo     echo ┌─────────────────────────────────────────┐
echo     type "%%reviewFile%%"
echo     echo └─────────────────────────────────────────┘
echo     echo.
echo     set /p openFile="메모장으로 보시겠습니까? ^(y/n^): "
echo     if /i "^!openFile^!"=="y" ^(
echo         start notepad "%%reviewFile%%"
echo     ^)
echo ^) else ^(
echo     echo ❌ 빠른 리뷰 결과가 생성되지 않았습니다.
echo ^)
echo.
echo pause
) > "ForkCodeReview_Tool\QuickReview.bat"
exit /b

:CREATE_FILE_BAT
(
echo @echo off
echo chcp 65001 ^> nul
echo echo ===============================================
echo echo      📄 파일별 C++ 코드 리뷰 ^(Fork용^)
echo echo ===============================================
echo echo.
echo set /p filePath="📁 리뷰할 C++ 파일의 전체 경로를 입력하세요: "
echo.
echo if not exist "%%filePath%%" ^(
echo     echo ❌ 파일을 찾을 수 없습니다: %%filePath%%
echo     pause
echo     exit /b
echo ^)
echo.
echo :: 파일 경로에서 디렉토리와 파일명 분리
echo for %%%%F in ^("%%filePath%%"^^) do ^(
echo     set "workDir=%%%%~dpF"
echo     set "fileName=%%%%~nxF"
echo ^)
echo.
echo echo ✅ 파일 발견: %%fileName%%
echo echo 📂 작업 디렉토리: %%workDir%%
echo echo 🤖 파일을 분석 중입니다...
echo echo.
echo.
echo "%%~dp0ForkCodeReviewer.exe" --work-path="%%workDir%%" --mode=single-file --target-file="%%fileName%%" --output=single_file_review
echo.
echo set "reviewFile=%%workDir%%single_file_review.txt"
echo if exist "%%reviewFile%%" ^(
echo     echo ✅ 파일 리뷰 완료!
echo     echo 📄 대상: %%filePath%%
echo     echo.
echo     echo 📋 리뷰 결과:
echo     echo ┌─────────────────────────────────────────┐
echo     type "%%reviewFile%%"
echo     echo └─────────────────────────────────────────┘
echo     echo.
echo     set /p openFile="전체 결과를 메모장으로 보시겠습니까? ^(y/n^): "
echo     if /i "^!openFile^!"=="y" ^(
echo         start notepad "%%reviewFile%%"
echo     ^)
echo ^) else ^(
echo     echo ❌ 리뷰 결과가 생성되지 않았습니다.
echo ^)
echo.
echo pause
) > "ForkCodeReview_Tool\FileReview.bat"
exit /b

:CREATE_README
(
echo ===============================================
echo      Fork 사용자용 C++ 코드 리뷰 도구
echo ===============================================
echo.
echo 🎯 Fork를 사용하는 개발팀을 위한 전용 도구
echo Git 명령어 없이도 C++ 코드 리뷰가 가능합니다!
echo.
echo 📋 주요 기능:
echo • OpenAI GPT-4 기반 전문 C++ 코드 분석
echo • Git 명령어 불필요 ^(Fork 사용자 최적화^)
echo • 다양한 리뷰 모드 지원
echo   - 전체 파일 리뷰
echo   - 최근 수정 파일 리뷰
echo   - 특정 폴더/파일 리뷰
echo • 메모리 관리, 성능, 모던 C++ 패턴 검토
echo.
echo 🚀 사용법:
echo.
echo 1️⃣ API 키 설정
echo    • config.json 파일을 메모장으로 열기
echo    • "여기에-실제-API-키-입력하세요" 부분을
echo      실제 OpenAI API 키로 교체
echo    • 파일 저장
echo.
echo 2️⃣ 리뷰 실행
echo    다음 중 하나의 배치 파일을 더블클릭:
echo.
echo    📁 CodeReview.bat
echo       → 상세 옵션 선택 가능한 메인 리뷰어
echo       → 프로젝트 경로 입력 후 리뷰 방식 선택
echo.
echo    🚀 QuickReview.bat  
echo       → 현재 폴더의 최근 수정 파일들 빠른 리뷰
echo       → 클릭 한 번으로 즉시 리뷰
echo.
echo    📄 FileReview.bat
echo       → 특정 파일 하나만 집중 리뷰
echo       → 파일 경로 입력하여 정밀 분석
echo.
echo 📊 리뷰 결과:
echo • 심각도별 분류 ^(🔴높음/🟡보통/🟢낮음^)
echo • 구체적인 개선 방안 제시
echo • 수정 전/후 코드 예시 제공
echo • 메모리 안전성 및 성능 최적화 제안
echo.
echo 💡 Fork 사용 팁:
echo 1. Fork에서 변경사항 확인 후
echo 2. 해당 프로젝트 폴더에서 이 도구 실행
echo 3. 리뷰 결과를 바탕으로 코드 개선
echo 4. Fork에서 커밋 전 재검토
echo.
echo 🔧 문제 해결:
echo • API 키 오류 → config.json의 API 키 확인
echo • 파일 없음 오류 → 정확한 프로젝트 경로 입력
echo • 네트워크 오류 → 인터넷 연결 및 방화벽 확인
echo • 리뷰 결과 없음 → C++ 파일이 있는 폴더인지 확인
echo.
echo ⚙️ 시스템 요구사항:
echo • Windows 7 이상
echo • 인터넷 연결
echo • OpenAI API 키
echo • C++ 소스 파일이 포함된 프로젝트
echo.
echo 📞 지원:
echo 이 도구는 Fork GUI Git 클라이언트 사용자를 위해
echo 특별히 최적화되었습니다. Git 명령줄 도구가 
echo 설치되어 있지 않아도 정상 작동합니다.
echo.
echo ===============================================
echo 버전: Fork-Compatible v1.0
echo OpenAI GPT-4 | Fork 최적화 | Git CLI 불필요
echo ===============================================
) > "ForkCodeReview_Tool\README.txt"
exit /b