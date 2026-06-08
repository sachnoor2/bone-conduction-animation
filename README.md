# 🧠 Bone Conduction Animation
### "तुम्हारी आवाज़ Recording में DIFFERENT क्यों?" | Hindi Science | 1080×1920 @60fps

> **Hidict Studio** — Animation + Science + Education in Hindi

---

## 🎬 What This Is

A 45-second Hindi science explainer animation built with **Remotion** (TypeScript React).  
Style: 3Blue1Brown × Kurzgesagt × Veritasium  
Voice: ElevenLabs — Liam (energetic young male)

---

## ⚡ Pipeline (3 GitHub Actions Workflows)

```
Workflow 1: Generate & Sync-Check Audio
  ├── ElevenLabs API → 8 scene MP3s
  ├── AI Sync Checker → measures each audio vs visual window
  └── Auto re-renders slow/missing scenes → narration_final.mp3

Workflow 2: Render Video Chunks (parallel)
  ├── chunk_01_hook       (0–220f   | 3.6s)
  ├── chunk_02_setup      (180–540f | 6.0s)
  ├── chunk_03_mechanism  (500–1240f| 12s)
  ├── chunk_04_proof      (1200–1800f| 10s)
  ├── chunk_05_twist      (1760–2360f| 10s)
  └── chunk_06_outro      (2320–2700f| 6.3s)

Workflow 3: Assemble Final Video
  └── FFmpeg concat → BoneConduction_FINAL.mp4
```

---

## 🚀 Running the Pipeline

### Prerequisites

1. **GitHub Secrets** — add in `Settings → Secrets → Actions`:
   - `ELEVENLABS_API_KEY` — your ElevenLabs API key

2. **Run Workflow 1** first — Audio generation  
   Go to `Actions → 1 — Generate & Sync-Check Audio → Run workflow`

3. **Workflow 2** auto-triggers after Workflow 1 succeeds  
   Or run manually: `Actions → 2 — Render Video Chunks → Run workflow`

4. **Workflow 3** auto-triggers after Workflow 2 succeeds  
   Or run manually: `Actions → 3 — Assemble Final Video → Run workflow`

---

## 💻 Local Development

```bash
npm install
npm start          # Remotion Studio — preview in browser
npm run typecheck  # TypeScript check
```

---

## 📁 Project Structure

```
src/
  BoneConduction.tsx   # Main animation — all 6 scenes
  Root.tsx             # Composition registry + chunk definitions
  index.ts             # Remotion entry point
scripts/
  generate_audio.py    # ElevenLabs TTS — per-scene segments
  check_audio_sync.py  # AI sync checker + auto re-render
  assemble_video.py    # FFmpeg chunk concatenation
.github/workflows/
  1-generate-audio.yml
  2-render-chunks.yml
  3-assemble-final.yml
public/audio/          # Generated audio (gitignored, created by CI)
```

---

## 🎙 Narration Script (Hindi)

> तुम जो सुनते हो... वो तुम्हारी असली आवाज़ नहीं है।
>
> तुम्हारी आवाज़ — तुम तक दो रास्तों से पहुँचती है।
>
> पहला — Air Conduction। Sound waves हवा में travel करती हैं, Ear तक पहुँचती हैं। Microphone यही record करता है।
>
> दूसरा — Bone Conduction। Skull की हड्डियाँ... vibration को directly Cochlea तक ले जाती हैं। हड्डियाँ low frequency boost करती हैं। इसीलिए अपनी आवाज़ — तुम्हें rich लगती है।
>
> Microphone सिर्फ हवा capture करता है। Bone path miss हो जाता है। इसीलिए recording में — तुम पतले लगते हो।
>
> Beethoven... पूरी तरह बहरे थे। जबड़े से छड़ी लगाकर piano feel किया। हड्डियाँ सुन रही थीं।
>
> तुम्हारी असली आवाज़ वही है — जो दूसरे सुनते हैं।
>
> Comment करो — क्या तुम्हें अपनी recording पसंद है?

---

## 🔊 AI Sync Checker Logic

The `check_audio_sync.py` script verifies each audio segment fits its visual window:

| Status | Meaning | Action |
|--------|---------|--------|
| ✅ PASS | Within ±250ms | None |
| ✂ TRIM | Slightly over window | Hard-trim with FFmpeg |
| ⚡ SLOW | Significantly over | Re-render with higher speed/style |
| ❌ MISSING | File not found | Full re-render |

After fixing all scenes, it rebuilds `narration_final.mp3` automatically.
