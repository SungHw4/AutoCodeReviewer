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
from datetime import datetime, timedelta
from pathlib import Path
from openai import OpenAI


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
    """config.json 로드 (exe와 같은 폴더에서)"""
    exe_dir = get_executable_dir()
    config_path = exe_dir / config_filename
    
    print(f"📁 Config 경로: {config_path}")
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        
        # 두 가지 필드명 모두 지원
        api_key = cfg.get("api_key") or cfg.get("openai_api_key")
        if not api_key:
            sys.exit("❌ config.json에 'api_key' 또는 'openai_api_key'가 없습니다.")
        
        cfg["api_key"] = api_key  # 통일된 키 이름
        print(f"✅ Config 로드 성공 (model: {cfg.get('model', 'gpt-4o-mini')})")
        return cfg
        
    except FileNotFoundError:
        sys.exit(f"❌ config.json을 찾을 수 없습니다: {config_path}")
    except json.JSONDecodeError as e:
        sys.exit(f"❌ config.json 형식 오류: {e}")


def init_openai_client(api_key: str):
    """OpenAI 클라이언트 초기화"""
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        sys.exit(f"❌ OpenAI 초기화 실패: {e}")


# ------------------------------------------------------------
# SVN 관련 함수
# ------------------------------------------------------------
def detect_svn_repo(path: Path) -> bool:
    """SVN 리포지토리 감지"""
    return (path / ".svn").exists()


def run_svn_cmd(cmd, cwd):
    """SVN 명령어 실행 (Windows 호환)"""
    try:
        # Windows에서는 shell=True 권장
        if isinstance(cmd, list):
            cmd = " ".join(cmd)
        
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
            print(f"⚠️ SVN 명령 실패: {cmd}")
            print(f"   오류: {result.stderr}")
            return None
        
        return result.stdout
    except Exception as e:
        print(f"⚠️ SVN 명령 실행 오류: {e}")
        return None


def get_changed_files(repo_path: Path, old_rev=None, new_rev=None):
    """SVN 변경 파일 목록"""
    print("\n=== SVN 변경 파일 스캔 ===")
    
    if old_rev and new_rev:
        print(f"리비전 비교: r{old_rev} → r{new_rev}")
        cmd = f'svn diff -r {old_rev}:{new_rev} --summarize'
    else:
        print("현재 작업 사본 변경사항")
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
            print(f"  ✓ {file} ({status})")
    
    print(f"총 {len(changed)}개 C/C++ 파일 변경됨")
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
def find_cpp_files(work_path: Path, mode="all", folder=None, file=None):
    """C++ 파일 탐색"""
    cpp_exts = ["*.cpp", "*.hpp", "*.cc", "*.h", "*.cxx", "*.hxx", "*.c"]
    result = []
    
    print(f"\n=== C++ 파일 탐색 (모드: {mode}) ===")
    
    if mode == "single" and file:
        target = work_path / file
        if target.exists():
            result.append(target)
            print(f"  ✓ {target}")
    
    elif mode == "folder" and folder:
        target = work_path / folder
        print(f"폴더 스캔: {target}")
        for ext in cpp_exts:
            result.extend(glob.glob(str(target / "**" / ext), recursive=True))
    
    elif mode == "recent":
        since = datetime.now() - timedelta(days=7)
        print(f"최근 7일 이내 수정된 파일 검색...")
        for ext in cpp_exts:
            for p in glob.glob(str(work_path / "**" / ext), recursive=True):
                if datetime.fromtimestamp(os.path.getmtime(p)) > since:
                    result.append(Path(p))
    
    else:  # all
        print(f"전체 C++ 파일 검색...")
        for ext in cpp_exts:
            result.extend([Path(p) for p in glob.glob(str(work_path / "**" / ext), recursive=True)])
    
    print(f"총 {len(result)}개 파일 발견")
    return result


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
# 코드 리뷰 수행
# ------------------------------------------------------------
def perform_review(client, model, max_tokens, temperature, prompt):
    """OpenAI API 호출"""
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
        if 'rate_limit' in error_msg.lower() or 'insufficient_quota' in error_msg.lower():
            print(f"⚠️ API 한도 초과: {error_msg}")
            return f"❌ API 호출 실패 (한도 초과): {error_msg}"
        
        print(f"⚠️ 리뷰 요청 실패: {e}")
        return f"❌ 리뷰 요청 실패: {e}"


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
    
    print(f"✅ 결과 저장 완료: {out_path}")


# ------------------------------------------------------------
# 메인 실행
# ------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="통합형 C++ 코드 리뷰어 (Fork + SVN)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # SVN 현재 변경사항 리뷰
  python CodeReview.py --path C:/work/repo --mode svn
  
  # SVN 특정 리비전 비교
  python CodeReview.py --path C:/work/repo --mode svn --old 1234 --new 1235
  
  # Fork 모드: 최근 7일 파일
  python CodeReview.py --path C:/work/project --mode recent
  
  # Fork 모드: 특정 파일
  python CodeReview.py --path C:/work/project --mode single --file main.cpp
        """
    )
    
    parser.add_argument("--path", required=True, help="리뷰 대상 경로")
    parser.add_argument("--config", default="config.json", help="OpenAI 설정 파일")
    parser.add_argument("--mode", default="auto",
                        choices=["auto", "all", "recent", "folder", "single", "svn"],
                        help="리뷰 모드")
    parser.add_argument("--folder", default=None, help="특정 폴더 (Fork 모드)")
    parser.add_argument("--file", default=None, help="특정 파일 (Fork 모드)")
    parser.add_argument("--old", default=None, help="SVN 이전 리비전")
    parser.add_argument("--new", default=None, help="SVN 새 리비전")
    parser.add_argument("--output", default="codereview.md", help="결과 파일명")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔍 통합형 C++ 코드 리뷰어")
    print("=" * 60)
    
    # Config 로드
    cfg = load_config(args.config)
    client = init_openai_client(cfg["api_key"])
    model = cfg.get("model", "gpt-4o-mini")
    max_tokens = cfg.get("max_tokens", 2000)
    temp = cfg.get("temperature", 0.3)
    
    work_path = Path(args.path)
    if not work_path.exists():
        sys.exit(f"❌ 경로가 존재하지 않습니다: {work_path}")
    
    # 모드 자동 결정
    if args.mode == "auto":
        is_svn = detect_svn_repo(work_path)
        mode_name = "SVN" if is_svn else "Fork"
        print(f"✅ 자동 감지: {mode_name} 모드")
    else:
        is_svn = (args.mode == "svn")
    
    reviews = []
    files_count = 0
    
    # SVN 모드
    if is_svn:
        print("\n🔧 SVN Diff 모드로 실행 중...")
        
        changed = get_changed_files(work_path, args.old, args.new)
        if not changed:
            sys.exit("📝 변경된 C++ 파일이 없습니다.")
        
        files_count = len(changed)
        
        for file_path in changed:
            print(f"\n--- 분석 중: {file_path} ---")
            
            diff_text = get_svn_diff(work_path, file_path, args.old, args.new)
            if not diff_text:
                print(f"  ⚠️ diff 가져오기 실패")
                continue
            
            sections = extract_meaningful_changes(diff_text)
            if not sections:
                print(f"  ℹ️ 의미있는 변경사항 없음")
                continue
            
            print(f"  ✓ {len(sections)}개 변경 섹션 발견")
            
            # 리뷰 수행
            prompt = create_prompt_diff_review(file_path, sections, model)
            review = perform_review(client, model, max_tokens, temp, prompt)
            
            reviews.append({
                "title": f"{file_path} (SVN Diff)",
                "content": review
            })
    
    # Fork 모드
    else:
        print("\n📁 Fork(일반 폴더) 모드로 실행 중...")
        
        files = find_cpp_files(work_path, args.mode, args.folder, args.file)
        if not files:
            sys.exit("📝 리뷰할 C++ 파일이 없습니다.")
        
        # 파일 수 제한 (토큰 절약)
        max_files = 20
        if len(files) > max_files:
            print(f"⚠️ 파일이 {len(files)}개로 많습니다. 처음 {max_files}개만 리뷰합니다.")
            files = files[:max_files]
        
        files_count = len(files)
        
        for file_path in files:
            print(f"\n--- 분석 중: {file_path.name} ---")
            
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as src:
                    content = src.read()
                
                if len(content.strip()) < 50:
                    print(f"  ℹ️ 파일이 너무 짧아서 스킵")
                    continue
                
                prompt = create_prompt_file_review(file_path.name, content, model)
                review = perform_review(client, model, max_tokens, temp, prompt)
                
                reviews.append({
                    "title": str(file_path.relative_to(work_path)),
                    "content": review
                })
                
            except Exception as e:
                print(f"  ⚠️ 파일 읽기 실패: {e}")
    
    # 결과 저장
    if not reviews:
        sys.exit("❌ 리뷰할 내용이 없습니다.")
    
    output_path = work_path / args.output
    save_markdown(output_path, "SVN" if is_svn else "Fork", reviews, files_count)
    
    print("\n" + "=" * 60)
    print(f"✅ 리뷰 완료!")
    print(f"   파일 수: {files_count}")
    print(f"   리뷰 섹션: {len(reviews)}")
    print(f"   결과: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()