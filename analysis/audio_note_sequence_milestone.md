# Notes et controle des sequences audio originales

Recherche sur la ROM v0181 inchangee, SHA-256
97313b559898dcdc3a4d98623526f58c7b0b7565741882a02298de85a4358236.

Le modele independant de la routine Z80 8357 reproduit les notes, silences,
durees seules, frequences brutes 16 bits, liens E7, boucles F7, appels F8
et retours F9. 103424 cas isoles PAL/NTSC passent : les 400 octets du lecteur
et le nombre de cycles sont identiques a l'execution de la ROM originale.
Les flux synthetiques utilisent un amorcage specifique, sans interruption ;
la banque 6 et ses tables restent intactes. Certaines limites sont artificielles.

Les terminaisons F1/F2 ont 384 cas distincts, avec comparaison des 400 octets,
du cout et du retour depilant deux appels. Types de canaux 80/A0/C0/E0,
propriete et emprunt des canaux sont varies. DE0E=0 uniquement : la restitution
8211 lorsque DE0E!=0 reste explicitement non prise en charge.

Sur le parcours controle de passage payant 6D vers 96, masque FF, les 212
appels observes (95 NTSC,117 PAL) correspondent au modele, y compris six
terminaisons F2. Aucun appel capture n'est ignore. Les tableaux complets
de cycles du jeu original sont identiques aux captures archivees v0179.
Ce parcours ne prouve pas toutes les situations musicales du jeu.

Restent notamment les autres commandes, le canal bruit 864F, la restitution
8211, le cout complet des canaux et du lecteur, puis l'integration de la
prediction des interruptions aux chargements natifs. Pas de nouvelle ROM,
ni de revendication de validation complete du jeu ou des formes d'onde PSG.

Reproduire :

- python tools/validate_audio_note_sequence_cost.py
- python tools/validate_audio_note_termination_cost.py
- python tools/validate_live_note_sequence_cost.py (captures locales requises)
- python tools/archive_audio_note_sequence_research.py

Les sources, captures, fixtures, bibliotheques de mesure et rapports sont
conserves dans audio-note-sequence-research-v0181 avec manifeste SHA-256.
Les captures volumineuses restent locales ; les outils et rapports sont suivis Git.
