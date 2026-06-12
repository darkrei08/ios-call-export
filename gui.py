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
        self.geometry("700x680")
        self.configure(bg="#f8f9fa")
        
        # Center the window on the screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Set up modern TTK styling (Google Material palette style)
        self.setup_styles()

        # State variables
        self.is_dark_mode = False
        self.backups = []
        self.selected_backup_dir = ""
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        # Create GUI layout
        self.create_widgets()
        
        # Auto-detect backups
        self.detect_backups()

    def setup_styles(self):
        style = ttk.Style()
        # Fall back to clam theme for custom styling control across platforms
        style.theme_use('clam')
        
        # Colors definition
        if getattr(self, 'is_dark_mode', False):
            self.bg_color = "#202124"
            self.card_color = "#292a2d"
            self.primary_color = "#8ab4f8"  # Lighter Google Blue for dark mode
            self.primary_active = "#aecbfa"
            self.text_color = "#e8eaed"
            self.border_color = "#5f6368"
            self.log_bg = "#3c4043"
        else:
            self.bg_color = "#f8f9fa"
            self.card_color = "#ffffff"
            self.primary_color = "#1a73e8"  # Google Blue
            self.primary_active = "#1557b0"
            self.text_color = "#202124"
            self.border_color = "#dadce0"
            self.log_bg = "#f1f3f4"
            
        bg_color = self.bg_color
        card_color = self.card_color
        primary_color = self.primary_color
        primary_active = self.primary_active
        text_color = self.text_color
        border_color = self.border_color

        self.configure(bg=bg_color)

        style.configure('TFrame', background=bg_color)
        style.configure('Card.TFrame', background=card_color, relief='solid', borderwidth=1)
        
        style.configure('TLabel', background=bg_color, foreground=text_color, font=('Segoe UI', 10))
        style.configure('Title.TLabel', background=card_color, foreground=primary_color, font=('Segoe UI', 16, 'bold'))
        style.configure('Subtitle.TLabel', background=card_color, foreground="#5f6368" if not self.is_dark_mode else "#9aa0a6", font=('Segoe UI', 9))
        style.configure('Section.TLabel', background=bg_color, foreground=text_color, font=('Segoe UI', 11, 'bold'))
        
        style.configure('TCheckbutton', background=bg_color, foreground=text_color, font=('Segoe UI', 10))
        
        # Entries
        style.configure('TEntry', fieldbackground=card_color, bordercolor=border_color, lightcolor=border_color, darkcolor=border_color, insertcolor=text_color, foreground=text_color)
        
        # Combobox
        style.configure('TCombobox', fieldbackground=card_color, background=card_color, arrowcolor=text_color, bordercolor=border_color, foreground=text_color)
        style.map('TCombobox', fieldbackground=[('readonly', card_color)])
        
        # Primary Button (Solid Blue)
        style.configure('Primary.TButton', background=primary_color, foreground='#ffffff' if not self.is_dark_mode else '#202124', font=('Segoe UI', 10, 'bold'), borderwidth=0, focuscolor=primary_color)
        style.map('Primary.TButton',
                  background=[('active', primary_active), ('disabled', border_color)],
                  foreground=[('disabled', '#9aa0a6')])

        # Secondary Button (Bordered White/Dark)
        style.configure('Secondary.TButton', background=card_color, foreground=primary_color, font=('Segoe UI', 9), borderwidth=1, bordercolor=border_color, focuscolor=card_color)
        style.map('Secondary.TButton',
                  background=[('active', '#f1f3f4' if not self.is_dark_mode else '#3c4043')])

    def create_widgets(self):
        # 1. Header (Banner)
        self.header_frame = tk.Frame(self, bg=self.card_color, bd=0, height=80)
        self.header_frame.pack(fill='x', side='top')
        self.header_frame.pack_propagate(False)
        
        # Material design bottom accent line
        self.accent_line = tk.Frame(self, bg=self.primary_color, height=3)
        self.accent_line.pack(fill='x', side='top')

        # Theme toggle button
        self.btn_theme = ttk.Button(self.header_frame, text="🌙 Tema Scuro", style="Secondary.TButton", command=self.toggle_theme)
        self.btn_theme.pack(side='right', padx=24, pady=24)

        title_label = ttk.Label(self.header_frame, text="iOS Call Exporter", style="Title.TLabel")
        title_label.pack(anchor='w', padx=24, pady=(12, 2))
        
        subtitle_label = ttk.Label(self.header_frame, text="Esporta la cronologia delle chiamate dell'iPhone da backup crittografati in file CSV legibili per Excel.", style="Subtitle.TLabel")
        subtitle_label.pack(anchor='w', padx=24)

        # Main scrollable container
        container = ttk.Frame(self, padding=20)
        container.pack(fill='both', expand=True)

        # Form Section
        ttk.Label(container, text="Configurazione dell'Esportazione", style="Section.TLabel").pack(anchor='w', pady=(0, 10))
        
        # Form Card
        self.form_card = tk.Frame(container, bg=self.card_color, bd=1, relief="solid", highlightthickness=0)
        self.form_card.configure(highlightbackground=self.border_color, bd=0) # custom flat card border
        self.form_card.pack(fill='x', pady=(0, 20))
        
        # Make the card look flat and material
        self.inner_form = tk.Frame(self.form_card, bg=self.card_color, padx=16, pady=16)
        self.inner_form.pack(fill='both', expand=True)

        # Row 1: Backup Directory
        self.lbl_backup = tk.Label(self.inner_form, text="Backup iOS di origine:", bg=self.card_color, fg=self.text_color, font=('Segoe UI', 9, 'bold'))
        self.lbl_backup.grid(row=0, column=0, sticky='w', pady=8)
        
        self.backup_var = tk.StringVar()
        self.backup_combobox = ttk.Combobox(self.inner_form, textvariable=self.backup_var, state='readonly', width=50)
        self.backup_combobox.grid(row=0, column=1, sticky='we', padx=(10, 10), pady=8)
        self.backup_combobox.bind("<<ComboboxSelected>>", self.on_backup_selected)
        
        btn_browse_backup = ttk.Button(self.inner_form, text="Sfoglia...", style="Secondary.TButton", command=self.browse_backup)
        btn_browse_backup.grid(row=0, column=2, pady=8)

        # Row 2: Passphrase
        self.lbl_pass = tk.Label(self.inner_form, text="Password del backup:", bg=self.card_color, fg=self.text_color, font=('Segoe UI', 9, 'bold'))
        self.lbl_pass.grid(row=1, column=0, sticky='w', pady=8)
        
        self.pass_var = tk.StringVar()
        self.pass_entry = ttk.Entry(self.inner_form, textvariable=self.pass_var, show="*", width=50)
        self.pass_entry.grid(row=1, column=1, sticky='we', padx=(10, 10), pady=8)
        
        self.show_pass_var = tk.BooleanVar(value=False)
        self.show_pass_check = tk.Checkbutton(self.inner_form, text="Mostra", variable=self.show_pass_var, command=self.toggle_pass_visibility, bg=self.card_color, fg=self.text_color, font=('Segoe UI', 9), activebackground=self.card_color, activeforeground=self.text_color, selectcolor=self.card_color)
        self.show_pass_check.grid(row=1, column=2, sticky='w', pady=8)

        # Row 3: Output Path
        self.lbl_out = tk.Label(self.inner_form, text="File di destinazione (CSV):", bg=self.card_color, fg=self.text_color, font=('Segoe UI', 9, 'bold'))
        self.lbl_out.grid(row=2, column=0, sticky='w', pady=8)
        
        self.out_var = tk.StringVar(value=str(Path.home() / "Desktop" / "calls.csv"))
        self.out_entry = ttk.Entry(self.inner_form, textvariable=self.out_var, width=50)
        self.out_entry.grid(row=2, column=1, sticky='we', padx=(10, 10), pady=8)
        
        btn_browse_out = ttk.Button(self.inner_form, text="Sfoglia...", style="Secondary.TButton", command=self.browse_output)
        btn_browse_out.grid(row=2, column=2, pady=8)
        
        inner_form.columnconfigure(1, weight=1)

        # Row 4: Options
        options_frame = ttk.Frame(container)
        options_frame.pack(fill='x', pady=(0, 20))
        
        self.excel_var = tk.BooleanVar(value=True)
        self.excel_check = ttk.Checkbutton(options_frame, text="Ottimizza formato per Microsoft Excel (risolve accenti, colonne e notazione scientifica)", variable=self.excel_var)
        self.excel_check.pack(anchor='w')

        # Row 5: Action Button
        self.btn_export = ttk.Button(container, text="AVVIA ESPORTAZIONE", style="Primary.TButton", command=self.start_export_thread)
        self.btn_export.pack(fill='x', ipady=8, pady=(0, 20))

        # Log Section
        ttk.Label(container, text="Avanzamento e Report", style="Section.TLabel").pack(anchor='w', pady=(0, 10))
        
        # Scrolled Text for logging
        self.log_text = ScrolledText(container, state='disabled', height=14, font=('Consolas', 9), bg=self.log_bg, fg=self.text_color, bd=1, relief='solid', highlightthickness=0)
        self.log_text.pack(fill='both', expand=True)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.setup_styles()
        
        # Update specific standard tk widgets
        self.configure(bg=self.bg_color)
        self.header_frame.configure(bg=self.card_color)
        self.accent_line.configure(bg=self.primary_color)
        self.form_card.configure(bg=self.card_color, highlightbackground=self.border_color)
        self.inner_form.configure(bg=self.card_color)
        
        self.lbl_backup.configure(bg=self.card_color, fg=self.text_color)
        self.lbl_pass.configure(bg=self.card_color, fg=self.text_color)
        self.show_pass_check.configure(bg=self.card_color, fg=self.text_color, activebackground=self.card_color, activeforeground=self.text_color, selectcolor=self.card_color)
        self.lbl_out.configure(bg=self.card_color, fg=self.text_color)
        
        self.log_text.configure(bg=self.log_bg, fg=self.text_color, insertbackground=self.text_color)

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
                self.log_message(f"Rilevati automaticamente {len(self.backups)} backup sul sistema.\nSelezionato il più recente.\n")
            else:
                self.backup_combobox.configure(values=["Nessun backup trovato automaticamente - Clicca Sfoglia..."])
                self.backup_combobox.current(0)
                self.selected_backup_dir = ""
                self.log_message("AVVISO: Nessun backup iOS rilevato nelle cartelle di default.\nSeleziona manualmente la cartella del backup cliccando su 'Sfoglia...'.\n")
        except Exception as e:
            self.log_message(f"Errore durante la scansione automatica dei backup: {e}\n")

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
            self.log_message(f"Selezionato manualmente backup in: {dir_path}\n")

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
        self.btn_export.configure(state='disabled')
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
            print(f"\nERRORE DI ESPORTAZIONE: {error_msg}")
        finally:
            # Restore stdout and stderr
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr
            
            # Update GUI elements back on the main thread
            self.after(0, self.export_finished, success, error_msg)

    def export_finished(self, success, error_msg):
        # Re-enable controls
        self.btn_export.configure(state='normal')
        self.pass_entry.configure(state='normal')
        self.out_entry.configure(state='normal')
        self.backup_combobox.configure(state='readonly')

        if success:
            messagebox.showinfo("Esportazione Completata", "La cronologia delle chiamate è stata esportata con successo!")
        else:
            if "Incorrect passphrase" in error_msg or "password" in error_msg.lower():
                messagebox.showerror("Errore Decrittografia", "Password non corretta. Verifica la chiave di crittografia inserita.")
            else:
                messagebox.showerror("Errore Esportazione", f"Si è verificato un errore durante l'esportazione:\n{error_msg}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
