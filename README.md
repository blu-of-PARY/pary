# Galpi · 갈피 Mintlify guide

2026-09-16 기준 한국어 17페이지와 영어 17페이지의 사용자 설명서입니다. 한국어는 루트 경로, 영어는 `en/`의 같은 파일명에 둡니다. `docs.json`의 `navigation.languages`가 언어 선택과 탐색을 구성합니다.

## 작성 기준

현재 앱 화면과 저장·인식 동작을 기준으로 설명합니다. 제품 방향 문서의 제안만으로 기능을 공개 문서에 추가하지 않습니다.

- 홈의 `잠깐 돌아보기` / `Take a moment`, 선택형 종이 활동, 원본을 보존하는 후속 생각 연결을 반영했습니다.
- 한국어·영어 기록 언어와 홈 위젯의 음성 진입을 반영했습니다. 화면을 여는 것과 실제 녹음 시작을 구분합니다.
- 기본 OCR·음성 전사와 선택적 Gemini·OpenAI 기능을 구분합니다. 실제 UI의 YouTube 자막 가져오기는 공개 자막 경로이며 개인 키가 필요하지 않습니다. 호출되지 않는 Gemini 영상 분석 경로를 현재 사용법으로 안내하지 않습니다.
- 현재 탐색에서 숨겨진 원고·발행·집중 세션은 사용자 사용법에 포함하지 않습니다.
- 책별 구절 자동 병합·자동 구절 분리·대화형 의미 검색은 구현 기능으로 설명하지 않습니다.
- `privacy-and-data`는 기능별 데이터 안내입니다. 사업자 정보와 법적 고지 전체를 갖춘 개인정보처리방침을 대신하지 않습니다.
- 색상은 `../ThoughtArchiveNative/design/brand-palette.json`의 기존 값으로 맞췄습니다. 별도의 색상 원본을 만들지 않습니다.

## 화면 구성과 자산

`style.css`는 Mintlify의 실제 렌더링 요소와 레이아웃 선택자를 사용해 문서 전체를 갈피의 종이·잉크·세이지 팔레트로 맞춥니다. 사이드바의 상위 묶음은 Freesentation Bold와 세이지 표시·구분선으로 하위 문서와 구별합니다. 기본 카드의 순백색 대신 앱 Surface `#F4EEE2`를 쓰고, 기본 파란색 Note·Tip도 세이지 계열로 맞췄습니다. 첫 화면과 시작 안내의 카드 구성은 한·영에서 같은 구조입니다. 모바일 390px, 데스크톱 1440px, 라이트·다크 모드에서 확인했습니다.

`assets/brand/galpi-snail.svg`는 사용자가 확정한 Illustrator 마스터 `../ThoughtArchiveNative/docs/brand-assets/snail-marker-v1/galpi-snail.svg`의 수정 없는 복사본입니다. 캐릭터 형태나 색은 문서에서 따로 고치지 않습니다. `assets/fonts/`의 WOFF2는 앱에 포함된 대구동성로체·Freesentation 원본의 웹용 압축본이며, 출처와 라이선스 고지를 같은 폴더에 보관합니다. 색상이나 글꼴을 바꿀 때는 앱의 원본과 고지를 먼저 확인합니다.

## 미리보기와 검증

프로젝트에 맞는 Mintlify CLI를 준비한 뒤 이 폴더에서 `mint dev`를 실행합니다. 글로벌 도구 설치는 필수가 아닙니다. 실제 사용할 CLI 버전의 명령과 환경 요건은 [공식 CLI 안내](https://www.mintlify.com/docs/cli/install)를 확인합니다.

공개 전 검증 순서:

1. Mintlify 설정과 MDX 검증 및 링크 확인.
2. 두 언어의 모바일·데스크톱 미리보기, 언어 전환과 내부 링크 확인.
3. 실제 한국어·영어 앱의 메뉴·버튼 이름과 사용법 대조.
4. 기능 검증이 끝난 배포 대상 앱의 화면만 필요한 경우 캡처.
5. 아래 외부 정보를 실제 값으로 채운 뒤 공식 안내 링크 연결.

34개 내비게이션 경로, frontmatter, 내부 링크와 MDX 컴포넌트 짝은 정적 검사에서 통과했습니다. 2026-09-16 현재 Mintlify 실제 빌드와 로컬 렌더링도 확인했습니다.

## 배포 연결

Mintlify의 `pary/pary` 프로젝트는 [blu-of-PARY/pary](https://github.com/blu-of-PARY/pary) 저장소의 `main` 브랜치 및 루트 `docs.json`에 연결돼 있습니다. 이 폴더의 문서와 자산을 저장소 루트에 동기화한 뒤 푸시하면 배포가 시작됩니다. 공개 주소는 [pary.mintlify.site](https://pary.mintlify.site)입니다.

언어 구성은 [공식 국제화 안내](https://www.mintlify.com/docs/guides/internationalization)를 따릅니다. 한국어와 영어는 동일 페이지 경로를 공유하지 않으며, 각 언어의 본문 링크는 해당 언어의 파일을 가리킵니다.

## 확인되지 않은 외부 정보

다음 정보는 로컬 자료에서 확인되지 않아 임의로 만들지 않았습니다.

- 운영자 이름과 공개 고객 문의 연락처.
- 최종 개인정보처리방침과 필요한 약관의 공개 주소.
- 이 앱의 App Store 또는 TestFlight 초대 주소.

실제 값을 확인한 뒤 해당 언어의 navbar/footer와 도움말에 연결합니다. 다른 이름이 비슷한 앱의 링크를 사용하지 않습니다. 현재 스크린샷은 포함하지 않았으므로 오래된 화면이 노출되지는 않습니다.

## 변경 시 유지할 것

한국어·영어 페이지를 함께 갱신하고 `docs.json`에 두 경로를 각각 등록합니다. 영어 UI의 최종 번역이 바뀌면 특히 Settings, Recognition language, Take a moment, Add a thought의 명칭을 대조합니다. 사용자가 직접 작성한 원문은 번역하거나 변경하지 않습니다.


## 2026-09-16 최종 검증

- 한국어 17개·영어 17개, 공식 Mintlify 빌드·끊어진 링크 검사 통과.
- 데스크톱 및 390px 모바일에서 본문, 언어 전환, 시작 페이지 링크 확인.
- 로컬 미리보기: http://localhost:3100 (공개 배포 주소가 아님).
- Mintlify 배포 성공: `blu-of-PARY/pary`의 `main`에서 `pary.mintlify.site`에 공개됨. 한국어·영어 첫 화면과 영어 상세 페이지, 밝은·어두운 모드의 표면색을 실제 사이트에서 확인함.
- 앱 측 구현·실기기/배포 잔여 항목: `../ThoughtArchiveNative/docs/RELEASE-READINESS-2026-09-16.md`.
