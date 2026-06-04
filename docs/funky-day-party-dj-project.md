# Funky Day Party Autonomous DJ Project
## Complete Session Summary & Project Brief

**Date:** May 27, 2026
**User:** Tam (Israel)
**Goal:** Build a low-effort, autonomous party DJ system + proper multi-phase funky playlist for small day parties (5–50 people, 10–12 hours).

---

## 1. Core Vision

Turn an **old Android phone** into a dedicated, always-on party DJ slave that:

- Plays music directly through speakers (Bluetooth/AUX)
- Watches the dance floor with its own camera
- Automatically detects when energy/movement drops
- Skips or shifts to higher-energy tracks without the host touching anything
- Delivers a proper **energy journey** instead of random bangers

User is tired of pure trance parties and wants **funky, groovy, bass-heavy, ass-moving music** with variety:
- Dancehall
- Dub
- Reggaeton / Reggaetek
- Drum & Bass elements
- Tribal / organic / percussion / didgeridoo
- Some hip-hop and afro grooves
- Day-party friendly (lighter, sexier, less dark/aggressive than night raves)

---

## 2. Desired Party Flow (Day Party Structure)

**Phase 1: Warm-Up (First 2–3 hours)**
People arriving, still chill. Tribal, organic, groovy, percussion-heavy, didgeridoo vibes. Low pressure, conversational but moving.

**Phase 2: Build (Next 2–3 hours)**
Energy rising. Funky dancehall, modern reggae, groovy bass lines. People start dancing naturally.

**Phase 3: Peak (Main 3–4 hours)**
Full nasty, high-energy funky chaos. Dancehall, reggaeton, afro-house, funk, hip-hop grooves. Maximum ass movement.

**Phase 4: Wind Down / Sunset (Last 2–3 hours)**
Still groovy and funky but more breathable, deep, melodic, psychedelic. People can still dance but it's not aggressive.

Crossfade enabled on Spotify for smooth transitions (since music plays directly on the phone).

---

## 3. Technical MVP (Old Phone as Full DJ)

**Hardware:**
- Any old Android phone (even low-end) that can stay plugged in
- Good front/back camera
- Bluetooth speaker or AUX connection to sound system

**Software Stack (Simplest possible):**
- **IP Webcam** (Pro version recommended) — turns phone into IP camera + has motion detection + Tasker integration
- **Tasker** — the automation brain. Can trigger actions based on motion/no-motion
- **Spotify** (Premium required) playing directly on the phone

**How it works (MVP):**
1. Phone is mounted/pointed at dance floor, plugged in, screen on or always-on mode.
2. IP Webcam runs in background, detects motion.
3. Tasker profile: "If no significant motion for 90–120 seconds → trigger Spotify skip to next track or jump to higher-energy section."
4. Optional future: More advanced analysis (crowd density, dancing vs standing) via simple scripts or local ML.

This is **not** a full computer-vision year project. It's a practical, buildable system in days/weeks.

---

## 4. Playlist Recommendations (Starting Template)

Below is a structured 12-hour playlist broken into the 4 phases.
**This is a living document.** Add/remove based on what actually works at your parties.

### Phase 1: Warm-Up (Tribal / Organic / Groovy Chill)
Focus: Didgeridoo, hand percussion, organic grooves, light funk, world music influences.

- Lane 8 – Road
- St Germain – Rose Rouge
- Thievery Corporation – Lebanese Blonde
- Bonobo – Kerala
- Emapea – Mind
- The Quantic Soul Orchestra – Pushin' On
- Fat Freddy's Drop – Roady
- TJ Rehmi – One
- Nickodemus – Sun People (Earthrise Soundsystem Remix)
- Rising Appalachia – Medicine

### Phase 2: Build (Funky Dancehall / Groovy Bass)
Focus: Getting hips moving, funky modern reggae/dancehall.

- Major Lazer – Pon de Floor
- Busy Signal – Night Shift
- Vybz Kartel – Fever
- Protoje – Resist
- Damian Marley – Welcome to Jamrock
- Chronixx – Here Comes Trouble
- Sister Nancy – Bam Bam (various remixes)
- Alborosie – Kingston Town
- Kabaka Pyramid – Well Done
- Raging Fyah – Jah Glory

### Phase 3: Peak (Nasty High-Energy Funky Dancefloor)
Focus: Maximum movement — dancehall, reggaeton, afro, funk, hip-hop grooves.

- Sean Paul – Temperature
- Popcaan – Family
- Burna Boy – Ye
- Wizkid – Essence (feat. Tems)
- Black Coffee – Turn Me On (feat. Bucie)
- Bontan – Call You Back
- Michael Bibi – Hanging Tree
- Peggy Gou – (It Goes Like) Nanana
- Drake – One Dance (or similar groovy hip-hop/dancehall crossovers)
- Major Lazer & DJ Snake – Lean On (or heavier dancehall versions)
- Diplo & Sleepy Tom – Be Right There
- Afrojack & Steve Aoki – No Beef (funky remixes)

### Phase 4: Wind Down / Sunset (Deep Groovy & Melodic)
Focus: Still funky but breathable, psychedelic, emotional, danceable but not chaotic.

- FKJ – Vibin'
- Jordan Rakei – Mind's Eye
- Glass Animals – Heat Waves (funky/psychedelic remixes)
- ODESZA – Line of Sight
- Rufus Du Sol – Innerbloom (shorter edit or live versions)
- Bonobo – Linked
- Emancipator – First Snow
- Tycho – Awake
- Lane 8 – Atlas

---

## 5. How to Use This Playlist in Spotify

1. Open your empty playlist (`Funky Party Beast` or whatever you named it).
2. Search each song one by one and add them in the order above (or shuffle within phases).
3. Create **4 separate playlists** (one per phase) if you want easier manual control at first.
4. Later we can combine them into one master list with clear section markers in the title (e.g., "01. Warm-Up - Tribal Grooves").

---

## 6. Automation Rules (Initial Logic)

We will encode these rules into the skill / Tasker profiles:

- If low movement detected for 2+ minutes during **Build** or **Peak** → skip to next track or jump forward in playlist.
- If high chaotic movement → maintain current energy or allow natural builds.
- Gentle preference for groovy/funky tracks over pure aggression.
- Day-party friendly: avoid overly dark/minimal techno or super aggressive D&B unless specifically requested.

---

## 7. Next Steps (Prioritized)

1. **Immediate (you):** Add 15–20 songs from Phase 1 + Phase 2 to your Spotify playlist and send the link back so we can refine.
2. **This week:** Buy/install IP Webcam Pro + Tasker on the old phone and test basic motion → skip trigger.
3. **Next:** We create the actual **skill** using skill-creator that contains all the decision logic (behavior analysis → music action).
4. **Future iterations:** Improve vision (simple pose estimation or crowd density), add volume ducking, lighting sync, better phase transitions.

---

## 8. Brutal Honesty Check

- This setup will **not** be perfect on day one. Expect tuning.
- The playlist above is a strong starting template based on everything you described, but **your taste is the final judge**.
- The phone-as-DJ approach is realistic and achievable quickly. Full custom computer vision is a much bigger project — we start simple.

---

**Status:** Playlist template created. Technical direction agreed. Awaiting your feedback on songs + confirmation to proceed with skill creation + Tasker automation.

Ready when you are. Send the updated playlist link or tell me what to change.
