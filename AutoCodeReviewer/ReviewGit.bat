@echo off
chcp 65001 > nul
echo =========================================
echo Git 현재 변경사항 리뷰
echo =========================================
echo.

set OUTPUT=codereview_git_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.md
set OUTPUT=%OUTPUT: =0%

"CPPCodeReviewer.exe" --path "%CD%" --mode git --output "%OUTPUT%"

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
