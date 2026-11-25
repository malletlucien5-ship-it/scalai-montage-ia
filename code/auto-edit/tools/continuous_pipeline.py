#!/usr/bin/env python3
"""Exécuter un graphe de commandes sans attente entre étapes, avec reprise vérifiée."""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import time


def atomic_json(path, data):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.partial')
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2))
    tmp.replace(path)


def signature(path):
    path=Path(path)
    st=path.stat()
    result={'path':str(path.resolve()),'size':st.st_size,'mtime_ns':st.st_mtime_ns}
    if st.st_size < 2_000_000:
        result['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def fingerprint(task):
    return hashlib.sha256(json.dumps({'command':task['command'],
        'inputs':[signature(p) for p in task.get('inputs',[])],
        'outputs':task['outputs'],'version':task.get('version',1)},sort_keys=True).encode()).hexdigest()


def validate_graph(tasks):
    ids=[t['id'] for t in tasks]
    if len(ids)!=len(set(ids)):
        raise ValueError('Identifiants dupliqués.')
    outputs=[str(Path(p).resolve()) for t in tasks for p in t['outputs']]
    if len(outputs)!=len(set(outputs)):
        raise ValueError('Deux étapes écrivent le même fichier.')
    pending={t['id']:set(t.get('depends',[])) for t in tasks}
    done=set()
    while pending:
        ready={key for key,deps in pending.items() if deps<=done}
        if not ready:
            raise ValueError('Dépendance absente ou circulaire.')
        done.update(ready)
        pending={key:deps for key,deps in pending.items() if key not in ready}


def run(config, state_dir, *, workers=2, stable_seconds=2, timeout=3600):
    tasks=config['tasks']; validate_graph(tasks)
    state_dir=Path(state_dir); state_dir.mkdir(parents=True,exist_ok=True)
    lock=(state_dir/'run.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    pending={t['id']:t for t in tasks}; done=set(); running={}; seen={}
    started=time.monotonic(); report={'started_at':time.time(),'status':'running','tasks':{}}

    def execute(task,key):
        begin=time.monotonic()
        log=state_dir/(task['id']+'.log')
        with log.open('a') as stream:
            subprocess.run(task['command'],stdout=stream,stderr=subprocess.STDOUT,check=True)
        if fingerprint(task)!=key:
            raise RuntimeError('Une entrée a changé pendant '+task['id'])
        outputs=[signature(p) for p in task['outputs']]
        if any(p['size']==0 for p in outputs):
            raise RuntimeError('Sortie vide : '+task['id'])
        receipt={'fingerprint':key,'outputs':outputs,'seconds':time.monotonic()-begin}
        atomic_json(state_dir/(task['id']+'.receipt.json'),receipt)
        return receipt

    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            while pending or running:
                if time.monotonic()-started > timeout:
                    raise TimeoutError('Délai maximal du pipeline dépassé.')
                for identity,task in list(pending.items()):
                    if not set(task.get('depends',[]))<=done:
                        continue
                    inputs=task.get('inputs',[])
                    if not all(Path(p).is_file() for p in inputs):
                        continue
                    sig=[signature(p) for p in inputs]
                    prior,when=seen.get(identity,(None,time.monotonic()))
                    if prior!=sig:
                        seen[identity]=(sig,time.monotonic()); continue
                    if time.monotonic()-when < stable_seconds:
                        continue
                    key=fingerprint(task)
                    receipt_path=state_dir/(identity+'.receipt.json')
                    receipt=json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
                    if receipt.get('fingerprint')==key and all(Path(p).is_file() for p in task['outputs']):
                        if receipt.get('outputs')==[signature(p) for p in task['outputs']]:
                            done.add(identity); del pending[identity]
                            report['tasks'][identity]={'status':'cached','seconds':0}
                            continue
                    if len(running)>=workers:
                        continue
                    running[pool.submit(execute,task,key)]=identity
                    report['tasks'][identity]={'status':'running','started_at':time.time()}
                    del pending[identity]
                    print('Démarrage : '+identity,flush=True)
                if running:
                    finished,_=wait(running,timeout=.25,return_when=FIRST_COMPLETED)
                    for future in finished:
                        identity=running.pop(future); result=future.result(); done.add(identity)
                        report['tasks'][identity]={'status':'complete',**result}
                        print('Terminé : '+identity,flush=True)
                elif pending:
                    time.sleep(.1)
                atomic_json(state_dir/'status.json',report)
        report['status']='complete'
    except BaseException as error:
        report['status']='failed'; report['error']=str(error)
        raise
    finally:
        report['seconds']=time.monotonic()-started
        atomic_json(state_dir/'status.json',report)
        lock.close()
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True,type=Path)
    parser.add_argument('--state',required=True,type=Path)
    parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--stable-seconds',type=float,default=2)
    parser.add_argument('--timeout',type=float,default=86400)
    parser.add_argument('--no-open',action='store_true')
    args=parser.parse_args()
    run(json.loads(args.config.read_text()),args.state,workers=args.workers,
        stable_seconds=args.stable_seconds,timeout=args.timeout)


if __name__=='__main__': main()
