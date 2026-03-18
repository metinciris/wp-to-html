import os
import re
import html
import json
import shutil
import threading
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox
from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver

# --- AYARLAR VE VERSİYON ---
VERSION = "1.1"
SERVER_PORT = 8000
BASE_DIR = ""
MESSAGES = []

def clean_filename(filename):
    filename = re.sub(r'[\u200e\u200f\u202a\u202c\u202d\u202e]', '', filename)
    match = re.search(r'(.*?\.(jpg|jpeg|png|webp|gif|pdf|mp4|mov))', filename, re.IGNORECASE)
    return match.group(1).strip() if match else filename.strip()

def parse_whatsapp_txt(folder_path):
    txt_files = [f for f in os.listdir(folder_path) if f.endswith('.txt') and not f.endswith('.py')]
    if not txt_files: return []
    txt_file = max(txt_files, key=lambda f: os.path.getsize(os.path.join(folder_path, f)))
    
    raw = []
    pattern = re.compile(r'^(\d{1,2}\.\d{1,2}\.\d{2,4})\s+(\d{2}:\d{2})\s*-\s*(.*?):\s*(.*)$')
    filter_k = ["katıldı", "eklendi", "ayrıldı", "değişti", "şifrelidir", "oluşturdu"]

    with open(os.path.join(folder_path, txt_file), 'r', encoding='utf-8') as f:
        for line in f:
            line = line.replace('\u200e', '').strip('\n')
            if not line: continue
            match = pattern.match(line)
            if match:
                date, time, sender, text = match.groups()
                if any(k in text for k in filter_k): continue
                raw.append({'date': date, 'time': time, 'sender': sender, 'text': text, 'files': [], 'caption': ''})
            elif raw:
                raw[-1]['text'] += '\n' + line

    processed = []
    for m in raw:
        if '(dosya ekli)' in m['text']:
            parts = m['text'].split('(dosya ekli)')
            fname = clean_filename(parts[0].strip())
            m['caption'] = parts[1].lstrip(': ').strip()
            if os.path.exists(os.path.join(folder_path, fname)):
                m['files'] = [fname]
            processed.append(m)
        else:
            if processed and processed[-1]['files'] and len(m['text'].strip()) < 100:
                current_text = m['text'].strip()
                processed[-1]['caption'] = (processed[-1]['caption'] + " | " + current_text) if processed[-1]['caption'] else current_text
            else:
                m['caption'] = m['text'].strip()
                processed.append(m)
    return processed

# --- TASARIM VE STİL ---
COMMON_STYLE = """
    body { font-family: 'Inter', sans-serif; background: #f0f2f5; margin:0; color: #1c1e21; }
    .toolbar { background:#1a202c; color:white; padding:12px 20px; position:sticky; top:0; z-index:1000; display:flex; gap:12px; align-items:center; }
    .chat { padding:20px; max-width:1000px; margin:auto; display:flex; flex-direction:column; }
    .message-row { display:flex; width:100%; margin-bottom:4px; }
    .select-area { width:0; overflow:hidden; transition:0.3s; display:flex; align-items:center; justify-content:center; cursor:pointer; background:rgba(0,0,0,0.03); }
    .selection-mode .select-area { width:50px; border-right:1px solid #cbd5e0; }
    .bubble { background:white; padding:12px 16px; border-radius:12px; box-shadow:0 2px 4px rgba(0,0,0,0.05); max-width:85%; min-width:250px; border: 1px solid #e2e8f0; }
    .bubble.continued { border-top-left-radius: 4px; margin-top: -4px; }
    .selected .bubble { background:#ebf4ff !important; border:1px solid #3182ce; }
    .sender { font-weight:700; color:#2d3748; font-size:0.9em; margin-bottom:6px; display:block; }
    .hide-names .sender, .hide-names .sender-info { display: none !important; }
    .media-item { max-width: 100%; border-radius:8px; cursor:zoom-in; display:block; margin: 8px 0; border: 1px solid #edf2f7; }
    .caption-box { font-weight: 600; color:#2d3748; background: #f8fafc; padding: 10px; border-radius: 6px; border-left: 5px solid #4a5568; margin-top:8px; font-size:15px; }
    .info { font-size:0.75em; color:#718096; text-align:right; margin-top:8px; }
    
    #zoomOverlay { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.97); z-index:9999; flex-direction:column; justify-content:center; align-items:center; }
    #zoomImg { transition: transform 0.15s; max-width:92%; max-height:80%; object-fit: contain; cursor:grab; }
    #zoomCaption { color: #edf2f7; background: rgba(26,32,44,0.9); padding: 18px 35px; margin-top: 25px; border-radius: 12px; font-size: 1.2em; text-align:center; min-width:400px; border: 1px solid #4a5568; }
    .nav-btn { position:absolute; top:50%; background:rgba(255,255,255,0.08); color:white; border:none; padding:25px; cursor:pointer; font-size:45px; border-radius:50%; }
    .btn { background:#2d3748; color:white; border:1px solid #4a5568; padding:10px 18px; border-radius:8px; cursor:pointer; font-weight:600; font-size:13px; }
    .btn-save { background:#3182ce; border-color: #2b6cb0; }
    .btn-all { background:#38a169; border-color: #2f855a; }
"""

COMMON_SCRIPT = """
    let currentIdx = 0, scale = 1, gallery = [];
    function initGallery() {
        gallery = Array.from(document.querySelectorAll('.media-item')).map(el => ({
            src: el.src,
            text: el.closest('.bubble').querySelector('.caption-box')?.innerText || ""
        }));
    }
    function openZoom(src) {
        initGallery();
        currentIdx = gallery.findIndex(i => i.src === src);
        document.getElementById('zoomOverlay').style.display = 'flex';
        renderZoom();
    }
    function renderZoom() {
        const img = document.getElementById('zoomImg');
        img.src = gallery[currentIdx].src;
        document.getElementById('zoomCaption').innerText = gallery[currentIdx].text;
        document.getElementById('zoomCaption').style.display = gallery[currentIdx].text ? 'block' : 'none';
        scale = 1; img.style.transform = `scale(${scale})`;
    }
    function move(d) { currentIdx = (currentIdx + d + gallery.length) % gallery.length; renderZoom(); }
    document.getElementById('zoomOverlay').onwheel = (e) => {
        e.preventDefault();
        scale = Math.min(Math.max(0.5, scale * (e.deltaY > 0 ? 0.85 : 1.15)), 20);
        document.getElementById('zoomImg').style.transform = `scale(${scale})`;
    };
    
    function toggleNames(btn) { 
        const isHidden = document.body.classList.toggle('hide-names');
        btn.innerText = isHidden ? "İsimleri Göster" : "İsimleri Gizle";
    }

    function selectMsg(el) {
        if(document.body.classList.contains('selection-mode')) {
            let cb = el.querySelector('.msg-cb');
            cb.checked = !cb.checked;
            el.classList.toggle('selected', cb.checked);
        }
    }
    document.addEventListener('keydown', e => {
        if(document.getElementById('zoomOverlay').style.display === 'flex') {
            if(e.key === 'ArrowRight') move(1);
            if(e.key === 'ArrowLeft') move(-1);
            if(e.key === 'Escape') document.getElementById('zoomOverlay').style.display='none';
        }
    });
"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): return
    def do_GET(self):
        if self.path == '/':
            self.send_response(200); self.send_header('Content-type','text/html; charset=utf-8'); self.end_headers()
            html_content = f"""<html><head><meta charset="UTF-8"><style>{COMMON_STYLE}</style></head><body>
            <div class="toolbar">
                <div style="font-size:11px; color:#a0aec0; margin-right:10px;">V-{VERSION}</div>
                <button class="btn" onclick="toggleNames(this)">İsimleri Gizle</button>
                <button class="btn" onclick="document.body.classList.toggle('selection-mode')">Seçim Modu</button>
                <input type="text" placeholder="Hızlı ara..." oninput="filter(this.value)" style="padding:10px; border-radius:8px; border:none; flex-grow:1; background:#2d3748; color:white;">
                <button class="btn btn-save" onclick="exportVaka(false)">Vakayı Paketle</button>
                <button class="btn btn-all" onclick="exportVaka(true)">Herşeyi Paketle</button>
            </div><div class="chat">"""
            
            last_sender = ""
            for i, m in enumerate(MESSAGES):
                is_cont = (m['sender'] == last_sender)
                last_sender = m['sender']
                imgs = "".join([f'<img src="{fn}" class="media-item" onclick="openZoom(this.src)">' for fn in m['files']])
                cap = f'<div class="caption-box">{html.escape(m["caption"])}</div>' if m['caption'] else ""
                html_content += f"""<div class="message-row" onclick="selectMsg(this)">
                    <div class="select-area"><input type="checkbox" class="msg-cb" data-idx="{i}"></div>
                    <div class="bubble {"continued" if is_cont else ""}">
                        {f'<span class="sender">{html.escape(m["sender"])}</span>' if not is_cont else ""}
                        {imgs}{cap}
                        <div class="info"><span class="sender-info">{m['sender']} | </span>{m['date']} {m['time']}</div>
                    </div></div>"""
            
            html_content += f"""</div><div id="zoomOverlay" onclick="if(event.target==this)this.style.display='none'">
                <button class="nav-btn" style="left:30px" onclick="move(-1)">&#10094;</button><img id="zoomImg"><div id="zoomCaption"></div><button class="nav-btn" style="right:30px" onclick="move(1)">&#10095;</button>
            </div><script>{COMMON_SCRIPT}
                function filter(q){{ q=q.toLowerCase(); document.querySelectorAll('.message-row').forEach(r=>{{ r.style.display=r.innerText.toLowerCase().includes(q)?'flex':'none'; }}); }}
                function exportVaka(all) {{
                    let ids = all ? Array.from(document.querySelectorAll('.msg-cb')).map(c => parseInt(c.dataset.idx)) : Array.from(document.querySelectorAll('.msg-cb:checked')).map(c => parseInt(c.dataset.idx));
                    if(!ids.length) return alert("Mesaj seçilmedi!");
                    let t = prompt("Klasör Adı:"); if(!t) return;
                    fetch('/export', {{method:'POST', body: JSON.stringify({{title:t, indices:ids, hidden:document.body.classList.contains('hide-names')}})}}).then(()=>alert("Hazır!"));
                }}
            </script></body></html>"""
            self.wfile.write(html_content.encode('utf-8'))
        else:
            try:
                with open(os.path.join(BASE_DIR, self.path.lstrip('/')), 'rb') as f:
                    self.send_response(200); self.end_headers(); self.wfile.write(f.read())
            except: self.send_error(404)

    def do_POST(self):
        if self.path == '/export':
            content_length = int(self.headers['Content-Length']); data = json.loads(self.rfile.read(content_length).decode())
            safe_title = re.sub(r'\W+', '_', data['title']); vaka_dir = os.path.join(BASE_DIR, safe_title); os.makedirs(vaka_dir, exist_ok=True)
            selected = [MESSAGES[i] for i in data['indices']]
            for m in selected:
                for f in m['files']:
                    if os.path.exists(os.path.join(BASE_DIR, f)): shutil.copy2(os.path.join(BASE_DIR, f), os.path.join(vaka_dir, f))
            with open(os.path.join(vaka_dir, "index.html"), "w", encoding="utf-8") as f:
                h_cls = "hide-names" if data['hidden'] else ""; f.write(f"<html><head><meta charset='UTF-8'><style>{COMMON_STYLE} .toolbar{{display:none;}}</style></head><body class='{h_cls}'><div class='chat'><h2>{data['title']}</h2>")
                l_s = ""
                for m in selected:
                    is_c = (m['sender'] == l_s); l_s = m['sender']
                    imgs = "".join([f'<img src="{fn}" class="media-item" onclick="openZoom(this.src)">' for fn in m['files']])
                    cap = f'<div class="caption-box">{m["caption"]}</div>' if m['caption'] else ""
                    f.write(f'<div class="bubble {"continued" if is_c else ""}">{f"<span class=\'sender\'>{m["sender"]}</span>" if not is_c else ""}{imgs}{cap}<div class="info"><span class="sender-info">{m["sender"]} | </span>{m["date"]}</div></div>')
                f.write(f"</div><div id='zoomOverlay' onclick='if(event.target==this)this.style.display=\"none\"'><button class='nav-btn' style='left:30px' onclick='move(-1)'>&#10094;</button><img id='zoomImg'><div id='zoomCaption'></div><button class='nav-btn' style='right:30px' onclick='move(1)'>&#10095;</button></div><script>{COMMON_SCRIPT}</script></body></html>")
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"ok":true}')

def run():
    global BASE_DIR, MESSAGES
    BASE_DIR = filedialog.askdirectory(title="WhatsApp Klasörünü Seçin")
    if not BASE_DIR: return
    MESSAGES = parse_whatsapp_txt(BASE_DIR)
    if not MESSAGES: messagebox.showerror("Hata", ".txt dosyası bulunamadı!"); return
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("", SERVER_PORT), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    webbrowser.open(f'http://localhost:{SERVER_PORT}')

# --- ANA PENCERE ---
root = tk.Tk(); root.title("Toraks Vaka Arşivi"); root.geometry("500x400")
root.configure(bg="#f8fafc")

tk.Label(root, text="Toraks Vaka Arşivi", font=("Arial", 16, "bold"), bg="#f8fafc", fg="#1a202c", pady=20).pack()
tk.Label(root, text=f"Versiyon {VERSION}", font=("Arial", 9), bg="#f8fafc", fg="#718096").pack()

guide_text = """
KLAVUZ:
● 'Klasör Seç' butonuyla WhatsApp dışa aktarma klasörünü seçin.
● 'İsimleri Gizle' butonu butonu ile anonimlik sağlayabilirsiniz.
● 'Vakayı Paketle' seçili mesajları yeni bir vaka dosyası yapar.
● 'Herşeyi Paketle' tüm arşivi tek seferde yedekler.
"""
tk.Label(root, text=guide_text, justify="left", font=("Arial", 10), bg="#f8fafc", fg="#2d3748", padx=30).pack(pady=10)

tk.Button(root, text="BAŞLANGIÇ: KLASÖR SEÇ", command=run, bg="#3182ce", fg="white", font=("Arial", 11, "bold"), width=30, height=2, relief="flat").pack(pady=20)

root.mainloop()
