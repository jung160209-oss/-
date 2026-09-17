
import streamlit as st
import pandas as pd
from pathlib import Path
import re
import streamlit.components.v1 as components

st.set_page_config(
    page_title="군 소액구매 도우미",
    page_icon="🛠️",
    layout="centered",
)

components.html(
    """
    <script>
    try {
      const doc = window.parent.document;
      doc.documentElement.setAttribute("lang", "ko");
      doc.documentElement.setAttribute("translate", "no");
      let meta = doc.querySelector('meta[name="google"]');
      if (!meta) {
        meta = doc.createElement("meta");
        meta.setAttribute("name", "google");
        doc.head.appendChild(meta);
      }
      meta.setAttribute("content", "notranslate");
    } catch (e) {}
    </script>
    """,
    height=0,
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
    for tok in re.split(r"[\s,./()\-]+", str(query).lower()):
        tok = tok.strip()
        if len(tok) >= 2 and norm(tok) in t:
            score += 2
    return score

def budget_matches(query):
    rows = []
    for _, r in budgets.iterrows():
        text = " ".join([
            str(r["예산명"]),
            str(r["용도설명"]),
            str(r["관련업무"]),
            str(r["검색키워드"]),
        ])
        score = token_score(query, text)
        if score > 0:
            rows.append((score, r))
    rows.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in rows]

def problem_matches(query):
    rows = []
    for _, r in problems.iterrows():
        text = " ".join([
            str(r["사용자표현"]),
            str(r["문제키워드"]),
            str(r["증상설명"]),
            str(r["추천품목"]),
        ])
        score = token_score(query, text)
        for kw in str(r["문제키워드"]).split(","):
            kw = norm(kw)
            if kw and kw in norm(query):
                score += 5
        if score > 0:
            rows.append((score, r))
    rows.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in rows]

def item_matches(query):
    rows = []
    for _, r in items.iterrows():
        text = " ".join([
            str(r["품목명"]),
            str(r["용도"]),
        ])
        score = token_score(query, text)
        if score > 0:
            rows.append((score, r))
    rows.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in rows]

def get_budget(budget_id):
    row = budgets[budgets["예산ID"] == budget_id]
    return None if row.empty else row.iloc[0]

def get_items(budget_id):
    return items[items["예산ID"] == budget_id].copy()

def won(v):
    return f"{int(v):,}원"

def reset_flow():
    for k in [
        "step", "mode", "budget_id", "budget_amount",
        "problem_text", "problem_result_id",
        "item_query", "selected_item_names",
        "budget_query"
    ]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()

defaults = {
    "step": 1,
    "mode": None,
    "budget_id": None,
    "budget_amount": 1_000_000,
    "problem_text": "",
    "problem_result_id": None,
    "item_query": "",
    "budget_query": "",
    "selected_item_names": [],
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

st.markdown("""
<style>
.block-container {
    max-width: 920px;
    padding-top: 2rem;
    padding-bottom: 5rem;
}
.hero {
    padding: 26px 26px 22px 26px;
    border: 1px solid rgba(120,120,120,.22);
    border-radius: 22px;
    margin-bottom: 16px;
    background: rgba(120,120,120,.045);
}
.hero h1 {font-size: 2rem; margin: 0 0 8px 0;}
.hero p {font-size: 1.03rem; line-height: 1.65; margin: 0;}
.stepbar {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 8px;
    margin: 20px 0 24px 0;
}
.step {
    border: 1px solid rgba(120,120,120,.25);
    border-radius: 14px;
    padding: 10px 5px;
    text-align: center;
    font-size: .82rem;
    opacity: .55;
}
.step.active {
    opacity: 1;
    font-weight: 750;
    border-width: 2px;
}
.info-card {
    border: 1px solid rgba(120,120,120,.22);
    border-radius: 18px;
    padding: 18px 18px 12px 18px;
    margin: 12px 0 18px 0;
}
.mode-card {
    border: 1px solid rgba(120,120,120,.22);
    border-radius: 18px;
    padding: 18px;
    min-height: 180px;
}
div[data-testid="stButton"] > button {
    min-height: 48px;
    border-radius: 12px;
    font-weight: 650;
}
@media (max-width: 650px) {
  .stepbar { gap: 4px; }
  .step { font-size: .72rem; padding: 9px 2px; }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero notranslate" translate="no">
  <h1>🛠️ 군 소액구매 도우미</h1>
  <p><b>예산에서 시작하는 구매</b><br>
  예산·문제·품목 중 편한 방식으로 시작하고, 필요한 품목을 골라 구매계획 초안까지 만들어보세요.</p>
</div>
""", unsafe_allow_html=True)

st.warning(
    "프로토타입 테스트용 예시 데이터입니다. 실제 집행 가능 여부는 적용 지침·회계 기준·담당자 확인이 필요합니다. "
    "부대명, 세부 위치, 장비 보유현황, 비공개 문서 등 군사보안 정보는 입력하지 마세요.",
    icon="⚠️",
)

step = st.session_state.step
labels = ["1. 시작", "2. 가용예산", "3. 검색", "4. 추천품목", "5. 구매계획"]
html = '<div class="stepbar notranslate" translate="no">'
for i, label in enumerate(labels, start=1):
    active = " active" if i == step else ""
    html += f'<div class="step{active}">{label}</div>'
html += "</div>"
st.markdown(html, unsafe_allow_html=True)

# 1단계: 시작 방식
if step == 1:
    st.subheader("어떤 방식으로 시작할까요?")
    st.write("현재 알고 있는 정보에 맞춰 하나를 선택하세요.")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("#### 💰 예산으로 시작")
        st.caption("사용할 예산을 알고 있을 때")
        st.write("예산명 또는 예산의 업무 용도를 기준으로 품목을 찾습니다.")
        if st.button("예산으로 시작", use_container_width=True, type="primary"):
            st.session_state.mode = "budget"
            st.session_state.step = 2
            st.rerun()

    with c2:
        st.markdown("#### 💬 문제로 시작")
        st.caption("뭘 사야 할지 모를 때")
        st.write("“에어호스를 연결하고 싶어요”처럼 상황을 설명합니다.")
        if st.button("문제로 시작", use_container_width=True):
            st.session_state.mode = "problem"
            st.session_state.step = 2
            st.rerun()

    with c3:
        st.markdown("#### 📦 품목으로 시작")
        st.caption("필요한 품목명을 알고 있을 때")
        st.write("에어호스, 피팅, 토너처럼 품목명을 직접 검색합니다.")
        if st.button("품목으로 시작", use_container_width=True):
            st.session_state.mode = "item"
            st.session_state.step = 2
            st.rerun()

# 2단계: 가용예산
elif step == 2:
    st.subheader("사용할 수 있는 예산 금액을 입력하세요")
    st.write("먼저 전체 가용예산을 정하면 뒤 단계에서 품목과 수량을 맞추기 쉬워집니다.")

    amount = st.number_input(
        "가용예산",
        min_value=10_000,
        max_value=100_000_000,
        value=int(st.session_state.budget_amount),
        step=10_000,
        format="%d",
    )
    st.session_state.budget_amount = int(amount)

    st.info(f"현재 가용예산: **{won(amount)}**")

    b1, b2 = st.columns(2)
    with b1:
        if st.button("← 이전", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with b2:
        if st.button("검색 단계로 →", use_container_width=True, type="primary"):
            st.session_state.step = 3
            st.rerun()

# 3단계: 모드별 검색
elif step == 3:
    mode = st.session_state.mode

    # 예산으로 시작
    if mode == "budget":
        st.subheader("사용할 예산을 찾아보세요")
        st.write("예산명을 검색하거나, 아래 목록에서 직접 선택할 수 있습니다.")

        budget_query = st.text_input(
            "예산 검색",
            value=st.session_state.budget_query,
            placeholder="예: 장비정비, 전산, 사무용품, 시설",
        )
        st.session_state.budget_query = budget_query

        matches = budget_matches(budget_query) if budget_query.strip() else []

        if matches:
            st.markdown("**검색 결과**")
            result_names = [r["예산명"] for r in matches[:6]]
            selected_name = st.selectbox("검색 결과에서 선택", result_names, key="budget_search_select")
        else:
            selected_name = st.selectbox(
                "또는 전체 예산 목록에서 선택",
                budgets["예산명"].tolist(),
            )

        br = budgets[budgets["예산명"] == selected_name].iloc[0]
        st.session_state.budget_id = br["예산ID"]

        st.markdown('<div class="info-card notranslate" translate="no">', unsafe_allow_html=True)
        st.markdown(f"### {br['예산명']}")
        st.write(br["용도설명"])
        st.markdown(f"**관련 업무**  \n{br['관련업무']}")
        st.markdown(f"**확인할 점**  \n{br['주의사항']}")
        st.markdown("</div>", unsafe_allow_html=True)

        can_next = True

    # 문제로 시작
    elif mode == "problem":
        st.subheader("어떤 문제가 있나요?")
        st.write("품목명을 몰라도 괜찮습니다. 하려는 일이나 현재 문제를 자연스럽게 적어주세요.")

        problem_text = st.text_area(
            "상황 설명",
            value=st.session_state.problem_text,
            placeholder="예: 에어호스를 연결하려는데 어떤 부속을 사야 할지 모르겠어요",
            height=120,
        )
        st.session_state.problem_text = problem_text

        matches = problem_matches(problem_text) if problem_text.strip() else []

        if matches:
            top = matches[0]
            st.session_state.problem_result_id = top["문제ID"]
            st.session_state.budget_id = top["관련예산ID"]

            st.markdown('<div class="info-card notranslate" translate="no">', unsafe_allow_html=True)
            st.markdown("### 🔧 비슷한 사례를 찾았습니다")
            st.markdown(f"**상황 해석:** {top['증상설명']}")
            st.markdown(f"**추천 품목:** {top['추천품목']}")
            st.markdown(f"**먼저 확인할 점:** {top['확인사항']}")
            br = get_budget(top["관련예산ID"])
            if br is not None:
                st.markdown(f"**연결할 예산 후보:** {br['예산명']}")
            st.markdown("</div>", unsafe_allow_html=True)

            can_next = True
        else:
            if problem_text.strip():
                st.info("현재 예시 데이터에서 비슷한 사례를 찾지 못했습니다. 다른 표현으로 적어보세요.")
            can_next = False

    # 품목으로 시작
    else:
        st.subheader("필요한 품목을 검색하세요")
        st.write("품목명을 알고 있다면 바로 검색해서 관련 예산과 비슷한 품목을 확인할 수 있습니다.")

        item_query = st.text_input(
            "품목 검색",
            value=st.session_state.item_query,
            placeholder="예: 에어호스, 피팅, 토너, 실리콘",
        )
        st.session_state.item_query = item_query

        imatches = item_matches(item_query) if item_query.strip() else []

        if imatches:
            st.markdown("**검색 결과**")
            item_names = []
            for r in imatches[:8]:
                item_names.append(r["품목명"])

            selected_item = st.selectbox("품목 선택", item_names)

            row = items[items["품목명"] == selected_item].iloc[0]
            st.session_state.budget_id = row["예산ID"]
            st.session_state.selected_item_names = [selected_item]
            br = get_budget(row["예산ID"])

            st.markdown('<div class="info-card notranslate" translate="no">', unsafe_allow_html=True)
            st.markdown(f"### 📦 {row['품목명']}")
            st.markdown(f"**용도:** {row['용도']}")
            st.markdown(f"**예상 가격대:** {won(row['최저가'])} ~ {won(row['최고가'])}")
            if br is not None:
                st.markdown(f"**연결 가능한 예산 후보:** {br['예산명']}")
            st.markdown("</div>", unsafe_allow_html=True)

            can_next = True
        else:
            if item_query.strip():
                st.info("현재 예시 데이터에서 일치하는 품목을 찾지 못했습니다.")
            can_next = False

    b1, b2 = st.columns(2)
    with b1:
        if st.button("← 이전", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with b2:
        if st.button(
            "추천 품목 보기 →",
            use_container_width=True,
            type="primary",
            disabled=not can_next,
        ):
            st.session_state.step = 4
            st.rerun()

# 4단계: 추천 품목
elif step == 4:
    br = get_budget(st.session_state.budget_id)
    if br is None:
        st.error("연결된 예산 정보가 없습니다.")
        if st.button("처음으로"):
            reset_flow()
    else:
        st.subheader("추천 품목을 선택하세요")
        st.caption(f"가용예산: {won(st.session_state.budget_amount)} · 연결 예산: {br['예산명']}")

        candidate = get_items(br["예산ID"])

        if candidate.empty:
            st.info("현재 이 예산에 연결된 예시 품목이 없습니다.")
        else:
            st.markdown("#### 추천 품목")
            for _, r in candidate.iterrows():
                st.markdown(
                    f"**{r['품목명']}**  \n"
                    f"{r['용도']} · 예상 {won(r['최저가'])} ~ {won(r['최고가'])}"
                )

            default = st.session_state.selected_item_names
            if not default:
                default = candidate["품목명"].tolist()[:3]

            selected = st.multiselect(
                "구매를 검토할 품목",
                candidate["품목명"].tolist(),
                default=[x for x in default if x in candidate["품목명"].tolist()],
                placeholder="품목을 하나 이상 선택하세요",
            )
            st.session_state.selected_item_names = selected

        b1, b2 = st.columns(2)
        with b1:
            if st.button("← 이전", use_container_width=True):
                st.session_state.step = 3
                st.rerun()
        with b2:
            if st.button(
                "구매계획 만들기 →",
                use_container_width=True,
                type="primary",
                disabled=len(st.session_state.selected_item_names) == 0,
            ):
                st.session_state.step = 5
                st.rerun()

# 5단계: 구매계획
elif step == 5:
    br = get_budget(st.session_state.budget_id)
    st.subheader("구매계획 초안을 확인하세요")

    if br is not None:
        st.caption(
            f"가용예산: {won(st.session_state.budget_amount)} · "
            f"연결 예산: {br['예산명']}"
        )

    candidate = get_items(st.session_state.budget_id)
    plan = candidate[candidate["품목명"].isin(st.session_state.selected_item_names)].copy()

    if plan.empty:
        st.info("선택된 품목이 없습니다.")
    else:
        plan["예상단가"] = ((plan["최저가"] + plan["최고가"]) / 2).astype(int)
        plan["수량"] = 1

        edited = st.data_editor(
            plan[["품목명", "용도", "예상단가", "수량"]],
            hide_index=True,
            use_container_width=True,
            disabled=["품목명", "용도", "예상단가"],
            column_config={
                "예상단가": st.column_config.NumberColumn("예상 단가", format="%d원"),
                "수량": st.column_config.NumberColumn("수량", min_value=1, max_value=999, step=1),
            },
        )

        edited["소계"] = edited["예상단가"] * edited["수량"]
        total = int(edited["소계"].sum())
        remain = int(st.session_state.budget_amount - total)

        st.markdown("### 구매계획(안)")
        result = edited[["품목명", "수량", "예상단가", "소계"]].copy()

        st.dataframe(
            result,
            hide_index=True,
            use_container_width=True,
            column_config={
                "예상단가": st.column_config.NumberColumn("예상 단가", format="%d원"),
                "소계": st.column_config.NumberColumn("소계", format="%d원"),
            },
        )

        c1, c2 = st.columns(2)
        c1.metric("계획 합계", won(total))
        c2.metric("잔여 예산", won(remain))

        if remain < 0:
            st.error(f"가용예산을 {won(abs(remain))} 초과했습니다. 수량이나 품목을 조정해주세요.")
        else:
            st.success("가용예산 범위 안에서 구매계획 초안이 만들어졌습니다.")

        csv_bytes = result.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "구매계획 CSV 내려받기",
            data=csv_bytes,
            file_name="구매계획_초안.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.caption(
        "예상 가격은 프로토타입용 예시 범위를 기준으로 계산합니다. "
        "실제 서비스에서는 공개 가격정보와 공급업체 견적을 연결할 수 있습니다."
    )

    b1, b2 = st.columns(2)
    with b1:
        if st.button("← 추천 품목 다시 선택", use_container_width=True):
            st.session_state.step = 4
            st.rerun()
    with b2:
        if st.button("처음부터 다시", use_container_width=True):
            reset_flow()

st.divider()
st.caption("군 소액구매 도우미 · 사용성 검증용 Prototype v0.3")
