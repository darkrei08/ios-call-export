#!/usr/bin/env python3
"""Cross-platform GUI for the iOS Call Exporter."""

import sys
import os
import threading
from datetime import datetime
from pathlib import Path

# Tkinter imports with clear installation instructions for Linux package managers
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from tkinter.scrolledtext import ScrolledText
except ImportError:
    print("=" * 60)
    print("ERROR: Tkinter is missing! To run this GUI, please install it:")
    print("  Debian/Ubuntu: sudo apt install python3-tk")
    print("  Fedora:        sudo dnf install python3-tkinter")
    print("  Arch Linux:    sudo pacman -S tk")
    print("=" * 60)
    sys.exit(1)

# Try to import the core modules
try:
    from export_calls import find_backups
except ImportError:
    # Append current directory to path if launched from outside
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from export_calls import find_backups


class TextRedirector:
    """Redirects stdout/stderr to a Tkinter Text widget."""
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.configure(state='normal')
        self.text_widget.insert('end', string)
        self.text_widget.see('end')
        self.text_widget.configure(state='disabled')

    def flush(self):
        pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("iOS Call Exporter")
        self.geometry("760x740")
        
        # Center the window on the screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # State variables
        self.is_dark_mode = False
        self.backups = []
        self.selected_backup_dir = ""
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        # Set up modern TTK styling (Premium Material Design)
        self.setup_styles()

        # Create GUI layout
        self.create_widgets()
        
        # Auto-detect backups
        self.detect_backups()

    def setup_styles(self):
        style = ttk.Style()
        # Fall back to clam theme for custom styling control across platforms
        style.theme_use('clam')
        
        # Premium Colors definition
        if getattr(self, 'is_dark_mode', False):
            self.bg_color = "#121212"
            self.card_color = "#1E1E1E"
            self.primary_color = "#0A84FF"  # Apple Dark Blue
            self.primary_active = "#409CFF"
            self.text_color = "#F9FAFB"
            self.sub_text_color = "#9CA3AF"
            self.border_color = "#374151"
            self.log_bg = "#000000"
            self.log_fg = "#A7F3D0" # Soft green for terminal
        else:
            self.bg_color = "#F3F4F6"
            self.card_color = "#FFFFFF"
            self.primary_color = "#007AFF"  # Apple Light Blue
            self.primary_active = "#0056B3"
            self.text_color = "#111827"
            self.sub_text_color = "#6B7280"
            self.border_color = "#E5E7EB"
            self.log_bg = "#1F2937"
            self.log_fg = "#E5E7EB"
            
        bg_color = self.bg_color
        card_color = self.card_color
        primary_color = self.primary_color
        primary_active = self.primary_active
        text_color = self.text_color
        sub_text_color = self.sub_text_color
        border_color = self.border_color

        self.configure(bg=bg_color)

        style.configure('TFrame', background=bg_color)
        style.configure('Card.TFrame', background=card_color)
        
        # Typography
        title_font = ('Segoe UI', 20, 'bold')
        subtitle_font = ('Segoe UI', 10)
        section_font = ('Segoe UI', 12, 'bold')
        label_font = ('Segoe UI', 10)
        btn_font = ('Segoe UI', 10, 'bold')
        
        style.configure('TLabel', background=bg_color, foreground=text_color, font=label_font)
        style.configure('Title.TLabel', background=card_color, foreground=primary_color, font=title_font)
        style.configure('Subtitle.TLabel', background=card_color, foreground=sub_text_color, font=subtitle_font)
        style.configure('Section.TLabel', background=bg_color, foreground=text_color, font=section_font)
        
        style.configure('TCheckbutton', background=bg_color, foreground=text_color, font=label_font)
        
        # Entries
        style.configure('TEntry', fieldbackground=card_color, bordercolor=border_color, lightcolor=border_color, darkcolor=border_color, insertcolor=text_color, foreground=text_color, padding=6)
        
        # Combobox
        style.configure('TCombobox', fieldbackground=card_color, background=card_color, arrowcolor=text_color, bordercolor=border_color, foreground=text_color, padding=6)
        style.map('TCombobox', fieldbackground=[('readonly', card_color)])
        
        # Primary Button (Solid Blue)
        style.configure('Primary.TButton', background=primary_color, foreground='#ffffff', font=btn_font, borderwidth=0, focuscolor=primary_color, padding=10)
        style.map('Primary.TButton',
                  background=[('active', primary_active), ('disabled', border_color)],
                  foreground=[('disabled', '#9CA3AF')])

        # Secondary Button (Bordered White/Dark)
        style.configure('Secondary.TButton', background=card_color, foreground=primary_color, font=label_font, borderwidth=1, bordercolor=border_color, focuscolor=card_color, padding=6)
        style.map('Secondary.TButton',
                  background=[('active', border_color)])

    def create_widgets(self):
        # 1. Header (Banner)
        self.header_frame = ttk.Frame(self, height=100)
        self.header_frame.pack(fill='x', side='top')
        self.header_frame.pack_propagate(False)
        
        # Material design bottom accent line
        self.accent_line = ttk.Frame(self, height=1)
        self.accent_line.pack(fill='x', side='top')

        # Theme toggle button
        self.btn_theme = ttk.Button(self.header_frame, text="🌙 Tema Scuro", style="Secondary.TButton", command=self.switch_theme)
        self.btn_theme.pack(side='right', padx=32, pady=32)

        title_label = tttk.Label(self.header_frame, text="iOS Backup Explorer", style="Title.TLabel")
        title_label.pack(anchor='w', padx=32, pady=(20, 4))
        
        subtitle_label = tttk.Label(self.header_frame, text="Esplora ed esporta dati dai tuoi backup iOS crittografati.", style="Subtitle.TLabel")
        subtitle_label.pack(anchor='w', padx=32)

        # Main scrollable container
        container = tttk.Frame(self, padding=16)
        container.pack(fill='both', expand=True)

        # Global Credentials Section
        cred_frame = ttk.Frame(container, padx=16, pady=16)
        cred_frame.configure(highlightthickness=0)
        cred_frame.pack(fill='x', pady=(0, 16))
        
        lbl_font = ('Segoe UI', 10, 'bold')
        self.lbl_backup = ttk.Label(cred_frame, text="Backup iOS di origine:", font=lbl_font)
        self.lbl_backup.grid(row=0, column=0, sticky='w', pady=8)
        
        self.backup_var = tk.StringVar()
        self.backup_combobox = ttk.Combobox(cred_frame, textvariable=self.backup_var, state='readonly', width=50)
        self.backup_combobox.grid(row=0, column=1, sticky='we', padx=(16, 16), pady=8, ipady=4)
        self.backup_combobox.bind("<<ComboboxSelected>>", self.on_backup_selected)
        
        btn_browse_backup = ttk.Button(cred_frame, text="Sfoglia...", style="Secondary.TButton", command=self.browse_backup)
        btn_browse_backup.grid(row=0, column=2, pady=8)

        self.lbl_pass = ttk.Label(cred_frame, text="Password del backup:", font=lbl_font)
        self.lbl_pass.grid(row=1, column=0, sticky='w', pady=8)
        
        self.pass_var = tk.StringVar()
        self.pass_entry = ttk.Entry(cred_frame, textvariable=self.pass_var, show="*", width=50)
        self.pass_entry.grid(row=1, column=1, sticky='we', padx=(16, 16), pady=8, ipady=4)
        
        self.show_pass_var = tk.BooleanVar(value=False)
        self.show_pass_check = ttk.Checkbutton(cred_frame, text="Mostra", variable=self.show_pass_var, command=self.toggle_pass_visibility)
        self.show_pass_check.grid(row=1, column=2, sticky='w', pady=8)
        cred_frame.columnconfigure(1, weight=1)

        # Notebook for Tabs
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill='both', expand=True, pady=(0, 16))
        
        # Tab 1: Export
        self.tab_export = tttk.Frame(self.notebook)
        self.tab_view_calls = tttk.Frame(self.notebook)
        self.tab_view_msgs = tttk.Frame(self.notebook)
        self.tab_explorer = tttk.Frame(self.notebook)
        self.tab_wifi = tttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_export, text="📥 Esportazioni")
        self.notebook.add(self.tab_view_calls, text="📞 Vista Chiamate")
        self.notebook.add(self.tab_view_msgs, text="💬 Vista Messaggi")
        self.notebook.add(self.tab_explorer, text="📂 File Explorer")
        self.notebook.add(self.tab_wifi, text="📶 Wi-Fi Passwords")
        
        # --- TAB 1: Esportazioni ---
        self.create_export_tab()

        # --- TAB 2/3: Viewers ---
        self.create_view_calls_tab()
        self.create_view_msgs_tab()

        # Tab 4: Explorer
        self.create_explorer_tab()

        # Tab 5: Wi-Fi
        self.create_wifi_tab()

        # Log Section
        # Log is now in the first tab
        
        # Viewer Backend
        self.db_backend = None
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_export_tab(self):
        container = ttk.Frame(self.tab_export, padx=16, pady=16)
        container.pack(fill='both', expand=True)

        lbl_desc = tttk.Label(container, text="Seleziona i dati da esportare dal tuo backup crittografato.", style="TLabel")
        lbl_desc.pack(anchor='w', pady=(0, 16))

        # Checkboxes for export types
        self.export_calls_var = tk.BooleanVar(value=True)
        self.export_msgs_var = tk.BooleanVar(value=False)

        chk_calls = tttk.Checkbutton(container, text="📞 Cronologia Chiamate (CSV)", variable=self.export_calls_var)
        chk_calls.pack(anchor='w', pady=(0, 4))

        chk_msgs = tttk.Checkbutton(container, text="💬 Messaggi SMS e iMessage (HTML Viewer Interattivo)", variable=self.export_msgs_var)
        chk_msgs.pack(anchor='w', pady=(0, 16))

        # Config Frame
        config_frame = ttk.LabelFrame(container, text="Impostazioni Chiamate", padx=16, pady=16)
        config_frame.pack(fill='x', pady=(0, 20))
        
        self.excel_var = tk.BooleanVar(value=True)
        chk_excel = tttk.Checkbutton(config_frame, text="Ottimizza CSV per Microsoft Excel (usa punto e virgola come separatore)", variable=self.excel_var)
        chk_excel.pack(anchor='w')

        # Action Bar
        action_frame = ttk.Frame(container)
        action_frame.pack(fill='x', pady=8)

        self.btn_export = ttk.Button(action_frame, text="AVVIA ESPORTAZIONE", style="Primary.TButton", command=self.start_export)
        self.btn_export.pack(side='left')

        self.spinner = ttk.Progressbar(action_frame, mode='indeterminate', length=150)
        
        lbl_logs = tttk.Label(container, text="Log Operazioni:", style="TLabel")
        lbl_logs.pack(anchor='w', pady=(16, 4))
        
        self.log_text = ScrolledText(container, height=10, padx=8, pady=8)
        self.log_text.pack(fill='both', expand=True)

    # --- Live Data Viewers ---
    def load_db_backend(self):
        if not self.selected_backup_dir:
            messagebox.showerror("Errore", "Nessun backup selezionato.")
            return

        passphrase = self.pass_var.get().strip()
        if not passphrase:
            if not messagebox.askyesno("Attenzione", "Password vuota. Continuare?"):
                return
                
        self.log_message("⏳ Caricamento dei database (Chiamate & Messaggi) in corso...\n")
        
        def _load():
            try:
                from db_viewers import DataViewerBackend
                if self.db_backend:
                    self.db_backend.close()
                self.db_backend = DataViewerBackend(self.selected_backup_dir, passphrase)
                self.db_backend.load_databases()
                self.after(0, self._on_db_loaded)
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda err=err_msg: messagebox.showerror("Errore", err))
        
        threading.Thread(target=_load, daemon=True).start()

    def _on_db_loaded(self):
        self.log_message("✅ Database caricati in memoria locale. Pronti per la ricerca veloce.\n")
        self.update_calls_view()
        self.update_msgs_view()

    def create_view_calls_tab(self):
        container = ttk.Frame(self.tab_view_calls, padx=16, pady=16)
        container.pack(fill='both', expand=True)
        
        top_frame = ttk.Frame(container)
        top_frame.pack(fill='x', pady=(0, 10))
        
        btn_load = ttk.Button(top_frame, text="Carica/Aggiorna Dati dal Backup", command=self.load_db_backend)
        btn_load.pack(side='left')
        
        self.search_calls_var = tk.StringVar()
        self.search_calls_var.trace("w", lambda *args: self.after(300, self.update_calls_view))
        search_entry = ttk.Entry(top_frame, textvariable=self.search_calls_var, width=40)
        search_entry.pack(side='right')
        tttk.Label(top_frame, text="Cerca:").pack(side='right', padx=8)
        
        columns = ("Data", "Contatto/Numero", "Durata", "Direzione", "Servizio")
        self.tree_calls = ttk.Treeview(container, columns=columns, show='headings', selectmode='browse')
        for col in columns:
            self.tree_calls.heading(col, text=col)
            self.tree_calls.column(col, width=150)
            
        scroll = ttk.Scrollbar(container, orient="vertical", command=self.tree_calls.yview)
        self.tree_calls.configure(yscrollcommand=scroll.set)
        self.tree_calls.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')

    def update_calls_view(self):
        if not self.db_backend:
            return
        term = self.search_calls_var.get()
        results = self.db_backend.search_calls(term)
        self.tree_calls.delete(*self.tree_calls.get_children())
        for r in results:
            self.tree_calls.insert("", "end", values=r)

    def create_view_msgs_tab(self):
        container = ttk.Frame(self.tab_view_msgs, padx=16, pady=16)
        container.pack(fill='both', expand=True)
        
        top_frame = ttk.Frame(container)
        top_frame.pack(fill='x', pady=(0, 10))
        
        btn_load = ttk.Button(top_frame, text="Carica/Aggiorna Dati dal Backup", command=self.load_db_backend)
        btn_load.pack(side='left')
        
        self.search_msgs_var = tk.StringVar()
        self.search_msgs_var.trace("w", lambda *args: self.after(300, self.update_msgs_view))
        search_entry = ttk.Entry(top_frame, textvariable=self.search_msgs_var, width=40)
        search_entry.pack(side='right')
        tttk.Label(top_frame, text="Cerca (Testo o Numero):").pack(side='right', padx=8)
        
        columns = ("Data", "Contatto", "Direzione", "Servizio", "Testo")
        self.tree_msgs = ttk.Treeview(container, columns=columns, show='headings', selectmode='browse')
        self.tree_msgs.heading("Data", text="Data")
        self.tree_msgs.heading("Contatto", text="Contatto")
        self.tree_msgs.heading("Direzione", text="Direzione")
        self.tree_msgs.heading("Servizio", text="Servizio")
        self.tree_msgs.heading("Testo", text="Testo del Messaggio")
        
        self.tree_msgs.column("Data", width=150, stretch=False)
        self.tree_msgs.column("Contatto", width=150, stretch=False)
        self.tree_msgs.column("Direzione", width=80, stretch=False)
        self.tree_msgs.column("Servizio", width=80, stretch=False)
        self.tree_msgs.column("Testo", width=400, stretch=True)
            
        scroll = ttk.Scrollbar(container, orient="vertical", command=self.tree_msgs.yview)
        self.tree_msgs.configure(yscrollcommand=scroll.set)
        self.tree_msgs.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')

    def update_msgs_view(self):
        if not self.db_backend:
            return
        term = self.search_msgs_var.get()
        results = self.db_backend.search_messages(term)
        self.tree_msgs.delete(*self.tree_msgs.get_children())
        for r in results:
            self.tree_msgs.insert("", "end", values=r)

    def create_explorer_tab(self):
        container = ttk.Frame(self.tab_explorer, padx=16, pady=16)
        container.pack(fill='both', expand=True)
        
        # Source selector
        source_frame = ttk.Frame(container)
        source_frame.pack(fill='x', pady=(0, 12))
        
        self.source_var = tk.StringVar(value="backup")
        rb_backup = ttk.Radiobutton(source_frame, text="📁 Backup Locale", variable=self.source_var, value="backup", command=self.on_source_changed)
        rb_backup.pack(side='left', padx=(0, 16))
        
        rb_live = ttk.Radiobutton(source_frame, text="📱 Dispositivo Collegato (Live)", variable=self.source_var, value="live", command=self.on_source_changed)
        rb_live.pack(side='left')
        
        self.live_path_var = tk.StringVar(value="/")
        
        # Action Bar
        self.action_frame = ttk.Frame(container)
        self.action_frame.pack(fill='x', pady=(0, 12))
        
        self.btn_load_files = ttk.Button(self.action_frame, text="Carica Lista File", style="Primary.TButton", command=self.load_explorer_data)
        self.btn_load_files.pack(side='left')
        
        self.btn_up_dir = ttk.Button(self.action_frame, text="⬆️ Su", command=self.go_up_dir)
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_files)
        self.search_entry = ttk.Entry(self.action_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side='right')
        self.lbl_search = tttk.Label(self.action_frame, text="Cerca:", style="TLabel")
        self.lbl_search.pack(side='right', padx=8)

        # Path label for Live mode
        self.lbl_live_path = tttk.Label(container, text="Percorso: /", style="TLabel")

        columns = ("col1", "col2")
        self.file_tree = ttk.Treeview(container, columns=columns, show='headings', selectmode='browse')
        self.file_tree.heading("col1", text="Dominio / Nome")
        self.file_tree.heading("col2", text="Percorso File / Tipo")
        self.file_tree.column("col1", width=200, stretch=False)
        self.file_tree.column("col2", width=400, stretch=True)
        
        # Double click event for navigating directories
        self.file_tree.bind("<Double-1>", self.on_tree_double_click)
        
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        self.file_tree.pack(side='top', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill='x', side='bottom', pady=(12,0))
        
        self.btn_extract_file = ttk.Button(btn_frame, text="Estrai Elemento Selezionato", style="Secondary.TButton", command=self.extract_selected_file)
        self.btn_extract_file.pack(side='right')
        
        self.on_source_changed()

    def create_wifi_tab(self):
        container = ttk.Frame(self.tab_wifi, padx=24, pady=24)
        container.pack(fill='both', expand=True)
        
        tttk.Label(container, text="Estrazione Password Wi-Fi (In arrivo)", style="Section.TLabel").pack(pady=(0, 16))
        
        msg = ("Le password del Wi-Fi sono conservate nel Keychain cifrato del dispositivo.\n"
               "L'estrazione del Keychain richiederà una gestione avanzata della decrittografia.\n\n"
               "Questa funzionalità sarà implementata nella prossima versione.")
        ttk.Label(container, text=msg, justify='left').pack(anchor='w')


    
    def switch_theme(self):
        import sv_ttk
        self.is_dark_mode = not self.is_dark_mode
        sv_ttk.set_theme('dark' if self.is_dark_mode else 'light')

    def old_toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.setup_styles()
        
        # Update specific standard tk widgets
        self.configure(bg=self.bg_color)
        self.header_frame.configure(bg=self.card_color)
        self.accent_line.configure(bg=self.border_color)
        
        self.lbl_backup.configure(bg=self.card_color)
        self.lbl_pass.configure(bg=self.card_color)
        self.show_pass_check.configure(bg=self.card_color)
        
        self.log_text.configure(bg=self.log_bg)

        if self.is_dark_mode:
            self.btn_theme.configure(text="☀️ Tema Chiaro")
        else:
            self.btn_theme.configure(text="🌙 Tema Scuro")

    def toggle_pass_visibility(self):
        if self.show_pass_var.get():
            self.pass_entry.configure(show="")
        else:
            self.pass_entry.configure(show="*")

    def detect_backups(self):
        try:
            self.backups = find_backups()
            if self.backups:
                options = []
                for b in self.backups:
                    mtime = datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                    options.append(f"{b.name} (Modificato: {mtime})")
                
                self.backup_combobox.configure(values=options)
                self.backup_combobox.current(0)
                self.selected_backup_dir = str(self.backups[0])
                self.log_message(f"✅ Rilevati automaticamente {len(self.backups)} backup sul sistema.\nSelezionato il più recente.\n\n")
            else:
                self.backup_combobox.configure(values=["Nessun backup trovato automaticamente - Clicca Sfoglia..."])
                self.backup_combobox.current(0)
                self.selected_backup_dir = ""
                self.log_message("⚠️ AVVISO: Nessun backup iOS rilevato nelle cartelle di default.\nSeleziona manualmente la cartella del backup cliccando su 'Sfoglia...'.\n\n")
        except Exception as e:
            self.log_message(f"❌ Errore durante la scansione automatica dei backup: {e}\n\n")

    def on_backup_selected(self, event):
        idx = self.backup_combobox.current()
        if self.backups and 0 <= idx < len(self.backups):
            self.selected_backup_dir = str(self.backups[idx])
        else:
            self.selected_backup_dir = ""

    def browse_backup(self):
        dir_path = filedialog.askdirectory(title="Seleziona la cartella del backup iOS (contenente Manifest.db)")
        if dir_path:
            # Check if Manifest.db exists in that directory
            if not (Path(dir_path) / "Manifest.db").exists():
                messagebox.showwarning(
                    "Verifica Cartella",
                    "Attenzione: la cartella selezionata non sembra contenere il file 'Manifest.db'.\nAssicurati che sia una cartella di backup valida."
                )
            self.selected_backup_dir = dir_path
            self.backup_var.set(dir_path)
            self.log_message(f"📁 Selezionato manualmente backup in: {dir_path}\n")

    def log_message(self, message):
        self.log_text.configure(state='normal')
        self.log_text.insert('end', message)
        self.log_text.see('end')
        self.log_text.configure(state='disabled')

    def start_export(self):
        if not self.selected_backup_dir:
            messagebox.showerror("Errore", "Nessun backup selezionato. Sfoglia e seleziona una cartella di backup valida.")
            return

        passphrase = self.pass_var.get().strip()
        if not passphrase:
            if not messagebox.askyesno("Attenzione", "Hai lasciato la password vuota. Se il backup è crittografato l'esportazione fallirà.\nVuoi procedere comunque?"):
                return
                
        if not self.export_calls_var.get() and not self.export_msgs_var.get():
            messagebox.showwarning("Nessuna selezione", "Seleziona almeno una voce da esportare (Chiamate o Messaggi).")
            return

        self.btn_export.configure(state='disabled')
        self.spinner.pack(side='left', padx=16)
        self.spinner.start()
        self.log_text.delete(1.0, tk.END)

        self.log_message("⏳ Inizializzazione in corso...\n")

        thread = threading.Thread(
            target=self._run_export,
            args=(self.selected_backup_dir, passphrase, self.excel_var.get(), self.export_calls_var.get(), self.export_msgs_var.get()),
            daemon=True
        )
        thread.start()

    def _run_export(self, backup_dir, passphrase, use_excel, do_calls, do_msgs):
        try:
            if do_calls:
                from export_calls import process_and_export_calls
                out_csv = str(Path.home() / "Desktop" / "calls.csv")
                self.log_message("📞 Avvio estrazione Chiamate...\n")
                process_and_export_calls(backup_dir, passphrase, out_csv, use_excel)
                self.log_message(f"✅ Chiamate esportate con successo in:\n{out_csv}\n\n")
                
            if do_msgs:
                from export_messages import export_messages_to_html
                out_html = str(Path.home() / "Desktop" / "Messages_Viewer.html")
                self.log_message("💬 Avvio estrazione Messaggi (SMS & iMessage)...\n")
                count = export_messages_to_html(backup_dir, passphrase, out_html)
                self.log_message(f"✅ Trovate {count} conversazioni.\n")
                self.log_message(f"✅ Messaggi esportati con successo nel Visualizzatore HTML in:\n{out_html}\n\n")

            self.after(0, self._export_success)
        except Exception as e:
            import traceback
            err_details = traceback.format_exc()
            self.after(0, self._export_failure, str(e), err_details)

    def _export_success(self):
        self.spinner.stop()
        self.spinner.pack_forget()
        self.btn_export.configure(state='normal')
        self.log_message("✅ Tutte le operazioni di esportazione sono state completate!\nControlla i file sul Desktop.\n")
        messagebox.showinfo("Successo", "Esportazione completata!\nControlla i file sul Desktop.")

    def _export_failure(self, error_msg, details):
        self.spinner.stop()
        self.spinner.pack_forget()
        self.btn_export.configure(state='normal')
        self.log_message(f"❌ Errore durante l'esportazione: {error_msg}\n")
        messagebox.showerror("Errore Esportazione", f"Si è verificato un errore:\n{error_msg}")

    # --- File Explorer Methods ---

    def on_source_changed(self):
        source = self.source_var.get()
        if source == "backup":
            self.lbl_live_path.pack_forget()
            self.btn_up_dir.pack_forget()
            self.file_tree.heading("col1", text="Dominio (App)")
            self.file_tree.heading("col2", text="Percorso File")
        else:
            self.lbl_live_path.pack(side='top', fill='x', pady=4)
            self.btn_up_dir.pack(side='left', padx=8)
            self.file_tree.heading("col1", text="Nome")
            self.file_tree.heading("col2", text="Tipo")
        
        self.file_tree.delete(*self.file_tree.get_children())
        self.all_files = []

    def load_explorer_data(self):
        source = self.source_var.get()
        if source == "backup":
            self.load_backup_files()
        else:
            self.live_path_var.set("/")
            self.load_live_files()

    def load_backup_files(self):
        if not self.selected_backup_dir:
            messagebox.showerror("Dati Mancanti", "Seleziona o sfoglia una cartella di backup valida prima di procedere.")
            return

        passphrase = self.pass_var.get().strip()
        if not passphrase:
            if not messagebox.askyesno("Password vuota", "Hai inserito una password vuota. Se il backup è crittografato, la lettura fallirà.\nVuoi continuare lo stesso?"):
                return

        self.btn_load_files.configure(state='disabled', text="Caricamento in corso...")
        self.file_tree.delete(*self.file_tree.get_children())
        self.all_files = []

        thread = threading.Thread(
            target=self._run_load_backup_files,
            args=(self.selected_backup_dir, passphrase),
            daemon=True
        )
        thread.start()

    def _run_load_backup_files(self, backup_dir, passphrase):
        try:
            from backup_explorer import get_backup_files
            files = get_backup_files(backup_dir, passphrase)
            self.after(0, self._populate_backup_tree, files, None)
        except Exception as e:
            self.after(0, self._populate_backup_tree, [], str(e))

    def _populate_backup_tree(self, files, error_msg):
        self.btn_load_files.configure(state='normal', text="Carica Lista File")
        if error_msg:
            messagebox.showerror("Errore di Caricamento", f"Impossibile leggere il backup:\n{error_msg}")
            return
            
        self.all_files = files
        for f in files:
            self.file_tree.insert("", "end", values=(f["domain"], f["relativePath"]))
        
        self.log_message(f"📁 File Explorer: Caricati {len(files)} file dal backup.\n")

    def load_live_files(self):
        self.btn_load_files.configure(state='disabled', text="Connessione in corso...")
        self.file_tree.delete(*self.file_tree.get_children())
        self.all_files = []
        
        path = self.live_path_var.get()
        self.lbl_live_path.configure(text=f"Percorso: {path}")

        thread = threading.Thread(
            target=self._run_load_live_files,
            args=(path,),
            daemon=True
        )
        thread.start()

    def _run_load_live_files(self, path):
        try:
            from live_device_explorer import get_connected_device_info, list_live_files
            info = get_connected_device_info()
            files = list_live_files(path)
            self.after(0, self._populate_live_tree, info, files, None)
        except ImportError as e:
            self.after(0, self._populate_live_tree, None, [], f"Modulo mancante: {e}. Prova: pip install pymobiledevice3")
        except Exception as e:
            self.after(0, self._populate_live_tree, None, [], str(e))

    def _populate_live_tree(self, info, files, error_msg):
        self.btn_load_files.configure(state='normal', text="Carica Lista File")
        if error_msg:
            messagebox.showerror("Errore di Connessione", f"Impossibile leggere il dispositivo:\n{error_msg}")
            return
            
        self.all_files = files
        self.log_message(f"📱 Dispositivo connesso: {info}\n")
        
        for f in files:
            tipo = "Cartella" if f["is_dir"] else "File"
            # Add a tag to highlight directories
            self.file_tree.insert("", "end", values=(f["name"], tipo), tags=("dir" if f["is_dir"] else "file", f["path"]))
            
        self.file_tree.tag_configure("dir")

    def go_up_dir(self):
        source = self.source_var.get()
        if source != "live":
            return
        
        current_path = self.live_path_var.get()
        if current_path == "/":
            return
            
        # Remove last part
        parts = current_path.split("/")
        parts.pop()
        new_path = "/".join(parts)
        if not new_path:
            new_path = "/"
            
        self.live_path_var.set(new_path)
        self.load_live_files()

    def on_tree_double_click(self, event):
        source = self.source_var.get()
        if source != "live":
            return
            
        selected = self.file_tree.selection()
        if not selected:
            return
            
        item = self.file_tree.item(selected[0])
        tipo = item['values'][1]
        
        if tipo == "Cartella":
            # Extract the actual full path stored in the tags
            tags = item['tags']
            if len(tags) > 1:
                path = tags[1]
                self.live_path_var.set(path)
                self.load_live_files()

    def filter_files(self, *args):
        if not hasattr(self, 'all_files') or not self.all_files:
            return
            
        query = self.search_var.get().lower()
        self.file_tree.delete(*self.file_tree.get_children())
        
        source = self.source_var.get()
        count = 0
        for f in self.all_files:
            if source == "backup":
                if query in f["domain"].lower() or query in f["relativePath"].lower():
                    self.file_tree.insert("", "end", values=(f["domain"], f["relativePath"]))
                    count += 1
            else:
                if query in f["name"].lower():
                    tipo = "Cartella" if f["is_dir"] else "File"
                    self.file_tree.insert("", "end", values=(f["name"], tipo), tags=("dir" if f["is_dir"] else "file", f["path"]))
                    count += 1
                    
            if count > 5000:  # Prevent UI freeze
                break

    def extract_selected_file(self):
        selected = self.file_tree.selection()
        if not selected:
            messagebox.showinfo("Nessun file", "Seleziona prima un file dalla lista.")
            return
            
        item = self.file_tree.item(selected[0])
        source = self.source_var.get()
        
        if source == "backup":
            domain, rel_path = item['values']
            passphrase = self.pass_var.get().strip()
            
            default_name = rel_path.split("/")[-1] if "/" in rel_path else rel_path
            out_path = filedialog.asksaveasfilename(title="Salva file estratto come", initialfile=default_name)
            if not out_path:
                return
                
            try:
                from iphone_backup_decrypt import EncryptedBackup
                backup = EncryptedBackup(backup_directory=self.selected_backup_dir, passphrase=passphrase)
                backup.extract_file(relative_path=rel_path, domain_like=domain, output_filename=out_path)
                
                self.log_message(f"✅ Estratto: {rel_path} -> {out_path}\n")
                messagebox.showinfo("Successo", f"File estratto con successo:\n{out_path}")
            except Exception as e:
                messagebox.showerror("Errore Estrazione", f"Errore durante l'estrazione:\n{e}")
        else:
            tipo = item['values'][1]
            if tipo == "Cartella":
                messagebox.showinfo("Cartella", "Puoi estrarre solo file singoli per ora. Fai doppio clic per entrare nella cartella.")
                return
                
            tags = item['tags']
            if len(tags) > 1:
                remote_path = tags[1]
                default_name = item['values'][0]
                
                out_path = filedialog.asksaveasfilename(title="Salva file estratto come", initialfile=default_name)
                if not out_path:
                    return
                
                try:
                    from live_device_explorer import extract_live_file
                    extract_live_file(remote_path, out_path)
                    self.log_message(f"✅ Estratto dal dispositivo live: {remote_path} -> {out_path}\n")
                    messagebox.showinfo("Successo", f"File estratto con successo:\n{out_path}")
                except Exception as e:
                    messagebox.showerror("Errore Estrazione", f"Errore durante l'estrazione live:\n{e}")

    def on_closing(self):
        if hasattr(self, 'db_backend') and self.db_backend:
            self.db_backend.close()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()
