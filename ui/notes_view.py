"""
Notes View Module
Provides a UI for managing custom admin diagnostic notes.
CRUD Operations: Create, Read, Update, Delete
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextEdit, QDateEdit, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt, QDate
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_database


class NotesView(QWidget):
    """
    Diagnostics Notes management interface.
    Allows users to perform CRUD operations on admin notes.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        
        self.init_ui()
        self.load_notes()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📝 Admin Diagnostic Notes")
        titleFont = title.font()
        titleFont.setPointSize(16)
        titleFont.setBold(True)
        title.setFont(titleFont)
        main_layout.addWidget(title)
        
        # Form to Create Notes
        form_group = QGroupBox("Add New Note")
        form_layout = QVBoxLayout(form_group)
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Date for Note:"))
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        row1.addWidget(self.date_input)
        row1.addStretch()
        form_layout.addLayout(row1)
        
        form_layout.addWidget(QLabel("Diagnostic Note Details:"))
        self.note_text_input = QTextEdit()
        self.note_text_input.setMaximumHeight(80)
        self.note_text_input.setPlaceholderText("Enter system events, maintenance logs, or observations...")
        form_layout.addWidget(self.note_text_input)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.add_btn = QPushButton("Save Note")
        self.add_btn.setFixedWidth(120)
        self.add_btn.clicked.connect(self.add_note)
        self.add_btn.setStyleSheet("background-color: #2e8bc0; color: white; font-weight: bold;")
        btn_layout.addWidget(self.add_btn)
        form_layout.addLayout(btn_layout)
        
        main_layout.addWidget(form_group)
        
        # List of existing notes
        list_group = QGroupBox("Existing Notes")
        list_layout = QVBoxLayout(list_group)
        
        self.notes_table = QTableWidget()
        self.notes_table.setColumnCount(4)
        self.notes_table.setHorizontalHeaderLabels(["ID", "Target Date", "Note", "Created On"])
        self.notes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.notes_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.notes_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.notes_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.notes_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.notes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.notes_table.setSelectionMode(QTableWidget.SingleSelection)
        self.notes_table.setAlternatingRowColors(True)
        list_layout.addWidget(self.notes_table)
        
        action_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_notes)
        action_layout.addWidget(self.refresh_btn)
        
        action_layout.addStretch()
        
        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.clicked.connect(self.edit_selected_note)
        action_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected_note)
        self.delete_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        action_layout.addWidget(self.delete_btn)
        
        list_layout.addLayout(action_layout)
        
        main_layout.addWidget(list_group)
    
    def load_notes(self):
        """Read operations."""
        notes = self.db.get_all_notes()
        self.notes_table.setRowCount(len(notes))
        
        for row, note in enumerate(notes):
            self.notes_table.setItem(row, 0, QTableWidgetItem(str(note['id'])))
            self.notes_table.setItem(row, 1, QTableWidgetItem(note['target_date']))
            self.notes_table.setItem(row, 2, QTableWidgetItem(note['note_text']))
            self.notes_table.setItem(row, 3, QTableWidgetItem(note['timestamp']))
    
    def add_note(self):
        """Create operation."""
        target_date = self.date_input.date().toString(Qt.ISODate)
        text = self.note_text_input.toPlainText().strip()
        
        if not text:
            QMessageBox.warning(self, "Validation Error", "Note text cannot be empty.")
            return
            
        self.db.insert_note(target_date, text)
        self.note_text_input.clear()
        self.load_notes()
        QMessageBox.information(self, "Success", "Note added successfully.")
        
    def edit_selected_note(self):
        """Update operation."""
        selected_rows = self.notes_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a note to edit.")
            return
            
        row = selected_rows[0].row()
        note_id = int(self.notes_table.item(row, 0).text())
        current_text = self.notes_table.item(row, 2).text()
        
        new_text, ok = QInputDialog.getMultiLineText(
            self, "Edit Note", "Modify note text:", current_text
        )
        
        if ok and new_text.strip():
            self.db.update_note(note_id, new_text.strip())
            self.load_notes()
            QMessageBox.information(self, "Success", "Note updated successfully.")
            
    def delete_selected_note(self):
        """Delete operation."""
        selected_rows = self.notes_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a note to delete.")
            return
            
        row = selected_rows[0].row()
        note_id = int(self.notes_table.item(row, 0).text())
        
        reply = QMessageBox.question(
            self, 'Confirm Deletion', 
            "Are you sure you want to delete this note?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db.delete_note(note_id)
            self.load_notes()
            QMessageBox.information(self, "Success", "Note deleted.")
