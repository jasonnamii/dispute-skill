#!/usr/bin/env python3
"""
dispute-intake-scanner — 소장·내용증명·가압류 수령 시 1차 자동 점검.
입력: 분쟁 문서 텍스트(파일 또는 stdin). 출력: 긴급 체크 + 유형 추정 + 다음 액션.
사용: python3 dispute-intake-scanner.py < 소장.txt
"""
import sys, re, datetime

TYPE_KEYWORDS = {
    "T1 계약불이행·손배": ["채무불이행","손해배상","하자","납품","이행지체","이행불능"],
    "T2 금전·채권추심": ["대여금","물품대금","미수금","약정금","구상금","양수금"],
    "T3 주주·지배구조": ["주주","의결권","이사","주주총회","경영권","진술보장","대표소송"],
    "T4 IP·영업비밀": ["특허","영업비밀","부정경쟁","전직금지","침해금지","직무발명","상표"],
    "T5 부동산·건설": ["공사대금","기성고","임대차","명도","인도","권리금","매매대금"],
    "T6 형사": ["고소","고발","피의자","사기","배임","횡령","수사","검찰","경찰"],
    "T7 국제·중재": ["중재","arbitration","ICC","SIAC","KCAB","외국","준거법"],
    "T8 행정·규제": ["공정위","과징금","시정명령","처분","인허가","행정"],
}
URGENT = {
    "가압류·가처분(보전처분)": ["가압류","가처분","보전처분"],
    "기일 지정(응소기한)": ["변론기일","답변서","30일","제출기한","송달"],
    "형사 소환·기한": ["출석","소환","피의자신문"],
    "항소·상고 기한(2주)": ["판결","선고","항소","상고"],
}

def scan(text):
    out = []
    out.append("="*52)
    out.append(f"📥 분쟁 문서 1차 스캔  ({datetime.date.today()})")
    out.append("="*52)

    # 1. 긴급도
    out.append("\n🚨 [긴급 체크 — 기한 놓치면 회복불능]")
    hit_urgent = False
    for label, kws in URGENT.items():
        if any(k in text for k in kws):
            out.append(f"  🔴 {label} — 즉시 기한 확인·대응")
            hit_urgent = True
    if not hit_urgent:
        out.append("  🟡 명시적 긴급 신호 미탐지 — 그래도 응소기한·시효 수동 확인")

    # 2. 유형 추정
    out.append("\n🗂  [분쟁 유형 추정]")
    scores = {t: sum(1 for k in kws if k in text) for t,kws in TYPE_KEYWORDS.items()}
    ranked = sorted([(t,s) for t,s in scores.items() if s>0], key=lambda x:-x[1])
    if ranked:
        for t,s in ranked[:3]:
            out.append(f"  • {t}  (신호 {s}개)")
    else:
        out.append("  • 유형 미상 — 사실관계 직접 확인 필요")

    # 3. 시효·금액 신호
    out.append("\n⏳ [시효·금액 신호]")
    amounts = re.findall(r'[0-9][0-9,]*\s*(?:원|만원|억)', text)
    if amounts:
        out.append(f"  • 금액 언급: {', '.join(amounts[:5])} → 인지대·소액심판(3천↓)·집행가능성 검토")
    dates = re.findall(r'20\d{2}[.\-년/]\s*\d{1,2}', text)
    if dates:
        out.append(f"  • 날짜 언급: {', '.join(dates[:5])} → 시효 기산점 확인(물품대금3년·상사5년·일반10년)")
    if not amounts and not dates:
        out.append("  • 금액·날짜 명시 부족 — 시효·소가 직접 산정")

    # 4. 다음 액션
    out.append("\n➡️  [다음 액션 — 우선순위]")
    out.append("  1) 시효·응소기한·항소기한 달력에 즉시 표기 (도과=권리소멸)")
    out.append("  2) 증거 인벤토리: 형 보유 vs 상대 보유 vs 제3자 (→ L3·Ω2)")
    out.append("  3) 집행가능성 선조사: 상대 재산 有無 (→ L5)")
    out.append("  4) 입장·관할·준거법 확정 후 5층 분석 진입")
    out.append("  5) 상대가 대형로펌이면 → M4 카운터 모드")
    out.append("\n⚠️ 자동 스캔은 1차 스크린. 변호사 선임·정밀 검토 필수.")
    return "\n".join(out)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        text = open(sys.argv[1], encoding="utf-8", errors="ignore").read()
    else:
        text = sys.stdin.read()
    print(scan(text))
