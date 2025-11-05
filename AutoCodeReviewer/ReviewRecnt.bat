@echo off
chcp 65001 > nul
echo =========================================
echo Fork 모드: 최근 7일 파일 리뷰
echo =========================================
echo.

set OUTPUT=codereview_recent_%date:~0,4%%date:~5,2%%date:~8,2%.md
set OUTPUT=%OUTPUT: =0%

"CPPCodeReviewer.exe" --path "%CD%" --mode recent --output "%OUTPUT%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 리뷰 완료!
    echo 결과: %OUTPUT%
    start notepad "%OUTPUT%"
) else (
    echo.
    echo ❌ 리뷰 실패
)

pause