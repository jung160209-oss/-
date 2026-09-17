
import streamlit as st
import pandas as pd
from pathlib import Path
import re
import streamlit.components.v1 as components

st.set_page_config(
    page_title="군 소액구매 도우미",
    page_icon="🛠️",
    layout="wide",
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
        text = f"{r['품목명']} {r['용도']}"
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
    st.session_state.clear()
    st.rerun()

defaults = {
    "step": 1,
    "mode": None,
    "budget_amount": 1_000_000,
    "budget_id": None,
    "problem_text": "",
    "budget_query": "",
    "item_query": "",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

st.markdown("""
<style>
.block-container {
    max-width: 1240px;
    padding-top: 1.6rem;
    padding-bottom: 4rem;
}
.hero {
    padding: 24px 26px 20px 26px;
    border: 1px solid rgba(120,120,120,.22);
    border-radius: 22px;
    margin-bottom: 14px;
    background: rgba(120,120,120,.045);
}
.hero h1 {font-size: 2rem; margin: 0 0 8px 0;}
.hero p {font-size: 1.02rem; line-height: 1.6; margin: 0;}
.stepbar {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    margin: 18px 0 22px 0;
}
.step {
    border: 1px solid rgba(120,120,120,.25);
    border-radius: 14px;
    padding: 10px 7px;
    text-align: center;
    font-size: .88rem;
    opacity: .55;
}
.step.active {
    opacity: 1;
    font-weight: 750;
    border-width: 2px;
}
div[data-testid="stButton"] > button {
    min-height: 46px;
    border-radius: 12px;
    font-weight: 650;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero notranslate" translate="no">
  <h1>🛠️ 군 소액구매 도우미</h1>
  <p><b>예산에서 시작하는 구매</b><br>
  무엇을 사야 할지 몰라도 괜찮습니다. 예산명·문제·품목 중 알고 있는 정보에서 시작해 구매계획까지 한 번에 만들어보세요.</p>
</div>
""", unsafe_allow_html=True)

st.warning(
    "프로토타입 테스트용 예시 데이터입니다. 실제 집행 가능 여부는 적용 지침·회계 기준·담당자 확인이 필요합니다. "
    "부대명, 세부 위치, 장비 보유현황, 비공개 문서 등 군사보안 정보는 입력하지 마세요.",
    icon="⚠️",
)

step = st.session_state.step
labels = ["1. 시작하기", "2. 구매계획 만들기"]
html = '<div class="stepbar notranslate" translate="no">'
for i, label in enumerate(labels, start=1):
    active = " active" if i == step else ""
    html += f'<div class="step{active}">{label}</div>'
html += "</div>"
st.markdown(html, unsafe_allow_html=True)

# 1단계
if step == 1:
    st.subheader("어떤 방식으로 시작할까요?")
    st.write("현재 알고 있는 정보에 맞춰 하나를 선택하세요.")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### 💰 예산명으로 시작")
        st.caption("사용할 예산명을 알고 있을 때")
        st.write("예산명 또는 관련 업무를 기준으로 추천 품목을 찾습니다.")
        if st.button("예산명으로 시작", use_container_width=True, type="primary"):
            st.session_state.mode = "budget"
            st.session_state.step = 2
            st.rerun()

    with c2:
        st.markdown("### 💬 문제로 시작")
        st.caption("무엇을 사야 할지 모를 때")
        st.write("“에어호스를 연결하고 싶어요”처럼 현재 상황을 설명합니다.")
        if st.button("문제로 시작", use_container_width=True):
            st.session_state.mode = "problem"
            st.session_state.step = 2
            st.rerun()

    with c3:
        st.markdown("### 📦 품목으로 시작")
        st.caption("필요한 품목명을 알고 있을 때")
        st.write("에어호스, 피팅, 토너처럼 품목명을 직접 검색합니다.")
        if st.button("품목으로 시작", use_container_width=True):
            st.session_state.mode = "item"
            st.session_state.step = 2
            st.rerun()

# 2단계
elif step == 2:
    mode = st.session_state.mode

    # 상단 예산 현황
    st.markdown("## 구매계획")
    budget_cols = st.columns([1.2, 1, 1])

    with budget_cols[0]:
        amount = st.number_input(
            "가용예산",
            min_value=10_000,
            max_value=100_000_000,
            value=int(st.session_state.budget_amount),
            step=10_000,
            format="%d",
            help="언제든 수정할 수 있습니다.",
        )
        st.session_state.budget_amount = int(amount)

    plan_total_box = budget_cols[1].empty()
    remain_box = budget_cols[2].empty()

    st.caption("가용예산은 이 화면에서 언제든 수정할 수 있으며 품목·수량·단가 변경 즉시 잔여예산이 다시 계산됩니다.")
    st.divider()

    left, right = st.columns([1.0, 1.65], gap="large")

    # 왼쪽 검색
    with left:
        st.markdown("## ① 검색")

        candidate = pd.DataFrame()

        if mode == "budget":
            st.markdown("### 💰 예산명으로 찾기")
            q = st.text_input(
                "예산명 또는 관련 업무",
                value=st.session_state.budget_query,
                placeholder="예: 장비정비, 전산, 사무용품",
            )
            st.session_state.budget_query = q

            matches = budget_matches(q) if q.strip() else []
            if matches:
                names = [r["예산명"] for r in matches[:6]]
                selected_name = st.selectbox("검색 결과", names)
            else:
                selected_name = st.selectbox(
                    "예산명 목록에서 선택",
                    budgets["예산명"].tolist()
                )

            br = budgets[budgets["예산명"] == selected_name].iloc[0]
            st.session_state.budget_id = br["예산ID"]
            candidate = get_items(br["예산ID"])

            st.info(
                f"**{br['예산명']}**\n\n"
                f"{br['용도설명']}\n\n"
                f"관련 업무: {br['관련업무']}\n\n"
                f"확인할 점: {br['주의사항']}"
            )

        elif mode == "problem":
            st.markdown("### 💬 문제로 찾기")
            p = st.text_area(
                "상황 설명",
                value=st.session_state.problem_text,
                placeholder="예: 에어호스를 연결하려는데 어떤 부속을 사야 할지 모르겠어요",
                height=120,
            )
            st.session_state.problem_text = p

            matches = problem_matches(p) if p.strip() else []

            if matches:
                top = matches[0]
                st.session_state.budget_id = top["관련예산ID"]
                br = get_budget(top["관련예산ID"])
                candidate = get_items(top["관련예산ID"])

                st.success(f"**상황 해석**\n\n{top['증상설명']}")
                st.write(f"추천 방향: {top['추천품목']}")
                st.write(f"먼저 확인할 점: {top['확인사항']}")
                if br is not None:
                    st.caption(f"연결 예산 후보: {br['예산명']}")
            elif p.strip():
                st.info("현재 예시 데이터에서 비슷한 사례를 찾지 못했습니다.")

        else:
            st.markdown("### 📦 품목으로 찾기")
            q = st.text_input(
                "품목명 검색",
                value=st.session_state.item_query,
                placeholder="예: 에어호스, 피팅, 토너",
            )
            st.session_state.item_query = q

            matches = item_matches(q) if q.strip() else []

            if matches:
                found = pd.DataFrame([r for r in matches[:8]])
                names = found["품목명"].tolist()
                selected_name = st.selectbox("검색 결과", names)
                row = found[found["품목명"] == selected_name].iloc[0]

                st.session_state.budget_id = row["예산ID"]
                br = get_budget(row["예산ID"])
                candidate = get_items(row["예산ID"])

                st.success(
                    f"**{row['품목명']}**\n\n"
                    f"{row['용도']}\n\n"
                    f"예상 가격대: {won(row['최저가'])} ~ {won(row['최고가'])}"
                )
                if br is not None:
                    st.caption(f"연결 예산 후보: {br['예산명']}")
            elif q.strip():
                st.info("현재 예시 데이터에서 일치하는 품목을 찾지 못했습니다.")

        st.markdown("---")
        if st.button("← 시작 방식 다시 선택", use_container_width=True):
            st.session_state.step = 1
            st.rerun()

        if st.button("처음부터 다시", use_container_width=True):
            reset_flow()

    # 오른쪽 추천 + 구매계획
    with right:
        st.markdown("## ② 추천품목 + 구매계획")
        st.caption("품목을 체크하면 바로 구매계획에 반영됩니다. 수량과 예상 단가도 직접 수정할 수 있습니다.")

        if candidate.empty:
            st.info("왼쪽에서 검색하거나 예산명을 선택하면 추천 품목과 구매계획표가 표시됩니다.")
            total = 0
            remain = st.session_state.budget_amount
        else:
            work = candidate.copy()
            work["선택"] = False
            work["예상단가"] = ((work["최저가"] + work["최고가"]) / 2).astype(int)
            work["수량"] = 1

            if mode == "item" and st.session_state.item_query.strip():
                ms = item_matches(st.session_state.item_query)
                if ms:
                    target = ms[0]["품목명"]
                    work.loc[work["품목명"] == target, "선택"] = True

            editor_key = f"purchase_editor_{st.session_state.budget_id}_{mode}"

            edited = st.data_editor(
                work[["선택", "품목명", "용도", "예상단가", "수량"]],
                hide_index=True,
                use_container_width=True,
                height=360,
                disabled=["품목명", "용도"],
                column_config={
                    "선택": st.column_config.CheckboxColumn(
                        "구매",
                        help="체크하면 구매계획에 포함됩니다.",
                        default=False,
                    ),
                    "품목명": st.column_config.TextColumn("품목"),
                    "용도": st.column_config.TextColumn("용도"),
                    "예상단가": st.column_config.NumberColumn(
                        "예상 단가",
                        min_value=0,
                        step=1000,
                        format="%d원",
                        help="실제 견적을 알고 있다면 직접 수정할 수 있습니다.",
                    ),
                    "수량": st.column_config.NumberColumn(
                        "수량",
                        min_value=1,
                        max_value=999,
                        step=1,
                    ),
                },
                key=editor_key,
            )

            selected = edited[edited["선택"] == True].copy()

            if not selected.empty:
                selected["소계"] = selected["예상단가"] * selected["수량"]
                total = int(selected["소계"].sum())
            else:
                total = 0

            remain = int(st.session_state.budget_amount - total)

            st.markdown("### 현재 구매계획")
            if selected.empty:
                st.caption("아직 선택한 품목이 없습니다. 위 표에서 필요한 품목을 체크해보세요.")
            else:
                st.dataframe(
                    selected[["품목명", "수량", "예상단가", "소계"]],
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "예상단가": st.column_config.NumberColumn("예상 단가", format="%d원"),
                        "소계": st.column_config.NumberColumn("소계", format="%d원"),
                    },
                )

                csv_bytes = selected[["품목명", "수량", "예상단가", "소계"]].to_csv(
                    index=False
                ).encode("utf-8-sig")

                st.download_button(
                    "구매계획 CSV 내려받기",
                    data=csv_bytes,
                    file_name="구매계획_초안.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            if remain < 0:
                st.error(f"가용예산을 {won(abs(remain))} 초과했습니다. 품목·수량·단가를 조정하세요.")
            elif total == 0:
                st.info("추천 품목을 체크하면 합계와 잔여예산이 즉시 계산됩니다.")
            else:
                ratio = min(total / st.session_state.budget_amount, 1.0)
                st.progress(ratio)
                st.success(f"가용예산의 약 {ratio*100:.1f}%를 계획했습니다.")

        plan_total_box.metric("현재 구매금액", won(total))
        remain_box.metric(
            "잔여예산",
            won(remain),
            delta=(f"-{won(total)} 사용" if total > 0 else None),
            delta_color="off",
        )

    st.divider()
    st.caption(
        "품목 선택, 수량 변경, 예상 단가 변경 시 구매금액과 잔여예산이 바로 다시 계산됩니다. "
        "예상 가격은 프로토타입용 예시 데이터입니다."
    )

st.divider()
st.caption("군 소액구매 도우미 · 사용성 검증용 Prototype v0.5")
