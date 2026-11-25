import json, re, difflib, statistics, sys
raw = json.load(open("work/whisper-raw.json"))
def norm(s): return re.sub(r"[^\w']", "", s.lower().replace("’", "'"))
new = []
for w in raw["words"]:
    colle = w["w"].startswith(("'", "’", "-")) or not re.search(r"\w", w["w"])
    if new and colle and w["s"] - new[-1]["e"] < 0.3:
        new[-1] = {"w": new[-1]["w"] + w["w"], "s": new[-1]["s"], "e": w["e"], "p": min(new[-1]["p"], w["p"])}
    elif norm(w["w"]):
        new.append(dict(w))
out = {"modele": raw["modele"], "langue": "fr", "source": raw["source"], "duree": round(raw["duree"], 3),
       "segments": raw["segments"], "words": new, "comparaison": {}}
for nom in ["words.json", "words-complet.json"]:
    old = json.load(open(f"in/faq/{nom}"))
    a = [norm(w["word"]) for w in old]; b = [norm(w["w"]) for w in new]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    ds, de, diffs = [], [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                ds.append(new[j1 + k]["s"] - old[i1 + k]["start"]); de.append(new[j1 + k]["e"] - old[i1 + k]["end"])
        else:
            diffs.append({"t": round(new[j1]["s"] if j1 < len(new) else old[i1]["start"], 2), "type": tag,
                          "ancien": " ".join(w["word"] for w in old[i1:i2]), "nouveau": " ".join(w["w"] for w in new[j1:j2])})
    ad = [abs(x) for x in ds]
    out["comparaison"][nom] = {"mots_ancien": len(old), "mots_nouveau": len(new), "identiques": len(ds),
        "ratio": round(sm.ratio(), 4), "ecart_debut_median_s": round(statistics.median(ad), 3),
        "ecart_debut_p95_s": round(sorted(ad)[int(0.95 * len(ad))], 3), "ecart_fin_median_s": round(statistics.median([abs(x) for x in de]), 3),
        "differences": diffs}
    print(nom, {k: v for k, v in out["comparaison"][nom].items() if k != "differences"}, "diffs", len(diffs))
dernier = new[-1]
out["dernier_mot"] = dernier
out["reprises"] = []
json.dump(out, open("transcript.json", "w"), ensure_ascii=False, indent=1)
