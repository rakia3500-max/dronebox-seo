# 드론박스 키워드 분석툴

네이버 실제 검색량 데이터 기반 키워드 분석 + AI SEO 문구 자동 생성툴

---

## 배포 순서 (10분이면 완료)

### 1단계 — 네이버 API 키 확인
1. https://searchad.naver.com 로그인
2. 우측 상단 프로필 클릭 → **API 관리**
3. 아래 3가지 값 메모
   - `고객 ID (Customer ID)`
   - `Access License`
   - `Secret Key`

---

### 2단계 — GitHub에 업로드
1. https://github.com 로그인
2. **New repository** 클릭
3. 이름: `dronebox-seo` / Public 선택 / Create
4. 이 폴더 전체를 올리기:
   - 방법 A: GitHub Desktop 앱 사용 (쉬움)
   - 방법 B: 아래 명령어
     ```bash
     git init
     git add .
     git commit -m "init"
     git remote add origin https://github.com/유저명/dronebox-seo.git
     git push -u origin main
     ```

---

### 3단계 — Vercel 배포
1. https://vercel.com 접속 → GitHub 계정으로 로그인
2. **Add New Project** → GitHub에서 `dronebox-seo` 선택 → Import
3. **Environment Variables** (환경변수) 3개 추가:

   | 이름 | 값 |
   |------|-----|
   | `NAVER_CUSTOMER_ID` | 1단계에서 메모한 고객 ID |
   | `NAVER_ACCESS_KEY` | 1단계에서 메모한 Access License |
   | `NAVER_SECRET_KEY` | 1단계에서 메모한 Secret Key |

4. **Deploy** 클릭 → 2분 후 완료!
5. 발급된 URL (예: `dronebox-seo.vercel.app`) 접속하면 바로 사용 가능

---

## 파일 구조
```
dronebox-seo/
├── api/
│   └── keyword.js     ← 네이버 API 호출 (서버)
├── public/
│   └── index.html     ← 키워드 분석 화면
├── vercel.json        ← Vercel 라우팅 설정
└── README.md
```

## 기능
- 키워드 입력 → 네이버 실제 PC/모바일 월간 검색량 조회
- 연관 키워드 최대 100개 표시
- 검색량 기반 AI SEO 문구 자동 생성 (타이틀/설명/키워드/태그/속성)
- CSV 다운로드
