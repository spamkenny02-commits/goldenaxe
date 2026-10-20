# Transferts video durant les vraies phases de chargement

La ROM jouable reste v0203, SHA-256
`7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7`.
Ce jalon raccorde le banc video au chargeur natif68000 ; il ne publie pas
une nouvelle version du jeu ni un ordonnanceur de production.

## Disponibilite et duree de vie des donnees

Le chargeur termine la decompression des motifs au point1706.
Les routines suivantes de carte/HUD ne modifient pas leur miroir. La seule
copie ulterieure vers ce miroir dans cette chaine ecrit1536octets de table
de carte a partir de3800, puis atteint1deb. La palette est preparee apres.
Les IRQ utilisent les contextes RAM/audio et ne possedent pas ce miroir.

Le nouveau banc libere donc les octets0..37ff au point1706 (448tuiles d'atlas),
puis3800..3fff au point1deb (64tuiles). Le curseur de conversion ne depasse
jamais la frontiere disponible. Un bloc prepare garde son contenu et son
jeton pendant WAIT ; le prochain cas ne peut reutiliser la source qu'apres
vidage du cas precedent. Deux compteurs verifient48liberations de chaque
zone par region. Le mode complet compare aussi le hash des14336octets du
prefixe aux deux points ; ce controle ajoute une charge de diagnostic importante.
La revue des ecritures de la chaine complete etablit les zones disjointes.

Le service tente un bloc128octets aux checkpoints et avant/apres les appels
`source_clock_repeat_disabled` :1344passages par region sur48cas.
Les calculs a l'interieur des appels et les blocs inline ne sont pas servis.
Il n'y a ni attente forcee dans ces callbacks ni garantie de delai maximal.
Les fichiers des routines source, du DMA et du pilote restent inchanges ;
les wrappers de service modifient le noyau de mesure.

## Resultats physiques et controles

L'[analyse des chemins compiles](md_z80_phase_video_windows_report.json)
retrouve36864transferts pour les trois variantes PAL/NTSC. Elle verifie
les marqueurs de disponibilite, l'ordre FIFO et la limite de448tuiles avant
la disponibilite tardive. Aucun transfert ne precede1706 et les16derniers
blocs de chaque cas commencent apres1deb. Chaque maintien du bus et sa garde
HV se trouvent en VBlank ; aucune lecture Z80 n'intervient apres la garde
sous BUSACK et avant liberation.

| Variante | Blocs durant le chargement NTSC / PAL | Images totales NTSC / PAL |
| --- | ---: | ---: |
| [Allegee avec relecture](md_z80_psg_video_source_phase4_repeat_report.json) | 15 / 10 | 18211 / 10221 |
| [16etats et hash du prefixe](md_z80_psg_video_source_phase4_proof_report.json) | 23 / 34 | 22420 / 13717 |
| [Sans relecture intermediaire](md_z80_psg_video_source_phase4_fast_report.json) | 12 / 24 | 16347 / 9793 |

Les anciennes variantes de cet atlas ne transferaient aucun bloc avant
la fin du chargement. Le recouvrement est maintenant effectif, mais reste
faible : la grande majorite des6144blocs par region finit encore apres le son.
Les changements de charge et de phase interdisent d'attribuer ces durees
au seul changement de point de service. Ce n'est pas un gain general de cadence.

Les variantes avec relecture comparent1572864mots au total, sans difference.
Chacune passe48cas source, les2976octets PSG par region, les dates logiques,
les IRQ et l'etat final ; le mode complet compare aussi les16etats intermediaires.
Toutes les512tuiles finales correspondent a la conversion planaire independante.
RAM/VRAM/image finale concordent avec le coeur sans instrumentation.
La variante sans relecture ne prouve pas chaque transfert intermediaire.

Les maintiens maximaux valent6550ticks avec relecture et6270sans relecture.
L'analyse verifie aussi directement les PCs qui mettent a jour le compteur
prive : maximum16785ticks entre mises a jour, strictement sous17100 ;
avance physique au plus5lignes. Le validateur applique desormais cette garde
privee a tous les pilotes avec rafraichissement, en plus des lectures HV generales.
Les octets ne partent jamais avant leur date et les intervalles intrarafale
restent exacts. La mesure sonore physique du mode complet inclut cependant
les copies et les deux hashes de14336octets : le pire retard approche
39637050ticks, environ0,74seconde. Ce mode prouve les etats, pas une cadence jouable.
Meme les variantes allegees ne constituent pas une acceptation des retards.

La [reanalyse des huit anciennes lignes physiques](md_z80_phase_prior_windows_report.json)
reproduit leur rapport octet pour octet. Une phrase generique contradictoire
sur la disponibilite du premier nouveau rapport a ete corrigee ; le rapport
initial est conserve, sans changement de ses mesures ni de son noyau.

## Raccorder la vraie scene

L'atlas transforme tout le miroir SMS en motifs MD pour observer les transferts.
Ce n'est pas la representation finale : la zone3800 contient une table de carte.
Seuls6176octets (193motifs) sont decompressees par le prefixe ici teste ;
les autres octets commencent au marqueur de diagnosticA7 dans ce banc.
Dans le dernier cas NTSC,128des768entrees de carte referencent un motif
hors de ces193motifs, jusqu'au numero400. Les motifs conserves avant
chargement doivent donc etre fournis par le vrai demarrage, sans les inventer.

Le module existant `source_class0_video` fournit deja les193motifs ROM
convertis, la traduction des768mots de carte et celle des32couleurs.
Son upload monolithique ecran eteint/H40 ne doit pas etre appele tel quel
sous l'horloge audio active : les longs transferts doivent etre decoupes.
La suite doit brancher les blocs ROM immuables au point1706, la carte MD
au point1deb et les couleurs au point24bf, en conservant les motifs residents
et le backdrop du vrai etat de jeu. Sprites, IRQ natives, echeances et
verification du jeu complet restent a traiter. Les marqueurs PSG ajoutent
des ecritures et ne permettent toujours pas une preuve de l'onde originale.

Le Git reste local. L'archive `md-z80-source-phases-v0203` conserve563references
compressees apres relecture complete et verification des empreintes. Le nettoyage
retire1019861529octets generes, pour800559151octets nets liberes (environ0,75Gio).
La relecture independante passe, et la reanalyse apres nettoyage reproduit
le rapport physique octet pour octet depuis les captures archivees.
