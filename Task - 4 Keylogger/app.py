"""
Ethical Keystroke Viewer — Clean White/Black Theme
Prodigy InfoTech Internship Project
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from datetime import datetime
import time, threading, os, re, platform, getpass
from modules.file_utils import LogManager
from modules.ui_utils import add_tooltip, open_folder


# ---------- Helpers ----------
def utc_now(fmt="%Y-%m-%d %H:%M:%S.%f UTC"):
    s = datetime.utcnow().strftime(fmt)
    return s[:-3] + " UTC"


def local_now(fmt="%Y-%m-%d %H:%M:%S.%f"):
    s = datetime.now().strftime(fmt)
    return s[:-3]


def looks_like_password(token: str) -> bool:
    if not token or len(token) < 6:
        return False
    classes = sum(bool(re.search(p, token)) for p in [r"[A-Za-z]", r"[0-9]", r"[^A-Za-z0-9]"])
    return classes >= 2


# ---------- App ----------
class EthicalKeystrokeViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Ethical Keystroke Viewer — Prodigy InfoTech")
        self.root.geometry("980x680")
        self.root.minsize(780, 500)
        self.root.configure(bg="#f8f9fa")

        # state
        self.events = []
        self.key_counts = {}
        self.total_keys = 0
        self.printable_keys = 0
        self.special_keys = 0
        self.logging_paused = False
        self.session_start = time.time()
        self.session_meta = {}
        self.alert_keywords = ["password", "secret", "token", "key", "confidential"]

        # options
        self.var_trim_to_printable = tk.BooleanVar(value=False)
        self.var_mask_sensitive = tk.BooleanVar(value=False)
        self.var_auto_redact = tk.BooleanVar(value=True)
        self.var_timestamp_local = tk.BooleanVar(value=False)

        # file manager
        self.log_manager = LogManager(base_dir="logs")

        # theme
        self.set_theme(light=True)

        # build UI
        self.build_header()
        self.build_consent_dialog()
        self.build_controls()
        self.build_text_input()
        self.build_log_area()
        self.build_status_bar()

        # bindings
        self.text_input.bind("<Key>", self.on_key)
        self.text_input.bind("<<Paste>>", self.on_paste)

        # timer thread
        threading.Thread(target=self._timer_loop, daemon=True).start()

    # ---------- Theme ----------
    def set_theme(self, light=True):
        if light:
            self.bg_main = "#f8f9fa"
            self.panel = "#ffffff"
            self.accent = "#0078d4"  # blue
            self.alert = "#d32f2f"
            self.fg = "#000000"
        else:
            self.bg_main = "#0b0b0b"
            self.panel = "#141414"
            self.accent = "#00FF7F"
            self.alert = "#FF3B3B"
            self.fg = "#00FF7F"

        self.font = ("Consolas", 11)
        self.root.configure(bg=self.bg_main)

    # ---------- Consent ----------
    def build_consent_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Consent Required")
        dlg.geometry("540x260")
        dlg.configure(bg=self.bg_main)
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(dlg, text="⚠️ CONSENT REQUIRED", fg=self.alert, bg=self.bg_main,
                 font=("Consolas", 14, "bold")).pack(anchor="w", padx=12, pady=(12, 6))
        tk.Label(dlg, text=("By continuing you confirm explicit permission to record keystrokes.\n"
                            "This app records only while the input area is focused."), justify="left",
                 wraplength=500, bg=self.bg_main, fg=self.fg, font=self.font).pack(anchor="w", padx=12)

        frm = tk.Frame(dlg, bg=self.bg_main)
        frm.pack(fill="x", padx=12, pady=10)
        tk.Label(frm, text="Your Name:", bg=self.bg_main, fg=self.fg).grid(row=0, column=0, sticky="w")
        self.entry_consent_name = tk.Entry(frm, width=40, bg="#f1f1f1", fg="#000000", insertbackground="#000000")
        self.entry_consent_name.grid(row=0, column=1, padx=(8, 0))

        self.var_consent_checkbox = tk.BooleanVar(value=False)
        tk.Checkbutton(dlg, text="✔ I confirm I have permission.", variable=self.var_consent_checkbox,
                       bg=self.bg_main, fg=self.fg).pack(anchor="w", padx=12, pady=(6, 0))

        btns = tk.Frame(dlg, bg=self.bg_main)
        btns.pack(fill="x", padx=12, pady=12)
        accept = ttk.Button(btns, text="✅ Accept & Continue", width=20, command=lambda: self._accept_consent(dlg))
        accept.pack(side="left", padx=(0, 10))
        add_tooltip(accept, "Agree and continue (consent will be logged)")
        cancel = ttk.Button(btns, text="❌ Cancel (Exit)", width=18, command=lambda: self.root.destroy())
        cancel.pack(side="left")
        self.entry_consent_name.focus_set()
        self.root.wait_window(dlg)

    def _accept_consent(self, dlg):
        name = self.entry_consent_name.get().strip()
        if not name:
            messagebox.showwarning("Name required", "Please enter your name to record consent.")
            return
        if not self.var_consent_checkbox.get():
            messagebox.showwarning("Consent required", "Please check the confirmation box.")
            return
        ts = utc_now()
        self.session_meta = {
            "consent_name": name,
            "consent_ts": ts,
            "os": platform.system(),
            "username": getpass.getuser(),
            "app_version": "EthicalKeystrokeViewer v3"
        }
        dlg.destroy()

    # ---------- Header / Controls ----------
    def build_header(self):
        hdr = tk.Frame(self.root, bg=self.panel)
        hdr.pack(fill="x", padx=8, pady=(6, 4))
        tk.Label(hdr, text="🧠 Ethical Keystroke Viewer — Prodigy InfoTech",
                 bg=self.panel, fg=self.accent, font=("Consolas", 14, "bold")).pack(side="left", padx=8)
        tk.Label(hdr, text="Secure • Local • Ethical", bg=self.panel, fg=self.alert, font=("Consolas", 10)).pack(side="right", padx=8)

    def build_controls(self):
        top = tk.Frame(self.root, bg=self.bg_main)
        top.pack(fill="x", padx=8, pady=(4, 6))

        left = tk.Frame(top, bg=self.bg_main)
        left.pack(side="left", anchor="w")

        btn_save = ttk.Button(left, text="💾 Save", command=self.save_dialog)
        btn_save.pack(side="left")
        add_tooltip(btn_save, "Save session log (txt/csv/json/pdf/xlsx)")

        btn_view = ttk.Button(left, text="📂 View Logs", command=lambda: open_folder("logs"))
        btn_view.pack(side="left", padx=(6, 0))
        add_tooltip(btn_view, "Open logs folder")

        btn_freq = ttk.Button(left, text="📊 Frequency", command=self.show_key_frequency)
        btn_freq.pack(side="left", padx=(6, 0))
        add_tooltip(btn_freq, "Show key frequency counts")

        btn_pause = ttk.Button(left, text="⏯ Pause/Resume", command=self.toggle_pause)
        btn_pause.pack(side="left", padx=(6, 0))
        add_tooltip(btn_pause, "Pause or resume logging")

        # 🔄 Restart Session
        btn_restart = ttk.Button(left, text="🔄 Restart Session", command=self.restart_session)
        btn_restart.pack(side="left", padx=(6, 0))
        add_tooltip(btn_restart, "Restart session: clears logs, resets timer, and starts fresh")

        mid = tk.Frame(top, bg=self.bg_main)
        mid.pack(side="left", padx=20)
        for txt, var in [("Printable-only", self.var_trim_to_printable),
                         ("Mask Sensitive", self.var_mask_sensitive),
                         ("Auto-Redact", self.var_auto_redact)]:
            tk.Checkbutton(mid, text=txt, variable=var, bg=self.bg_main, fg=self.fg).pack(side="left", padx=(8, 0))

        right = tk.Frame(top, bg=self.bg_main)
        right.pack(side="right")
        self.ts_choice = ttk.Combobox(right, values=["UTC", "Local"], width=8, state="readonly")
        self.ts_choice.current(0)
        self.ts_choice.pack(side="left")
        self.ts_choice.bind("<<ComboboxSelected>>", lambda e: self.var_timestamp_local.set(self.ts_choice.get() == "Local"))

    # ---------- Text input / Log ----------
    def build_text_input(self):
        tk.Label(self.root, text="> Input Terminal (focused for capture):", bg=self.bg_main, fg=self.accent).pack(anchor="w", padx=8)
        self.text_input = scrolledtext.ScrolledText(self.root, height=6, wrap="word", bg="#f1f1f1", fg="#000000", insertbackground="#000000")
        self.text_input.pack(fill="x", padx=8, pady=(0, 8))
        self.text_input.focus_set()

    def build_log_area(self):
        tk.Label(self.root, text="> Capture Log:", bg=self.bg_main, fg=self.alert).pack(anchor="w", padx=8)
        self.log_area = scrolledtext.ScrolledText(self.root, height=18, wrap="word", state="disabled", bg="#ffffff", fg="#000000")
        self.log_area.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    # ---------- Status ----------
    def build_status_bar(self):
        frm = tk.Frame(self.root, bg="#e0e0e0", relief="sunken", bd=1)
        frm.pack(fill="x", side="bottom")
        self.status_var = tk.StringVar(value="Total: 0 | Printable: 0 | Special: 0 | Time: 0s")
        tk.Label(frm, textvariable=self.status_var, bg="#e0e0e0", fg="#000000").pack(side="left", padx=6)
        tk.Label(frm, text="🛡 Ethical Logging Active", bg="#e0e0e0", fg=self.accent).pack(side="right", padx=6)

    # ---------- Key handling ----------
    def _format_ts(self):
        return local_now() if self.var_timestamp_local.get() else utc_now()

    def on_key(self, event):
        if self.logging_paused:
            return

        timestamp = self._format_ts()
        char = event.char if event.char else ""
        keysym = event.keysym
        printable = bool(char and char.isprintable())

        entry = {"timestamp": timestamp, "type": "KEY", "key": char if printable else keysym, "keysym": keysym,
                 "char": char if printable else None, "printable": printable, "note": ""}

        if printable and any(k.lower() in char.lower() for k in self.alert_keywords):
            entry["note"] = "⚠️ ALERT: sensitive keyword"

        if self.var_auto_redact.get() and printable:
            content = self.text_input.get("1.0", "end-1c")
            last_token = content.split()[-1] if content.strip() else char
            if looks_like_password(last_token):
                entry.update({"note": "AUTO-REDACTED", "key": "[REDACTED]", "char": None, "printable": False})

        if self.var_mask_sensitive.get() and printable:
            entry.update({"note": (entry.get("note", "") + " | MANUAL-MASK").strip(" |"),
                          "key": "[MASKED]", "char": None, "printable": False})

        self.events.append(entry)
        self.key_counts[keysym] = self.key_counts.get(keysym, 0) + 1
        self.total_keys += 1
        self.printable_keys += int(printable)
        self.special_keys += int(not printable)

        if not (self.var_trim_to_printable.get() and not entry["printable"]):
            color = self.alert if "ALERT" in entry.get("note", "") or "REDACTED" in entry.get("note", "") else self.fg
            self._append_log_line(f"{timestamp} — {entry['key']} (keysym={entry['keysym']}) {entry.get('note', '')}", color)

        self._update_status()

    def _append_log_line(self, text, color=None):
        self.log_area.config(state="normal")
        if color:
            tag_name = f"c{int(time.time() * 1000) % 100000}"
            self.log_area.insert("end", text + "\n", (tag_name,))
            self.log_area.tag_configure(tag_name, foreground=color)
        else:
            self.log_area.insert("end", text + "\n")
        self.log_area.see("end")
        self.log_area.config(state="disabled")

    def on_paste(self, event=None):
        if self.logging_paused:
            return
        ts = self._format_ts()
        try:
            data = self.root.clipboard_get()
        except Exception:
            data = "[clipboard unavailable]"
        entry = {"timestamp": ts, "type": "PASTE", "key": "[PASTE]", "char": data, "printable": True,
                 "note": f"Pasted len={len(data)}"}
        self.events.append(entry)
        self._append_log_line(f"{ts} — [PASTE] len={len(data)}")
        self._update_status()

    # ---------- Controls ----------
    def toggle_pause(self):
        self.logging_paused = not self.logging_paused
        messagebox.showinfo("Logger", "Paused" if self.logging_paused else "Resumed")

    def restart_session(self):
        """Restart everything fresh — clears all data, logs, and resets session timer"""
        if not messagebox.askyesno("Confirm Restart", "Are you sure you want to restart the session?\nAll current logs will be cleared."):
            return

        self.events.clear()
        self.key_counts.clear()
        self.total_keys = self.printable_keys = self.special_keys = 0
        self.session_start = time.time()

        self.log_area.config(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.config(state="disabled")

        self.text_input.delete("1.0", "end")
        self.text_input.insert("end", "")

        self.logging_paused = False
        self._update_status()
        messagebox.showinfo("Restarted", "Session restarted successfully!")

    def show_key_frequency(self):
        if not self.key_counts:
            messagebox.showinfo("No Data", "No keys logged yet.")
            return
        win = tk.Toplevel(self.root)
        win.title("Key Frequency")
        win.geometry("320x420")
        win.configure(bg=self.bg_main)
        lb = tk.Listbox(win, bg=self.panel, fg=self.fg, font=self.font)
        lb.pack(fill="both", expand=True, padx=8, pady=8)
        for k, v in sorted(self.key_counts.items(), key=lambda x: -x[1]):
            lb.insert("end", f"{k}: {v}")

    def _update_status(self):
        elapsed = int(time.time() - self.session_start)
        self.status_var.set(f"Total: {self.total_keys} | Printable: {self.printable_keys} | Special: {self.special_keys} | Time: {elapsed}s")

    def _timer_loop(self):
        while True:
            self._update_status()
            time.sleep(1)

    # ---------- Save / Export ----------
    def save_dialog(self):
        if not self.events:
            messagebox.showinfo("No Data", "No keystrokes recorded yet.")
            return
        choice = filedialog.asksaveasfilename(defaultextension=".txt",
                                              filetypes=[("Text", "*.txt"), ("CSV", "*.csv"), ("JSON", "*.json"),
                                                         ("Excel", "*.xlsx"), ("PDF", "*.pdf")],
                                              initialfile=f"keystroke_log_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")

        if not choice:
            return

        duration = int(time.time() - self.session_start)
        metadata = dict(self.session_meta)
        metadata.update({
            "duration_sec": duration,
            "events_count": len(self.events),
            "saved_at": utc_now(),
        })
        try:
            final = self.log_manager.save(choice, self.events, metadata)
            messagebox.showinfo("Saved", f"Saved log to:\n{final}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    # ---------- Clear ----------
    def clear_log(self):
        if messagebox.askyesno("Confirm", "Clear all logged events?"):
            self.events.clear()
            self.key_counts.clear()
            self.total_keys = self.printable_keys = self.special_keys = 0
            self.log_area.config(state="normal")
            self.log_area.delete("1.0", "end")
            self.log_area.config(state="disabled")
            self._update_status()


# ---------- Run ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = EthicalKeystrokeViewer(root)
    root.mainloop()
