# 🤖 AutoCodeReviewer

AI 기반 C++ 코드 자동 리뷰 및 수정 도구

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-412991.svg)](https://openai.com/)

> OpenAI GPT 모델을 활용하여 C++ 코드를 자동으로 리뷰하고, AI가 제안한 수정사항을 선택적으로 적용할 수 있는 통합 도구입니다.

---

## 📋 목차

- [특징](#-특징)
- [지원 환경](#-지원-환경)
- [설치 방법](#-설치-방법)
- [설정](#-설정)
- [사용 방법](#-사용-방법)
  - [Windows 배치 파일](#windows-배치-파일)
  - [Python 직접 실행](#python-직접-실행)
- [동작 모드](#-동작-모드)
- [API 키 설정](#-api-키-설정)
- [고급 기능](#-고급-기능)
- [실행 파일 빌드](#-실행-파일-빌드)
- [문제 해결](#-문제-해결)
- [기여하기](#-기여하기)
- [라이선스](#-라이선스)

---

## ✨ 특징

### 🎯 핵심 기능

- **🔍 다중 버전 관리 시스템 지원**
  - Git 리포지토리 자동 감지 및 diff 분석
  - SVN 리포지토리 지원
  - 일반 폴더 (Fork 모드) 지원

- **🤖 AI 기반 코드 리뷰**
  - OpenAI GPT-4, GPT-4o, GPT-3.5 시리즈 지원
  - 한국어로 상세한 리뷰 제공
  - 버그, 성능, 코드 품질 분석

- **⚡ 자동 코드 수정 (신규!)**
  - AI가 제안한 수정사항을 구조화된 형태로 제공
  - 대화형 UI로 선택적 적용
  - 자동 브랜치 생성 및 Pull Request 생성

- **📊 Markdown 리포트**
  - 보기 쉬운 Markdown 형식 보고서
  - 심각도별 분류 (🔴 치명적, 🟡 경고, 🟢 개선)
  - 구체적인 개선 방안 제시

### 🛠️ 편의 기능

- **다중 경로 config 탐색** - 실행 폴더, 작업 디렉토리, 하위 폴더 자동 검색
- **환경 변수 지원** - `OPENAI_API_KEY` 환경 변수 사용 가능
- **재시도 로직** - API 호출 실패 시 자동 재시도 (지수 백오프)
- **다중 인코딩 지원** - UTF-8, CP949, EUC-KR 등 자동 감지
- **로깅 시스템** - 상세한 로그 파일 자동 생성

---

## 🖥️ 지원 환경

### 버전 관리 시스템
- ✅ Git
- ✅ SVN
- ✅ 없음 (일반 폴더)

### 운영 체제
- ✅ Windows 10/11
- ✅ Linux
- ✅ macOS

### Python 버전
- Python 3.9 이상

### 지원 파일 형식
- `.cpp`, `.hpp`, `.h`, `.cc`, `.cxx`, `.hxx`, `.c`

---

## 📦 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/SungHw4/AutoCodeReviewer.git
cd AutoCodeReviewer
```

### 2. Python 의존성 설치

```bash
pip install -r AutoCodeReviewer/requirements.txt
```

또는 개별 설치:

```bash
pip install openai
```

### 3. GitHub CLI 설치 (PR 자동 생성 기능 사용 시)

**Windows:**
```bash
winget install GitHub.cli
```

**macOS:**
```bash
brew install gh
```

**Linux:**
```bash
# Debian/Ubuntu
sudo apt install gh

# Fedora/CentOS
sudo dnf install gh
```

설치 후 인증:
```bash
gh auth login
```

---

## ⚙️ 설정

### config.json 파일 생성

프로젝트 내 다음 위치 중 하나에 `config.json` 파일을 생성하세요:

1. `AutoCodeReviewer/` (Python 스크립트와 같은 폴더) ⭐ 추천
2. `AutoCodeReviewer/ForkCodeReview_Tool/` (하위 폴더)
3. 작업 디렉토리 (실행하는 곳)

### config.json 템플릿

```json
{
  "openai_api_key": "sk-your-api-key-here",
  "model": "gpt-4o-mini",
  "max_tokens": 2000,
  "temperature": 0.3,
  "recent_days": 7,
  "max_code_tokens": 12000,
  "max_files": 20,
  "max_retries": 3,
  "team_name": "개발팀",
  "version": "2.0-Git-Compatible"
}
```

### 설정 항목 설명

| 항목 | 설명 | 기본값 | 추천값 |
|------|------|--------|--------|
| `openai_api_key` | OpenAI API 키 (필수) | - | `sk-...` |
| `model` | 사용할 GPT 모델 | `gpt-4o-mini` | `gpt-4o` |
| `max_tokens` | 응답 최대 토큰 수 | `2000` | `2000-4000` |
| `temperature` | 응답 창의성 (0~1) | `0.3` | `0.2-0.4` |
| `recent_days` | 최근 파일 검색 기간 (일) | `7` | `7` |
| `max_code_tokens` | 코드 최대 토큰 수 | `12000` | `12000` |
| `max_files` | 최대 리뷰 파일 수 | `20` | `20` |
| `max_retries` | API 재시도 횟수 | `3` | `3` |

### 모델 선택 가이드

| 모델 | 속도 | 품질 | 비용 | 추천 용도 |
|------|------|------|------|-----------|
| `gpt-3.5-turbo` | ⚡⚡⚡ | ⭐⭐ | 💰 | 빠른 리뷰, 테스트 |
| `gpt-4o-mini` | ⚡⚡ | ⭐⭐⭐ | 💰💰 | 일반적인 리뷰 ⭐ |
| `gpt-4o` | ⚡ | ⭐⭐⭐⭐ | 💰💰💰 | 중요한 코드 리뷰 |
| `gpt-4` | 🐌 | ⭐⭐⭐⭐⭐ | 💰💰💰💰 | 최고 품질 필요 시 |

---

## 🚀 사용 방법

### Windows 배치 파일

Windows 환경에서 가장 간편하게 사용할 수 있는 방법입니다.

#### 📁 배치 파일 위치
프로젝트 루트에 exe 파일과 배치 파일을 복사하거나, `AutoCodeReviewer/` 폴더에서 직접 실행하세요.

#### 1. **ReviewGit.bat** - Git 리뷰 (기본)
```batch
# 사용: Git 변경사항을 리뷰만 수행
# 위치: Git 리포지토리 루트에서 실행
# 출력: codereview_git_YYYYMMDD_HHMMSS.md

더블 클릭 또는:
ReviewGit.bat
```

**언제 사용?**
- Git으로 관리되는 프로젝트
- 변경된 C++ 코드만 빠르게 리뷰
- 수정은 직접 할 때

---

#### 2. **ReviewGitFix.bat** - Git 리뷰 + 자동 수정 ⭐ 추천
```batch
# 사용: Git 변경사항 리뷰 + AI 수정 제안 + 대화형 선택
# 위치: Git 리포지토리 루트에서 실행
# 출력: codereview_fix_YYYYMMDD_HHMMSS.md + 수정된 파일들

더블 클릭 또는:
ReviewGitFix.bat
```

**언제 사용?**
- AI가 제안한 수정사항을 하나씩 검토하고 싶을 때
- 선택적으로 코드를 개선하고 싶을 때
- 수동으로 commit/push 하고 싶을 때

**실행 화면:**
```
=========================================
🔴 수정 제안 1: 메모리 누수 방지
=========================================

📝 설명: new로 할당한 메모리를 delete하지 않음
💡 이유: 스마트 포인터 사용으로 자동 해제

────────────────────────────────────────
🔴 현재 코드:
────────────────────────────────────────
MyClass* ptr = new MyClass();

────────────────────────────────────────
🟢 수정 코드:
────────────────────────────────────────
std::unique_ptr<MyClass> ptr = std::make_unique<MyClass>();

이 수정을 적용하시겠습니까? ([y]es/[n]o/[q]uit/[a]ll): 
```

---

#### 3. **ReviewGitFixPR.bat** - Git 리뷰 + 수정 + PR 자동 생성
```batch
# 사용: Git 리뷰 + 수정 제안 + 선택 + PR 자동 생성
# 위치: Git 리포지토리 루트에서 실행
# 출력: codereview_fix_pr_YYYYMMDD_HHMMSS.md + PR URL

더블 클릭 또는:
ReviewGitFixPR.bat
```

**언제 사용?**
- 수정사항을 바로 PR로 올리고 싶을 때
- 팀 리뷰를 위해 PR을 생성하고 싶을 때
- 완전 자동화된 워크플로우를 원할 때

**필요 조건:**
- GitHub CLI (`gh`) 설치 및 인증 완료
- Git 리포지토리가 GitHub에 연결되어 있어야 함

---

#### 4. **ReviewSVN.bat** - SVN 리뷰
```batch
# 사용: SVN 변경사항 리뷰
# 위치: SVN 작업 사본 루트에서 실행
# 출력: codereview_YYYYMMDD_HHMMSS.md

더블 클릭 또는:
ReviewSVN.bat
```

**언제 사용?**
- SVN으로 관리되는 프로젝트
- SVN commit 전 변경사항 리뷰

---

#### 5. **ReviewRecnt.bat** - 최근 파일 리뷰
```batch
# 사용: 최근 7일 이내 수정된 파일 리뷰
# 위치: 프로젝트 루트에서 실행
# 출력: codereview_recent_YYYYMMDD.md

더블 클릭 또는:
ReviewRecnt.bat
```

**언제 사용?**
- 버전 관리를 사용하지 않는 프로젝트
- 최근 작업한 코드를 전체적으로 리뷰
- 정기적인 코드 품질 점검

---

### Python 직접 실행

더 세밀한 제어가 필요한 경우 Python으로 직접 실행할 수 있습니다.

#### 기본 문법

```bash
python AutoCodeReviewer/CodeReviewer.py --path <경로> --mode <모드> --action <액션>
```

#### 주요 옵션

| 옵션 | 설명 | 선택값 | 기본값 |
|------|------|--------|--------|
| `--path` | 리뷰 대상 경로 (필수) | 경로 | - |
| `--mode` | 리뷰 모드 | auto, git, svn, all, recent, folder, single | auto |
| `--action` | 동작 모드 | review, fix | review |
| `--config` | 설정 파일 경로 | 파일 경로 | config.json |
| `--old` | 이전 커밋/리비전 | 커밋 해시/번호 | - |
| `--new` | 새 커밋/리비전 | 커밋 해시/번호 | - |
| `--output` | 출력 파일명 | 파일명 | codereview.md |
| `--create-pr` | PR 자동 생성 | - | False |
| `--dry-run` | 미리보기만 | - | False |
| `--folder` | 특정 폴더 | 폴더 경로 | - |
| `--file` | 특정 파일 | 파일 경로 | - |

---

## 📚 동작 모드

### 1. Review 모드 (기본)

리뷰만 수행하고 Markdown 보고서를 생성합니다.

```bash
# Git 현재 변경사항 리뷰
python CodeReviewer.py --path . --mode git --action review

# SVN 현재 변경사항 리뷰
python CodeReviewer.py --path . --mode svn --action review

# 자동 감지 (Git/SVN/Fork 자동 선택)
python CodeReviewer.py --path . --mode auto
```

### 2. Fix 모드 (자동 수정)

리뷰 + 수정 제안 + 선택적 적용을 수행합니다.

```bash
# 기본: 대화형 선택
python CodeReviewer.py --path . --mode git --action fix

# PR 자동 생성 포함
python CodeReviewer.py --path . --mode git --action fix --create-pr

# 미리보기만 (파일 수정 안 함)
python CodeReviewer.py --path . --mode git --action fix --dry-run
```

### 3. 고급 옵션

```bash
# 특정 커밋 비교
python CodeReviewer.py --path . --mode git --old HEAD~3 --new HEAD

# 특정 SVN 리비전 비교
python CodeReviewer.py --path . --mode svn --old 1234 --new 1235

# 특정 폴더만 리뷰
python CodeReviewer.py --path . --mode folder --folder src/core

# 특정 파일만 리뷰
python CodeReviewer.py --path . --mode single --file main.cpp

# 최근 N일 파일 리뷰 (config.json의 recent_days 설정 사용)
python CodeReviewer.py --path . --mode recent
```

---

## 🔑 API 키 설정

OpenAI API 키를 설정하는 방법은 3가지입니다.

### 방법 1: config.json (추천)

```json
{
  "openai_api_key": "sk-proj-abc123...",
  "model": "gpt-4o-mini"
}
```

**장점:** 프로젝트별로 다른 키 사용 가능

---

### 방법 2: 환경 변수

#### Windows (PowerShell)
```powershell
$env:OPENAI_API_KEY="sk-proj-abc123..."
```

#### Windows (CMD)
```cmd
set OPENAI_API_KEY=sk-proj-abc123...
```

#### Linux/macOS
```bash
export OPENAI_API_KEY="sk-proj-abc123..."
```

영구 설정:
```bash
# Linux/macOS (~/.bashrc 또는 ~/.zshrc에 추가)
echo 'export OPENAI_API_KEY="sk-proj-abc123..."' >> ~/.bashrc
source ~/.bashrc

# Windows (시스템 환경 변수로 설정)
# 시스템 속성 > 환경 변수 > 새로 만들기
```

**장점:** 보안성 높음, 여러 프로젝트에서 공유

---

### 방법 3: 실행 시 지정

```bash
python CodeReviewer.py --path . --config /path/to/config.json
```

**장점:** 테스트용 설정 사용 시 편리

---

### API 키 발급 방법

1. [OpenAI Platform](https://platform.openai.com/) 접속
2. 로그인 후 **API keys** 메뉴 선택
3. **Create new secret key** 클릭
4. 키 이름 입력 후 생성
5. 생성된 키 복사 (한 번만 표시됨!)

⚠️ **주의사항:**
- API 키는 절대 GitHub 등에 공개하지 마세요
- `.gitignore`에 `config.json` 추가 권장
- 팀에서 사용 시 각자 개인 키 사용

---

## 🎓 고급 기능

### 1. 스마트 코드 매칭

AI가 제안한 코드가 정확히 일치하지 않아도 유사한 코드를 찾아 적용합니다.

```python
# AI 제안:
MyClass* ptr = new MyClass();

# 실제 코드 (공백, 주석 차이):
MyClass*  ptr  =  new  MyClass();  // 생성

# ✅ 자동으로 찾아서 적용!
```

### 2. 대화형 선택 UI

```bash
이 수정을 적용하시겠습니까? ([y]es/[n]o/[q]uit/[a]ll):
```

- `y` 또는 `yes` 또는 Enter: 이 수정 적용
- `n` 또는 `no`: 건너뛰기
- `a` 또는 `all`: 남은 모든 수정 적용
- `q` 또는 `quit`: 중단

### 3. 자동 PR 생성 워크플로우

```bash
python CodeReviewer.py --path . --mode git --action fix --create-pr
```

실행 흐름:
1. 🔍 Git diff 분석
2. 🤖 AI 리뷰 및 수정 제안
3. 💬 사용자가 각 제안 선택
4. 📝 파일 수정 적용
5. 🌿 새 브랜치 자동 생성 (`ai-code-review-YYYYMMDD_HHMMSS`)
6. 💾 자동 커밋
7. 📤 GitHub push
8. 🔗 PR 자동 생성

생성되는 PR 예시:
```
제목: fix: AI 코드 리뷰 기반 자동 수정 (3개 수정)

본문:
## 🤖 AI 코드 리뷰 자동 수정

### 📋 수정 내역

#### 📄 `src/main.cpp` (2개 수정)
- 🔴 **메모리 누수 방지**
  - new로 할당한 메모리를 delete하지 않음
  - 이유: 스마트 포인터 사용으로 자동 해제
  
- 🟡 **성능 개선**
  - 불필요한 복사 발생
  - 이유: const reference 사용
```

### 4. Dry-run 모드

실제 파일을 수정하지 않고 어떤 변경이 제안되는지 미리 확인합니다.

```bash
python CodeReviewer.py --path . --mode git --action fix --dry-run
```

모든 수정 제안을 출력하지만 파일은 변경하지 않습니다.

---

## 🔨 실행 파일 빌드

Python이 없는 환경에서 사용하기 위해 exe 파일을 빌드할 수 있습니다.

### Windows에서 빌드

```batch
# 빌드 스크립트 실행
cd AutoCodeReviewer
build_exe.bat
```

빌드 완료 후:
- `CPPCodeReviewer.exe` 생성
- `dist/` 폴더에도 복사본 생성
- 배치 파일과 함께 사용 가능

### 수동 빌드

```bash
pip install pyinstaller
cd AutoCodeReviewer

# 단일 파일로 빌드
pyinstaller --onefile --name CPPCodeReviewer CodeReviewer.py

# 또는 spec 파일 사용
pyinstaller ForkCodeReviewer.spec
```

### 배포 파일 구성

```
프로젝트_루트/
├── CPPCodeReviewer.exe         # 실행 파일
├── config.json                  # API 키 설정
├── ReviewGit.bat               # Git 리뷰
├── ReviewGitFix.bat            # Git 수정
├── ReviewGitFixPR.bat          # Git 수정 + PR
├── ReviewSVN.bat               # SVN 리뷰
└── ReviewRecnt.bat             # 최근 파일 리뷰
```

---

## ❓ 문제 해결

### 1. "config.json을 찾을 수 없습니다"

**원인:** config.json 파일이 올바른 위치에 없음

**해결:**
```bash
# 다음 위치 중 하나에 config.json 생성
AutoCodeReviewer/config.json              # 추천
AutoCodeReviewer/ForkCodeReview_Tool/config.json
./config.json (현재 디렉토리)

# 또는 환경 변수 사용
export OPENAI_API_KEY="sk-..."
```

### 2. "ModuleNotFoundError: No module named 'openai'"

**원인:** openai 패키지가 설치되지 않음

**해결:**
```bash
pip install openai

# 또는 requirements.txt 사용
pip install -r AutoCodeReviewer/requirements.txt
```

### 3. "API 호출 실패 (quota 초과)"

**원인:** OpenAI API 할당량 초과 또는 크레딧 부족

**해결:**
1. [OpenAI Billing](https://platform.openai.com/account/billing) 확인
2. 크레딧 추가 또는 플랜 업그레이드
3. 더 저렴한 모델 사용 (`gpt-3.5-turbo`)

### 4. "변경된 C++ 파일이 없습니다"

**원인:** Git/SVN 변경사항이 없거나, C++ 파일이 아님

**해결:**
```bash
# Git 상태 확인
git status

# SVN 상태 확인
svn status

# 대신 recent 모드 사용
python CodeReviewer.py --path . --mode recent
```

### 5. "gh: command not found" (PR 생성 시)

**원인:** GitHub CLI가 설치되지 않음

**해결:**
```bash
# Windows
winget install GitHub.cli

# macOS
brew install gh

# Linux
sudo apt install gh

# 인증
gh auth login
```

### 6. 한글 파일명/경로 인코딩 오류

**원인:** Windows에서 한글 경로 처리 문제

**해결:**
```bash
# PowerShell에서 실행 시
chcp 65001
python CodeReviewer.py --path "C:/한글경로/프로젝트"

# 또는 배치 파일에서 자동 처리됨
```

### 7. "파일을 찾을 수 없어 수정 적용 실패"

**원인:** AI가 제안한 코드와 실제 코드가 정확히 일치하지 않음

**해결:**
- 유사 코드 찾기 기능이 자동으로 시도됨
- 수동으로 수정이 필요할 수 있음
- Markdown 보고서를 참고하여 직접 수정

---

## 📖 사용 예시

### 시나리오 1: 일상적인 코드 리뷰

```bash
# 1. 코드 수정 후 Git add
git add src/

# 2. 리뷰 실행 (배치 파일)
ReviewGit.bat

# 3. 생성된 Markdown 파일 확인
# codereview_git_20240202_143022.md

# 4. 리뷰 내용 반영 후 커밋
git commit -m "fix: 리뷰 내용 반영"
```

### 시나리오 2: AI 자동 수정 활용

```bash
# 1. 코드 수정 후
git add .

# 2. AI 수정 모드 실행
ReviewGitFix.bat

# 3. 각 제안을 검토하고 y/n 선택
# 수정 제안 1: 메모리 누수 방지
# 이 수정을 적용하시겠습니까? y

# 4. 수정사항 자동 적용됨
# 5. Git에서 변경 확인
git diff

# 6. 만족하면 커밋
git commit -m "fix: AI 제안 수정 적용"
git push
```

### 시나리오 3: PR 자동 생성

```bash
# 1. AI 수정 + PR 생성
ReviewGitFixPR.bat

# 2. 각 제안 검토 및 선택
# 3. 자동으로 브랜치 생성 및 PR 생성
# 출력: https://github.com/user/repo/pull/123

# 4. GitHub에서 PR 확인 및 리뷰 요청
```

### 시나리오 4: 레거시 코드 리뷰

```bash
# 1. 최근 7일 변경 파일 리뷰
ReviewRecnt.bat

# 2. 또는 특정 폴더만
python CodeReviewer.py --path . --mode folder --folder src/legacy

# 3. 생성된 보고서 확인
# 4. 주요 문제점 파악 및 개선 계획 수립
```

### 시나리오 5: SVN 프로젝트

```bash
# 1. SVN 작업 디렉토리에서
cd C:\Work\SVN_Project

# 2. SVN 리뷰 실행
ReviewSVN.bat

# 3. 또는 특정 리비전 비교
python CodeReviewer.py --path . --mode svn --old 1234 --new 1235

# 4. 리뷰 확인 후 SVN 커밋
svn commit -m "리뷰 내용 반영"
```

---

## 🤝 기여하기

기여를 환영합니다! 다음 방법으로 참여해 주세요:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'feat: Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### 개발 환경 설정

```bash
# 저장소 클론
git clone https://github.com/SungHw4/AutoCodeReviewer.git
cd AutoCodeReviewer

# 의존성 설치
pip install -r AutoCodeReviewer/requirements.txt

# 테스트 실행
python AutoCodeReviewer/CodeReviewer.py --help
```

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

---

## 🙏 감사의 말

- OpenAI GPT 모델 제공
- Python 커뮤니티
- 모든 기여자분들

---

## 📞 연락처

프로젝트 링크: [https://github.com/SungHw4/AutoCodeReviewer](https://github.com/SungHw4/AutoCodeReviewer)

문제 보고: [Issues](https://github.com/SungHw4/AutoCodeReviewer/issues)

---

## 🔄 버전 히스토리

### v2.0.0 (2024-02-02)
- ✨ AI 자동 수정 기능 추가
- ✨ 대화형 선택 UI
- ✨ 자동 PR 생성
- ✨ Dry-run 모드
- ✨ Git 지원 추가
- 🐛 다양한 버그 수정 및 안정성 개선

### v1.0.0 (Initial Release)
- ✨ SVN diff 리뷰
- ✨ Fork 모드 (일반 폴더)
- ✨ OpenAI GPT 통합
- ✨ Markdown 보고서

---

**⭐ 이 프로젝트가 도움이 되셨다면 Star를 눌러주세요!**
