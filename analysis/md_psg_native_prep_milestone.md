# Preparation des commandes PSG sur68000

Le module `md_z80_psg.c` utilise maintenant par defaut une preparation
plus compacte des commandes. Apres validation, count-1 et spacing tiennent
sur16bits : le produit passe par MULU.W plutot que le helper general32bits.
Les16octets sonores sont copies avec builtin memcpy vers un tableau local
explicitement aligne sur2octets. Cela evite les conversions de pointeurs
qui pourraient violer l'aliasing et permet quatre copies longues natives.

Le format22octets, la validation, l'ordre, les horizons, la propriete de
l'horloge, les gardes BUSREQ/grant et la publication atomique restent actifs.
Le compteur de tentatives n'est pas modifie. Le chemin historique reste
compilable avec MD_PSG_NATIVE_PREP=0. Les bancs le selectionnent explicitement
par defaut pour conserver leurs references; --psg-native-prep teste le chemin
optimise selectionne dans les sources du moteur.

La ROM jouable reste v0203. L'integration du nouveau pipeline au jeu et
l'echeance originale de reaffichage ne sont pas encore etablies.

## Mesures et validation

Les [comparaisons](md_psg_native_prep_comparison_report.json) utilisent les
memes48cas par region et2976octets PSG, avec memes dates logiques de fin,
memes motifs, carte, CRAM et image finale.

| Chemin | Retard maximal avant / apres NTSC | Retard maximal avant / apres PAL |
| --- | ---: | ---: |
| Refresh sans diagnostics lourds | 318720 / 146970 | 290235 / 149940 |
| Fresh-grant experimental | 394575 / 393945 | 400410 / 225270 |
| Refresh avec16etats et relectures | 2952315 / 2880780 | 2918520 / 2856450 |

Valeurs en ticks master. Le premier banc reduit son maximum d'environ54%
en NTSC et48%en PAL. Ses moyennes baissent aussi, de11761a10616ticks et
de11604a10780ticks. Le cout cumule des callbacks de publication baisse
d'environ7.7/7.8%. Cela mesure ces bancs, pas un gain global de vitesse du jeu.
Les autres comparaisons reduisent aussi leurs moyennes et maxima sonores.

Certains octets partent cependant plus tard quand la phase de bus change.
Le maximum de vidange video NTSC peut egalement augmenter. Le rapport
conserve ces differences; aucune echeance stricte ni fidelite complete
n'est declaree satisfaite. Fresh-grant reste un chemin video experimental.

Les12016tests du modele de publication comparent les22octets de chaque
commande avec des cibles HV independantes, y compris les reports de date,
la pression du ring et les erreurs atomiques. Les132tests de transfert
borne couvrent attente, epuisement, reprise, erreurs et limites de tentative.
Ils ne remplacent pas les captures natives.

Les trois noyaux optimises passent en PAL/NTSC. Le noyau complet verifie
768checkpoints RAM/audio et186624mots VRAM/CRAM par region, sans ecart.
Les intervalles PSG intrarafale restent exacts et aucune emission anticipee
n'est acceptee. L'[audit physique](md_psg_native_prep_physical_report.json)
controle21024DMA, le mode H32, l'affichage coupe, les phases source et les
intervalles prives Z80 strictement sous17100ticks.

La [revue du code compile](md_psg_native_prep_codegen_report.json) confirme
l'absence de __mulsi3 dans le publisher et quatre copies longues sur les
deux branches de copie. Une reconstruction du chemin historique produit
exactement le meme noyau que la reference archivee, SHA-256
3e6e88755a495d268acfbd255ddce6e36ed3abcb5085644d462d7d8c642e1661.

Les captures sont conservees dans md-psg-native-prep-v0203 et relues
integralement avant nettoyage. Le code source selectionne est optimise,
mais le boot, les sprites, l'integration complete, le waveform audio et
les echeances du jeu restent a terminer/verifier.

Archive finalisee :742references compressees;138948498octets generes retires,
104129799octets nets liberes. Reanalyse physique et revue des binaires lies regeneres
depuis gzip : rapports identiques; comparaison regeneree identique.
