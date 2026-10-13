# 방문 IP 기록 사이트

관리자 화면의 접속 시간은 한국 시간(KST, UTC+9)으로 표시됩니다. 저장된 UTC 기록도 한국 시간으로 변환해서 표시합니다.

Python 3.12 이상, 외부 패키지 없이 실행합니다.

```bash
cd /workspace/reverse
read -rs -p '관리자 비밀번호(16자 이상): ' ADMIN_PASSWORD
export ADMIN_PASSWORD
python3 visitor_site.py
```

방문 페이지는 `/`, 관리자 기록은 `/admin`입니다. 로그인 사용자명은 `admin`, 비밀번호는 `ADMIN_PASSWORD`입니다. `/`에 GET 요청이 올 때 IP와 UTC 접속 시간이 SQLite에 기록됩니다. 최신 500건을 표시하며 30일이 지난 기록은 다음 방문 시 삭제됩니다. 기본 데이터 경로는 `/workspace/visitor-site-data/visits.sqlite3`이고 `VISITOR_DB`로 변경할 수 있습니다. 실제 운영 시 데이터 폴더를 영구 볼륨에 두세요.

기본 주소는 `127.0.0.1:8000`입니다. 운영 서버에서는 HTTPS 리버스 프록시 뒤에 두세요. 외부 직접 바인딩이 필요하면 `HOST=0.0.0.0`을 설정할 수 있습니다. 공개 배포에는 TLS와 관리자 경로 접근 제한을 적용하세요. 이 클라우드 작업 자체가 인터넷 공개 배포를 제공하지는 않습니다.

리버스 프록시를 사용할 때는 `TRUSTED_PROXIES`에 실제 프록시의 IP/CIDR만 쉼표로 구분해 지정하고, 프록시가 `X-Forwarded-For`에 실제 접속 IP를 추가하도록 설정하세요. 기본값은 전달 헤더를 신뢰하지 않습니다. 모든 주소를 신뢰하도록 설정하지 마세요.

IP는 VPN·공유기·프록시 주소일 수 있어 방문자의 신원을 특정하지는 못합니다. 방문 페이지에 기록 안내가 표시됩니다.

검증: `python3 -B -m unittest -v test_visitor_site.py`
