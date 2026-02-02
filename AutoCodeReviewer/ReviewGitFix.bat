@echo off
chcp 65001 > nul
echo =========================================
echo Git 자동 수정 모드 (대화형)
echo =========================================
echo.
echo 이 모드는 AI가 제안한 수정사항을 선택적으로 적용합니다.
echo.

set OUTPUT=codereview_fix_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.md
set OUTPUT=%OUTPUT: =0%

"CPPCodeReviewer.exe" --path "%CD%" --mode git --action fix --output "%OUTPUT%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 작업 완료!
    echo 결과: %OUTPUT%
    start notepad "%OUTPUT%"
) else (
    echo.
    echo ❌ 작업 실패
)

pause
