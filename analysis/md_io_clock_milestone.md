# Horloge vidéo et sorties PSG physiques du prototype

La ROM recommandée reste **v0203**, SHA-256
`7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7`.
Ces changements préparent le cadencement physique de la chaîne avec horloge.
Ils ne remplacent pas encore les routines de la ROM jouable.

## Mesure indépendante des ports

`tools/build_md_io_core.py` construit un cœur de diagnostic séparé. Il observe
les lectures HV et les écritures PSG 68000, avec leurs dates maître, valeurs et
PC. Les tableaux sont uniquement côté hôte. Les deux fichiers du cœur modifiés
pour la compilation sont restaurés octet par octet, même en cas d'échec.

`tools/validate_md_io_clock.py` produit une cartouche 68000 et teste les régions
NTSC/PAL. Dans chaque région, 8 192 lectures HV sont recopiées dans les deux
largeurs de port PSG : l'octet bas par une écriture octet, l'octet haut par une
écriture mot. Les valeurs observées correspondent à chaque lecture. Les états
RAM finaux complets et les images d'arrêt sont identiques avec le cœur normal.

Le compteur H32 commence à **0x85** au début de ligne, passe de **0x93 à 0xE9**,
puis revient à zéro 760 ticks maître après le début de ligne. Chaque valeur
couvre 20 ticks. Les 16 384 lectures physiques concordent avec la table du cœur
et la position verticale effective. L'écart de quantification observé est
0..18 ticks ; la borne générale est 0..19 ticks.

## Horloge native

`source_md_hclock` transforme des lectures HV en temps maître croissant modulo
32 bits, avec une origine et une ligne initiales explicitement fournies. Les
valeurs calculées en 68000 correspondent à chaque date physique quantifiée,
avec les rebouclages horizontaux, verticaux et 32 bits. **885 105 contrôles hôte**
couvrent aussi chaque position quantifiée de chaque région, plusieurs écarts
entre lectures, les entrées invalides et le maintien de l'état en cas d'erreur.

Les valeurs verticales sont parfois répétées. La première tentative de germe
PAL à partir du seul octet V a échoué : V=243 pouvait désigner la ligne 300.
La preuve finale commence à V=100, qui est sans ambiguïté, et vérifie cette
ligne contre la position physique observée. Ce germe ne constitue pas une
solution pour la phase globale depuis le boot.

Le contrat exige des lectures espacées de moins de 20 500 ticks maître en
NTSC, ou 194 920 en PAL. Une interruption ou un DMA compte dans cet intervalle.
Un échantillonnage trop lent peut donner un résultat plausible mais faux ; il
ne peut pas toujours être détecté à partir des seuls compteurs HV.

## Rafales rapprochées

Le chemin C de reconstruction, avec enregistrement du résultat dans la
cartouche de mesure, coûte plusieurs milliers de ticks entre la lecture HV
et la sortie. Il ne convient pas à une lecture d'horloge pour chaque octet
espacé de 315 ou 630 ticks source.

Deux candidats assembleur restent donc dans la cartouche de diagnostic :
quatre octets espacés nominalement de 315 ticks, et deux octets de 630 ticks.
**512 rafales de chaque type par région**, soit 3 072 écritures par région,
conservent les octets et leur ordre. Résultats mesurés au port :

| Espacement source | Espacement physique mesuré | Erreur depuis le premier octet |
| --- | --- | --- |
| 315 ticks | 308 ou 322 ticks | -14 à +7 ticks |
| 630 ticks | 616 ou 630 ticks | -14 à 0 ticks |

Les dates incluent le rafraîchissement du bus 68000 : le cœur ajoute parfois
14 ticks. Une somme théorique des coûts d'instructions ne suffisait donc pas.
Ces petits écarts sont des résultats de mesure, pas une relaxation de fidélité
autorisée par l'utilisateur.

## Limites et prochaine intégration

La première écriture de chaque rafale n'est pas encore placée sur une échéance
source. Les rafales ne sont pas encore reliées à la file. Le test masque les
interruptions et désactive l'affichage ; DMA, charge graphique et interruptions
de la chaîne complète doivent encore être mesurés. Seuls deux espacements sont
testés. Le matériel réel, la phase globale depuis le boot, les autres transferts
graphiques et l'aventure complète restent à vérifier.

Prochaine étape : un chemin assembleur court pour attendre l'échéance du premier
octet, puis utiliser les rafales lorsque leurs dates source correspondent.
Mesurer les erreurs au port, puis réévaluer le budget de la chaîne avec file.
Conserver la gestion des paquets entiers, la pression de file et l'arrêt du
consommateur sur toute erreur fatale.

Les preuves sont dans `analysis/md_io_clock_report.json` et l'archive immuable
`analysis/md-io-clock-v0203`. Les sources et la ROM restent dans le Git local.
