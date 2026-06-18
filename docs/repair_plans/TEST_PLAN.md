# Test Plan - Main Phase to Phase 6

Muc tieu: sua giao dien va harden he thong theo thu tu phase ma khong lam mat noi dung tab, subtab, nut bam, tinh nang hoac du lieu dang hien thi.

## Main Phase - UI Containment

Pham vi:

- Login/register/Google ID screen.
- Theme injection tu `utils/demo_ui.py`.
- Khong thay doi schema JSON hoac noi dung tab sau login.

Checks:

```powershell
rg -n "pro_ui_theme|inject_pro_ui_theme" app.py utils
rg -n "auth_card_streamlit|auth-shell|inject_streamlit_skin" app.py utils\demo_ui.py
python -m py_compile app.py utils\demo_ui.py
```

Current implementation notes:

- UI theme is injected from `utils/demo_ui.py`.
- Login card uses Streamlit container key `auth_card_streamlit` so CSS stays scoped.
- Legacy `utils/pro_ui_theme.py` is no longer imported.

Manual smoke:

- Mo trang login o dark va light mode.
- Dam bao khong con CSS hien nhu text tren man hinh.
- Thu chon 4 vai tro: Benh nhan, Bac si / KTV PHCN, Nghien cuu vien, Quan tri vien.
- Thu 3 tab login: Dang nhap, Dang ky, Google ID.
- Sau login, cac tab/subtab va du lieu hien nhu truoc.

## Phase 0 - Containment and Baseline

Checks:

```powershell
git status --short
git remote -v
git log --oneline -n 20
git ls-files database debug_files README.md scripts
rg -n "logged_in_user|logged_in_role" app.py scripts README.md docs
rg -n "HF_TOKEN|HF_DATASET_ID|token=\{HF_TOKEN\}|\?token=" app.py scripts README.md
rg -c "unsafe_allow_html=True" app.py
rg -n "except:\s*$" app.py
rg -n "except Exception:\s*pass" app.py
python -m py_compile app.py utils\reference_utils.py utils\pose_classifier_utils.py utils\checkpoint_utils.py scripts\sync_from_hf.py scripts\sync_data_and_report.py scripts\reset_data.py
```

Data rule:

- Backup `database/` va `debug_files/` truoc moi phase co mutation.
- Khong commit backup runtime.

## Phase 1A - Immediate Leak Blocking

Checks:

```powershell
rg -n "logged_in_user|logged_in_role" app.py scripts README.md
rg -n "\?logged_in_user=|&logged_in_role=" .
rg -n "token=\{HF_TOKEN\}|\?token=|HF_TOKEN.*st\.|st\..*HF_TOKEN|cloud_url" app.py
python -m py_compile app.py scripts\sync_data_and_report.py
```

Expected:

- Query params khong the dang nhap thay credential/OIDC.
- Script/README khong tao link bypass.
- Token khong render ra UI/DOM.
- App khong fallback ve dataset ca nhan hard-code khi thieu `HF_DATASET_ID`.

## Phase 1B - Security Hardening

Checks:

```powershell
rg -n "admin123|bs123|ncv123|plain" app.py database scripts
rg -n "\?token=|token=\{HF_TOKEN\}|HF_TOKEN.*quote|cloud_url" app.py
rg -n "SimpleHTTPRequestHandler|Access-Control-Allow-Origin|translate_path" app.py
rg -n "unsafe_allow_html=True" app.py
python -m py_compile app.py
```

Manual smoke:

- Payload `<script>alert(1)</script>` trong comment/plan/name khong chay va khong pha UI.
- Video cloud/local khong lo token trong source/network URL.

## Phase 2 - Access Stability

Checks:

```powershell
rg -n "maxUploadSize|MAX_FILE_SIZE_MB|MAX_UPLOAD_SIZE_MB|getbuffer\(|-threads 0|subprocess\.Popen" app.py Dockerfile .streamlit
rg -n "enableCORS=false|enableXsrfProtection=false" Dockerfile .streamlit
rg -n "extractall|ZipInfo|infolist|check_and_extract_frames_zip" app.py
python -m py_compile app.py scripts\sync_from_hf.py
```

Expected:

- File lon bi reject truoc khi doc buffer.
- Path traversal va ZIP traversal bi reject.
- Default sync khong ghi de `users.json`.
- Docker production khong tat CORS/XSRF.

## Phase 3 - Data Quality

Checks:

```powershell
rg -n "sha256|hash_password|verify_password|hash_version|argon2|bcrypt" app.py requirements.txt
rg -n "save_data\(|doc_lock_save_data\(|load_data\(" app.py
rg -n "except:\s*$|except Exception:\s*pass|except Exception:\s*$" app.py scripts utils
python -m py_compile app.py
pytest tests/
```

Expected:

- Password moi dung PBKDF2-SHA256 built-in, hash SHA-256 cu duoc nang cap sau login thanh cong.
- `storage/json_store.py` cung cap atomic read/write/update lam nen cho refactor storage.
- Test suite co fixtures sanitize.

## Phase 4 - Frontend UX

Checks:

```powershell
rg -n "<style|unsafe_allow_html=True|!important|scale\(2\.2\)|\.stButton > button|\* \{" app.py assets utils
rg -n "window\.parent|document\.querySelector|MutationObserver|setInterval|components\.html" app.py
python -m py_compile app.py utils\demo_ui.py
```

Manual smoke:

- Desktop 1920x1080 va mobile narrow khong overlap.
- Role patient/doctor-NCV/admin van thay dung tab/subtab.
- Light/dark mode khong bi chu trang tren nen trang.

## Phase 5 - Architecture

Checks:

```powershell
python -m py_compile app.py auth\*.py storage\*.py cloud\*.py video\*.py ui\*.py
pytest tests/
rg -n "threading\.Thread\(|while True|start\(|upload_file|download|os\.makedirs|save_data\(" app.py auth storage cloud video ui
```

Expected:

- `app.py` chi con setup, startup va route.
- Auth/storage/cloud/video/ui duoc tach theo slice nho, moi slice co smoke/test.
- Da co scaffold `auth/`, `storage/`, `models/`, `jobs/` de tach dan khong pha monolith.

## Phase 6 - Production Ready

Checks:

```powershell
pytest tests/
python -m py_compile app.py scripts\*.py
rg -n "sqlite|postgres|migration|dry-run|rollback|audit|retention|incident" docs scripts storage models
```

Expected:

- Migration JSON -> DB co backup, dry-run, rollback report.
- CI/CD chay compile, tests, secret scan va Docker smoke.
- Background jobs co status, retry/backoff, shutdown.
- Privacy/compliance workflow co audit, retention va incident response.
- Da co `.github/workflows/ci.yml` va `docs/ops/PRODUCTION_READINESS.md` lam nen van hanh.
