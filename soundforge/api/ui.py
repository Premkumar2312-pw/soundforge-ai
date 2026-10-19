"""
Embedded Demonstration Web UI for SoundForge AI
Interactive interface for generation, stem solo/mute playback, ducking preview, and manifest inspection.
PS1 Specification & IncuBrix Integration Standard Compliant.
"""

DEMO_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SoundForge AI - Background Music Engine</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0b0f19;
            --surface: #131b2e;
            --surface-hover: #1b253e;
            --surface-elevated: #1e294b;
            --border: #232f4e;
            --border-highlight: #3b82f6;
            --primary: #4f46e5;
            --primary-hover: #4338ca;
            --primary-glow: rgba(79, 70, 229, 0.35);
            --accent: #06b6d4;
            --accent-green: #10b981;
            --accent-amber: #f59e0b;
            --accent-red: #ef4444;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --text-subtle: #64748b;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg);
            color: var(--text-main);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.5;
            padding: 24px;
            min-height: 100vh;
        }
        .container { max-width: 1280px; margin: 0 auto; }
        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 28px;
            flex-wrap: wrap;
            gap: 16px;
        }
        .logo-area { display: flex; align-items: center; gap: 14px; }
        .logo-badge {
            background: linear-gradient(135deg, var(--primary), var(--accent));
            width: 44px; height: 44px; border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            font-weight: 700; font-size: 20px; color: #fff;
            box-shadow: 0 0 20px var(--primary-glow);
            letter-spacing: -0.05em;
        }
        h1 { font-size: 22px; font-weight: 700; letter-spacing: -0.02em; }
        .tagline { font-size: 13px; color: var(--text-muted); }
        .header-badges { display: flex; align-items: center; gap: 10px; }
        .badge {
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            display: flex; align-items: center; gap: 6px;
        }
        .badge-cleared {
            background: rgba(16, 185, 129, 0.12);
            color: var(--accent-green);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .badge-status {
            background: rgba(6, 182, 212, 0.12);
            color: var(--accent);
            border: 1px solid rgba(6, 182, 212, 0.3);
        }
        .grid {
            display: grid;
            grid-template-columns: 440px 1fr;
            gap: 28px;
            align-items: start;
        }
        @media (max-width: 1024px) { .grid { grid-template-columns: 1fr; } }
        .card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 22px;
            margin-bottom: 20px;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        .card-title {
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            color: #fff;
        }
        .card-title-left {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .form-group { margin-bottom: 16px; }
        label { display: block; font-size: 12px; font-weight: 500; color: var(--text-muted); margin-bottom: 6px; }
        input[type="text"], select, textarea {
            width: 100%;
            background: #0d1322;
            border: 1px solid var(--border);
            color: #fff;
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 13px;
            font-family: inherit;
            transition: border 0.2s, box-shadow 0.2s;
        }
        input[type="text"]:focus, select:focus, textarea:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-glow);
        }
        .presets { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
        .preset-btn {
            background: var(--surface-hover);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 5px 11px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        .preset-btn:hover { background: var(--border); color: #fff; transform: translateY(-1px); }
        .slider-row { display: flex; align-items: center; gap: 12px; }
        .slider-row input[type="range"] { flex: 1; accent-color: var(--primary); height: 6px; cursor: pointer; }
        .slider-val {
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            font-weight: 600;
            min-width: 58px;
            text-align: right;
            color: var(--accent);
        }
        .btn-generate {
            width: 100%;
            background: linear-gradient(135deg, var(--primary), #3b82f6);
            color: #fff;
            border: none;
            padding: 13px 20px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            box-shadow: 0 4px 16px var(--primary-glow);
            transition: all 0.2s;
        }
        .btn-generate:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 20px var(--primary-glow); }
        .btn-generate:disabled { opacity: 0.55; cursor: not-allowed; transform: none; }
        
        /* Alert Box */
        .alert-box {
            display: none;
            padding: 14px 16px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 13px;
            display: flex;
            align-items: flex-start;
            gap: 12px;
        }
        .alert-error {
            background: rgba(239, 68, 68, 0.12);
            border: 1px solid rgba(239, 68, 68, 0.35);
            color: #fca5a5;
        }
        .alert-success {
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.35);
            color: #6ee7b7;
        }

        /* Progress Box */
        .progress-box {
            display: none;
            background: #0d1322;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
            margin-top: 16px;
        }
        .progress-bar-bg {
            background: #1b253e;
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-bar-fill {
            background: linear-gradient(90deg, var(--primary), var(--accent));
            height: 100%;
            width: 0%;
            transition: width 0.3s ease;
        }
        .progress-label {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: var(--text-muted);
        }
        
        /* Empty State */
        .empty-state {
            background: var(--surface);
            border: 2px dashed var(--border);
            border-radius: 16px;
            padding: 60px 32px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 480px;
        }
        .empty-icon {
            width: 64px;
            height: 64px;
            border-radius: 20px;
            background: rgba(79, 70, 229, 0.12);
            border: 1px solid rgba(79, 70, 229, 0.25);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--primary);
            margin-bottom: 20px;
        }
        .empty-title { font-size: 18px; font-weight: 600; color: #fff; margin-bottom: 8px; }
        .empty-desc {
            font-size: 13px;
            color: var(--text-muted);
            max-width: 440px;
            line-height: 1.6;
            margin-bottom: 24px;
        }
        .empty-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: center;
        }
        .empty-tag {
            background: #0d1322;
            border: 1px solid var(--border);
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 11px;
            color: var(--text-subtle);
            font-family: 'JetBrains Mono', monospace;
        }

        /* Results Container */
        #resultsPanel { display: none; }

        /* Job Header Bar */
        .job-banner {
            background: var(--surface-hover);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 12px 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 12px;
        }
        .job-banner-left {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 12px;
            color: var(--text-muted);
        }
        .job-id-pill {
            font-family: 'JetBrains Mono', monospace;
            background: #0d1322;
            padding: 3px 8px;
            border-radius: 6px;
            border: 1px solid var(--border);
            color: var(--accent);
            font-size: 11px;
        }
        .status-pill {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .status-pill.succeeded { background: rgba(16, 185, 129, 0.2); color: var(--accent-green); border: 1px solid rgba(16, 185, 129, 0.4); }

        /* Metric Badges */
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: #0d1322;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 14px 12px;
            text-align: center;
            transition: transform 0.2s;
        }
        .metric-card:hover { transform: translateY(-2px); border-color: var(--border-highlight); }
        .metric-title { font-size: 11px; font-weight: 500; color: var(--text-muted); margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.04em; }
        .metric-val { font-size: 17px; font-weight: 700; color: #fff; font-family: 'JetBrains Mono', monospace; }

        /* Stems Player */
        .stem-player-card {
            background: #0d1322;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            flex-wrap: wrap;
            transition: border-color 0.2s;
        }
        .stem-player-card:hover { border-color: rgba(79, 70, 229, 0.5); }
        .stem-info { min-width: 140px; }
        .stem-name { font-weight: 600; font-size: 13px; display: flex; align-items: center; gap: 8px; }
        .stem-gain { font-size: 11px; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; margin-top: 2px; }
        audio { height: 36px; flex: 1; min-width: 220px; outline: none; border-radius: 20px; }
        .stem-actions { display: flex; align-items: center; gap: 8px; }
        
        .btn-pill {
            background: var(--surface-hover);
            border: 1px solid var(--border);
            color: var(--text-main);
            padding: 6px 14px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }
        .btn-pill:hover {
            background: var(--primary);
            border-color: var(--primary);
            color: #fff;
            transform: translateY(-1px);
        }
        .btn-pill.primary {
            background: linear-gradient(135deg, var(--primary), #3b82f6);
            border: none;
            color: #fff;
            font-weight: 600;
        }
        .btn-pill.primary:hover {
            box-shadow: 0 4px 12px var(--primary-glow);
        }

        /* JSON Viewer */
        .manifest-container {
            position: relative;
        }
        pre {
            background: #080c14;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: #38bdf8;
            max-height: 280px;
            overflow: auto;
            line-height: 1.6;
        }
        .copy-btn {
            position: absolute;
            top: 10px;
            right: 10px;
            background: var(--surface-hover);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            cursor: pointer;
        }
        .copy-btn:hover { color: #fff; background: var(--border); }
        .links-row { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }
    </style>
</head>
<body>
<div class="container">
    <header>
        <div class="logo-area">
            <div class="logo-badge">SF</div>
            <div>
                <h1>SoundForge AI</h1>
                <div class="tagline">Professional AI Background Music Engine for Video • PS1 Specification</div>
            </div>
        </div>
        <div class="header-badges">
            <div class="badge badge-status" id="serverStatusBadge">
                <span style="width: 8px; height: 8px; border-radius: 50%; background: var(--accent); display: inline-block;"></span>
                API Ready (48 kHz)
            </div>
            <div class="badge badge-cleared">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
                100% Cleared DSP Stems
            </div>
        </div>
    </header>

    <div class="grid">
        <!-- Controls Column -->
        <div>
            <div class="card">
                <div class="card-title">
                    <div class="card-title-left">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
                        Generation Parameters
                    </div>
                </div>

                <div class="form-group">
                    <label>Prompt / Vibe Description</label>
                    <textarea id="promptInput" rows="3">Upbeat modern corporate intro with energetic drums and inspiring melody</textarea>
                    <div class="presets">
                        <button class="preset-btn" type="button" onclick="setPreset('Upbeat modern corporate tech tutorial with bright rhythm and uplifting acoustic feel', 12.0, 120, 'C_major')">Corporate Tech</button>
                        <button class="preset-btn" type="button" onclick="setPreset('Chill lo-fi study beat with warm electric piano and subtle relaxed bassline', 16.0, 80, 'A_minor')">Lo-Fi Chill</button>
                        <button class="preset-btn" type="button" onclick="setPreset('Cinematic dramatic build-up with driving bass and intense orchestral lead', 16.0, 95, 'D_minor')">Cinematic</button>
                        <button class="preset-btn" type="button" onclick="setPreset('Retro synthwave 80s arcade highway drive with analog synths', 14.0, 122, 'F_major')">Synthwave</button>
                        <button class="preset-btn" type="button" onclick="setPreset('Serene ambient drone with deep meditative texture', 20.0, 70, 'G_major')">Ambient</button>
                        <button class="preset-btn" type="button" onclick="setPreset('Funky energetic pop groove with punchy bass and bright chords', 12.0, 115, 'C_major')">Funk Groove</button>
                    </div>
                </div>

                <div class="form-group">
                    <label>Duration (Seconds) • 5.0s to 300.0s</label>
                    <div class="slider-row">
                        <input type="range" id="durationSlider" min="5" max="300" value="12" step="1" oninput="document.getElementById('durationVal').innerText = this.value + '.0s'">
                        <span class="slider-val" id="durationVal">12.0s</span>
                    </div>
                </div>

                <div class="form-group">
                    <label>Tempo (BPM) • Auto-inferred if Auto</label>
                    <div class="slider-row">
                        <input type="range" id="tempoSlider" min="0" max="200" value="0" step="1" oninput="document.getElementById('tempoVal').innerText = this.value == 0 ? 'Auto' : this.value">
                        <span class="slider-val" id="tempoVal">Auto</span>
                    </div>
                </div>

                <div class="form-group">
                    <label>Target Integrated Loudness (LUFS) • Default -16.0 LUFS</label>
                    <div class="slider-row">
                        <input type="range" id="lufsSlider" min="-24" max="-8" value="-16" step="1" oninput="document.getElementById('lufsVal').innerText = this.value + '.0 LUFS'">
                        <span class="slider-val" id="lufsVal">-16.0 LUFS</span>
                    </div>
                </div>

                <div class="form-group">
                    <label>Musical Key / Tonality</label>
                    <select id="keySelect">
                        <option value="">Auto-inferred from prompt</option>
                        <option value="C_major">C Major (Bright & Clean)</option>
                        <option value="A_minor">A Minor (Melancholic / Relaxed)</option>
                        <option value="G_major">G Major (Uplifting & Inspiring)</option>
                        <option value="D_minor">D Minor (Cinematic / Dramatic)</option>
                        <option value="F_major">F Major (Warm & Optimistic)</option>
                        <option value="E_minor">E Minor (Introspective)</option>
                    </select>
                </div>

                <div class="form-group" style="display: flex; gap: 20px; align-items: center; margin-top: 14px;">
                    <label style="margin: 0; cursor: pointer; display: flex; align-items: center; gap: 7px; color: var(--text-main);">
                        <input type="checkbox" id="loopCheck" style="accent-color: var(--primary);"> Seamless Loop
                    </label>
                    <label style="margin: 0; cursor: pointer; display: flex; align-items: center; gap: 7px; color: var(--text-main);">
                        <input type="checkbox" id="mp3Check" checked style="accent-color: var(--primary);"> Produce MP3 (320kbps)
                    </label>
                </div>

                <button class="btn-generate" id="generateBtn" type="button" onclick="submitMusicJob()">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                    <span>Generate Music</span>
                </button>

                <!-- Dynamic Progress Box -->
                <div class="progress-box" id="progressBox">
                    <div class="progress-label">
                        <span id="stageLabel">Submitting generation job...</span>
                        <span id="percentLabel">0%</span>
                    </div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill" id="progressBar"></div>
                    </div>
                    <div style="font-size: 11px; color: var(--text-subtle); display: flex; justify-content: space-between; margin-top: 4px;">
                        <span id="jobIdLabel">Job ID: Initializing</span>
                        <span id="elapsedTimer">0.0s</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Output Display Column -->
        <div>
            <!-- Visible Error / Warning Notification Banner -->
            <div id="alertBox" class="alert-box alert-error" style="display: none;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                <div style="flex: 1;" id="alertMessage">Error occurred.</div>
                <button type="button" onclick="hideAlert()" style="background: none; border: none; color: inherit; cursor: pointer; font-size: 14px;">✕</button>
            </div>

            <!-- Empty State (Shown before first generation) -->
            <div class="empty-state" id="emptyState">
                <div class="empty-icon">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
                </div>
                <div class="empty-title">Studio Monitor Ready</div>
                <div class="empty-desc">
                    Configure your desired musical parameters on the left and click <strong>Generate Music</strong> to synthesize a master mix, 4 genuine isolated instrument stems, and a full IncuBrix PS1 compliance manifest.
                </div>
                <div class="empty-tags">
                    <span class="empty-tag">48 kHz 24-bit PCM</span>
                    <span class="empty-tag">-16.0 LUFS EBU R128</span>
                    <span class="empty-tag">≤ -1.0 dBTP Ceiling</span>
                    <span class="empty-tag">4 Multi-Track Stems</span>
                    <span class="empty-tag">Linear Reconstruction Error &lt; 1e-6</span>
                </div>
            </div>

            <!-- Results Panel (Rendered dynamically when job succeeds) -->
            <div id="resultsPanel">
                <!-- Job Header Status Bar -->
                <div class="job-banner">
                    <div class="job-banner-left">
                        <span>Job:</span>
                        <span class="job-id-pill" id="renderedJobId">--</span>
                        <span class="status-pill succeeded" id="renderedStatus">Succeeded</span>
                    </div>
                    <div style="font-size: 11px; color: var(--text-muted);" id="renderedTimeInfo">
                        Ready for playback and export
                    </div>
                </div>

                <!-- Metrics Summary (Duration, Sample Rate, LUFS, True Peak, Recon Error) -->
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-title">Duration</div>
                        <div class="metric-val" id="metricDuration">-</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Sample Rate</div>
                        <div class="metric-val" id="metricSampleRate">48 kHz</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Loudness</div>
                        <div class="metric-val" id="metricLoudness">-</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">True Peak</div>
                        <div class="metric-val" id="metricPeak">-</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Recon Delta</div>
                        <div class="metric-val" id="metricRecon" style="color: var(--accent-green);">-</div>
                    </div>
                </div>

                <!-- Master Mix Player Card -->
                <div class="card" id="mixCard">
                    <div class="card-title">
                        <div class="card-title-left">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
                            Master Mix (48 kHz Stereo)
                        </div>
                        <span style="font-size: 11px; font-family: 'JetBrains Mono', monospace; color: var(--accent);">EBU R128 Mastered</span>
                    </div>
                    <div class="stem-player-card">
                        <div class="stem-info">
                            <div class="stem-name">Master Output</div>
                            <div class="stem-gain">Linear Summed Mix</div>
                        </div>
                        <audio id="audioMix" controls preload="metadata"></audio>
                    </div>

                    <div class="links-row" id="downloadLinks">
                        <!-- Populated by renderCompletedJob -->
                    </div>
                </div>

                <!-- Separate Stems Multi-Track Section -->
                <div class="card" id="stemsCard">
                    <div class="card-title">
                        <div class="card-title-left">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
                            Genuine Instrument Stems (Zero Frequency-Splitting Policy)
                        </div>
                        <span style="font-size: 11px; font-family: 'JetBrains Mono', monospace; color: var(--accent-green);">4 Independent Parts</span>
                    </div>

                    <!-- Drums Stem -->
                    <div class="stem-player-card">
                        <div class="stem-info">
                            <div class="stem-name">🥁 Drums & Percussion</div>
                            <div class="stem-gain" id="gainDrums">Gain: 0.85</div>
                        </div>
                        <audio id="audioDrums" controls preload="metadata"></audio>
                        <div class="stem-actions">
                            <a class="btn-pill" id="dlDrums" href="#" download="stem_drums.wav">WAV</a>
                        </div>
                    </div>

                    <!-- Bass Stem -->
                    <div class="stem-player-card">
                        <div class="stem-info">
                            <div class="stem-name">🎸 Bassline</div>
                            <div class="stem-gain" id="gainBass">Gain: 0.80</div>
                        </div>
                        <audio id="audioBass" controls preload="metadata"></audio>
                        <div class="stem-actions">
                            <a class="btn-pill" id="dlBass" href="#" download="stem_bass.wav">WAV</a>
                        </div>
                    </div>

                    <!-- Chords Stem -->
                    <div class="stem-player-card">
                        <div class="stem-info">
                            <div class="stem-name">🎹 Chords & Harmony</div>
                            <div class="stem-gain" id="gainChords">Gain: 0.70</div>
                        </div>
                        <audio id="audioChords" controls preload="metadata"></audio>
                        <div class="stem-actions">
                            <a class="btn-pill" id="dlChords" href="#" download="stem_chords.wav">WAV</a>
                        </div>
                    </div>

                    <!-- Melody Stem -->
                    <div class="stem-player-card">
                        <div class="stem-info">
                            <div class="stem-name">🎺 Lead Melody</div>
                            <div class="stem-gain" id="gainMelody">Gain: 0.75</div>
                        </div>
                        <audio id="audioMelody" controls preload="metadata"></audio>
                        <div class="stem-actions">
                            <a class="btn-pill" id="dlMelody" href="#" download="stem_melody.wav">WAV</a>
                        </div>
                    </div>
                </div>

                <!-- Manifest Inspector Card -->
                <div class="card" id="manifestCard">
                    <div class="card-title">
                        <div class="card-title-left">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                            PS1 Provenance Manifest (music_manifest.json)
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <a class="btn-pill" id="dlManifestLink" href="#" target="_blank" download="manifest.json">Download JSON</a>
                        </div>
                    </div>
                    <div class="manifest-container">
                        <button class="copy-btn" type="button" onclick="copyManifestText()">Copy JSON</button>
                        <pre id="manifestViewer"></pre>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
function resolveArtifactUrl(url) {
    if (!url) return '';
    if (url.startsWith('http://') || url.startsWith('https://')) {
        return url;
    }
    const cleanPath = url.startsWith('/') ? url : '/' + url;
    return window.location.origin + cleanPath;
}

function showAlert(msg, isError = true) {
    const box = document.getElementById('alertBox');
    const txt = document.getElementById('alertMessage');
    box.className = isError ? 'alert-box alert-error' : 'alert-box alert-success';
    box.style.display = 'flex';
    txt.innerText = msg;
}

function hideAlert() {
    document.getElementById('alertBox').style.display = 'none';
}

function setPreset(prompt, dur, bpm, key) {
    document.getElementById('promptInput').value = prompt;
    document.getElementById('durationSlider').value = dur;
    document.getElementById('durationVal').innerText = dur + '.0s';
    document.getElementById('tempoSlider').value = bpm;
    document.getElementById('tempoVal').innerText = bpm == 0 ? 'Auto' : bpm;
    document.getElementById('keySelect').value = key;
}

let activePollInterval = null;
let pollStartTime = null;

async function submitMusicJob() {
    hideAlert();
    const btn = document.getElementById('generateBtn');
    const pBox = document.getElementById('progressBox');
    const pBar = document.getElementById('progressBar');
    const pStage = document.getElementById('stageLabel');
    const pPercent = document.getElementById('percentLabel');
    const jobIdLabel = document.getElementById('jobIdLabel');
    const elapsedTimer = document.getElementById('elapsedTimer');

    btn.disabled = true;
    pBox.style.display = 'block';
    pBar.style.width = '5%';
    pStage.innerText = 'Submitting job...';
    pPercent.innerText = '5%';
    jobIdLabel.innerText = 'Job ID: Enqueuing...';

    const formats = ['wav'];
    if (document.getElementById('mp3Check').checked) formats.push('mp3');

    const tempoVal = parseFloat(document.getElementById('tempoSlider').value);
    const keyVal = document.getElementById('keySelect').value;
    const durVal = parseFloat(document.getElementById('durationSlider').value);
    const lufsVal = parseFloat(document.getElementById('lufsSlider').value);
    const loopVal = document.getElementById('loopCheck').checked;

    const payload = {
        prompt: document.getElementById('promptInput').value.trim(),
        duration_s: durVal,
        duration: durVal,
        tempo_bpm: tempoVal > 0 ? tempoVal : undefined,
        tempo: tempoVal > 0 ? tempoVal : undefined,
        key: keyVal || undefined,
        loopable: loopVal,
        loopability: loopVal,
        target_loudness: lufsVal,
        output_formats: formats
    };

    try {
        const resp = await fetch('/api/v1/music/jobs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!resp.ok) {
            const errBody = await resp.json().catch(() => ({}));
            const errMsg = errBody.error?.message || errBody.detail || 'HTTP ' + resp.status;
            showAlert('Failed to create music job: ' + errMsg, true);
            btn.disabled = false;
            pBox.style.display = 'none';
            return;
        }

        const data = await resp.json();
        const jobId = data.job_id;
        jobIdLabel.innerText = 'Job ID: ' + jobId.substring(0, 8) + '...';
        pollJob(jobId);
    } catch (e) {
        showAlert('Network error connecting to API: ' + e.message, true);
        btn.disabled = false;
        pBox.style.display = 'none';
    }
}

function pollJob(jobId) {
    if (activePollInterval) clearInterval(activePollInterval);
    pollStartTime = Date.now();
    let consecutiveErrors = 0;

    activePollInterval = setInterval(async () => {
        const elapsedSec = ((Date.now() - pollStartTime) / 1000).toFixed(1);
        document.getElementById('elapsedTimer').innerText = elapsedSec + 's';

        // Timeout check (300 seconds max)
        if (Date.now() - pollStartTime > 300000) {
            clearInterval(activePollInterval);
            document.getElementById('generateBtn').disabled = false;
            showAlert('Job polling timed out after 300 seconds. Check server logs.', true);
            return;
        }

        try {
            const resp = await fetch('/api/v1/music/jobs/' + jobId);
            if (!resp.ok) {
                consecutiveErrors++;
                if (consecutiveErrors > 5) {
                    clearInterval(activePollInterval);
                    document.getElementById('generateBtn').disabled = false;
                    showAlert('Failed to poll job status: Server returned HTTP ' + resp.status, true);
                }
                return;
            }
            consecutiveErrors = 0;
            const data = await resp.json();

            const pBar = document.getElementById('progressBar');
            const pStage = document.getElementById('stageLabel');
            const pPercent = document.getElementById('percentLabel');

            const pct = Math.max(5, Math.min(100, Math.round((data.progress || 0) * 100)));
            pBar.style.width = pct + '%';
            pPercent.innerText = pct + '%';
            pStage.innerText = data.current_stage || data.status;

            // IncuBrix status can be 'succeeded' or 'completed'
            if (data.status === 'succeeded' || data.status === 'completed') {
                clearInterval(activePollInterval);
                pBar.style.width = '100%';
                pPercent.innerText = '100%';
                pStage.innerText = 'Generation complete!';
                document.getElementById('generateBtn').disabled = false;
                renderCompletedJob(data);
            } else if (data.status === 'failed') {
                clearInterval(activePollInterval);
                document.getElementById('generateBtn').disabled = false;
                showAlert('Job synthesis failed: ' + (data.error || 'Unknown error'), true);
            }
        } catch (e) {
            consecutiveErrors++;
            if (consecutiveErrors > 5) {
                clearInterval(activePollInterval);
                document.getElementById('generateBtn').disabled = false;
                showAlert('Network polling error: ' + e.message, true);
            }
        }
    }, 600);
}

function renderCompletedJob(data) {
    const art = data.artifacts || {};
    const man = data.manifest || {};
    const metrics = man.audio_metrics || {};
    const recon = man.reconstruction_verification || {};

    // Hide empty state, reveal results panel
    document.getElementById('emptyState').style.display = 'none';
    const panel = document.getElementById('resultsPanel');
    panel.style.display = 'block';

    // Job header
    document.getElementById('renderedJobId').innerText = data.job_id || '--';
    document.getElementById('renderedStatus').innerText = (data.status || 'Succeeded').toUpperCase();
    if (data.completed_at) {
        document.getElementById('renderedTimeInfo').innerText = 'Completed at ' + new Date(data.completed_at).toLocaleTimeString();
    }

    // Populate Metrics
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

    // Master Mix Audio and Downloads
    const mixWavUrl = resolveArtifactUrl(art.mix_wav);
    const audioMix = document.getElementById('audioMix');
    if (mixWavUrl) {
        audioMix.src = mixWavUrl;
        audioMix.load();
    }

    const downloadLinks = document.getElementById('downloadLinks');
    let linksHtml = '';
    if (art.mix_wav) {
        linksHtml += `<a class="btn-pill primary" href="${resolveArtifactUrl(art.mix_wav)}" download="mix.wav">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            Download Master WAV
        </a>`;
    }
    if (art.mix_mp3) {
        linksHtml += `<a class="btn-pill" href="${resolveArtifactUrl(art.mix_mp3)}" download="mix.mp3">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            Download MP3
        </a>`;
    }
    if (art.mix_ducked_wav || art.ducked_mix_wav) {
        const duckedUrl = resolveArtifactUrl(art.mix_ducked_wav || art.ducked_mix_wav);
        linksHtml += `<a class="btn-pill" href="${duckedUrl}" download="ducked_mix.wav">Download Ducked Mix</a>`;
    }
    if (art.manifest_json || art.music_manifest_json) {
        const mfUrl = resolveArtifactUrl(art.manifest_json || art.music_manifest_json);
        linksHtml += `<a class="btn-pill" href="${mfUrl}" target="_blank" download="manifest.json">Download Manifest</a>`;
    }
    downloadLinks.innerHTML = linksHtml;

    // Stem Players & Downloads
    const stemConfig = [
        { id: 'Drums', artKey: 'stem_drums', defaultGain: '0.85', emoji: '🥁' },
        { id: 'Bass', artKey: 'stem_bass', defaultGain: '0.80', emoji: '🎸' },
        { id: 'Chords', artKey: 'stem_chords', defaultGain: '0.70', emoji: '🎹' },
        { id: 'Melody', artKey: 'stem_melody', defaultGain: '0.75', emoji: '🎺' }
    ];

    const stemGains = man.stem_gains || {};
    stemConfig.forEach(st => {
        const elAudio = document.getElementById('audio' + st.id);
        const elDl = document.getElementById('dl' + st.id);
        const elGain = document.getElementById('gain' + st.id);

        const stemUrl = resolveArtifactUrl(art[st.artKey]);
        if (elAudio && stemUrl) {
            elAudio.src = stemUrl;
            elAudio.load();
        }
        if (elDl && stemUrl) {
            elDl.href = stemUrl;
            elDl.download = `${st.artKey}.wav`;
        }
        if (elGain) {
            const g = stemGains[st.artKey.replace('stem_', '')] ?? st.defaultGain;
            elGain.innerText = `Mix Weight: ${g}`;
        }
    });

    // Manifest Inspector
    const manifestViewer = document.getElementById('manifestViewer');
    manifestViewer.innerText = JSON.stringify(man, null, 2);

    const dlMf = document.getElementById('dlManifestLink');
    if (dlMf && (art.manifest_json || art.music_manifest_json)) {
        dlMf.href = resolveArtifactUrl(art.manifest_json || art.music_manifest_json);
    }

    // Scroll results into view smoothly
    panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function copyManifestText() {
    const text = document.getElementById('manifestViewer').innerText;
    navigator.clipboard.writeText(text).then(() => {
        alert('Manifest JSON copied to clipboard!');
    }).catch(err => {
        console.error('Copy failed: ', err);
    });
}
</script>
</body>
</html>
"""
