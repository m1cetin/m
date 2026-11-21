"""Ücretsiz arka plan müziği: yumuşak, sıcak bir ambiyans (numpy sentezi, telif yok)."""
import numpy as np, wave, os
SR = 44100; SURE = 72
t = np.arange(SR * SURE) / SR
rng = np.random.default_rng(3)
def nota(f, g):
    # hafif detune'lu iki testere + yumuşatma → pad
    x = sum(np.sin(2*np.pi*f*k*(1+d)*t)/k for k in range(1, 6) for d in (-0.003, 0.003))
    return x * g
# 4'er saniyelik akorlar: Dm – Bb – F – C (Doğu esintili, sakin)
akorlar = [(146.8, 174.6, 220.0), (116.5, 146.8, 174.6), (87.3, 130.8, 174.6), (130.8, 164.8, 196.0)]
y = np.zeros_like(t)
L = 8.0
for i in range(int(SURE / L) + 1):
    a = akorlar[i % 4]; s = i * L
    env = np.clip((t - s) / 2.5, 0, 1) * np.clip((s + L + 2.5 - t) / 2.5, 0, 1)
    for f in a:
        y += nota(f, 0.12) * env
# hafif kum/rüzgâr dokusu
n = rng.standard_normal(len(t)); k = np.ones(400) / 400
y += np.convolve(n, k, "same") * 0.4
# basit yankı
for d, g in ((0.23, .3), (0.41, .2), (0.67, .12)):
    s = int(d * SR); y[s:] += y[:-s] * g
y *= np.clip(t / 2, 0, 1) * np.clip((SURE - t) / 3, 0, 1)
y = y / np.abs(y).max() * 0.8
st = np.stack([y, np.roll(y, 300)], 1)
with wave.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "efektler", "muzik.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
print("ok")
