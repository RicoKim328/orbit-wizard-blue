# orbit-wizard-blue

Windows 11 x64용 한국어 위성 궤도 데스크톱 앱입니다. CelesTrak GP JSON에서 공공 위성을 검색하고 SGP4로 지정된 UTC 구간의 위치와 속도를 계산합니다. TEME·ITRS 결과 표, 측지 위도·경도·고도 표, GCRS 또는 ITRS 3D 궤도, CSV와 계산 메타데이터를 제공합니다.

## 사용 방법

1. `orbit-wizard-blue.exe`를 실행합니다. ZIP으로 받은 경우 폴더 전체를 먼저 압축 해제하세요.
2. 이름이나 NORAD 번호로 위성을 검색하고 결과 하나를 선택합니다.
3. UTC 시작·종료 시각과 간격을 확인한 후 **궤도 계산**을 누릅니다. 기본값은 현재 UTC부터 24시간, 60초 간격입니다.
4. 3D 화면을 마우스로 회전·확대하고, **GCRS · 관성** / **ITRS · 지구 고정**을 바꿔 봅니다. 슬라이더와 표의 행 선택은 동일한 샘플을 가리킵니다. 재생은 1×, 10×, 60×, 600×이며 기본값은 60×입니다. 계산된 샘플 사이의 위성 위치를 보간하지 않습니다.
5. **자료 상태…**에서 현재 GP·IERS·윤초 자료와 표시된 결과에 사용된 자료의 출처·수신/확인 시각·캐시 상태를 확인할 수 있습니다. **결과 CSV 내보내기**는 UTF-8 BOM CSV와 메타데이터 JSON을 저장합니다.

단위는 위치 km, 속도 km/s, 각도 도(°)입니다. 모든 입력·출력 시각은 UTC입니다. CelesTrak 위성 자료와 IERS/윤초 자료는 **2시간 디스크 캐시**에 저장되어 실행 사이에 공유됩니다. 계산을 시작할 때 선택 위성 자료의 캐시 만료 여부를 확인하며, 만료된 경우 갱신을 시도합니다. 앱의 **자료 업데이트**도 공급자의 2시간 재확인 제한 안에서는 기존 자료를 유지하고 다음 확인 가능 시각을 표시할 수 있습니다. 자료가 바뀌어도 기존 계산 결과는 유지되므로 다시 계산해야 새 자료가 반영됩니다. 최신 요소시각에서 멀리 떨어진 예측, 오래된/예측 지구 회전 자료, 제공자 자료 오류는 상태와 결과 경고에 표시됩니다. 인터넷에 접근할 수 없으면 사용 가능한 캐시 또는 동봉된 지구 회전 자료가 사용될 수 있습니다.

## 개발 환경

Python 3.12가 필요합니다. 모든 명령은 저장소 루트에서 실행합니다.

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pip install --no-deps -e .
.venv\Scripts\python.exe -m orbit_wizard_blue
```

Linux/macOS:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python -m orbit_wizard_blue
```

린트와 테스트:

```sh
.venv/bin/python -m ruff check src tests tools
QT_QPA_PLATFORM=offscreen ORBIT_WIZARD_DISABLE_3D=1 .venv/bin/python -m pytest -q
.venv/bin/python -m orbit_wizard_blue --smoke-test
```

Windows에서는 위 명령의 `.venv/bin/python`을 `.venv\Scripts\python.exe`로 바꿉니다. `ORBIT_WIZARD_DISABLE_3D=1`은 OpenGL 없이 GUI 테스트를 실행합니다.

Windows x64 폴더 ZIP 빌드:

```powershell
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm orbit-wizard-blue.spec
.\dist\orbit-wizard-blue\orbit-wizard-blue.exe --smoke-test
Compress-Archive -Path dist\orbit-wizard-blue -DestinationPath dist\orbit-wizard-blue-windows-x64.zip
```

`.github/workflows/build.yml`은 push 또는 수동 실행 시 Windows에서 린트·테스트·빌드·실행 파일 기본 검사를 하고 ZIP 아티팩트를 업로드합니다. Linux에서 만든 실행 파일은 Windows용이 아닙니다. `--smoke-test`는 네트워크 접속이나 GUI 창 없이 패키지 import, 로컬 GP JSON→SGP4 변환, IERS 좌표 변환과 CSV 저장을 확인합니다. `--smoke-output 파일명`을 함께 지정하면 검증 상태를 JSON으로 저장합니다.

## 코드 구조

- `src/orbit_wizard_blue/data.py`: CelesTrak/IERS 데이터 접근과 디스크 캐시
- `src/orbit_wizard_blue/orbit.py`, `models.py`, `export.py`: 전파·좌표 변환·불변 결과·내보내기
- `src/orbit_wizard_blue/gui/`: PySide6 화면, 3D 표시, 결과 표, 비동기 작업
- `tests/`: 자동 테스트
- `orbit-wizard-blue.spec`: PyInstaller 폴더형 배포 설정

Python 코드는 4칸 들여쓰기와 `snake_case` 함수/파일 이름, `PascalCase` 클래스 이름을 사용합니다. 외부 자료 조회와 궤도 계산은 작업 스레드에서 실행하며 3D 렌더링 중 네트워크를 호출하지 않습니다.

앱 실행과 백그라운드 작업 오류의 진단 로그는 운영체제 사용자 로그 디렉터리의 `orbit-wizard-blue/orbit-wizard-blue.log`에 저장됩니다. 파일은 최대 1 MB, 이전 로그 3개까지 보관합니다. 테스트나 별도 실행에서 로그 경로를 바꾸려면 `ORBIT_WIZARD_LOG_DIR` 환경 변수를 지정할 수 있습니다.
