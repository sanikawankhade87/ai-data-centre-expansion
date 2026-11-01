# Run from the repo root: python scripts/check_colours.py
"""Colour vision deficiency check: simulate each chart's colour pairs (Machado et al. 2009, severity 1.0)
and report the colour difference (CIE76 delta E in Lab). A pair passes if delta E >= 20 under every
simulation (clearly distinguishable); every pair also differs in lightness, which survives all three."""
import numpy as np
M = {"normal": np.eye(3),
     "protanopia": np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]]),
     "deuteranopia": np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]]),
     "tritanopia": np.array([[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]])}
def lin(c): c = np.array([int(c[i:i+2], 16) for i in (1, 3, 5)]) / 255; return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def lab(rgb_lin):
    xyz = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]) @ np.clip(rgb_lin, 0, 1)
    xyz = xyz / np.array([0.95047, 1.0, 1.08883]); f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])
pairs = {"Tab 1: 12-month average vs monthly line": ("#C46A10", "#A79E97"),
         "Tab 2: top-N bars vs other bars": ("#2a78d6", "#c9c7c1"),
         "Tab 2: top-N bars vs undisclosed (also hatched)": ("#2a78d6", "#e4e2dd"),
         "Tab 3: United States vs other regions": ("#C46A10", "#A79E97"),
         "Tab 4: construction vs AI use (lines and gap bars)": ("#C46A10", "#2B6CB0")}
ok = True
for name, (a, b) in pairs.items():
    des = {k: float(np.linalg.norm(lab(m @ lin(a)) - lab(m @ lin(b)))) for k, m in M.items()}
    worst = min(des, key=des.get); passed = des[worst] >= 20; ok &= passed
    print(f"{'PASS' if passed else 'FAIL'}  {name}: smallest delta E {des[worst]:.0f} ({worst}); " + ", ".join(f"{k} {v:.0f}" for k, v in des.items()))
print("All pairs distinguishable under protanopia, deuteranopia and tritanopia." if ok else "Some pairs fail.")
