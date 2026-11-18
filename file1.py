import os
import time
import math
import queue
import ctypes
import tempfile
import threading
import urllib.request
import tkinter as tk

ICON_URL = "https://raw.githubusercontent.com/scpstudioofficaltr-spec/load-system-by-crgame/main/icoimg"
APP_URL = "https://raw.githubusercontent.com/scpstudioofficaltr-spec/load-system-by-crgame/main/apppy"

MAX_ATTEMPTS = 3
TIMEOUT = 10
RETRY_DELAY = 2
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
APP_ID = "crgame.loadsystem.1"

WHITE = "#ffffff"
RED = "#e10600"
DARK_RED = "#f2c4c2"
ERR_BG = "#2a0000"
ERR_TXT = "#ff2a2a"
ERR_SUB = "#ff6b6b"

ICO_PATH = os.path.join(tempfile.gettempdir(), "crgame_app_icon.ico")
PNG_PATH = os.path.join(tempfile.gettempdir(), "crgame_app_icon.png")


def set_app_id():
    """Windows'a bu uygulamanın kendi kimliği olduğunu söyler; görev çubuğunda Python ikonu yerine bizimki görünür."""
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except (AttributeError, OSError):
        pass


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def download_icon():
    """İkonu indirir. Dönüş: (dosya_yolu, tür) veya (None, None). Tür: 'ico' veya 'png'."""
    try:
        data = fetch(ICON_URL)
    except Exception:
        return None, None

    if data[:4] == b"\x00\x00\x01\x00":
        path, kind = ICO_PATH, "ico"
    elif data[:8] == b"\x89PNG\r\n\x1a\n":
        path, kind = PNG_PATH, "png"
    else:
        return None, None

    try:
        with open(path, "wb") as f:
            f.write(data)
    except OSError:
        return None, None
    return path, kind


class Loader:
    def __init__(self, root):
        self.root = root
        self.mode = "loading"
        self.tick = 0
        self.status = "Hazırlanıyor"
        self.q = queue.Queue()
        self.icon_img = None  # PNG ikon referansı (çöp toplayıcıdan korunmak için)

        root.title("LOAD SYSTEM")
        root.configure(bg=WHITE)
        try:
            root.state("zoomed")
        except tk.TclError:
            root.geometry("1280x800")

        self.start_loading_screen()
        self.start_download()
        self.root.after(100, self.poll)

    # ---- İkon ----
    def apply_icon(self, path, kind):
        try:
            if kind == "ico":
                self.root.iconbitmap(path)
            else:
                self.icon_img = tk.PhotoImage(file=path)
                self.root.iconphoto(True, self.icon_img)
        except tk.TclError:
            pass

    # ---- Ekran ----
    def start_loading_screen(self):
        self.mode = "loading"
        self.canvas = tk.Canvas(self.root, bg=WHITE, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.animate()

    def start_download(self):
        threading.Thread(target=self.worker, daemon=True).start()

    def worker(self):
        self.q.put(("status", "İkon indiriliyor"))
        path, kind = download_icon()
        if path:
            self.q.put(("icon", (path, kind)))

        for attempt in range(1, MAX_ATTEMPTS + 1):
            self.q.put(("status", f"Uygulama indiriliyor ({attempt}/{MAX_ATTEMPTS})"))
            try:
                data = fetch(APP_URL)
                if data.strip():
                    self.q.put(("code", data))
                    return
            except Exception:
                pass
            if attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_DELAY)

        self.q.put(("fail", "SYSTEM CONNECTION ERROR"))

    def poll(self):
        try:
            while True:
                kind, val = self.q.get_nowait()
                if kind == "status":
                    self.status = val
                elif kind == "icon":
                    path, ikind = val
                    self.apply_icon(path, ikind)
                    # Windows ilk ayarı bazen görev çubuğunda yok sayar; birkaç kez tekrar uygula
                    for delay in (300, 1000, 2500):
                        self.root.after(delay, lambda p=path, k=ikind: self.apply_icon(p, k))
                elif kind == "code":
                    self.run_app(val)
                    return
                elif kind == "fail":
                    self.show_error(val, "Sunucuya ulaşılamadı. İnternet bağlantını kontrol et.")
                    return
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def animate(self):
        if self.mode != "loading":
            return
        c = self.canvas
        w, h = c.winfo_width(), c.winfo_height()
        c.delete("all")
        cx, cy = w // 2, h // 2

        c.create_text(cx, cy - 140, text="LOAD SYSTEM", fill=RED, font=("Consolas", 48, "bold"))

        bars, bw, gap = 24, 14, 8
        total = bars * (bw + gap) - gap
        x0 = cx - total // 2
        base = cy + 60
        for i in range(bars):
            amp = (math.sin(self.tick * 0.15 + i * 0.45) + 1) / 2
            bh = 10 + amp * 110
            x = x0 + i * (bw + gap)
            color = RED if amp > 0.5 else DARK_RED
            c.create_rectangle(x, base - bh, x + bw, base, fill=color, outline="")

        pw, py = 600, cy + 110
        left = cx - pw // 2
        c.create_rectangle(left, py, left + pw, py + 8, outline=DARK_RED)
        pos = (self.tick * 10) % (pw + 120) - 120
        seg_l = max(left, left + pos)
        seg_r = min(left + pw, left + pos + 120)
        if seg_r > seg_l:
            c.create_rectangle(seg_l, py, seg_r, py + 8, fill=RED, outline="")

        dots = "." * ((self.tick // 12) % 4)
        c.create_text(cx, cy + 150, text=self.status + dots, fill=RED, font=("Consolas", 14))

        self.tick += 1
        self.root.after(33, self.animate)

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def run_app(self, data):
        self.mode = "app"
        self.clear()
        try:
            src = data.decode("utf-8")
            ns = {"__name__": "apppy", "root": self.root}
            exec(compile(src, "apppy", "exec"), ns)
            ns["build"](self.root)
        except Exception as e:
            self.show_error("APP ERROR", str(e)[:150])

    def show_error(self, title, detail):
        self.mode = "error"
        self.clear()
        self.root.configure(bg=ERR_BG)

        f = tk.Frame(self.root, bg=ERR_BG)
        f.pack(fill="both", expand=True)
        tk.Label(f, text=title, fg=ERR_TXT, bg=ERR_BG,
                 font=("Consolas", 40, "bold")).pack(expand=True, pady=(0, 10))
        tk.Label(f, text=detail, fg=ERR_SUB, bg=ERR_BG,
                 font=("Consolas", 14)).pack()

        btns = tk.Frame(f, bg=ERR_BG)
        btns.pack(pady=40)
        tk.Button(btns, text="TEKRAR DENE", fg=ERR_BG, bg=ERR_TXT, activebackground=ERR_SUB,
                  font=("Consolas", 13, "bold"), width=16, command=self.retry).pack(side="left", padx=10)
        tk.Button(btns, text="KAPAT", fg=ERR_BG, bg=ERR_TXT, activebackground=ERR_SUB,
                  font=("Consolas", 13, "bold"), width=16, command=self.root.destroy).pack(side="left", padx=10)

    def retry(self):
        self.clear()
        self.root.configure(bg=WHITE)
        self.tick = 0
        self.status = "Yeniden deneniyor"
        self.start_loading_screen()
        self.start_download()
        self.root.after(100, self.poll)


def main():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    set_app_id()

    root = tk.Tk()
    Loader(root)
    root.mainloop()


if __name__ == "__main__":
    main()
