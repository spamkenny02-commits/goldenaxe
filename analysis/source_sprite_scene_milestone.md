# Production native de la table de sprites

`source_sprite_scene` traduit0938..0A71 et09EE : visibilite du heros,
initialisation des pointeurs, tri par Y ou ordre tournant, parcours des
descripteurs de direction/animation, indices de collision, cumul des
coordonnees et base de tuiles, terminaison de la SAT.
Le composant travaille sur la RAM C000..DFFF et une vue immuable de la
banque12. Il renvoie la banque selectionnee par la routine originale.

L'ordre tournant est choisi lorsque C047>=8 ou que le statut C01B contient
le debordement. Les quatre phases utilisent les tables originales en ROM.
Le tri parcourt les32 acteurs en sens inverse et insere avant les Y egaux;
les indices les plus faibles passent donc devant en cas d'egalite.
Le test de visibilite/type differe entre les deux branches et est conserve.
Les queues inutilisees de SAT et du workspace de tri restent intactes.
A64 entrees, le terminateur source DD80 recouvre le premier octet X : cet
effet exact est conserve, plutot que de le remplacer par une convention MD.

La fonction valide les adresses, descripteurs et la capacite avant de
modifier la RAM. Une entree invalide ou plus de64 sprites est refusee
sans mutation. Ce contrat borne le composant; il ne pretend pas reproduire
les ecritures hors table que ferait un programme Z80 avec des donnees invalides.

## Verification contre le programme original

Le [banc source](source_sprite_scene_report.json) execute les octets originaux
0938..0AA3 et la banque12 originale, dans un appelant de test SMS.
Seuls le boot, l'appelant, le vecteur et les donnees d'entree sont ajoutes
dans la ROM de diagnostic. Aucun remplacement de la routine testee.

Les133 cas passent en PAL et en NTSC :60 etats captures,64 variations du
seuil/phase/debordement et de visibilite/type/egalites, huit listes a64 entrees,
puis une ancienne SAT/workspace/indices de collision volontairement corrompus.
Chaque cas compare7934 octets RAM, hors marqueur de cas et page de pile de
l'appelant. Sept refus invalides verifient l'absence de modification RAM/sortie.

Le [banc68000](source_sprite_scene_68k_report.json) utilise directement les
resultats RAM produits par le Z80, exige d'abord leur egalite PAL/NTSC,
puis execute les memes133 cas dans une ROM Mega Drive avec le module natif.
Les7934 octets RAM et les pointeurs de sortie concordent pour chaque cas,
dans les deux regions. Il ne s'agit pas seulement d'un test compile pour PC.

## Raccordement au rendu et au son

Le banc `class0-sprite8-actors` demarre d'une copie separee de RAM d'acteurs,
avec ancienne SAT remplie de A5, workspace de5A et collisions de3C.
Il ne contient pas de SAT prerendue. Le68000 construit la liste de20 sprites
depuis les acteurs et la banque12, puis le flux DMA publie les motifs clones
et la SAT MD pendant que le Z80 assure la sortie PSG.

Les48 constructions par region passent. Le flux conserve les768 checkpoints
RAM/audio du chargeur,186624 mots de fond/CRAM et27648 mots de sprites relus
par region, sans erreur. Les2976 octets PSG, l'absence d'emission anticipee
et les intervalles intrarafale restent controles. Le noyau standard produit
le meme resultat que le noyau observateur.

La [comparaison des images](md_sprite_scene_pixel_report.json) trouve zero
ecart RGB sur256x216 pixels par region, avec833 pixels de sprites visibles.
L'oracle reconstruit independamment la table depuis les acteurs/descripteurs.
Les couleurs viennent de la calibration independante du jalon precedent.
L'[audit physique](md_sprite_scene_physical_report.json) lie la RAM d'entree
et la banque au binaire reel; il controle7008 spans de fond et864 spans de
sprites. Les ecarts prives Z80 restent sous17100 ticks master.

## Integration restante

La ROM jouable reste v0203. Le nouveau producteur est relie au rendu dans
le banc natif, pas encore au cycle complet du jeu. Il travaille atomiquement :
les points d'interruption intermediaires de0938, la date d'envoi de DD40 a
l'IRQ, la latence des statuts VDP et la date originale de reaffichage restent
a modeliser et raccorder. La copie d'acteurs du banc ne remplace pas leur
evolution autonome. Les motifs de sprites sont encore une entree capturee.
Le chargement/animation natif de ces motifs et leur propriete doivent suivre.

Le boot, une partie complete, le waveform audio et le materiel restent
non valides. Les preuves sont figees dans `md-sprite-scene-v0203` et relues
integralement avant nettoyage; les207 ROMs numerotees sont conservees.

Archive finalisee :323 references compressees;69175198 octets generes retires,
54665659 octets nets liberes. Audits physique et RGB regeneres depuis gzip :
rapports identiques octet par octet.
