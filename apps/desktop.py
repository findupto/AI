import sys
from pathlib import Path
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QFileDialog, QLabel, QMessageBox
from orchestrator.core import Orchestrator


class Worker(QThread):
    done = Signal(str)
    def __init__(self, orchestrator, prompt):
        super().__init__(); self.o = orchestrator; self.prompt = prompt
    def run(self):
        self.done.emit(self.o.agent_answer(self.prompt))


class Window(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Findupto AI — Standalone"); self.resize(1000, 720)
        self.o = Orchestrator()
        root = QWidget(); self.setCentralWidget(root); layout = QVBoxLayout(root)
        self.status = QLabel("Local AI • " + ("Model ready" if self.o.llm.ready else "Model not loaded")); layout.addWidget(self.status)
        self.chat = QTextEdit(); self.chat.setReadOnly(True); layout.addWidget(self.chat)
        row = QHBoxLayout(); self.input = QLineEdit(); self.input.setPlaceholderText("Ask your local AI…"); self.input.returnPressed.connect(self.send); row.addWidget(self.input)
        send = QPushButton("Send"); send.clicked.connect(self.send); row.addWidget(send)
        file_btn = QPushButton("Add document"); file_btn.clicked.connect(self.ingest); row.addWidget(file_btn)
        layout.addLayout(row)
        if not self.o.llm.ready:
            self.chat.append("Add a GGUF model at models/model.gguf (or set FINDUPTO_MODEL_PATH) and install: pip install -e .[local]")

    def send(self):
        text = self.input.text().strip()
        if not text or hasattr(self, "worker") and self.worker.isRunning(): return
        self.chat.append(f"<b>You:</b> {text}"); self.input.clear(); self.status.setText("Thinking locally…")
        self.worker = Worker(self.o, text); self.worker.done.connect(self.receive); self.worker.start()

    def receive(self, text):
        self.chat.append(f"<b>Findupto AI:</b> {text}"); self.status.setText("Local AI")

    def ingest(self):
        path, _ = QFileDialog.getOpenFileName(self, "Add local document", "", "Documents (*.txt *.md *.markdown *.json *.csv *.py *.pdf)")
        if not path: return
        try:
            n = self.o.ingest(path); self.chat.append(f"<i>Indexed {Path(path).name} ({n} characters) with local provenance.</i>")
        except Exception as exc:
            QMessageBox.warning(self, "Document ingestion failed", str(exc))


def main():
    app = QApplication(sys.argv); app.setApplicationName("Findupto AI"); w = Window(); w.show(); sys.exit(app.exec())


if __name__ == "__main__": main()
