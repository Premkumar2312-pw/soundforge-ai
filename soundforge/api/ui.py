"""
Embedded Demonstration Web UI for SoundForge AI
Interactive interface for generation, stem solo/mute playback, ducking preview, and manifest inspection.
"""

DEMO_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SoundForge AI - Background Music Engine</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0b0f19;
            --surface: #131b2e;
            --surface-hover: #1b253e;
            --border: #232f4e;
            --primary: #4f46e5;
            --primary-glow: rgba(79, 70, 229, 0.35);
            --accent: #06b6d4;
            --accent-green: #10b981;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg);
            color: var(--text-main);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.5;
            padding: 24px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 28px;
        }
        .logo-area { display: flex; align-items: center; gap: 14px; }
        .logo-badge {
            background: linear-gradient(135deg, var(--primary), var(--accent));
            width: 44px; height: 44px; border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            font-weight: 700; font-size: 22px; color: #fff;
            box-shadow: 0 0 20px var(--primary-glow);
        }
        h1 { font-size: 22px; font-weight: 700; letter-spacing: -0.02em; }
        .tagline { font-size: 13px; color: var(--text-muted); }
        .badge-cleared {
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-green);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            border: 1px solid rgba(16, 185, 129, 0.3);
            display: flex; align-items: center; gap: 6px;
        }
        .grid {
            display: grid;
            grid-template-columns: 420px 1fr;
            gap: 28px;
        }
        @media (max-width: 960px) { .grid { grid-template-columns: 1fr; } }
        .card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 22px;
            margin-bottom: 20px;
        }
        .card-title {
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
            color: #fff;
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
            transition: border 0.2s;
        }
        input[type="text"]:focus, select:focus, textarea:focus {
            outline: none;
            border-color: var(--primary);
        }
        .presets { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
        .preset-btn {
            background: var(--surface-hover);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .preset-btn:hover { background: var(--border); color: #fff; }
        .slider-row { display: flex; align-items: center; gap: 12px; }
        .slider-row input[type="range"] { flex: 1; accent-color: var(--primary); }
        .slider-val { font-family: 'JetBrains Mono', monospace; font-size: 12px; min-width: 45px; text-align: right; color: var(--accent); }
        .btn-generate {
            width: 100%;
            background: linear-gradient(135deg, var(--primary), #3b82f6);
            color: #fff;
            border: none;
            padding: 12px 18px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            box-shadow: 0 4px 16px var(--primary-glow);
            transition: all 0.2s;
        }
        .btn-generate:hover { transform: translateY(-1px); box-shadow: 0 6px 20px var(--primary-glow); }
        .btn-generate:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        
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
            transition: width 0.3s;
        }
        .progress-label {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: var(--text-muted);
        }
        
        /* Stems Player */
        .stem-player-card {
            background: #0d1322;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
        }
        .stem-info { min-width: 130px; }
        .stem-name { font-weight: 600; font-size: 13px; text-transform: capitalize; }
        .stem-gain { font-size: 11px; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; }
        audio { height: 34px; flex: 1; outline: none; }
        .btn-pill {
            background: var(--surface-hover);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            cursor: pointer;
            text-decoration: none;
        }
        .btn-pill:hover { background: var(--border); color: #fff; }
        
        /* Metric Badges */
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: #0d1322;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 12px;
            text-align: center;
        }
        .metric-title { font-size: 11px; color: var(--text-muted); margin-bottom: 4px; }
        .metric-val { font-size: 18px; font-weight: 700; color: #fff; font-family: 'JetBrains Mono', monospace; }
        
        /* JSON Viewer */
        pre {
            background: #090d16;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: #38bdf8;
            max-height: 280px;
            overflow: auto;
        }
        .links-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
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
        <div class="badge-cleared">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
            100% Commercially Cleared DSP
        </div>
    </header>

    <div class="grid">
        <!-- Controls Column -->
        <div>
            <div class="card">
                <div class="card-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
                    Generation Parameters
                </div>

                <div class="form-group">
                    <label>Prompt / Vibe Description</label>
                    <textarea id="promptInput" rows="3">Upbeat modern corporate intro with energetic drums and inspiring melody</textarea>
                    <div class="presets">
                        <button class="preset-btn" onclick="setPreset('Upbeat corporate tech tutorial with bright rhythm', 12.0, 120, 'C_major')">Corporate Tech</button>
                        <button class="preset-btn" onclick="setPreset('Chill lo-fi study beat with warm electric piano and subtle bass', 16.0, 80, 'A_minor')">Lo-Fi Chill</button>
                        <button class="preset-btn" onclick="setPreset('Cinematic dramatic build-up with driving bass and epic lead', 16.0, 95, 'D_minor')">Cinematic</button>
                        <button class="preset-btn" onclick="setPreset('Retro synthwave 80s arcade groove', 14.0, 122, 'F_major')">Synthwave</button>
                    </div>
                </div>

                <div class="form-group">
                    <label>Duration (Seconds) • 5s to 300s</label>
                    <div class="slider-row">
                        <input type="range" id="durationSlider" min="5" max="300" value="12" step="1" oninput="durationVal.innerText = this.value + 's'">
                        <span class="slider-val" id="durationVal">12s</span>
                    </div>
                </div>

                <div class="form-group">
                    <label>Tempo (BPM) • Auto-detected if 0</label>
                    <div class="slider-row">
                        <input type="range" id="tempoSlider" min="0" max="180" value="0" step="1" oninput="tempoVal.innerText = this.value == 0 ? 'Auto' : this.value">
                        <span class="slider-val" id="tempoVal">Auto</span>
                    </div>
                </div>

                <div class="form-group">
                    <label>Target Integrated Loudness (LUFS) • Default -16 LUFS</label>
                    <div class="slider-row">
                        <input type="range" id="lufsSlider" min="-24" max="-8" value="-16" step="1" oninput="lufsVal.innerText = this.value + ' LUFS'">
                        <span class="slider-val" id="lufsVal">-16 LUFS</span>
                    </div>
                </div>

                <div class="form-group">
                    <label>Musical Key</label>
                    <select id="keySelect">
                        <option value="">Auto-inferred from prompt</option>
                        <option value="C_major">C Major (Bright & Clean)</option>
                        <option value="A_minor">A Minor (Melancholic / Chill)</option>
                        <option value="G_major">G Major (Uplifting)</option>
                        <option value="D_minor">D Minor (Cinematic / Serious)</option>
                        <option value="F_major">F Major (Warm & Optimistic)</option>
                    </select>
                </div>

                <div class="form-group" style="display: flex; gap: 16px; align-items: center;">
                    <label style="margin: 0; cursor: pointer; display: flex; align-items: center; gap: 6px;">
                        <input type="checkbox" id="loopCheck"> Seamless Loopable
                    </label>
                    <label style="margin: 0; cursor: pointer; display: flex; align-items: center; gap: 6px;">
                        <input type="checkbox" id="mp3Check" checked> Include MP3
                    </label>
                </div>

                <button class="btn-generate" id="generateBtn" onclick="submitMusicJob()">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                    Generate Music
                </button>

                <!-- Progress box -->
                <div class="progress-box" id="progressBox">
                    <div class="progress-label">
                        <span id="stageLabel">Enqueuing job...</span>
                        <span id="percentLabel">0%</span>
                    </div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill" id="progressBar"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Output Display Column -->
        <div>
            <!-- Metrics Summary -->
            <div class="metric-grid" id="metricsGrid" style="display: none;">
                <div class="metric-card">
                    <div class="metric-title">Duration</div>
                    <div class="metric-val" id="metricDuration">-</div>
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
                    <div class="metric-title">Recon Error</div>
                    <div class="metric-val" id="metricRecon" style="color: var(--accent-green);">0.0</div>
                </div>
            </div>

            <!-- Master Mix Player -->
            <div class="card" id="mixCard" style="display: none;">
                <div class="card-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
                    Master Mix (48 kHz 24-bit Stereo)
                </div>
                <div class="stem-player-card">
                    <div class="stem-info">
                        <div class="stem-name">Master Output</div>
                        <div class="stem-gain">Reconstructed Mix</div>
                    </div>
                    <audio id="audioMix" controls></audio>
                </div>

                <div class="links-row" id="downloadLinks"></div>
            </div>

            <!-- Separate Stems Multi-Track Section -->
            <div class="card" id="stemsCard" style="display: none;">
                <div class="card-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
                    Isolated Instrument Stems (Zero Frequency-Splitting)
                </div>

                <div class="stem-player-card">
                    <div class="stem-info">
                        <div class="stem-name">🥁 Drums & Perc</div>
                        <div class="stem-gain">Weight: 0.85</div>
                    </div>
                    <audio id="audioDrums" controls></audio>
                </div>

                <div class="stem-player-card">
                    <div class="stem-info">
                        <div class="stem-name">🎸 Bassline</div>
                        <div class="stem-gain">Weight: 0.80</div>
                    </div>
                    <audio id="audioBass" controls></audio>
                </div>

                <div class="stem-player-card">
                    <div class="stem-info">
                        <div class="stem-name">🎹 Chords & Harmony</div>
                        <div class="stem-gain">Weight: 0.70</div>
                    </div>
                    <audio id="audioChords" controls></audio>
                </div>

                <div class="stem-player-card">
                    <div class="stem-info">
                        <div class="stem-name">🎺 Lead Melody</div>
                        <div class="stem-gain">Weight: 0.75</div>
                    </div>
                    <audio id="audioMelody" controls></audio>
                </div>
            </div>

            <!-- Manifest Inspector -->
            <div class="card" id="manifestCard" style="display: none;">
                <div class="card-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                    Job Manifest (PS1 Compliance)
                </div>
                <pre id="manifestViewer"></pre>
            </div>
        </div>
    </div>
</div>

<script>
function setPreset(prompt, dur, bpm, key) {
    document.getElementById('promptInput').value = prompt;
    document.getElementById('durationSlider').value = dur;
    document.getElementById('durationVal').innerText = dur + 's';
    document.getElementById('tempoSlider').value = bpm;
    document.getElementById('tempoVal').innerText = bpm == 0 ? 'Auto' : bpm;
    document.getElementById('keySelect').value = key;
}

let activePollInterval = null;

async function submitMusicJob() {
    const btn = document.getElementById('generateBtn');
    const pBox = document.getElementById('progressBox');
    const pBar = document.getElementById('progressBar');
    const pStage = document.getElementById('stageLabel');
    const pPercent = document.getElementById('percentLabel');

    btn.disabled = true;
    pBox.style.display = 'block';
    pBar.style.width = '5%';
    pStage.innerText = 'Submitting job...';
    pPercent.innerText = '5%';

    const formats = ['wav'];
    if (document.getElementById('mp3Check').checked) formats.push('mp3');

    const tempoVal = parseFloat(document.getElementById('tempoSlider').value);
    const keyVal = document.getElementById('keySelect').value;

    const payload = {
        prompt: document.getElementById('promptInput').value,
        duration: parseFloat(document.getElementById('durationSlider').value),
        loopability: document.getElementById('loopCheck').checked,
        target_loudness: parseFloat(document.getElementById('lufsSlider').value),
        output_formats: formats
    };
    if (tempoVal > 0) payload.tempo = tempoVal;
    if (keyVal) payload.key = keyVal;

    try {
        const resp = await fetch('/api/v1/music/jobs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!resp.ok) {
            const err = await resp.json();
            alert('Error creating job: ' + (err.detail || JSON.stringify(err)));
            btn.disabled = false;
            pBox.style.display = 'none';
            return;
        }

        const data = await resp.json();
        pollJob(data.job_id);
    } catch (e) {
        alert('Network error: ' + e);
        btn.disabled = false;
        pBox.style.display = 'none';
    }
}

function pollJob(jobId) {
    if (activePollInterval) clearInterval(activePollInterval);

    activePollInterval = setInterval(async () => {
        try {
            const resp = await fetch('/api/v1/music/jobs/' + jobId);
            const data = await resp.json();

            const pBar = document.getElementById('progressBar');
            const pStage = document.getElementById('stageLabel');
            const pPercent = document.getElementById('percentLabel');

            const pct = Math.round(data.progress * 100);
            pBar.style.width = pct + '%';
            pPercent.innerText = pct + '%';
            pStage.innerText = data.current_stage || data.status;

            if (data.status === 'completed') {
                clearInterval(activePollInterval);
                document.getElementById('generateBtn').disabled = false;
                renderCompletedJob(data);
            } else if (data.status === 'failed') {
                clearInterval(activePollInterval);
                document.getElementById('generateBtn').disabled = false;
                alert('Job failed: ' + data.error);
            }
        } catch (e) {
            console.error('Polling error', e);
        }
    }, 700);
}

function renderCompletedJob(data) {
    const art = data.artifacts;
    const man = data.manifest;

    // Metrics
    document.getElementById('metricsGrid').style.display = 'grid';
    document.getElementById('metricDuration').innerText = man.audio_metrics.actual_duration_seconds + 's';
    document.getElementById('metricLoudness').innerText = man.audio_metrics.measured_loudness_lufs + ' LUFS';
    document.getElementById('metricPeak').innerText = man.audio_metrics.true_peak_dbtp + ' dBTP';
    document.getElementById('metricRecon').innerText = man.reconstruction_verification.max_reconstruction_error.toFixed(4);

    // Audio elements
    document.getElementById('mixCard').style.display = 'block';
    document.getElementById('audioMix').src = art.mix_wav;

    document.getElementById('stemsCard').style.display = 'block';
    document.getElementById('audioDrums').src = art.stem_drums;
    document.getElementById('audioBass').src = art.stem_bass;
    document.getElementById('audioChords').src = art.stem_chords;
    document.getElementById('audioMelody').src = art.stem_melody;

    // Download Links
    const linksDiv = document.getElementById('downloadLinks');
    linksDiv.innerHTML = `
        <a class="btn-pill" href="${art.mix_wav}" download="mix.wav">Download WAV</a>
        ${art.mix_mp3 ? `<a class="btn-pill" href="${art.mix_mp3}" download="mix.mp3">Download MP3</a>` : ''}
        <a class="btn-pill" href="${art.stem_drums}" download="stem_drums.wav">Drums Stem</a>
        <a class="btn-pill" href="${art.stem_bass}" download="stem_bass.wav">Bass Stem</a>
        <a class="btn-pill" href="${art.stem_chords}" download="stem_chords.wav">Chords Stem</a>
        <a class="btn-pill" href="${art.stem_melody}" download="stem_melody.wav">Melody Stem</a>
        <a class="btn-pill" href="${art.manifest_json}" download="manifest.json">Manifest JSON</a>
    `;

    // Manifest viewer
    document.getElementById('manifestCard').style.display = 'block';
    document.getElementById('manifestViewer').innerText = JSON.stringify(man, null, 2);
}
</script>
</body>
</html>
"""
