import sys
from pathlib import Path
from threading import Event
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QFileDialog, QLabel, QMessageBox, QListWidget, QDialog, QDialogButtonBox
from orchestrator.core import Orchestrator


class Worker(QThread):
    done = Signal(object)

    def __init__(self, action, *args):
        super().__init__()
        self.action = action
        self.args = args

    def run(self):
        try:
            self.done.emit({"ok": True, "value": self.action(*self.args)})
        except Exception as exc:
            self.done.emit({"ok": False, "value": str(exc)})


class StreamWorker(QThread):
    token = Signal(str)
    done = Signal(object)

    def __init__(self, action, *args):
        super().__init__()
        self.action = action
        self.args = args
        self.stop_event = Event()

    def stop(self):
        self.stop_event.set()

    def run(self):
        try:
            result = self.action(*self.args, self.token.emit, self.stop_event)
            self.done.emit({"ok": True, "value": result})
        except Exception as exc:
            self.done.emit({"ok": False, "value": str(exc)})


class DocumentDialog(QDialog):
    def __init__(self, documents, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Local knowledge")
        self.resize(700, 400)
        layout = QVBoxLayout(self)
        self.list = QListWidget()
        for document in documents:
            self.list.addItem(f"{document['source']}  •  {document['characters']} chars  •  {document['created_at']}")
        layout.addWidget(self.list)
        row = QHBoxLayout()
        delete = QPushButton("Remove selected")
        delete.clicked.connect(self.accept)
        row.addWidget(delete)
        close = QDialogButtonBox(QDialogButtonBox.Close)
        close.rejected.connect(self.reject)
        row.addWidget(close)
        layout.addLayout(row)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Findupto AI — Standalone")
        self.resize(1000, 720)
        self.o = Orchestrator()
        self.pending_tool = None
        self.worker = None
        self._last_ingest_path = ""
        self._stream_text = ""

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        model_state = "Model ready" if self.o.llm.ready else f"Model not loaded — {self.o.llm.error or 'unknown error'}"
        self.status = QLabel("Local AI • " + model_state)
        layout.addWidget(self.status)
        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        layout.addWidget(self.chat)

        self.approval = QWidget()
        approval_row = QHBoxLayout(self.approval)
        approval_row.setContentsMargins(0, 0, 0, 0)
        self.approval_label = QLabel()
        approval_row.addWidget(self.approval_label, 1)
        approve = QPushButton("Approve")
        approve.clicked.connect(self.approve_tool)
        approval_row.addWidget(approve)
        reject = QPushButton("Reject")
        reject.clicked.connect(self.reject_tool)
        approval_row.addWidget(reject)
        self.approval.hide()
        layout.addWidget(self.approval)

        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask your local AI…")
        self.input.returnPressed.connect(self.send)
        row.addWidget(self.input)
        send = QPushButton("Send")
        send.clicked.connect(self.send)
        row.addWidget(send)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_generation)
        self.stop_btn.setEnabled(False)
        row.addWidget(self.stop_btn)
        model_btn = QPushButton("Choose model")
        model_btn.clicked.connect(self.choose_model)
        row.addWidget(model_btn)
        file_btn = QPushButton("Add document")
        file_btn.clicked.connect(self.ingest)
        row.addWidget(file_btn)
        docs_btn = QPushButton("Knowledge")
        docs_btn.clicked.connect(self.show_documents)
        row.addWidget(docs_btn)
        layout.addLayout(row)

        if not self.o.llm.ready:
            self.chat.append("<b>Model setup:</b> Choose a compatible GGUF model, or add one at models/model.gguf / set FINDUPTO_MODEL_PATH. Install the local extra with <code>pip install -e .[local]</code>.")

    def start_worker(self, action, callback, *args):
        self.worker = Worker(action, *args)
        self.worker.done.connect(callback)
        self.worker.start()

    def send(self):
        text = self.input.text().strip()
        if not text or (self.worker and self.worker.isRunning()) or self.pending_tool:
            return
        self.chat.append(f"<b>You:</b> {text}")
        self.input.clear()
        self._stream_text = ""
        self.chat.append("<b>Findupto AI:</b> ")
        self.status.setText("Generating locally…")
        self.stop_btn.setEnabled(True)
        self.worker = StreamWorker(self.o.prepare_agent_request_stream, text)
        self.worker.token.connect(self.receive_token)
        self.worker.done.connect(self.receive_stream)
        self.worker.start()

    def receive_token(self, token):
        self._stream_text += token
        cursor = self.chat.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(token)
        self.chat.setTextCursor(cursor)
        self.chat.ensureCursorVisible()

    def stop_generation(self):
        if isinstance(self.worker, StreamWorker) and self.worker.isRunning():
            self.worker.stop()
            self.status.setText("Stopping generation…")

    def receive_stream(self, result):
        self.stop_btn.setEnabled(False)
        if not result["ok"]:
            self.chat.append(f"<b>Error:</b> {result['value']}")
            self.status.setText("Local AI • error")
            return
        value = result["value"]
        if value.get("kind") == "tool_request":
            self.pending_tool = value
            self.show_sources(value.get("sources", []))
            self.approval_label.setText(f"Allow tool '{value['tool']}' to run?")
            self.approval.show()
            self.status.setText("Waiting for tool approval")
            return
        self.show_sources(value.get("sources", []))
        if value.get("kind") == "stopped":
            self.status.setText("Generation stopped")
            return
        self.status.setText("Local AI")

    def show_sources(self, sources):
        if not sources:
            return
        self.chat.append("<b>Sources:</b>")
        for source in sources:
            self.chat.append(f"• {source}")

    def choose_model(self):
        if self.worker and self.worker.isRunning() or self.pending_tool:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Choose local GGUF model", str(self.o.llm.resolve_path("models")), "GGUF models (*.gguf)")
        if not path:
            return
        self.status.setText("Loading local model…")
        self.start_worker(self.o.llm.load_model, self.receive_model, path)

    def receive_model(self, result):
        if not result["ok"]:
            self.status.setText("Local AI • model error")
            QMessageBox.warning(self, "Model load failed", str(result["value"]))
            return
        if not result["value"]:
            self.status.setText("Local AI • model error")
            QMessageBox.warning(self, "Model load failed", self.o.llm.error or "The model could not be loaded.")
            return
        self.chat.append(f"<i>Loaded local model: {Path(self.o.llm.model_path).name}</i>")
        self.status.setText(f"Local AI • {Path(self.o.llm.model_path).name}")

    def approve_tool(self):
        if not self.pending_tool:
            return
        p = self.pending_tool
        self.approval.hide()
        self.status.setText("Running approved tool locally…")
        self.start_worker(self.o.approve_tool, self.receive_tool_result, p["user_text"], p["tool"], p["input"])
        self.pending_tool = None

    def reject_tool(self):
        if not self.pending_tool:
            return
        p = self.pending_tool
        self.approval.hide()
        self.status.setText("Rejecting tool request…")
        self.start_worker(self.o.reject_tool, self.receive_tool_result, p["user_text"], p["tool"], p["input"])
        self.pending_tool = None

    def receive_tool_result(self, result):
        if not result["ok"]:
            self.chat.append(f"<b>Error:</b> {result['value']}")
            self.status.setText("Local AI • error")
            return
        self.chat.append(f"<b>Findupto AI:</b> {result['value']}")
        self.status.setText("Local AI")

    def ingest(self):
        path, _ = QFileDialog.getOpenFileName(self, "Add local document", "", "Documents (*.txt *.md *.markdown *.json *.csv *.py *.pdf)")
        if not path or (self.worker and self.worker.isRunning()):
            return
        self._last_ingest_path = path
        self.status.setText("Indexing document locally…")
        self.start_worker(self.o.ingest, self.receive_ingest, path)

    def receive_ingest(self, result):
        if not result["ok"]:
            QMessageBox.warning(self, "Document ingestion failed", str(result["value"]))
            self.status.setText("Local AI • error")
            return
        self.chat.append(f"<i>Indexed {Path(self._last_ingest_path).name} ({result['value']} characters) with local provenance.</i>")
        self.status.setText("Local AI")

    def show_documents(self):
        if self.worker and self.worker.isRunning() or self.pending_tool:
            return
        documents = self.o.list_documents()
        if not documents:
            QMessageBox.information(self, "Knowledge", "No local documents are indexed yet.")
            return
        dialog = DocumentDialog(documents, self)
        if dialog.exec() == QDialog.Accepted and dialog.list.currentRow() >= 0:
            source = documents[dialog.list.currentRow()]["source"]
            if QMessageBox.question(self, "Remove document", f"Remove this document from local knowledge?\n\n{source}") == QMessageBox.Yes:
                if self.o.delete_document(source):
                    self.chat.append(f"<i>Removed from local knowledge: {Path(source).name}</i>")

    def closeEvent(self, event):
        if isinstance(self.worker, StreamWorker) and self.worker.isRunning():
            self.worker.stop()
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait(2000)
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Findupto AI")
    w = Window()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
