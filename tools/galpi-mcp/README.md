# 갈피 보관함을 GPT·Claude에서 묻기 (로컬 실험판)

갈피에서 직접 내보낸 백업 ZIP을 **내 컴퓨터에서만** 읽는 MCP 서버입니다. Codex/ChatGPT 데스크톱 앱과 Claude Code의 로컬 MCP 클라이언트에서 `archive_info`, `search_archive`, `get_record`, `recent_records` 네 가지 읽기 전용 도구를 제공합니다. 백업 파일을 수정하거나 서버로 업로드하지 않습니다. AI 클라이언트가 도구를 호출하면 **요청에 해당하는 텍스트 결과는 그 AI 서비스에 전달**될 수 있습니다.

현재는 한 시점의 백업입니다. 갈피에서 새 기록을 쓰거나 고친 뒤에는 새 ZIP을 내보내고 `GALPI_BACKUP_PATH`를 그 파일로 바꾼 다음 AI 클라이언트를 재시작해야 합니다. ChatGPT 웹과 Claude 웹은 이 로컬 서버에 직접 접속할 수 없습니다. 일반 사용자용 원격 연동에는 계정별 인증, 사용자 동의, 동기화/삭제 정책이 별도로 필요합니다.

## 준비

1. iPhone 갈피의 **설정 → 백업·복원 → 내보내기**에서 ZIP을 만들고 Mac의 원하는 폴더에 저장합니다. 백업 ZIP에는 사진·녹음·설정 등도 들어 있으므로 본인이 관리하는 위치에 보관하세요. 이 서버는 ZIP 중 텍스트 기록·자료·연결 정보만 읽습니다.
2. Mac에 [`uv`](https://docs.astral.sh/uv/)가 있다면 이 폴더에서 `uv sync --locked`를 실행합니다. Python 3.10 이상 환경에서는 `python3 -m venv .venv` 후 `.venv/bin/python -m pip install 'mcp>=2,<3'`도 가능합니다.
3. 터미널에서 이 폴더(`tools/galpi-mcp`)로 이동합니다. 아래 예시의 `/absolute/path/to/GalpiBackup.zip`을 실제 파일의 **절대경로**로 바꿉니다. 키나 비밀번호는 필요하지 않습니다.

### Codex / ChatGPT 데스크톱 앱

```sh
codex mcp add galpi-local \
  --env GALPI_BACKUP_PATH=/absolute/path/to/GalpiBackup.zip \
  -- "$(pwd)/.venv/bin/python" "$(pwd)/server.py"
```

`codex mcp list`로 등록을 확인합니다. ChatGPT 데스크톱 앱에서는 MCP 서버 설정에서 같은 로컬 구성을 볼 수 있습니다. 다른 Mac에 옮길 때는 위의 코드 경로도 새 위치로 바꿉니다.

### Claude Code

```sh
claude mcp add --transport stdio \
  --scope user \
  galpi-local -e GALPI_BACKUP_PATH=/absolute/path/to/GalpiBackup.zip -- \
  "$(pwd)/.venv/bin/python" "$(pwd)/server.py"
```

`claude mcp get galpi-local`로 확인합니다. Claude 데스크톱/웹의 클라우드 커넥터는 별도의 원격 MCP 서버가 필요합니다.

### Claude Desktop의 채팅 화면

Claude Code의 설정은 Claude Desktop **채팅** 설정과 별개입니다. macOS에서는 `~/Library/Application Support/Claude/claude_desktop_config.json`의 `mcpServers`에 다음 항목을 추가하고 Claude Desktop을 완전히 종료했다가 다시 엽니다. `command`, `args`, `env`의 파일 경로는 이 Mac에서 실제로 존재하는 절대경로로 바꿉니다. 기존 설정의 다른 항목은 지우지 마세요.

```json
{
  "galpi-local": {
    "command": "/absolute/path/to/tools/galpi-mcp/.venv/bin/python",
    "args": ["/absolute/path/to/tools/galpi-mcp/server.py"],
    "env": {"GALPI_BACKUP_PATH": "/absolute/path/to/GalpiBackup.zip"}
  }
}
```

위 객체는 `mcpServers` **안에 들어갈 한 항목**입니다. 설정 파일 전체를 이 예시로 덮어쓰지 마세요. Claude 웹이나 Claude Desktop의 원격 커넥터 메뉴는 이 로컬 설정과 다릅니다.

연결 후 예시 질문: “갈피에서 내가 저장한 독서 자료와 직접 남긴 생각을 구분해서, 최근 반복되는 주제를 근거 기록 ID와 함께 정리해 줘.”

## 데이터 범위

- 포함: 휴지통이나 보관 상태가 아닌 생각의 편집된 글(없으면 원문), 저장 자료의 제목·발췌·메모·원래 URL, 생각과 자료의 연결 ID
- 제외: 사진·녹음 원본, API 키·설정, 휴지통/보관 항목, ZIP 밖에 저장된 YouTube 자막 파일
- 자료는 `thoughtarchive://sources/<ID>` 주소로 갈피 앱을 열 수 있습니다. 생각 기록은 현재 앱에 전용 딥링크가 없어 ID로만 인용합니다.
- 검색은 간단한 단어 포함 방식이며 의미 검색이나 대화형 동기화가 아닙니다. 검색 결과는 일부 문장이고 `get_record`로 세부 내용을 읽습니다. 세부 본문은 20,000자로 제한됩니다.

백업 ZIP과 MCP 등록 환경 변수에 저장된 경로는 본인 컴퓨터에 남습니다. 사용을 중단하려면 `codex mcp remove galpi-local` 또는 `claude mcp remove galpi-local -s user`를 실행합니다. ZIP 삭제 여부는 본인이 결정합니다.

## 검증

실제 개인 자료 대신 합성 백업으로 프라이버시 필터와 MCP 왕복을 테스트합니다.

```sh
.venv/bin/python -m unittest -v test_archive.py
```
