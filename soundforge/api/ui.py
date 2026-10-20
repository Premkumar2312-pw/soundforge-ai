"""
Embedded Demonstration Web UI for SoundForge AI
Professional creator interface for AI background music synthesis, multi-track stem playback,
narration ducking, and PS1 compliance inspection.
"""

DEMO_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SoundForge AI — Background Music Engine for Video</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #0b0f19;
            --bg-surface: #121929;
            --bg-surface-elevated: #182238;
            --bg-surface-subtle: #0d1322;
            --border-subtle: #1e293b;
            --border-default: #23314d;
            --border-focus: #4f46e5;
            --primary: #4f46e5;
            --primary-hover: #4338ca;
            --primary-glow: rgba(79, 70, 229, 0.25);
            --accent-cyan: #06b6d4;
            --accent-green: #10b981;
            --accent-amber: #f59e0b;
            --accent-red: #ef4444;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-tertiary: #64748b;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg-base);
            color: var(--text-primary);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.5;
            padding: 24px;
            min-height: 100vh;
            overflow-x: hidden;
        }

        .app-container { max-width: 1360px; margin: 0 auto; }

        /* Header */
        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border-default);
            margin-bottom: 24px;
            flex-wrap: wrap;
            gap: 16px;
        }
        .brand-area { display: flex; align-items: center; gap: 14px; }
        .brand-mark {
            background: linear-gradient(135deg, var(--primary), var(--accent-cyan));
            width: 42px; height: 42px; border-radius: 10px;
            display: flex; align-items: center; justify-content: center;
            font-weight: 700; font-size: 19px; color: #fff;
            letter-spacing: -0.04em;
        }
        h1 { font-size: 20px; font-weight: 700; letter-spacing: -0.02em; }
        .tagline { font-size: 12px; color: var(--text-secondary); }
        .header-status-group { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
        .status-badge {
            padding: 5px 12px;
            border-radius: 16px;
            font-size: 11px;
            font-weight: 600;
            display: inline-flex; align-items: center; gap: 6px;
        }
        .status-badge-cleared {
            background: rgba(16, 185, 129, 0.12);
            color: var(--accent-green);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .status-badge-standard {
            background: rgba(6, 182, 212, 0.12);
            color: var(--accent-cyan);
            border: 1px solid rgba(6, 182, 212, 0.3);
        }

        /* Two-column layout */
        .workspace-grid {
            display: grid;
            grid-template-columns: 460px 1fr;
            gap: 24px;
            align-items: start;
        }
        @media (max-width: 1100px) { .workspace-grid { grid-template-columns: 1fr; } }

        /* Panel Cards */
        .panel {
            background: var(--bg-surface);
            border: 1px solid var(--border-default);
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-subtle);
        }
        .panel-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .panel-subtitle { font-size: 11px; color: var(--text-secondary); }

        /* Form elements */
        .field-group { margin-bottom: 16px; }
        .field-label {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 6px;
        }
        .field-hint { font-size: 11px; color: var(--text-tertiary); font-weight: 400; }
        textarea, input[type="text"], input[type="number"], select {
            width: 100%;
            background: var(--bg-surface-subtle);
            border: 1px solid var(--border-default);
            color: var(--text-primary);
            padding: 9px 12px;
            border-radius: 8px;
            font-size: 13px;
            font-family: inherit;
            transition: border-color 0.15s, box-shadow 0.15s;
        }
        textarea:focus, input[type="text"]:focus, input[type="number"]:focus, select:focus {
            outline: none;
            border-color: var(--border-focus);
            box-shadow: 0 0 0 2px var(--primary-glow);
        }

        /* Preset buttons */
        .presets-bar {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 8px;
        }
        .preset-chip {
            background: var(--bg-surface-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            cursor: pointer;
            transition: all 0.15s;
        }
        .preset-chip:hover {
            background: var(--border-default);
            color: var(--text-primary);
            border-color: var(--text-tertiary);
        }

        /* Sliders */
        .range-wrapper {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        input[type="range"] {
            flex: 1;
            accent-color: var(--primary);
            height: 5px;
            background: var(--border-default);
            border-radius: 3px;
            cursor: pointer;
        }
        .range-val {
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            font-weight: 600;
            color: var(--accent-cyan);
            min-width: 55px;
            text-align: right;
        }

        /* Section Timeline Editor */
        .section-editor-box {
            background: var(--bg-surface-subtle);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            padding: 12px;
            margin-top: 8px;
        }
        .section-row {
            display: grid;
            grid-template-columns: 80px 1fr 32px;
            gap: 8px;
            align-items: center;
            margin-bottom: 8px;
        }
        .btn-icon-danger {
            background: transparent;
            border: 1px solid var(--border-default);
            color: var(--accent-red);
            border-radius: 6px;
            height: 32px;
            cursor: pointer;
            display: flex; align-items: center; justify-content: center;
        }
        .btn-icon-danger:hover { background: rgba(239, 68, 68, 0.15); border-color: var(--accent-red); }

        /* Checkbox row */
        .checkbox-row {
            display: flex;
            align-items: center;
            gap: 18px;
            margin-top: 10px;
            flex-wrap: wrap;
        }
        .checkbox-label {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: var(--text-primary);
            cursor: pointer;
        }
        .checkbox-label input { accent-color: var(--primary); }

        /* Upload drag & drop zone */
        .dropzone {
            border: 1px dashed var(--border-default);
            border-radius: 8px;
            padding: 12px;
            text-align: center;
            background: var(--bg-surface-subtle);
            cursor: pointer;
            transition: border-color 0.15s, background-color 0.15s;
            margin-top: 6px;
        }
        .dropzone:hover { border-color: var(--primary); background: rgba(79, 70, 229, 0.05); }
        .dropzone-text { font-size: 11px; color: var(--text-secondary); }

        /* Action button */
        .btn-primary {
            width: 100%;
            background: var(--primary);
            color: #fff;
            border: none;
            padding: 12px 18px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: background 0.15s, transform 0.05s;
        }
        .btn-primary:hover:not(:disabled) { background: var(--primary-hover); }
        .btn-primary:active:not(:disabled) { transform: translateY(1px); }
        .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

        .btn-secondary {
            background: var(--bg-surface-elevated);
            border: 1px solid var(--border-default);
            color: var(--text-primary);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            text-decoration: none;
            transition: background 0.15s, border-color 0.15s;
        }
        .btn-secondary:hover { background: var(--border-default); border-color: var(--text-tertiary); }

        /* Live Progress Monitor Card */
        .progress-monitor {
            display: none;
            background: var(--bg-surface-elevated);
            border: 1px solid var(--border-default);
            border-radius: 10px;
            padding: 14px 16px;
            margin-top: 14px;
        }
        .progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            margin-bottom: 8px;
        }
        .progress-track {
            height: 6px;
            background: var(--bg-surface-subtle);
            border-radius: 3px;
            overflow: hidden;
            margin-bottom: 8px;
        }
        .progress-fill {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, var(--primary), var(--accent-cyan));
            transition: width 0.25s ease;
        }
        .progress-footer {
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: var(--text-tertiary);
            font-family: 'JetBrains Mono', monospace;
        }

        /* Failure & Alert Banner */
        .alert-card {
            display: none;
            border-radius: 10px;
            padding: 14px 16px;
            margin-bottom: 18px;
            font-size: 12px;
        }
        .alert-card-danger {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.35);
            color: #fca5a5;
        }
        .alert-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-weight: 600;
            margin-bottom: 4px;
        }

        /* Empty State */
        .empty-placeholder {
            background: var(--bg-surface);
            border: 1px dashed var(--border-default);
            border-radius: 14px;
            padding: 56px 24px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 480px;
        }
        .empty-icon {
            width: 52px; height: 52px; border-radius: 12px;
            background: var(--bg-surface-elevated);
            border: 1px solid var(--border-subtle);
            display: flex; align-items: center; justify-content: center;
            color: var(--accent-cyan);
            margin-bottom: 16px;
        }
        .empty-title { font-size: 16px; font-weight: 600; color: var(--text-primary); margin-bottom: 6px; }
        .empty-description { font-size: 12px; color: var(--text-secondary); max-width: 420px; line-height: 1.6; margin-bottom: 20px; }
        .pill-cluster { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; }
        .pill {
            background: var(--bg-surface-subtle);
            border: 1px solid var(--border-subtle);
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            color: var(--text-secondary);
            font-family: 'JetBrains Mono', monospace;
        }

        /* Output View */
        #activeResultsContainer { display: none; }

        /* Job Header Bar */
        .job-meta-bar {
            background: var(--bg-surface-elevated);
            border: 1px solid var(--border-default);
            border-radius: 10px;
            padding: 12px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
            flex-wrap: wrap;
            gap: 10px;
        }
        .job-meta-left { display: flex; align-items: center; gap: 10px; font-size: 12px; }
        .job-id-code {
            font-family: 'JetBrains Mono', monospace;
            background: var(--bg-surface-subtle);
            padding: 3px 8px;
            border-radius: 4px;
            border: 1px solid var(--border-subtle);
            color: var(--accent-cyan);
            font-size: 11px;
        }
        .pill-success {
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-green);
            border: 1px solid rgba(16, 185, 129, 0.3);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
        }

        /* Metrics Bar */
        .metrics-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(105px, 1fr));
            gap: 10px;
            margin-bottom: 18px;
        }
        .metric-tile {
            background: var(--bg-surface-subtle);
            border: 1px solid var(--border-default);
            border-radius: 8px;
            padding: 10px 12px;
            text-align: center;
        }
        .metric-label { font-size: 10px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
        .metric-data { font-size: 15px; font-weight: 700; color: var(--text-primary); font-family: 'JetBrains Mono', monospace; }

        /* Stems Multi-Track Mixer */
        .stem-mixer-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
            flex-wrap: wrap;
            gap: 8px;
        }
        .stem-mixer-controls { display: flex; align-items: center; gap: 8px; }
        .stem-channel {
            background: var(--bg-surface-subtle);
            border: 1px solid var(--border-default);
            border-radius: 10px;
            padding: 12px 14px;
            margin-bottom: 10px;
            display: grid;
            grid-template-columns: 140px 1fr 140px auto;
            gap: 12px;
            align-items: center;
        }
        @media (max-width: 820px) {
            .stem-channel { grid-template-columns: 1fr; gap: 8px; }
        }
        .channel-name { font-size: 13px; font-weight: 600; }
        .channel-gain { font-size: 11px; color: var(--text-tertiary); font-family: 'JetBrains Mono', monospace; }
        .channel-slider-row { display: flex; align-items: center; gap: 8px; }
        .channel-btns { display: flex; align-items: center; gap: 6px; }

        .btn-track {
            background: var(--bg-surface-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            font-size: 11px;
            font-weight: 600;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            min-width: 30px;
            text-align: center;
            transition: all 0.15s;
        }
        .btn-track:hover { border-color: var(--text-secondary); color: var(--text-primary); }
        .btn-track.active-solo { background: #ca8a04; color: #fff; border-color: #eab308; }
        .btn-track.active-mute { background: #b91c1c; color: #fff; border-color: #ef4444; }

        audio { width: 100%; height: 34px; outline: none; border-radius: 4px; }

        /* Manifest JSON viewer */
        pre {
            background: #080c14;
            border: 1px solid var(--border-default);
            border-radius: 8px;
            padding: 14px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: #38bdf8;
            max-height: 260px;
            overflow: auto;
            line-height: 1.5;
        }

        /* Isolated Previous Result Card */
        #previousResultCard {
            display: none;
            border: 1px dashed var(--border-default);
            opacity: 0.85;
            transition: opacity 0.2s;
        }
        #previousResultCard:hover { opacity: 1; }
    </style>
</head>
<body>
<div class="app-container">
    <header>
        <div class="brand-area">
            <div class="brand-mark">SF</div>
            <div>
                <h1>SoundForge AI</h1>
                <div class="tagline">Background Music Engine for Video • IncuBrix PS1 Creator Suite</div>
            </div>
        </div>
        <div class="header-status-group">
            <div class="status-badge status-badge-standard">EBU R128 (-16 LUFS) • 48 kHz</div>
            <div class="status-badge status-badge-cleared">100% Cleared DSP Stems</div>
        </div>
    </header>

    <div class="workspace-grid">
        <!-- Left: Generation Form -->
        <div>
            <!-- Main Controls Panel -->
            <div class="panel">
                <div class="panel-header">
                    <div>
                        <div class="panel-title">Music Parameters</div>
                        <div class="panel-subtitle">Configure audio synthesis pipeline</div>
                    </div>
                </div>

                <!-- Prompt Group -->
                <div class="field-group">
                    <div class="field-label">
                        <span>Musical Prompt & Description</span>
                        <span class="field-hint" id="charCount">0/1000</span>
                    </div>
                    <textarea id="promptInput" rows="3" placeholder="Describe mood, genre, instruments and video pacing..." oninput="updateCharCount()">Upbeat modern corporate tech tutorial with bright rhythm and uplifting acoustic feel</textarea>
                    
                    <div class="presets-bar">
                        <button class="preset-chip" type="button" onclick="applyPreset('Upbeat modern corporate tech tutorial with bright rhythm and uplifting acoustic feel', 12, 120, 'C_major', false)">Corporate Tech</button>
                        <button class="preset-chip" type="button" onclick="applyPreset('Chill lo-fi study beat with warm electric piano and subtle relaxed bassline', 16, 80, 'A_minor', true)">Lo-Fi Chill</button>
                        <button class="preset-chip" type="button" onclick="applyPreset('Cinematic dramatic build-up with driving bass and intense orchestral lead', 16, 95, 'D_minor', false)">Cinematic</button>
                        <button class="preset-chip" type="button" onclick="applyPreset('Retro synthwave 80s arcade highway drive with analog synths', 14, 122, 'F_major', true)">Synthwave</button>
                        <button class="preset-chip" type="button" onclick="applyPreset('Serene ambient drone with deep meditative texture', 20, 70, 'G_major', true)">Ambient</button>
                        <button class="preset-chip" type="button" onclick="applyPreset('Funky energetic pop groove with punchy bass and bright chords', 12, 115, 'C_major', false)">Funk Groove</button>
                    </div>
                </div>

                <!-- Duration Slider -->
                <div class="field-group">
                    <div class="field-label">
                        <span>Duration (Seconds)</span>
                        <span class="field-hint">Range: 5.0s to 300.0s</span>
                    </div>
                    <div class="range-wrapper">
                        <input type="range" id="durationSlider" min="5" max="300" value="12" step="1" oninput="document.getElementById('durationVal').innerText = this.value + '.0s'">
                        <span class="range-val" id="durationVal">12.0s</span>
                    </div>
                </div>

                <!-- Custom Sections (Optional Accordion) -->
                <div class="field-group">
                    <div class="field-label">
                        <span>Custom Musical Sections (Optional)</span>
                        <button class="preset-chip" type="button" onclick="toggleSectionEditor()">+ Add Timeline Section</button>
                    </div>
                    <div id="sectionEditorBox" class="section-editor-box" style="display: none;">
                        <div id="sectionRowsList"></div>
                        <button class="btn-secondary" type="button" style="width: 100%; justify-content: center; margin-top: 6px;" onclick="addSectionRow()">+ Add Row</button>
                    </div>
                </div>

                <!-- Tempo & Key -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;" class="field-group">
                    <div>
                        <div class="field-label"><span>Tempo (BPM)</span></div>
                        <div class="range-wrapper">
                            <input type="range" id="tempoSlider" min="0" max="200" value="0" step="1" oninput="document.getElementById('tempoVal').innerText = this.value == 0 ? 'Auto' : this.value">
                            <span class="range-val" id="tempoVal" style="min-width: 42px;">Auto</span>
                        </div>
                    </div>
                    <div>
                        <div class="field-label"><span>Musical Key</span></div>
                        <select id="keySelect">
                            <option value="">Auto-detected</option>
                            <option value="C_major">C Major (Bright / Clean)</option>
                            <option value="A_minor">A Minor (Melancholic / Lo-Fi)</option>
                            <option value="G_major">G Major (Uplifting)</option>
                            <option value="D_minor">D Minor (Cinematic / Tension)</option>
                            <option value="F_major">F Major (Warm / Optimistic)</option>
                            <option value="E_minor">E Minor (Introspective)</option>
                        </select>
                    </div>
                </div>

                <!-- Loudness & Audio Settings -->
                <div class="field-group">
                    <div class="field-label">
                        <span>Target Integrated Loudness</span>
                        <span class="field-hint">PS1 Default: -16.0 LUFS</span>
                    </div>
                    <div class="range-wrapper">
                        <input type="range" id="lufsSlider" min="-24" max="-8" value="-16" step="1" oninput="document.getElementById('lufsVal').innerText = this.value + '.0 LUFS'">
                        <span class="range-val" id="lufsVal">-16.0 LUFS</span>
                    </div>
                </div>

                <!-- Formats and Looping -->
                <div class="checkbox-row field-group">
                    <label class="checkbox-label">
                        <input type="checkbox" id="loopCheck">
                        <span>Seamless Loop Seam</span>
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" id="mp3Check" checked>
                        <span>Include MP3 (320kbps)</span>
                    </label>
                </div>

                <!-- Narration Ducking (Optional) -->
                <div class="field-group">
                    <div class="field-label">
                        <span>Narration Voiceover (Optional Ducking)</span>
                        <span class="field-hint">-14 dB Sidechain Attenuation</span>
                    </div>
                    <div style="display: flex; gap: 8px; margin-bottom: 6px;">
                        <input type="text" id="narrationUrlInput" placeholder="https://example.com/voice.wav or upload below">
                    </div>
                    <div class="dropzone" onclick="document.getElementById('narrationFileInput').click()">
                        <div class="dropzone-text" id="uploadStatusText">📁 Click to upload local voiceover (.wav, .mp3 max 50MB)</div>
                        <input type="file" id="narrationFileInput" accept=".wav,.mp3" style="display: none;" onchange="handleNarrationFileUpload(this)">
                    </div>
                </div>

                <!-- Advanced Settings (Collapsible) -->
                <div class="field-group">
                    <div class="field-label">
                        <span style="cursor: pointer;" onclick="toggleAdvancedSettings()">⚙️ Advanced Parameters ▾</span>
                    </div>
                    <div id="advancedBox" style="display: none; background: var(--bg-surface-subtle); padding: 12px; border-radius: 8px; border: 1px solid var(--border-subtle); margin-top: 6px;">
                        <div style="margin-bottom: 8px;">
                            <label style="font-size: 11px; color: var(--text-secondary);">Deterministic Seed</label>
                            <div style="display: flex; gap: 6px; margin-top: 4px;">
                                <input type="number" id="seedInput" placeholder="Random seed (e.g. 42)">
                                <button class="btn-secondary" type="button" onclick="document.getElementById('seedInput').value = Math.floor(Math.random() * 100000)">🎲</button>
                            </div>
                        </div>
                        <div>
                            <label style="font-size: 11px; color: var(--text-secondary);">Sample Rate</label>
                            <select id="sampleRateSelect" style="margin-top: 4px;">
                                <option value="48000" selected>48,000 Hz (IncuBrix Standard)</option>
                                <option value="44100">44,100 Hz (CD Audio)</option>
                                <option value="96000">96,000 Hz (Hi-Res)</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Submit Button -->
                <button class="btn-primary" id="generateBtn" type="button" onclick="startGenerationWorkflow()">
                    <span id="btnIcon">▶</span>
                    <span id="btnLabel">Generate Music</span>
                </button>

                <!-- In-Flight Progress Monitor -->
                <div class="progress-monitor" id="progressMonitor">
                    <div class="progress-header">
                        <span id="progressStage" style="font-weight: 500;">Enqueuing request...</span>
                        <span id="progressPct" style="font-weight: 600; color: var(--accent-cyan);">0%</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <div class="progress-footer">
                        <span id="progressJobId">Job: --</span>
                        <span id="progressElapsed">Elapsed: 0.0s</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Right: Results & Studio Monitor -->
        <div>
            <!-- Active Error Notification Card -->
            <div id="errorCard" class="alert-card alert-card-danger">
                <div class="alert-card-header">
                    <span id="errorTitle">Generation Error</span>
                    <button class="preset-chip" type="button" onclick="dismissError()">✕ Dismiss</button>
                </div>
                <div id="errorMessage" style="margin-bottom: 8px;">An unexpected error occurred.</div>
                <div id="retryActionRow" style="display: none;">
                    <button class="btn-secondary" type="button" onclick="retryLastRequest()">🔄 Retry Request</button>
                </div>
            </div>

            <!-- Empty State (Shown before any generation completes) -->
            <div class="empty-placeholder" id="emptyPlaceholder">
                <div class="empty-icon">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
                </div>
                <div class="empty-title">Studio Monitor Idle</div>
                <div class="empty-description">
                    Adjust the musical parameters on the left or select a preset, then click <strong>Generate Music</strong>.
                    SoundForge AI will synthesize a 48 kHz master mix, 4 separate instrument stems, and a full IncuBrix PS1 manifest.
                </div>
                <div class="pill-cluster">
                    <span class="pill">48 kHz 24-bit PCM</span>
                    <span class="pill">-16.0 LUFS EBU R128</span>
                    <span class="pill">≤ -1.0 dBTP Ceiling</span>
                    <span class="pill">4 Isolated Stems</span>
                    <span class="pill">Linear Summing Verification</span>
                </div>
            </div>

            <!-- Active Successful Results Container -->
            <div id="activeResultsContainer">
                <!-- Current Job Header Bar -->
                <div class="job-meta-bar">
                    <div class="job-meta-left">
                        <span style="color: var(--text-secondary);">Active Output:</span>
                        <span class="job-id-code" id="activeJobIdText">--</span>
                        <span class="pill-success" id="activeStatusPill">SUCCEEDED</span>
                    </div>
                    <div style="font-size: 11px; color: var(--text-tertiary);" id="activeTimestampText">Just now</div>
                </div>

                <!-- Metrics Grid -->
                <div class="metrics-row">
                    <div class="metric-tile">
                        <div class="metric-label">Duration</div>
                        <div class="metric-data" id="metricDuration">-</div>
                    </div>
                    <div class="metric-tile">
                        <div class="metric-label">Sample Rate</div>
                        <div class="metric-data" id="metricSampleRate">48 kHz</div>
                    </div>
                    <div class="metric-tile">
                        <div class="metric-label">Loudness</div>
                        <div class="metric-data" id="metricLoudness">-</div>
                    </div>
                    <div class="metric-tile">
                        <div class="metric-label">True Peak</div>
                        <div class="metric-data" id="metricPeak">-</div>
                    </div>
                    <div class="metric-tile">
                        <div class="metric-label">Recon Delta</div>
                        <div class="metric-data" id="metricRecon" style="color: var(--accent-green);">-</div>
                    </div>
                </div>

                <!-- Master Mix Player Panel -->
                <div class="panel">
                    <div class="panel-header">
                        <div>
                            <div class="panel-title">Master Mix</div>
                            <div class="panel-subtitle">Full stereo mixdown (48 kHz 24-bit PCM)</div>
                        </div>
                        <div id="masterDownloadsGroup" style="display: flex; gap: 8px; flex-wrap: wrap;"></div>
                    </div>
                    <div style="margin-top: 8px;">
                        <audio id="audioMasterMix" controls preload="metadata"></audio>
                    </div>
                </div>

                <!-- Multi-Track Stems Studio -->
                <div class="panel">
                    <div class="panel-header">
                        <div>
                            <div class="panel-title">Isolated Instrument Stems</div>
                            <div class="panel-subtitle">Zero frequency-splitting • Independent synthesis</div>
                        </div>
                        <div class="stem-mixer-controls">
                            <button class="btn-secondary" type="button" id="btnSyncPlayAll" onclick="togglePlayAllStems()">▶ Play All Stems</button>
                            <button class="btn-secondary" type="button" onclick="resetAllStemMixer()">Reset Mixer</button>
                        </div>
                    </div>

                    <!-- Channel 1: Drums -->
                    <div class="stem-channel" id="channelDrums">
                        <div>
                            <div class="channel-name">Drums & Perc</div>
                            <div class="channel-gain" id="gainWeightDrums">Weight: 0.85</div>
                        </div>
                        <audio id="audioStemDrums" controls preload="metadata"></audio>
                        <div class="channel-slider-row">
                            <span style="font-size: 10px; color: var(--text-tertiary);">VOL</span>
                            <input type="range" min="0" max="1" step="0.05" value="1" oninput="setStemVolume('drums', this.value)">
                        </div>
                        <div class="channel-btns">
                            <button class="btn-track" type="button" id="soloDrums" onclick="toggleStemSolo('drums')">S</button>
                            <button class="btn-track" type="button" id="muteDrums" onclick="toggleStemMute('drums')">M</button>
                            <a class="btn-secondary" id="dlStemDrums" href="#" download="stem_drums.wav">WAV</a>
                        </div>
                    </div>

                    <!-- Channel 2: Bass -->
                    <div class="stem-channel" id="channelBass">
                        <div>
                            <div class="channel-name">Bassline</div>
                            <div class="channel-gain" id="gainWeightBass">Weight: 0.80</div>
                        </div>
                        <audio id="audioStemBass" controls preload="metadata"></audio>
                        <div class="channel-slider-row">
                            <span style="font-size: 10px; color: var(--text-tertiary);">VOL</span>
                            <input type="range" min="0" max="1" step="0.05" value="1" oninput="setStemVolume('bass', this.value)">
                        </div>
                        <div class="channel-btns">
                            <button class="btn-track" type="button" id="soloBass" onclick="toggleStemSolo('bass')">S</button>
                            <button class="btn-track" type="button" id="muteBass" onclick="toggleStemMute('bass')">M</button>
                            <a class="btn-secondary" id="dlStemBass" href="#" download="stem_bass.wav">WAV</a>
                        </div>
                    </div>

                    <!-- Channel 3: Chords -->
                    <div class="stem-channel" id="channelChords">
                        <div>
                            <div class="channel-name">Chords & Harmony</div>
                            <div class="channel-gain" id="gainWeightChords">Weight: 0.70</div>
                        </div>
                        <audio id="audioStemChords" controls preload="metadata"></audio>
                        <div class="channel-slider-row">
                            <span style="font-size: 10px; color: var(--text-tertiary);">VOL</span>
                            <input type="range" min="0" max="1" step="0.05" value="1" oninput="setStemVolume('chords', this.value)">
                        </div>
                        <div class="channel-btns">
                            <button class="btn-track" type="button" id="soloChords" onclick="toggleStemSolo('chords')">S</button>
                            <button class="btn-track" type="button" id="muteChords" onclick="toggleStemMute('chords')">M</button>
                            <a class="btn-secondary" id="dlStemChords" href="#" download="stem_chords.wav">WAV</a>
                        </div>
                    </div>

                    <!-- Channel 4: Melody -->
                    <div class="stem-channel" id="channelMelody">
                        <div>
                            <div class="channel-name">Lead Melody</div>
                            <div class="channel-gain" id="gainWeightMelody">Weight: 0.75</div>
                        </div>
                        <audio id="audioStemMelody" controls preload="metadata"></audio>
                        <div class="channel-slider-row">
                            <span style="font-size: 10px; color: var(--text-tertiary);">VOL</span>
                            <input type="range" min="0" max="1" step="0.05" value="1" oninput="setStemVolume('melody', this.value)">
                        </div>
                        <div class="channel-btns">
                            <button class="btn-track" type="button" id="soloMelody" onclick="toggleStemSolo('melody')">S</button>
                            <button class="btn-track" type="button" id="muteMelody" onclick="toggleStemMute('melody')">M</button>
                            <a class="btn-secondary" id="dlStemMelody" href="#" download="stem_melody.wav">WAV</a>
                        </div>
                    </div>
                </div>

                <!-- Provenance Manifest Panel -->
                <div class="panel">
                    <div class="panel-header">
                        <div>
                            <div class="panel-title">PS1 Provenance Manifest</div>
                            <div class="panel-subtitle">Metadata, beat grid, loudness and licensing compliance</div>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn-secondary" type="button" onclick="copyManifestJson()">Copy JSON</button>
                            <a class="btn-secondary" id="dlManifestBtn" href="#" download="manifest.json">Download JSON</a>
                        </div>
                    </div>
                    <pre id="manifestCodeViewer"></pre>
                </div>
            </div>

            <!-- Isolated Previous Successful Output (Shown if user retries or generates again) -->
            <div class="panel" id="previousResultCard">
                <div class="panel-header">
                    <div>
                        <div class="panel-title" style="color: var(--text-secondary);">
                            <span>📦 Previous Successful Output</span>
                            <span class="status-badge" style="background: rgba(148, 163, 184, 0.15); color: var(--text-secondary);" id="prevJobPill">--</span>
                        </div>
                        <div class="panel-subtitle">Retained from earlier successful run for comparison</div>
                    </div>
                    <button class="btn-secondary" type="button" onclick="togglePreviousResultView()" id="btnTogglePrev">Show Previous Audio ▾</button>
                </div>
                <div id="prevResultContent" style="display: none; padding-top: 8px;">
                    <div style="font-size: 12px; margin-bottom: 8px; color: var(--text-secondary);" id="prevInfoSummary"></div>
                    <audio id="audioPrevMix" controls preload="metadata" style="margin-bottom: 8px;"></audio>
                    <div id="prevDownloadLinks" style="display: flex; gap: 8px; flex-wrap: wrap;"></div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
// =========================================================================
// SoundForge AI — Professional Client State Machine & Audio Engine
// =========================================================================

const AppState = {
    IDLE: 'IDLE',
    SUBMITTING: 'SUBMITTING',
    RUNNING: 'RUNNING',
    SUCCEEDED: 'SUCCEEDED',
    FAILED: 'FAILED',
    TIMED_OUT: 'TIMED_OUT'
};

const session = {
    seq: 0,
    state: AppState.IDLE,
    activeJobId: null,
    pollTimer: null,
    startTime: null,
    lastPayload: null,
    currentResult: null,
    previousResult: null,
    error: null
};

// Stem Mixer State
const stemMixer = {
    isPlayingAll: false,
    stems: {
        drums: { solo: false, mute: false, vol: 1.0 },
        bass: { solo: false, mute: false, vol: 1.0 },
        chords: { solo: false, mute: false, vol: 1.0 },
        melody: { solo: false, mute: false, vol: 1.0 }
    }
};

function resolveArtifactUrl(url) {
    if (!url) return '';
    if (url.startsWith('http://') || url.startsWith('https://')) return url;
    const cleanPath = url.startsWith('/') ? url : '/' + url;
    return window.location.origin + cleanPath;
}

function updateCharCount() {
    const val = document.getElementById('promptInput').value;
    document.getElementById('charCount').innerText = `${val.length}/1000`;
}
updateCharCount();

function applyPreset(prompt, dur, bpm, key, loop) {
    document.getElementById('promptInput').value = prompt;
    updateCharCount();
    document.getElementById('durationSlider').value = dur;
    document.getElementById('durationVal').innerText = dur + '.0s';
    document.getElementById('tempoSlider').value = bpm;
    document.getElementById('tempoVal').innerText = bpm === 0 ? 'Auto' : bpm;
    document.getElementById('keySelect').value = key;
    document.getElementById('loopCheck').checked = !!loop;
}

// Custom Section Timeline
let customSections = [];
function toggleSectionEditor() {
    const box = document.getElementById('sectionEditorBox');
    if (box.style.display === 'none') {
        box.style.display = 'block';
        if (customSections.length === 0) addSectionRow();
    } else {
        box.style.display = 'none';
    }
}

function renderSectionRows() {
    const list = document.getElementById('sectionRowsList');
    list.innerHTML = '';
    customSections.forEach((sec, idx) => {
        const row = document.createElement('div');
        row.className = 'section-row';
        row.innerHTML = `
            <input type="number" min="0" max="300" step="0.5" value="${sec.start_s}" placeholder="Start (s)" onchange="updateSectionData(${idx}, 'start_s', this.value)">
            <select onchange="updateSectionData(${idx}, 'mood', this.value)">
                <option value="intro" ${sec.mood==='intro'?'selected':''}>Intro</option>
                <option value="verse" ${sec.mood==='verse'?'selected':''}>Verse</option>
                <option value="chorus" ${sec.mood==='chorus'?'selected':''}>Chorus</option>
                <option value="build" ${sec.mood==='build'?'selected':''}>Build</option>
                <option value="climax" ${sec.mood==='climax'?'selected':''}>Climax</option>
                <option value="outro" ${sec.mood==='outro'?'selected':''}>Outro</option>
            </select>
            <button class="btn-icon-danger" type="button" onclick="removeSectionRow(${idx})">✕</button>
        `;
        list.appendChild(row);
    });
}

function addSectionRow() {
    const lastStart = customSections.length > 0 ? customSections[customSections.length - 1].start_s + 4.0 : 0.0;
    customSections.push({ start_s: lastStart, mood: 'verse' });
    renderSectionRows();
}

function removeSectionRow(idx) {
    customSections.splice(idx, 1);
    renderSectionRows();
}

function updateSectionData(idx, key, val) {
    if (key === 'start_s') customSections[idx].start_s = parseFloat(val) || 0.0;
    else customSections[idx].mood = val;
}

function toggleAdvancedSettings() {
    const box = document.getElementById('advancedBox');
    box.style.display = box.style.display === 'none' ? 'block' : 'none';
}

// Narration Audio Upload
async function handleNarrationFileUpload(input) {
    if (!input.files || input.files.length === 0) return;
    const file = input.files[0];
    const statusText = document.getElementById('uploadStatusText');
    statusText.innerText = `⏳ Uploading ${file.name}...`;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const resp = await fetch('/api/v1/narration/upload', {
            method: 'POST',
            body: formData
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || err.error?.message || `HTTP ${resp.status}`);
        }
        const data = await resp.json();
        document.getElementById('narrationUrlInput').value = data.narration_url;
        statusText.innerText = `✅ Uploaded: ${file.name} (${data.duration_s}s, ${data.sample_rate}Hz)`;
    } catch (e) {
        statusText.innerText = `❌ Upload failed: ${e.message}`;
    }
}

// UI State Updates
function updateUiState(newState) {
    session.state = newState;
    const btn = document.getElementById('generateBtn');
    const btnLabel = document.getElementById('btnLabel');
    const pMonitor = document.getElementById('progressMonitor');

    if (newState === AppState.SUBMITTING || newState === AppState.RUNNING) {
        btn.disabled = true;
        btnLabel.innerText = 'Generating...';
        pMonitor.style.display = 'block';
    } else {
        btn.disabled = false;
        btnLabel.innerText = 'Generate Music';
    }
}

function dismissError() {
    document.getElementById('errorCard').style.display = 'none';
}

function displayError(code, message, retryable = false) {
    const card = document.getElementById('errorCard');
    document.getElementById('errorTitle').innerText = `Generation Failed (${code || 'ERROR'})`;
    document.getElementById('errorMessage').innerText = message || 'An unknown error occurred during generation.';
    document.getElementById('retryActionRow').style.display = retryable ? 'block' : 'none';
    card.style.display = 'block';
}

// =========================================================================
// Generation Workflow & Polling
// =========================================================================

async function startGenerationWorkflow() {
    dismissError();
    session.seq++;
    const currentSeq = session.seq;

    if (session.pollTimer) {
        clearInterval(session.pollTimer);
        session.pollTimer = null;
    }

    // Isolate previous results if present
    if (session.currentResult) {
        archiveCurrentToPrevious();
    }

    // Hide active results container while new job generates
    document.getElementById('activeResultsContainer').style.display = 'none';

    // Build payload
    const promptVal = document.getElementById('promptInput').value.trim();
    if (!promptVal) {
        displayError('VALIDATION_ERROR', 'Prompt is required. Please enter a musical description.');
        return;
    }

    const durVal = parseFloat(document.getElementById('durationSlider').value);
    const tempoVal = parseFloat(document.getElementById('tempoSlider').value);
    const keyVal = document.getElementById('keySelect').value;
    const lufsVal = parseFloat(document.getElementById('lufsSlider').value);
    const loopVal = document.getElementById('loopCheck').checked;
    const mp3Val = document.getElementById('mp3Check').checked;
    const narrVal = document.getElementById('narrationUrlInput').value.trim();
    const seedVal = parseInt(document.getElementById('seedInput').value, 10);
    const srVal = parseInt(document.getElementById('sampleRateSelect').value, 10);

    const formats = ['wav'];
    if (mp3Val) formats.push('mp3');

    const payload = {
        prompt: promptVal,
        duration_s: durVal,
        duration: durVal,
        tempo_bpm: tempoVal > 0 ? tempoVal : undefined,
        tempo: tempoVal > 0 ? tempoVal : undefined,
        key: keyVal || undefined,
        loopable: loopVal,
        loopability: loopVal,
        target_loudness: lufsVal,
        output_formats: formats,
        sample_rate: srVal || 48000
    };

    if (narrVal) payload.narration_url = narrVal;
    if (!isNaN(seedVal)) payload.seed = seedVal;
    if (customSections.length > 0) {
        payload.sections = customSections.map(s => ({ start_s: s.start_s, mood: s.mood }));
    }

    session.lastPayload = payload;
    updateUiState(AppState.SUBMITTING);

    const pFill = document.getElementById('progressFill');
    const pStage = document.getElementById('progressStage');
    const pPct = document.getElementById('progressPct');
    const pJobId = document.getElementById('progressJobId');
    const pElapsed = document.getElementById('progressElapsed');

    pFill.style.width = '5%';
    pStage.innerText = 'Enqueuing job...';
    pPct.innerText = '5%';
    pJobId.innerText = 'Job: Submitting';
    pElapsed.innerText = 'Elapsed: 0.0s';

    try {
        const resp = await fetch('/api/v1/music/jobs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (currentSeq !== session.seq) return; // Stale check

        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            const errCode = err.error?.code || 'VALIDATION_ERROR';
            const errMsg = err.error?.message || err.detail || `Server returned HTTP ${resp.status}`;
            const retryable = err.error?.retryable || resp.status >= 500;
            updateUiState(AppState.FAILED);
            document.getElementById('progressMonitor').style.display = 'none';
            displayError(errCode, errMsg, retryable);
            return;
        }

        const data = await resp.json();
        const jobId = data.job_id;
        session.activeJobId = jobId;
        pJobId.innerText = `Job: ${jobId.substring(0, 8)}...`;
        updateUiState(AppState.RUNNING);
        pollJobStatus(jobId, currentSeq);

    } catch (e) {
        if (currentSeq !== session.seq) return;
        updateUiState(AppState.FAILED);
        document.getElementById('progressMonitor').style.display = 'none';
        displayError('NETWORK_ERROR', `Network connection failed: ${e.message}`, true);
    }
}

function pollJobStatus(jobId, seqId) {
    session.startTime = Date.now();
    let consecutiveErrors = 0;

    session.pollTimer = setInterval(async () => {
        if (seqId !== session.seq) {
            clearInterval(session.pollTimer);
            return;
        }

        const elapsedSec = ((Date.now() - session.startTime) / 1000).toFixed(1);
        document.getElementById('progressElapsed').innerText = `Elapsed: ${elapsedSec}s`;

        // 300s timeout guard
        if (Date.now() - session.startTime > 300000) {
            clearInterval(session.pollTimer);
            updateUiState(AppState.TIMED_OUT);
            document.getElementById('progressMonitor').style.display = 'none';
            displayError('TIMEOUT', 'Job synthesis timed out after 300 seconds. Check server logs.', true);
            return;
        }

        try {
            const resp = await fetch(`/api/v1/music/jobs/${jobId}`);
            if (seqId !== session.seq) return;

            if (!resp.ok) {
                consecutiveErrors++;
                if (consecutiveErrors >= 5) {
                    clearInterval(session.pollTimer);
                    updateUiState(AppState.FAILED);
                    document.getElementById('progressMonitor').style.display = 'none';
                    displayError('POLLING_ERROR', `Failed to poll job status: HTTP ${resp.status}`, true);
                }
                return;
            }

            consecutiveErrors = 0;
            const data = await resp.json();
            if (seqId !== session.seq) return;

            const pFill = document.getElementById('progressFill');
            const pStage = document.getElementById('progressStage');
            const pPct = document.getElementById('progressPct');

            const pct = Math.max(5, Math.min(100, Math.round((data.progress || 0) * 100)));
            pFill.style.width = pct + '%';
            pPct.innerText = pct + '%';
            pStage.innerText = data.current_stage || data.status;

            if (data.status === 'succeeded' || data.status === 'completed') {
                clearInterval(session.pollTimer);
                pFill.style.width = '100%';
                pPct.innerText = '100%';
                pStage.innerText = 'Generation complete!';
                updateUiState(AppState.SUCCEEDED);
                session.currentResult = data;
                renderActiveResults(data);
            } else if (data.status === 'failed') {
                clearInterval(session.pollTimer);
                updateUiState(AppState.FAILED);
                document.getElementById('progressMonitor').style.display = 'none';
                displayError('SYNTHESIS_FAILED', data.error || 'Audio synthesis pipeline failed.', true);
            }
        } catch (e) {
            if (seqId !== session.seq) return;
            consecutiveErrors++;
            if (consecutiveErrors >= 5) {
                clearInterval(session.pollTimer);
                updateUiState(AppState.FAILED);
                document.getElementById('progressMonitor').style.display = 'none';
                displayError('NETWORK_ERROR', `Polling connection lost: ${e.message}`, true);
            }
        }
    }, 600);
}

function retryLastRequest() {
    dismissError();
    startGenerationWorkflow();
}

// Archive current result to isolated previous card
function archiveCurrentToPrevious() {
    if (!session.currentResult) return;
    session.previousResult = session.currentResult;
    const res = session.previousResult;
    const art = res.artifacts || {};

    const prevCard = document.getElementById('previousResultCard');
    document.getElementById('prevJobPill').innerText = res.job_id ? res.job_id.substring(0, 8) + '...' : '--';
    document.getElementById('prevInfoSummary').innerText = `Created: ${res.completed_at || 'earlier run'} • Master Mix & Stems preserved below.`;

    const prevAudio = document.getElementById('audioPrevMix');
    if (art.mix_wav) prevAudio.src = resolveArtifactUrl(art.mix_wav);

    const prevDl = document.getElementById('prevDownloadLinks');
    let html = '';
    if (art.mix_wav) html += `<a class="btn-secondary" href="${resolveArtifactUrl(art.mix_wav)}" download="prev_mix.wav">WAV</a>`;
    if (art.mix_mp3) html += `<a class="btn-secondary" href="${resolveArtifactUrl(art.mix_mp3)}" download="prev_mix.mp3">MP3</a>`;
    if (art.manifest_json) html += `<a class="btn-secondary" href="${resolveArtifactUrl(art.manifest_json)}" target="_blank" download="prev_manifest.json">Manifest</a>`;
    prevDl.innerHTML = html;

    prevCard.style.display = 'block';
}

function togglePreviousResultView() {
    const box = document.getElementById('prevResultContent');
    const btn = document.getElementById('btnTogglePrev');
    if (box.style.display === 'none') {
        box.style.display = 'block';
        btn.innerText = 'Hide Previous Audio ▴';
    } else {
        box.style.display = 'none';
        btn.innerText = 'Show Previous Audio ▾';
    }
}

// Render active successful results
function renderActiveResults(data) {
    document.getElementById('emptyPlaceholder').style.display = 'none';
    const container = document.getElementById('activeResultsContainer');
    container.style.display = 'block';

    const art = data.artifacts || {};
    const man = data.manifest || {};
    const metrics = man.audio_metrics || {};
    const recon = man.reconstruction_verification || {};

    // Header Meta
    document.getElementById('activeJobIdText').innerText = data.job_id || '--';
    document.getElementById('activeStatusPill').innerText = (data.status || 'SUCCEEDED').toUpperCase();
    document.getElementById('activeTimestampText').innerText = data.completed_at ? new Date(data.completed_at).toLocaleTimeString() : 'Ready';

    // Metrics Row
    const dur = metrics.actual_duration_seconds != null ? metrics.actual_duration_seconds.toFixed(2) + 's' : '--';
    const sr = metrics.sample_rate_hz ? (metrics.sample_rate_hz / 1000) + ' kHz' : '48 kHz';
    const lufs = metrics.measured_loudness_lufs != null ? metrics.measured_loudness_lufs.toFixed(1) + ' LUFS' : '--';
    const peak = metrics.true_peak_dbtp != null ? metrics.true_peak_dbtp.toFixed(1) + ' dBTP' : '--';

    let reconStr = '0.0';
    if (recon.max_reconstruction_error != null) {
        reconStr = recon.max_reconstruction_error < 0.0001
            ? recon.max_reconstruction_error.toExponential(2)
            : recon.max_reconstruction_error.toFixed(4);
    }

    document.getElementById('metricDuration').innerText = dur;
    document.getElementById('metricSampleRate').innerText = sr;
    document.getElementById('metricLoudness').innerText = lufs;
    document.getElementById('metricPeak').innerText = peak;
    document.getElementById('metricRecon').innerText = reconStr;

    // Master Player & Downloads
    const masterAudio = document.getElementById('audioMasterMix');
    if (art.mix_wav) {
        masterAudio.src = resolveArtifactUrl(art.mix_wav);
        masterAudio.load();
    }

    const dlGroup = document.getElementById('masterDownloadsGroup');
    let dlHtml = '';
    if (art.mix_wav) {
        dlHtml += `<a class="btn-secondary" href="${resolveArtifactUrl(art.mix_wav)}" download="mix.wav">Download WAV</a>`;
    }
    if (art.mix_mp3) {
        dlHtml += `<a class="btn-secondary" href="${resolveArtifactUrl(art.mix_mp3)}" download="mix.mp3">Download MP3</a>`;
    }
    if (art.mix_ducked_wav || art.ducked_mix_wav) {
        const ducked = resolveArtifactUrl(art.mix_ducked_wav || art.ducked_mix_wav);
        dlHtml += `<a class="btn-secondary" href="${ducked}" download="ducked_mix.wav">Ducked Mix</a>`;
    }
    dlGroup.innerHTML = dlHtml;

    // Stems Channels
    const stemWeights = man.stem_gains || {};
    const stemKeys = [
        { id: 'Drums', key: 'stem_drums', defaultG: '0.85' },
        { id: 'Bass', key: 'stem_bass', defaultG: '0.80' },
        { id: 'Chords', key: 'stem_chords', defaultG: '0.70' },
        { id: 'Melody', key: 'stem_melody', defaultG: '0.75' }
    ];

    stemKeys.forEach(item => {
        const audioEl = document.getElementById('audioStem' + item.id);
        const dlEl = document.getElementById('dlStem' + item.id);
        const gainEl = document.getElementById('gainWeight' + item.id);

        const stemUrl = resolveArtifactUrl(art[item.key]);
        if (audioEl && stemUrl) {
            audioEl.src = stemUrl;
            audioEl.load();
        }
        if (dlEl && stemUrl) {
            dlEl.href = stemUrl;
            dlEl.download = `${item.key}.wav`;
        }
        if (gainEl) {
            const rawG = stemWeights[item.key.replace('stem_', '')] ?? item.defaultG;
            gainEl.innerText = `Weight: ${rawG}`;
        }
    });

    // Reset stem mixer controls
    resetAllStemMixer();

    // Manifest Viewer
    const mfViewer = document.getElementById('manifestCodeViewer');
    mfViewer.innerText = JSON.stringify(man, null, 2);

    const dlMfBtn = document.getElementById('dlManifestBtn');
    if (dlMfBtn && (art.manifest_json || art.music_manifest_json)) {
        dlMfBtn.href = resolveArtifactUrl(art.manifest_json || art.music_manifest_json);
    }
}

// Multi-Track Stem Mixer In-Browser Controls
function setStemVolume(stemName, val) {
    const audio = getStemAudioElement(stemName);
    if (audio) {
        stemMixer.stems[stemName].vol = parseFloat(val);
        if (!stemMixer.stems[stemName].mute) {
            audio.volume = parseFloat(val);
        }
    }
}

function toggleStemMute(stemName) {
    const audio = getStemAudioElement(stemName);
    const btn = document.getElementById('mute' + capitalize(stemName));
    if (!audio || !btn) return;

    const isMuted = !stemMixer.stems[stemName].mute;
    stemMixer.stems[stemName].mute = isMuted;

    if (isMuted) {
        audio.volume = 0;
        btn.classList.add('active-mute');
    } else {
        audio.volume = stemMixer.stems[stemName].vol;
        btn.classList.remove('active-mute');
    }
}

function toggleStemSolo(stemName) {
    const btn = document.getElementById('solo' + capitalize(stemName));
    const currentlySolo = stemMixer.stems[stemName].solo;
    const newSolo = !currentlySolo;

    // Reset all solos
    Object.keys(stemMixer.stems).forEach(k => {
        stemMixer.stems[k].solo = false;
        const b = document.getElementById('solo' + capitalize(k));
        if (b) b.classList.remove('active-solo');
    });

    if (newSolo) {
        stemMixer.stems[stemName].solo = true;
        if (btn) btn.classList.add('active-solo');

        // Mute other stems, unmute soloed
        Object.keys(stemMixer.stems).forEach(k => {
            const aud = getStemAudioElement(k);
            if (aud) {
                if (k === stemName) {
                    aud.volume = stemMixer.stems[k].vol;
                } else {
                    aud.volume = 0;
                }
            }
        });
    } else {
        // Restore volume per mute states
        Object.keys(stemMixer.stems).forEach(k => {
            const aud = getStemAudioElement(k);
            if (aud) {
                aud.volume = stemMixer.stems[k].mute ? 0 : stemMixer.stems[k].vol;
            }
        });
    }
}

function togglePlayAllStems() {
    const btn = document.getElementById('btnSyncPlayAll');
    const stemNames = ['drums', 'bass', 'chords', 'melody'];

    if (!stemMixer.isPlayingAll) {
        // Sync time to 0 and play
        stemNames.forEach(k => {
            const aud = getStemAudioElement(k);
            if (aud) {
                aud.currentTime = 0;
                aud.play().catch(() => {});
            }
        });
        stemMixer.isPlayingAll = true;
        btn.innerText = '⏸ Pause Stems';
    } else {
        stemNames.forEach(k => {
            const aud = getStemAudioElement(k);
            if (aud) aud.pause();
        });
        stemMixer.isPlayingAll = false;
        btn.innerText = '▶ Play All Stems';
    }
}

function resetAllStemMixer() {
    const stemNames = ['drums', 'bass', 'chords', 'melody'];
    stemMixer.isPlayingAll = false;
    document.getElementById('btnSyncPlayAll').innerText = '▶ Play All Stems';

    stemNames.forEach(k => {
        stemMixer.stems[k].solo = false;
        stemMixer.stems[k].mute = false;
        stemMixer.stems[k].vol = 1.0;

        const aud = getStemAudioElement(k);
        if (aud) {
            aud.pause();
            aud.currentTime = 0;
            aud.volume = 1.0;
        }

        const bSolo = document.getElementById('solo' + capitalize(k));
        const bMute = document.getElementById('mute' + capitalize(k));
        if (bSolo) bSolo.classList.remove('active-solo');
        if (bMute) bMute.classList.remove('active-mute');
    });
}

function getStemAudioElement(name) {
    return document.getElementById('audioStem' + capitalize(name));
}

function capitalize(s) {
    return s.charAt(0).toUpperCase() + s.slice(1);
}

function copyManifestJson() {
    const text = document.getElementById('manifestCodeViewer').innerText;
    navigator.clipboard.writeText(text).then(() => {
        alert('PS1 Manifest JSON copied to clipboard!');
    }).catch(err => {
        console.error('Clipboard copy failed:', err);
    });
}
</script>
</body>
</html>
"""
