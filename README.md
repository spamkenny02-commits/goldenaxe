# Golden Axe Warrior — portage Mega Drive

Reconstruire Golden Axe Warrior à partir de la ROM Master System fournie,
puis porter sa logique Z80 en code natif 68000 avec SGDK. La fidélité à la
Master System passe avant les améliorations.

<!-- ROM-RELEASE:START -->
**Version courante : v0183 — 1024 Kio.**

[Télécharger la ROM v0183](versions/v0183-ec1677f7/gaw-megadrive-v0183.bin) · [Toutes les versions](versions/README.md)

Contrôles ciblés réussis ; portage complet encore non validé.

SHA-256 : `ec1677f7fd5b45ff86a6a910488b47302ef759e5bfadd26332a1f3ded3bef876`  
Checksum Mega Drive : `CAAA`
<!-- ROM-RELEASE:END -->

## État du portage

Le portage est jouable mais reste incomplet. Les sources natives couvrent
l’intro avant le titre, le titre, les menus et dialogues, l’exploration,
les transitions, les combats, de nombreuses familles d’ennemis et boss,
les objets et sorts, les marchands, les récompenses, les sauvegardes et
la fin du jeu. Ces éléments ont des validations ciblées ; une partie
complète en progression naturelle reste à vérifier.

Les treize pistes musicales PSG et les bruitages ont un lecteur natif.
Leur synchronisation dans toutes les situations de jeu reste à contrôler.
Le binaire Mega Drive ne contient pas d’interpréteur Z80.

### Dernières corrections intégrées

- v0177 : conservation des récompenses et de la transformation des pièces,
  avec contrôles des retours dans les maisons et de la sauvegarde/reprise.
- v0178 : fondu musical B0 pendant les sorties de passages payants,
  puis lancement de la musique de destination avant la révélation.
- v0179 : fondus et révélation progressive des portes de maisons et de donjons,
  chargement masqué et restauration des couleurs des sprites.
- v0180 : attente explicite de la prochaine interruption vidéo avant la
  révélation, même lorsque l’affichage est désactivé. Les huit transitions
  de portes contrôlées ont un fondu d’entrée de 18 images, comme la SMS.
- v0181 : lecture des durées de notes au format brut 16 bits alignée sur la
  SMS, y compris lorsque le bit haut de la durée est positionné. Les 1 080
  cas ciblés, les 13 musiques et les 29 bruitages passent leurs contrôles.
- v0182 : arrêt conditionnel de séquence F3 lorsque le canal emprunté est
  actif, conforme à la SMS. Les 400 cas ciblés et les contrôles audio passent.

- v0183 : un silence du canal de bruit emprunté conserve la sortie PSG,
  comme sur SMS. Les 18 432 cas ciblés et les contrôles audio passent.

### Travail en cours

Rapprocher les durées de chargement et les animations de la SMS, en calculant
le travail original et les interruptions audio. Les routines de tempo,
fondu, arbitrage et traitement des commandes musicales/sonores ont des
modèles de coût vérifiés. Les enveloppes de volume ADSR et sur tables sont
également vérifiées. Les calculs de hauteur et de vibrato passent les tests
isolés ; le parcours observé en jeu utilise seulement le mode sans modulation.
Les notes, durées, silences, boucles, appels et retours de séquence ont
maintenant des coûts vérifiés en PAL et NTSC. Les arrêts F1/F2 sans restitution
8211 sont aussi contrôlés. Vingt commandes déterministes supplémentaires
et le partage F3 sont vérifiés sur des contextes isolés. Les commandes
utilisant le registre R et certaines restitutions restent à couvrir
avant une validation générale. La sélection
des notes de bruit (8679) dispose maintenant d’un modèle de coût vérifié ;
les notes, enveloppes et boucles F6/F7 du canal de bruit (864F) passent
39 360 cas isolés et les 1 102 appels d’un parcours en jeu. Les autres
commandes du bruit restent à couvrir. La composition des canaux de tonalité
(84C7) passe 20 680 cas isolés et les 3 372 appels du parcours observé,
qui utilise uniquement le vibrato sans modulation (mode 0). Le lecteur
complet correspond maintenant aux 1 202 appels du parcours contrôlé,
y compris ses deux sites de retour d’interruption. Les priorités passent
33 480 cas isolés et les conditions de pause/compensation passent 10 752 cas.
Les commandes utilisant R, certaines restitutions et les combinaisons
non couvertes restent à vérifier avant l’intégration aux chargements.
Le budget hors interruptions du chargement est désormais complet sur
24 scénarios de passages payants, avec 13 725 attentes VBlank et
14 424 appels audio contrôlés. La phase future et le travail VDP des
interruptions complètes restent à calculer pour prédire la durée physique.

Restent aussi la fidélité du hasard au registre Z80 R, les différences de
combat et d’affichage encore ouvertes, la progression naturelle complète
et la vérification sur matériel Mega Drive.

## Fichiers utiles

- [Sources 68000/SGDK](megadrive/src/main.c) et [moteur des acteurs](megadrive/src/actors.c).
- [Journal des ROMs numérotées](versions/README.md) et [index des versions](versions/index.json).
- [Corrections v0180](analysis/reveal_wait_milestone.md).
- [Correction audio v0181](analysis/raw_note_duration_milestone.md).
- [Correction du partage audio v0182](analysis/audio_ownership_milestone.md).
- [Correction du silence du bruit emprunté v0183](analysis/noise_note_milestone.md).
- [Mesures des interruptions audio](analysis/audio_irq_milestone.md).
- [Calcul du traitement des musiques et bruitages](analysis/audio_dispatch_milestone.md).
- [Calcul des enveloppes de volume](analysis/audio_envelope_milestone.md).
- [Calcul de la hauteur des notes et du vibrato](analysis/audio_pitch_milestone.md).
- [Calcul des notes et du contrôle des séquences](analysis/audio_note_sequence_milestone.md).
- [Calcul du canal de bruit](analysis/audio_noise_channel_milestone.md).
- [Calcul des canaux de tonalité](analysis/audio_tone_channel_milestone.md).
- [Composition du lecteur audio](analysis/audio_reader_milestone.md).
- [Attentes VBlank et budget de chargement](analysis/save_wait_milestone.md).
- [Travail restant et notes techniques](analysis/world_next.md).
- [Ancien README conservé comme historique](analysis/README_historique_avant_v0180.md).

`gaw-megadrive.bin` est le binaire courant. `gaw-title-megadrive.bin` est
un alias du même binaire pour les anciens liens. Les anciennes ROMs
numérotées sont conservées sans écrasement dans `versions/`.

## Compilation et Git

Depuis ce dossier, dans PowerShell :

```powershell
.\build.ps1
python tools/verify_git_roms.py
```

La compilation utilise SGDK et Java ; leurs chemins peuvent être fournis
avec les paramètres `-Sgdk` et `-Java` de [build.ps1](build.ps1).
Chaque nouveau binaire reçoit un numéro de version. La version et le lien
affichés en tête de ce README sont actualisés par `tools/version_rom.py`.

Git conserve les sources, outils, rapports principaux et ROMs numérotées.
Les captures et fichiers temporaires volumineux restent disponibles localement.
Le travail reste dans le dépôt Git local, sur la branche `main`, sans dépôt
distant configuré. Il sera copié vers un nouveau dépôt lorsque demandé.
L’ancien dépôt GitHub V51 contient un autre arbre de code ; aucun changement
n’y a été envoyé depuis ce projet.
