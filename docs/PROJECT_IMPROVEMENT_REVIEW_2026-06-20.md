# Bao cao cai tien du an Rehab AI Monitor

Ngay cap nhat: 2026-06-20

Tai lieu nay tong hop ket qua quet nhanh repo `Rehab-AI-Monitor-UI-new`, nham chi ra nhung diem da cai tien tot, nhung diem chua cai tien, rui ro con lai va huong uu tien tiep theo. Bao cao nay chi danh gia code/tai lieu hien co, khong thay doi du lieu tai khoan hay cac file runtime.

## 1. Tong quan hien trang

- `app.py` van la legacy monolith lon, hien co khoang **17,973 dong**. File nay van chua nhieu workflow quan trong: UI Streamlit legacy, xu ly video, Hugging Face sync, background jobs, phuc hoi/debug artifact va cac tab theo role.
- Du an da co buoc tach kien truc ro hon sang cac thu muc `auth/`, `backend/`, `controllers/`, `frontend/`, `video/`, `storage/`, `tests/`, `models/` va `views/`.
- Da co tai lieu dinh huong refactor/migration, dac biet la:
  - `docs/MVC_STRUCTURE.md`
  - `docs/REACT_BACKEND_MIGRATION_ROADMAP.md`
  - `docs/ops/PRODUCTION_READINESS.md`
- Frontend moi da co React/Vite shell va cac dashboard theo role, nhung Streamlit legacy van la be mat chinh cho nhieu workflow lam sang/nghien cuu.
- Data runtime va seed van chu yeu dua vao JSON file trong `database/` va mot so file JSON o root/runtime.

## 2. Diem da cai tien tot

- **Auth va session da duoc tach module**: cac phan password hashing, session version, auth service va metadata user da co module rieng va co unit test nen tang.
- **Upload/video security da co module rieng**: logic validate upload nam o `video/validation.py`, giup giam viec nhung logic bao mat truc tiep trong `app.py`.
- **CSS Streamlit da duoc tach khoi `app.py`**: phan style lon da chuyen sang `frontend/styles.py`, giam kich thuoc va do roi cua file entrypoint.
- **Co MVC boundary ban dau**: `controllers/`, `views/`, `models/`, `backend/` da tao duong bien de tiep tuc boc tach legacy code.
- **React/backend migration da khoi dong**: repo co React app, Node backend thu nghiem, role dashboards va tai lieu lo trinh parity voi Streamlit.
- **Kiem tra tinh cho loi Python quan trong dang sach**:
  - Lenh: `python -m ruff check app.py --select F401,F841,F821`
  - Ket qua: `All checks passed!`
- **Unit tests nen tang dang pass**:
  - Nhom test: password, video security, auth service metadata, sessions.
  - Ket qua: `10 passed`.

## 3. Diem chua cai tien va rui ro con lai

- **`app.py` van la nut that lon nhat**: file nay con qua nhieu trach nhiem, lam cho viec review, test, sua loi va migration rat ton suc.
- **Background jobs chua co queue chuan**: nhieu tac vu video/HF/analysis van dua vao thread, progress file, checkpoint va co che resume rieng le. Dieu nay gay kho theo doi timeout, retry, cancel va graceful shutdown.
- **Storage van chu yeu la JSON file**: du an chua co migration DB that su sang SQLite/Postgres, nen con rui ro ve tranh chap ghi file, audit, backup/restore va scale multi-instance.
- **Logging chua chuan hoa**: con nhieu `print(...)` trong `app.py` va utils. Nen thay bang logger co level, context va format thong nhat de de debug tren Hugging Face/production.
- **Debug/recovery UI con rai rac**: mot so block debug phuc vu chan doan video/HF van nam trong UI legacy, can tach thanh che do dev/admin hoac logging server-side.
- **React migration chua phu het workflow**: cac workflow benh nhan, bac si/KTV, NCV, admin con phan lon logic gia tri nam trong Streamlit legacy.
- **CI/build frontend can on dinh hon**: trong moi truong PowerShell hien tai, `npm run build` bi chan do `npm.ps1` execution policy, nhung `cmd /c npm run build` build thanh cong. CI nen chon shell on dinh va ghi ro lenh build.
- **Repo co nhieu artifact/runtime khong nen xem nhu source chinh**: `_push_tmp/`, `.cache/`, `debug.log`, `doctor_evaluations.json`, `video_list.json` o root la file tam/runtime/untracked trong lan quet nay, khong nen dua vao danh gia source chinh.

## 4. De xuat cai thien uu tien

### Uu tien 1: Boc tiep `app.py` theo workflow

- Tach HF sync, video processing, background analysis, progress/checkpoint va resume logic ra cac service/module rieng.
- Giu `app.py` o vai tro bootstrap + legacy adapter, tranh tiep tuc them workflow moi vao file nay.
- Moi lan tach can co test nho hoac smoke script de dam bao khong vo luong Streamlit hien co.

### Uu tien 2: Chuan hoa logging

- Thay dan `print(...)` bang `logging.getLogger(...)`.
- Dinh nghia format log co module, job id/video id neu co.
- Tach log nguoi dung co the doc trong UI khoi log ky thuat cho developer/admin.

### Uu tien 3: Chuyen storage JSON sang DB co kiem soat

- Lam script `json -> db --dry-run` truoc, co bao cao row count/checksum.
- Uu tien SQLite neu van single-instance; chon Postgres neu can multi-instance/audit-heavy.
- Co backup/rollback report truoc khi ghi migrate that.

### Uu tien 4: Hoan thien React/backend parity

- Dua cac man hinh ket qua AI, frame gallery, bieu do, schedules, admin audit va clinical evaluation sang API/React tung slice nho.
- Giu rule scope/auth guard o backend, khong dua logic bao mat vao frontend.
- Cac thao tac nguy hiem nhu xoa/reset/revoke/export can confirm, audit log va backup neu co ghi/xoa du lieu.

### Uu tien 5: Bo sung CI smoke

- CI nen chay toi thieu:
  - `python -m ruff check app.py --select F401,F841,F821`
  - unit tests Python hien co
  - frontend build qua shell khong bi chan execution policy
  - secret scan va dependency audit co ban
- Neu workflow UI thay doi, them Playwright smoke cho login/dashboard/upload/result.

## 5. Kiem tra da thuc hien trong lan quet

| Hang muc | Lenh/Kiem tra | Ket qua |
| --- | --- | --- |
| So dong `app.py` | Doc bang Python `splitlines()` | `17,973` dong |
| Ruff loi quan trong | `python -m ruff check app.py --select F401,F841,F821` | Pass |
| Unit tests nen tang | `python -m pytest --basetemp=.cache\\pytest-report-review -p no:cacheprovider tests/unit/test_passwords.py tests/unit/test_video_security.py tests/unit/test_auth_service_metadata.py tests/unit/test_sessions.py -q` | `10 passed` |
| Frontend build local | `npm run build` | Bi chan boi PowerShell execution policy voi `npm.ps1` |
| Frontend build local qua cmd | `cmd /c npm run build` | Pass; Vite build thanh cong |

## 6. Ket qua quet chi tiet bo sung

### 6.1. Diem nong trong `app.py`

Ket qua quet AST cho thay `app.py` hien co **405 function/class**. Cac ham dai nhat nen duoc uu tien tach module:

| Ham | Dong bat dau | Do dai uoc tinh | Nhan xet |
| --- | ---: | ---: | --- |
| `_noi_dung_frames_day_du` | 14,726 | 989 dong | UI frame gallery + recovery, nen tach view/service artifact |
| `xu_ly_video_day_du` | 7,350 | 959 dong | Core video processing, nen tach job/service rieng |
| `_hien_thi_tab_phan_tich_noi_dung` | 12,259 | 918 dong | UI phan tich lon, nen tach thanh nhieu component/view |
| `_render_main_tab_content` | 16,936 | 791 dong | Dispatcher/tab legacy, nen dua ve controller/view boundary |
| `bat_dau_phan_tich_background` | 10,132 | 588 dong | Background analysis orchestration, nen thay bang job queue |
| `_noi_dung_danh_sach_video_fragment` | 16,308 | 565 dong | UI danh sach video, nen tach role-specific view |
| `thread_target` | 10,215 | 486 dong | Worker long-running nam trong ham, nen tach module job |
| `_render_frame_grid` | 15,242 | 420 dong | Render frame HTML lon, nen tach frontend/view helper |
| `_noi_dung_khu_vuc_phan_tich` | 9,308 | 409 dong | Progress/status UI, nen tach state presenter |
| `xu_ly_frame` | 6,697 | 399 dong | Per-frame CV logic, nen tach video/pose service |

### 6.2. Mat do log/debug va silent handling

- `app.py` con khoang **151** dong co `print(`. Nen thay dan bang logger co level (`info`, `warning`, `error`, `debug`) va context video/job.
- `app.py` co khoang **320** dong chua `pass`, trong do nhieu `except: pass`/`except Exception: pass`. Nen uu tien thay silent catch bang log debug/warning o cac workflow HF sync, video processing, auth callback va artifact recovery.
- Co **2** vi tri `st.code(traceback.format_exc())` dang hien traceback ra UI. Can dam bao chi hien voi admin/dev mode, tranh lo thong tin ky thuat cho nguoi dung thuong.
- Khong thay `TODO`/`FIXME` dang ke trong `app.py`, nghia la no ky thuat chu yeu nam o cau truc va workflow dai, khong phai marker TODO.

### 6.3. Kich thuoc module ngoai `app.py`

| Khu vuc | So file Python | Tong dong uoc tinh | Nhan xet |
| --- | ---: | ---: | --- |
| `utils/` | 6 | 5,355 | `demo_ui.py` rat lon, can tiep tuc tach UI/design helper |
| `frontend/` | 16 | 2,197 | Da tach duoc nhieu view/style, tiep tuc dua UI legacy sang day |
| `scripts/` | 13 | 2,046 | Nhieu script van hanh/tac vu du lieu, can tai lieu hoa lenh an toan |
| `controllers/` | 11 | 441 | Controller boundary da co nhung con mong so voi legacy trong `app.py` |
| `auth/` | 5 | 320 | Kich thuoc gon, co test nen giu pattern nay cho module moi |
| `video/` | 3 | 306 | Nen dua tiep video processing/CV logic tu `app.py` vao khu vuc nay |
| `storage/` | 3 | 90 | Con nho, can mo rong neu lam migration JSON -> DB |

### 6.4. File/ten goi can xem lai

- `utils/demo_ui.py` co kich thuoc lon, nen tach tiep neu con chua CSS/UI helper cu.
- `utils/pose_classfier_untils.py` co ten typo (`classfier`, `untils`) va kich thuoc rat nho. Can kiem tra co con can giu lam compatibility shim hay co the xoa/doi ten sau khi xac minh import.
- `_push_tmp/`, `.cache/`, `.ruff_cache`, `.pytest_cache`, `debug.log` va cac JSON runtime o root khong nen dua vao danh gia source chinh hoac commit neu khong co chu dich.

## 7. Doi chieu voi `quynhphuong1209/Rehab-AI-Monitor`

Nguon doi chieu: GitHub repo `quynhphuong1209/Rehab-AI-Monitor`, branch `main`, commit `eec0193`.

### 7.1. So lieu so sanh nhanh

| Hang muc | Repo hien tai `Rehab-AI-Monitor-UI-new` | Repo GitHub `Rehab-AI-Monitor` | Nhan xet |
| --- | ---: | ---: | --- |
| Dong `app.py` | 17,973 | 9,934 | Ban GitHub da giam monolith manh hon |
| Function/class trong `app.py` | 405 | 389 | So symbol gan tuong duong, nhung ban GitHub co ham ngan hon ro |
| `print(` trong `app.py` | 151 | 111 | Ban GitHub da giam log ad hoc hon |
| Dong co `pass` trong `app.py` | 320 | 179 | Ban GitHub it silent handling hon |
| `st.code(traceback.format_exc())` | 2 | 2 | Ca hai can guard bang admin/dev mode |
| File unit test | 4 | 26 | Ban GitHub co coverage rong hon |
| File trong `backend/` | 3 | 14 | Ban GitHub backend hoa workflow tot hon |
| File trong `video/` | 3 | 7 | Ban GitHub tach video/CV pipeline tot hon |
| File trong `docs/` | 20 | 37 | Ban GitHub co nhieu repair/production docs hon |

### 7.2. Diem cai tien hon cua repo GitHub kia

| Nhom | Diem cai tien | Nen hoc theo nhu the nao |
| --- | --- | --- |
| Kien truc backend | Co `backend/main.py`, `backend/analysis_jobs.py`, `backend/frame_gallery.py`, `backend/hf_workflow.py`, `backend/repository.py` | Lay y tuong API/job boundary, khong copy nguyen file vao repo hien tai |
| Video pipeline | Co `video/processing.py`, `video/jobs.py`, `video/metrics.py`, `video/io.py` | Dua dan `xu_ly_video_day_du`, `xu_ly_frame`, metric/report logic ra `video/` |
| UI Streamlit | Co thu muc `ui/` cho admin, doctor, researcher, patient, frames, reminders, layout | Tach cac tab role trong `app.py` sang view module tuong tu |
| React web | Co `web/` TypeScript rieng voi script `lint`, `build`, `e2e:smoke` | Bo sung type-check/e2e smoke cho frontend hien tai hoac chon duong hop nhat voi `frontend/react_app` |
| Job lifecycle | Backend README mo ta analysis job history, cancel, retry, rerun, four-step progress | Thay thread/progress ad hoc bang job API co run_id/status/steps |
| HF sync va ML workflow | Co endpoint/status/job cho HF sync va pose classifier | Tach HF sync/pose classifier khoi UI legacy, dua vao backend/service |
| Storage migration | Co `docs/JSON_TO_SQLITE_MIGRATION.md` va `scripts/migrate_json_to_sqlite.py` | Ap dung dry-run migration co backup/rollback truoc khi doi runtime storage |
| Test coverage | Co test cho access, schema, storage, video jobs, video metrics, backend API, SQLite migration | Mo rong test theo nhom rui ro thay vi chi test auth/upload/session |
| Production gate | Co production checklist, repair plans, bug report docs | Dung lam khung checklist truoc khi deploy web cho nguoi dung that |

### 7.3. Diem repo hien tai dang co va can giu

| Nhom | Gia tri hien co | Ly do can giu |
| --- | --- | --- |
| MVC Streamlit moi | `controllers/`, `views/`, `models/navigation.py`, `models/auth.py` | Da tao boundary de bootstrap app va role dispatch ro hon |
| Frontend role shell | `frontend/roles/*`, `frontend/ui/*`, `frontend/auth/*` | Da co cau truc dashboard/bridge gan voi Streamlit hien tai |
| Style extraction | `frontend/styles.py` | Da giam tai `app.py`, nen tiep tuc tach CSS/UI vao day hoac module view |
| Node backend thu nghiem | `backend_node/` | Co the giu lam sandbox API nhe neu van phuc vu React shell |
| Auth/session/upload hardening | `auth/`, `backend/auth_service.py`, `video/validation.py`, unit tests pass | Day la nen tang an toan da on, khong nen thay the bang copy thang tu repo khac |
| Bao cao hien tai | `docs/PROJECT_IMPROVEMENT_REVIEW_2026-06-20.md` | Lam noi tong hop roadmap va doi chieu, nen cap nhat tiep sau moi phase refactor |

### 7.4. Khuyen nghi ap dung vao web hien tai

1. **Khong copy big-bang tu repo GitHub kia.** Hai repo da lech kien truc: repo hien tai co `controllers/views/frontend` rieng, trong khi repo kia co `ui/web/backend` rieng. Nen lay pattern tot va migrate theo slice.
2. **Uu tien tach video processing truoc.** Dua `xu_ly_video_day_du`, `xu_ly_frame`, metrics va artifact helpers sang `video/processing.py`, `video/metrics.py`, `video/io.py`. Giu wrapper trong `app.py` de khong vo UI hien co.
3. **Tach HF sync/job orchestration tiep theo.** Tao service cho HF sync va analysis job lifecycle, huong den status/history/cancel/retry/rerun nhu repo GitHub kia.
4. **Tach UI role tabs sau khi service on.** Dua cac ham UI dai nhu `_render_main_tab_content`, `_noi_dung_danh_sach_video_fragment`, `_noi_dung_frames_day_du` sang view module theo role/artifact.
5. **Mo rong tests theo nhom rui ro.** Them test cho access/scope, schema JSON, storage read/write, video jobs, metrics, path security, backend/API contracts va SQLite migration dry-run.
6. **Bo sung production gate.** Dua checklist tu repo GitHub kia vao docs hien tai: secret scan, PII scan, backup/rollback, dependency audit, frontend build, e2e smoke.
7. **Chuan hoa frontend build.** Ghi ro trong docs/CI: PowerShell co the chan `npm.ps1`, lenh local on dinh la `cmd /c npm run build`; CI nen dung shell khong bi policy chan.

### 7.5. De xuat thu tu roadmap sau doi chieu

| Thu tu | Viec nen lam | Ly do |
| ---: | --- | --- |
| 1 | Tao test baseline cho video metrics/path/security truoc khi tach | Giam rui ro sai so AI/clinical khi refactor |
| 2 | Tach `video/processing` va `video/metrics` | Giam nhanh kich thuoc `app.py`, tac dong truc tiep diem nong 959/399 dong |
| 3 | Tach HF sync va analysis job lifecycle | Xu ly nut that thread/progress/checkpoint |
| 4 | Them JSON-to-SQLite dry-run migration | Giam rui ro data runtime JSON |
| 5 | Tach frame gallery/result UI sang view module | Giam cac ham UI 989/918/791 dong |
| 6 | Bo sung CI gate va e2e smoke | Dam bao moi lan tach deu co guard |

## 8. Ket luan

Du an da tien bo ro ve cau truc: da co module auth/session, upload validation, MVC boundary, React/Vite shell, tai lieu migration va test nen tang. Tuy nhien, nut that lon nhat van la `app.py` legacy, storage JSON, background jobs va migration React chua hoan tat.

Huong di nen la tiep tuc boc tach theo workflow nho, co test kem theo moi slice, dong thoi chuan hoa logging va dua storage sang DB co dry-run/rollback. Cach lam nay giu on dinh app hien tai trong khi van giam dan rui ro ky thuat.
