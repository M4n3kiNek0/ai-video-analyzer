"""
AI Prompt Templates for Video/Audio Analysis.
Centralized storage for all prompt templates used by AIAnalyzer.
"""


# System message for transcription enrichment
SYSTEM_ENRICH_TRANSCRIPTION = "Sei un esperto analista di contenuti video. Analizza trascrizioni e produci analisi semantiche dettagliate in JSON."

# Prompt template for enriching transcription with semantic analysis
PROMPT_ENRICH_TRANSCRIPTION = """Analizza questa trascrizione audio di un video dimostrativo di un'applicazione software.

INFORMAZIONI VIDEO:
- File: {video_filename}
- Durata: {video_duration:.1f} secondi

TRASCRIZIONE COMPLETA:
{full_text}

SEGMENTI CON TIMESTAMP:
{segments_formatted}

Fornisci un'analisi dettagliata in formato JSON:
{{
    "semantic_summary": "Riassunto dettagliato di 3-5 frasi che descrive il contenuto del video, cosa viene mostrato/spiegato, e il contesto generale",
    "topics": [
        {{
            "topic": "Nome argomento/funzionalità discussa",
            "start_time": 0.0,
            "end_time": 30.0,
            "description": "Breve descrizione di cosa viene detto/mostrato su questo argomento"
        }}
    ],
    "tone": "professionale|informale|tutorial|presentazione|conversazione",
    "speaking_style": "descrizione dello stile di comunicazione",
    "speakers_detected": 1,
    "speaker_notes": "note sui parlanti se rilevante",
    "keywords": ["parola1", "parola2", "parola3"],
    "visual_context_hints": ["suggerimento1 per correlazione visiva", "suggerimento2"],
    "action_phrases": [
        {{
            "timestamp": 10.5,
            "phrase": "frase che indica un'azione visibile",
            "expected_visual": "cosa ci si aspetta di vedere nel video"
        }}
    ]
}}

IMPORTANTE:
- Identifica TUTTI gli argomenti discussi con i loro timestamp
- Estrai parole chiave utili per correlare con le immagini
- Identifica frasi che descrivono azioni ("clicco qui", "vediamo", "apriamo", etc.)
- Sii dettagliato nel riassunto semantico"""


# System message for contextual frame analysis
SYSTEM_CONTEXTUAL_FRAME = "Sei un esperto analista UX senior con 15 anni di esperienza. Il tuo compito è analizzare schermate di applicazioni software in modo ESTREMAMENTE DETTAGLIATO, documentando OGNI elemento visibile. Correli sempre l'analisi visiva con la narrazione audio per produrre documentazione tecnica di alta qualità. Rispondi SEMPRE con JSON valido e completo."

# Prompt template for contextual frame description (reverse engineering)
PROMPT_CONTEXTUAL_FRAME = """Sei un REVERSE ENGINEER e ANALISTA UX SENIOR. Devi documentare questa schermata per permettere la ricostruzione dell'applicazione.

=== CONTESTO VIDEO ===
{context_block}

=== ISTRUZIONI IMPORTANTI ===
1. USA SEMPRE il contesto fornito sopra per interpretare correttamente la schermata
2. Se il contesto menziona funzionalità specifiche (es: "POS", "gestione ordini", "pagamenti", "inventario"), cerca questi elementi nella schermata e correlali
3. Correla sempre ciò che vedi visivamente con ciò che è stato descritto nel contesto dell'applicazione
4. Se il contesto descrive un'applicazione per un dominio specifico (ristoranti, vendita, ecc.), interpreta gli elementi UI in quel contesto
5. Il contesto può aiutarti a capire la terminologia specifica del dominio e lo scopo funzionale degli elementi

=== OBIETTIVO: REVERSE ENGINEERING COMPLETO ===

Analizza questa schermata come se dovessi ricostruire l'applicazione da zero. Documenta OGNI dettaglio tecnico e visivo. USA IL CONTESTO per interpretare correttamente gli elementi visibili nella schermata.

**1. OVERVIEW FUNZIONALE** (4-5 frasi)
Cosa fa questa schermata, qual è il suo scopo nel flusso applicativo, quali operazioni CRUD permette.

**2. OCR - ESTRAI TUTTI I TESTI**
Leggi e trascrivi OGNI testo visibile: titoli, bottoni, label, menu, valori, placeholder, tooltip, badge, notifiche.

**3. ARCHITETTURA UI**
- Layout grid (quante colonne, responsive?)
- Gerarchia visiva (cosa è primario, secondario)
- Spacing e padding pattern
- Sistema di colori utilizzato

**4. COMPONENTI UI (per ricostruzione)**
Per OGNI componente identifica:
- Tipo esatto (Button/IconButton/FAB, TextField/Select/DatePicker, Card/List/Table, Modal/Dialog/Drawer, etc.)
- Variante (primary/secondary, filled/outlined, small/medium/large)
- Stato corrente (default/hover/active/disabled/loading/error)
- Icone utilizzate (nome se riconoscibile: edit, delete, add, menu, etc.)
- Props/Attributi visibili

**5. STRUTTURA DATI INFERITA**
Basandoti sui dati visualizzati, inferisci:
- Entità/Modelli (es: Tavolo, Sala, Prenotazione)
- Campi e tipi (nome: string, coperti: number, etc.)
- Relazioni (Sala ha molti Tavoli)
- Stati possibili (libero/occupato/prenotato)

**6. INTERAZIONI E EVENTI**
- Click handlers visibili (cosa succede cliccando ogni elemento)
- Drag & drop (se evidente)
- Form submission
- Navigation triggers
- Gesture (swipe, long-press se mobile)

**7. STATO APPLICATIVO**
- Dati caricati/visualizzati
- Selezioni attive
- Filtri applicati
- Modalità corrente (view/edit/create)
- Loading states

**8. API/BACKEND INFERITI**
Basandoti sulle operazioni visibili, inferisci:
- GET endpoints (cosa viene caricato)
- POST/PUT (cosa viene creato/modificato)
- DELETE (cosa viene eliminato)
- Parametri probabili

**9. TECNOLOGIE RILEVATE**
Indizi su framework/librerie:
- Design system (Material, Ant Design, Bootstrap, custom)
- Pattern React/Vue/Angular
- Stile CSS (Tailwind, styled-components)
- Mobile (nativo/ibrido/PWA)

**10. CORRELAZIONE CON AUDIO**
Come questa schermata si collega alla narrazione audio.

**11. DIFFERENZE DAL FRAME PRECEDENTE**
Cosa è cambiato (se hai info).

**12. NOTE PER RICOSTRUZIONE**
Suggerimenti tecnici per chi deve reimplementare.

=== OUTPUT JSON ===
{{
    "summary": "Descrizione funzionale completa della schermata",
    "screen_type": "dashboard|form|list|detail|modal|settings|navigation|editor|canvas|...",
    "module_name": "Nome del modulo/sezione dell'app",
    "audio_correlation": "Collegamento esatto con la narrazione audio",
    
    "ocr_extracted_texts": {{
        "headers": ["tutti i titoli/intestazioni"],
        "buttons": ["testo esatto di ogni bottone"],
        "labels": ["etichette campi form"],
        "menu_items": ["voci di navigazione/menu"],
        "data_values": ["valori visualizzati"],
        "tab_names": ["nomi delle tab"],
        "tooltips": ["testi tooltip se visibili"],
        "badges": ["badge e stati"]
    }},
    
    "layout_architecture": {{
        "grid_system": "descrizione griglia (es: 2 colonne, sidebar 250px + main)",
        "header_height": "stima altezza header",
        "navigation_type": "tabs|sidebar|drawer|bottom_nav|breadcrumb",
        "main_area": "descrizione area principale",
        "color_scheme": "palette colori dominanti (es: brown wood texture, blue accents)",
        "spacing_pattern": "pattern spaziature (es: 8px grid)"
    }},
    
    "components": [
        {{
            "id": "componente_1",
            "type": "tipo esatto (es: IconButton, TabBar, Canvas, FAB)",
            "variant": "primary|secondary|outlined|text|...",
            "label": "testo/etichetta",
            "icon": "nome icona se presente",
            "position": "top-left|header|footer|floating|...",
            "state": "default|active|disabled|selected|...",
            "size": "small|medium|large",
            "estimated_dimensions": "es: 48x48px",
            "interactions": ["click", "drag", "hover"],
            "children": "descrizione contenuto se container"
        }}
    ],
    
    "inferred_data_model": {{
        "entities": [
            {{
                "name": "nome entità (es: Tavolo)",
                "fields": [
                    {{"name": "id", "type": "string|number", "example": "valore esempio"}},
                    {{"name": "nome", "type": "string", "example": "18 bis"}}
                ],
                "relationships": ["appartiene a Sala"]
            }}
        ]
    }},
    
    "inferred_api": {{
        "get_endpoints": ["/api/sale", "/api/sale/:id/tavoli"],
        "post_endpoints": ["/api/tavoli"],
        "put_endpoints": ["/api/tavoli/:id"],
        "delete_endpoints": ["/api/tavoli/:id"],
        "websocket": "se real-time updates evidenti"
    }},
    
    "current_state": {{
        "mode": "view|edit|create|delete_confirm",
        "loaded_data": "descrizione dati caricati",
        "active_selection": "elementi selezionati",
        "active_filters": "filtri applicati",
        "modal_open": "nome modal se aperto"
    }},
    
    "current_action": {{
        "action": "azione in corso",
        "target_element": "elemento target",
        "user_intent": "cosa vuole fare l'utente",
        "next_step": "prossimo step probabile"
    }},
    
    "technology_hints": {{
        "ui_framework": "Material|AntDesign|Bootstrap|Custom",
        "frontend_framework": "React|Vue|Angular|unknown",
        "css_approach": "Tailwind|styled-components|CSS Modules|unknown",
        "platform": "web|mobile|desktop|hybrid",
        "design_patterns": ["pattern riconosciuti"]
    }},
    
    "transition_from_previous": {{
        "changed_elements": ["elementi modificati"],
        "new_elements": ["elementi nuovi"],
        "removed_elements": ["elementi rimossi"],
        "animation_detected": "tipo animazione se evidente"
    }},
    
    "reconstruction_notes": {{
        "key_components": ["componenti principali da implementare"],
        "complex_interactions": ["interazioni complesse da gestire"],
        "state_management": "suggerimenti per state management",
        "styling_notes": ["note per styling"]
    }},
    
    "detected_features": ["lista feature dell'app"],
    "confidence": "high|medium|low"
}}"""


# System message for full flow analysis
SYSTEM_FULL_FLOW_ANALYSIS = "Sei un esperto analista di software e UX. Analizza le demo video di applicazioni e genera report strutturati in JSON. Rispondi SEMPRE con JSON valido."

# Prompt template for full flow analysis
PROMPT_FULL_FLOW_ANALYSIS = """Sei un REVERSE ENGINEER. Analizza questa demo video per documentare l'applicazione in modo che possa essere ricostruita.

{context}Durata video: {video_duration:.1f} secondi

=== TRASCRIZIONE AUDIO ===
{truncated_transcript}

=== ANALISI SCHERMATE (con timestamp) ===
{keyframes_str}

=== OBIETTIVO: DOCUMENTAZIONE TECNICA COMPLETA ===

Genera una documentazione che permetta di:
1. Comprendere COSA fa l'applicazione
2. Capire COME è strutturata
3. Ricostruirla da zero

Rispondi con JSON:
{{
    "app_name_short": "Nome breve dell'app (es: Tilby)",
    "summary": "Descrizione completa dell'applicazione in 4-5 frasi, includendo scopo, target utenti, funzionalità principali",
    "app_type": "web|mobile|desktop|hybrid",
    "app_category": "POS|ERP|CRM|E-commerce|Dashboard|Management|...",
    
    "architecture_overview": {{
        "frontend_type": "SPA|MPA|Mobile Native|PWA",
        "estimated_complexity": "simple|medium|complex",
        "main_screens_count": 0,
        "navigation_pattern": "tabs|sidebar|drawer|bottom_nav|stack"
    }},
    
    "modules": [
        {{
            "name": "Nome modulo",
            "description": "Descrizione dettagliata funzionalità",
            "purpose": "Scopo del modulo",
            "screens": ["lista schermate"],
            "key_features": ["feature dettagliata 1", "feature 2"],
            "crud_operations": ["create", "read", "update", "delete"],
            "data_entities": ["entità gestite dal modulo"]
        }}
    ],
    
    "data_model": {{
        "entities": [
            {{
                "name": "NomeEntità",
                "description": "Descrizione entità",
                "fields": [
                    {{"name": "campo", "type": "string|number|boolean|date|enum|relation", "description": "descrizione", "required": true, "example": "valore"}}
                ],
                "relationships": [
                    {{"type": "has_many|belongs_to|has_one", "target": "AltraEntità", "description": "descrizione relazione"}}
                ]
            }}
        ],
        "enums": [
            {{"name": "NomeEnum", "values": ["value1", "value2"], "description": "descrizione"}}
        ]
    }},
    
    "user_flows": [
        {{
            "name": "Nome flusso (es: Aggiunta Nuovo Tavolo)",
            "description": "Descrizione completa del flusso",
            "trigger": "Cosa avvia questo flusso",
            "actors": ["Utente", "Sistema"],
            "preconditions": ["condizioni necessarie"],
            "steps": [
                {{
                    "step": 1,
                    "timestamp": "0:XXs",
                    "actor": "Utente|Sistema",
                    "action": "Descrizione azione dettagliata",
                    "ui_element": "elemento UI coinvolto",
                    "input_data": "dati inseriti se presenti",
                    "system_response": "risposta del sistema",
                    "next_state": "stato risultante"
                }}
            ],
            "outcome": "Risultato finale del flusso",
            "alternative_paths": ["varianti del flusso"]
        }}
    ],
    
    "api_specification": {{
        "base_url": "/api",
        "endpoints": [
            {{
                "method": "GET|POST|PUT|DELETE",
                "path": "/risorsa/:id",
                "description": "Cosa fa questo endpoint",
                "request_body": {{"campo": "tipo"}},
                "response": {{"campo": "tipo"}},
                "inferred_from": "timestamp o schermata di riferimento"
            }}
        ]
    }},
    
    "ui_components_library": {{
        "design_system": "Material|AntDesign|Bootstrap|Custom|unknown",
        "components_used": [
            {{
                "name": "NomeComponente",
                "type": "Button|Input|Modal|Table|Card|...",
                "variants": ["primary", "secondary"],
                "usage_count": "stimato",
                "custom_styling": "note su stili custom"
            }}
        ],
        "icons_library": "Material Icons|FontAwesome|Custom|...",
        "color_palette": {{
            "primary": "#colore",
            "secondary": "#colore",
            "background": "descrizione",
            "accent": "#colore"
        }}
    }},
    
    "state_management": {{
        "global_state": ["dati gestiti globalmente"],
        "local_state": ["dati gestiti per componente"],
        "persistence": "localStorage|sessionStorage|cookies|none"
    }},
    
    "issues_and_observations": [
        {{
            "type": "UI|UX|Performance|Bug|Accessibility|Data|Security",
            "description": "Descrizione dettagliata",
            "timestamp": "X:XXs",
            "severity": "low|medium|high|critical",
            "affected_component": "componente coinvolto",
            "suggested_fix": "come risolvere"
        }}
    ],
    
    "technology_stack": {{
        "frontend_framework": "React|Vue|Angular|Svelte|unknown",
        "ui_library": "Material UI|Ant Design|Chakra|...",
        "state_management": "Redux|Zustand|Vuex|Context|...",
        "styling": "CSS Modules|Tailwind|styled-components|...",
        "platform": "Web|iOS|Android|Electron|..."
    }},
    
    "recommendations": [
        {{
            "category": "UX|Performance|Architecture|Feature",
            "priority": "low|medium|high",
            "description": "Descrizione dettagliata del suggerimento",
            "implementation_hint": "Come implementare"
        }}
    ],
    
    "reconstruction_guide": {{
        "estimated_effort": "hours|days|weeks",
        "key_challenges": ["sfide principali"],
        "required_skills": ["competenze necessarie"],
        "suggested_stack": ["tecnologie suggerite per ricostruzione"],
        "mvp_features": ["feature essenziali per MVP"]
    }}
}}

IMPORTANTE:
- Usa timestamp reali del video
- Sii SPECIFICO e DETTAGLIATO
- Inferisci la struttura dati dai dati visualizzati
- Documenta OGNI flusso utente osservato
- Fornisci una specifica API completa basata sulle operazioni viste"""


# System message for enhanced executive summary
SYSTEM_ENHANCED_EXECUTIVE_SUMMARY = "Sei un esperto analista di documentazione tecnica. Il tuo compito è creare un riepilogo esecutivo completo e coerente che integra informazioni da multiple fonti (trascrizione audio, analisi visiva, moduli identificati) in un unico testo fluido e ben strutturato. Produci sempre output JSON valido."

# Prompt template for enhanced executive summary
PROMPT_ENHANCED_EXECUTIVE_SUMMARY = """Sei un ESPERTO ANALISTA di documentazione tecnica. Il tuo compito è creare un Riepilogo Esecutivo completo e coerente per un report di analisi video.

=== CONTESTO ===
{user_context}

=== SUMMARY ESISTENTE ===
{existing_summary}

=== RIASSUNTO SEMANTICO (Trascrizione Audio) ===
{semantic_summary}

=== OSSERVAZIONI CHIAVE DAI KEYFRAME ===
{keyframes_observations}

=== MODULI IDENTIFICATI ===
{modules_summary}

=== FLUSSI UTENTE PRINCIPALI ===
{user_flows_summary}

=== OBIETTIVO: RIEPILOGO ESECUTIVO COMPLETO ===

Genera un riepilogo esecutivo che:
1. Integra in modo coerente tutte le informazioni fornite
2. È fluido e ben strutturato (non una semplice concatenazione)
3. Evidenzia gli insight chiave dall'analisi visiva
4. Include il contesto del dominio applicativo
5. Ha una lunghezza appropriata (4-7 paragrafi)

Il riepilogo deve essere scritto in italiano, professionale, e dare una visione completa dell'applicazione analizzata.

Rispondi con JSON:
{{
    "executive_summary": "Riepilogo esecutivo completo in 4-7 paragrafi che integra tutte le fonti in modo coerente e fluido. Deve essere ben strutturato e professionale.",
    "key_insights": ["insight chiave 1", "insight chiave 2", "insight chiave 3"],
    "application_context": "Contesto del dominio applicativo e scopo principale",
    "main_functionality": "Descrizione delle funzionalità principali identificate"
}}

IMPORTANTE:
- NON fare semplice copia-incolla delle varie fonti
- Crea un testo COERENTE e FLUIDO che integra tutto
- Evidenzia gli insight più importanti
- Usa il contesto utente per interpretare correttamente l'applicazione
- Mantieni un tono professionale e chiaro"""


# System message for audio content analysis
SYSTEM_AUDIO_CONTENT_ANALYSIS = "Sei un esperto analista di contenuti audio. Analizzi registrazioni audio di meeting, interviste, podcast e conversazioni per estrarre insight strutturati. Produci sempre output JSON valido e completo, con particolare attenzione ad action items, decisioni e idee emerse."

# Prompt template for audio content analysis
PROMPT_AUDIO_CONTENT_ANALYSIS = """Sei un ANALISTA ESPERTO di contenuti audio. Analizza questa registrazione audio per produrre un report strutturato completo.

=== INFORMAZIONI FILE ===
- File: {audio_filename}
- Durata: {audio_duration:.1f} secondi ({duration_minutes} minuti)
- Parlanti rilevati: {speakers_detected}
- Tono: {tone}
{context_block}

=== RIASSUNTO SEMANTICO ===
{semantic_summary}

=== ARGOMENTI IDENTIFICATI ===
{topics_str}

=== PAROLE CHIAVE ===
{keywords_str}

=== TRASCRIZIONE ===
{truncated_transcript}

=== OBIETTIVO: ANALISI COMPLETA AUDIO ===

Genera un'analisi strutturata che includa:
1. Riepilogo esecutivo (cosa viene discusso, conclusioni principali)
2. Identificazione e profilo dei parlanti (se multipli)
3. Argomenti principali con timeline
4. Action items e task estratti
5. Decisioni chiave prese
6. Idee e proposte emerse
7. Punti di discussione aperti
8. Raccomandazioni

Rispondi con JSON:
{{
    "summary": "Riassunto esecutivo completo di 5-7 frasi che cattura l'essenza della registrazione",
    "audio_type": "meeting|interview|podcast|brainstorming|presentation|voice_note|lecture|conversation",
    "audio_category": "business|technical|creative|educational|personal|other",
    
    "metadata": {{
        "duration_formatted": "{duration_formatted}",
        "speakers_count": {speakers_detected},
        "language": "it",
        "tone": "{tone}",
        "formality_level": "formal|semi-formal|informal",
        "energy_level": "high|medium|low"
    }},
    
    "speakers": [
        {{
            "id": "speaker_1",
            "inferred_name": "Nome se menzionato o Speaker 1",
            "role": "ruolo inferito (moderatore, esperto, partecipante, etc.)",
            "speaking_percentage": 50,
            "characteristics": "note sullo stile di comunicazione",
            "key_contributions": ["contributo 1", "contributo 2"]
        }}
    ],
    
    "topics": [
        {{
            "name": "Nome argomento",
            "start_time": 0,
            "end_time": 120,
            "duration_seconds": 120,
            "summary": "Riassunto di cosa viene detto su questo argomento",
            "key_points": ["punto 1", "punto 2"],
            "speakers_involved": ["speaker_1"],
            "sentiment": "positive|neutral|negative|mixed"
        }}
    ],
    
    "action_items": [
        {{
            "item": "Descrizione del task/azione",
            "assignee": "persona responsabile se menzionata",
            "deadline": "deadline se menzionata",
            "priority": "high|medium|low",
            "timestamp": "MM:SS quando viene menzionato",
            "context": "contesto in cui viene discusso"
        }}
    ],
    
    "decisions": [
        {{
            "decision": "Descrizione della decisione presa",
            "timestamp": "MM:SS",
            "made_by": "chi ha preso la decisione",
            "rationale": "motivazione se discussa",
            "impact": "impatto previsto"
        }}
    ],
    
    "ideas_and_proposals": [
        {{
            "idea": "Descrizione dell'idea/proposta",
            "proposed_by": "speaker se identificabile",
            "timestamp": "MM:SS",
            "reception": "accepted|discussed|rejected|pending",
            "details": "dettagli aggiuntivi"
        }}
    ],
    
    "questions_raised": [
        {{
            "question": "Domanda posta",
            "asked_by": "speaker",
            "timestamp": "MM:SS",
            "answered": true,
            "answer_summary": "riassunto risposta se data"
        }}
    ],
    
    "key_quotes": [
        {{
            "quote": "Citazione importante verbatim",
            "speaker": "chi l'ha detta",
            "timestamp": "MM:SS",
            "significance": "perché è importante"
        }}
    ],
    
    "open_issues": [
        {{
            "issue": "Problema/questione rimasta aperta",
            "discussed_at": "MM:SS",
            "requires_followup": true,
            "suggested_next_steps": "passi suggeriti"
        }}
    ],
    
    "sentiment_analysis": {{
        "overall_sentiment": "positive|neutral|negative|mixed",
        "sentiment_progression": "descrizione di come cambia il sentiment",
        "tension_points": ["momenti di tensione se presenti"],
        "positive_moments": ["momenti positivi"]
    }},
    
    "content_structure": {{
        "introduction": {{"start": 0, "end": 0, "summary": ""}},
        "main_body": [{{"topic": "", "start": 0, "end": 0}}],
        "conclusion": {{"start": 0, "end": 0, "summary": ""}}
    }},
    
    "recommendations": [
        {{
            "category": "follow_up|process|communication|content",
            "priority": "high|medium|low",
            "recommendation": "Suggerimento specifico",
            "rationale": "Motivazione"
        }}
    ],
    
    "tags": ["tag1", "tag2", "tag3"],
    
    "next_steps": [
        "Passo successivo suggerito 1",
        "Passo successivo suggerito 2"
    ],
    
    "confidence": "high|medium|low",
    "analysis_notes": "Note aggiuntive sull'analisi"
}}

IMPORTANTE:
- Usa timestamp reali (MM:SS) basati sulla trascrizione
- Identifica TUTTI gli action items menzionati
- Estrai OGNI decisione presa durante la discussione
- Sii preciso nell'attribuire citazioni e idee ai parlanti
- Fornisci un'analisi del sentiment basata sul tono della conversazione"""


# System message for prompt optimization
SYSTEM_OPTIMIZE_CONTEXT = "Sei un esperto di prompt engineering. Il tuo compito è migliorare le descrizioni fornite dagli utenti per analisi video di applicazioni software. Mantieni sempre il significato originale ma aggiungi struttura, dettagli e indicazioni utili per un'analisi più accurata. Rispondi sempre con JSON valido."

# Prompt template for context optimization
PROMPT_OPTIMIZE_CONTEXT = """Sei un esperto di prompt engineering specializzato in analisi video di applicazioni software.

L'utente ha fornito questa descrizione per guidare l'analisi di un video demo:

--- DESCRIZIONE ORIGINALE ---
{user_context}
--- FINE DESCRIZIONE ---

Il tuo compito è MIGLIORARE questa descrizione per ottenere un'analisi video più accurata e dettagliata.
L'utente vedrà sia la versione originale che quella ottimizzata e potrà scegliere quale usare.

LINEE GUIDA PER L'OTTIMIZZAZIONE:
1. Mantieni il significato e l'intento originale dell'utente
2. Espandi i dettagli dove appropriato (tipo di applicazione, contesto d'uso)
3. Aggiungi struttura se mancante (suddividi in sezioni logiche)
4. Usa terminologia tecnica appropriata (UI, UX, flussi utente, etc.)
5. Se l'utente menziona un'app specifica, MANTIENI il nome
6. Aggiungi indicazioni specifiche su cosa documentare nell'analisi
7. Specifica gli aspetti chiave da osservare (navigazione, interazioni, dati)
8. NON inventare informazioni non presenti nell'originale
9. La versione ottimizzata dovrebbe essere più lunga e dettagliata ma NON eccessivamente prolissa

Rispondi con un JSON valido:
{{
    "optimized_text": "La descrizione migliorata e più dettagliata. Deve essere almeno 30% più lunga dell'originale.",
    "improvements": [
        "Descrizione breve del primo miglioramento applicato",
        "Descrizione breve del secondo miglioramento applicato",
        "..."
    ]
}}

Assicurati che improvements contenga 3-5 voci che spiegano cosa hai migliorato."""


# =============================================================================
# CONTENT TYPE INFERENCE
# =============================================================================

SYSTEM_INFER_CONTENT_TYPE = "Sei un esperto classificatore di contenuti audio/video. Determina il tipo di contenuto analizzando la trascrizione. Rispondi sempre con JSON valido."

PROMPT_INFER_CONTENT_TYPE = """Analizza questa trascrizione e determina il tipo di contenuto più appropriato.

=== TRASCRIZIONE ===
{transcript}

=== CONTESTO UTENTE (se fornito) ===
{user_context}

=== TIPI DISPONIBILI ===
1. **reverse_engineering**: Video demo di applicazioni software, tutorial tecnici, walkthrough di interfacce
   - Indicatori: click, schermata, bottone, menu, applicazione, software, interfaccia, demo, funzionalità

2. **meeting**: Riunioni strutturate con agenda, decisioni e action items
   - Indicatori: riunione, meeting, punto, agenda, decisione, task, assegnare, team, progetto, deadline

3. **debrief**: Analisi post-evento, retrospettive, post-mortem
   - Indicatori: retrospettiva, cosa ha funzionato, migliorare, lessons learned, errori, successi, analisi

4. **brainstorming**: Sessioni creative per generare idee
   - Indicatori: idee, proposta, creatività, e se, potremmo, alternativa, soluzione, pensare

5. **notes**: Appunti generici, memo vocali, riflessioni
   - Indicatori: nota, appunto, promemoria, pensiero, riflessione (o nessun pattern specifico)

=== OUTPUT JSON ===
{{
    "content_type": "reverse_engineering|meeting|debrief|brainstorming|notes",
    "confidence": 0.0-1.0,
    "reasoning": "Spiegazione breve del perché hai scelto questo tipo",
    "detected_indicators": ["indicatore1", "indicatore2"],
    "alternative_type": "tipo alternativo se confidence < 0.7",
    "alternative_confidence": 0.0-1.0
}}

IMPORTANTE:
- Se il contenuto è chiaramente tecnico/software, scegli "reverse_engineering"
- Se ci sono action items e decisioni esplicite, scegli "meeting"
- Se si parla di cosa è andato bene/male, scegli "debrief"
- Se si generano molte idee nuove, scegli "brainstorming"
- Se non rientra in nessuna categoria specifica, scegli "notes"
- Fornisci sempre una confidence realistica"""


# =============================================================================
# TEMPLATE-SPECIFIC PROMPTS - MEETING
# =============================================================================

SYSTEM_MEETING_ANALYSIS = "Sei un esperto facilitatore di riunioni e analista di meeting. Estrai informazioni strutturate da registrazioni di riunioni con focus su action items, decisioni e follow-up. Produci sempre output JSON valido."

PROMPT_MEETING_ANALYSIS = """Sei un ESPERTO FACILITATORE DI MEETING. Analizza questa registrazione di riunione per produrre un verbale strutturato e completo.

=== INFORMAZIONI FILE ===
- File: {audio_filename}
- Durata: {audio_duration:.1f} secondi ({duration_minutes} minuti)
- Parlanti rilevati: {speakers_detected}
- Tono: {tone}
{context_block}

=== RIASSUNTO SEMANTICO ===
{semantic_summary}

=== ARGOMENTI IDENTIFICATI ===
{topics_str}

=== TRASCRIZIONE ===
{truncated_transcript}

=== OBIETTIVO: VERBALE DI RIUNIONE COMPLETO ===

Genera un verbale di riunione professionale con:
1. Executive summary (3-5 frasi)
2. Lista partecipanti con ruoli
3. Argomenti discussi con timeline
4. TUTTI gli action items (con responsabile, deadline, priorità)
5. TUTTE le decisioni prese
6. Questioni rimaste aperte
7. Prossimi passi concreti

Rispondi con JSON:
{{
    "summary": "Executive summary della riunione in 3-5 frasi",
    "meeting_type": "standup|planning|retrospective|decision|brainstorm|status_update|kickoff|review|other",
    
    "meeting_info": {{
        "duration_formatted": "{duration_formatted}",
        "participants_count": {speakers_detected},
        "main_topic": "Argomento principale della riunione",
        "meeting_objective": "Obiettivo della riunione",
        "outcome": "Risultato raggiunto o meno"
    }},
    
    "participants": [
        {{
            "id": "speaker_1",
            "name": "Nome se menzionato",
            "role": "Ruolo inferito (facilitatore, decisore, contributor, observer)",
            "speaking_time_percent": 50,
            "contributions": ["contributo chiave 1", "contributo chiave 2"]
        }}
    ],
    
    "agenda_topics": [
        {{
            "topic": "Nome argomento",
            "start_time": "MM:SS",
            "end_time": "MM:SS",
            "duration_minutes": 10,
            "summary": "Riassunto discussione",
            "key_points": ["punto 1", "punto 2"],
            "outcome": "Decisione presa o azione definita"
        }}
    ],
    
    "action_items": [
        {{
            "id": "AI-001",
            "description": "Descrizione chiara del task",
            "assignee": "Nome responsabile",
            "deadline": "Data/termine se menzionato",
            "priority": "high|medium|low",
            "status": "new|in_progress|blocked",
            "timestamp": "MM:SS quando discusso",
            "context": "Contesto/motivazione",
            "dependencies": ["eventuali dipendenze"]
        }}
    ],
    
    "decisions": [
        {{
            "id": "DEC-001",
            "decision": "Descrizione della decisione",
            "timestamp": "MM:SS",
            "made_by": "Chi ha preso/proposto la decisione",
            "rationale": "Motivazione",
            "impact": "Impatto previsto",
            "dissent": "Eventuali obiezioni o riserve",
            "follow_up_required": true
        }}
    ],
    
    "open_issues": [
        {{
            "issue": "Questione non risolta",
            "discussed_at": "MM:SS",
            "blocker_for": "Cosa blocca",
            "proposed_solutions": ["soluzione 1", "soluzione 2"],
            "next_steps": "Come procedere",
            "owner": "Chi se ne occupa"
        }}
    ],
    
    "next_steps": [
        {{
            "step": "Azione da fare",
            "owner": "Responsabile",
            "timeline": "Entro quando"
        }}
    ],
    
    "follow_up_meeting": {{
        "needed": true,
        "suggested_date": "Suggerimento data",
        "topics_to_cover": ["argomento 1", "argomento 2"]
    }},
    
    "key_quotes": [
        {{
            "quote": "Citazione importante",
            "speaker": "Chi l'ha detta",
            "timestamp": "MM:SS",
            "context": "Perché è rilevante"
        }}
    ],
    
    "meeting_effectiveness": {{
        "objectives_met": true,
        "time_well_spent": "high|medium|low",
        "participation_balance": "Tutti hanno partecipato equamente?",
        "improvement_suggestions": ["suggerimento 1"]
    }},
    
    "tags": ["tag1", "tag2"],
    "confidence": "high|medium|low"
}}

IMPORTANTE:
- Estrai OGNI action item, anche quelli impliciti
- Identifica TUTTE le decisioni, anche quelle informali
- Associa sempre un responsabile agli action items quando possibile
- Segnala le questioni rimaste aperte
- Usa timestamp reali dalla trascrizione"""


# =============================================================================
# TEMPLATE-SPECIFIC PROMPTS - DEBRIEF
# =============================================================================

SYSTEM_DEBRIEF_ANALYSIS = "Sei un esperto facilitatore di retrospettive e analisi post-mortem. Estrai lessons learned, successi, aree di miglioramento e raccomandazioni da discussioni di debrief. Produci sempre output JSON valido."

PROMPT_DEBRIEF_ANALYSIS = """Sei un FACILITATORE ESPERTO di retrospettive e debrief. Analizza questa registrazione per produrre un report di debrief strutturato.

=== INFORMAZIONI FILE ===
- File: {audio_filename}
- Durata: {audio_duration:.1f} secondi ({duration_minutes} minuti)
- Parlanti rilevati: {speakers_detected}
- Tono: {tone}
{context_block}

=== RIASSUNTO SEMANTICO ===
{semantic_summary}

=== ARGOMENTI IDENTIFICATI ===
{topics_str}

=== TRASCRIZIONE ===
{truncated_transcript}

=== OBIETTIVO: REPORT DI DEBRIEF COMPLETO ===

Genera un report di debrief che catturi:
1. Cosa è stato analizzato/discusso
2. Cosa ha funzionato bene (successi)
3. Cosa non ha funzionato (problemi)
4. Lessons learned
5. Azioni correttive proposte
6. Raccomandazioni per il futuro

Rispondi con JSON:
{{
    "executive_summary": "Riassunto esecutivo del debrief in 4-6 frasi",
    "debrief_type": "project|event|sprint|incident|process|general",
    
    "event_overview": {{
        "subject": "Cosa viene analizzato (progetto, evento, sprint, etc.)",
        "timeframe": "Periodo di riferimento",
        "participants": ["partecipanti al debrief"],
        "context": "Contesto e obiettivi originali"
    }},
    
    "key_findings": [
        {{
            "finding": "Scoperta/osservazione chiave",
            "category": "success|issue|neutral",
            "impact": "high|medium|low",
            "evidence": "Cosa supporta questa osservazione",
            "timestamp": "MM:SS quando discusso"
        }}
    ],
    
    "what_worked": [
        {{
            "item": "Cosa ha funzionato",
            "why": "Perché ha funzionato",
            "impact": "Impatto positivo",
            "replicable": true,
            "recommendation": "Come replicare in futuro"
        }}
    ],
    
    "what_didnt_work": [
        {{
            "item": "Cosa non ha funzionato",
            "root_cause": "Causa radice se identificata",
            "impact": "Impatto negativo",
            "preventable": true,
            "mitigation": "Come mitigare/prevenire in futuro"
        }}
    ],
    
    "lessons_learned": [
        {{
            "lesson": "Lezione appresa",
            "category": "process|technical|communication|planning|execution|other",
            "applies_to": "A cosa si applica",
            "priority": "high|medium|low",
            "actionable": true,
            "action": "Azione concreta per applicare la lezione"
        }}
    ],
    
    "improvements": [
        {{
            "area": "Area da migliorare",
            "current_state": "Situazione attuale",
            "desired_state": "Situazione desiderata",
            "proposed_actions": ["azione 1", "azione 2"],
            "owner": "Chi se ne occupa",
            "timeline": "Quando implementare"
        }}
    ],
    
    "action_items": [
        {{
            "action": "Azione da intraprendere",
            "owner": "Responsabile",
            "deadline": "Scadenza",
            "priority": "high|medium|low",
            "linked_to": "A quale lesson/improvement è collegato"
        }}
    ],
    
    "recommendations": [
        {{
            "recommendation": "Raccomandazione specifica",
            "rationale": "Motivazione",
            "priority": "high|medium|low",
            "effort": "low|medium|high",
            "impact": "low|medium|high",
            "quick_win": true
        }}
    ],
    
    "sentiment_analysis": {{
        "overall_tone": "constructive|defensive|blame|collaborative|neutral",
        "team_morale": "high|medium|low",
        "psychological_safety": "Osservazioni sulla sicurezza psicologica"
    }},
    
    "metrics_mentioned": [
        {{
            "metric": "Nome metrica",
            "value": "Valore",
            "target": "Obiettivo",
            "status": "met|missed|exceeded"
        }}
    ],
    
    "follow_up": {{
        "next_debrief": "Quando fare follow-up",
        "tracking_needed": ["cosa monitorare"],
        "success_criteria": ["come misurare il miglioramento"]
    }},
    
    "tags": ["tag1", "tag2"],
    "confidence": "high|medium|low"
}}

IMPORTANTE:
- Bilancia successi e aree di miglioramento
- Identifica cause radice, non solo sintomi
- Rendi le lessons learned actionable
- Prioritizza le raccomandazioni
- Mantieni un tono costruttivo nell'analisi"""


# =============================================================================
# TEMPLATE-SPECIFIC PROMPTS - BRAINSTORMING
# =============================================================================

SYSTEM_BRAINSTORMING_ANALYSIS = "Sei un esperto facilitatore di sessioni creative e brainstorming. Raccogli, categorizza e valuta idee emerse da sessioni di ideazione. Produci sempre output JSON valido."

PROMPT_BRAINSTORMING_ANALYSIS = """Sei un FACILITATORE ESPERTO di sessioni di brainstorming. Analizza questa registrazione per raccogliere e organizzare tutte le idee emerse.

=== INFORMAZIONI FILE ===
- File: {audio_filename}
- Durata: {audio_duration:.1f} secondi ({duration_minutes} minuti)
- Parlanti rilevati: {speakers_detected}
- Tono: {tone}
{context_block}

=== RIASSUNTO SEMANTICO ===
{semantic_summary}

=== ARGOMENTI IDENTIFICATI ===
{topics_str}

=== TRASCRIZIONE ===
{truncated_transcript}

=== OBIETTIVO: REPORT BRAINSTORMING COMPLETO ===

Genera un report che catturi:
1. Tutte le idee emerse (anche abbozzi)
2. Categorizzazione delle idee
3. Le idee più promettenti
4. Valutazione fattibilità/impatto
5. Connessioni tra idee
6. Prossimi passi

Rispondi con JSON:
{{
    "session_overview": {{
        "topic": "Argomento/sfida del brainstorming",
        "objective": "Obiettivo della sessione",
        "duration_formatted": "{duration_formatted}",
        "participants_count": {speakers_detected},
        "ideas_count": 0,
        "energy_level": "high|medium|low",
        "creativity_level": "high|medium|low"
    }},
    
    "participants": [
        {{
            "id": "speaker_1",
            "name": "Nome se identificato",
            "ideas_contributed": 5,
            "role": "Ruolo nella sessione",
            "style": "Stile di contribuzione (divergente, convergente, costruttivo, critico)"
        }}
    ],
    
    "ideas_collected": [
        {{
            "id": "IDEA-001",
            "idea": "Descrizione completa dell'idea",
            "proposed_by": "Chi l'ha proposta",
            "timestamp": "MM:SS",
            "category": "Categoria tematica",
            "type": "new|improvement|combination|wild",
            "build_on": "ID idea precedente se è un'evoluzione",
            "reception": "enthusiasm|interest|neutral|skepticism",
            "discussed_further": true,
            "keywords": ["keyword1", "keyword2"]
        }}
    ],
    
    "ideas_by_category": [
        {{
            "category": "Nome categoria",
            "description": "Descrizione della categoria",
            "ideas_count": 5,
            "idea_ids": ["IDEA-001", "IDEA-002"],
            "theme": "Tema comune"
        }}
    ],
    
    "top_ideas": [
        {{
            "id": "IDEA-001",
            "idea": "L'idea",
            "why_top": "Perché è tra le migliori",
            "potential_impact": "high|medium|low",
            "feasibility": "high|medium|low",
            "innovation_level": "incremental|significant|breakthrough",
            "next_steps": ["passo 1", "passo 2"]
        }}
    ],
    
    "feasibility_analysis": [
        {{
            "idea_id": "IDEA-001",
            "idea_summary": "Breve descrizione",
            "feasibility_score": 1-5,
            "impact_score": 1-5,
            "effort_estimate": "low|medium|high",
            "risks": ["rischio 1"],
            "dependencies": ["dipendenza 1"],
            "quick_win": true
        }}
    ],
    
    "idea_connections": [
        {{
            "connection": "Descrizione della connessione",
            "ideas_involved": ["IDEA-001", "IDEA-002"],
            "synergy_potential": "high|medium|low",
            "combined_idea": "Idea risultante dalla combinazione"
        }}
    ],
    
    "parking_lot": [
        {{
            "item": "Idea o punto parcheggiato",
            "reason": "Perché è stato parcheggiato",
            "revisit_when": "Quando riprendere"
        }}
    ],
    
    "session_dynamics": {{
        "divergent_phase": {{"start": "MM:SS", "end": "MM:SS", "ideas_generated": 10}},
        "convergent_phase": {{"start": "MM:SS", "end": "MM:SS", "ideas_selected": 3}},
        "energy_peaks": ["MM:SS momento di alta energia"],
        "blockers": ["eventuali blocchi creativi"],
        "breakthrough_moments": ["momenti di insight"]
    }},
    
    "next_steps": [
        {{
            "step": "Azione da fare",
            "owner": "Responsabile",
            "timeline": "Quando",
            "related_ideas": ["IDEA-001"]
        }}
    ],
    
    "follow_up_sessions": {{
        "needed": true,
        "focus": "Su cosa concentrarsi",
        "suggested_techniques": ["tecnica 1", "tecnica 2"]
    }},
    
    "key_quotes": [
        {{
            "quote": "Frase significativa",
            "speaker": "Chi",
            "context": "Perché rilevante"
        }}
    ],
    
    "tags": ["tag1", "tag2"],
    "confidence": "high|medium|low"
}}

IMPORTANTE:
- Cattura OGNI idea, anche quelle abbozzate
- Non giudicare le idee, documentale tutte
- Identifica le connessioni tra idee
- Evidenzia le idee più promettenti
- Suggerisci combinazioni creative"""


# =============================================================================
# TEMPLATE-SPECIFIC PROMPTS - NOTES
# =============================================================================

SYSTEM_NOTES_ANALYSIS = "Sei un esperto nel sintetizzare contenuti audio in note strutturate e facilmente consultabili. Estrai i punti chiave e organizzali in modo chiaro. Produci sempre output JSON valido."

PROMPT_NOTES_ANALYSIS = """Sei un ESPERTO nel creare note strutturate da contenuti audio. Analizza questa registrazione per produrre appunti chiari e organizzati.

=== INFORMAZIONI FILE ===
- File: {audio_filename}
- Durata: {audio_duration:.1f} secondi ({duration_minutes} minuti)
- Parlanti rilevati: {speakers_detected}
- Tono: {tone}
{context_block}

=== RIASSUNTO SEMANTICO ===
{semantic_summary}

=== ARGOMENTI IDENTIFICATI ===
{topics_str}

=== TRASCRIZIONE ===
{truncated_transcript}

=== OBIETTIVO: NOTE STRUTTURATE ===

Genera note chiare e organizzate con:
1. Riassunto conciso
2. Punti chiave (bullet points)
3. Argomenti trattati
4. Citazioni importanti
5. Riferimenti menzionati

Rispondi con JSON:
{{
    "summary": "Riassunto conciso in 3-4 frasi",
    "content_type": "lecture|podcast|interview|monologue|conversation|voice_memo|other",
    
    "metadata": {{
        "duration_formatted": "{duration_formatted}",
        "speakers_count": {speakers_detected},
        "language": "it",
        "tone": "{tone}",
        "complexity": "simple|moderate|complex"
    }},
    
    "key_points": [
        {{
            "point": "Punto chiave",
            "importance": "high|medium|low",
            "timestamp": "MM:SS",
            "details": "Dettagli aggiuntivi se necessario"
        }}
    ],
    
    "topics": [
        {{
            "topic": "Nome argomento",
            "start_time": "MM:SS",
            "end_time": "MM:SS",
            "summary": "Breve riassunto",
            "subtopics": ["sottotema 1", "sottotema 2"]
        }}
    ],
    
    "important_mentions": [
        {{
            "mention": "Cosa viene menzionato (persona, azienda, concetto, etc.)",
            "type": "person|company|concept|product|event|place|other",
            "context": "In che contesto",
            "timestamp": "MM:SS"
        }}
    ],
    
    "quotes": [
        {{
            "quote": "Citazione significativa",
            "speaker": "Chi l'ha detta",
            "timestamp": "MM:SS",
            "significance": "Perché è importante"
        }}
    ],
    
    "references": [
        {{
            "reference": "Riferimento menzionato (libro, articolo, sito, etc.)",
            "type": "book|article|website|video|podcast|person|other",
            "context": "Come viene menzionato",
            "url": "URL se menzionato"
        }}
    ],
    
    "numbers_and_data": [
        {{
            "data": "Dato o numero menzionato",
            "context": "A cosa si riferisce",
            "timestamp": "MM:SS"
        }}
    ],
    
    "questions_raised": [
        {{
            "question": "Domanda emersa",
            "answered": true,
            "answer": "Risposta se data"
        }}
    ],
    
    "action_items": [
        {{
            "item": "Cosa fare",
            "priority": "high|medium|low"
        }}
    ],
    
    "related_topics": ["argomento correlato 1", "argomento correlato 2"],
    
    "tags": ["tag1", "tag2", "tag3"],
    
    "quick_reference": {{
        "one_sentence_summary": "Riassunto in una frase",
        "main_takeaway": "Cosa ricordare principalmente",
        "follow_up_needed": true,
        "follow_up_actions": ["azione 1"]
    }},
    
    "confidence": "high|medium|low"
}}

IMPORTANTE:
- Mantieni le note concise ma complete
- Evidenzia i punti davvero importanti
- Organizza per facilità di consultazione
- Includi timestamp per riferimento
- Estrai dati e numeri rilevanti"""

