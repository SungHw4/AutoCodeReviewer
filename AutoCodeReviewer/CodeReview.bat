@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ===============================================
echo      Fork 사용자용 C++ 코드 리뷰 도구 v1.0
echo ===============================================
echo.

echo 📁 프로젝트 경로를 입력해주세요:
echo    💡 예시: C:\worker\PristontaleS\branches\HYI
echo    💡 예시: D:\MyProject\src
echo.
set /p workPath="📂 프로젝트 경로: "

if not exist "%workPath%" (
    echo ❌ 입력하신 경로가 존재하지 않습니다: %workPath%
    echo    경로를 다시 확인해주세요.
    pause
    exit /b
)

echo.
echo ✅ 경로 확인 완료: %workPath%

echo.
echo 🎯 리뷰 방식을 선택해주세요:
echo ┌─────────────────────────────────────────┐
echo │ 1. 전체 C++ 파일 리뷰                  │
echo │ 2. 특정 파일만 리뷰                    │
echo │ 3. 최근 수정된 파일들 리뷰 (7일)       │
echo │ 4. 특정 폴더만 리뷰                    │
echo └─────────────────────────────────────────┘
echo.

set /p choice="👉 선택하세요 (1/2/3/4): "

if "%choice%"=="1" (
    echo ✅ 전체 C++ 파일 리뷰 선택
    set "reviewCmd="%~dp0FlexibleCodeReviewer.exe" --work-path="%workPath%" --mode=all-files --output=codereview"
    set "reviewType=전체 파일"
    
) else if "%choice%"=="2" (
    echo.
    echo 📝 리뷰할 파일의 상대 경로를 입력하세요:
    echo    💡 예시: src\main.cpp
    echo    💡 예시: include\header.h
    echo    💡 예시: Common\Utils.cpp
    echo.
    set /p targetFile="📄 파일 경로: "
    
    set "fullPath=%workPath%\!targetFile!"
    if exist "!fullPath!" (
        echo ✅ 파일 확인: !targetFile!
        set "reviewCmd="%~dp0FlexibleCodeReviewer.exe" --work-path="%workPath%" --mode=single-file --target-file="!targetFile!" --output=codereview"
        set "reviewType=단일 파일: !targetFile!"
    ) else (
        echo ❌ 파일을 찾을 수 없습니다: !targetFile!
        echo    전체 경로: !fullPath!
        pause
        exit /b
    )
    
) else if "%choice%"=="3" (
    echo ✅ 최근 7일 내 수정된 파일들 리뷰 선택
    set "reviewCmd="%~dp0FlexibleCodeReviewer.exe" --work-path="%workPath%" --mode=recent-files --days=7 --output=codereview"
    set "reviewType=최근 수정 파일들"
    
) else if "%choice%"=="4" (
    echo.
    echo 📁 리뷰할 폴더명을 입력하세요:
    echo    💡 예시: src
    echo    💡 예시: include
    echo    💡 예시: Common
    echo.
    set /p targetFolder="📂 폴더명: "
    
    set "folderPath=%workPath%\!targetFolder!"
    if exist "!folderPath!" (
        echo ✅ 폴더 확인: !targetFolder!
        set "reviewCmd="%~dp0FlexibleCodeReviewer.exe" --work-path="%workPath%" --mode=all-files --target-folder="!targetFolder!" --output=codereview"
        set "reviewType=특정 폴더: !targetFolder!"
    ) else (
        echo ❌ 폴더를 찾을 수 없습니다: !targetFolder!
        echo    전체 경로: !folderPath!
        pause
        exit /b
    )
    
) else (
    echo ❌ 잘못된 선택입니다. 1, 2, 3, 4 중 하나를 선택해주세요.
    pause
    exit /b
)

echo.
echo ========================================
echo          🤖 AI 코드 리뷰 시작
echo ========================================
echo 📋 리뷰 유형: %reviewType%
echo 📂 작업 경로: %workPath%
echo 💭 AI가 코드를 분석 중입니다...
echo    잠시만 기다려주세요 (약 30초-2분 소요)
echo.

%reviewCmd%

if %errorlevel% neq 0 (
    echo.
    echo ❌ 코드 리뷰 실행 중 오류가 발생했습니다.
    echo.
    echo 🔧 가능한 원인:
    echo    • config.json의 OpenAI API 키가 잘못됨
    echo    • 인터넷 연결 문제
    echo    • OpenAI 서비스 일시 중단
    echo    • 분석할 C++ 파일이 없음
    echo.
    pause
    exit /b
)

echo.
echo ========================================
echo           ✅ 코드 리뷰 완료!
echo ========================================

set "reviewFile=%workPath%\codereview.txt"

if exist "%reviewFile%" (
    echo.
    echo 📄 리뷰 결과 파일: %reviewFile%
    echo.
    echo 📋 리뷰 결과 미리보기:
    echo ┌─────────────────────────────────────────┐
    
    REM 파일의 처음 30줄만 표시
    for /f "skip=0 tokens=* delims=" %%a in ('type "%reviewFile%"') do (
        set /a lineCount+=1
        echo %%a
        if !lineCount! geq 30 (
            echo ... (더 많은 내용은 파일을 확인하세요)
            goto :end_preview
        )
    )
    :end_preview
    
    echo └─────────────────────────────────────────┘
    echo.
    set /p openFile="📝 전체 리뷰 결과를 메모장으로 열어보시겠습니까? (y/n): "
    if /i "!openFile!"=="y" (
        start notepad "%reviewFile%"
    )
    
    echo.
    echo 🎯 리뷰 결과 활용 방법:
    echo    • Fork에서 코드 변경사항과 함께 검토
    echo    • 지적된 사항들을 개선 작업 계획에 반영
    echo    • 정기적으로 실행하여 코드 품질 향상
    
) else (
    echo ❌ 리뷰 결과 파일이 생성되지 않았습니다.
    echo    예상 위치: %reviewFile%
    echo.
    echo 🔧 확인사항:
    echo    • OpenAI API 키가 올바르게 설정되었는지 확인
    echo    • 네트워크 연결 상태 확인  
    echo    • 분석할 C++ 코드 파일이 있는지 확인
)

echo.
echo 💾 작업 완료!
echo 📁 프로젝트 경로: %workPath%
echo 📝 이 경로를 기억해두시면 다음에 빠르게 사용할 수 있습니다.
echo.

pause