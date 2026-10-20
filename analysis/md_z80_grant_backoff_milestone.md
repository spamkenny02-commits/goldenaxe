# Reprises DMA : attentes, phase du faisceau et cout reel

La ROM jouable reste v0203, SHA-256
`7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7`.
Les primitives natives DMA et le pilote de reference restent inchanges.
Ce jalon ajoute des experiences de reprise et de publication idle, pas une nouvelle ROM.

## Trois essais qui ne terminent pas

Une comparaison preliminaire stricte entre le V courant et l'autorisation
fraiche semble pouvoir eviter de prendre le bus pour un transfert voue au rejet.
En pratique, elle ne laisse passer que4blocs de8tuiles avant un million
de tentatives infructueuses. La garde de vidage signale0xf10 ;95echecs sont
ensuite visibles dans le banc complet. Les mots deja relus concordent,
mais cela ne prouve pas que le chemin peut terminer.

Dans la premiere capture,6823lectures sous BUSACK surviennent une ligne
apres le dernier V lu pour l'autorisation, contre seulement4dans la meme
ligne. Cette mesure rapproche les lectures physiques ; elle ne prouve pas
a elle seule la valeur de chaque octet de boite aux lettres.

Un pilote idle experimental rafraichit compteur prive et autorisation a
chaque passage, avec publication coherente complete une fois sur quatre.
Avec la comparaison preliminaire stricte, il ne termine pas non plus :
2blocs seulement. Autoriser une ligne de marge avant BUSREQ, tout en gardant
l'age final0 sous BUSACK, donne20blocs puis le meme echec avec le pilote
initial. Ces trois experiences sont rejetees et leurs captures conservees.

Le pilote idle et la marge preliminaire combines terminent en PAL/NTSC,
mais regressent :16783/11004images contre16326/10594pour la reference.
Le [banc physique](md_z80_idle_slack_windows_report.json) confirme les
transferts en VBlank. Le [test audio long](md_z80_psg_idle_grant_output_core_report.json)
passe48cas source et26synthetiques par region, avec pression de file et
bouclages8/16/32bits. Cela ne justifie pas de selectionner ce pilote pour le debit.
Les [609controles natifs par region](md_video_span_contract_fresh_precheck_report.json)
passent aussi pour le premier essai : ils verifient les contrats, pas la
progression des transferts. Leur succes ne remplace pas les tests longs.

## Attendre un changement d'autorisation

L'option experimentale `--video-grant-backoff` conserve jeton et contenu
apres WAIT et differe l'appel suivant tant que l'octet d'autorisation reste
identique. Une erreur de boite aux lettres contourne cette attente et reste
traitee. L'option ne reutilise jamais une autorisation comme preuve de succes :
la primitive DMA originale refait tous ses controles sous BUSACK.
Le compteur des appels DMA et celui des tentatives sautees sont distincts.

La [comparaison physique des chemins compiles](md_z80_grant_backoff_windows_report.json)
controle quatre variantes en PAL/NTSC. Tous les transferts comptabilises
restent integralement en VBlank. Le maintien maximal du bus vaut9649ticks
avec relecture et9299sans relecture. Toutes les mises a jour privees restent
sous17100ticks ; maximum15930pour ces quatre variantes.

| Charge identique dans chaque paire | NTSC : images totales | PAL : images totales |
| --- | ---: | ---: |
| Reference avec relecture de chaque mot | 16326 | 10594 |
| Attente du changement, avec relecture | 15739 | 9983 |
| Reference sans relecture | 17633 | 9706 |
| Attente du changement, sans relecture | 14893 | 12160 |

Avec relecture, les appels DMA baissent de1039461a737377en NTSC et de625392a417337en PAL.
Les393216mots par region concordent, et19/21transferts precedent le dernier octet
PSG, contre7/11pour la reference. Aucun ne precede la fin du chargement logique.
Le pire vidage apres chargement passe de271,005a317,418images NTSC :
le gain total ne suffit pas a prouver une meilleure echeance par cas.

Sans relecture, le temps total baisse d'environ15,5pourcent NTSC et augmente
de25,3pourcent PAL. Le pire vidage passe de286,815a233,945images NTSC,
mais de113,453a191,864PAL. Les512tuiles finales sont toutes comparees a une
conversion planaire independante ; ces deux variantes ne relisent pas chacun
de leurs transferts intermediaires. Les tailles adaptatives peuvent varier,
mais chaque cas doit produire exactement512tuiles, avec histogrammes et
chemins physiques verifies separement.

Le [controle des16etats intermediaires](md_z80_psg_video_source_span8_backoff_proof_report.json)
passe aussi avec l'attente :48cas,2976octets PSG et393216mots relus par region,
aucune difference. Il ne se compare pas directement a la variante allegee :
les copies de diagnostic changent la charge et les retards audio mesures.
Aucune emission anticipee ni alteration des intervalles intrarafale n'est acceptee.
La RAM/VRAM/image finale concorde avec le coeur sans instrumentation.

L'attente reste optionnelle et non selectionnee comme ordonnanceur de production.
La phase des appels et la charge changent fortement les resultats ; des reprises
moins nombreuses ne prouvent ni une cadence du jeu ni une echeance de rendu.
La suite doit placer les conversions/transferts sur les vraies phases productrices,
avec une duree maximale par phase, puis raccorder carte/palettes/sprites et IRQ natives.
Les marqueurs PSG ne permettent toujours pas de valider l'onde sonore originale.
Le Git reste local. L'archive `md-z80-grant-backoff-v0203` conserve1616references
compressees, apres verification des empreintes et relecture complete. Le nettoyage
retire2373167471octets generes, soit1852389688octets nets liberes (environ1,73Gio).
La relecture independante passe et la reanalyse des captures archivees reproduit
le rapport physique octet pour octet apres nettoyage.
