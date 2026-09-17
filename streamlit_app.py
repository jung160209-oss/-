
import streamlit as st
import pandas as pd
from pathlib import Path
import re

st.set_page_config(
    page_title="군 소액구매 도우미",
    page_icon="🛠️",
    layout="centered",
)

BASE = Path(__file__).parent
DATA = BASE / "data"

@st.cache_data
def load_data():
    budgets = pd.read_csv(DATA / "budgets.csv")
    items = pd.read_csv(DATA / "items.csv")
    problems = pd.read_csv(DATA / "problem_map.csv")
    return budgets, items, problems

budgets, items, problems = load_data()

def norm(s):
    if pd.isna(s):
        return ""
    return re.sub(r"\s+", "", str(s).lower())

def token_score(query, text):
    q = norm(query)
    t = norm(text)
    if not q:
        return 0
    score = 0
    if q in t:
        score += 10
    # 짧은 한국어 자연어 입력에서도 어느 정도 매칭되도록 키워드 조각 비교
    raw_tokens = re.split(r"[\s,./()\-]+", str(query).lower())
    for tok in raw_tokens:
        tok = tok.strip()
        if len(tok) >= 2 and norm(tok) in t:
            score += 2
    return score

def budget_matches(query):
    rows = []
    for _, r in budgets.iterrows():
        text = " ".join([
            str(r["예산명"]), str(r["용도설명"]),
            str(r["관련업무"]), str(r["검색키워드"])
        ])
        s = token_score(query, text)
        if s > 0:
            rows.append((s, r))
    rows.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in rows]

def problem_matches(query):
    rows = []
    for _, r in problems.iterrows():
        text = " ".join([
            str(r["사용자표현"]), str(r["문제키워드"]),
            str(r["증상설명"]), str(r["추천품목"])
        ])
        s = token_score(query, text)
        # 문제 키워드를 쉼표 단위로 추가 가중치
        for kw in str(r["문제키워드"]).split(","):
            kw = norm(kw)
            if kw and kw in norm(query):
                s += 5
        if s > 0:
            rows.append((s, r))
    rows.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in rows]

def money(v):
    return f"{int(v):,}원"

def get_items_for_budget(budget_id):
    return items[items["예산ID"] == budget_id].copy()

st.markdown("""
<style>
.block-container {max-width: 920px; padding-top: 2.2rem; padding-bottom: 4rem;}
.hero {
    padding: 26px 26px 22px 26px;
    border: 1px solid rgba(120,120,120,.22);
    border-radius: 22px;
    margin-bottom: 18px;
    background: rgba(120,120,120,.045);
}
.hero h1 {font-size: 2.0rem; margin: 0 0 8px 0;}
.hero p {font-size: 1.04rem; line-height: 1.65; margin: 0;}
.small-note {font-size: .88rem; opacity: .76;}
.result-card {
    border: 1px solid rgba(120,120,120,.24);
    border-radius: 18px;
    padding: 18px;
    margin: 10px 0 16px 0;
}
.badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    border: 1px solid rgba(120,120,120,.28);
    margin-right: 5px;
    font-size: .82rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>🛠️ 군 소액구매 도우미</h1>
  <p><b>예산에서 시작하는 구매</b><br>
  예산명을 검색하면 용도를 이해하고, 필요한 품목을 추천받아 구매계획까지 한 번에 도와드립니다.</p>
</div>
""", unsafe_allow_html=True)

st.warning(
    "프로토타입 테스트용 예시 데이터입니다. 실제 집행 가능 여부는 적용 지침·회계 기준·담당자 확인이 필요합니다. "
    "부대명, 세부 위치, 장비 보유현황, 비공개 문서 등 군사보안 정보는 입력하지 마세요.",
    icon="⚠️",
)

tab1, tab2, tab3 = st.tabs(["🔎 예산으로 찾기", "💬 문제로 찾기", "📊 구매계획"])

with tab1:
    st.subheader("어떤 예산을 사용하시나요?")
    q = st.text_input(
        "예산명 또는 키워드",
        placeholder="예: 장비정비, 사무용품, 전산, 시설...",
        key="budget_q"
    )

    if q:
        matches = budget_matches(q)
        if not matches:
            st.info("현재 예시 데이터에서 일치하는 예산을 찾지 못했습니다.")
        else:
            for r in matches[:4]:
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown(f"### {r['예산명']}")
                st.caption(f"예산코드(예시): {r['예산코드']}")
                st.write(r["용도설명"])
                st.markdown(f"**관련 업무**  \n{r['관련업무']}")
                st.markdown(f"**주의사항**  \n{r['주의사항']}")

                rec = get_items_for_budget(r["예산ID"])
                if len(rec):
                    show = rec[["품목명", "용도", "최저가", "최고가"]].copy()
                    show["예상 가격대"] = show.apply(
                        lambda x: f"{int(x['최저가']):,} ~ {int(x['최고가']):,}원", axis=1
                    )
                    st.markdown("**추천 품목 예시**")
                    st.dataframe(
                        show[["품목명", "용도", "예상 가격대"]],
                        hide_index=True,
                        use_container_width=True,
                    )
                st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.caption("예산명을 정확히 몰라도 업무 키워드로 검색해보세요.")
        cols = st.columns(2)
        examples = ["장비정비", "사무용품", "전산", "시설"]
        for i, e in enumerate(examples):
            with cols[i % 2]:
                st.code(e, language=None)

with tab2:
    st.subheader("필요한 물건 이름을 모르셔도 됩니다")
    st.write("지금 겪고 있는 문제나 하려는 작업을 평소 말하듯 적어보세요.")
    pq = st.text_area(
        "상황 설명",
        placeholder="예: 에어호스를 연결하려는데 어떤 부속을 사야 할지 모르겠어요",
        height=120,
        key="problem_q",
    )

    if pq:
        pm = problem_matches(pq)
        if not pm:
            st.info("현재 예시 데이터에서 비슷한 사례를 찾지 못했습니다. 테스트 데이터가 늘어나면 이 영역이 가장 좋아집니다.")
        else:
            top = pm[0]
            st.success("비슷한 업무 사례를 찾았습니다.")
            st.markdown(f"### 🔧 {top['증상설명']}")
            st.markdown(f"**추천 품목:** {top['추천품목']}")
            st.markdown(f"**확인할 점:** {top['확인사항']}")

            bid = top["관련예산ID"]
            b = budgets[budgets["예산ID"] == bid]
            if len(b):
                br = b.iloc[0]
                st.markdown(f"**연결 가능한 예산 분류 예시:** `{br['예산명']}`")
                st.caption("실제 집행 가능 여부를 확정하는 기능이 아니라, 확인해야 할 예산 후보를 좁혀주는 기능입니다.")

            if len(pm) > 1:
                with st.expander("다른 가능성도 보기"):
                    for alt in pm[1:4]:
                        st.markdown(f"- **{alt['증상설명']}** → {alt['추천품목']}")

with tab3:
    st.subheader("구매계획 초안 만들기")

    budget_names = budgets["예산명"].tolist()
    selected_budget = st.selectbox("예산 분류", budget_names)
    budget_row = budgets[budgets["예산명"] == selected_budget].iloc[0]
    budget_id = budget_row["예산ID"]

    amount = st.number_input(
        "가용 예산",
        min_value=10000,
        max_value=100000000,
        value=1000000,
        step=10000,
        format="%d"
    )

    candidates = get_items_for_budget(budget_id)
    if len(candidates) == 0:
        st.info("이 예산에 연결된 예시 품목이 없습니다.")
    else:
        selected_names = st.multiselect(
            "구매를 검토할 품목",
            candidates["품목명"].tolist(),
            default=candidates["품목명"].tolist()[:3]
        )

        plan = candidates[candidates["품목명"].isin(selected_names)].copy()
        if len(plan):
            plan["기준단가"] = ((plan["최저가"] + plan["최고가"]) / 2).astype(int)
            plan["수량"] = 1

            editor = st.data_editor(
                plan[["품목명", "용도", "기준단가", "수량"]],
                hide_index=True,
                use_container_width=True,
                disabled=["품목명", "용도", "기준단가"],
                column_config={
                    "기준단가": st.column_config.NumberColumn("예상 단가", format="%d원"),
                    "수량": st.column_config.NumberColumn("수량", min_value=1, max_value=100, step=1),
                },
                key="plan_editor",
            )

            editor["소계"] = editor["기준단가"] * editor["수량"]
            total = int(editor["소계"].sum())
            remain = int(amount - total)

            st.markdown("### 구매계획(안)")
            result = editor[["품목명", "수량", "기준단가", "소계"]].copy()
            st.dataframe(
                result,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "기준단가": st.column_config.NumberColumn("예상 단가", format="%d원"),
                    "소계": st.column_config.NumberColumn("소계", format="%d원"),
                }
            )

            c1, c2 = st.columns(2)
            c1.metric("계획 합계", money(total))
            c2.metric("잔여 예산", money(remain))

            if remain < 0:
                st.error(f"가용 예산을 {money(abs(remain))} 초과했습니다. 수량이나 품목을 조정해주세요.")
            else:
                st.success("가용 예산 범위 안에서 구매계획 초안이 만들어졌습니다.")

            st.caption(
                "가격은 프로토타입용 예시 범위의 중간값을 사용합니다. "
                "실제 서비스에서는 공급업체 견적·공개 가격정보를 연결할 수 있습니다."
            )

st.divider()
st.caption("군 소액구매 도우미 · 사용성 검증용 Prototype v0.1")
