# v0275 : plage des lectures directes de R pour les directions

Le sélecteur SMS 4EB7 lit R en 4EBE et compare la valeur à 32 avant de choisir
une direction libre ou la table de virages. Le port lui fournissait parfois
un octet SGDK de 128 à 255. Pour le démarrage de référence sans BIOS, R7 est
nul : RESET remet R à zéro et seuls les sept bits bas s'incrémentent. La ROM
originale ne contient aucune instruction LD R,A (ED4F).

Source primaire : [Zilog, Z80 CPU User Manual UM008011-0816](https://www.zilog.com/docs/z80/um0080.pdf),
pages imprimées 3 (registre R) et 6 (RESET). Le reset du coeur de référence
initialise également ses deux parties de R à zéro. Ce constat ne couvre pas
une précondition de registre imposée par un BIOS externe ni le matériel réel.

La production projette désormais les entrées directes de R sur sept bits :
47/48/49 via dungeon_phase_move, et le boss 65 via son dispatch. La pause A935
du boss utilise le même domaine ; son masque suivant de six bits conservait
déjà la même durée. Les paramètres explicites des bancs de routines restent
inchangés. Les portes 04E1 (4DB0 et A921) conservent leur octet complet.
L'historique des salles et les autres appels au générateur ne sont pas modifiés.

Il s'agit d'une correction du domaine des entrées provisoires. SGDK produit
encore les tirages : cette version ne reconstruit pas la valeur de R depuis
le compteur de frames et ne prétend pas reproduire le flux R/IRQ de la SMS.
La fréquence réelle des branches dépend de ce flux ; aucune uniformité de
R n'est supposée ou démontrée par les comptes de cas contrôlés.

## Vérification

- tools/validate_refresh_domain.py compile les corps C réels et compare les
  directions à 4EB7/4E0A exécuté sur Z80. Seuls les deux points d'entrée R sont
  remplacés par des valeurs contrôlées. 36 864 cas couvrent trois types,
  huit directions précédentes, trois positions, les choix pair/impair et les
  256 octets SGDK projetés. Les vecteurs proviennent des tables ROM originales.
  2 464 directions diffèrent du calcul avec entrées non projetées.
- tools/validate_refresh_domain_game.py exécute 26 cas du binaire jouable en
  NTSC/PAL, avec graines SGDK et entités contrôlées. Les branches, directions,
  vecteurs et le nombre/ordre exact des appels sont vérifiés. Le cas porte
  04E1 = 128 confirme qu'elle reste sur huit bits et déclenche le mouvement.

La ROM fait 1 Mio, SHA-256 02b597b346e3518670f93e1cfc5281a9db6a6cfbfbe2a70139ef18b11f05a5c5,
checksum 8042. Les anciennes ROMs sont conservées. La campagne naturelle complète
sur ce nouveau binaire, l'horloge globale, les formes d'onde et le matériel
restent non validés ou incomplets. Les anciens parcours v0274 restent des preuves
propres à leur ancien SHA ; ils ne sont pas réattribués à la v0275.
