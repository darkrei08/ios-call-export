import os
import re

current_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(current_dir, 'gui.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

translations_dict = """
import json

TRANSLATIONS = {
    "it": {
        "🌙 Tema Scuro": "🌙 Tema Scuro",
        "☀️ Tema Chiaro": "☀️ Tema Chiaro",
        "🇬🇧 English": "🇬🇧 English",
        "🇮🇹 Italiano": "🇮🇹 Italiano",
        "iOS Backup Explorer": "iOS Backup Explorer",
        "Esplora ed esporta dati dai tuoi backup iOS crittografati.": "Esplora ed esporta dati dai tuoi backup iOS crittografati.",
        "Backup iOS di origine:": "Backup iOS di origine:",
        "Sfoglia...": "Sfoglia...",
        "Password del backup:": "Password del backup:",
        "Mostra": "Mostra",
        "Nascondi": "Nascondi",
        "📥 Esportazioni": "📥 Esportazioni",
        "📞 Vista Chiamate": "📞 Vista Chiamate",
        "💬 Vista Messaggi": "💬 Vista Messaggi",
        "📂 File Explorer": "📂 File Explorer",
        "📶 Wi-Fi Passwords": "📶 Wi-Fi Passwords",
        "Seleziona i dati da esportare dal tuo backup crittografato.": "Seleziona i dati da esportare dal tuo backup crittografato.",
        "📞 Cronologia Chiamate (CSV)": "📞 Cronologia Chiamate (CSV)",
        "📞 Cronologia Chiamate (HTML Viewer Interattivo)": "📞 Cronologia Chiamate (HTML Viewer Interattivo)",
        "💬 Messaggi SMS e iMessage (HTML Viewer Interattivo)": "💬 Messaggi SMS e iMessage (HTML Viewer Interattivo)",
        "Impostazioni Chiamate": "Impostazioni Chiamate",
        "Ottimizza CSV per Microsoft Excel (usa punto e virgola come separatore)": "Ottimizza CSV per Microsoft Excel (usa punto e virgola come separatore)",
        "AVVIA ESPORTAZIONE": "AVVIA ESPORTAZIONE",
        "Log Operazioni:": "Log Operazioni:",
        "📋 Copia Log (Debug)": "📋 Copia Log (Debug)",
        "Carica/Aggiorna Dati dal Backup": "Carica/Aggiorna Dati dal Backup",
        "Cerca:": "Cerca:",
        "Cerca (Testo o Numero):": "Cerca (Testo o Numero):",
        "Data": "Data",
        "Contatto": "Contatto",
        "Direzione": "Direzione",
        "Servizio": "Servizio",
        "Testo del Messaggio": "Testo del Messaggio",
        "📁 Backup Locale": "📁 Backup Locale",
        "📱 Dispositivo Collegato (Live)": "📱 Dispositivo Collegato (Live)",
        "Carica Lista File": "Carica Lista File",
        "⬆️ Su": "⬆️ Su",
        "Percorso: /": "Percorso: /",
        "Dominio / Nome": "Dominio / Nome",
        "Percorso File / Tipo": "Percorso File / Tipo",
        "Estrai Elemento Selezionato": "Estrai Elemento Selezionato",
        "Estrazione Password Wi-Fi (In arrivo)": "Estrazione Password Wi-Fi (In arrivo)",
        "Dominio (App)": "Dominio (App)",
        "Percorso File": "Percorso File",
        "Nome": "Nome",
        "Tipo": "Tipo",
        "Caricamento in corso...": "Caricamento in corso...",
        "Connessione in corso...": "Connessione in corso...",
        "Nessun file selezionato.": "Nessun file selezionato."
    },
    "en": {
        "🌙 Tema Scuro": "🌙 Dark Theme",
        "☀️ Tema Chiaro": "☀️ Light Theme",
        "🇬🇧 English": "🇮🇹 Italiano",
        "🇮🇹 Italiano": "🇬🇧 English",
        "iOS Backup Explorer": "iOS Backup Explorer",
        "Esplora ed esporta dati dai tuoi backup iOS crittografati.": "Explore and export data from encrypted iOS backups.",
        "Backup iOS di origine:": "Source iOS Backup:",
        "Sfoglia...": "Browse...",
        "Password del backup:": "Backup Password:",
        "Mostra": "Show",
        "Nascondi": "Hide",
        "📥 Esportazioni": "📥 Exports",
        "📞 Vista Chiamate": "📞 Calls View",
        "💬 Vista Messaggi": "💬 Messages View",
        "📂 File Explorer": "📂 File Explorer",
        "📶 Wi-Fi Passwords": "📶 Wi-Fi Passwords",
        "Seleziona i dati da esportare dal tuo backup crittografato.": "Select data to export from your encrypted backup.",
        "📞 Cronologia Chiamate (CSV)": "📞 Call History (CSV)",
        "📞 Cronologia Chiamate (HTML Viewer Interattivo)": "📞 Call History (Interactive HTML Viewer)",
        "💬 Messaggi SMS e iMessage (HTML Viewer Interattivo)": "💬 SMS & iMessage (Interactive HTML Viewer)",
        "Impostazioni Chiamate": "Call Settings",
        "Ottimizza CSV per Microsoft Excel (usa punto e virgola come separatore)": "Optimize CSV for Microsoft Excel (use semicolon as separator)",
        "AVVIA ESPORTAZIONE": "START EXPORT",
        "Log Operazioni:": "Operation Logs:",
        "📋 Copia Log (Debug)": "📋 Copy Logs (Debug)",
        "Carica/Aggiorna Dati dal Backup": "Load/Update Backup Data",
        "Cerca:": "Search:",
        "Cerca (Testo o Numero):": "Search (Text or Number):",
        "Data": "Date",
        "Contatto": "Contact",
        "Direzione": "Direction",
        "Servizio": "Service",
        "Testo del Messaggio": "Message Text",
        "📁 Backup Locale": "📁 Local Backup",
        "📱 Dispositivo Collegato (Live)": "📱 Connected Device (Live)",
        "Carica Lista File": "Load File List",
        "⬆️ Su": "⬆️ Up",
        "Percorso: /": "Path: /",
        "Dominio / Nome": "Domain / Name",
        "Percorso File / Tipo": "File Path / Type",
        "Estrai Elemento Selezionato": "Extract Selected Item",
        "Estrazione Password Wi-Fi (In arrivo)": "Wi-Fi Password Extraction (Coming soon)",
        "Dominio (App)": "Domain (App)",
        "Percorso File": "File Path",
        "Nome": "Name",
        "Tipo": "Type",
        "Caricamento in corso...": "Loading...",
        "Connessione in corso...": "Connecting...",
        "Nessun file selezionato.": "No file selected."
    }
}
CURRENT_LANG = "it"

def t(text):
    return TRANSLATIONS[CURRENT_LANG].get(text, text)
"""

if "def t(text):" not in content:
    content = content.replace("import os", "import os\n" + translations_dict)

lang_btn_code = """
        # Language toggle button
        self.btn_lang = ttk.Button(
            self.header_frame,
            text=t("🇬🇧 English"),
            style="Secondary.TButton",
            command=self.switch_language,
        )
        self.btn_lang.pack(side="right", padx=(0, 16), pady=32)

        self.btn_theme = ttk.Button(
"""
if "self.btn_lang =" not in content:
    content = content.replace("        self.btn_theme = ttk.Button(", lang_btn_code)

switch_lang_method = """
    def switch_language(self):
        global CURRENT_LANG
        CURRENT_LANG = "en" if CURRENT_LANG == "it" else "it"
        from tkinter import messagebox
        msg = "Riavvia l'applicazione per applicare la nuova lingua." if CURRENT_LANG == "en" else "Restart the application to apply the new language."
        messagebox.showinfo("Language Changed", msg)
        self.btn_lang.configure(text=t("🇬🇧 English"))
        self.btn_theme.configure(text=t("☀️ Tema Chiaro" if self.is_dark_mode else "🌙 Tema Scuro"))
"""

if "def switch_language" not in content:
    content = content.replace("    def switch_theme(self):", switch_lang_method + "\n    def switch_theme(self):")


keys_to_replace = [
    "🌙 Tema Scuro", "☀️ Tema Chiaro", "iOS Backup Explorer", "Esplora ed esporta dati dai tuoi backup iOS crittografati.",
    "Backup iOS di origine:", "Sfoglia...", "Password del backup:", "Mostra", "Nascondi", "📥 Esportazioni",
    "📞 Vista Chiamate", "💬 Vista Messaggi", "📂 File Explorer", "📶 Wi-Fi Passwords",
    "Seleziona i dati da esportare dal tuo backup crittografato.", "📞 Cronologia Chiamate (CSV)",
    "📞 Cronologia Chiamate (HTML Viewer Interattivo)", "💬 Messaggi SMS e iMessage (HTML Viewer Interattivo)",
    "Impostazioni Chiamate", "Ottimizza CSV per Microsoft Excel (usa punto e virgola come separatore)",
    "AVVIA ESPORTAZIONE", "Log Operazioni:", "📋 Copia Log (Debug)", "Carica/Aggiorna Dati dal Backup", "Cerca:",
    "Cerca (Testo o Numero):", "Data", "Contatto", "Direzione", "Servizio", "Testo del Messaggio", "📁 Backup Locale",
    "📱 Dispositivo Collegato (Live)", "Carica Lista File", "⬆️ Su", "Percorso: /", "Dominio / Nome", "Percorso File / Tipo",
    "Estrai Elemento Selezionato", "Estrazione Password Wi-Fi (In arrivo)", "Dominio (App)", "Percorso File", "Nome", "Tipo",
    "Caricamento in corso...", "Connessione in corso...", "Nessun file selezionato."
]

for key in keys_to_replace:
    if key in ["Mostra", "Nascondi"]:
        continue
    pattern = r'text\s*=\s*"{}"'.format(re.escape(key))
    replacement = f'text=t("{key}")'
    content = re.sub(pattern, replacement, content)
    
    pattern2 = r"text\s*=\s*'{}'".format(re.escape(key))
    replacement2 = f"text=t('{key}')"
    content = re.sub(pattern2, replacement2, content)

content = content.replace('text="☀️ Tema Chiaro" if self.is_dark_mode else "🌙 Tema Scuro"', 'text=t("☀️ Tema Chiaro") if self.is_dark_mode else t("🌙 Tema Scuro")')
content = content.replace('self.btn_show_hide.configure(text="Nascondi")', 'self.btn_show_hide.configure(text=t("Nascondi"))')
content = content.replace('self.btn_show_hide.configure(text="Mostra")', 'self.btn_show_hide.configure(text=t("Mostra"))')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated gui.py")
