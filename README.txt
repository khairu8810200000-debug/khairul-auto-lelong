KHAIRUL AUTO LELONG — pakej dipertingkat (Python Flask)

FUNGSI
- Daftar akaun / log masuk pengguna
- Iklan kereta dengan muat naik gambar
- Carian kereta
- Bidaan dengan rekod bidaan tertinggi
- Kemas kini bidaan automatik setiap 5 saat pada halaman kereta (polling)
- Panel admin untuk mengaktifkan / menutup iklan
- Fail konfigurasi untuk hosting Render, termasuk storan persisten untuk database dan gambar

JALANKAN DI WINDOWS
1. Extract ZIP ke folder baharu.
2. Buka CMD dalam folder tersebut.
3. Jalankan:
   python -m pip install -r requirements.txt
   python app.py
4. Buka http://127.0.0.1:5000

ADMIN DEMO
username: admin
password: Admin123!
Tukar akaun demo sebelum melancarkan kepada orang ramai. Jika database lama digunakan, akaun admin sedia ada tidak akan ditetapkan semula.

CARA HOSTING ONLINE (ANDA PERLU AKAUN HOSTING)
1. Buat akaun GitHub dan cipta repository baharu.
2. Muat naik fail dalam ZIP ini ke repository.
3. Dalam Render, pilih New > Blueprint dan sambungkan repository tersebut. Render akan membaca render.yaml.
4. Tunggu deployment selesai; Render akan beri URL awam.
5. Uji pendaftaran, log masuk, muat naik gambar, bidaan dan admin.
Nota: deployment online tidak dibuat secara automatik kerana memerlukan akaun hosting/GitHub anda.

PENTING
- Versi ini mengemas kini paparan bidaan setiap 5 saat; ia bukan WebSocket masa nyata tulen.
- Ini masih prototaip. Sebelum menerima wang atau membuka lelong awam, tambah pengesahan identiti, semakan hak milik/kuasa jualan, CSRF protection menyeluruh, had percubaan log masuk, audit trail, notifikasi, syarat lelong, pemprosesan pembayaran yang patuh dan ujian keselamatan.
- Pastikan anda hanya mengiklankan kenderaan yang anda berhak menjual atau lelongkan. Jangan dedahkan maklumat peribadi peminjam.
