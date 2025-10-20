#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fork 사용자용 C++ 코드 리뷰어 - Config 기반 모델 선택 지원
Git 명령어 없이 작동하며, config.json에서 OpenAI 모델을 자유롭게 설정 가능
"""

import argparse
import os
import sys
import json
import openai
from datetime import datetime, timedelta
import glob
import time

class ForkCompatibleCodeReviewer:
    def __init__(self, config_path="config.json"):
        """Fork 호환 코드 리뷰어 초기화"""
        self.config = self.load_config(config_path)
        self.client = self.init_openai_client()
        
        # 모델별 설정
        self.model_configs = {
            "gpt-4": {"max_tokens": 2000, "context_window": 8000},
            "gpt-4o": {"max_tokens": 2000, "context_window": 8000},
            "gpt-4-turbo": {"max_tokens": 3000, "context_window": 12000},
            "gpt-4-turbo-preview": {"max_tokens": 3000, "context_window": 12000},
            "gpt-3.5-turbo": {"max_tokens": 1500, "context_window": 4000},
            "gpt-3.5-turbo-16k": {"max_tokens": 2500, "context_window": 10000}
        }
        
        print(f"🤖 사용 모델: {self.config.get('model', 'gpt-4o')}")
        print(f"📊 최대 토큰: {self.get_model_max_tokens()}")
    
    def load_config(self, config_path):
        """config.json 파일 로드"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                # 필수 설정 확인
                if not config.get('openai_api_key') or config['openai_api_key'] == "여기에-실제-API-키-입력하세요":
                    print("❌ config.json에서 올바른 OpenAI API 키를 설정해주세요.")
                    sys.exit(1)
                
                # 기본값 설정
                config.setdefault('model', 'gpt-4')
                config.setdefault('temperature', 0.3)
                config.setdefault('max_tokens', 2000)
                
                return config
                
        except FileNotFoundError:
            print(f"❌ {config_path} 파일을 찾을 수 없습니다.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ {config_path} 파일 형식 오류: {e}")
            sys.exit(1)
    
    def init_openai_client(self):
        """OpenAI 클라이언트 초기화"""
        try:
            client = openai.OpenAI(api_key=self.config['openai_api_key'])
            return client
        except Exception as e:
            print(f"❌ OpenAI 클라이언트 초기화 실패: {e}")
            sys.exit(1)
    
    def get_model_max_tokens(self):
        """현재 모델의 최대 토큰 수 반환"""
        model = self.config.get('model', 'gpt-4')
        
        # config에서 직접 설정한 값이 있으면 우선 사용
        if 'max_tokens' in self.config and self.config['max_tokens'] != 2000:
            return self.config['max_tokens']
        
        # 모델별 기본값 사용
        return self.model_configs.get(model, {}).get('max_tokens', 2000)
    
    def get_context_window(self):
        """현재 모델의 컨텍스트 윈도우 크기 반환"""
        model = self.config.get('model', 'gpt-4')
        return self.model_configs.get(model, {}).get('context_window', 8000)
    
    def find_cpp_files(self, work_path, mode='all-files', target_folder=None, target_file=None):
        """C++ 파일들을 찾기 (다양한 모드 지원)"""
        cpp_extensions = ['*.cpp', '*.hpp', '*.cc', '*.h', '*.cxx', '*.hxx', '*.c']
        found_files = []
        
        try:
            if mode == 'single-file' and target_file:
                file_path = os.path.join(work_path, target_file)
                if os.path.exists(file_path):
                    found_files.append(file_path)
                    print(f"📄 대상 파일: {target_file}")
                else:
                    print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
                    return []
            
            elif mode == 'folder' and target_folder:
                search_path = os.path.join(work_path, target_folder)
                if os.path.exists(search_path):
                    for ext in cpp_extensions:
                        pattern = os.path.join(search_path, '**', ext)
                        found_files.extend(glob.glob(pattern, recursive=True))
                    print(f"📁 대상 폴더: {target_folder} ({len(found_files)}개 파일)")
                else:
                    print(f"❌ 폴더를 찾을 수 없습니다: {search_path}")
                    return []
            
            elif mode == 'recent-files':
                # 최근 7일 이내 수정된 파일들
                recent_time = datetime.now() - timedelta(days=7)
                for ext in cpp_extensions:
                    pattern = os.path.join(work_path, '**', ext)
                    for file_path in glob.glob(pattern, recursive=True):
                        if datetime.fromtimestamp(os.path.getmtime(file_path)) > recent_time:
                            found_files.append(file_path)
                print(f"🕒 최근 수정된 파일: {len(found_files)}개")
            
            else:  # 'all-files'
                for ext in cpp_extensions:
                    pattern = os.path.join(work_path, '**', ext)
                    found_files.extend(glob.glob(pattern, recursive=True))
                print(f"📂 전체 C++ 파일: {len(found_files)}개")
            
            return found_files[:20]  # 최대 20개 파일로 제한
            
        except Exception as e:
            print(f"❌ 파일 검색 중 오류: {e}")
            return []
    
    def read_file_content(self, file_path, max_lines=200):
        """파일 내용 읽기 (길이 제한 포함)"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
                if len(lines) > max_lines:
                    content = ''.join(lines[:max_lines])
                    content += f"\n\n... (파일이 길어서 {max_lines}줄까지만 표시)"
                else:
                    content = ''.join(lines)
                
                return content
                
        except Exception as e:
            return f"파일 읽기 오류: {e}"
    
    def create_review_prompt(self, files_content):
        """모델 타입에 따라 최적화된 리뷰 프롬프트 생성"""
        model = self.config.get('model', 'gpt-4')
        
        # 모델별 프롬프트 최적화
        if 'gpt-4' in model:
            expertise_level = "15년 경력의 시니어 C++ 아키텍트"
            detail_level = "매우 상세하고 전문적인"
        elif '3.5' in model:
            expertise_level = "10년 경력의 C++ 개발자"
            detail_level = "실용적이고 명확한"
        else:
            expertise_level = "경험 많은 C++ 전문가"
            detail_level = "전문적이고 구체적인"
        
        prompt = f"""
다음은 C++ 프로젝트의 소스 코드입니다. {expertise_level}의 관점에서 {detail_level} 코드 리뷰를 진행해주세요.

**핵심 검토 항목:**
1. 🔍 메모리 관리 및 안전성
   - 메모리 누수 가능성
   - 댕글링 포인터 위험
   - 스마트 포인터 활용도
   - RAII 패턴 적용

2. ⚡ 성능 최적화
   - 알고리즘 효율성
   - 불필요한 복사 연산
   - 캐시 친화적 설계
   - 컴파일러 최적화 힌트

3. 🆕 모던 C++ 활용 ({model} 최적화)
   - C++11/14/17/20 기능 적용
   - auto, 람다, 범위 기반 for
   - constexpr, noexcept 활용
   - 표준 라이브러리 최신 기능

4. 🛡️ 안전성 및 견고성
   - 예외 안전성
   - 경계 검사
   - 타입 안전성
   - 에러 처리 방식

5. 📖 코드 품질
   - 가독성 및 유지보수성
   - 네이밍 컨벤션
   - 코드 구조 및 설계
   - 주석 및 문서화

**출력 형식:**
- 각 파일별로 분석 결과 제시
- 심각도별 분류: 🔴 높음(즉시 수정) / 🟡 보통(개선 권장) / 🟢 낮음(선택사항)
- 구체적인 개선 방안 및 수정 예시 코드 제공

**분석 대상 코드:**
{files_content}

한국어로 {detail_level} 분석을 제공해주세요.
"""
        
        return prompt
    
    def review_code(self, files_content):
        """OpenAI API로 코드 리뷰 수행"""
        if not files_content or len(files_content.strip()) == 0:
            return "📝 리뷰할 C++ 코드가 없습니다."
        
        # 컨텍스트 윈도우에 맞게 내용 조정
        context_window = self.get_context_window()
        if len(files_content) > context_window:
            files_content = files_content[:context_window] + "\n\n... (내용이 길어서 일부만 표시됩니다)"
        
        try:
            prompt = self.create_review_prompt(files_content)
            
            model = self.config.get('model', 'gpt-4')
            max_tokens = self.get_model_max_tokens()
            temperature = self.config.get('temperature', 0.3)
            
            print(f"🤖 {model} 모델로 분석 중...")
            print(f"📊 설정 - 최대토큰: {max_tokens}, 온도: {temperature}")
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system", 
                        "content": f"당신은 {model} 모델을 활용하는 전문 C++ 코드 리뷰어입니다. Fork Git GUI를 사용하는 개발팀을 위해 실용적이고 구체적인 리뷰를 제공하세요."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except openai.RateLimitError:
            return "❌ API 사용량 한도 초과. 잠시 후 다시 시도해주세요."
        except openai.AuthenticationError:
            return "❌ API 키가 유효하지 않습니다. config.json을 확인해주세요."
        except openai.BadRequestError as e:
            return f"❌ 요청 오류: {e}. 모델명이 정확한지 확인해주세요."
        except Exception as e:
            return f"❌ API 호출 중 예상치 못한 오류: {e}"
    
    def save_review(self, review_content, output_filename, work_path, files_info):
        """리뷰 결과를 파일로 저장"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            model = self.config.get('model', 'gpt-4')
            
            header = f"""
===============================================
        Fork 호환 C++ 코드 리뷰 결과
===============================================
생성 시간: {timestamp}
사용 모델: {model}
리뷰 대상: {len(files_info)}개 파일
작업 경로: {work_path}

분석된 파일 목록:
{chr(10).join(['• ' + f for f in files_info]) if files_info else '• 파일 정보 없음'}

===============================================
                  리뷰 내용
===============================================

"""
            
            footer = f"""

===============================================
                  리뷰 완료
===============================================
생성 시간: {timestamp}
Fork GUI 호환 | {model} 분석 | Git CLI 불필요
==============================================="""
            
            full_content = header + review_content + footer
            
            output_path = os.path.join(work_path, f"{output_filename}.txt")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            print(f"✅ 리뷰 결과가 저장되었습니다: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ 파일 저장 중 오류: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Fork 호환 C++ 코드 리뷰어 - Config 기반 모델 선택')
    parser.add_argument('--work-path', type=str, required=True,
                       help='작업할 프로젝트 경로')
    parser.add_argument('--mode', type=str, default='recent-files',
                       choices=['all-files', 'recent-files', 'folder', 'single-file'],
                       help='리뷰 모드 선택')
    parser.add_argument('--target-folder', type=str, default=None,
                       help='특정 폴더만 리뷰할 경우 폴더명')
    parser.add_argument('--target-file', type=str, default=None,
                       help='특정 파일만 리뷰할 경우 파일명')
    parser.add_argument('--output', type=str, default='codereview',
                       help='출력 파일명 (확장자 제외)')
    parser.add_argument('--config', type=str, default='config.json',
                       help='설정 파일 경로')
    
    args = parser.parse_args()
    
    # 작업 경로 확인
    if not os.path.exists(args.work_path):
        print(f"❌ 작업 경로가 존재하지 않습니다: {args.work_path}")
        sys.exit(1)
    
    # 리뷰어 초기화
    try:
        reviewer = ForkCompatibleCodeReviewer(args.config)
    except SystemExit:
        return
    
    print(f"📂 작업 경로: {args.work_path}")
    print(f"🎯 리뷰 모드: {args.mode}")
    
    # C++ 파일 찾기
    cpp_files = reviewer.find_cpp_files(
        args.work_path, 
        args.mode, 
        args.target_folder, 
        args.target_file
    )
    
    if not cpp_files:
        print("📝 리뷰할 C++ 파일을 찾을 수 없습니다.")
        reviewer.save_review("리뷰할 C++ 파일을 찾을 수 없습니다.", args.output, args.work_path, [])
        return
    
    # 파일 내용 읽기
    print("📖 파일 내용 읽는 중...")
    files_content = ""
    files_info = []
    
    for file_path in cpp_files:
        rel_path = os.path.relpath(file_path, args.work_path)
        files_info.append(rel_path)
        
        content = reviewer.read_file_content(file_path)
        files_content += f"\n\n=== 파일: {rel_path} ===\n{content}\n"
    
    # 코드 리뷰 수행
    print("🤖 AI 코드 리뷰 진행 중...")
    review_result = reviewer.review_code(files_content)
    
    # 결과 저장
    if reviewer.save_review(review_result, args.output, args.work_path, files_info):
        print("✅ C++ 코드 리뷰 완료!")
    else:
        print("❌ 코드 리뷰 저장 실패!")
        sys.exit(1)

if __name__ == '__main__':
    main()