#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except Exception:
    tk = None
    filedialog = None
    messagebox = None


DATE_LINE_RE = re.compile(r'^(\d{1,2}\.\d{1,2}\.\d{4}) (\d{1,2}:\d{2}) - (.*)$')
FILENAME_RE = re.compile(
    r'^(?P<name>.+?\.(?:jpg|jpeg|png|gif|webp|bmp|mp4|mov|m4v|avi|mkv|webm|pdf|doc|docx|xls|xlsx|ppt|pptx|txt|csv|mp3|ogg|opus|wav))'
    r'(?:\s*\((?:dosya ekli)\))?(?:\s+(?P<rest>.*))?$',
    re.IGNORECASE
)

SYSTEM_PATTERNS = [
    'bir grup bağlantısıyla katıldı',
    'gruba eklendi',
    'kişisini ekledi',
    'changed their phone number',
    'numarasını',
    'Mesajlar ve aramalar uçtan uca şifrelidir',
]


def gui_available() -> bool:
    return tk is not None and filedialog is not None


def show_info(title: str, text: str):
    if messagebox is not None:
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            messagebox.showinfo(title, text)
            root.destroy()
            return
        except Exception:
            pass
    print(text)


def show_error(title: str, text: str):
    if messagebox is not None:
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            messagebox.showerror(title, text)
            root.destroy()
            return
        except Exception:
            pass
    print(text, file=sys.stderr)


def choose_folder_dialog() -> Path | None:
    if not gui_available():
        return None
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    chosen = filedialog.askdirectory(title='WhatsApp sohbet klasörünü seçin')
    root.destroy()
    if not chosen:
        return None
    return Path(chosen)


def try_read_text(path: Path) -> str:
    encodings = ['utf-8-sig', 'utf-8', 'utf-16', 'cp1254', 'latin-1']
    last_error = None
    for enc in encodings:
        try:
            return path.read_text(encoding=enc)
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f'Metin dosyası okunamadı: {path} ({last_error})')


def clean_text(s: str) -> str:
    if s is None:
        return ''
    return s.replace('\u200e', '').replace('\ufeff', '').replace('\u202a', '').replace('\u202c', '').strip()


def is_system_text(text: str) -> bool:
    t = clean_text(text)
    if not t:
        return False
    return any(p in t for p in SYSTEM_PATTERNS)


def looks_like_attachment(text: str):
    t = clean_text(text)
    if not t or t == '<Medya dahil edilmedi>':
        return None
    m = FILENAME_RE.match(t.splitlines()[0])
    if not m:
        return None
    name = clean_text(m.group('name'))
    rest = clean_text(m.group('rest') or '')
    extra_lines = t.splitlines()[1:]
    caption_parts = []
    if rest:
        caption_parts.append(rest)
    if extra_lines:
        caption_parts.extend(extra_lines)
    caption = '\n'.join([x for x in caption_parts if x is not None]).strip()
    return {'filename': name, 'caption': caption}


def parse_chat(text: str):
    lines = text.splitlines()
    raw_messages = []
    current = None

    for line in lines:
        m = DATE_LINE_RE.match(line)
        if m:
            if current:
                raw_messages.append(current)
            date_str, time_str, remainder = m.groups()
            current = {
                'date_str': date_str,
                'time_str': time_str,
                'raw': remainder,
                'continuations': []
            }
        else:
            if current is None:
                continue
            current['continuations'].append(line)

    if current:
        raw_messages.append(current)

    messages = []
    for idx, item in enumerate(raw_messages):
        date_str = item['date_str']
        time_str = item['time_str']
        raw = item['raw']
        full = raw
        if item['continuations']:
            full += '\n' + '\n'.join(item['continuations'])
        full = full.rstrip()

        sender = None
        text_part = full

        if ': ' in raw:
            possible_sender, first_text = raw.split(': ', 1)
            sender = clean_text(possible_sender)
            text_part = first_text
            if item['continuations']:
                text_part += '\n' + '\n'.join(item['continuations'])

        try:
            dt = datetime.strptime(f'{date_str} {time_str}', '%d.%m.%Y %H:%M')
            iso = dt.isoformat()
            date_key = dt.strftime('%Y-%m-%d')
            date_label = dt.strftime('%d.%m.%Y')
        except Exception:
            iso = f'{date_str}T{time_str}'
            date_key = date_str
            date_label = date_str

        body = clean_text(text_part)
        msg = {
            'id': idx + 1,
            'datetime': iso,
            'date': date_key,
            'date_label': date_label,
            'time': time_str,
            'sender': sender,
            'text': body,
            'kind': 'text',
            'file_name': None,
            'file_rel': None,
            'file_exists': False,
            'file_type': None,
            'caption': '',
        }

        if sender is None or is_system_text(body):
            msg['kind'] = 'system'
            messages.append(msg)
            continue

        if body == 'Bu mesaj silindi':
            msg['kind'] = 'deleted'
            messages.append(msg)
            continue

        if body == '<Medya dahil edilmedi>':
            msg['kind'] = 'omitted'
            messages.append(msg)
            continue

        attachment = looks_like_attachment(body)
        if attachment:
            msg['kind'] = 'attachment'
            msg['file_name'] = attachment['filename']
            msg['caption'] = attachment['caption']
            messages.append(msg)
            continue

        messages.append(msg)

    return messages


def detect_file_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}:
        return 'image'
    if ext in {'.mp4', '.mov', '.m4v', '.avi', '.mkv', '.webm'}:
        return 'video'
    if ext == '.pdf':
        return 'pdf'
    if ext in {'.mp3', '.ogg', '.opus', '.wav'}:
        return 'audio'
    return 'file'


def build_media_index(folder: Path):
    media_index = {}
    for p in folder.iterdir():
        if not p.is_file():
            continue
        if p.suffix.lower() in {'.txt', '.html', '.htm', '.py', '.bat'}:
            continue
        media_index[p.name.lower()] = p
    return media_index


def enrich_with_media(messages, folder: Path):
    media_index = build_media_index(folder)
    for msg in messages:
        if msg['kind'] != 'attachment' or not msg['file_name']:
            continue
        p = media_index.get(msg['file_name'].lower())
        if p and p.exists():
            msg['file_exists'] = True
            msg['file_rel'] = f"./{p.name}"
            msg['file_type'] = detect_file_type(p)
        else:
            msg['file_exists'] = False
            msg['file_rel'] = None
            msg['file_type'] = 'missing'
    return messages


HTML_TEMPLATE = r"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root{
    --bg:#0b141a; --panel:#111b21; --chat-bg:#0b141a;
    --bubble-in:#202c33; --bubble-out:#005c4b; --text:#e9edef;
    --muted:#8696a0; --line:#233138; --sys:#1f2c34;
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0;background:var(--bg);color:var(--text);font-family:Segoe UI,Roboto,Arial,sans-serif}
  body{display:flex;flex-direction:column;min-height:100vh}
  .topbar{position:sticky;top:0;z-index:10;background:var(--panel);border-bottom:1px solid var(--line);padding:12px 14px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
  .title-wrap{display:flex;flex-direction:column;gap:4px;min-width:260px}
  .title{font-size:18px;font-weight:700}
  .meta{font-size:12px;color:var(--muted)}
  .controls{display:flex;gap:8px;flex:1;flex-wrap:wrap}
  .controls input,.controls button{background:#0f171c;border:1px solid var(--line);color:var(--text);border-radius:10px;padding:10px 12px}
  .controls input{min-width:220px;outline:none}
  .controls button{cursor:pointer}
  .app{display:flex;justify-content:center;padding:18px}
  .chat{width:min(100%,980px);background:radial-gradient(rgba(255,255,255,0.03) 1px, transparent 1px) 0 0/14px 14px,var(--chat-bg);border:1px solid var(--line);border-radius:16px;padding:16px;min-height:70vh}
  .date-sep{position:sticky;top:70px;z-index:3;display:flex;justify-content:center;margin:14px 0}
  .date-sep span{background:rgba(17,27,33,.92);color:#d1d7db;padding:6px 10px;border-radius:8px;font-size:12px;border:1px solid var(--line)}
  .msg-row{display:flex;margin:6px 0}
  .msg-row.in{justify-content:flex-start}
  .bubble{max-width:min(78%,760px);border-radius:10px;padding:8px 10px 6px 10px;box-shadow:0 1px 0 rgba(0,0,0,.2);overflow-wrap:anywhere;white-space:pre-wrap;line-height:1.35}
  .bubble.in{background:var(--bubble-in)}
  .bubble.system{background:var(--sys);margin:0 auto;max-width:min(92%,860px);color:#d1d7db;border:1px solid var(--line);text-align:center}
  .sender{font-size:12px;font-weight:700;color:#7ad7ff;margin-bottom:4px}
  .text{font-size:14px}
  .meta-line{display:flex;gap:8px;justify-content:flex-end;align-items:center;margin-top:4px;font-size:11px;color:#d1d7dbb8}
  .file-card{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:10px;margin-top:4px}
  .file-name{font-weight:600}
  .file-type{font-size:12px;color:var(--muted);margin-top:3px}
  img.media{max-width:100%;border-radius:10px;display:block;cursor:pointer;margin-top:4px}
  video.media,audio.media{width:100%;border-radius:10px;display:block;margin-top:4px;background:#000}
  .caption{margin-top:6px}
  .deleted,.omitted{font-style:italic;color:#b7c4cc}
  .missing{color:#ffb4b4}
  .load-more{display:block;margin:20px auto 6px auto;background:#0f171c;border:1px solid var(--line);color:var(--text);padding:10px 14px;border-radius:10px;cursor:pointer}
  .footer-note{margin-top:16px;text-align:center;color:var(--muted);font-size:12px}
  a{color:#8bd3ff}
  mark{background:#ffe082;color:#000;padding:0 2px;border-radius:3px}
  .modal{position:fixed;inset:0;background:rgba(0,0,0,.85);display:none;align-items:center;justify-content:center;z-index:20;padding:20px}
  .modal img{max-width:95vw;max-height:92vh;border-radius:12px}
  .stats{font-size:12px;color:var(--muted)}
</style>
</head>
<body>
  <div class="topbar">
    <div class="title-wrap">
      <div class="title">__TITLE__</div>
      <div class="meta">Toplam __COUNT__ mesaj • Medya dosyaları ayrı tutulur</div>
    </div>
    <div class="controls">
      <input id="search" type="search" placeholder="Mesaj, kişi, dosya adı ara...">
      <button id="clearBtn">Temizle</button>
      <button id="jumpEndBtn">Sona git</button>
      <div class="stats" id="stats"></div>
    </div>
  </div>

  <div class="app">
    <div class="chat">
      <div id="messages"></div>
      <button id="loadMoreBtn" class="load-more">Daha fazla yükle</button>
      <div class="footer-note">Not: “Medya dahil edilmedi” satırları placeholder olarak gösterilir. Eksik dosyalar ayrıca işaretlenir.</div>
    </div>
  </div>

  <div class="modal" id="imgModal"><img alt=""></div>

<script>
const allMessages = __MESSAGES__;
const pageSize = 220;
let visibleCount = Math.min(pageSize, allMessages.length);
let activeSearch = "";

const messagesEl = document.getElementById("messages");
const loadMoreBtn = document.getElementById("loadMoreBtn");
const searchEl = document.getElementById("search");
const clearBtn = document.getElementById("clearBtn");
const jumpEndBtn = document.getElementById("jumpEndBtn");
const statsEl = document.getElementById("stats");
const imgModal = document.getElementById("imgModal");
const imgModalImg = imgModal.querySelector("img");

function escapeHtml(s){ return (s ?? "").replace(/[&<>"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch])); }
function linkify(text){ const escaped = escapeHtml(text); return escaped.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>'); }
function highlight(text, term){
  if(!term) return linkify(text);
  const src = text ?? "";
  const parts = src.split(new RegExp(`(${term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'ig'));
  return parts.map(part => part.toLowerCase() === term.toLowerCase() ? `<mark>${escapeHtml(part)}</mark>` : linkify(part)).join("");
}
function bubbleClass(msg){ return msg.kind === "system" ? "bubble system" : "bubble in"; }
function rowClass(msg){ return msg.kind === "system" ? "msg-row" : "msg-row in"; }
function renderAttachment(msg){
  const captionHtml = msg.caption ? `<div class="caption text">${highlight(msg.caption, activeSearch)}</div>` : "";
  if (!msg.file_exists) {
    return `<div class="file-card"><div class="file-name missing">Eksik dosya: ${escapeHtml(msg.file_name || "")}</div><div class="file-type">Dosya klasörde bulunamadı</div></div>${captionHtml}`;
  }
  if (msg.file_type === "image") return `<img class="media" loading="lazy" src="${encodeURI(msg.file_rel)}" alt="${escapeHtml(msg.file_name || "")}" data-full="${encodeURI(msg.file_rel)}">${captionHtml}`;
  if (msg.file_type === "video") return `<video class="media" controls preload="none"><source src="${encodeURI(msg.file_rel)}">Tarayıcı bu videoyu açamadı.</video>${captionHtml}`;
  if (msg.file_type === "audio") return `<audio class="media" controls preload="none"><source src="${encodeURI(msg.file_rel)}">Tarayıcı bu sesi açamadı.</audio>${captionHtml}`;
  if (msg.file_type === "pdf") return `<div class="file-card"><div class="file-name"><a href="${encodeURI(msg.file_rel)}" target="_blank" rel="noopener">${escapeHtml(msg.file_name || "")}</a></div><div class="file-type">PDF</div></div>${captionHtml}`;
  return `<div class="file-card"><div class="file-name"><a href="${encodeURI(msg.file_rel)}" target="_blank" rel="noopener">${escapeHtml(msg.file_name || "")}</a></div><div class="file-type">Dosya</div></div>${captionHtml}`;
}
function matchesSearch(msg, term){
  if(!term) return true;
  const hay = [msg.sender || "", msg.text || "", msg.caption || "", msg.file_name || "", msg.date_label || ""].join("\n").toLowerCase();
  return hay.includes(term.toLowerCase());
}
function currentData(){ return activeSearch ? allMessages.filter(m => matchesSearch(m, activeSearch)) : allMessages; }

function render(){
  const data = currentData();
  const visible = activeSearch ? data : data.slice(0, visibleCount);
  messagesEl.innerHTML = "";
  let lastDate = "";
  for(const msg of visible){
    if(msg.date !== lastDate){
      lastDate = msg.date;
      const sep = document.createElement("div");
      sep.className = "date-sep";
      sep.innerHTML = `<span>${escapeHtml(msg.date_label)}</span>`;
      messagesEl.appendChild(sep);
    }
    const row = document.createElement("div");
    row.className = rowClass(msg);
    const bubble = document.createElement("div");
    bubble.className = bubbleClass(msg);
    let inner = "";
    if(msg.kind === "system"){
      inner = `<div class="text">${highlight(msg.text, activeSearch)}</div><div class="meta-line"><span>${escapeHtml(msg.time)}</span></div>`;
    } else {
      const sender = msg.sender ? `<div class="sender">${highlight(msg.sender, activeSearch)}</div>` : "";
      if(msg.kind === "deleted"){
        inner = `${sender}<div class="text deleted">Bu mesaj silindi</div><div class="meta-line"><span>${escapeHtml(msg.time)}</span></div>`;
      } else if(msg.kind === "omitted"){
        inner = `${sender}<div class="text omitted">&lt;Medya dahil edilmedi&gt;</div><div class="meta-line"><span>${escapeHtml(msg.time)}</span></div>`;
      } else if(msg.kind === "attachment"){
        inner = `${sender}${renderAttachment(msg)}<div class="meta-line"><span>${escapeHtml(msg.time)}</span></div>`;
      } else {
        inner = `${sender}<div class="text">${highlight(msg.text, activeSearch)}</div><div class="meta-line"><span>${escapeHtml(msg.time)}</span></div>`;
      }
    }
    bubble.innerHTML = inner;
    row.appendChild(bubble);
    messagesEl.appendChild(row);
  }
  const total = data.length;
  statsEl.textContent = activeSearch ? `${total} eşleşme` : `${Math.min(visibleCount, total)} / ${total} gösteriliyor`;
  loadMoreBtn.style.display = (!activeSearch && visibleCount < total) ? "block" : "none";
  document.querySelectorAll("img.media").forEach(img => img.addEventListener("click", () => { imgModalImg.src = img.getAttribute("data-full"); imgModal.style.display = "flex"; }));
}
loadMoreBtn.addEventListener("click", () => { visibleCount = Math.min(visibleCount + pageSize, allMessages.length); render(); });
searchEl.addEventListener("input", e => { activeSearch = e.target.value.trim(); render(); });
clearBtn.addEventListener("click", () => { searchEl.value = ""; activeSearch = ""; render(); });
jumpEndBtn.addEventListener("click", () => { visibleCount = allMessages.length; activeSearch = ""; searchEl.value = ""; render(); window.scrollTo({top: document.body.scrollHeight, behavior: "smooth"}); });
imgModal.addEventListener("click", () => { imgModal.style.display = "none"; imgModalImg.src = ""; });
render();
</script>
</body>
</html>
"""


def build_html(messages, title: str) -> str:
    messages_json = json.dumps(messages, ensure_ascii=False, separators=(',', ':'))
    return HTML_TEMPLATE.replace('__TITLE__', html.escape(title)).replace('__COUNT__', str(len(messages))).replace('__MESSAGES__', messages_json)


def choose_txt(folder: Path):
    txts = sorted(folder.glob('*.txt'))
    if not txts:
        raise FileNotFoundError(f'Klasörde .txt bulunamadı: {folder}')
    if len(txts) == 1:
        return txts[0]
    preferred = [p for p in txts if 'whatsapp' in p.name.lower() or 'sohbet' in p.name.lower()]
    return preferred[0] if preferred else max(txts, key=lambda p: p.stat().st_size)


def resolve_folder(input_path: Path):
    if input_path.is_dir():
        return input_path
    if input_path.is_file() and input_path.suffix.lower() == '.txt':
        return input_path.parent
    raise FileNotFoundError(f'Geçersiz yol: {input_path}')


def choose_output_path(input_path: Path, folder: Path, txt_file: Path):
    if input_path.is_dir():
        title = clean_text(folder.name) or clean_text(txt_file.stem)
        return folder.parent / f'{title}.html', title
    media_candidates = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() not in {'.txt', '.html', '.htm', '.py', '.bat'}]
    if media_candidates:
        title = clean_text(folder.name) or clean_text(txt_file.stem)
        return folder.parent / f'{title}.html', title
    title = clean_text(txt_file.stem)
    return txt_file.with_suffix('.html'), title


def convert(target: Path):
    folder = resolve_folder(target)
    txt_file = target if target.is_file() and target.suffix.lower() == '.txt' else choose_txt(folder)
    raw_text = try_read_text(txt_file)
    messages = parse_chat(raw_text)
    messages = enrich_with_media(messages, folder)
    out_html, title = choose_output_path(target, folder, txt_file)
    out_html.write_text(build_html(messages, title), encoding='utf-8')

    total_attach = sum(1 for m in messages if m['kind'] == 'attachment')
    found_attach = sum(1 for m in messages if m['kind'] == 'attachment' and m['file_exists'])
    omitted = sum(1 for m in messages if m['kind'] == 'omitted')

    return {
        'out_html': out_html,
        'message_count': len(messages),
        'attachment_count': total_attach,
        'attachment_found': found_attach,
        'attachment_missing': total_attach - found_attach,
        'omitted_count': omitted,
    }


def main():
    parser = argparse.ArgumentParser(description='WhatsApp dışa aktarma klasörünü tek HTML arşive dönüştürür.')
    parser.add_argument('path', nargs='?', help='Klasör yolu veya içindeki .txt dosyası')
    args = parser.parse_args()

    if args.path:
        target = Path(args.path).expanduser()
    else:
        chosen = choose_folder_dialog()
        if chosen is None:
            print('İşlem iptal edildi.')
            return
        target = chosen

    if not target.exists():
        msg = f'Yol bulunamadı: {target}'
        show_error('Hata', msg)
        raise FileNotFoundError(msg)

    try:
        result = convert(target)
    except Exception as exc:
        show_error('Dönüştürme hatası', str(exc))
        raise

    summary = (
        f"HTML oluşturuldu:\n{result['out_html']}\n\n"
        f"Toplam mesaj: {result['message_count']}\n"
        f"Ek dosya mesajı: {result['attachment_count']}\n"
        f"Bulunan ek: {result['attachment_found']}\n"
        f"Eksik ek: {result['attachment_missing']}\n"
        f"Medya dahil edilmedi satırı: {result['omitted_count']}"
    )
    print(summary)
    if not args.path:
        show_info('Tamamlandı', summary)


if __name__ == '__main__':
    main()
