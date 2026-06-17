import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(current_dir, 'assets', 'calls_template.html')
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

start_idx = html.find('<script>')
end_idx = html.find('</script>') + 9

new_script = r'''<script>
        // Placeholder for python injection. DO NOT REMOVE the comment above.
        const CALLS_DATA = {{ CALLS_DATA_JSON }};

        const translations = {
            en: {
                filters: "Filters",
                refine: "Refine call logs",
                search: "Search contacts, numbers...",
                totalCalls: "Total Calls",
                totalDuration: "Total Duration",
                topContacts: "Top Contacts",
                recentActivity: "Recent Activity",
                openCsv: "Download CSV",
                thContact: "Contact",
                thNumber: "Number",
                thDuration: "Duration",
                thDir: "Dir",
                thDate: "Date",
                thService: "Service",
                callsText: "calls",
                unknown: "Unknown",
                dirIncoming: "Incoming",
                dirOutgoing: "Outgoing",
                dirMissed: "Missed",
            },
            it: {
                filters: "Filtri",
                refine: "Filtra cronologia chiamate",
                search: "Cerca contatti, numeri...",
                totalCalls: "Chiamate Totali",
                totalDuration: "Durata Totale",
                topContacts: "Contatti Frequenti",
                recentActivity: "Attività Recente",
                openCsv: "Apri CSV",
                thContact: "Contatto",
                thNumber: "Numero",
                thDuration: "Durata",
                thDir: "Direz",
                thDate: "Data",
                thService: "Servizio",
                callsText: "chiamate",
                unknown: "Sconosciuto",
                dirIncoming: "In Entrata",
                dirOutgoing: "In Uscita",
                dirMissed: "Perse",
            }
        };
        
        let currentLang = "it";

        document.addEventListener("DOMContentLoaded", () => {
            let currentFilterService = null;
            let currentFilterDirection = null;
            let currentSearchQuery = "";
            let currentSortColumn = "date";
            let currentSortAsc = false;

            const tbody = document.querySelector("tbody");
            const totalCallsEl = document.querySelectorAll(".font-display-lg")[0];
            const totalDurationEl = document.querySelectorAll(".font-display-lg")[1];
            const topContactsContainer = document.querySelector(".glass-panel .flex-col.gap-xs");
            const dynamicFiltersContainer = document.getElementById("dynamic-filters-container");
            const searchInput = document.getElementById("search-input");

            // Language toggle
            const btnIt = document.getElementById("lang-it");
            const btnEn = document.getElementById("lang-en");
            
            function updateLangUI() {
                const t = translations[currentLang];
                document.getElementById("lbl-filters").innerText = t.filters;
                document.getElementById("lbl-refine").innerText = t.refine;
                if (searchInput) searchInput.placeholder = t.search;
                document.getElementById("lbl-total-calls").innerText = t.totalCalls;
                document.getElementById("lbl-total-duration").innerText = t.totalDuration;
                document.getElementById("lbl-top-contacts").innerText = t.topContacts;
                document.getElementById("lbl-recent-activity").innerText = t.recentActivity;
                document.getElementById("lbl-open-csv").innerText = t.openCsv;
                
                document.querySelector('[data-th="contact"]').innerText = t.thContact;
                document.querySelector('[data-th="number"]').innerText = t.thNumber;
                document.querySelector('[data-th="duration"]').innerText = t.thDuration;
                document.querySelector('[data-th="dir"]').innerText = t.thDir;
                document.querySelector('[data-th="date"]').innerText = t.thDate;
                document.querySelector('[data-th="service"]').innerText = t.thService;

                if (currentLang === "it") {
                    btnIt.className = "px-3 py-1 rounded-md text-sm font-bold bg-primary-container text-on-primary-container transition-all";
                    btnEn.className = "px-3 py-1 rounded-md text-sm font-medium text-on-surface-variant hover:text-on-surface transition-all";
                } else {
                    btnEn.className = "px-3 py-1 rounded-md text-sm font-bold bg-primary-container text-on-primary-container transition-all";
                    btnIt.className = "px-3 py-1 rounded-md text-sm font-medium text-on-surface-variant hover:text-on-surface transition-all";
                }
                renderAll();
            }

            btnIt.addEventListener("click", () => { currentLang = "it"; updateLangUI(); });
            btnEn.addEventListener("click", () => { currentLang = "en"; updateLangUI(); });

            if (searchInput) {
                searchInput.addEventListener("input", (e) => {
                    currentSearchQuery = e.target.value.toLowerCase();
                    renderAll();
                });
            }

            document.querySelectorAll("th[data-sort]").forEach(th => {
                th.addEventListener("click", () => {
                    const col = th.getAttribute("data-sort");
                    if (currentSortColumn === col) {
                        currentSortAsc = !currentSortAsc;
                    } else {
                        currentSortColumn = col;
                        currentSortAsc = col === "date" ? false : true;
                    }
                    renderAll();
                });
            });

            // CSV Download
            document.getElementById("btn-export-csv").addEventListener("click", () => {
                if (!CALLS_DATA || !CALLS_DATA.length) return;
                const headers = Object.keys(CALLS_DATA[0]);
                const csvRows = [headers.join(",")];
                CALLS_DATA.forEach(row => {
                    const values = headers.map(header => {
                        const val = row[header] === null || row[header] === undefined ? "" : row[header];
                        return `"${String(val).replace(/"/g, '""')}"`;
                    });
                    csvRows.push(values.join(","));
                });
                const csvData = csvRows.join("\n");
                const blob = new Blob([csvData], { type: "text/csv;charset=utf-8;" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "calls_export.csv";
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            });

            let uniqueServices = new Set();
            let uniqueDirections = new Set();
            
            if (Array.isArray(CALLS_DATA)) {
                CALLS_DATA.forEach(c => {
                    if (c.call_type) uniqueServices.add(c.call_type);
                    if (c.direction) uniqueDirections.add(c.direction);
                });
            }
            uniqueServices = Array.from(uniqueServices).sort();
            uniqueDirections = Array.from(uniqueDirections).sort();

            const serviceIcons = {
                "Phone": "phone",
                "Whatsapp": "chat",
                "FaceTime Video": "video_chat",
                "FaceTime Audio": "call",
                "Telegram": "send",
                "Skype": "video_call",
            };
            const serviceColors = {
                "Phone": "text-blue-400 bg-blue-400/10 border-blue-400/20",
                "Whatsapp": "text-green-500 bg-green-500/10 border-green-500/20",
                "FaceTime Video": "text-blue-500 bg-blue-500/10 border-blue-500/20",
                "FaceTime Audio": "text-blue-500 bg-blue-500/10 border-blue-500/20",
                "Telegram": "text-cyan-400 bg-cyan-400/10 border-cyan-400/20",
            };
            const dirIcons = {
                "Incoming": "call_received",
                "Outgoing": "call_made",
                "Missed": "call_missed"
            };
            const dirColors = {
                "Incoming": "text-green-400",
                "Outgoing": "text-blue-400",
                "Missed": "text-red-400"
            };

            function translateDir(d) {
                if (currentLang === "en") return d;
                if (d === "Incoming") return "In Entrata";
                if (d === "Outgoing") return "In Uscita";
                if (d === "Missed") return "Perse";
                return d;
            }

            function translateService(s) {
                if (currentLang === "en") return s;
                if (s === "Phone") return "Telefono";
                return s;
            }

            function buildFilterButton(label, icon, type, origVal) {
                return `
                <button data-type="${type}" data-val="${origVal}" class="filter-btn flex items-center gap-md px-md py-sm rounded-lg text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface active:translate-x-1 duration-150 w-full text-left">
                    <span class="material-symbols-outlined text-lg" style="font-variation-settings: 'FILL' 0;">${icon}</span>
                    <span class="font-label-md text-label-md flex-1 filter-label">${label}</span>
                </button>`;
            }

            function renderFilters() {
                if (!dynamicFiltersContainer) return;
                let html = '';
                uniqueServices.forEach(s => {
                    html += buildFilterButton(translateService(s), serviceIcons[s] || "apps", "service", s);
                });
                html += '<div class="h-px bg-outline-variant/10 my-xs"></div>';
                uniqueDirections.forEach(d => {
                    html += buildFilterButton(translateDir(d), dirIcons[d] || "call", "direction", d);
                });
                dynamicFiltersContainer.innerHTML = html;
                
                // Reattach listeners
                document.querySelectorAll(".filter-btn").forEach(btn => {
                    btn.addEventListener("click", () => {
                        const type = btn.getAttribute("data-type");
                        const val = btn.getAttribute("data-val");
                        
                        if (type === "service") {
                            currentFilterService = currentFilterService === val ? null : val;
                        } else if (type === "direction") {
                            currentFilterDirection = currentFilterDirection === val ? null : val;
                        }
                        
                        document.querySelectorAll(`.filter-btn[data-type="${type}"]`).forEach(b => {
                            b.classList.remove("bg-primary-container", "text-on-primary-container", "font-semibold");
                            b.classList.add("text-on-surface-variant");
                        });
                        
                        if ((type === "service" && currentFilterService) || (type === "direction" && currentFilterDirection)) {
                            btn.classList.add("bg-primary-container", "text-on-primary-container", "font-semibold");
                            btn.classList.remove("text-on-surface-variant");
                        }
                        renderAll();
                    });
                    
                    // Set active states based on current selection
                    const t = btn.getAttribute("data-type");
                    const v = btn.getAttribute("data-val");
                    if ((t === "service" && currentFilterService === v) || (t === "direction" && currentFilterDirection === v)) {
                        btn.classList.add("bg-primary-container", "text-on-primary-container", "font-semibold");
                        btn.classList.remove("text-on-surface-variant");
                    }
                });
            }

            function formatDuration(seconds) {
                if (!seconds) return "00h 00m 00s";
                const h = Math.floor(seconds / 3600);
                const m = Math.floor((seconds % 3600) / 60);
                const s = Math.floor(seconds % 60);
                return `${h.toString().padStart(2,'0')}h ${m.toString().padStart(2,'0')}m ${s.toString().padStart(2,'0')}s`;
            }

            function formatDirIcon(direction) {
                return dirIcons[direction] || "call";
            }

            function getDirColor(direction) {
                return dirColors[direction] || "text-on-surface";
            }
            
            function getServiceColor(service) {
                return serviceColors[service] || "text-on-surface-variant bg-surface-container border-outline-variant/20";
            }

            function renderAll() {
                renderFilters();
                let filtered = CALLS_DATA;
                const t = translations[currentLang];
                
                if (!Array.isArray(filtered)) {
                    filtered = []; 
                } else {
                    filtered = filtered.filter(c => {
                        let matchSearch = true;
                        if (currentSearchQuery) {
                            const name = (c.contact_name || "").toLowerCase();
                            const num = (c.phone_number || "").toLowerCase();
                            matchSearch = name.includes(currentSearchQuery) || num.includes(currentSearchQuery);
                        }

                        let matchService = true;
                        if (currentFilterService) {
                            matchService = (c.call_type || c.service) === currentFilterService;
                        }

                        let matchDir = true;
                        if (currentFilterDirection) {
                            matchDir = c.direction === currentFilterDirection;
                        }

                        return matchSearch && matchService && matchDir;
                    });
                    
                    filtered.sort((a, b) => {
                        let valA, valB;
                        switch (currentSortColumn) {
                            case "contact":
                                valA = (a.contact_name || a.phone_number || t.unknown).toLowerCase();
                                valB = (b.contact_name || b.phone_number || t.unknown).toLowerCase();
                                break;
                            case "number":
                                valA = (a.phone_number || "").toLowerCase();
                                valB = (b.phone_number || "").toLowerCase();
                                break;
                            case "duration":
                                valA = a.duration_seconds || 0;
                                valB = b.duration_seconds || 0;
                                break;
                            case "dir":
                                valA = (a.direction || "").toLowerCase();
                                valB = (b.direction || "").toLowerCase();
                                break;
                            case "service":
                                valA = (a.call_type || a.service || "").toLowerCase();
                                valB = (b.call_type || b.service || "").toLowerCase();
                                break;
                            case "date":
                            default:
                                valA = new Date(a.start || 0).getTime();
                                valB = new Date(b.start || 0).getTime();
                                break;
                        }
                        if (valA < valB) return currentSortAsc ? -1 : 1;
                        if (valA > valB) return currentSortAsc ? 1 : -1;
                        return 0;
                    });
                }

                document.querySelectorAll("th[data-sort]").forEach(th => {
                    const icon = th.querySelector(".sort-icon");
                    if (th.getAttribute("data-sort") === currentSortColumn) {
                        icon.innerHTML = currentSortAsc ? "arrow_upward" : "arrow_downward";
                        icon.classList.remove("opacity-0", "group-hover:opacity-50");
                        icon.classList.add("opacity-100", "text-primary");
                    } else {
                        icon.innerHTML = "swap_vert";
                        icon.classList.remove("opacity-100", "text-primary");
                        icon.classList.add("opacity-0", "group-hover:opacity-50");
                    }
                });

                if (totalCallsEl) {
                    totalCallsEl.innerHTML = filtered.length.toLocaleString();
                }

                if (totalDurationEl) {
                    const totalSec = filtered.reduce((acc, c) => acc + (c.duration_seconds || 0), 0);
                    const h = Math.floor(totalSec / 3600);
                    const m = Math.floor((totalSec % 3600) / 60);
                    const s = Math.floor(totalSec % 60);
                    totalDurationEl.innerHTML = `${h}<span class="text-on-surface-variant text-2xl ml-1">h</span> ${m}<span class="text-on-surface-variant text-2xl ml-1">m</span> ${s}<span class="text-on-surface-variant text-2xl ml-1">s</span>`;
                }

                if (topContactsContainer) {
                    const contactCounts = {};
                    filtered.forEach(c => {
                        const name = c.contact_name || c.phone_number || t.unknown;
                        contactCounts[name] = (contactCounts[name] || 0) + 1;
                    });

                    const sortedContacts = Object.entries(contactCounts).sort((a,b) => b[1] - a[1]).slice(0, 3);
                    
                    topContactsContainer.innerHTML = sortedContacts.map(sc => {
                        const initials = sc[0].substring(0, 2).toUpperCase();
                        return `
                        <div class="flex items-center justify-between p-xs rounded-lg hover:bg-white/5 transition-colors cursor-default">
                            <div class="flex items-center gap-sm">
                                <div class="w-8 h-8 rounded-full bg-surface-container flex items-center justify-center font-label-sm text-label-sm font-bold text-on-surface">${initials}</div>
                                <span class="font-body-md text-body-md text-on-surface">${sc[0]}</span>
                            </div>
                            <span class="font-label-md text-label-md text-on-surface-variant">${sc[1]} ${t.callsText}</span>
                        </div>`;
                    }).join("");
                }

                if (tbody) {
                    tbody.innerHTML = filtered.map(c => {
                        const dispName = c.contact_name || t.unknown;
                        const initials = dispName.substring(0, 2).toUpperCase();
                        const iconColor = getDirColor(c.direction);
                        const dateStr = c.start || '';
                        const servLabel = c.call_type || c.service || t.unknown;
                        const servClass = getServiceColor(c.call_type || c.service);
                        
                        return `
                        <tr class="border-b border-outline-variant/10 table-row-hover transition-colors cursor-pointer">
                            <td class="py-md px-lg">
                                <div class="flex items-center gap-sm">
                                    <div class="w-8 h-8 rounded-full bg-surface-container flex items-center justify-center font-bold text-sm text-on-surface">${initials}</div>
                                    <span class="font-medium text-on-surface">${dispName}</span>
                                </div>
                            </td>
                            <td class="py-md px-lg text-on-surface-variant">${c.phone_number || ''}</td>
                            <td class="py-md px-lg text-on-surface">${formatDuration(c.duration_seconds)}</td>
                            <td class="py-md px-lg">
                                <span class="material-symbols-outlined ${iconColor} text-lg" title="${translateDir(c.direction)}" style="font-variation-settings: 'FILL' 1;">${formatDirIcon(c.direction)}</span>
                            </td>
                            <td class="py-md px-lg text-on-surface-variant">${dateStr}</td>
                            <td class="py-md px-lg">
                                <span class="inline-flex items-center px-2 py-1 rounded-full font-label-sm text-label-sm border ${servClass}">${translateService(servLabel)}</span>
                            </td>
                        </tr>`;
                    }).join("");
                }
            }

            updateLangUI();
        });
    </script>'''

new_html = html[:start_idx] + new_script + html[end_idx:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_html)

print('Updated html successfully')
