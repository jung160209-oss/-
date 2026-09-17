# 군 소액구매 도우미 — 프로토타입 v0.1

지인에게 링크를 보내 사용성 반응을 확인하기 위한 **작동형 웹앱**입니다.

## 현재 구현 기능

- 예산명/업무 키워드 검색
- 예산의 용도·관련업무·주의사항 표시
- 예산별 추천 품목과 예시 가격대 표시
- 자연어 문제 설명 → 비슷한 문제 → 추천 품목 연결
- 예산 금액과 품목/수량을 넣어 구매계획 초안 계산
- 군사보안 정보 입력 금지 안내

> 모든 예산명·코드·가격은 프로토타입 테스트용 예시 데이터입니다.
> 실제 군/공공기관 집행 가능 여부를 확정하는 서비스가 아닙니다.

---

## 1. 내 PC에서 바로 실행하기

Python이 설치되어 있다면 이 폴더에서:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

브라우저에서 앱이 열립니다.

---

## 2. 지인에게 링크로 공유하기 — Streamlit Community Cloud

1. GitHub 계정을 만듭니다.
2. 새 GitHub 저장소(repository)를 하나 만듭니다.
3. 이 폴더 안의 파일을 전부 업로드합니다.
   - `streamlit_app.py`
   - `requirements.txt`
   - `data/` 폴더와 CSV 3개
4. Streamlit Community Cloud에 GitHub로 로그인합니다.
5. `Create app`을 누릅니다.
6. 방금 만든 저장소를 선택합니다.
7. Main file path는 `streamlit_app.py`를 지정합니다.
8. Deploy 합니다.
9. 생성된 `*.streamlit.app` 링크를 지인에게 공유합니다.

이 버전은 OpenAI API 키가 필요 없습니다.

---

## 3. 데이터를 바꾸는 방법

`data/` 폴더의 CSV만 수정하면 됩니다.

### budgets.csv
예산 분류와 설명

### items.csv
예산에 연결되는 추천 품목과 가격대

### problem_map.csv
사용자가 말하는 문제와 추천 품목 매핑

GitHub에 수정본을 올리면 배포 앱에도 반영됩니다.

---

## 다음 버전에서 붙일 기능

- OpenAI API 자연어 분석
- 실제 공개가격 검색/비교
- 품목 즐겨찾기
- 구매계획 저장
- 견적요청서 PDF 출력
- 테스트 사용자 피드백 수집
