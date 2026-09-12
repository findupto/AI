import html
import re
import sys
from datetime import datetime
from pathlib import Path
from threading import Event
from PySide6.QtCore import QThread, Signal, QSettings
from PySide6.QtGui import QTextCursor, QKeySequence, QShortcut, QFont
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QLineEdit, QPushButton, QFileDialog, QLabel, QMessageBox, QListWidget, QDialog, QDialogButtonBox, QComboBox, QInputDialog, QCheckBox, QSpinBox, QFormLayout
from orchestrator.core import Orchestrator
from orchestrator.export import session_to_markdown, session_to_html, session_to_json

class Worker(QThread):
    done=Signal(object)
    def __init__(self,action,*args): super().__init__(); self.action=action; self.args=args
    def run(self):
        try:self.done.emit({"ok":True,"value":self.action(*self.args)})
        except Exception as exc:self.done.emit({"ok":False,"value":str(exc)})

class StreamWorker(QThread):
    token=Signal(str); done=Signal(object)
    def __init__(self,action,*args): super().__init__(); self.action=action; self.args=args; self.stop_event=Event()
    def stop(self):self.stop_event.set()
    def run(self):
        try:self.done.emit({"ok":True,"value":self.action(*self.args,self.token.emit,self.stop_event)})
        except Exception as exc:self.done.emit({"ok":False,"value":str(exc)})

class DocumentDialog(QDialog):
    def __init__(self,documents,parent=None):
        super().__init__(parent); self.setWindowTitle("Local knowledge"); self.resize(700,400); layout=QVBoxLayout(self); self.list=QListWidget()
        for d in documents:self.list.addItem(f"{d['source']}  •  {d['characters']} chars  •  {d['created_at']}")
        layout.addWidget(self.list); row=QHBoxLayout(); delete=QPushButton("Remove selected"); delete.clicked.connect(self.accept); row.addWidget(delete); close=QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); row.addWidget(close); layout.addLayout(row)

class SettingsDialog(QDialog):
    def __init__(self,settings,parent=None):
        super().__init__(parent); self.setWindowTitle("Settings"); self.setMinimumWidth(420); self.settings=settings
        layout=QVBoxLayout(self); form=QFormLayout()
        self.theme=QComboBox(); self.theme.addItems(["Dark","System"]); self.theme.setCurrentText(settings.value("ui/theme","Dark")); form.addRow("Appearance",self.theme)
        self.timestamps=QCheckBox("Show message timestamps"); self.timestamps.setChecked(settings.value("ui/show_timestamps",True,type=bool)); form.addRow("Chat",self.timestamps)
        self.font_size=QSpinBox(); self.font_size.setRange(10,22); self.font_size.setValue(settings.value("ui/font_size",11,type=int)); form.addRow("Font size",self.font_size)
        self.restore_geometry=QCheckBox("Remember window size and position"); self.restore_geometry.setChecked(settings.value("ui/restore_geometry",True,type=bool)); form.addRow("Window",self.restore_geometry)
        layout.addLayout(form); buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); layout.addWidget(buttons)
    def values(self):return {"theme":self.theme.currentText(),"show_timestamps":self.timestamps.isChecked(),"font_size":self.font_size.value(),"restore_geometry":self.restore_geometry.isChecked()}

class Window(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Findupto AI — Standalone"); self.settings=QSettings("Findupto","AI"); self.pending_tool=None; self.worker=None; self._last_ingest_path=""; self._stream_text=""; self._stream_start=None; self._last_response=""; self._message_counter=0; self._messages={}; self.apply_preferences(False)
        if self.settings.value("ui/restore_geometry",True,type=bool) and self.settings.value("window/geometry",b""): self.restoreGeometry(self.settings.value("window/geometry"))
        else:self.resize(1000,720)
        self.o=Orchestrator(); root=QWidget(); self.setCentralWidget(root); layout=QVBoxLayout(root); model_state="Model ready" if self.o.llm.ready else f"Model not loaded — {self.o.llm.error or 'unknown error'}"; self.status=QLabel("Local AI • "+model_state); layout.addWidget(self.status)
        session_row=QHBoxLayout(); session_row.addWidget(QLabel("Chats")); self.sessions=QComboBox(); self.sessions.currentIndexChanged.connect(self.switch_session); session_row.addWidget(self.sessions,1)
        for text,slot in (("＋ New",self.new_session),("Rename",self.rename_session),("Delete",self.delete_session)): b=QPushButton(text); b.clicked.connect(slot); session_row.addWidget(b)
        layout.addLayout(session_row)
        search_row=QHBoxLayout(); self.search_input=QLineEdit(); self.search_input.setPlaceholderText("Search this conversation…  (Ctrl+F)"); self.search_input.returnPressed.connect(self.search_messages); search_row.addWidget(self.search_input,1); search_btn=QPushButton("Search"); search_btn.clicked.connect(self.search_messages); search_row.addWidget(search_btn); clear_search=QPushButton("Clear"); clear_search.clicked.connect(self.clear_search); search_row.addWidget(clear_search); layout.addLayout(search_row)
        self.chat=QTextBrowser(); self.chat.setReadOnly(True); self.chat.setOpenLinks(False); self.chat.setOpenExternalLinks(False); self.chat.anchorClicked.connect(self.anchor_clicked); layout.addWidget(self.chat)
        self.approval=QWidget(); approval_row=QHBoxLayout(self.approval); approval_row.setContentsMargins(0,0,0,0); self.approval_label=QLabel(); approval_row.addWidget(self.approval_label,1)
        for text,slot in (("Approve",self.approve_tool),("Reject",self.reject_tool)): b=QPushButton(text); b.clicked.connect(slot); approval_row.addWidget(b)
        self.approval.hide(); layout.addWidget(self.approval)
        row=QHBoxLayout(); self.input=QLineEdit(); self.input.setPlaceholderText("Ask your local AI…  (Ctrl+Enter to send)"); self.input.returnPressed.connect(self.send); row.addWidget(self.input)
        for text,slot in (("Send",self.send),("Stop",self.stop_generation),("Copy last",self.copy_last_response),("Export",self.export_conversation),("Choose model",self.choose_model),("Add document",self.ingest),("Knowledge",self.show_documents),("Settings",self.open_settings)):
            b=QPushButton(text); b.clicked.connect(slot); b.setEnabled(text!="Stop");
            if text=="Stop":self.stop_btn=b
            row.addWidget(b)
        layout.addLayout(row); self.install_shortcuts(); self.refresh_sessions(); self.apply_preferences(True)
        if not self.o.llm.ready:self.chat.append("<b>Model setup:</b> Choose a compatible GGUF model, or add one at models/model.gguf / set FINDUPTO_MODEL_PATH. Install the local extra with <code>pip install -e .[local]</code>.")

    def dark_stylesheet(self):
        return """QWidget{background:#111827;color:#e5e7eb;} QLabel{color:#cbd5e1;} QTextBrowser{background:#0b1220;border:1px solid #263244;border-radius:12px;padding:12px;} QLineEdit,QComboBox,QSpinBox{background:#0f172a;color:#f8fafc;border:1px solid #334155;border-radius:8px;padding:7px;} QLineEdit:focus,QComboBox:focus,QSpinBox:focus{border:1px solid #60a5fa;} QPushButton{background:#1f2937;color:#e5e7eb;border:1px solid #374151;border-radius:8px;padding:7px 11px;} QPushButton:hover{background:#374151;} QPushButton:pressed{background:#4b5563;} QPushButton:disabled{color:#6b7280;} QDialog{background:#111827;} QCheckBox{color:#e5e7eb;}"""
    def apply_preferences(self,initial=False):
        theme=self.settings.value("ui/theme","Dark"); app=QApplication.instance()
        if theme=="Dark":app.setStyleSheet(self.dark_stylesheet())
        else:app.setStyleSheet("")
        size=self.settings.value("ui/font_size",11,type=int); font=app.font(); font.setPointSize(size); app.setFont(font)
        self._show_timestamps=self.settings.value("ui/show_timestamps",True,type=bool)
        if not initial and hasattr(self,"chat"):self.load_session_view()
    def open_settings(self):
        if self.worker and self.worker.isRunning() or self.pending_tool:return
        dialog=SettingsDialog(self.settings,self)
        if dialog.exec()!=QDialog.Accepted:return
        values=dialog.values(); self.settings.setValue("ui/theme",values["theme"]); self.settings.setValue("ui/show_timestamps",values["show_timestamps"]); self.settings.setValue("ui/font_size",values["font_size"]); self.settings.setValue("ui/restore_geometry",values["restore_geometry"]); self.apply_preferences(); self.status.setText("Settings saved")
    def install_shortcuts(self):
        for key,slot in (("Ctrl+N",self.new_session),("Ctrl+F",lambda:self.search_input.setFocus()),("Ctrl+L",lambda:self.input.setFocus()),("Ctrl+Enter",self.send),("Escape",self.stop_generation),("Ctrl+Shift+C",self.copy_last_response),("Ctrl+Shift+E",self.export_conversation)):
            QShortcut(QKeySequence(key),self).activated.connect(slot)
    def start_worker(self,action,callback,*args):self.worker=Worker(action,*args);self.worker.done.connect(callback);self.worker.start()
    def refresh_sessions(self):
        sessions=self.o.list_sessions(); current=self.o.session_id; self.sessions.blockSignals(True); self.sessions.clear()
        for s in sessions:self.sessions.addItem(s["title"],s["id"])
        index=self.sessions.findData(current)
        if index>=0:self.sessions.setCurrentIndex(index)
        self.sessions.blockSignals(False); self.load_session_view()
    def active_session_title(self):
        return next((s["title"] for s in self.o.list_sessions() if s["id"]==self.o.session_id),"Conversation")
    def export_conversation(self):
        if self.worker and self.worker.isRunning() or self.pending_tool:return
        messages=self.o.session_messages()
        if not messages:QMessageBox.information(self,"Export conversation","There are no messages to export yet.");return
        path,_=QFileDialog.getSaveFileName(self,"Export conversation",self.active_session_title(),"Markdown (*.md);;HTML (*.html);;JSON (*.json)")
        if not path:return
        suffix=Path(path).suffix.lower()
        renderer={".md":session_to_markdown,".html":session_to_html,".json":session_to_json}.get(suffix)
        if renderer is None:
            QMessageBox.warning(self,"Export conversation","Choose a .md, .html, or .json filename.");return
        try:
            Path(path).write_text(renderer(messages,self.active_session_title()),encoding="utf-8")
        except Exception as exc:
            QMessageBox.warning(self,"Export failed",str(exc));return
        self.status.setText(f"Exported conversation to {Path(path).name}")
    def render_markdown(self,content):
        safe=html.escape(content); code_blocks=[]
        def replace_code(m):
            language=m.group(1).strip(); code=m.group(2).strip("\n"); i=len(code_blocks); label=f'<div><small>{html.escape(language) if language else "code"}</small></div>'; code_blocks.append(label+f'<pre><code>{code}</code></pre>'); return f"@@CODE{i}@@"
        safe=re.sub(r"```([A-Za-z0-9_+-]*)\n?(.*?)```",replace_code,safe,flags=re.DOTALL); safe=re.sub(r"`([^`\n]+)`",r"<code>\1</code>",safe); safe=re.sub(r"\*\*(.+?)\*\*",r"<b>\1</b>",safe); safe=re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)",r"<i>\1</i>",safe)
        rendered=[]; in_list=False; list_type=None
        for line in safe.splitlines():
            stripped=line.strip(); heading=re.match(r"^(#{1,3})\s+(.+)$",stripped); unordered=re.match(r"^[-*]\s+(.+)$",stripped); ordered=re.match(r"^\d+[.)]\s+(.+)$",stripped)
            if heading:
                if in_list:rendered.append(f"</{list_type}>");in_list=False
                rendered.append(f"<h{len(heading.group(1))}>{heading.group(2)}</h{len(heading.group(1))}>")
            elif unordered or ordered:
                wanted="ul" if unordered else "ol"; item=(unordered or ordered).group(1)
                if not in_list:rendered.append(f"<{wanted}>");in_list=True;list_type=wanted
                elif list_type!=wanted:rendered.append(f"</{list_type}><{wanted}>");list_type=wanted
                rendered.append(f"<li>{item}</li>")
            else:
                if in_list:rendered.append(f"</{list_type}>");in_list=False;list_type=None
                if stripped:rendered.append(f"<p>{line}</p>")
        if in_list:rendered.append(f"</{list_type}>")
        result="".join(rendered) if rendered else "<p></p>"
        for i,block in enumerate(code_blocks):result=result.replace(f"@@CODE{i}@@",block)
        return result
    def render_message(self,role,content,timestamp=None,mid=None,highlight=""):
        self._message_counter+=1; mid=mid or f"m{self._message_counter}"; self._messages[mid]=content; label="You" if role=="user" else "Findupto AI"; stamp=timestamp or datetime.now().strftime("%H:%M"); stamp_html=f' <small>{html.escape(str(stamp))}</small>' if self._show_timestamps else ""; body=html.escape(content).replace("\n","<br>") if role=="user" else self.render_markdown(content)
        if highlight:body=re.sub(re.escape(html.escape(highlight)),lambda m:f'<span style="background:#facc15;color:#111827">{m.group(0)}</span>',body,flags=re.IGNORECASE)
        button=f'<a href="copy:{html.escape(mid)}">Copy</a>'; bubble_class="user-bubble" if role=="user" else "ai-bubble"; bubble=f'<div class="{bubble_class}" style="margin:8px 4px;padding:10px 14px;border-radius:12px;"><div><b>{label}</b>{stamp_html} <small>•</small> {button}</div><div style="margin-top:5px;">{body}</div></div>'; self.chat.append(bubble)
    def load_session_view(self,highlight=""):
        self.chat.clear();self._last_response="";self._messages.clear();self._message_counter=0
        for message in self.o.session_messages():self.render_message(message["role"],message["content"],message.get("created_at"),highlight=highlight);self._last_response=message["content"] if message["role"]=="assistant" else self._last_response
    def search_messages(self):
        term=self.search_input.text().strip()
        if not term:self.load_session_view();return
        messages=[m for m in self.o.session_messages() if term.casefold() in m["content"].casefold()];self.chat.clear();self._messages.clear();self._message_counter=0
        if not messages:self.chat.append(f'<i>No messages found for “{html.escape(term)}”.</i>');return
        for message in messages:self.render_message(message["role"],message["content"],message.get("created_at"),highlight=term)
        self.status.setText(f"Found {len(messages)} matching message(s)")
    def clear_search(self):self.search_input.clear();self.load_session_view();self.status.setText("Local AI")
    def copy_message(self,mid):
        content=self._messages.get(mid)
        if content is not None:QApplication.clipboard().setText(content);self.status.setText("Message copied")
    def anchor_clicked(self,url):
        target=url.toString()
        if target.startswith("copy:"):self.copy_message(target[5:])
    def switch_session(self,index):
        if index<0 or (self.worker and self.worker.isRunning()) or self.pending_tool:return
        session_id=self.sessions.itemData(index)
        if session_id and self.o.switch_session(session_id):self.load_session_view();self.status.setText("Local AI")
    def new_session(self):
        if self.worker and self.worker.isRunning() or self.pending_tool:return
        title,ok=QInputDialog.getText(self,"New chat","Chat name:")
        if ok:self.o.new_session(title or "New chat");self.refresh_sessions();self.input.setFocus()
    def rename_session(self):
        if self.worker and self.worker.isRunning() or self.pending_tool:return
        title,ok=QInputDialog.getText(self,"Rename chat","Chat name:",text=self.sessions.currentText())
        if ok:self.o.rename_session(title);self.refresh_sessions()
    def delete_session(self):
        if self.worker and self.worker.isRunning() or self.pending_tool:return
        if len(self.o.list_sessions())<=1:QMessageBox.information(self,"Delete chat","At least one chat must remain.");return
        if QMessageBox.question(self,"Delete chat",f"Delete '{self.sessions.currentText()}' and its messages?")!=QMessageBox.Yes:return
        self.o.delete_session(self.o.session_id);self.refresh_sessions()
    def send(self):
        text=self.input.text().strip()
        if not text or (self.worker and self.worker.isRunning()) or self.pending_tool:return
        self.render_message("user",text);self.input.clear();self._stream_text="";self.chat.append("<p><b>Findupto AI</b> <small>now</small><br>");cursor=QTextCursor(self.chat.document());cursor.movePosition(QTextCursor.MoveOperation.End);self._stream_start=cursor.position();self.status.setText("Generating locally…");self.stop_btn.setEnabled(True);self.worker=StreamWorker(self.o.prepare_agent_request_stream,text);self.worker.token.connect(self.receive_token);self.worker.done.connect(self.receive_stream);self.worker.start()
    def receive_token(self,token):
        self._stream_text+=token
        if self._stream_start is None:return
        cursor=QTextCursor(self.chat.document());cursor.setPosition(self._stream_start);cursor.movePosition(QTextCursor.MoveOperation.End,QTextCursor.MoveMode.KeepAnchor);cursor.removeSelectedText();cursor.insertHtml(self.render_markdown(self._stream_text));self.chat.setTextCursor(cursor);self.chat.ensureCursorVisible()
    def stop_generation(self):
        if isinstance(self.worker,StreamWorker) and self.worker.isRunning():self.worker.stop();self.status.setText("Stopping generation…")
    def receive_stream(self,result):
        self.stop_btn.setEnabled(False);self._stream_start=None
        if not result["ok"]:self.chat.append(f"<b>Error:</b> {html.escape(str(result['value']))}");self.status.setText("Local AI • error");return
        value=result["value"];self._last_response=value.get("text","")
        if value.get("kind")=="tool_request":self.pending_tool=value;self.show_sources(value.get("sources",[]));self.approval_label.setText(f"Allow tool '{value['tool']}' to run?");self.approval.show();self.refresh_sessions();self.status.setText("Waiting for tool approval");return
        self.show_sources(value.get("sources",[]));self.refresh_sessions();self.status.setText("Generation stopped" if value.get("kind")=="stopped" else "Local AI")
    def show_sources(self,sources):
        if not sources:return
        self.chat.append("<b>Sources:</b>")
        for source in sources:self.chat.append(f"• {html.escape(source)}")
    def copy_last_response(self):
        if not self._last_response:return
        QApplication.clipboard().setText(self._last_response);self.status.setText("Copied last response")
    def choose_model(self):
        if self.worker and self.worker.isRunning() or self.pending_tool:return
        path,_=QFileDialog.getOpenFileName(self,"Choose local GGUF model",str(self.o.llm.resolve_path("models")),"GGUF models (*.gguf)")
        if not path:return
        self.status.setText("Loading local model…");self.start_worker(self.o.llm.load_model,self.receive_model,path)
    def receive_model(self,result):
        if not result["ok"]:self.status.setText("Local AI • model error");QMessageBox.warning(self,"Model load failed",str(result["value"]));return
        if not result["value"]:self.status.setText("Local AI • model error");QMessageBox.warning(self,"Model load failed",self.o.llm.error or "The model could not be loaded.");return
        self.chat.append(f"<i>Loaded local model: {Path(self.o.llm.model_path).name}</i>");self.status.setText(f"Local AI • {Path(self.o.llm.model_path).name}")
    def approve_tool(self):
        if not self.pending_tool:return
        p=self.pending_tool;self.approval.hide();self.status.setText("Running approved tool locally…");self.start_worker(self.o.approve_tool,self.receive_tool_result,p["user_text"],p["tool"],p["input"]);self.pending_tool=None
    def reject_tool(self):
        if not self.pending_tool:return
        p=self.pending_tool;self.approval.hide();self.status.setText("Rejecting tool request…");self.start_worker(self.o.reject_tool,self.receive_tool_result,p["user_text"],p["tool"],p["input"]);self.pending_tool=None
    def receive_tool_result(self,result):
        if not result["ok"]:self.chat.append(f"<b>Error:</b> {html.escape(str(result['value']))}");self.status.setText("Local AI • error");return
        self._last_response=result["value"];self.render_message("assistant",result["value"]);self.status.setText("Local AI")
    def ingest(self):
        path,_=QFileDialog.getOpenFileName(self,"Add local document","","Documents (*.txt *.md *.markdown *.json *.csv *.py *.pdf)")
        if not path or (self.worker and self.worker.isRunning()):return
        self._last_ingest_path=path;self.status.setText("Indexing document locally…");self.start_worker(self.o.ingest,self.receive_ingest,path)
    def receive_ingest(self,result):
        if not result["ok"]:QMessageBox.warning(self,"Document ingestion failed",str(result["value"]));self.status.setText("Local AI • error");return
        self.chat.append(f"<i>Indexed {Path(self._last_ingest_path).name} ({result['value']} characters) with local provenance.</i>");self.status.setText("Local AI")
    def show_documents(self):
        if self.worker and self.worker.isRunning() or self.pending_tool:return
        documents=self.o.list_documents()
        if not documents:QMessageBox.information(self,"Knowledge","No local documents are indexed yet.");return
        dialog=DocumentDialog(documents,self)
        if dialog.exec()==QDialog.Accepted and dialog.list.currentRow()>=0:
            source=documents[dialog.list.currentRow()]["source"]
            if QMessageBox.question(self,"Remove document",f"Remove this document from local knowledge?\n\n{source}")==QMessageBox.Yes and self.o.delete_document(source):self.chat.append(f"<i>Removed from local knowledge: {Path(source).name}</i>")
    def closeEvent(self,event):
        if self.settings.value("ui/restore_geometry",True,type=bool):self.settings.setValue("window/geometry",self.saveGeometry())
        if isinstance(self.worker,StreamWorker) and self.worker.isRunning():self.worker.stop()
        if self.worker and self.worker.isRunning():self.worker.quit();self.worker.wait(2000)
        self.o.memory.close();self.o.knowledge.close();event.accept()

def main():
    app=QApplication(sys.argv);app.setApplicationName("Findupto AI");w=Window();w.show();sys.exit(app.exec())
if __name__=="__main__":main()
