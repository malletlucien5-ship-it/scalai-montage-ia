#!/usr/bin/env python3
"""Régression AI Advantage (09/10/2026) : une phrase dite une seule fois entre une amorce
et sa reprise restait coupée. Portions réelles de la prise 1, transcription faster-whisper."""
import unittest
import restart_detect as R

TEXTES = [
    "J'ai envie de vous parler du temps.",
    "Pas d'un point de vue motivationnel, mais d'une manière pratique.",
    "Parce que le temps est la seule chose dont vous ne pouvez pas créer davantage.",
    "Vous pouvez gagner plus d'argent.",
    "Vous pouvez gagner plus d'argent.",
    "agrandir votre équipe, trouver d'autres occasions pour faire des choses.",
    "Mais vous ne pouvez pas récupérer une seule heure que vous avez dépensé.",
    "Vous pouvez gagner plus d'argent, agrandir votre équipe, trouver d'autres occasions.",
    "Mais vous ne pouvez pas récupérer une seule heure que vous avez dépensée.",
    "Et en ce moment, la plupart des gens consacrent chaque semaine des heures à un travail que l'IA devrait déjà faire à leur place.",
]


def segs():
    return [{'index': i, 'text': t, 'camera': {'path': 'prise1.mp4', 'start': 10. + 4 * i, 'end': 13. + 4 * i}}
            for i, t in enumerate(TEXTES)]


class ReprisesAIAdvantage(unittest.TestCase):
    def test_phrase_unique_entre_amorce_et_reprise_gardee(self):
        self.assertNotIn(7, R.detect(segs()))

    def test_amorces_et_morceau_redit_coupes(self):
        cut = R.detect(segs())
        for k in (3, 4, 5, 6):
            self.assertIn(k, cut)

    def test_bonnes_prises_gardees(self):
        cut = R.detect(segs())
        for k in (0, 1, 2, 7, 8, 9):
            self.assertNotIn(k, cut)


if __name__ == '__main__':
    unittest.main()
