# Relevé au passage vers une commande éloignée

Jalon historique : le chargement vivant a ensuite révélé un défaut de la
comparaison verticale de cette famille. La source est conservée sans modification
dans `megadrive/research/md_psg_sampled_z80.asm`. Le pilote courant compare les
lignes absolues ; voir le [nouveau banc et sa correction](md_z80_psg_live_milestone.md).

La variante `megadrive/z80/md_psg_sampled_z80.asm` ajoute un relevé privé après
la fin d'une rafale, lorsque la prochaine commande préparée arrive dans plus
de deux lignes. Elle intervient avant de refaire les décisions d'attente et
d'accorder une nouvelle prise du bus. À cet instant, `busy` reste actif,
l'accord reste révoqué et la publication reste impaire. Le relevé coupe un
intervalle qui pouvait accumuler calculs et pause native avant la lecture suivante.

Le prototype `md_psg_prefetch_z80.asm` est restauré octet pour octet depuis le
jalon précédent. La nouvelle variante est conservée séparément : elle améliore
un cas d'horloge critique, mais augmente certains retards sonores. Aucun pilote
expérimental n'est raccordé au jeu jouable ; jeu et lecteur source restent 68000.

## Trois phases physiques

Les rapports [nominal](md_z80_psg_sampled_handoff_report.json),
[intermédiaire](md_z80_psg_sampled_midserial_report.json) et
[frontière](md_z80_psg_sampled_edge_report.json) correspondent aux mêmes octets
de pilote. Les offsets de restitution sont 0, 1 700 et 3 419 ticks ; les points
de contrôle du producteur source restent inchangés.

| Offset, ticks | Retard maximal NTSC / PAL | Intervalle maximal entre lectures NTSC / PAL |
| ---: | ---: | ---: |
| 0 | 16 860 / 17 175 | 15 495 / 15 885 |
| 1 700 | 16 075 / 16 000 | 15 495 / 15 780 |
| 3 419 | 17 071 / 15 496 | 15 480 / 15 870 |

Les intervalles restent sous 17 100 ticks dans les six exécutions. Le cas NTSC
nominal descend de 16 860 à 15 495 ticks par rapport au prototype précédent.
Cette amélioration n'est pas uniforme sur chaque phase et région. Le retard
sonore maximal de la nouvelle variante est d'environ 0,32 ms, contre environ
0,29 ms pour le prototype précédent ; elle n'est donc pas promue en remplacement.

Les trois phases vérifient 17 856 octets source au total, les mêmes contextes
de chargement et points de contrôle, les rafales partielles, le parcours des
seize tampons et les sessions longues avec saturation et rebouclages. Les
3 576 intervalles internes contrôlés restent exactement à 315 ou 630 ticks.
Les 5 891 publications visibles et 7 535 mises à jour courtes concordent avec
les lectures physiques indépendantes. Les écarts de compteur restent au plus
de cinq lignes. Les prises de bus restent au plus à 4 242 ticks et ne chevauchent
pas les intervalles internes des rafales contrôlées. Le calcul 68000 témoin,
la RAM finale et l'image d'arrêt restent conformes aux contrôles indépendants.

Ces résultats couvrent trois phases, sans preuve exhaustive des autres phases,
des DMA, des interruptions natives ni d'une console réelle. Le producteur finit
encore avant la restitution : ce banc ne prouve pas leur fonctionnement simultané.

## Essai rejeté et compilation échouée

`retained-clock` ajoute le relevé après les écritures de publication et conserve
la première date pour les décisions d'attente. Le cas NTSC 128 atteint néanmoins
17 850 ticks entre lectures et est rejeté avant le PAL. La capture situe la pause
native dans un intervalle suivant une fin de rafale ; cela motive le relevé ciblé
de la variante conservée séparément.

La première compilation de la phase intermédiaire, lancée en parallèle d'une
autre compilation du SDK, cesse de progresser. Son journal final révèle une
erreur de GCC sur un chemin temporaire mal converti, avec le lecteur intégré
une seconde fois au chemin courant. Une tentative d'arrêt ciblé est effectuée,
mais aucun manifeste de processus n'est produit : elle ne prouve pas que des
processus ont effectivement été arrêtés. Le handle est confirmé terminé avec
le code 1. La cause établie est l'erreur de chemin ; le rôle du parallélisme
n'est pas démontré. `sampled-middle` est conservé comme build échoué avant
émulation. Le nouveau répertoire `sampled-midserial`, compilé seul, passe le
banc complet. Les prochains builds de ce SDK restent séquentiels pendant
l'analyse de la conversion des chemins temporaires.

La commande suivante correspond au banc historique ; la variante est désormais
retirée du répertoire des pilotes sélectionnables :

```powershell
python tools/validate_md_z80_psg.py --variant sampled-proof --driver md_psg_sampled_z80.asm --expect-prefetch --phase-offset 1700
```

L'archive `analysis/md-z80-psg-margin-v0203` conserve sources, captures et journal
d'échec de compilation avant nettoyage vérifié des fichiers générés. La ROM jouable reste
**v0203**, les 207 ROMs numérotées sont préservées et le Git reste local. Le
portage complet reste en cours : il faut encore résoudre le compromis entre
marge d'horloge et délai, puis mesurer le vrai producteur avec le son, l'affichage,
les entrées, les interruptions, la phase de boot et l'abandon immédiat.
