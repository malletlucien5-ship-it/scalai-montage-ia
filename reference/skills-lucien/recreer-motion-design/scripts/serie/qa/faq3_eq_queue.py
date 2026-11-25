import numpy as np, subprocess
from scipy.signal import welch
def lire(f, ss=None, t=None, sr=48000):
    cmd=["ffmpeg","-v","error"]+(["-ss",str(ss)] if ss is not None else [])+(["-t",str(t)] if t else [])+["-i",f,"-map","0:a:0","-af","pan=mono|c0=c0","-ar",str(sr),"-f","f32le","-"]
    return np.frombuffer(subprocess.run(cmd,capture_output=True,check=True).stdout,np.float32).astype(np.float64)
sr=48000; off=285.45673
p=lire("in/faq/montage.mp4",off,0.40); q=lire("in/queue/queue-3-metier.mov",0,0.40)
# signe local
print("corr signe", np.corrcoef(p[:len(q)],q[:len(p)])[0,1])
f,Pp=welch(p,sr,nperseg=2048); _,Pq=welch(q,sr,nperseg=2048)
bands=[63,125,250,500,1000,2000,4000,8000,12000,16000]
for lo,hi in zip(bands,bands[1:]):
    m=(f>=lo)&(f<hi); print(f"{lo:5d}-{hi:5d} Hz : {10*np.log10(Pp[m].sum()/Pq[m].sum()):6.1f} dB")
# bruit de fond : plaque 285.74-285.79 vs queue même instant
pb=lire("in/faq/montage.mp4",285.735,0.05); qb=lire("in/queue/queue-3-metier.mov",285.735-off,0.05)
print("bruit plaque %.1f dB, queue+24.3 %.1f dB"%(20*np.log10(pb.std()),20*np.log10(qb.std())+24.3))
