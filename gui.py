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
    from export_calls import find_backups, process_and_export_calls
except ImportError:
    # Append current directory to path if launched from outside
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from export_calls import find_backups, process_and_export_calls


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
        style.configure('Card.TFrame', background=card_color, relief='flat')
        
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
        self.header_frame = tk.Frame(self, bg=self.card_color, bd=0, height=100)
        self.header_frame.pack(fill='x', side='top')
        self.header_frame.pack_propagate(False)
        
        # Material design bottom accent line
        self.accent_line = tk.Frame(self, bg=self.border_color, height=1)
        self.accent_line.pack(fill='x', side='top')

        # Theme toggle button
        self.btn_theme = ttk.Button(self.header_frame, text="🌙 Tema Scuro", style="Secondary.TButton", command=self.toggle_theme)
        self.btn_theme.pack(side='right', padx=32, pady=32)

        title_label = ttk.Label(self.header_frame, text="iOS Backup Explorer", style="Title.TLabel")
        title_label.pack(anchor='w', padx=32, pady=(20, 4))
        
        subtitle_label = ttk.Label(self.header_frame, text="Esplora ed esporta dati dai tuoi backup iOS crittografati.", style="Subtitle.TLabel")
        subtitle_label.pack(anchor='w', padx=32)

        # Main scrollable container
        container = ttk.Frame(self, padding=16)
        container.pack(fill='both', expand=True)

        # Global Credentials Section
        cred_frame = tk.Frame(container, bg=self.card_color, padx=16, pady=16, bd=1, relief="solid")
        cred_frame.configure(highlightthickness=0, highlightbackground=self.border_color, bd=0)
        cred_frame.pack(fill='x', pady=(0, 16))
        
        lbl_font = ('Segoe UI', 10, 'bold')
        self.lbl_backup = tk.Label(cred_frame, text="Backup iOS di origine:", bg=self.card_color, fg=self.text_color, font=lbl_font)
        self.lbl_backup.grid(row=0, column=0, sticky='w', pady=8)
        
        self.backup_var = tk.StringVar()
        self.backup_combobox = ttk.Combobox(cred_frame, textvariable=self.backup_var, state='readonly', width=50)
        self.backup_combobox.grid(row=0, column=1, sticky='we', padx=(16, 16), pady=8, ipady=4)
        self.backup_combobox.bind("<<ComboboxSelected>>", self.on_backup_selected)
        
        btn_browse_backup = ttk.Button(cred_frame, text="Sfoglia...", style="Secondary.TButton", command=self.browse_backup)
        btn_browse_backup.grid(row=0, column=2, pady=8)

        self.lbl_pass = tk.Label(cred_frame, text="Password del backup:", bg=self.card_color, fg=self.text_color, font=lbl_font)
        self.lbl_pass.grid(row=1, column=0, sticky='w', pady=8)
        
        self.pass_var = tk.StringVar()
        self.pass_entry = ttk.Entry(cred_frame, textvariable=self.pass_var, show="*", width=50)
        self.pass_entry.grid(row=1, column=1, sticky='we', padx=(16, 16), pady=8, ipady=4)
        
        self.show_pass_var = tk.BooleanVar(value=False)
        self.show_pass_check = tk.Checkbutton(cred_frame, text="Mostra", variable=self.show_pass_var, command=self.toggle_pass_visibility, bg=self.card_color, fg=self.text_color, font=('Segoe UI', 10), activebackground=self.card_color, activeforeground=self.text_color, selectcolor=self.card_color)
        self.show_pass_check.grid(row=1, column=2, sticky='w', pady=8)
        cred_frame.columnconfigure(1, weight=1)

        # Notebook for Tabs
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill='both', expand=True, pady=(0, 16))

        # Tab 1: Calls
        self.tab_calls = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_calls, text="📞 Chiamate")
        self.create_calls_tab()

        # Tab 2: Explorer
        self.tab_explorer = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_explorer, text="📂 File Explorer")
        self.create_explorer_tab()

        # Tab 3: Wi-Fi
        self.tab_wifi = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_wifi, text="📶 Wi-Fi Passwords")
        self.create_wifi_tab()

        # Log Section
        ttk.Label(container, text="Avanzamento e Report", style="Section.TLabel").pack(anchor='w', pady=(0, 8))
        self.log_text = ScrolledText(container, state='disabled', height=8, font=('Consolas', 10), bg=self.log_bg, fg=self.log_fg, bd=0, relief='flat', highlightthickness=1, highlightbackground=self.border_color, highlightcolor=self.border_color, padx=12, pady=12)
        self.log_text.pack(fill='both', expand=True)

    def create_calls_tab(self):
        container = tk.Frame(self.tab_calls, bg=self.card_color, padx=24, pady=24)
        container.pack(fill='both', expand=True)
        
        lbl_font = ('Segoe UI', 10, 'bold')
        self.lbl_out = tk.Label(container, text="File di destinazione (CSV):", bg=self.card_color, fg=self.text_color, font=lbl_font)
        self.lbl_out.grid(row=0, column=0, sticky='w', pady=12)
        
        self.out_var = tk.StringVar(value=str(Path.home() / "Desktop" / "calls.csv"))
        self.out_entry = ttk.Entry(container, textvariable=self.out_var, width=50)
        self.out_entry.grid(row=0, column=1, sticky='we', padx=(16, 16), pady=12, ipady=4)
        
        btn_browse_out = ttk.Button(container, text="Sfoglia...", style="Secondary.TButton", command=self.browse_output)
        btn_browse_out.grid(row=0, column=2, pady=12)
        container.columnconfigure(1, weight=1)

        self.excel_var = tk.BooleanVar(value=True)
        self.excel_check = tk.Checkbutton(container, text="Ottimizza formato per Microsoft Excel", variable=self.excel_var, bg=self.card_color, fg=self.text_color, activebackground=self.card_color, activeforeground=self.text_color, selectcolor=self.card_color)
        self.excel_check.grid(row=1, column=0, columnspan=3, sticky='w', pady=12)

        self.btn_export = ttk.Button(container, text="AVVIA ESPORTAZIONE CHIAMATE", style="Primary.TButton", command=self.start_export_thread)
        self.btn_export.grid(row=2, column=0, columnspan=3, sticky='we', pady=(24,0))

    def create_explorer_tab(self):
        container = tk.Frame(self.tab_explorer, bg=self.card_color, padx=16, pady=16)
        container.pack(fill='both', expand=True)
        
        # Source selector
        source_frame = tk.Frame(container, bg=self.card_color)
        source_frame.pack(fill='x', pady=(0, 12))
        
        self.source_var = tk.StringVar(value="backup")
        rb_backup = ttk.Radiobutton(source_frame, text="📁 Backup Locale", variable=self.source_var, value="backup", command=self.on_source_changed)
        rb_backup.pack(side='left', padx=(0, 16))
        
        rb_live = ttk.Radiobutton(source_frame, text="📱 Dispositivo Collegato (Live)", variable=self.source_var, value="live", command=self.on_source_changed)
        rb_live.pack(side='left')
        
        self.live_path_var = tk.StringVar(value="/")
        
        # Action Bar
        self.action_frame = tk.Frame(container, bg=self.card_color)
        self.action_frame.pack(fill='x', pady=(0, 12))
        
        self.btn_load_files = ttk.Button(self.action_frame, text="Carica Lista File", style="Primary.TButton", command=self.load_explorer_data)
        self.btn_load_files.pack(side='left')
        
        self.btn_up_dir = ttk.Button(self.action_frame, text="⬆️ Su", command=self.go_up_dir)
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_files)
        self.search_entry = ttk.Entry(self.action_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side='right')
        self.lbl_search = ttk.Label(self.action_frame, text="Cerca:", style="TLabel", background=self.card_color)
        self.lbl_search.pack(side='right', padx=8)

        # Path label for Live mode
        self.lbl_live_path = ttk.Label(container, text="Percorso: /", style="TLabel", background=self.card_color)

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
        
        btn_frame = tk.Frame(container, bg=self.card_color)
        btn_frame.pack(fill='x', side='bottom', pady=(12,0))
        
        self.btn_extract_file = ttk.Button(btn_frame, text="Estrai Elemento Selezionato", style="Secondary.TButton", command=self.extract_selected_file)
        self.btn_extract_file.pack(side='right')
        
        self.on_source_changed()

    def create_wifi_tab(self):
        container = tk.Frame(self.tab_wifi, bg=self.card_color, padx=24, pady=24)
        container.pack(fill='both', expand=True)
        
        ttk.Label(container, text="Estrazione Password Wi-Fi (In arrivo)", style="Section.TLabel", background=self.card_color).pack(pady=(0, 16))
        
        msg = ("Le password del Wi-Fi sono conservate nel Keychain cifrato del dispositivo.\n"
               "L'estrazione del Keychain richiederà una gestione avanzata della decrittografia.\n\n"
               "Questa funzionalità sarà implementata nella prossima versione.")
        tk.Label(container, text=msg, bg=self.card_color, fg=self.text_color, justify='left').pack(anchor='w')


    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.setup_styles()
        
        # Update specific standard tk widgets
        self.configure(bg=self.bg_color)
        self.header_frame.configure(bg=self.card_color)
        self.accent_line.configure(bg=self.border_color)
        self.form_card.configure(bg=self.card_color, highlightbackground=self.border_color)
        self.inner_form.configure(bg=self.card_color)
        
        self.lbl_backup.configure(bg=self.card_color, fg=self.text_color)
        self.lbl_pass.configure(bg=self.card_color, fg=self.text_color)
        self.show_pass_check.configure(bg=self.card_color, fg=self.text_color, activebackground=self.card_color, activeforeground=self.text_color, selectcolor=self.card_color)
        self.lbl_out.configure(bg=self.card_color, fg=self.text_color)
        
        self.log_text.configure(bg=self.log_bg, fg=self.log_fg, insertbackground=self.log_fg, highlightbackground=self.border_color, highlightcolor=self.border_color)

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

    def browse_output(self):
        file_path = filedialog.asksaveasfilename(
            title="Salva file CSV come",
            defaultextension=".csv",
            filetypes=[("File CSV (*.csv)", "*.csv"), ("Tutti i file (*.*)", "*.*")],
            initialfile="calls.csv"
        )
        if file_path:
            self.out_var.set(file_path)

    def log_message(self, message):
        self.log_text.configure(state='normal')
        self.log_text.insert('end', message)
        self.log_text.see('end')
        self.log_text.configure(state='disabled')

    def start_export_thread(self):
        # Validation checks
        if not self.selected_backup_dir:
            messagebox.showerror("Dati Mancanti", "Seleziona o sfoglia una cartella di backup valida prima di procedere.")
            return

        passphrase = self.pass_var.get().strip()
        if not passphrase:
            if not messagebox.askyesno("Password vuota", "Hai inserito una password vuota. Se il backup è crittografato, l'esportazione fallirà.\nVuoi continuare lo stesso?"):
                return

        output_path = self.out_var.get().strip()
        if not output_path:
            messagebox.showerror("Dati Mancanti", "Specifica un percorso valido per il file di destinazione (CSV).")
            return

        # Disable controls during export
        self.btn_export.configure(state='disabled', text="ESPORTAZIONE IN CORSO...")
        self.pass_entry.configure(state='disabled')
        self.out_entry.configure(state='disabled')
        self.backup_combobox.configure(state='disabled')
        
        # Clear log area
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.configure(state='disabled')

        # Start background thread
        thread = threading.Thread(
            target=self.run_export_process,
            args=(self.selected_backup_dir, passphrase, output_path, self.excel_var.get()),
            daemon=True
        )
        thread.start()

    def run_export_process(self, backup_dir, passphrase, output_path, excel_compat):
        # Redirect stdout and stderr to the GUI log panel
        redirector = TextRedirector(self.log_text)
        sys.stdout = redirector
        sys.stderr = redirector

        success = False
        error_msg = ""
        
        try:
            total_calls, resolved_path = process_and_export_calls(
                backup_dir=backup_dir,
                passphrase=passphrase,
                output_path=output_path,
                excel_compat=excel_compat
            )
            success = True
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ ERRORE DI ESPORTAZIONE: {error_msg}")
        finally:
            # Restore stdout and stderr
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr
            
            # Update GUI elements back on the main thread
            self.after(0, self.export_finished, success, error_msg)

    def export_finished(self, success, error_msg):
        # Re-enable controls
        self.btn_export.configure(state='normal', text="AVVIA ESPORTAZIONE")
        self.pass_entry.configure(state='normal')
        self.out_entry.configure(state='normal')
        self.backup_combobox.configure(state='readonly')

        if success:
            messagebox.showinfo("Esportazione Completata", "🎉 La cronologia delle chiamate è stata esportata con successo!")
        else:
            if "Incorrect passphrase" in error_msg or "password" in error_msg.lower():
                messagebox.showerror("Errore Decrittografia", "Password non corretta. Verifica la chiave di crittografia inserita.")
            else:
                messagebox.showerror("Errore Esportazione", f"Si è verificato un errore durante l'esportazione:\n{error_msg}")

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
            
        self.file_tree.tag_configure("dir", font=('Segoe UI', 10, 'bold'))

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

if __name__ == "__main__":
    app = App()
    app.mainloop()
