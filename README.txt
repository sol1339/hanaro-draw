하나로마트 행운 추첨 - Android 소스 프로젝트

현재 제공 상태
APK가 아닌 소스 프로젝트입니다. 제작 환경에서 Java 컴파일러 및 도구 설치가
실패하여 APK 생성과 Android 실기기 검증은 완료하지 못했습니다.
PC에서 Kivy 화면 실행, 시작/멈춤, 설정 화면 및 한글 표시를 확인했습니다.
추첨 엔진 테스트 5개가 통과했습니다. Android 파일 저장창과 외부 키보드는
실기기 확인이 필요합니다. 아래 빌드 워크플로도 아직 실행 검증되지 않았습니다.

기능
- 총 추첨 20,000회 기본값. 1~10등 경품명과 전체 배정 수량 수정.
- 기본 당첨 1등 1개 / 2등 2개 / 3등 4개 / 나머지 등수 0개.
- 나머지 꽝 자동 계산. 남은 수량에 비례한 무작위 비복원 추첨.
- 터치 시작/멈춤 버튼 하나. 외부 키보드 Enter 지원.
- 애니메이션 중 앱을 벗어나면 미확정 추첨은 취소(수량 차감 없음).
- 결과는 기기 내부 SQLite에 저장 후 화면에 표시.
- 초기화: 경품 설정 유지, 전체 기록 및 차감 수량 초기화.
- 기록 저장: Android 파일 저장 창에서 CSV 저장 위치 선택.
- 네트워크 연결 없이 운영. 고객 개인정보 수집 기능 없음.

대상
Android 6.0 이상, 64비트 ARM 기기, 가로 화면 기준.
설치 및 실기기 시험이 필요합니다. 모든 기기에서 작동을 보장하지 않습니다.
관리자 설정은 비밀번호가 없으므로 직원 입회형 운영을 전제로 합니다.
영수증 확인과 실제 경품 지급 확인은 직원이 수행해야 합니다.
PC 버전 데이터가 자동으로 이전되는 기능은 없습니다.
앱 삭제 또는 앱 데이터 삭제 시 기록이 사라집니다. 매일 CSV 기록을 내보내세요.

APK 생성 (인터넷 사용 가능한 Linux 또는 Windows WSL 환경)
1. Python 3.11, OpenJDK 17 및 아래 빌드 의존성 설치:
   git zip unzip autoconf automake libtool pkg-config cmake libffi-dev libssl-dev zlib1g-dev
2. python -m pip install buildozer "Cython<3"
3. 이 폴더에서 buildozer android debug
4. 성공하면 bin 폴더에 APK 생성.
첫 빌드에는 Android SDK/NDK 및 라이브러리 다운로드가 필요합니다.
빌드 도구 변경에 따라 버전 조정이 필요할 수 있습니다.

GitHub Actions를 사용하는 방법
이 폴더의 내용(main.py와 buildozer.spec 포함)을 저장소 최상위에 넣고,
.github/workflows/android.yml도 함께 추가합니다.
Actions → Build Android APK → Run workflow를 실행합니다.
성공한 실행의 Artifacts에서 hanaro-android-apk를 내려받습니다.
이 워크플로는 개발용 APK를 생성합니다. 실행마다 서명키가 달라질 수 있으므로
기존 앱 업데이트용으로 사용하기 전 고정된 서명키를 구성해야 합니다.
서명키 불일치로 삭제 후 재설치할 경우 내부 기록이 삭제됩니다.

로컬 PC 화면 확인
python -m pip install kivy==2.3.1
python main.py

구성
main.py: Android 대응 화면 / 저장창 / 키 입력
 draw_store.py: 수량, 무작위 추첨, 영구 저장, 초기화
buildozer.spec: APK 빌드 설정
 test_store.py: 추첨 로직 자동 테스트
assets/NotoSansKR.ttf 및 OFL.txt: 한글 폰트와 라이선스

참고 문서
https://kivy.org/doc/stable/guide/packaging-android.html
https://buildozer.readthedocs.io/
