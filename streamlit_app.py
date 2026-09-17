
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

def won(v):
    return f"{int(v):,}원"

def get_budget(budget_id):
    row = budgets[budgets["예산ID"] == budget_id]
    return None if row.empty else row.iloc[0]

def problem_scores(query):
    result = []
    if not query.strip():
        return result
    for _, r in problems.iterrows():
        text = " ".join([
            str(r["사용자표현"]),
            str(r["문제키워드"]),
            str(r["증상설명"]),
            str(r["추천품목"])
        ])
        s = token_score(query, text)
        for kw in str(r["문제키워드"]).split(","):
            kw = norm(kw)
            if kw and kw in norm(query):
                s += 5
        if s > 0:
            result.append((s, r))
    result.sort(key=lambda x: x[0], reverse=True)
    return result

def reset_all():
    st.session_state.clear()
    st.rerun()

defaults = {
    "started": False,
    "budget_amount": 1_000_000,
    "budget_filter": "전체",
    "problem_filter": "",
    "item_filter": "",
    "cart": {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.markdown("""
<style>
.block-container {
    max-width: 1280px;
    padding-top: 1.5rem;
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
.filterbox {
    border: 1px solid rgba(120,120,120,.22);
    border-radius: 18px;
    padding: 16px 18px;
    margin-bottom: 14px;
    background: rgba(120,120,120,.025);
}
div[data-testid="stButton"] > button {
    min-height: 44px;
    border-radius: 12px;
    font-weight: 650;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero notranslate" translate="no">
  <h1>🛠️ 군 소액구매 도우미</h1>
  <p><b>예산에서 시작하는 구매</b><br>
  예산명·업무 문제·품목명 등 알고 있는 정보만 입력하면 필요한 품목을 좁혀가며 구매계획을 만들 수 있습니다.</p>
</div>
""", unsafe_allow_html=True)

st.warning(
    "프로토타입 테스트용 예시 데이터입니다. 실제 집행 가능 여부는 적용 지침·회계 기준·담당자 확인이 필요합니다. "
    "부대명, 세부 위치, 장비 보유현황, 비공개 문서 등 군사보안 정보는 입력하지 마세요.",
    icon="⚠️",
)

# 시작 화면은 취지만 보여주고 한 버튼으로 진입
if not st.session_state.started:
    st.subheader("구매계획을 시작해보세요")
    st.write(
        "처음부터 검색 방식을 하나 고를 필요는 없습니다. "
        "전체 품목을 보면서 예산명, 문제, 품목명 조건을 원하는 만큼 조합해서 찾을 수 있습니다."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 💰 예산명")
        st.caption("사용할 예산명을 알고 있다면 예산으로 먼저 좁힙니다.")
    with c2:
        st.markdown("### 💬 문제·업무")
        st.caption("무엇을 사야 할지 모르면 상황을 평소 말하듯 입력합니다.")
    with c3:
        st.markdown("### 📦 품목명")
        st.caption("필요한 품목을 알고 있다면 품목명으로 바로 찾습니다.")

    st.write("")
    if st.button("구매계획 시작하기 →", type="primary", use_container_width=True):
        st.session_state.started = True
        st.rerun()

else:
    # 상단 예산 요약
    st.markdown("## 구매계획 만들기")
    top = st.columns([1.2, 1, 1])

    with top[0]:
        amount = st.number_input(
            "가용예산",
            min_value=10_000,
            max_value=100_000_000,
            value=int(st.session_state.budget_amount),
            step=10_000,
            format="%d",
            help="언제든 변경할 수 있습니다.",
        )
        st.session_state.budget_amount = int(amount)

    total_placeholder = top[1].empty()
    remain_placeholder = top[2].empty()

    st.caption("검색 조건을 여러 개 함께 사용할 수 있습니다. 조건을 지우면 다시 전체 품목이 표시됩니다.")
    st.divider()

    # 여러 조건 검색
    st.markdown("## ① 조건으로 품목 좁히기")

    f1, f2, f3 = st.columns([1, 1.25, 1])

    with f1:
        budget_names = ["전체"] + budgets["예산명"].tolist()
        selected_budget = st.selectbox(
            "예산명",
            budget_names,
            index=budget_names.index(st.session_state.budget_filter)
            if st.session_state.budget_filter in budget_names else 0,
        )
        st.session_state.budget_filter = selected_budget

    with f2:
        problem_q = st.text_input(
            "문제·업무로 찾기",
            value=st.session_state.problem_filter,
            placeholder="예: 에어호스를 연결하고 싶어요",
        )
        st.session_state.problem_filter = problem_q

    with f3:
        item_q = st.text_input(
            "품목명으로 찾기",
            value=st.session_state.item_filter,
            placeholder="예: 호스, 피팅, 토너",
        )
        st.session_state.item_filter = item_q

    # 후보 품목 만들기
    filtered = items.copy()

    # 예산 조건
    if selected_budget != "전체":
        bid = budgets[budgets["예산명"] == selected_budget].iloc[0]["예산ID"]
        filtered = filtered[filtered["예산ID"] == bid]

    # 문제 조건
    problem_info = None
    if problem_q.strip():
        scored = problem_scores(problem_q)
        if scored:
            top_problem = scored[0][1]
            problem_info = top_problem
            related_bid = top_problem["관련예산ID"]

            # 문제 조건은 관련 예산으로 먼저 좁히고 추천품목 단어가 있으면 점수 우선순위에 활용
            filtered = filtered[filtered["예산ID"] == related_bid]

            st.info(
                f"**문제 해석:** {top_problem['증상설명']}\n\n"
                f"추천 방향: {top_problem['추천품목']}\n\n"
                f"먼저 확인: {top_problem['확인사항']}"
            )
        else:
            filtered = filtered.iloc[0:0]
            st.info("현재 예시 데이터에서 비슷한 문제를 찾지 못했습니다.")

    # 품목명 조건
    if item_q.strip():
        mask = filtered.apply(
            lambda r: token_score(item_q, f"{r['품목명']} {r['용도']}") > 0,
            axis=1
        )
        filtered = filtered[mask]

    # 예산명 붙이기
    budget_name_map = dict(zip(budgets["예산ID"], budgets["예산명"]))
    filtered = filtered.copy()
    filtered["예산명"] = filtered["예산ID"].map(budget_name_map)

    # 조건 초기화
    rc1, rc2 = st.columns([1, 4])
    with rc1:
        if st.button("검색조건 초기화", use_container_width=True):
            st.session_state.budget_filter = "전체"
            st.session_state.problem_filter = ""
            st.session_state.item_filter = ""
            st.rerun()
    with rc2:
        st.caption(f"현재 조건에 맞는 품목: {len(filtered)}개")

    st.divider()

    # 아래는 좌우: 품목 목록 / 구매계획
    left, right = st.columns([1.55, 1], gap="large")

    with left:
        st.markdown("## ② 품목 선택")
        st.caption("처음에는 전체 품목이 표시됩니다. 검색 조건을 추가할수록 목록이 좁아집니다.")

        if filtered.empty:
            st.warning("현재 조건에 맞는 품목이 없습니다. 검색 조건을 일부 지워보세요.")
        else:
            # 세션 카트 상태 기반으로 표 구성
            work = filtered[["품목ID", "예산명", "품목명", "용도", "최저가", "최고가"]].copy()
            work["선택"] = work["품목ID"].apply(lambda pid: pid in st.session_state.cart)
            work["예상단가"] = work.apply(
                lambda r: st.session_state.cart.get(r["품목ID"], {}).get(
                    "단가", int((r["최저가"] + r["최고가"]) / 2)
                ),
                axis=1
            )
            work["수량"] = work["품목ID"].apply(
                lambda pid: st.session_state.cart.get(pid, {}).get("수량", 1)
            )

            editor = st.data_editor(
                work[["선택", "품목ID", "예산명", "품목명", "용도", "예상단가", "수량"]],
                hide_index=True,
                use_container_width=True,
                height=480,
                disabled=["품목ID", "예산명", "품목명", "용도"],
                column_config={
                    "선택": st.column_config.CheckboxColumn("구매"),
                    "품목ID": None,
                    "예산명": st.column_config.TextColumn("관련 예산"),
                    "품목명": st.column_config.TextColumn("품목"),
                    "용도": st.column_config.TextColumn("용도"),
                    "예상단가": st.column_config.NumberColumn(
                        "예상 단가",
                        min_value=0,
                        step=1000,
                        format="%d원",
                    ),
                    "수량": st.column_config.NumberColumn(
                        "수량",
                        min_value=1,
                        max_value=999,
                        step=1,
                    ),
                },
                key="catalog_editor",
            )

            # 현재 화면에서 변경한 내용을 cart에 동기화
            visible_ids = set(work["품목ID"].tolist())
            edited_ids = set(editor["품목ID"].tolist())

            for _, row in editor.iterrows():
                pid = row["품목ID"]
                if bool(row["선택"]):
                    st.session_state.cart[pid] = {
                        "품목명": row["품목명"],
                        "예산명": row["예산명"],
                        "용도": row["용도"],
                        "단가": int(row["예상단가"]),
                        "수량": int(row["수량"]),
                    }
                else:
                    st.session_state.cart.pop(pid, None)

    with right:
        st.markdown("## ③ 구매계획")
        cart = st.session_state.cart

        if not cart:
            total = 0
            remain = st.session_state.budget_amount
            st.info("왼쪽 품목표에서 구매할 품목을 체크해보세요.")
        else:
            plan_rows = []
            for pid, d in cart.items():
                sub = int(d["단가"]) * int(d["수량"])
                plan_rows.append({
                    "품목": d["품목명"],
                    "관련 예산": d["예산명"],
                    "수량": d["수량"],
                    "단가": d["단가"],
                    "소계": sub,
                })

            plan = pd.DataFrame(plan_rows)
            total = int(plan["소계"].sum())
            remain = int(st.session_state.budget_amount - total)

            st.dataframe(
                plan,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "단가": st.column_config.NumberColumn("단가", format="%d원"),
                    "소계": st.column_config.NumberColumn("소계", format="%d원"),
                },
            )

            if remain < 0:
                st.error(f"가용예산을 {won(abs(remain))} 초과했습니다.")
            else:
                ratio = min(total / st.session_state.budget_amount, 1.0)
                st.progress(ratio)
                st.success(f"가용예산의 약 {ratio*100:.1f}%를 계획했습니다.")

            csv_bytes = plan.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "구매계획 CSV 내려받기",
                data=csv_bytes,
                file_name="구매계획_초안.csv",
                mime="text/csv",
                use_container_width=True,
            )

            if st.button("구매계획 전체 비우기", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()

        total_placeholder.metric("현재 구매금액", won(total))
        remain_placeholder.metric(
            "잔여예산",
            won(remain),
            delta=(f"-{won(total)} 사용" if total > 0 else None),
            delta_color="off",
        )

    st.divider()
    b1, b2 = st.columns([1, 1])
    with b1:
        if st.button("처음 화면으로", use_container_width=True):
            st.session_state.started = False
            st.rerun()
    with b2:
        if st.button("전체 초기화", use_container_width=True):
            reset_all()

st.divider()
st.caption("군 소액구매 도우미 · 사용성 검증용 Prototype v0.6")
