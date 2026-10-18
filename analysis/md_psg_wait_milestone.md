# Attente matérielle et premières sorties PSG depuis la file

La ROM jouable reste **v0203**, SHA-256
`7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7`.
Le nouveau chemin reste dans le prototype de cadencement.

## Changement

`source_md_psg_wait_emit` attend une ligne et une position horizontale H32,
puis émet un octet, une paire à 630 ticks, ou quatre octets à 315 ticks. Le
calcul du compteur cible et le choix de la rafale se font avant l'attente.
Les boucles finales interrogent directement les octets V/H. Le compteur cible
est arrondi vers le haut au prochain palier de 20 ticks.

L'ordre signé de la portion H=85..FF puis 00..7F permet une boucle courte pour
les premières positions de la ligne. Une branche distincte traite la portion
H=00..84 et le passage à la ligne suivante. En particulier, manquer la valeur
FF ou la dernière valeur d'une ligne ne provoque pas une attente d'image entière.
L'assembleur conserve les registres que l'ABI SGDK impose de préserver.

Le contrat exige un appel anticipé d'au moins 3 000 ticks avant le début de
la ligne visée, des interruptions masquées et aucun DMA. La ligne doit être
la prochaine occurrence de la valeur V demandée. L'appel ne découvre ni
l'époque globale, ni les ambiguïtés verticales PAL/NTSC. Les arguments et la
disponibilité de la mémoire doivent être vérifiés par l'appelant.

## Preuve au port physique émulé

`tools/validate_md_psg_wait.py` construit une cartouche de mesure et utilise le
cœur d'observation HV/PSG du jalon précédent. Les octets passent par la file
native avec compteurs proches du rebouclage 16 bits et des dates qui rebouclent
sur 32 bits. Un consommateur unique les précharge à leur date logique ; les
écritures matérielles attendent ensuite la position vidéo demandée.

Chaque phase horizontale entière **0..3419** est testée avec les trois formes
de sortie, en PAL et NTSC : **10 260 groupes et 23 940 octets par région**.
Chaque groupe commence par un marqueur au port sur la ligne physique 90, puis
vise la ligne 100. La vérification utilise la date physique du marqueur, pas
la date de sortie pour reconstruire l'échéance. Aucune image n'est sautée.
Tous les octets et leur ordre correspondent aux entrées de file.

| Mesure en ticks maître | NTSC | PAL |
| --- | --- | --- |
| Retard du premier octet | 224..774 | 224..804 |
| Retard de tous les octets | 218..774 | 217..804 |
| Écart relatif à l'espacement source dans une rafale | -14..+7 | -14..+7 |

Les paires utilisent les valeurs et l'écart de 630 ticks capturés dans le
lecteur SMS d'origine. Les groupes de quatre volumes sont des cas synthétiques
de cadence. Ce test ne rejoue pas un flux audio SMS complet.

La RAM complète à l'arrêt et l'image d'arrêt sont identiques avec le cœur
normal et le cœur d'observation. Ce dernier ne modifie pas les cycles émulés.
Le rafraîchissement du bus 68000 reste actif. Les détails de chaque groupe
et les captures des ports sont archivés avec leurs empreintes.

## Essais et limites

Une première version relisant/décodant tout le compteur HV a dépassé
1 200 ticks de retard sur une phase testée. Les boucles directes V/H ont
remplacé ce chemin ; les mesures ci-dessus sont celles de la version finale.
Le test a également détecté les mauvais offsets de pile d'une première
version : SGDK réserve quatre octets pour chaque argument scalaire, même u16.
Les offsets sont corrigés dans le code final.

Le retard résiduel, surtout près des changements de portion du compteur H,
reste mesurable. Il ne constitue pas une tolérance de fidélité accordée par
l'utilisateur. Ce chemin ne promet pas de livrer chaque octet à sa date exacte.

Le producteur est arrêté pendant l'émission et ne subit pas de pression de
file dans ce test. Les interruptions et l'affichage sont désactivés. La
gestion d'erreur fatale, le réveil du consommateur pendant les calculs, les
autres espacements audio et l'intégration des événements du lecteur complet
restent à raccorder et à mesurer sous charge. Un appel avec un calendrier
erroné peut attendre la mauvaise occurrence V ; l'appelant doit le prévenir.
Il ne faut donc pas brancher directement cette fonction dans la ROM jouable.

Prochaine étape : séparer la préparation et l'attente courte, résoudre le
calendrier physique depuis l'horloge source, puis rejouer les événements
complets des chargements avec file et comparer les dates réellement émises.
Réévaluer ensuite le coût CPU et les interactions VINT/DMA/graphismes.

Voir `analysis/md_psg_wait_report.json` et l'archive immuable
`analysis/md-psg-wait-v0203`. Le README et les sources sont versionnés localement.
