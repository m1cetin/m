"""Ücretsiz efekt sesleri: hepsi numpy ile sentezlenir, lisans derdi yok."""
import numpy as np, wave, os
SR = 44100
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "efektler")
os.makedirs(D, exist_ok=True)
rng = np.random.default_rng(1)

def yaz(ad, x):
    x = x / (np.abs(x).max() + 1e-9) * 0.9
    y = np.stack([x, x], 1)
    with wave.open(os.path.join(D, ad + ".wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((y * 32767).astype(np.int16).tobytes())

def t(sn): return np.arange(int(SR * sn)) / SR

def lp(x, a):  # basit tek kutuplu alçak geçiren (a sabit ya da zamanla değişen dizi)
    a = np.broadcast_to(np.asarray(a, float), x.shape)
    y = np.zeros_like(x); s = 0.0
    for i in range(len(x)): s += a[i] * (x[i] - s); y[i] = s
    return y

# ping: parlak, kısa çan
tt = t(0.9)
ping = sum(np.sin(2*np.pi*f*tt) * g * np.exp(-tt*d) for f, g, d in [(1760,1,7),(2640,.5,9),(3520,.3,12),(5280,.12,16)])
yaz("ping", ping * np.minimum(1, tt*400))
# pop: yeni parça belirdiğinde tok "pup"
tt = t(0.25); f = 300*np.exp(-tt*18)+120
yaz("pop", np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-tt*22))
# whoosh: geçişler
tt = t(0.8); n = rng.standard_normal(len(tt)); env = np.sin(np.pi*tt/0.8)**2
yaz("whoosh", lp(n, 0.05 + 0.25*env) * env)
# top atışı: düşük patlama + kuyruk
tt = t(2.2); n = rng.standard_normal(len(tt))
boom = lp(n, 0.02) * np.exp(-tt*2.5) * 3 + np.sin(2*np.pi*55*tt) * np.exp(-tt*6) + lp(n, 0.3) * np.exp(-tt*30)
yaz("top", boom)
# deprem: uzun alçak gürleme + taş çatırtıları
tt = t(4.0); n = rng.standard_normal(len(tt))
rumble = lp(n, 0.006) * 8 * np.minimum(1, tt/0.6) * np.exp(-np.maximum(0, tt-2.8)*2)
for k in range(25):
    p = int(rng.uniform(0.3, 3.4)*SR); L = int(0.08*SR)
    rumble[p:p+L] += lp(rng.standard_normal(L), 0.4) * np.exp(-np.arange(L)/SR*60) * rng.uniform(0.3, 1)
yaz("deprem", rumble)
# taş yerine oturma: kısa tok tık
tt = t(0.15); yaz("tas", lp(rng.standard_normal(len(tt)), 0.25) * np.exp(-tt*45) + np.sin(2*np.pi*180*tt)*np.exp(-tt*40))
# su: damlalar + akış
tt = t(2.0); su = lp(rng.standard_normal(len(tt)), 0.08) * 0.25
for k in range(14):
    p = int(rng.uniform(0, 1.8)*SR); L = int(0.12*SR); u = np.arange(L)/SR
    f0 = rng.uniform(700, 1400); su[p:p+L] += np.sin(2*np.pi*np.cumsum(f0*(1+u*8))/SR) * np.exp(-u*35) * 0.6
yaz("su", su)
# davul: son vuruş
tt = t(1.2); f = 140*np.exp(-tt*10)+60
yaz("davul", np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*4) + lp(rng.standard_normal(len(tt)),0.3)*np.exp(-tt*25)*0.5)
# çatal/tabak: tını
tt = t(0.7); yaz("catal", sum(np.sin(2*np.pi*f*tt)*np.exp(-tt*d) for f, d in [(3100,9),(4650,12),(6200,15)]) * np.minimum(1, tt*800))
print("ok", sorted(os.listdir(D)))
