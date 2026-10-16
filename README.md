# Golden Axe Warrior — portage Mega Drive

Reconstruire Golden Axe Warrior à partir de la ROM Master System fournie,
puis porter sa logique Z80 en code natif 68000 avec SGDK. La fidélité à la
Master System passe avant les améliorations.

<!-- ROM-RELEASE:START -->
**Version courante : v0186 — 1024 Kio.**

[Télécharger la ROM v0186](versions/v0186-83a88ce9/gaw-megadrive-v0186.bin) · [Toutes les versions](versions/README.md)

Contrôles ciblés réussis ; portage complet encore non validé.

SHA-256 : `83a88ce9e663a49944e1f729e4529f446c4e8997c195b3ef55907657aac66734`  
Checksum Mega Drive : `C045`
<!-- ROM-RELEASE:END -->

## État du portage

La v0186 raccorde le dispatch audio natif vérifié (musique, bruitages et
commandes de contrôle). Les 2 304 cas de composant passent sur hôte et
en code 68000 PAL/NTSC ; 34 états contrôlés de la ROM jouable correspondent
aux 400 octets du lecteur SMS. Les coûts Z80/M1 sont désormais disponibles
pour cette routine, mais ne pilotent pas encore l'horloge du jeu.
Voir le [détail et les limites](analysis/native_audio_dispatch_milestone.md).

La v0185 rétablit les bruitages du menu Nouveau jeu/Continue : `$95` quand
le curseur change de ligne et `$AB` à la validation. Les parcours avec les
deux choix passent en PAL et en NTSC, avec des déclenchements aux mêmes
images que sur SMS et un canal d'effet audible. Appuyer vers le choix déjà
sélectionné reste silencieux. Ces contrôles ne remplacent pas une partie
complète ni une comparaison des formes d'onde audio.

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
14 424 appels audio contrôlés. Le travail des interruptions complètes
passe aussi 13 749 appels en jeu et 2 880 cas isolés. Le budget total
correspond aux 24 chargements contrôlés, avec les boucles et entrées
observées comme données. Les boucles de palette sont désormais prédites
depuis la phase d’entrée des 13 749 interruptions ; le compteur vidéo passe
149 500 positions isolées. Les 13 725 attentes VBlank sont maintenant
prédites depuis leur état d’entrée, avec 6 156 cas synthétiques supplémentaires.
La séquence de révélation est désormais prédite depuis un seul état
d’entrée : effacement, préparation, attente VBlank et réactivation de
l’affichage correspondent sur les 24 parcours et 7 220 cas isolés.
La routine graphique complète est également prédite depuis un seul état
sur les 24 parcours : motifs, métatuiles, terrain et copie SRAM, avec
six points de contrôle. Cela inclut les interruptions audio, la demande
de fondu musical B0 et la suspension des interruptions pendant la copie.
Le chargement de la carte est maintenant enchaîné à cette routine sans
état intermédiaire mesuré : les 24 parcours passent neuf points de
contrôle, avec les correctifs persistants et la file de tuiles.
Le HUD, son attente VBlank, le transfert vidéo et la restauration de
palette sont également enchaînés depuis l’état initial : les 24 parcours
passent maintenant 16 points de contrôle, avec les compteurs du HUD
fournis à l’entrée et les interruptions complètes calculées.
La suite du chargement (acteurs, historique) et les entrées de hasard
restent à prédire avant l’intégration aux timings natifs. Ces recherches
ne modifient pas encore la ROM v0183. Les lectures d’opcodes et le registre R
des interruptions vidéo passent désormais les 13 749 appels et 2 880 cas
isolés, sur leurs neuf étapes. Les files graphiques, motifs, HUD et lecteur
audio sont composés. Le premier trajet hors interruptions, du début du
chargement à la fin des motifs (16D0–1706), prédit maintenant R sur les
24 scénarios, avec 122 703 lectures d’opcodes et les interruptions audio
calculées. Ce calcul s’étend désormais jusqu’au retour de la routine
graphique complète (24B9) : six points de contrôle passent sur chacun
des 24 scénarios, soit 137 614 lectures hors interruptions, terrain et
copie SRAM compris. Le calcul atteint maintenant aussi le retour du
chargement de carte (24BC), avec neuf points par scénario : correctifs
persistants et file de tuiles sont inclus. HUD, attentes VBlank, acteurs
et historique restent à traiter. Les attentes VBlank calculent désormais
aussi R et les lectures des interruptions : 13 725 appels en jeu et
6 156 cas synthétiques correspondent. Le HUD est maintenant raccordé
depuis l’entrée du chargement jusqu’au retour 24BF : 384 comparaisons
sur les 24 scénarios, transfert et palette compris. Les jauges passent
aussi 18 042 cas isolés. L’historique est maintenant raccordé jusqu’à
l’entrée des acteurs : les 72 tirages aléatoires, leurs graines et R sont
prédits depuis l’état initial, avec 720 comparaisons sur les 24 parcours.
L’initialisation des acteurs atteint maintenant 1853 : types, statistiques,
persistance et compte actif correspondent sur les 24 parcours et les
1 536 combinaisons salle/masque. Le calcul couvre désormais aussi leurs
motifs, allocations partagées et conversions de palette jusqu’au retour
18E1 : R, timings, état des acteurs et motifs VRAM écrits correspondent.
Les routines du héros calculent maintenant R et la phase depuis leur
propre état d’entrée : 24 parcours et 13 150 cas isolés correspondent,
avec 475 octets d’état vérifiés. Ce raccordement est maintenant fait
depuis la RAM initiale du chargement : carte de collision et entrée du
héros sont reconstruites, avec 1 080 comparaisons jusqu’au retour 24E7.
Les scripts, la demande musicale et la préparation de révélation sont
maintenant raccordés jusqu’à la réactivation de l’affichage (0ACE), avec
1 320 comparaisons sur les 24 parcours. Le fondu/contours suivants, les
autres contextes et l’intégration native restent à vérifier. La récurrence
aléatoire et la progression de R sont maintenant traduites en C 68000 :
65 536 graines, 196 608 sorties et 66 816 progressions passent sur hôte
et dans une cartouche SGDK de test PAL/NTSC. Ces helpers attendent encore
le suivi natif de R. Le mécanisme d’horloge est maintenant aussi traduit
en C 68000 : 7 664 scénarios correspondent et cinq cas invalides sont
rejetés sur hôte et cartouche SGDK PAL/NTSC. Le callback audio dynamique
et le branchement au jeu restent à faire ; le hasard SGDK et les budgets
fixes sont encore utilisés en production.

La routine aléatoire originale est désormais vérifiée jusqu’à l’octet
produit à partir du registre R : 135 168 cas isolés et les 72 appels
d’historique des parcours contrôlés passent. La valeur de R à l’entrée
de la routine reste fournie ; son évolution depuis le début du chargement
et dans les interruptions reste à calculer avant de remplacer le hasard SGDK.
Le comptage des lectures d’opcodes du tempo, du fondu, de l’arrêt musical
et de l’arbitrage passe maintenant 66 530 cas isolés, avec contrôle de R,
des durées et de l’état audio. Le dispatch et la file des bruitages
prioritaires passent aussi 81 480 cas, avec les restitutions de canaux
prises en charge. Les enveloppes ADSR et sur tables passent maintenant
107 184 cas, avec contrôle de l’accumulateur, de DE et du dépilage des appels.
Les hauteurs et le vibrato passent aussi 118 832 cas, dont 32 dépilages
d’appel exercés avec des contextes synthétiques. Les notes et commandes
de séquence prises en charge passent 167 552 cas, dont 816 dépilages.
La composition des canaux de tonalité passe 20 680 cas isolés et les
3 372 appels d’un parcours en jeu, dont les anciennes captures restent
identiques. Le canal de bruit passe aussi 39 360 cas isolés et 1 102 appels
en jeu. Le lecteur complet compose maintenant ces comptes : 10 752 cas
de pause/compensation et 14 424 appels sur les 24 parcours passent, avec
les anciennes captures inchangées. Les commandes utilisant R, certaines
restitutions et les instructions du chargement restent à couvrir pour
calculer R depuis l’entrée. Le code des interruptions audio seules passe
15 360 cas isolés et 675 interruptions en jeu ; le vecteur et le lecteur
sont aussi vérifiés sur les 14 424 appels des parcours. Le corps des
interruptions vidéo complètes reste à composer pour ce comptage.

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
- [Interruptions vidéo et budget conditionnel complet](analysis/full_irq_milestone.md).
- [Phase vidéo et prédiction des boucles de palette](analysis/irq_raster_milestone.md).
- [Prédiction des attentes VBlank](analysis/wait_raster_milestone.md).
- [Prédiction de la révélation depuis un seul état](analysis/reveal_phase_milestone.md).
- [Phase du début de chargement graphique](analysis/graphics_prefix_phase_milestone.md).
- [Phase de la routine graphique complète](analysis/graphics_load_phase_milestone.md).
- [Phase graphique et chargement de carte](analysis/world_map_phase_milestone.md).
- [Phase graphique, carte, HUD et attente vidéo](analysis/map_hud_phase_milestone.md).
- [Sortie du hasard original et registre R](analysis/rng_refresh_milestone.md).
- [Lectures d’opcodes des préfixes audio](analysis/audio_prefix_refresh_milestone.md).
- [Lectures d’opcodes du dispatch et des effets prioritaires](analysis/audio_control_refresh_milestone.md).
- [Lectures d’opcodes des enveloppes audio](analysis/audio_envelope_refresh_milestone.md).
- [Lectures d’opcodes des hauteurs et du vibrato](analysis/audio_pitch_refresh_milestone.md).
- [Lectures d’opcodes des notes et commandes de séquence](analysis/audio_note_sequence_refresh_milestone.md).
- [Composition des lectures d’opcodes des canaux de tonalité](analysis/audio_tone_channel_refresh_milestone.md).
- [Composition des lectures d’opcodes du canal de bruit](analysis/audio_noise_channel_refresh_milestone.md).
- [Composition des lectures d’opcodes du lecteur audio complet](analysis/audio_reader_refresh_milestone.md).
- [Lectures d’opcodes du vecteur et des interruptions audio seules](analysis/audio_irq_refresh_milestone.md).
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

- [Lectures d’opcodes des interruptions vidéo complètes](analysis/full_irq_refresh_milestone.md).

- [Registre R pendant le chargement des motifs](analysis/graphics_prefix_refresh_milestone.md).

- [Registre R sur la routine graphique complète](analysis/graphics_load_refresh_milestone.md).

- [Registre R jusqu’au chargement de la carte](analysis/world_map_refresh_milestone.md).

- [Registre R pendant les attentes VBlank](analysis/wait_refresh_milestone.md).

- [Registre R jusqu’à la sortie du HUD](analysis/map_hud_refresh_milestone.md).

- [Tirages de l’historique depuis le début du chargement](analysis/history_refresh_phase_milestone.md).

- [Initialisation des acteurs et registre R](analysis/actor_prefix_refresh_milestone.md).

- [Graphismes des acteurs et registre R](analysis/actor_graphics_refresh_milestone.md).

- [Phases et registre R de l’initialisation du héros](analysis/hero_refresh_phase_milestone.md).

- [Chargement raccordé jusqu’au héros](analysis/loader_hero_refresh_milestone.md).

- [Chargement jusqu’à la réactivation de l’écran](analysis/loader_tail_refresh_milestone.md).

- [Routines aléatoires traduites en C 68000](analysis/native_source_rng_milestone.md).

- [Horloge d’instructions en C 68000](analysis/native_source_clock_milestone.md).
