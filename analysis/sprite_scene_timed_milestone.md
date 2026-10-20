# Frontieres d'instructions de la construction des sprites

`source_sprite_scene_timed` est une traduction C native dediee a0938,
son initialisation0A60 et l'emission09EE. Ce n'est pas un interpreteur Z80.
Les decisions et donnees du programme sont traduites en operations natives;
chaque instruction conserve son travail source T/M1 et sa frontiere
d'acceptation des interruptions via `SourceClock`.

Les ecritures du heros, pointeurs, tri, collisions, Y et X/tuiles deviennent
visibles avant l'instruction suivante. Une interruption peut donc observer
la table en cours de construction, au lieu d'une publication atomique finale.
Le chemin atomique precedent reste disponible. Le nouveau chemin peut avoir
deja modifie la RAM ou execute un callback lorsqu'il echoue : son contrat
impose d'abandonner la session, sans recommencer l'appel sur cet etat.

## Verification source et68000

L'observateur lit les frontieres d'instructions de la routine originale,
les dates master, le raster physique, R/IFF et581 octets de RAM : pointeurs,
visibilite du heros, workspace de tri, collisions, SAT et copie IRQ de test.
Le retour est observe immediatement apres RET, avant une instruction ou
interruption de l'appelant. Les sources du coeur sont restaurees apres
construction du DLL d'observation separe.

Les133 cas du producteur precedent passent en PAL et NTSC : captures reelles,
seuils/ordre/debordement, egalites et visibilite/type,64 entrees et anciens
buffers corrompus. Chaque region et chaque mode compare110010 instructions
plus133 retours. Le [banc sans IRQ](sprite_scene_timed_report.json) et le
[banc avec IRQ](sprite_scene_timed_irq_report.json) concordent a chaque point,
sur les dates, raster, R/IFF et les581 octets exacts.

Le banc avec interruptions utilise un ISR de test qui preserve les registres,
acquitte le VDP a35T et copie les192 octets SAT courants vers DF00, puis
restaure les registres/EI/RET. Son cout complet est4179T/398M1, accept inclus.
Ses84 acceptations par region surviennent devant28 PC distincts en NTSC et27
en PAL. Dix cas par region conservent une copie differente de la table initiale
et finale : ce sont bien des tables partielles observees pendant la construction.
Le [coeur standard](sprite_scene_observer_parity_report.json) produit les memes
resultats RAM que le coeur observateur pour les quatre variantes.

Les ROMs de [verification68000 sans IRQ](sprite_scene_timed_68k_report.json)
et [avec IRQ](sprite_scene_timed_irq_68k_report.json) executent les133 cas dans
chaque region. Elles comparent les110143 points par variante avec581 octets
RAM exacts, sans remplacer les donnees par un hash. Les dates et M1 attendus
viennent des traces et des octets d'instructions originaux. Les donnees sont
stockees sous forme de deltas sans perte; le [controle du format et du binaire](sprite_scene_trace_codec_report.json)
reconstruit chaque point et lie les donnees aux octets reels des ROMs natives.

Une seconde execution68000 sans hooks de trace donne la meme RAM8192 octets,
les memes travaux T/M1, dates, raster, echeance VINT, R/IFF/pending et nombre
d'interruptions. La trace de diagnostic ne cree donc pas le comportement teste.
Les ROMs de diagnostic font3 Mio; la ROM jouable reste v0203/1 Mio.

## Suite d'integration

L'ISR de test n'est pas l'interruption complete du jeu. Le raccordement au
contexte natif RAM336 octets/audio, les deux transferts source SAT64/SAT128,
leurs dates et la publication VDP doivent encore etre reunis. La sauvegarde
des registres/pile Z80 n'est pas comparee; les effets de pile restent a
l'appelant. Les motifs dynamiques, l'evolution autonome des acteurs, le boot,
une partie complete, les echeances de reaffichage, le waveform et le materiel
restent non valides. Aucun pourcentage global n'est deduit de ces bancs.

Les preuves sont figees dans `sprite-scene-timed-v0203` avant nettoyage.
Le verificateur du format peut relire les objets gzip verifies apres retrait
des fichiers generes. Les207 ROMs numerotees sont conservees, Git local uniquement.

Archive finalisee :181 references compressees;314753106 octets generes retires,
301680382 octets nets liberes. Reconstruction des traces depuis gzip et octets
des ROMs natives : rapport identique octet par octet apres nettoyage.
