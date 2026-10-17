# Motifs et coûts032A préparés depuis la ROM

La construction génère maintenant les6176 octets de motifs et les sommes
cumulées T/M1 des566 commandes du flux ROM de classe0. Chaque commande
est aussi comparée isolément au modèle d’instructions audité. Les données
et leurs coûts viennent de la ROM ; aucune phase capturée n’est utilisée.

Une nouvelle API facultative accepte ce plan correspondant exactement au
flux ROM. Elle cherche par dichotomie la dernière commande avant VINT,
avance l’horloge de son coût exact et copie les octets précalculés. Les
commandes qui traversent une limite conservent le chemin détaillé. Les
fins de plan, les mises à jour C031/C032 et les retours restent exécutés.
L’API existante conserve son décodeur général sans plan.

## Preuves

- 566 commandes vérifiées individuellement contre la suite d’instructions,
  puis216 entrées réelles et variantes de phase comparées au code scalaire :
  tous les16384 octets graphiques,336 RAM,400 audio,horloge et traces IRQ
  concordent. Les1460 cas du décodeur général restent conformes également.
- 16 cas supplémentaires de l’asset réel, avec régions logiques, phases,
  IFF, attente IRQ et délai EI variés, passent aussi en68000 sous PAL etNTSC.
  Comparaison octet par octet avec le scalaire immuable, y compris les
  journaux d’interruption. Les durées19072/15957 images sont celles de la
  preuve avec référence détaillée, pas celles du jeu.
- Avec et sans plan,24 parcours retrouvent les16 points SMS de16D0..24BF.
  Les deux voies passent en68000 PAL/NTSC. Le noyau précalculé termine en
  3083/2580 images de contrôle. Ses cas sont strictement identiques à ceux
  de la voie générale et aux preuves précédentes.

## Construction et mesure

`build.ps1` appelle `tools/generate_pattern_plan.py` et conserve le header
identique sans le réécrire. Le rapport lie les données à la ROM source par
SHA256. Les outils de chaîne et de profilage acceptent `--planned` ; le
profilage sans compteurs ajoute `--bare`. Les résultats précalculés ont
leurs propres fichiers et ne remplacent pas les contrôles généraux.

Le calcul seul de la voie précalculée demande22–24 images NTSC et18–19 PAL,
pour22,71/19,57 de travail SMS. La voie générale, mesurée avec le même outil,
demande23–24 et18–20. La résolution reste d’une image et le binaire change
d’alignement : le gain est modeste, dépendant du contexte.

Il n’y a toujours ni transferts graphiques réels ni sortie PSG dans cette
mesure. Certains cas NTSC dépassent encore le budget ; aucune marge pour
l’affichage n’est déclarée acquise. L’intégration de la phase depuis le
boot, les autres classes/branches, les acteurs et le héros restent à
compléter. La ROM jouable reconstruite reste exactement v0198 et n’utilise
pas encore cette chaîne avec horloge. Le portage complet reste en cours.

Rapports : [assets et commandes](pattern_plan_assets_report.json),
[comparaisons de phases68000](pattern_plan_phases_68k_report.json),
[chaîne précalculée68000](native_planned_room_finish_68k_report.json),
[budget précalculé](native_planned_loading_budget_bare_report.json).
