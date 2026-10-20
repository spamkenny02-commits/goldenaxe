# Rendu natif des sprites SMS 8x8

Le nouveau composant `source_sms_sprite8` transforme une table SMS de
64 sprites en table Mega Drive et en motifs propres a chaque entree.
Les masques de lignes reproduisent la limite de huit sprites par ligne
de la Master System, y compris les sprites transparents ou hors ecran
qui consomment une place. Les masques de colonnes reproduisent le decalage
de huit pixels, le bord gauche masque et les limites horizontales.
Les coordonnees verticales rebouclent et le marqueur Y208 termine la liste.

Le transfert `md_sms_sprite8_stream` publie les motifs puis remplace les
64 entrees de la SAT Mega Drive. Une liste vide efface donc aussi l'ancienne
table. Les charges utiles restent propres au transfert pendant WAIT.
Le chemin utilise les spans DMA caches existants avec l'affichage coupe,
en H32/224, sous un seul proprietaire VDP et interruptions masquees.
Il ne decide pas de la date de reaffichage et n'active jamais l'affichage.

## Preuves

- [Oracle portable](sms_sprite8_report.json) : 701 cas, 34455552 pixels,
  60 captures SMS reelles, toutes les valeurs Y, limites et debordements,
  cas aleatoires; 11 refus invalides sans modification de sortie.
- [Contrat natif](md_sms_sprite8_contract_report.json) : 25 controles par
  region, notamment refus avant BUSREQ/HV, WAIT conserve, defaut persistant,
  reservation VRAM, changement de largeur et table vide.
- [Images physiques](md_sms_sprite8_pixel_report.json) : six variantes
  PAL/NTSC, chacune comparee sur 256x216 pixels, aucun pixel RGB different.
  La capture reelle contient 17 sprites; les autres cas couvrent 18 entrees
  et debordement, bouclage Y, effacement d'une ancienne SAT, capacite64 et
  masquage par le HUD (308 pixels masques par region).
- [Audit physique](md_sms_sprite8_physical_report.json) : 42048 spans de
  fond et 5376 spans de sprites verifies par signatures natives uniques,
  tous dans l'intervalle affichage coupe. Maintien BUSREQ maximal6074 ticks
  pour le fond,6060 pour les sprites. Ecart maximal entre echantillons
  prives Z80 :16815 ticks, sous la borne17100.
- Le banc complet `class0-sprite8-source-proof` conserve les768 checkpoints
  d'etat par region et relit186624 mots de fond/CRAM plus25344 mots de
  sprites, sans erreur. Chaque variante conserve48cas et2976octets PSG
  par region, aucun depart anticipe, intervalles intrarafale exacts et
  resultat identique entre noyau observateur et noyau standard.
- La reanalyse des trois anciens bancs de preparation PSG produit exactement
  le rapport precedent; les nouvelles signatures n'alterent pas leur audit.

La premiere mire de couleurs du banc avait deux erreurs : adresse calculee
avec OR au lieu d'une addition et motifs10..15 construits en chiffres decimaux.
Les anciens noyaux/captures et leurs generateurs sont conserves tels quels.
Cette mire est hors de la zone comparee. Le generateur actuel est corrige;
les couleurs de comparaison viennent d'une [ROM de calibration independante](md_sprite8_palette_report.json)
dont les16 motifs, carte et CRAM sont verifies, en PAL/NTSC.

## Limites et suite

La ROM jouable reste v0203. Ce jalon valide un moteur de rendu sur des
entrees SAT/motifs capturees, pas la production native des acteurs et de
leur SAT. Les entrees du banc ne sont pas injectees dans la RAM du jeu.
La prochaine integration doit prendre la table DD40..DDFF produite par
le moteur natif et son ombre de motifs, puis publier au bon point du cycle.

Seul le mode SMS4/192, sprites8x8 sans zoom est accepte. Le composant refuse
les autres modes. Il ne produit pas la latence des statuts collision ou
debordement du VDP SMS. Le bit de debordement fourni est une information
de rendu. Les routines du jeu, les animations, les autres modes eventuels,
le boot complet, les echeances originales, le waveform audio et le materiel
restent a integrer/verifier. Aucune nouvelle version jouable n'est annoncee.

Les preuves sont figees dans `md-sms-sprite8-v0203` avant tout nettoyage.
Les outils d'audit physique et de comparaison RGB relisent les objets
gzip verifies si les fichiers generes ont ete retires.

Archive finalisee :1608 references compressees;336712880 octets generes retires,
258688555 octets nets liberes. Reanalyse physique et comparaison RGB regenerees
depuis les objets gzip : rapports identiques octet par octet.
