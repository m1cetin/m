"""GECE NÖBETİ – Bölüm 1 ses tasarımı.

Hiçbir hazır ses dosyası kullanmadan; oda uğultusu, ayak sesleri, saat tıkırtısı,
çan, gerilim drone'u, ani vuruş (stinger), elektrik cızırtısı ve son notayı
matematiksel olarak üretir. Kullanım:  python ses.py cikti.wav
"""
import os
import subprocess
import sys
import wave

import numpy as np

SR = 48000
FPS = 24
DUR = 40.5
rng = np.random.default_rng(11)
N = int(DUR * SR)
L = np.zeros(N)
R = np.zeros(N)


def t_arr(d):
    return np.arange(int(d * SR)) / SR


def lowpass_fft(x, cutoff, slope=4):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (f / cutoff) ** (2 * slope))
    return np.fft.irfft(X, len(x))


def bandpass_fft(x, lo, hi, slope=4):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR) + 1e-9
    X *= 1 / np.sqrt(1 + (f / hi) ** (2 * slope)) * 1 / np.sqrt(1 + (lo / f) ** (2 * slope))
    return np.fft.irfft(X, len(x))


def add(sig, start, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    gl = gain * np.sqrt((1 - pan) / 2)
    gr = gain * np.sqrt((1 + pan) / 2)
    L[i:i + len(sig)] += sig * gl
    R[i:i + len(sig)] += sig * gr


def env(n, a, d_total, release=None):
    e = np.ones(n)
    na = max(1, int(a * SR))
    e[:na] = np.linspace(0, 1, na)
    if release:
        nr = int(release * SR)
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def reverb(x, rt=1.6, mix=0.35, seed=0):
    """Müze salonu yankısı: üstel sönen gürültü ile konvolüsyon."""
    r = np.random.default_rng(seed)
    n = int(rt * SR)
    ir = r.standard_normal(n) * np.exp(-6.9 * np.arange(n) / n)
    ir = lowpass_fft(ir, 4500)
    ir /= np.sqrt(np.sum(ir ** 2))
    wet = np.fft.irfft(np.fft.rfft(x, len(x) + n) * np.fft.rfft(ir, len(x) + n))[: len(x)]
    return x * (1 - mix) + wet * mix


# ------------------------------------------------------------- oda uğultusu
def room_tone():
    d = 34.2
    w = rng.standard_normal(int(d * SR))
    brown = np.cumsum(w)
    brown -= lowpass_fft(brown, 8)  # DC kaymasını at
    brown = lowpass_fft(brown, 300)
    brown /= np.max(np.abs(brown))
    t = t_arr(d)
    hum = 0.25 * np.sin(2 * np.pi * 50 * t) + 0.1 * np.sin(2 * np.pi * 100 * t)
    tone = brown * 0.8 + hum * 0.3
    tone *= env(len(tone), 1.0, d, release=0.8)
    add(tone, 0, 0.07, -0.1)
    add(np.roll(tone, 5000), 0, 0.07, 0.1)


# ------------------------------------------------------------- ayak sesi
def footstep(seed):
    r = np.random.default_rng(seed)
    d = 0.25
    t = t_arr(d)
    click = bandpass_fft(r.standard_normal(len(t)), 300, 2500) * np.exp(-t / 0.018)
    thump = np.sin(2 * np.pi * (90 - 40 * t) * t) * np.exp(-t / 0.04)
    s = click * 0.8 + thump * 0.6
    return s / np.max(np.abs(s))


def footsteps():
    buf = np.zeros(int(6.0 * SR))
    step_dt = 1 / (2 * 0.9)
    k = 0
    tt = 0.15
    while tt < 5.0:
        s = footstep(k)
        i = int(tt * SR)
        g = 0.9 if k % 2 else 0.75
        buf[i:i + len(s)] += s[: len(buf) - i] * g
        tt += step_dt
        k += 1
    buf = reverb(buf, 1.8, 0.45, 1)
    add(buf, 0, 0.32)


# ------------------------------------------------------------- kalp atışı
def heartbeat(start, end, bpm=72):
    t0 = start
    while t0 < end:
        for off, g in ((0, 1.0), (0.18, 0.7)):
            t = t_arr(0.2)
            s = np.sin(2 * np.pi * 48 * t) * np.exp(-t / 0.05)
            add(s, t0 + off, 0.35 * g * min(1, (t0 - start + 0.5) / 2))
        t0 += 60 / bpm


# ------------------------------------------------------------- saat
def tick(seed, hi=True):
    r = np.random.default_rng(seed)
    t = t_arr(0.06)
    s = bandpass_fft(r.standard_normal(len(t)), 2000 if hi else 900, 6000 if hi else 3000) * np.exp(-t / 0.004)
    return s / np.max(np.abs(s))


def bell(f0=98.0, d=6.0):
    t = t_arr(d)
    s = np.zeros_like(t)
    for ratio, amp, dec in ((0.5, 0.6, 3.5), (1.0, 1.0, 2.5), (2.0, 0.5, 1.6), (2.76, 0.4, 1.2),
                            (5.4, 0.2, 0.6), (8.9, 0.1, 0.3)):
        s += amp * np.sin(2 * np.pi * f0 * ratio * t + ratio) * np.exp(-t / dec)
    s *= np.minimum(1, t / 0.004)
    return s / np.max(np.abs(s))


def clock():
    s3 = 265 / FPS
    jump = 312 / FPS
    tt = s3 + 0.15
    k = 0
    while tt < jump - 0.05:
        add(reverb(np.pad(tick(k, k % 2 == 0), (0, int(0.6 * SR))), 1.0, 0.3, 2), tt, 0.4)
        tt += 0.5
        k += 1
    # 03:00 – mekanik "klak" + çan; sonra saat durur
    add(reverb(np.pad(tick(99, False), (0, int(0.8 * SR))), 1.2, 0.4, 3), jump, 0.8)
    b = reverb(np.pad(bell(), (0, SR)), 2.5, 0.4, 4)
    add(b, jump + 0.02, 0.3, -0.2)
    add(np.roll(b, 900), jump + 0.02, 0.3, 0.2)


# ------------------------------------------------------------- gerilim
def drone(start, d, f=55.0, rise=True, bright=1200, seed=5, detune=0.6):
    t = t_arr(d)
    s = np.zeros_like(t)
    for k, df in enumerate((-detune, 0, detune)):
        ph = 2 * np.pi * (f + df) * t
        s += 2 * ((ph / (2 * np.pi)) % 1) - 1  # testere dişi
    s = lowpass_fft(s, bright)
    s /= np.max(np.abs(s))
    e = (t / d) ** 1.5 if rise else np.ones_like(t)
    e *= np.minimum(1, t / 0.5) * np.minimum(1, (d - t) / 0.3)
    return s * e


def cluster(start, d):
    """Kemanımsı uyumsuz yüksek tonlar, giderek yükselir."""
    t = t_arr(d)
    s = np.zeros_like(t)
    for k, f in enumerate((622.0, 659.0, 698.0, 932.0)):
        vib = 1 + 0.004 * np.sin(2 * np.pi * (5 + k * 0.3) * t)
        s += np.sin(2 * np.pi * f * vib * t + k)
    s /= 4
    s *= (t / d) ** 2.2 * np.minimum(1, (d - t) / 0.05)
    return s


def stinger():
    d = 3.5
    t = t_arr(d)
    sub = np.sin(2 * np.pi * (70 * np.exp(-t * 1.2) + 28) * t) * np.exp(-t / 1.2)
    hit = lowpass_fft(rng.standard_normal(len(t)), 1800) * np.exp(-t / 0.15)
    screech = np.zeros_like(t)
    for f in (1245.0, 1318.0, 1864.0):
        screech += np.sin(2 * np.pi * f * t * (1 - 0.02 * t))
    screech *= np.exp(-t / 0.7) * 0.2
    s = sub * 1.0 + hit * 0.8 + screech
    s = reverb(s, 2.5, 0.35, 6)
    return s / np.max(np.abs(s))


def buzz(d, seed):
    """Fener titrerken elektrik cızırtısı."""
    r = np.random.default_rng(seed)
    t = t_arr(d)
    s = np.sign(np.sin(2 * np.pi * 100 * t)) * 0.3 + r.standard_normal(len(t)) * 0.5
    s = bandpass_fft(s, 400, 5000)
    gate = (r.random(len(t) // 400 + 1) > 0.4).repeat(400)[: len(t)]
    s *= gate * np.minimum(1, (d - t) / 0.02)
    return s / (np.max(np.abs(s)) + 1e-9)


def flashlight_click():
    t = t_arr(0.08)
    s = bandpass_fft(rng.standard_normal(len(t)), 1500, 7000) * np.exp(-t / 0.006)
    return s / np.max(np.abs(s))


def whispers(start, d, seed=8):
    """Fısıltıyı andıran, filtrelenmiş nefes gürültüsü dalgaları."""
    r = np.random.default_rng(seed)
    t = t_arr(d)
    s = bandpass_fft(r.standard_normal(len(t)), 1800, 5200)
    mod = np.clip(lowpass_fft(r.standard_normal(len(t)), 3) * 6, 0, None)
    s *= mod * np.minimum(1, t / 1.5) * np.minimum(1, (d - t) / 0.2)
    return s / (np.max(np.abs(s)) + 1e-9)


def end_note():
    d = 4.0
    t = t_arr(d)
    f = 73.4  # D2
    s = sum(a * np.sin(2 * np.pi * f * h * t) * np.exp(-t / (2.2 / h))
            for h, a in ((1, 1.0), (2, 0.5), (3, 0.25), (4, 0.15), (6, 0.05)))
    s *= np.minimum(1, t / 0.01)
    s = reverb(s, 3.0, 0.5, 9)
    return s / np.max(np.abs(s))


def load_mp3(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<f4").astype(float)


def highpass_fft(x, cutoff, slope=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR) + 1e-9
    X *= 1 / np.sqrt(1 + (cutoff / f) ** (2 * slope))
    return np.fft.irfft(X, len(x))


def voices():
    """seslendirme/ klasöründeki ElevenLabs repliklerini karaktere göre işleyip yerleştirir."""
    import seslendirme as sl
    if os.environ.get("SESLENDIRME", "1") == "0" or not os.path.isdir(sl.KLASOR):
        return None
    track = np.zeros(N)
    found = False
    for name, who, start, _ in sl.REPLIKLER:
        p = os.path.join(sl.KLASOR, name + ".mp3")
        if not os.path.exists(p):
            continue
        found = True
        x = highpass_fft(load_mp3(p), 90)
        x = np.pad(x, (0, int(2.0 * SR)))  # yankı kuyruğu için boşluk
        if who == "riza":
            # hafızadan gelen fısıltı: ince bant + uzun yankı
            x = bandpass_fft(x, 250, 6500)
            x = reverb(x, 2.2, 0.38, 21)
        else:
            x = reverb(x, 0.8, 0.06, 23)  # Kemal: tüm repliklerde aynı, yakın ve kuru
        rms = np.sqrt(np.mean(x[np.abs(x) > 1e-3] ** 2))
        x *= 10 ** (-17 / 20) / (rms + 1e-9)
        i = int(start * SR)
        n = min(len(x), N - i)
        track[i:i + n] += x[:n]
    return track if found else None


def main(out):
    room_tone()
    footsteps()
    heartbeat(7.6, 11.0)
    clock()
    s4, s5, s6, son = 361 / FPS, 529 / FPS, 649 / FPS, 802 / FPS
    # Ç4: gerilim yükselir
    add(drone(s4, s5 - s4, 55.0, True, 900), s4, 0.38, -0.15)
    add(drone(s4, s5 - s4, 82.4, True, 700, detune=0.9), s4, 0.25, 0.15)
    add(cluster(s4, s5 - s4), s4 + 0.0, 0.12)
    # Ç5: ani vuruş + fener titremesi
    add(stinger(), s5 - 0.02, 0.95)
    add(buzz(0.45, 1), (529 + 26) / FPS, 0.18, 0.3)
    # Ç5–Ç6: derin drone ve fısıltılar
    add(drone(s5 + 0.5, son - s5 - 0.5, 36.7, False, 400), s5 + 0.5, 0.42)
    add(drone(s5 + 0.5, son - s5 - 0.5, 38.9, False, 300, detune=0.3), s5 + 0.5, 0.2)
    w = whispers(s6, son - s6)
    add(w, s6, 0.09, -0.5)
    add(np.roll(w, 7000), s6, 0.09, 0.5)
    add(buzz(son - (816 - 30) / FPS, 2), (816 - 30) / FPS, 0.2, 0.3)
    add(flashlight_click(), son, 0.6, 0.3)
    # son kart notası
    add(end_note(), 34.35, 0.55)

    mix = np.stack([L, R], axis=1)
    mix = np.tanh(mix * 1.2) / np.tanh(1.2)  # yumuşak limiter
    mix *= 0.7 / np.max(np.abs(mix))
    voice = voices()
    if voice is not None:
        # konuşma sırasında efekt/müzik ~7 dB kısılır (ducking)
        e = lowpass_fft(np.abs(voice), 4)  # yumuşak zarf
        e = np.clip(e / (np.percentile(e[e > 1e-4], 90) + 1e-9), 0, 1)
        duck = 1 - 0.55 * e
        mix = mix * duck[:, None] + voice[:, None]
        mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    mix *= 0.89 / np.max(np.abs(mix))
    pcm = (mix * 32767).astype("<i2")
    with wave.open(out, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    print("ses yazıldı:", out, f"{DUR}s")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "ses.wav")
