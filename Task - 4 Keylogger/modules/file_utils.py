# modules/file_utils.py
import os
import json
import csv
import platform
from datetime import datetime
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

class LogManager:
    """
    LogManager provides simple helpers to save keystroke events to multiple formats.
    Usage:
        lm = LogManager(base_dir="logs")
        lm.save(path, events, metadata)
    """

    def __init__(self, base_dir="logs"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _timestamp(self):
        return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    def _ensure_session_folder(self):
        sess = os.path.join(self.base_dir, f"session_{self._timestamp()}")
        os.makedirs(sess, exist_ok=True)
        return sess

    # ---------- Writers ----------
    def _write_txt(self, path, events, metadata):
        with open(path, "w", encoding="utf-8") as f:
            f.write("=== Session metadata ===\n")
            f.write(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
            f.write("========================\n\n")
            for e in events:
                if e.get("type") == "PASTE":
                    f.write(f"{e['timestamp']} — PASTE — len={len(e.get('char') or '')} — note={e.get('note','')}\n")
                else:
                    f.write(f"{e['timestamp']} — {e.get('key')} (keysym={e.get('keysym')}) {e.get('note','')}\n")

    def _write_csv(self, path, events, metadata):
        keys = ["timestamp", "type", "key", "keysym", "char", "printable", "note"]
        with open(path, "w", newline="", encoding="utf-8") as csvfile:
            # write metadata as commented header
            for line in ["=== Session metadata ==="] + [f"{k}: {v}" for k, v in metadata.items()] + ["========================"]:
                csvfile.write(f"# {line}\n")
            writer = csv.DictWriter(csvfile, fieldnames=keys)
            writer.writeheader()
            for e in events:
                writer.writerow({k: e.get(k, "") for k in keys})

    def _write_json(self, path, events, metadata):
        obj = {"metadata": metadata, "events": events}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)

    def _write_pdf(self, path, events, metadata):
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(path, pagesize=letter, title="Keystroke Session Report")
        story = []
        story.append(Paragraph("Ethical Keystroke Viewer — Session Report", styles["Title"]))
        story.append(Spacer(1, 8))
        story.append(Paragraph("Session metadata:", styles["Heading2"]))
        for k, v in metadata.items():
            story.append(Paragraph(f"<b>{k}:</b> {v}", styles["Normal"]))
        story.append(Spacer(1, 8))
        story.append(Paragraph("Captured events:", styles["Heading2"]))
        # Build a small table
        data = [["Timestamp", "Key", "Keysym", "Printable", "Note"]]
        for e in events:
            data.append([e.get("timestamp", ""), str(e.get("key", "")), str(e.get("keysym", "")), str(e.get("printable", "")), e.get("note", "")])
        story.append(Table(data))
        doc.build(story)

    def _write_xlsx(self, path, events, metadata):
        wb = Workbook()
        ws = wb.active
        ws.title = "Keystrokes"
        ws.append(["Timestamp", "Type", "Key", "Keysym", "Char", "Printable", "Note"])
        for e in events:
            ws.append([e.get("timestamp", ""), e.get("type",""), e.get("key",""), e.get("keysym",""), e.get("char",""), e.get("printable",""), e.get("note","")])
        meta = wb.create_sheet("Metadata")
        meta.append(["Key", "Value"])
        for k, v in metadata.items():
            meta.append([k, str(v)])
        wb.save(path)

    # ---------- Public save ----------
    def save(self, dest_path, events, metadata):
        """
        Save to dest_path (path must include filename and extension).
        Supported extensions: .txt, .csv, .json, .pdf, .xlsx
        If dest_path is inside the base_dir, it will be used as-is; otherwise,
        a session folder under base_dir will be created and the file written there.
        Returns the final path written.
        """
        dest_path = os.path.abspath(dest_path)
        _, ext = os.path.splitext(dest_path)
        ext = ext.lower().strip(".")
        # If user picked a path outside logs, create a session folder and write there instead for organization
        if os.path.commonpath([os.path.abspath(self.base_dir)]) != os.path.commonpath([os.path.abspath(dest_path), os.path.abspath(self.base_dir)]):
            session_folder = self._ensure_session_folder()
            filename = os.path.basename(dest_path)
            final = os.path.join(session_folder, filename)
        else:
            # dest is inside logs or same root — ensure folder exists
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            final = dest_path

        if ext == "txt":
            self._write_txt(final, events, metadata)
        elif ext == "csv":
            self._write_csv(final, events, metadata)
        elif ext == "json":
            self._write_json(final, events, metadata)
        elif ext == "pdf":
            self._write_pdf(final, events, metadata)
        elif ext == "xlsx":
            self._write_xlsx(final, events, metadata)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

        return final
