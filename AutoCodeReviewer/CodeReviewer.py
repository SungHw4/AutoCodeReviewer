#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합형 C++ 코드 리뷰어 (Fork + SVN 지원)
-----------------------------------------
✅ 자동 모드 선택:
   - SVN 리포지토리 감지 시 → 변경된 코드(diff) 리뷰
   - 일반 폴더일 경우 → 전체 / 최근 / 특정 파일 리뷰

✅ 공통 기능:
   - config.json 기반 OpenAI 모델 설정
   - GPT-4, GPT-4o, GPT-3.5 시리즈 지원
   - 한국어 상세 리뷰
   - Markdown 보고서 출력
   
✅ 개선 사항:
   - PyInstaller exe 호환성 (config.json 경로 처리)
   - Windows SVN 명령어 호환성
   - 향상된 diff 파싱 (의미있는 변경만)
   - 토큰 절약 (청크 단위 처리)
   - 에러 핸들링 강화
"""

import argparse
import subprocess
import os
import sys
import json
import glob
import re
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from openai import OpenAI


# ------------------------------------------------------------
# 로깅 설정
# ------------------------------------------------------------
def setup_logging():
    """로깅 시스템 초기화"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('codereview.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()


# ------------------------------------------------------------
# 실행 파일 경로 감지 (PyInstaller 호환)
# ------------------------------------------------------------
def get_executable_dir():
    """exe 또는 스크립트 실제 위치 반환"""
    if getattr(sys, 'frozen', False):
        # PyInstaller로 빌드된 exe
        return Path(sys.executable).parent
    else:
        # Python 스크립트
        return Path(__file__).parent


# ------------------------------------------------------------
# Config 및 OpenAI 초기화
# ------------------------------------------------------------
def load_config(config_filename: str = "config.json"):
    """config.json을 여러 경로에서 순차 탐색하여 로드"""
    search_paths = [
        get_executable_dir() / config_filename,  # exe 실행 폴더
        Path.cwd() / config_filename,            # 현재 작업 디렉토리
        get_executable_dir() / "ForkCodeReview_Tool" / config_filename,  # 하위 폴더
    ]
    
    logger.info(f"Config 파일 탐색 중: {config_filename}")
    
    config_path = None
    for path in search_paths:
        if path.exists():
            config_path = path
            logger.info(f"📁 Config 발견: {config_path}")
            break
    
    if not config_path:
        error_msg = f"❌ config.json을 찾을 수 없습니다.\n탐색 경로:\n" + "\n".join(f"  - {p}" for p in search_paths)
        logger.error(error_msg)
        sys.exit(error_msg)
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        
        # API 키 처리 (환경 변수 지원)
        api_key = cfg.get("api_key") or cfg.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            sys.exit("❌ config.json에 'api_key' 또는 'openai_api_key'가 없고, 환경 변수 OPENAI_API_KEY도 설정되지 않았습니다.")
        
        cfg["api_key"] = api_key  # 통일된 키 이름
        
        # 기본값 설정
        cfg.setdefault("model", "gpt-4o-mini")
        cfg.setdefault("max_tokens", 2000)
        cfg.setdefault("temperature", 0.3)
        cfg.setdefault("recent_days", 7)
        cfg.setdefault("max_code_tokens", 12000)
        cfg.setdefault("max_files", 20)
        cfg.setdefault("max_retries", 3)
        
        logger.info(f"✅ Config 로드 성공 (model: {cfg.get('model')})")
        return cfg
        
    except FileNotFoundError:
        logger.error(f"❌ config.json을 찾을 수 없습니다: {config_path}")
        sys.exit(f"❌ config.json을 찾을 수 없습니다: {config_path}")
    except json.JSONDecodeError as e:
        logger.error(f"❌ config.json 형식 오류: {e}")
        sys.exit(f"❌ config.json 형식 오류: {e}")


def init_openai_client(api_key: str):
    """OpenAI 클라이언트 초기화"""
    try:
        client = OpenAI(api_key=api_key)
        logger.info("✅ OpenAI 클라이언트 초기화 성공")
        return client
    except Exception as e:
        logger.error(f"❌ OpenAI 초기화 실패: {e}")
        sys.exit(f"❌ OpenAI 초기화 실패: {e}")


# ------------------------------------------------------------
# 버전 관리 시스템 (VCS) 관련 함수
# ------------------------------------------------------------
def detect_vcs(path: Path) -> str:
    """버전 관리 시스템 감지 (Git, SVN, 또는 None)"""
    if (path / ".git").exists():
        logger.info("🔍 Git 리포지토리 감지")
        return "git"
    elif (path / ".svn").exists():
        logger.info("🔍 SVN 리포지토리 감지")
        return "svn"
    logger.info("📁 일반 폴더 (VCS 없음)")
    return None


# ------------------------------------------------------------
# Git 관련 함수
# ------------------------------------------------------------
def run_git_cmd(cmd, cwd):
    """Git 명령어 실행"""
    try:
        if isinstance(cmd, list):
            cmd_str = " ".join(cmd)
        else:
            cmd_str = cmd
        
        logger.debug(f"Git 명령어 실행: {cmd_str}")
        
        result = subprocess.run(
            cmd_str,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=True
        )
        
        if result.returncode != 0:
            logger.warning(f"⚠️ Git 명령 실패: {cmd_str}")
            logger.warning(f"   오류: {result.stderr}")
            return None
        
        return result.stdout
    except Exception as e:
        logger.error(f"⚠️ Git 명령 실행 오류: {e}")
        return None


def get_git_changed_files(repo_path: Path, old_commit=None, new_commit=None):
    """Git 변경 파일 목록"""
    logger.info("\n=== Git 변경 파일 스캠 ===")
    
    if old_commit and new_commit:
        logger.info(f"커밋 비교: {old_commit} → {new_commit}")
        cmd = f'git diff --name-status {old_commit} {new_commit}'
    elif old_commit:
        logger.info(f"커밋 기준 변경: {old_commit}..HEAD")
        cmd = f'git diff --name-status {old_commit}'
    else:
        logger.info("현재 작업 디렉토리 변경사항 (unstaged + staged)")
        cmd = 'git diff --name-status HEAD'

    output = run_git_cmd(cmd, cwd=repo_path)
    if not output:
        # staged 파일도 확인
        logger.info("HEAD diff 결과 없음, staged 파일 확인...")
        cmd = 'git diff --cached --name-status'
        output = run_git_cmd(cmd, cwd=repo_path)
        if not output:
            return []

    cpp_ext = (".cpp", ".hpp", ".h", ".cc", ".cxx", ".c")
    changed = []
    
    for line in output.splitlines():
        if not line.strip():
            continue
        
        parts = line.split(None, 1)
        if len(parts) < 2:
            continue
        
        status, file = parts[0], parts[1]
        
        # 탭으로 구분된 경우 (이름 변경 등)
        if '\t' in file:
            file = file.split('\t')[-1]
        
        if status in ["M", "A", "C"] and file.endswith(cpp_ext):
            changed.append(file)
            logger.info(f"  ✓ {file} ({status})")
    
    logger.info(f"총 {len(changed)}개 C/C++ 파일 변경됨")
    return changed


def get_git_diff(repo_path: Path, file_path: str, old_commit=None, new_commit=None):
    """Git diff 내용"""
    if old_commit and new_commit:
        cmd = f'git diff {old_commit} {new_commit} -- "{file_path}"'
    elif old_commit:
        cmd = f'git diff {old_commit} -- "{file_path}"'
    else:
        # 작업 디렉토리 변경사항
        cmd = f'git diff HEAD -- "{file_path}"'
        result = run_git_cmd(cmd, cwd=repo_path)
        if not result or not result.strip():
            # staged 변경사항 확인
            cmd = f'git diff --cached -- "{file_path}"'
            return run_git_cmd(cmd, cwd=repo_path)
        return result
    
    return run_git_cmd(cmd, cwd=repo_path)


# ------------------------------------------------------------
# SVN 관련 함수
# ------------------------------------------------------------
def detect_svn_repo(path: Path) -> bool:
    """더 이상 사용하지 않음 - detect_vcs()로 대체"""
    return (path / ".svn").exists()


def run_svn_cmd(cmd, cwd):
    """SVN 명령어 실행 (Windows 호환)"""
    try:
        # Windows에서는 shell=True 권장
        if isinstance(cmd, list):
            cmd = " ".join(cmd)
        
        logger.debug(f"SVN 명령어 실행: {cmd}")
        
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=True  # Windows 호환성
        )
        
        if result.returncode != 0:
            logger.warning(f"⚠️ SVN 명령 실패: {cmd}")
            logger.warning(f"   오류: {result.stderr}")
            return None
        
        return result.stdout
    except Exception as e:
        logger.error(f"⚠️ SVN 명령 실행 오류: {e}")
        return None


def get_changed_files(repo_path: Path, old_rev=None, new_rev=None):
    """SVN 변경 파일 목록"""
    logger.info("\n=== SVN 변경 파일 스캔 ===")
    
    if old_rev and new_rev:
        logger.info(f"리비전 비교: r{old_rev} → r{new_rev}")
        cmd = f'svn diff -r {old_rev}:{new_rev} --summarize'
    else:
        logger.info("현재 작업 사본 변경사항")
        cmd = 'svn status'

    output = run_svn_cmd(cmd, cwd=repo_path)
    if not output:
        return []

    cpp_ext = (".cpp", ".hpp", ".h", ".cc", ".cxx", ".c")
    changed = []
    
    for line in output.splitlines():
        if not line.strip():
            continue
        
        if old_rev and new_rev:
            parts = line.split(None, 1)
            if len(parts) < 2:
                continue
            status, file = parts[0], parts[1]
        else:
            # svn status 형식
            if len(line) < 8:
                continue
            status = line[0]
            file = line[7:].strip()
        
        if status in ["M", "A"] and file.endswith(cpp_ext):
            changed.append(file)
            logger.info(f"  ✓ {file} ({status})")
    
    logger.info(f"총 {len(changed)}개 C/C++ 파일 변경됨")
    return changed


def get_svn_diff(repo_path: Path, file_path: str, old_rev=None, new_rev=None):
    """SVN diff 내용"""
    if old_rev and new_rev:
        cmd = f'svn diff -r {old_rev}:{new_rev} "{file_path}"'
    else:
        cmd = f'svn diff "{file_path}"'
    
    return run_svn_cmd(cmd, cwd=repo_path)


# ------------------------------------------------------------
# Fork 모드용 파일 탐색
# ------------------------------------------------------------
def find_cpp_files(work_path: Path, mode="all", folder=None, file=None, recent_days=7):
    """C++ 파일 탐색"""
    cpp_exts = ["*.cpp", "*.hpp", "*.cc", "*.h", "*.cxx", "*.hxx", "*.c"]
    result = []
    
    logger.info(f"\n=== C++ 파일 탐색 (모드: {mode}) ===")
    
    if mode == "single" and file:
        target = work_path / file
        if target.exists():
            result.append(target)
            logger.info(f"  ✓ {target}")
    
    elif mode == "folder" and folder:
        target = work_path / folder
        logger.info(f"폴더 스캔: {target}")
        for ext in cpp_exts:
            result.extend(glob.glob(str(target / "**" / ext), recursive=True))
    
    elif mode == "recent":
        since = datetime.now() - timedelta(days=recent_days)
        logger.info(f"최근 {recent_days}일 이내 수정된 파일 검색...")
        for ext in cpp_exts:
            for p in glob.glob(str(work_path / "**" / ext), recursive=True):
                if datetime.fromtimestamp(os.path.getmtime(p)) > since:
                    result.append(Path(p))
    
    else:  # all
        logger.info(f"전체 C++ 파일 검색...")
        for ext in cpp_exts:
            result.extend([Path(p) for p in glob.glob(str(work_path / "**" / ext), recursive=True)])
    
    logger.info(f"총 {len(result)}개 파일 발견")
    return result


# ------------------------------------------------------------
# 파일 읽기 (인코딩 개선)
# ------------------------------------------------------------
def read_file_with_fallback_encoding(file_path: Path):
    """여러 인코딩을 시도하여 파일 읽기"""
    encodings = ['utf-8', 'cp949', 'euc-kr', 'latin-1', 'utf-16']
    
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()
            logger.debug(f"파일 읽기 성공 ({encoding}): {file_path.name}")
            return content
        except (UnicodeDecodeError, LookupError):
            continue
    
    # 모든 인코딩 실패 시 마지막 시도 (errors='replace')
    try:
        with open(file_path, "r", encoding='utf-8', errors='replace') as f:
            content = f.read()
        logger.warning(f"⚠️ 인코딩 감지 실패, 일부 문자 손실 가능: {file_path.name}")
        return content
    except Exception as e:
        logger.error(f"❌ 파일 읽기 실패: {file_path.name} - {e}")
        return None


# ------------------------------------------------------------
# Diff 파싱 (SVN 모드) - 개선된 버전
# ------------------------------------------------------------
def extract_meaningful_changes(diff_text: str):
    """의미있는 변경사항만 추출"""
    if not diff_text or not diff_text.strip():
        return []
    
    sections = []
    current_section = []
    section_header = None
    has_actual_change = False
    
    for line in diff_text.splitlines():
        # 파일 헤더 스킵
        if line.startswith("---") or line.startswith("+++"):
            continue
        
        # 새 섹션 시작
        if line.startswith("@@"):
            # 이전 섹션 저장
            if current_section and has_actual_change:
                sections.append({
                    "header": section_header,
                    "diff": "\n".join(current_section)
                })
            
            # 새 섹션 초기화
            section_header = line
            current_section = [line]
            has_actual_change = False
            continue
        
        # 실제 변경사항 체크
        if line.startswith("+") or line.startswith("-"):
            # 빈 라인 변경은 무시
            if line.strip() not in ["+", "-"]:
                has_actual_change = True
        
        current_section.append(line)
    
    # 마지막 섹션 저장
    if current_section and has_actual_change:
        sections.append({
            "header": section_header,
            "diff": "\n".join(current_section)
        })
    
    return sections


def extract_context_name(diff_section: str):
    """diff에서 함수/클래스 이름 추출"""
    patterns = [
        r'\b\w+[\w\s\*&:<>,]*\s+(\w+::\w+|\w+)\s*\([^)]*\)',  # 함수
        r'\bclass\s+(\w+)',  # 클래스
        r'\bstruct\s+(\w+)',  # 구조체
    ]
    
    for line in diff_section.split('\n')[:20]:  # 앞부분만 체크
        clean_line = line.lstrip('+ -')
        for pattern in patterns:
            match = re.search(pattern, clean_line)
            if match:
                return match.group(1)
    
    return "Code Section"


# ------------------------------------------------------------
# 리뷰 프롬프트 생성
# ------------------------------------------------------------
def create_prompt_diff_review(file_name: str, changes: list, model: str):
    """diff 리뷰 프롬프트"""
    change_text = ""
    for ch in changes:
        context = extract_context_name(ch["diff"])
        change_text += f"\n### {ch['header']} - {context}\n"
        change_text += ch["diff"][:2000]  # 토큰 제한
        change_text += "\n"
    
    prompt = f"""당신은 {model} 모델을 사용하는 15년 경력의 C++ 전문가입니다.
다음 파일의 변경사항을 리뷰하세요.

파일: {file_name}
변경 내용:
{change_text}

검토 항목:
1. 🔴 **버그 위험**: 메모리 누수, nullptr 접근, 논리 오류
2. 🟡 **성능**: 불필요한 복사, 비효율적 알고리즘
3. 🟢 **코드 품질**: 가독성, 모던 C++ 활용, 네이밍

출력 형식:
- 각 항목별로 구체적인 라인 번호와 개선 방안 제시
- 심각도 이모지로 우선순위 표시

한국어로 작성하세요."""
    
    return prompt


def create_prompt_file_review(file_name: str, code: str, model: str):
    """전체 파일 리뷰 프롬프트"""
    # 토큰 제한 (약 3000 토큰)
    code_preview = code[:12000] if len(code) > 12000 else code
    truncated = len(code) > 12000
    
    prompt = f"""당신은 {model} 모델을 사용하는 C++ 코드 리뷰어입니다.
다음 파일을 전체적으로 리뷰하세요.

파일: {file_name}
{'[주의: 파일이 너무 커서 앞부분만 표시됨]' if truncated else ''}

```cpp
{code_preview}
```

검토 항목:
1. 전반적인 구조와 설계
2. 잠재적 버그 및 취약점
3. 성능 개선 포인트
4. 모던 C++ 활용 가능성

한국어로 간결하게 작성하세요."""
    
    return prompt


# ------------------------------------------------------------
# 코드 리뷰 수행 (재시도 로직 포함)
# ------------------------------------------------------------
def perform_review(client, model, max_tokens, temperature, prompt, max_retries=3):
    """OpenAI API 호출 (재시도 로직 포함)"""
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "당신은 C++ 전문가로서 코드를 분석하고 개선 방안을 제시합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return resp.choices[0].message.content
        
        except Exception as e:
            error_msg = str(e)
            
            # Rate limit 처리
            if 'rate_limit' in error_msg.lower():
                wait_time = 2 ** attempt  # 지수 백오프: 1초, 2초, 4초
                logger.warning(f"⚠️ API rate limit (시도 {attempt + 1}/{max_retries}), {wait_time}초 대기...")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ API 호출 최종 실패 (rate limit): {error_msg}")
                    return f"❌ API 호출 실패 (rate limit): {error_msg}"
            
            # Quota 초과는 재시도 불가
            elif 'insufficient_quota' in error_msg.lower():
                logger.error(f"❌ API quota 초과: {error_msg}")
                return f"❌ API 호출 실패 (quota 초과): {error_msg}"
            
            # 기타 오류
            else:
                logger.warning(f"⚠️ 리뷰 요청 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    logger.error(f"❌ 리뷰 요청 최종 실패: {e}")
                    return f"❌ 리뷰 요청 실패: {e}"
    
    return "❌ 알 수 없는 오류"


# ------------------------------------------------------------
# 결과 저장
# ------------------------------------------------------------
def save_markdown(out_path: Path, mode: str, reviews: list, files_count: int):
    """Markdown 형식으로 저장"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# 🧾 C++ 코드 리뷰 결과\n\n")
        f.write(f"- **모드**: {mode.upper()}\n")
        f.write(f"- **생성 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- **리뷰 파일 수**: {files_count}\n")
        f.write(f"- **리뷰 섹션 수**: {len(reviews)}\n\n")
        f.write("---\n\n")
        
        for i, r in enumerate(reviews, 1):
            f.write(f"## 📄 [{i}/{len(reviews)}] {r['title']}\n\n")
            f.write(r["content"])
            f.write("\n\n---\n\n")
    
    logger.info(f"✅ 결과 저장 완료: {out_path}")


# ------------------------------------------------------------
# 메인 실행
# ------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="통합형 C++ 코드 리뷰어 (Git + SVN + Fork)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 자동 모드 (Git/SVN 자동 감지)
  python CodeReview.py --path C:/work/repo --mode auto
  
  # Git 현재 변경사항 리뷰
  python CodeReview.py --path C:/work/repo --mode git
  
  # Git 커밋 비교
  python CodeReview.py --path C:/work/repo --mode git --old HEAD~1 --new HEAD
  
  # SVN 현재 변경사항 리뷰
  python CodeReview.py --path C:/work/repo --mode svn
  
  # SVN 특정 리비전 비교
  python CodeReview.py --path C:/work/repo --mode svn --old 1234 --new 1235
  
  # Fork 모드: 최근 N일 파일
  python CodeReview.py --path C:/work/project --mode recent
  
  # Fork 모드: 특정 파일
  python CodeReview.py --path C:/work/project --mode single --file main.cpp
        """
    )
    
    parser.add_argument("--path", required=True, help="리뷰 대상 경로")
    parser.add_argument("--config", default="config.json", help="OpenAI 설정 파일")
    parser.add_argument("--mode", default="auto",
                        choices=["auto", "all", "recent", "folder", "single", "git", "svn"],
                        help="리뷰 모드")
    parser.add_argument("--folder", default=None, help="특정 폴더 (Fork 모드)")
    parser.add_argument("--file", default=None, help="특정 파일 (Fork 모드)")
    parser.add_argument("--old", default=None, help="Git/SVN 이전 커밋/리비전")
    parser.add_argument("--new", default=None, help="Git/SVN 새 커밋/리비전")
    parser.add_argument("--output", default="codereview.md", help="결과 파일명")
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("🔍 통합형 C++ 코드 리뷰어 (Git + SVN + Fork)")
    logger.info("=" * 60)
    
    # Config 로드
    cfg = load_config(args.config)
    client = init_openai_client(cfg["api_key"])
    model = cfg.get("model", "gpt-4o-mini")
    max_tokens = cfg.get("max_tokens", 2000)
    temp = cfg.get("temperature", 0.3)
    max_retries = cfg.get("max_retries", 3)
    recent_days = cfg.get("recent_days", 7)
    max_files = cfg.get("max_files", 20)
    max_code_tokens = cfg.get("max_code_tokens", 12000)
    
    work_path = Path(args.path)
    if not work_path.exists():
        logger.error(f"❌ 경로가 존재하지 않습니다: {work_path}")
        sys.exit(f"❌ 경로가 존재하지 않습니다: {work_path}")
    
    # 모드 자동 결정
    vcs_type = None
    if args.mode == "auto":
        vcs_type = detect_vcs(work_path)
        if vcs_type:
            mode_name = vcs_type.upper()
            logger.info(f"✅ 자동 감지: {mode_name} 모드")
        else:
            logger.info("✅ 자동 감지: Fork 모드")
    elif args.mode in ["git", "svn"]:
        vcs_type = args.mode
    
    reviews = []
    files_count = 0
    
    # Git 모드
    if vcs_type == "git" or args.mode == "git":
        logger.info("\n🔧 Git Diff 모드로 실행 중...")
        
        changed = get_git_changed_files(work_path, args.old, args.new)
        if not changed:
            logger.warning("📝 변경된 C++ 파일이 없습니다.")
            sys.exit("📝 변경된 C++ 파일이 없습니다.")
        
        files_count = len(changed)
        
        for file_path in changed:
            logger.info(f"\n--- 분석 중: {file_path} ---")
            
            diff_text = get_git_diff(work_path, file_path, args.old, args.new)
            if not diff_text:
                logger.warning(f"  ⚠️ diff 가져오기 실패")
                continue
            
            sections = extract_meaningful_changes(diff_text)
            if not sections:
                logger.info(f"  ℹ️ 의미있는 변경사항 없음")
                continue
            
            logger.info(f"  ✓ {len(sections)}개 변경 섹션 발견")
            
            # 리뷰 수행
            prompt = create_prompt_diff_review(file_path, sections, model)
            review = perform_review(client, model, max_tokens, temp, prompt, max_retries)
            
            reviews.append({
                "title": f"{file_path} (Git Diff)",
                "content": review
            })
    
    # SVN 모드
    elif vcs_type == "svn" or args.mode == "svn":
        logger.info("\n🔧 SVN Diff 모드로 실행 중...")
        
        changed = get_changed_files(work_path, args.old, args.new)
        if not changed:
            logger.warning("📝 변경된 C++ 파일이 없습니다.")
            sys.exit("📝 변경된 C++ 파일이 없습니다.")
        
        files_count = len(changed)
        
        for file_path in changed:
            logger.info(f"\n--- 분석 중: {file_path} ---")
            
            diff_text = get_svn_diff(work_path, file_path, args.old, args.new)
            if not diff_text:
                logger.warning(f"  ⚠️ diff 가져오기 실패")
                continue
            
            sections = extract_meaningful_changes(diff_text)
            if not sections:
                logger.info(f"  ℹ️ 의미있는 변경사항 없음")
                continue
            
            logger.info(f"  ✓ {len(sections)}개 변경 섹션 발견")
            
            # 리뷰 수행
            prompt = create_prompt_diff_review(file_path, sections, model)
            review = perform_review(client, model, max_tokens, temp, prompt, max_retries)
            
            reviews.append({
                "title": f"{file_path} (SVN Diff)",
                "content": review
            })
    
    # Fork 모드
    else:
        logger.info("\n📁 Fork(일반 폴더) 모드로 실행 중...")
        
        files = find_cpp_files(work_path, args.mode, args.folder, args.file, recent_days)
        if not files:
            logger.warning("📝 리뷰할 C++ 파일이 없습니다.")
            sys.exit("📝 리뷰할 C++ 파일이 없습니다.")
        
        # 파일 수 제한 (토큰 절약)
        if len(files) > max_files:
            logger.warning(f"⚠️ 파일이 {len(files)}개로 많습니다. 처음 {max_files}개만 리뷰합니다.")
            files = files[:max_files]
        
        files_count = len(files)
        
        for file_path in files:
            logger.info(f"\n--- 분석 중: {file_path.name} ---")
            
            content = read_file_with_fallback_encoding(file_path)
            if content is None:
                logger.warning(f"  ⚠️ 파일 읽기 실패")
                continue
            
            if len(content.strip()) < 50:
                logger.info(f"  ℹ️ 파일이 너무 짧아서 스킵")
                continue
            
            # 토큰 제한
            code_preview = content[:max_code_tokens] if len(content) > max_code_tokens else content
            
            prompt = create_prompt_file_review(file_path.name, code_preview, model)
            review = perform_review(client, model, max_tokens, temp, prompt, max_retries)
            
            reviews.append({
                "title": str(file_path.relative_to(work_path)),
                "content": review
            })
    
    # 결과 저장
    if not reviews:
        logger.error("❌ 리뷰할 내용이 없습니다.")
        sys.exit("❌ 리뷰할 내용이 없습니다.")
    
    output_path = work_path / args.output
    mode_name = "Git" if vcs_type == "git" else ("SVN" if vcs_type == "svn" else "Fork")
    save_markdown(output_path, mode_name, reviews, files_count)
    
    logger.info("\n" + "=" * 60)
    logger.info(f"✅ 리뷰 완료!")
    logger.info(f"   파일 수: {files_count}")
    logger.info(f"   리뷰 섹션: {len(reviews)}")
    logger.info(f"   결과: {output_path}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()