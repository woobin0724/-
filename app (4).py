# -*- coding: utf-8 -*-
"""
AI Job Pass Finder
전북기계공고 E.M.P 팀 | 마이스터고 학생 맞춤형 취업 매칭 플랫폼

실행 방법:
    streamlit run app.py

주의사항 (README.md 참고):
- Q-Net / 링커리어 실시간 스크래핑 함수는 예시 구조로 작성되었습니다.
  실제 배포 전 반드시 각 사이트의 robots.txt 및 이용약관을 확인하고,
  최신 HTML 구조에 맞춰 CSS 선택자를 재검증해야 합니다.
- 스크래핑이 실패(사이트 구조 변경, 접속 차단, 네트워크 오류 등)하면
  내부에 내장된 20건의 백업 데이터로 자동 전환(fallback)됩니다.
"""

import time
import random
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st

# ============================================================
# 0. 페이지 기본 설정
# ============================================================
st.set_page_config(
    page_title="AI Job Pass Finder",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 1. 디자인 토큰 & 커스텀 CSS
#    - '데이터 대시보드'의 신뢰감 + 'OGQ 게임 스토리'의 친근함을 5:5로 결합
#    - 블루프린트 네이비 + 세이프티 오렌지의 산업/공고 테마
# ============================================================
INK = "#0B1F33"
BLUE = "#123A5C"
LINE = "#3E6E97"
PAPER = "#EDEBE2"
PAPER_DIM = "#DFDCCF"
AMBER = "#FF7A33"
AMBER_DEEP = "#E05E17"
BRASS = "#C9A24B"
GREEN = "#3E9B6F"
RED = "#D9534F"
STEEL = "#8CA0AE"

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

.stApp {{
    background-color: {INK};
}}
html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

/* 상단 배지 */
.eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    color: {STEEL};
    font-size: 12px;
    letter-spacing: 0.2em;
    margin-bottom: 6px;
}}

/* NPC 말풍선 (OGQ 캐릭터 대사창) */
.speech-bubble {{
    background: {PAPER};
    border: 2px solid {INK};
    border-radius: 16px;
    padding: 16px 18px;
    color: {INK};
    font-weight: 500;
    font-size: 15px;
    line-height: 1.5;
    position: relative;
}}

/* 섹션 타이틀 */
.section-title {{
    font-family: 'Rajdhani', sans-serif;
    color: {PAPER};
    font-weight: 700;
    font-size: 17px;
    letter-spacing: 0.03em;
    margin: 22px 0 10px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.section-title .idx {{
    color: {AMBER};
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
}}

/* 기업 매칭 카드 */
.job-card {{
    background: {PAPER};
    border: 2px solid {INK};
    border-radius: 16px;
    padding: 16px 18px;
    margin-bottom: 16px;
    animation: cardIn 0.5s ease both;
}}
@keyframes cardIn {{
    from {{ opacity: 0; transform: translateY(12px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
.job-card-top {{
    display:flex; justify-content: space-between; align-items:center; margin-bottom: 6px;
}}
.tier-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; font-weight: 700; color: #fff;
    padding: 2px 8px; border-radius: 999px; letter-spacing: 0.05em;
}}
.job-name {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 22px; font-weight: 700; color: {INK}; margin: 4px 0 2px 0;
}}
.job-sub {{
    font-family: 'Inter', sans-serif;
    font-size: 12px; font-weight: 600; color: {LINE}; margin-bottom: 8px;
}}
.cert-tag {{
    display:inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    padding: 2px 7px;
    border-radius: 6px;
    margin: 2px 4px 2px 0;
}}
.feedback-box {{
    background: {BLUE};
    border-radius: 10px;
    padding: 10px 12px;
    margin-top: 10px;
    color: {PAPER};
    font-size: 12.5px;
    line-height: 1.5;
}}

/* 점수 게이지 숫자 */
.score-num {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 30px; font-weight: 700; color: {INK}; text-align:center; line-height: 1;
}}
.score-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; color: {STEEL}; text-align:center; letter-spacing: 0.15em;
}}

/* 로드맵 */
.roadmap-box {{
    background: {BLUE};
    border-radius: 16px;
    padding: 18px;
    margin-top: 10px;
}}
.roadmap-title {{
    font-family: 'Rajdhani', sans-serif;
    color: {PAPER}; font-weight: 700; font-size: 14px; letter-spacing: 0.05em; margin-bottom: 14px;
}}
.stamp-done {{
    background: {AMBER}; border: 2px solid {AMBER_DEEP};
}}
.stamp-pending {{
    background: {INK}; border: 2px solid rgba(255,255,255,0.25);
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ============================================================
# 2. 상수 정의 — 직군 / 자격증 목록 / 등급 기준
# ============================================================
INDUSTRIES = ["기계", "전기", "제조", "IT"]

CERTS_BY_INDUSTRY = {
    "기계": ["컴퓨터응용선반기능사", "컴퓨터응용밀링기능사", "생산자동화기능사", "지게차운전기능사"],
    "전기": ["전기기능사", "전기공사기능사", "승강기기능사", "신재생에너지발전설비기능사"],
    "제조": ["용접기능사", "판금제관기능사", "사출금형기능사", "프레스금형기능사"],
    "IT": ["정보처리기능사", "정보기기운용기능사", "리눅스마스터", "네트워크관리사"],
}

# 마이스터고 5등급 성취평가제 권장 등급 (숫자가 낮을수록 우수)
GRADE_MIN, GRADE_MAX = 1.0, 5.0


# ============================================================
# 3. 백업 데이터 (20건) — 스크래핑 실패 시 자동 대체
#    Q-Net / 링커리어 데이터 구조를 참고하여 구성한 예시(가상) 데이터입니다.
# ============================================================
BACKUP_COMPANIES = [
    {"id": 1, "name": "한빛정밀공업", "industry": "기계", "size": "중견기업",
     "required_certs": ["컴퓨터응용선반기능사", "컴퓨터응용밀링기능사"], "recommended_grade": 2.0,
     "ai_tip": "CNC 선반·밀링 두 자격 동시 보유자의 서류 통과율이 가장 높은 기업이야."},
    {"id": 2, "name": "대성메카트로닉스", "industry": "기계", "size": "중소기업",
     "required_certs": ["생산자동화기능사", "전기기능사"], "recommended_grade": 2.5,
     "ai_tip": "자동화 설비 직무는 전기 기초 지식을 함께 요구하는 추세가 뚜렷해."},
    {"id": 3, "name": "우진산업기계", "industry": "기계", "size": "중소기업",
     "required_certs": ["컴퓨터응용밀링기능사", "지게차운전기능사"], "recommended_grade": 3.0,
     "ai_tip": "현장 실습생 출신 채용 비중이 높은 기업이라 실기 스펙이 유리해."},
    {"id": 4, "name": "태백중공업", "industry": "기계", "size": "대기업",
     "required_certs": ["컴퓨터응용선반기능사", "용접기능사"], "recommended_grade": 2.0,
     "ai_tip": "대기업 계열사라 서류 단계에서 성취도 컷이 존재하는 편이야."},
    {"id": 5, "name": "신성정공", "industry": "기계", "size": "중견기업",
     "required_certs": ["컴퓨터응용밀링기능사", "생산자동화기능사"], "recommended_grade": 1.5,
     "ai_tip": "정밀가공 라인 특성상 최상위 성취도 지원자 선호도가 매우 높아."},
    {"id": 6, "name": "코리아파워시스템", "industry": "전기", "size": "중견기업",
     "required_certs": ["전기기능사", "전기공사기능사"], "recommended_grade": 2.0,
     "ai_tip": "전기기능사+전기공사기능사 조합 보유자는 합격률이 꾸준히 상승 중이야."},
    {"id": 7, "name": "한강전력엔지니어링", "industry": "전기", "size": "중소기업",
     "required_certs": ["전기기능사", "승강기기능사"], "recommended_grade": 3.0,
     "ai_tip": "승강기 유지보수 인력 수요가 커지면서 신입 채용문이 넓어지고 있어."},
    {"id": 8, "name": "대한이엔지", "industry": "전기", "size": "스타트업",
     "required_certs": ["전기기능사"], "recommendedGrade": 2.5, "recommended_grade": 2.5,
     "ai_tip": "소규모 조직이라 자격증 1개만 있어도 실무 역량을 더 중요하게 봐."},
    {"id": 9, "name": "서울전기설비", "industry": "전기", "size": "중소기업",
     "required_certs": ["전기공사기능사", "전기기능사"], "recommended_grade": 3.0,
     "ai_tip": "건축 전기설비 분야라 현장 실습 이수 여부를 가산점으로 반영해."},
    {"id": 10, "name": "미래에너지솔루션", "industry": "전기", "size": "중견기업",
     "required_certs": ["전기기능사", "신재생에너지발전설비기능사"], "recommended_grade": 1.5,
     "ai_tip": "신재생에너지 분야는 최근 채용 공고 수가 가장 빠르게 늘고 있는 영역이야."},
    {"id": 11, "name": "동양금속제관", "industry": "제조", "size": "중소기업",
     "required_certs": ["판금제관기능사", "용접기능사"], "recommended_grade": 3.0,
     "ai_tip": "용접기능사 보유자에게 실기 테스트 없이 서류 우대를 적용하는 기업이야."},
    {"id": 12, "name": "한일사출성형", "industry": "제조", "size": "중소기업",
     "required_certs": ["사출금형기능사"], "recommended_grade": 2.5,
     "ai_tip": "사출금형 단일 자격만으로도 지원 가능해 진입장벽이 낮은 편이야."},
    {"id": 13, "name": "대현프레스산업", "industry": "제조", "size": "중소기업",
     "required_certs": ["프레스금형기능사", "용접기능사"], "recommended_grade": 3.0,
     "ai_tip": "프레스 공정 특성상 안전교육 이수자를 우선 서류 통과시키는 편이야."},
    {"id": 14, "name": "삼진용접테크", "industry": "제조", "size": "중견기업",
     "required_certs": ["용접기능사"], "recommended_grade": 2.0,
     "ai_tip": "용접기능사 단일 보유자 중 성취도 상위권 지원자 채용 비중이 가장 커."},
    {"id": 15, "name": "청호정밀금형", "industry": "제조", "size": "중견기업",
     "required_certs": ["사출금형기능사", "프레스금형기능사"], "recommended_grade": 1.5,
     "ai_tip": "금형 두 자격 동시 보유자는 최근 데이터에서 합격 상위권을 차지했어."},
    {"id": 16, "name": "넥스트웨이브소프트", "industry": "IT", "size": "중견기업",
     "required_certs": ["정보처리기능사", "네트워크관리사"], "recommended_grade": 2.0,
     "ai_tip": "정보처리+네트워크 조합은 백엔드 신입 직무 서류 통과율이 가장 높은 조합이야."},
    {"id": 17, "name": "스마트팩토리시스템즈", "industry": "IT", "size": "중소기업",
     "required_certs": ["정보기기운용기능사", "정보처리기능사"], "recommended_grade": 2.0,
     "ai_tip": "스마트팩토리 관제 직무라 기계 이해도가 있는 IT 인재를 특히 선호해."},
    {"id": 18, "name": "클라우드베이스코리아", "industry": "IT", "size": "스타트업",
     "required_certs": ["리눅스마스터", "네트워크관리사"], "recommended_grade": 1.5,
     "ai_tip": "클라우드 인프라 직무는 최근 채용 공고 증가율 1위 분야로 나타났어."},
    {"id": 19, "name": "한빛데이터센터", "industry": "IT", "size": "중소기업",
     "required_certs": ["정보처리기능사", "리눅스마스터"], "recommended_grade": 2.5,
     "ai_tip": "데이터센터 운영직은 야간 근무 가능 여부보다 자격증 보유를 더 우선시해."},
    {"id": 20, "name": "이지테크솔루션", "industry": "IT", "size": "중소기업",
     "required_certs": ["정보기기운용기능사"], "recommended_grade": 3.0,
     "ai_tip": "단일 자격 요건이라 마이스터고 졸업예정자 채용 문턱이 낮은 기업이야."},
]

# recommendedGrade 오타 키 정리 (id=8 항목 방어 코드)
for _c in BACKUP_COMPANIES:
    _c.pop("recommendedGrade", None)


# ============================================================
# 4. 실시간 데이터 수집 함수 (Q-Net / 링커리어)
#    - 1시간 캐시(@st.cache_data)로 과도한 요청 방지
#    - 예외 발생 시 반드시 백업 데이터로 자동 전환(fallback)
#    - ⚠️ 아래 CSS 선택자는 예시이며, 실제 배포 전 최신 페이지 구조로
#      재검증이 필요합니다. robots.txt 및 이용약관 준수는 필수입니다.
# ============================================================
HEADERS = {"User-Agent": "Mozilla/5.0 (AI-Job-Pass-Finder EMP-Team Bot)"}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_qnet_certs():
    """
    한국산업인력공단(Q-Net, www.q-net.or.kr)에서 국가기술자격 종목 목록을 가져온다.
    실패 시 내장된 CERTS_BY_INDUSTRY 딕셔너리를 그대로 사용한다.
    """
    try:
        url = "https://www.q-net.or.kr/crf005.do"  # 예시 URL (실제 배포 전 검증 필요)
        res = requests.get(url, headers=HEADERS, timeout=5)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        # 실제 페이지 구조에 맞춰 조정이 필요한 부분
        rows = soup.select(".cert-list-table tbody tr")
        if not rows:
            raise ValueError("Q-Net 자격증 목록 파싱 결과가 비어 있음 (페이지 구조 변경 의심)")

        parsed = {k: [] for k in INDUSTRIES}
        for row in rows:
            name = row.select_one(".cert-name")
            category = row.select_one(".cert-category")
            if name and category and category.text.strip() in parsed:
                parsed[category.text.strip()].append(name.text.strip())

        # 파싱은 됐지만 실질 데이터가 비어 있으면 백업으로 대체
        if all(len(v) == 0 for v in parsed.values()):
            raise ValueError("Q-Net 파싱 결과 유효 데이터 없음")

        return parsed, "live"

    except Exception:
        # 네트워크 차단 / 구조 변경 / 타임아웃 등 모든 예외를 여기서 흡수
        return CERTS_BY_INDUSTRY, "backup"


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_linkareer_companies():
    """
    링커리어(Linkareer, linkareer.com)에서 마이스터고 관련 채용 공고를 가져온다.
    실패 시 내장된 BACKUP_COMPANIES(20건)로 자동 전환한다.
    """
    try:
        url = "https://linkareer.com/list/recruit"  # 예시 URL (실제 배포 전 검증 필요)
        res = requests.get(url, headers=HEADERS, timeout=5)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        cards = soup.select(".activity-card")  # 예시 선택자
        if not cards:
            raise ValueError("링커리어 채용 공고 파싱 결과가 비어 있음 (페이지 구조 변경 의심)")

        companies = []
        for i, card in enumerate(cards):
            name_el = card.select_one(".org-name")
            if not name_el:
                continue
            companies.append({
                "id": i + 1,
                "name": name_el.text.strip(),
                "industry": random.choice(INDUSTRIES),  # 실제 파싱 로직으로 대체 필요
                "size": "정보없음",
                "required_certs": [],
                "recommended_grade": 3.0,
                "ai_tip": "실시간 수집된 공고입니다. 상세 요건은 원문을 확인해줘.",
            })

        if not companies:
            raise ValueError("링커리어 파싱 결과 유효 데이터 없음")

        return companies, "live"

    except Exception:
        return BACKUP_COMPANIES, "backup"


# ============================================================
# 5. 매칭 알고리즘
# ============================================================
def convert_grade_to_score(grade: float) -> float:
    """
    마이스터고 5등급 성취평가제(1.0 ~ 5.0)를 100점 만점으로 선형 환산한다.
    1.0등급 = 100점, 5.0등급 = 0점 기준으로 균등 배분.
    """
    grade = max(GRADE_MIN, min(GRADE_MAX, grade))
    score = 100 - (grade - GRADE_MIN) * (100 / (GRADE_MAX - GRADE_MIN))
    return round(score, 1)


def calc_cert_bonus(user_certs, required_certs) -> float:
    """
    보유 자격증과 기업 요구 자격증의 일치 비율을 0~100점으로 환산한다.
    요구 자격증이 없는 기업은 만점(100점) 처리한다.
    """
    if not required_certs:
        return 100.0
    matched = [c for c in required_certs if c in user_certs]
    return round(len(matched) / len(required_certs) * 100, 1)


def calc_final_score(grade: float, user_certs, company: dict) -> dict:
    """
    [내신 환산 점수 50% + 자격증 가산점 50%]를 합산해
    100점 만점의 '취업 합격 지수'를 산출한다.
    """
    grade_score = convert_grade_to_score(grade)
    cert_score = calc_cert_bonus(user_certs, company["required_certs"])
    final_score = round(grade_score * 0.5 + cert_score * 0.5, 1)

    matched = [c for c in company["required_certs"] if c in user_certs]
    missing = [c for c in company["required_certs"] if c not in user_certs]

    return {
        "grade_score": grade_score,
        "cert_score": cert_score,
        "final_score": final_score,
        "matched": matched,
        "missing": missing,
    }


def generate_feedback(grade: float, company: dict, score_info: dict) -> str:
    """
    기업 카드마다 잘한 점 / 부족한 점을 1:1로 안내하는 AI 피드백 문장을 생성한다.
    """
    grade_ok = grade <= company["recommended_grade"]
    parts = []

    if grade_ok:
        parts.append(f"너의 성취도(내신 {grade:.1f}등급)는 이 기업의 권장 기준"
                      f"({company['recommended_grade']:.1f}등급)보다 우수해!")
    else:
        parts.append(f"이 기업의 권장 내신은 {company['recommended_grade']:.1f}등급이라 "
                      f"조금 더 끌어올리면 유리해.")

    if score_info["matched"]:
        parts.append(f"보유한 '{score_info['matched'][0]}'은(는) 이 기업이 선호하는 핵심 자격증이야.")

    if score_info["missing"]:
        parts.append(f"'{score_info['missing'][0]}'을 취득하면 합격 지수를 더 끌어올릴 수 있어.")
    else:
        parts.append("요구 자격증을 모두 갖췄어. 자신감을 가지고 지원해봐!")

    return " ".join(parts)


# ============================================================
# 6. UI 보조 컴포넌트
# ============================================================
def mascot_svg(mood="normal", size=64):
    """
    OGQ 캐릭터 대체용 원본 마스코트(기어 로봇) SVG.
    실제 배포 시 unnamed.jpg 등 팀에서 보유한 OGQ 라이선스 이미지로 교체 가능하도록
    st.image(...) 호출부를 별도로 분리해두었다. (main() 하단 참고)
    """
    eye_y = 27 if mood == "cheer" else 28
    if mood == "sad":
        eyes = f'<circle cx="25" cy="32" r="2.6" fill="{PAPER}"/><circle cx="39" cy="32" r="2.6" fill="{PAPER}"/>'
        mouth = f'<path d="M24 42 Q32 37 40 42" stroke="{PAPER}" stroke-width="2.2" fill="none" stroke-linecap="round"/>'
    else:
        eyes = f'<circle cx="25" cy="{eye_y}" r="2.8" fill="{PAPER}"/><circle cx="39" cy="{eye_y}" r="2.8" fill="{PAPER}"/>'
        mouth = f'<path d="M24 38 Q32 45 40 38" stroke="{PAPER}" stroke-width="2.4" fill="none" stroke-linecap="round"/>'

    teeth = "".join(
        f'<rect x="30" y="8" width="4" height="7" rx="1.5" fill="{AMBER}" transform="rotate({a} 32 34)"/>'
        for a in range(0, 360, 45)
    )

    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 64 64" fill="none">
        <circle cx="32" cy="34" r="22" fill="{PAPER}" stroke="{INK}" stroke-width="2.5"/>
        {teeth}
        <circle cx="32" cy="34" r="16" fill="{BLUE}"/>
        {eyes}
        {mouth}
        <rect x="12" y="32" width="6" height="4" rx="2" fill="{INK}"/>
        <rect x="46" y="32" width="6" height="4" rx="2" fill="{INK}"/>
    </svg>
    """


def render_mascot_bubble(text: str, mood="normal"):
    """상단 NPC(마스코트) 대사창을 렌더링한다."""
    col1, col2 = st.columns([1, 5])
    with col1:
        st.markdown(mascot_svg(mood=mood, size=60), unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="speech-bubble">{text}</div>', unsafe_allow_html=True)


def render_score_gauge(score: float):
    """0~100점 매칭 점수를 원형 프로그레스 형태로 표시한다 (matplotlib 없이 CSS conic-gradient 사용)."""
    color = GREEN if score >= 80 else (BRASS if score >= 55 else RED)
    deg = score / 100 * 360
    html = f"""
    <div style="
        width:84px; height:84px; border-radius:50%;
        background: conic-gradient({color} {deg}deg, {PAPER_DIM} {deg}deg);
        display:flex; align-items:center; justify-content:center;">
        <div style="width:66px; height:66px; border-radius:50%; background:{PAPER};
                    display:flex; flex-direction:column; align-items:center; justify-content:center;">
            <span class="score-num">{score:.0f}</span>
            <span class="score-label">MATCH</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


ROADMAP_STEPS = [
    ("cert", "자격증 취득", "🥇"),
    ("apply", "매칭기업 지원", "🚩"),
    ("interview", "면접 대비", "🏢"),
    ("offer", "합격 · 입사", "🚀"),
]


def render_roadmap(stage: int, animate: bool = False):
    """
    사다리 타기 형태의 커리어 로드맵을 렌더링한다.
    animate=True 이면 스탬프가 순차적으로 찍히는 연출을 보여준다.
    """
    placeholder = st.empty()

    def draw(current_stage):
        stamps_html = ""
        for i, (key, label, emoji) in enumerate(ROADMAP_STEPS):
            done = i <= current_stage
            cls = "stamp-done" if done else "stamp-pending"
            stamps_html += f"""
            <div style="display:flex; flex-direction:column; align-items:center; gap:6px; width:70px;">
                <div class="{cls}" style="width:40px; height:40px; border-radius:50%;
                            display:flex; align-items:center; justify-content:center; font-size:18px;
                            transition: background 0.4s;">
                    {emoji if done else "🔒"}
                </div>
                <span style="font-size:10px; color:{'#EDEBE2' if done else STEEL}; text-align:center;">{label}</span>
            </div>
            """
        progress_pct = (current_stage / (len(ROADMAP_STEPS) - 1)) * 100 if current_stage >= 0 else 0
        html = f"""
        <div class="roadmap-box">
            <div class="roadmap-title">🪜 CAREER ROADMAP (사다리 타기)</div>
            <div style="position:relative;">
                <div style="position:absolute; top:20px; left:0; right:0; height:3px;
                            background:rgba(255,255,255,0.15); border-radius:2px;"></div>
                <div style="position:absolute; top:20px; left:0; height:3px; width:{progress_pct}%;
                            background:{AMBER}; border-radius:2px; transition: width 0.6s ease;"></div>
                <div style="position:relative; display:flex; justify-content:space-between;">
                    {stamps_html}
                </div>
            </div>
        </div>
        """
        placeholder.markdown(html, unsafe_allow_html=True)

    if animate:
        # 단계별로 스탬프가 순차적으로 찍히는 애니메이션 연출
        for s in range(-1, stage + 1):
            draw(s)
            time.sleep(0.35)
    else:
        draw(stage)


# ============================================================
# 7. 메인 애플리케이션 로직
# ============================================================
def main():
    # ---- 세션 상태 초기화 ----
    if "screen" not in st.session_state:
        st.session_state.screen = "input"
    if "results" not in st.session_state:
        st.session_state.results = []

    st.markdown('<div class="eyebrow">🛠️ AI JOB PASS FINDER · 전북기계공고 E.M.P TEAM</div>', unsafe_allow_html=True)

    # ---- 실시간 데이터 로드 (자격증 / 기업) ----
    with st.spinner("최신 자격증 · 채용 데이터를 불러오는 중..."):
        certs_by_industry, certs_source = fetch_qnet_certs()
        companies, companies_source = fetch_linkareer_companies()

    # 데이터 출처 상태 표시 (투명성 확보)
    src_label = "🟢 실시간 수집 데이터" if companies_source == "live" else "🟡 백업 데이터(스크래핑 실패 시 자동 전환)"
    st.caption(f"{src_label} · 기준시각 {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    if st.session_state.screen == "input":
        render_input_screen(certs_by_industry, companies)
    else:
        render_result_screen()


def render_input_screen(certs_by_industry, companies):
    """입력 화면: 내신 등급 슬라이더 + 자격증 다중 선택 + 희망 직군 선택"""
    render_mascot_bubble("네 취업 스펙 수치를 입력해봐! 최신 공공 데이터로 딱 맞는 기업을 찾아줄게 🔧")

    # --- 01. 희망 직군 ---
    st.markdown('<div class="section-title"><span class="idx">01</span> 희망 직군</div>', unsafe_allow_html=True)
    industry = st.radio("희망 직군 선택", INDUSTRIES, horizontal=True, label_visibility="collapsed")

    # --- 02. 내신 등급 (5등급 성취평가제, 1.0~5.0) ---
    st.markdown('<div class="section-title"><span class="idx">02</span> 내신 등급 (마이스터고 5등급 성취평가제)</div>', unsafe_allow_html=True)
    grade = st.slider("내신 등급", min_value=1.0, max_value=5.0, value=2.5, step=0.1,
                       help="1.0등급이 최상위, 5.0등급이 최하위입니다.", label_visibility="collapsed")
    converted = convert_grade_to_score(grade)
    st.caption(f"환산 점수: **{converted}점** / 100점 (1.0등급=100점, 5.0등급=0점 기준 선형 환산)")

    # --- 03. 보유 자격증 (희망 직군 관련 목록만 노출) ---
    st.markdown('<div class="section-title"><span class="idx">03</span> 보유 자격증 (복수 선택)</div>', unsafe_allow_html=True)
    available_certs = certs_by_industry.get(industry, [])
    user_certs = st.multiselect("보유 자격증 선택", available_certs, label_visibility="collapsed")

    st.write("")
    if st.button("🚀 매칭 결과 분석하기", use_container_width=True, type="primary"):
        # --- 매칭 알고리즘 실행 ---
        target_companies = [c for c in companies if c.get("industry") == industry]
        scored = []
        for company in target_companies:
            score_info = calc_final_score(grade, user_certs, company)
            feedback = generate_feedback(grade, company, score_info)
            scored.append({"company": company, "score_info": score_info, "feedback": feedback})
        scored.sort(key=lambda x: x["score_info"]["final_score"], reverse=True)

        st.session_state.results = scored
        st.session_state.grade = grade
        st.session_state.industry = industry
        st.session_state.screen = "result"
        st.rerun()


def render_result_screen():
    """결과 화면: 매칭 카드 + AI 피드백 + 커리어 로드맵(사다리 타기)"""
    if st.button("← 다시 입력하기"):
        st.session_state.screen = "input"
        st.rerun()

    results = st.session_state.results
    top = results[:5]
    best_score = top[0]["score_info"]["final_score"] if top else 0

    # --- 점수대별 마스코트 리액션 ---
    if best_score >= 80:
        mood, msg = "cheer", f"대박! {st.session_state.industry} 직군에서 최고 {best_score:.0f}점 매칭을 찾았어. 지금 바로 지원해보자! 🎉"
    elif best_score >= 55:
        mood, msg = "normal", "괜찮은 매칭을 찾았어! 부족한 자격증 하나만 더 채우면 합격 지수가 확 올라갈 거야."
    else:
        mood, msg = "sad", "아직은 조금 부족하지만 걱정 마! 다음엔 이 자격증을 따보자, 분명 좋아질 거야 💪"
    render_mascot_bubble(msg, mood=mood)

    st.markdown(f'<div class="eyebrow">TOP {len(top)} MATCHES</div>', unsafe_allow_html=True)

    for i, item in enumerate(top):
        render_job_card(item, i)

    # --- 커리어 로드맵 (사다리 타기 + 스탬프 애니메이션) ---
    stage = 3 if best_score >= 80 else 2 if best_score >= 55 else 1 if best_score >= 35 else 0
    animate_key = "roadmap_animated"
    animate = animate_key not in st.session_state
    render_roadmap(stage, animate=animate)
    st.session_state[animate_key] = True


def render_job_card(item, index):
    """기업 매칭 카드 1건을 렌더링한다."""
    company = item["company"]
    score_info = item["score_info"]
    score = score_info["final_score"]

    tier = "STRONG MATCH" if score >= 80 else ("GOOD MATCH" if score >= 55 else "STRETCH GOAL")
    tier_color = GREEN if score >= 80 else (BRASS if score >= 55 else RED)

    cert_tags = ""
    for c in company["required_certs"]:
        matched = c in score_info["matched"]
        bg = GREEN if matched else PAPER_DIM
        color = "#fff" if matched else INK
        cert_tags += f'<span class="cert-tag" style="background:{bg}; color:{color};">{c}</span>'

    st.markdown(f"""
    <div class="job-card">
        <div class="job-card-top">
            <span style="font-family:'JetBrains Mono',monospace; color:{STEEL}; font-size:11px;">
                NO.{index+1:02d}
            </span>
            <span class="tier-badge" style="background:{tier_color};">{tier}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2.4])
    with col1:
        render_score_gauge(score)
    with col2:
        st.markdown(f"""
            <div class="job-name">{company['name']}</div>
            <div class="job-sub">{company['industry']} 직군 · {company['size']} · 권장 {company['recommended_grade']:.1f}등급</div>
            <div>{cert_tags}</div>
        """, unsafe_allow_html=True)

    st.markdown(f'<div class="feedback-box">✨ {item["feedback"]}</div>', unsafe_allow_html=True)
    st.write("")


# ============================================================
# 8. 엔트리포인트
# ============================================================
if __name__ == "__main__":
    main()
