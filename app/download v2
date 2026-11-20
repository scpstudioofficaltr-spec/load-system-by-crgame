import os
import re
import sys
import time
import queue
import tempfile
import threading
import subprocess
import urllib.request
import urllib.parse
import tkinter as tk

WHITE = "#ffffff"
RED = "#e10600"
DARK = "#111111"
GREY = "#666666"
LIGHT = "#f6f6f6"
LINE = "#e5e5e5"

BASE = "https://raw.githubusercontent.com/scpstudioofficaltr-spec/load-system-by-crgame/main/"
LIST_URLS = [BASE + "game/list", BASE + "oyun/list"]
APP_LIST_URLS = [BASE + "app/list"]
APP_FILES_BASE = BASE + "app/"
APP_URL = BASE + "apppy"

TMP = tempfile.gettempdir()
LOG_PATH = os.path.join(TMP, "crgame_game.log")
APP_LOG_PATH = os.path.join(TMP, "crgame_app.log")
RUNNER_PATH = os.path.join(TMP, "crgame_runner.py")
APPS_DIR = os.path.join(TMP, "crgame_apps")

FALLBACK = [{"name": "Örnek Oyun", "file": "ornek_oyun.py", "url": None,
             "desc": "Liste alınamadı. Bu bir örnek oyundur."}]

APP_FALLBACK = [{"name": "scp app v1", "file": "scp_app_v1.pyw",
                 "slug": "scp_app_v1",
                 "url": BASE + "app/scp_app_v1.pyw",
                 "desc": "Kurmanızı tercih ederiz."}]

RUNNER = r'''
import sys, ctypes
import tkinter as tk
import traceback

def main():
    path, slug, icon, kind = sys.argv[1:5]
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    root.withdraw()
    if kind == "ico":
        try:
            root.iconbitmap(default=icon)
        except tk.TclError:
            pass
    try:
        with open(path, encoding="utf-8") as f:
            src = f.read()
        ns = {"__name__": "__main__"}
        exec(compile(src, path, "exec"), ns)
        
        if "build" in ns:
            ns["build"](root)
        elif "play" in ns:
            ns["play"](root)
        else:
            root.deiconify()
        root.mainloop()
    except Exception as e:
        with open(path + ".err", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        print(f"Hata oluştu, detaylar: {path}.err")
        sys.exit(1)

main()
'''

def fetch_bytes(url, timeout=15):
    if not url:
        raise ValueError("URL boş")
    
    if "github.com" in url and "/raw/" not in url:
        url = url.replace("github.com", "raw.githubusercontent.com")
        url = url.replace("/blob/", "/")
        
    if "raw.githubusercontent.com" in url:
        sep = "&" if "?" in url else "?"
        url = url + sep + "t=" + str(int(time.time()))
        
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def parse_line(line):
    parts = [p.strip() for p in line.split("|")]
    url = None
    if len(parts) > 1 and parts[-1].lower().startswith("http"):
        url = parts.pop()
    name = parts[0]
    if name.lower().endswith(".py"):
        name = name[:-3]
    desc = parts[1] if len(parts) > 1 and parts[1] else "Bu oyun için henüz açıklama eklenmedi."
    return {"name": name, "file": name.replace(" ", "_").lower() + ".py",
            "url": url, "desc": desc}

def parse_app_line(line):
    parts = [p.strip() for p in line.split("|")]
    url = None
    if len(parts) > 1 and parts[-1].lower().startswith("http"):
        url = parts.pop()
    raw = parts[0]
    name = raw
    for ext in (".pyw", ".py"):
        if name.lower().endswith(ext):
            name = name[:-len(ext)]
            break
    slug = re.sub(r"[^A-Za-z0-9_-]", "_", name) or "app"
    
    if not url:
        safe = urllib.parse.quote(raw.replace(" ", "_"))
        url = APP_FILES_BASE + safe
        
    desc = parts[1] if len(parts) > 1 and parts[1] else "Bu uygulama için henüz açıklama eklenmedi."
    return {"name": name, "file": slug + ".pyw", "slug": slug, "url": url, "desc": desc}

def fetch_games():
    for u in LIST_URLS:
        try:
            text = fetch_bytes(u, 8).decode("utf-8", errors="ignore")
        except Exception:
            continue
        games = []
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                games.append(parse_line(line))
        if games:
            return games
    return FALLBACK

def fetch_apps():
    for u in APP_LIST_URLS:
        try:
            text = fetch_bytes(u, 8).decode("utf-8", errors="ignore")
        except Exception:
            continue
        apps = []
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                apps.append(parse_app_line(line))
        if apps:
            return apps
    return APP_FALLBACK

def find_icon():
    ico = os.path.join(TMP, "crgame_app_icon.ico")
    png = os.path.join(TMP, "crgame_app_icon.png")
    if os.path.exists(ico):
        return ico, "ico"
    if os.path.exists(png):
        return png, "png"
    return "-", "none"

def start_process(game, code):
    if getattr(sys, "frozen", False):
        raise RuntimeError("Ayrı uygulama olarak açmak için programı Python ile çalıştır (exe olmaz).")
    slug = re.sub(r"[^a-z0-9]", "", game["file"].lower().replace(".py", "")) or "game"
    gpath = os.path.join(TMP, "crgame_game_%s.py" % slug)
    with open(gpath, "wb") as f:
        f.write(code)
    with open(RUNNER_PATH, "w", encoding="utf-8") as f:
        f.write(RUNNER)
    icon, kind = find_icon()
    log = open(LOG_PATH, "w")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        return subprocess.Popen([sys.executable, RUNNER_PATH, gpath, slug, icon, kind],
                                stdout=log, stderr=log, creationflags=flags)
    finally:
        log.close()

def app_path(app):
    return os.path.join(APPS_DIR, app["slug"] + ".pyw")

def install_app(app):
    data = fetch_bytes(app["url"], 30)
    if not data.strip() or b"<html" in data.lower():
        raise ValueError("İndirilen dosya geçersiz (HTML sayfası inmiş olabilir).")
    os.makedirs(APPS_DIR, exist_ok=True)
    with open(app_path(app), "wb") as f:
        f.write(data)

def launch_app(app):
    if getattr(sys, "frozen", False):
        raise RuntimeError("Uygulamayı açmak için programı Python ile çalıştır (exe olmaz).")
    exe = sys.executable
    pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
    if os.name == "nt" and os.path.exists(pyw):
        exe = pyw
    log = open(APP_LOG_PATH, "w")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        return subprocess.Popen([exe, app_path(app)], stdout=log, stderr=log,
                                creationflags=flags, cwd=APPS_DIR)
    finally:
        log.close()

def tail_of(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            lines = [l.strip() for l in f.read().splitlines() if l.strip()]
        return lines[-1][:150] if lines else "unknown error"
    except OSError:
        return "unknown error"

def log_tail():
    return tail_of(LOG_PATH)

def build(root):
    root.title("LOAD SYSTEM")
    root.configure(bg=WHITE)
    for w in root.winfo_children():
        w.destroy()

    state = {"anim": None, "games": None, "apps": None, "proc": None, "game": None,
             "app_procs": {}, "user_closed": False, "dead": False}
    q = queue.Queue()

    def proc_alive():
        p = state["proc"]
        return p is not None and p.poll() is None

    def poll():
        if state["dead"]:
            return
        try:
            while True:
                cb, res = q.get_nowait()
                cb(res)
        except queue.Empty:
            pass
        except tk.TclError:
            return
        try:
            root.after(80, poll)
        except tk.TclError:
            pass

    def bg(fn, cb):
        def work():
            try:
                res = fn()
            except Exception as e:
                res = e
            q.put((cb, res))
        threading.Thread(target=work, daemon=True).start()

    nav = tk.Frame(root, bg=WHITE, highlightbackground=LINE, highlightthickness=1)
    nav.pack(fill="x", side="top")
    tk.Label(nav, text="LOAD SYSTEM", fg=RED, bg=WHITE,
             font=("Segoe UI", 16, "bold")).pack(side="left", padx=24, pady=14)
    upd = tk.Button(nav, text="Update", fg=RED, bg=WHITE, activeforeground=WHITE,
                    activebackground=RED, relief="solid", bd=1,
                    font=("Segoe UI", 11, "bold"), padx=16, pady=4, cursor="hand2",
                    disabledforeground="#bbbbbb",
                    command=lambda: do_update())
    upd.pack(side="right", padx=(8, 24))
    apps_btn = tk.Label(nav, text="Apps", fg=RED, bg=WHITE,
                        font=("Segoe UI", 11, "bold"), cursor="hand2")
    apps_btn.pack(side="right", padx=16)
    home_btn = tk.Label(nav, text="Ana Menü", fg=DARK, bg=WHITE,
                        font=("Segoe UI", 11), cursor="hand2")
    home_btn.pack(side="right", padx=16)
    note_lbl = tk.Label(nav, text="", fg=GREY, bg=WHITE, font=("Segoe UI", 10))
    note_lbl.pack(side="right", padx=8)

    def note(text, ms=5000):
        try:
            note_lbl.config(text=text)
            if text:
                root.after(ms, lambda: note_lbl.winfo_exists() and note_lbl.config(text=""))
        except tk.TclError:
            pass

    pending = getattr(root, "_crgame_note", "")
    if pending:
        root._crgame_note = ""
        note(pending)

    body = tk.Frame(root, bg=WHITE)
    body.pack(fill="both", expand=True)
    canvas = tk.Canvas(body, bg=WHITE, highlightthickness=0)
    sb = tk.Scrollbar(body, orient="vertical", command=canvas.yview)
    sb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.configure(yscrollcommand=sb.set)

    page = tk.Frame(canvas, bg=WHITE)
    win = canvas.create_window((0, 0), window=page, anchor="nw")
    page.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win, width=e.width))
    canvas.bind_all("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

    def clear():
        if state["anim"]:
            root.after_cancel(state["anim"])
            state["anim"] = None
        for w in page.winfo_children():
            w.destroy()
        canvas.yview_moveto(0)

    def do_update():
        if proc_alive():
            note("Close the game first.")
            return
        upd.config(text="Updating...", state="disabled")
        note("")

        def work():
            data = fetch_bytes(APP_URL, 20)
            if not data.strip():
                raise ValueError("empty file")
            ns = {"__name__": "apppy", "root": root}
            exec(compile(data.decode("utf-8"), "apppy", "exec"), ns)
            if "build" not in ns:
                raise ValueError("build() not found")
            return ns

        def done(res):
            try:
                if state["anim"]:
                    root.after_cancel(state["anim"])
                    state["anim"] = None
            except tk.TclError:
                return
            state["dead"] = True
            if isinstance(res, Exception):
                root._crgame_note = "Update failed: " + str(res)[:70]
                build(root)
                return
            root._crgame_note = "Updated ✓"
            try:
                res["build"](root)
            except Exception as e:
                root._crgame_note = "Update failed: " + str(e)[:70]
                build(root)

        bg(work, done)

    def show_home():
        clear()
        hero = tk.Frame(page, bg=WHITE)
        hero.pack(fill="x", padx=60, pady=(50, 20))
        tk.Label(hero, text="Hoş geldin", fg=RED, bg=WHITE,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(hero, text="Oyunlar", fg=DARK, bg=WHITE,
                 font=("Segoe UI", 38, "bold")).pack(anchor="w", pady=(6, 0))
        tk.Label(hero, text="Bir oyun seç ve başla.", fg=GREY, bg=WHITE,
                 font=("Segoe UI", 13)).pack(anchor="w", pady=(10, 0))

        grid = tk.Frame(page, bg=WHITE)
        grid.pack(fill="x", padx=50, pady=20)
        status = tk.Label(page, text="Oyunlar yükleniyor...", fg=GREY, bg=WHITE,
                          font=("Segoe UI", 12))
        status.pack(pady=10)

        def fill(games):
            try:
                if not grid.winfo_exists():
                    return
                status.destroy()
            except tk.TclError:
                return
            state["games"] = games
            cols = 3
            for i, g in enumerate(games):
                card = tk.Frame(grid, bg=LIGHT, highlightbackground=LINE,
                                highlightthickness=1, cursor="hand2")
                card.grid(row=i // cols, column=i % cols, padx=10, pady=10, sticky="nsew")
                grid.grid_columnconfigure(i % cols, weight=1, uniform="c")
                tk.Frame(card, bg=RED, height=4).pack(fill="x")
                t = tk.Label(card, text=g["name"], fg=DARK, bg=LIGHT,
                             font=("Segoe UI", 15, "bold"), cursor="hand2")
                t.pack(anchor="w", padx=20, pady=(20, 6))
                f = tk.Label(card, text=g["file"], fg=GREY, bg=LIGHT,
                             font=("Consolas", 10), cursor="hand2")
                f.pack(anchor="w", padx=20, pady=(0, 24))
                for w in (card, t, f):
                    w.bind("<Button-1>", lambda e, g=g: show_loading(g))

        if state["games"] is not None:
            fill(state["games"])
        else:
            bg(fetch_games, lambda res: fill(FALLBACK if isinstance(res, Exception) else res))

    def show_spinner(text, after_done, frames=60):
        clear()
        box = tk.Frame(page, bg=WHITE)
        box.pack(pady=(140, 0))
        c = tk.Canvas(box, width=90, height=90, bg=WHITE, highlightthickness=0)
        c.pack()
        tk.Label(box, text=text, fg=DARK, bg=WHITE,
                 font=("Segoe UI", 14)).pack(pady=(20, 0))
        c.create_oval(10, 10, 80, 80, outline=LINE, width=6)
        arc = c.create_arc(10, 10, 80, 80, start=0, extent=100,
                           style="arc", outline=RED, width=6)
        ticks = {"n": 0}

        def spin():
            ticks["n"] += 1
            c.itemconfigure(arc, start=(ticks["n"] * 12) % 360)
            if ticks["n"] >= frames:
                after_done()
                return
            state["anim"] = root.after(33, spin)

        spin()

    def show_loading(game):
        show_spinner(f"{game['name']} yükleniyor...", lambda: show_game(game))

    def show_game(game):
        clear()
        box = tk.Frame(page, bg=WHITE)
        box.pack(fill="x", padx=60, pady=(70, 20))
        tk.Label(box, text=game["name"], fg=DARK, bg=WHITE,
                 font=("Segoe UI", 34, "bold")).pack(anchor="w")
        tk.Label(box, text=game["file"], fg=GREY, bg=WHITE,
                 font=("Consolas", 11)).pack(anchor="w", pady=(4, 0))
        tk.Label(box, text=game["desc"], fg=GREY, bg=WHITE, font=("Segoe UI", 13),
                 wraplength=800, justify="left").pack(anchor="w", pady=(20, 28))

        row = tk.Frame(box, bg=WHITE)
        row.pack(anchor="w")
        play_btn = tk.Button(row, text="Play", fg=WHITE, bg=RED, activebackground="#b80500",
                             activeforeground=WHITE, disabledforeground="#ffd0ce",
                             relief="flat", font=("Segoe UI", 13, "bold"),
                             padx=36, pady=12, cursor="hand2")
        play_btn.pack(side="left")
        close_btn = tk.Button(row, text="Close", fg=DARK, bg=WHITE, activebackground=LIGHT,
                              disabledforeground="#bbbbbb", relief="solid", bd=1,
                              font=("Segoe UI", 13, "bold"), padx=30, pady=11, cursor="hand2")
        close_btn.pack(side="left", padx=(12, 0))
        msg = tk.Label(box, text="", fg=GREY, bg=WHITE, font=("Segoe UI", 11),
                       wraplength=800, justify="left")
        msg.pack(anchor="w", pady=(12, 0))
        tk.Button(box, text="← Geri", fg=DARK, bg=WHITE, relief="flat",
                  font=("Segoe UI", 11), cursor="hand2",
                  command=show_home).pack(anchor="w", pady=(20, 0))

        ui = {"busy": False}

        def sync():
            alive = proc_alive()
            mine = alive and state["game"] == game["name"]
            if mine:
                play_btn.config(text="Playing", state="disabled")
                close_btn.config(state="normal")
                msg.config(text="The game is running in its own window.", fg=GREY)
            elif ui["busy"]:
                play_btn.config(text="Loading...", state="disabled")
                close_btn.config(state="disabled")
            elif alive:
                play_btn.config(text="Play", state="disabled")
                close_btn.config(state="normal")
                msg.config(text="Another game is running. Close it first.", fg=GREY)
            else:
                play_btn.config(text="Play", state="normal")
                close_btn.config(state="disabled")

        def start():
            if proc_alive() or ui["busy"]:
                return
            if not game.get("url"):
                msg.config(text="Bu oyun için listede bağlantı (url) yok.", fg=RED)
                return
            ui["busy"] = True
            msg.config(text="", fg=GREY)
            sync()

            def done(res):
                ui["busy"] = False
                try:
                    if isinstance(res, Exception):
                        msg.config(text="Download failed: " + str(res)[:120], fg=RED)
                    else:
                        try:
                            state["proc"] = start_process(game, res)
                            state["game"] = game["name"]
                            state["user_closed"] = False
                        except Exception as e:
                            msg.config(text="Could not start: " + str(e)[:150], fg=RED)
                    sync()
                except tk.TclError:
                    pass

            bg(lambda: fetch_bytes(game["url"]), done)

        def stop():
            p = state["proc"]
            if p is not None and p.poll() is None:
                state["user_closed"] = True
                p.terminate()

        def tick():
            p = state["proc"]
            if p is not None and p.poll() is not None:
                rc = p.returncode
                state["proc"] = None
                if state["user_closed"]:
                    state["user_closed"] = False
                    msg.config(text="")
                elif rc not in (0, None):
                    msg.config(text="Game error: " + log_tail(), fg=RED)
                else:
                    msg.config(text="")
            sync()
            state["anim"] = root.after(400, tick)

        play_btn.config(command=start)
        close_btn.config(command=stop)
        tick()

    def open_apps():
        show_spinner("Apps yükleniyor...", show_apps, frames=45)

    def show_apps():
        clear()
        hero = tk.Frame(page, bg=WHITE)
        hero.pack(fill="x", padx=60, pady=(50, 20))
        tk.Label(hero, text="Uygulamalar", fg=RED, bg=WHITE,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(hero, text="Apps", fg=DARK, bg=WHITE,
                 font=("Segoe UI", 38, "bold")).pack(anchor="w", pady=(6, 0))
        tk.Label(hero, text="Bir uygulama seç, yükle ve çalıştır.", fg=GREY, bg=WHITE,
                 font=("Segoe UI", 13)).pack(anchor="w", pady=(10, 0))

        grid = tk.Frame(page, bg=WHITE)
        grid.pack(fill="x", padx=50, pady=20)
        status = tk.Label(page, text="Uygulama listesi yükleniyor...", fg=GREY, bg=WHITE,
                          font=("Segoe UI", 12))
        status.pack(pady=10)

        def fill(apps):
            try:
                if not grid.winfo_exists():
                    return
                status.destroy()
            except tk.TclError:
                return
            state["apps"] = apps
            cols = 3
            for i, a in enumerate(apps):
                card = tk.Frame(grid, bg=LIGHT, highlightbackground=LINE,
                                highlightthickness=1, cursor="hand2")
                card.grid(row=i // cols, column=i % cols, padx=10, pady=10, sticky="nsew")
                grid.grid_columnconfigure(i % cols, weight=1, uniform="c")
                tk.Frame(card, bg=RED, height=4).pack(fill="x")
                t = tk.Label(card, text=a["name"], fg=DARK, bg=LIGHT,
                             font=("Segoe UI", 15, "bold"), cursor="hand2")
                t.pack(anchor="w", padx=20, pady=(20, 6))
                f = tk.Label(card, text=a["file"], fg=GREY, bg=LIGHT,
                             font=("Consolas", 10), cursor="hand2")
                f.pack(anchor="w", padx=20, pady=(0, 24))
                for w in (card, t, f):
                    w.bind("<Button-1>", lambda e, a=a: show_app(a))

        if state["apps"] is not None:
            fill(state["apps"])
        else:
            bg(fetch_apps, lambda res: fill(APP_FALLBACK if isinstance(res, Exception) else res))

    # ---------- APP SAYFASI (DÜZELTİLEN YER BURASI) ----------
    def show_app(app):
        clear()
        box = tk.Frame(page, bg=WHITE)
        box.pack(fill="x", padx=60, pady=(70, 20))
        tk.Label(box, text=app["name"], fg=DARK, bg=WHITE,
                 font=("Segoe UI", 34, "bold")).pack(anchor="w")
        tk.Label(box, text=app["file"], fg=GREY, bg=WHITE,
                 font=("Consolas", 11)).pack(anchor="w", pady=(4, 0))
        tk.Label(box, text=app["desc"], fg=GREY, bg=WHITE, font=("Segoe UI", 13),
                 wraplength=800, justify="left").pack(anchor="w", pady=(20, 28))

        row = tk.Frame(box, bg=WHITE)
        row.pack(anchor="w")
        
        # Buton metni başlangıçta "Kurulumu Başlat" olacak
        main_btn = tk.Button(row, text="Kurulumu Başlat", fg=WHITE, bg=RED, activebackground="#b80500",
                             activeforeground=WHITE, disabledforeground="#ffd0ce",
                             relief="flat", font=("Segoe UI", 13, "bold"),
                             padx=36, pady=12, cursor="hand2")
        main_btn.pack(side="left")
        
        close_btn = tk.Button(row, text="Kapat", fg=DARK, bg=WHITE, activebackground=LIGHT,
                              disabledforeground="#bbbbbb", relief="solid", bd=1,
                              font=("Segoe UI", 13, "bold"), padx=30, pady=11, cursor="hand2")
        close_btn.pack(side="left", padx=(12, 0))
        
        msg = tk.Label(box, text="", fg=GREY, bg=WHITE, font=("Segoe UI", 11),
                       wraplength=800, justify="left")
        msg.pack(anchor="w", pady=(12, 0))
        tk.Button(box, text="← Geri", fg=DARK, bg=WHITE, relief="flat",
                  font=("Segoe UI", 11), cursor="hand2",
                  command=show_apps).pack(anchor="w", pady=(20, 0))

        ui = {"busy": False}

        def alive():
            p = state["app_procs"].get(app["name"])
            return p is not None and p.poll() is None

        def sync():
            # Eğer uygulama zaten kuruluysa "Çalıştır" butonu çıkacak
            installed = os.path.exists(app_path(app))
            
            if alive():
                main_btn.config(text="Çalışıyor", state="disabled")
                close_btn.config(state="normal")
                msg.config(text="Uygulama çalışıyor.", fg=GREY)
            elif ui["busy"]:
                main_btn.config(text="İndiriliyor...", state="disabled")
                close_btn.config(state="disabled")
            else:
                main_btn.config(text="Çalıştır" if installed else "İndir ve Kurulumu Başlat", state="normal")
                close_btn.config(state="disabled")

        def start():
            if alive() or ui["busy"]:
                return
            ui["busy"] = True
            msg.config(text="", fg=GREY)
            sync()

            def work():
                # Eğer dosya yoksa indir
                if not os.path.exists(app_path(app)):
                    install_app(app)
                time.sleep(0.5)
                return launch_app(app)

            def done(res):
                ui["busy"] = False
                try:
                    if isinstance(res, Exception):
                        msg.config(text="Başarısız: " + str(res)[:150], fg=RED)
                    else:
                        state["app_procs"][app["name"]] = res
                        ui["closed"] = False
                    sync()
                except tk.TclError:
                    pass

            bg(work, done)

        def stop():
            p = state["app_procs"].get(app["name"])
            if p is not None and p.poll() is None:
                ui["closed"] = True
                p.terminate()

        def tick():
            p = state["app_procs"].get(app["name"])
            if p is not None and p.poll() is not None:
                rc = p.returncode
                state["app_procs"].pop(app["name"], None)
                if ui.get("closed"):
                    ui["closed"] = False
                    msg.config(text="")
                elif rc not in (0, None):
                    msg.config(text="Uygulama hatası: " + tail_of(APP_LOG_PATH), fg=RED)
                else:
                    msg.config(text="")
            sync()
            state["anim"] = root.after(400, tick)

        main_btn.config(command=start)
        close_btn.config(command=stop)
        tick()

    home_btn.bind("<Button-1>", lambda e: show_home())
    apps_btn.bind("<Button-1>", lambda e: open_apps())

    footer = tk.Frame(root, bg=LIGHT, highlightbackground=LINE, highlightthickness=1)
    footer.pack(fill="x", side="bottom")
    tk.Label(footer, text="© LOAD SYSTEM", fg=GREY, bg=LIGHT,
             font=("Segoe UI", 10)).pack(pady=12)

    poll()
    show_home()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x700")
    build(root)
    root.mainloop()
