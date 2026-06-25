# Full Patient Exports

This folder is intentionally not committed with raw patient export data because the latest export contains large videos, frame archives, and overlay frames that are too large for GitHub.

Latest local export:

- `full_web_exact_web_overlay_frames_20260624_173500`
- Verified local source size: `57,338` files, `23,257,472,818` bytes
- Local source path: `D:\Downloads\Rehab-AI-Monitor-UI-new\processed_results\full_patient_exports\full_web_exact_web_overlay_frames_20260624_173500`

Full data archive on Hugging Face Dataset:

https://huggingface.co/datasets/quynhphuong1209/Rehab-AI-Monitor-2026-data/tree/main/archives/full_patient_exports/full_web_exact_web_overlay_frames_20260624_173500

Archive files:

| File | Bytes | SHA256 |
| --- | ---: | --- |
| `BN01_cao_thi_thuong.tar` | `1,637,786,112` | `728f53f6b32044504be11ded7a13d5cdcca2e44be67f8298e1455b3f23fa4068` |
| `BN02_hoang_hanh_nguyen.tar` | `6,317,180,928` | `eff40907365f8e7c31e92a1189c8e49db75eca2f800bb5ecea121af968afa1e0` |
| `BN03_nguyen_thi_nga.tar` | `4,996,451,328` | `fa0a4448b1f445827829484c008a6d85d357ca3186ea193e103bf570fee8a3d7` |
| `BN04_vu_thi_hoa.tar` | `3,410,356,224` | `464ccc34a64f9efb96e902cf2d997fa147dff518ab98a0807fb2a16593ebcd8d` |
| `database_snapshots.tar` | `619,520` | `46c0701d62a085cc6942b155e46710caa6cb8cee4eb444d0668ccedf81a2a4dd` |
| `full_patient_exports_archive_manifest.json` | `1,575` | See HF Dataset |

Notes:

- Raw web/backend data was not modified for this export.
- GitHub stores this README and the small pointer manifest only.
- Hugging Face Dataset stores the full archive payload.
