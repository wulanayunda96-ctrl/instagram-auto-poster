# Wulan Auto Poster — GitHub Actions

Posting Instagram otomatis, tanpa approve. Jalan 2x sehari: 08:00 dan 19:00 EST.

## Cara pasang (sekali saja)
1. Buat repo baru di GitHub (gratis, Private boleh).
2. Upload semua isi folder ini ke repo itu.
3. Di repo: Settings → Secrets and variables → Actions → New repository secret.
   Nama: `IG_ACCESS_TOKEN`
   Isi: Page Access Token Whuland.ayunda (yang tadi dibuat di Graph API Explorer).
4. Di repo: Actions → "Auto Post Instagram" → Run workflow → Run workflow (test sekali).

Setelah itu jalan sendiri sesuai jadwal di queue.json. Untuk menambah post baru,
tambah file ke folder media/ dan satu entri baru di queue.json dengan status "ready".
