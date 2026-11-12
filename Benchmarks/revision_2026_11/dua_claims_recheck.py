import sys, runpy, io, contextlib, numpy as np
sys.argv=['x']
buf=io.StringIO()
with contextlib.redirect_stdout(buf):
    g=runpy.run_path('Benchmarks/revision_2026_11/dua_claims_check.py')
P,axis,ref,hits,shift_test,keys,DB,holm,SH=(g[k] for k in 'P axis ref hits shift_test keys DB holm SH'.split())
npk=P.sum(1)
print("mean peaks/spectrum", npk.mean().round(1), " ID3 peaks", npk[keys.index(('ch3_lib_002_20230825T104221_00_l1',3))])
# 1/2: her series = analytic n*2tol/580 ?
for n in (npk.mean(), 59):
    print(f"analytic min(1,n*2tol/580) n={n:.0f}:", [f"{min(1,n*2*t/580):.0%}" for t in (0.5,1.1,2,3,5)])
i3=keys.index(('ch3_lib_002_20230825T104221_00_l1',3))
pk3=axis[P[i3]]
for t in (0.5,1.1,2,3,5):
    hit=(np.abs(ref[:,None]-pk3[None])<t).any(1).sum()
    null=np.array([(np.abs(ref[:,None]+s-pk3[None])<t).any(1).sum() for s in SH])
    print(f"ID3 ±{t}: lines hit {hit}/24, null mean {null.mean():.1f}, p={(1+(null>=hit).sum())/(1+len(SH)):.4f}")
# 3: species tests with all 10000 shifts, parent axis, pilot
rows=[]
for sp,gq in DB.groupby('sp'):
    o,nm,p=shift_test(gq.wl.to_numpy(),axis); rows.append((sp,o,round(nm,1),p))
ps=np.array([r[3] for r in rows]); ad=holm(ps)
for r,a in sorted(zip(rows,ad),key=lambda z:z[0][3])[:3]: print("pilot 10k shifts", r, "holm", round(a,4))
# O I: how many distinct products carry the 777 hit
h=hits(np.array([777.19]),axis)[:,0]; prods={keys[i][0] for i in np.flatnonzero(h)}
print(f"O I 777.19: {h.sum()} spectra in {len(prods)} products")
# 6: her analytic per-line null
exp=np.minimum(1,npk*2*0.5/580).sum(); obs=hits(ref,axis).sum(0)
print(f"analytic expected per line {exp:.1f}; lines obs<=exp: {(obs<=exp).sum()}/24")
# 7: offset quantisation
pkw=[axis[r] for r in P]
o=[round(p[np.argmin(abs(p-396.85))]-396.85,3) for p in pkw if len(p) and abs(p-396.85).min()<0.5]
print("Ca II 396.85 offsets, distinct values:", sorted(set(o)))
