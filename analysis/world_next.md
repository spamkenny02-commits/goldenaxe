# Point d'entrée pour la suite du portage



La ROM source est arrivée dans son premier écran jouable via une séquence réelle de boutons, sans modifier sa RAM. Les images et états correspondants sont dans `validation/sms-world/`. La séquence est enregistrée dans `capture.json`, et la couverture d'instructions dans `trace_counts.bin` avec les fenêtres du mapper dans `trace_windows.bin`.



Le nom choisi est `A`. Après le premier dialogue et ses confirmations aux images 2200 et 2400, la valeur de `$C01D` est `$0C` à partir de l'image 2500. Les mots à `$C0C0` et `$C0C2` valent `$0095`. Le héros apparaît au centre d'une salle extérieure avec quatre piliers et un HUD en bas.



## État actuel du code natif



`finish_name` valide le nom et `opening_dialogue` rend le premier message. Après confirmation, `enter_initial_room` charge la salle `$0095`. `move_hero` traduit la marche normale, ses collisions et le glissement ; 371 images sont identiques. `begin_room_transition`/`step_room_transition` permettent maintenant l'aller-retour horizontal `$0095 ↔ $0094` ; état, positions et images sont identiques sur 118 captures, avec tables d'arrivée identiques. La boucle `$0C` complète, les autres terrains, actions, objets et classes de salles restent à porter.



## Déplacement établi et prochaines extensions



`movement_reference.py` est une référence sémantique indépendante du chargement natif et vérifie les données SMS. `validate_movement.py` compare l'état et les images du code natif. La grille de collision est reconstruite autour de `(Y-12,X-12)`, quatre mots par ligne sur trois lignes ; les bits hauts `$20` deviennent bloquants en l'absence d'équipement de traversée. Aucun état capturé n'alimente la simulation.



La liste de sprites affiche la position de l'itération précédente, comme la liste engagée par l'interruption SMS. Les données graphiques de la pose suivante sont préparées après la simulation, mais leur transfert VDP est effectué au début de l'image suivante. Convertir les motifs après l'attente VBlank produisait des poses partiellement remplacées lorsque le héros se trouvait près du haut de l'écran. Les sprites du monde utilisent priorité Mega Drive 0, contrairement aux curseurs de nom ; cela restitue l'occultation par les tuiles SMS prioritaires.



Prochaine cible : le chargement et la simulation des objets dans `$00A4`, puis les autres directions verticales, classes de décor et portes/interactions/attaque. Le script propre à `$0095` est appelé par `$5B5A` via le pointeur de banque 2 `$B762 + salle*2` ; il vaut `$B761` (RET) pour cette salle.



## Transitions établies



- Numéros de salles horizontales : conserver le nibble haut et additionner ±1 au nibble bas ; sorties verticales : ±$10. Cas spécial du labyrinthe `$77`, routines `$21D7..$2236`, encore absent.

- Sortie gauche : clamp X=$1000 ; préparation, puis 32 pas de huit pixels vers la droite. Le héros se déplace visuellement pendant les 28 premiers pas, reste à X=240 ensuite et reprend sa simulation à X=$F000. L'état reste `$0A` pendant le défilement puis revient à `$0C`.

- Le premier départ vers le village survient à l'image 2775 ; nouvelle salle 2776 ; premier décalage enregistré dans `$C018` à 2780 ; retour au gameplay 2812. Au retour vers la droite, la préparation finale de la salle croise une interruption supplémentaire : coordonnées et animation sont déjà réinitialisées lorsque l'état reste `$0A` à 3112 ; `$0C` à 3113.

- Les motifs du héros restent ceux de la pose précédente pendant la préparation (`$C033=1`) ; la nouvelle pose n'est transférée qu'au premier pas de défilement. La pose suivante est préparée en RAM, mais le transfert natif attend `transition_step!=0`.

- Native : carte destination chargée dans les colonnes 32..63 de BG_A, largeur 64 ; défilement horizontal par ligne uniquement sur les lignes 16..175. Le HUD ne défile pas. Les commandes DMA sont engagées au VBlank suivant. Fin : copie de la carte vers les colonnes 0..31 et remise à zéro du défilement dans le même VBlank.

- Une première composition CPU de 640 cellules par image prenait plusieurs images sur 68000 : remplacée par le défilement matériel horizontal. Vertical : `world_metatiles_md` convertit les mots une seule fois ; `decode_room_map` produit directement `world_new_md`. `world_old_md` conserve la source, et vingt copies de rangées alimentent le DMA sans conversion supplémentaire. La sortie sud est vérifiée jusqu'au chargement des objets.

- Ressources extraites : 225 cartes de classe normale, 20 641 octets compressés, index de 256 entrées (offset $FFFF pour classe non prise en charge). Chaque flux produit 160 cellules. Les règles de progression `$1976`, le portail dynamique `$1A30` et les objets de chaque salle ne sont pas tous portés.



## Sortie sud : objets à porter ensuite



Scénario dans `validation/sms-vertical/capture.json` (instrumenté), `sms-vertical-check` (officiel) et `md-vertical` : après l'entrée au village, X=120/Y=88 ; maintenir Bas de 3000 à 3060. Sortie à 3045, salle `$00A4` à 3046, vingt pas de défilement, Y=$1000 à 3070. La SMS reste en état `$0A` jusqu'à 3096 pendant `$24C5`/`$1780`, puis passe à `$0C` à 3097. Le prototype passe prématurément à `$0C` à 3070 ; cette différence est enregistrée, pas comptée comme réussite.



La carte et les 102 images de 3000 à 3101 sont identiques ; les premiers objets produisent des différences à 3102. `validate_vertical.py` prouve aussi les coordonnées, poses et compteurs du héros sur les 161 images, mais signale l'entrée complète comme inachevée. Le premier objet à `$C600` devient type `$26`, flags `$28`, PV/dégâts `$02/$02`, à 3071 ; ses coordonnées sont encore nulles pendant la préparation. Identifier les huit types depuis banque 12 `$A34E + $A4*8`, traduire le chargement de motifs via banque 2 `$825F`, la remap `$1D0D`, puis la routine de type `$26` avant de revendiquer le gameplay dans cette salle.



Attention : `transition_stage=5` sert uniquement à la préparation finale du retour horizontal droit. Une valeur 3 commune aux préparations verticales interceptait à tort la finalisation Y, bien que l'image reste correcte grâce à l'offset temporaire du sprite ; la validation de position a révélé et corrigé ce défaut.



- `$24F3` : synchronisation `$0B95`, mise à jour objets `$26B6`, sprites `$0940`, HUD `$1E99`, script de salle `$5B5A`, effets `$699C`, palette `$1DF6`, transitions `$2051`.

- `$2DBE` : mise à jour du héros ; dispatch de son état via `$2EF3`. L'état initial devient `$01`, entrée `$3295`.

- `$3295` : efface les vitesses `$C314..C317`, choisit la direction par `$C020` et conserve la direction précédente si elle est encore appuyée. `$3315` contient les masques ; `$33DB` contient les séquences de mouvement et sondages de collision.

- `$C310`/`$C311` sont la position verticale en virgule fixe, `$C312`/`$C313` la position horizontale. Initialement Y=$7000, X=$8800. Direction `$C30A=1` ; graphismes via `$3B67 + direction*16`.

- `$22E2` développe une cellule 16×16 en quatre mots de tuiles. `$230E` sonde les mots de collision dans `$D600` autour du héros. Les bits hauts non VDP doivent rester disponibles au gameplay.



Attention au mapper de salle : après multiplication du numéro par deux, la banque vaut `8 + H`, mais le pointeur est lu à `$8000 + L`. Pour `$0095`, cela sélectionne la banque **9**, offset `$2A`, flux ROM `$2482F..$2488C`. Ce n'est pas une table de 512 octets continue dans la banque 8.



La pose du héros sélectionne les données à banque 4 `$83D8`, quatre tuiles à trois plans copiées vers VRAM `$3E00`. Le descripteur est indirect via banque 12 `$80A0`, direction et animation ; pose initiale `$8260`, quatre sprites, indices absolus `$F0..$F3`.



## Chaîne Z80 à porter



- `$1197..$11B7` : nettoyage de l'interface, palettes et chargement de police `$A74C` depuis la banque 4 ; message `$AB68` dans la banque 3 via `$7444`.

- État `$04`, entrée `$2433` : initialise les objets `$C300..$C8FF`, la progression du héros et ses statistiques ; appelle `$1C97` ; écrit `$0095` comme salle courante et destination.

- `$246F` : prépare la salle et ses ressources, puis charge les éléments communs d'interface.

- `$24C5` : réinitialise les objets temporaires, appelle `$1C15`, `$1780`, `$2C63`, `$5B20`, `$1CAF`, puis sélectionne l'état `$0C`.

- État `$0C`, entrée `$24F3` : boucle du gameplay à examiner ensuite.

- `$16D0..$1756` : choix et chargement des ressources de décor. `$175F` classe la salle ; `$C066` reçoit une banque dérivée de cette classe. Chargement de la palette à partir de `$8000`, RLE quatre plans vers VRAM `$0000`, RLE deux plans vers RAM `$C900`, puis traitement par `$1A30` et routines de banque.

- `$1780..$18E1` : objets de salle, tables de la banque 12, chargement et partage des graphismes des objets.

- `$2C63` et sous-routines : création et placement du héros, état de son équipement et données de collision.



Les mots de la table `$00DC` sont indexés par un **offset en octets** : état `$04` → `$2433`, `$06` → `$246F`, `$0C` → `$24F3`, `$12` → `$1101`.



Les captures servent de référence de vérification. Elles ne doivent pas remplacer le chargement des données depuis la ROM ni la traduction des routines du jeu.



## Chargement des acteurs : référence vérifiée



`tools/actor_reference.py` traduit `$1780..$18E2` depuis la ROM : effacement `$C600..$C8FF`, huit types dans banque 12 `$A34E + salle*8`, statistiques à `$A0EA + (type-$20)*4`, masque de persistance bit 7 en premier, partage des tuiles par type, RLE quatre plans et remap de palette `$1D0D`. Le traitement conditionnel de progression `$1805` reste séparé et non traduit.



Pour `$A4`, les types sont `26 26 26 26 20 00 00 00`. Type `$26` : banque 15, flux ROM `$3DEA3..$3DF43`, six tuiles, base 0. Type `$20` : banque 15, flux `$3D7B2..$3DDA1`, 55 tuiles, base 6. Les deux utilisent la remap `$20` (table `$1DC2`). Le chargement produit 61 tuiles et cinq acteurs. Comparaison exacte : 768 octets d'état à 3071 avant allocation, puis à 3097 après allocation ; 1 952 octets de VRAM à 3097. Références officielle et instrumentée identiques.



Type `$26` : `$4C78` dispatche dans banque 2 via `$8756`, états byte-offsets `0→8530, 2→8760, 4→8786, 6→878A, 8→87A1`. `$8530` appelle `$57F8` avec BC=4 pour tenter le placement. Succès : descripteur `$84FA`, période 16, quatre poses et état 2. À la pose 3, `$8760` passe au descripteur `$8624`, deux poses, état 4. Attention à `$877F` : `RST 8` renvoie un mot dans HL ; `LD (IX+20h),L` stocke le premier octet de la table `$87C4`, pas son adresse.



Le placement `$57F8..$586C` est aussi traduit avec deux valeurs de rafraîchissement explicites. Une tentative n'est permise que si `(C02F & 7) == (C046 & 7)`. Le premier `LD A,R` sélectionne une cellule `$DC00 + ((R & 7Fh)+10h)` ; les colonnes limites, terrains non autorisés et positions trop proches du héros sont rejetés. X et Y peuvent être modifiés avant un rejet. Le second `LD A,R` choisit la direction (`&3`). La première réussite à 3101 correspond à la cellule `$88`, X=136/Y=144/direction=2, avec des valeurs explicites R=78h et R=2. Cela vérifie la fonction, pas la reproduction de la séquence R.



Prochaine étape : intégrer le chargeur et les descripteurs dans le code 68000, traduire les états et collisions des acteurs, puis reproduire la source de hasard instruction-dépendante. Ne pas coder les coordonnées ou délais de ces captures comme script de salle. Le binaire natif n'a pas été modifié pendant cette étape de référence.



## Chargeur 68000 intégré



`megadrive/src/actors.c` initialise les huit acteurs de la salle en code C compilé 68000, conserve les enregistrements de 48 octets et partage les graphismes des types identiques. Les données viennent exclusivement de la ROM via `extract_actors.py` : 256 listes de salles, statistiques, 33 types graphiques (31 520 octets SMS et leur conversion Mega Drive). Le chargeur prépare `sms_vram`, `md_patterns` puis transfère les motifs par DMA à la fin du défilement. La plus grande allocation dans les 256 tables originales est de 126 tuiles (salle `$24`).



La progression conditionnelle `$1805` et la consommation temporelle du chargement Z80 restent absentes : l'intégration utilise le masque initial FFh. Les acteurs sont initialisés, mais ne sont pas encore simulés ni ajoutés à la liste de sprites. L'ancien défaut des 27 images de préparation reste signalé par `validate_vertical.py`. Ne pas confondre le chargement effectif de motifs dans le VDP et l'affichage d'acteurs.



`validate_actors.py` compare aux données calculées depuis la ROM les 768 octets d'état, l'allocation, le compteur d'acteurs, les motifs SMS préparés et les motifs convertis réellement présents dans le VDP. Cas : salle `$94` à 3000, puis salle `$A4` à 3097 et 3160. `regression.ps1` reconstruit désormais ces ressources et exécute cette validation après le parcours vertical.



## Descripteurs et rendu des ennemis



`tools/sprite_reference.py` traduit `$09EE..$0A5F` : deux indirections direction/pose dans banque 12, nombre de sprites avec bit 7 d'indices absolus, deux indices de collision, deltas Y cumulatifs et couples delta X/tuile. Les additions de coordonnées et de bases de tuiles se font modulo 256. La branche `$097E` trie les objets par Y décroissant, avec indice d'objet croissant à égalité. Les 60 états de 3101 à 3160 donnent des listes RAM `$DD40/$DD80` et des indices de collision exacts (1 004 sprites).



`add_world_actor_sprites` porte ce décodage en C natif et insère les ennemis autour du héros selon leur profondeur. Le bit 0 des flags contrôle leur visibilité. Les enregistrements initialisés restent invisibles tant que leur comportement n'est pas porté. Les descripteurs ROM `$8000..$A0E9` sont extraits comme données ; aucun interpréteur Z80 n'est ajouté.



`validate_actor_sprites.py` vérifie le moteur natif en injectant, uniquement dans la RAM de l'émulateur de test, les états SMS de l'image précédente. Les 60 listes VDP sont exactes et les 59 images disponibles à la même image source correspondent après normalisation des palettes. Ce test ne prouve pas les déplacements, décisions ou placements natifs : le rapport marque explicitement `native_actor_simulation_verified=false`. Le dossier `md-actor-render-test` et sa provenance `test_ram_writes` distinguent ce test des exécutions normales. `validate_actors.py` refuse une capture injectée. Les captures ne sont pas incluses dans la ROM ou les ressources.



Étape suivante : porter la mise à jour de type `$26` et l'animation automatique de `$26E5`, les essais de placement `$57F8` et les sondages de terrain `$48F3`, en conservant une source de hasard explicitement identifiée. Les délais de chargement et les conditions de progression restent à résoudre.



## Compteurs communs des acteurs traduits



`tick_world_actor_counters` est appelé dans la boucle native de gameplay, après la marche du héros. Il traduit les règles communes de `$26E5..$2753` pour les huit acteurs de salle : intégration de vitesses signées en positions 16 bits, annulation des fractions au dernier pas, animation automatique, délai et clignotement de blessure. Les appels de comportement, de collision et de dommages ne sont pas encore connectés.



Piège Z80 : `DEC A; JP M` saute le mouvement pour les compteurs initiaux 00h et 81h..FFh ; 80h est encore accepté (devient 7Fh). La même règle s'applique au compteur de clignotement. Le délai d'offset 06h se décrémente en sautant mouvement/animation, mais pas le clignotement. La pose n'est remise à zéro que si sa nouvelle valeur égale le nombre de poses, et non si elle le dépasse.



La référence Python compare les 48 octets du premier acteur sur les 47 étapes de 3102 à 3148. Le test natif injecte une fois son état à 3101, puis laisse le code 68000 évoluer seul : 46 octets de logique par étape correspondent exactement. Les deux indices de collision sont exclus de cette comparaison, car ils sont engagés au stade du rendu, vérifié séparément. Huit fixtures vérifient les compteurs 0/1/2/80h/81h/FFh, les fractions, vitesses, délais et clignotements. Ces fixtures sont uniquement utilisées par l'émulateur de test.



À 3148, la pose devient 3. La mise à jour de type `$26` à 3149 doit changer le descripteur en `$8624`, longueur d'animation 2, état 4 ; tenter une direction via `$4859`, puis charger la séquence de déplacement `$87CD` (32 pas, vitesse ±64 soit 0,25 pixel par image), et passer en état 8. La source choisit Haut pour le premier acteur : Y=143,75 au premier pas et compteur 31. C'est la prochaine branche à connecter, avec les tentatives de placement de l'état 0 et les décisions de direction de 4/6/8.



## États de déplacement des types 26h à 28h



`tick_world_actors` inclut désormais les états `$2/$4/$6/$8`, avant les compteurs communs. `$2` attend la pose 3 puis passe au descripteur `$8624`, deux poses et au mode depuis `$87C4`. `$4` tente une direction aléatoire et ne la change que si les limites et le terrain l'autorisent. `$6` charge la séquence de vitesse pour la direction courante et passe à `$8`. `$8` attend la fin du compteur, puis conserve la direction via `$6` ou retourne à `$4`. Un mode valant 1 devient 0 et impose `$4` sans tirer de hasard.



`$48F3` sonde le bord de déplacement dans la carte brute de tuiles : Haut/Bas combinent deux mots adjacents ; Gauche/Droite un seul. Les bits A0h indiquent le blocage habituel. Le cas spécial type 34h exige les bits C0h sur les sondages (helper traduit, comportement du type 34h encore absent). Limites : Y<25 en Haut, Y>=152 en Bas, X<17 à Gauche et X>=232 à Droite.



Type 26h/27h : 32 pas à 0,25 pixel/image depuis `$87CD` ; type 28h : 16 pas à 0,5 pixel/image depuis `$85D9`. Les sélecteurs et vitesses sont extraits de la ROM. Le premier pas est intégré dès le chargement de séquence ; à la dernière image, les fractions s'annulent.



Le hasard natif utilise provisoirement `random()` de SGDK, lu uniquement lorsque le Z80 lirait R dans ces états. Il ne reproduit pas la séquence instruction-dépendante du registre R. Le test isolé injecte une fois l'acteur à 3101 et le seed SGDK 4 (premier choix Haut), puis laisse 59 mises à jour natives évoluer : 46 octets de logique correspondent à la source jusqu'à 3160. Les indices de collision restent vérifiés séparément au stade du rendu. Trente-deux cas supplémentaires vérifient limites, murs, séquences des trois types et décisions de fin de mouvement.



L'état 0 de placement et les branches de dommages/clonage de `$4C7E` sont encore absents. Les acteurs initialisés en état 0 restent donc invisibles dans le jeu normal. Prochaine cible : placement `$57F8`, calendrier des essais et origine du hasard ; puis interaction des acteurs avec le héros et les coups.



## Placement actif dans le jeu normal



L'état 0 des types `$26..$28` est connecté à `tick_world_actors` : `$57F8` essaie un emplacement une fois par huit images pour chaque slot. La cellule est `(random() & 7Fh)+10h`, ses colonnes 0/F sont exclues, et son type doit figurer dans les quatre octets ROM `$586D`. X est écrit avant le test de distance horizontale, Y avant le test vertical ; ces mutations intermédiaires restent présentes même lors d'un rejet. La distance doit être >=16 sur chacun des deux axes. Un succès choisit la direction, ajoute les flags 03h, charge le descripteur `$84FA`, période 16/longueur 4 et état 2. Le compteur commun avance la phase dès cette image.



Le calendrier natif utilise `vtimer & 7`, compteur matériel de VBlank SGDK ; la phase initiale de `$C02F` SMS reste différente. La source de hasard demeure SGDK, donc les dates/positions d'apparition ne reproduisent pas encore la source. Le chargement natif se termine aussi plus tôt. Ces écarts sont enregistrés dans le rapport vertical : 71 images du défilement sont vérifiées ; 83 images du parcours actuel sur 161 restent identiques, les premières différences sont à 3083. Le rapport ne revendique pas l'arrivée complète fidèle.



`validate_actor_spawn.py` vérifie une exécution normale sans injection : 89 images, 712 mises à jour d'entités, consommation exacte des tirages natifs et respect des terrains/distances de placement. Les quatre type 26h apparaissent aux images 3082/3089/3092/3099 puis se déplacent ; le type 20h reste en attente. Un test isolé choisit une seed donnant les mêmes bits que le placement source à 3101, et rend le slot 0 éligible via le compteur de l'émulateur : ses 48 octets correspondent exactement. Ce contrôle valide le placement, pas une reproduction de la séquence R.



Les tests isolés d'apparition/déplacement masquent maintenant les autres acteurs pour éviter que leurs tentatives de placement consomment du hasard dans le test du premier acteur. L'exécution normale est vérifiée séparément, sans masquer ses quatre ennemis. Le test du chargeur compare tous les octets avant activation, puis seulement les champs immuables après activation, ainsi que les motifs préparés et réellement chargés au VDP.



Restent à porter : état 20h et autres familles, collision acteurs/héros, dommages et attaques, branches de clonage `$4C7E`, progression, séquence de hasard et délai de chargement original. La ROM est encore un portage incomplet, avec quatre ennemis visibles et mobiles dans cette zone.



## Types 20h à 22h et projectiles 10h à 12h



Les états `$854B..$85D5` sont intégrés : apparition commune, descripteur `$852E`, animation à deux poses/période 10, marche de 16 pas à 0,5 pixel/image. À la fin d'un déplacement, un tirage bas nibble 0/1 force un nouveau choix, 2..7 continue la direction, et 8..15 tente l'alignement au héros (colonne 16 pixels prioritaire, sinon ligne). Un alignement valide arrête les vitesses, attend 16 images en état 0Ah, puis réserve un projectile et attend huit images en état 0Ch. La saturation de sprites SMS C01B bit 40h doit encore supprimer certaines créations.



Les huit enregistrements `$C780..$C8D0` constituent la réserve de projectiles et sont maintenant mis à jour/rendus avec les huit acteurs de salle. Leurs types viennent de `$85D6` (10h/11h/12h). Un slot libre reçoit le type, la base graphique, les coordonnées entières et la direction du parent ; les autres champs sont conservés comme dans le Z80. Il est initialisé et déplacé dans la même mise à jour, car la réserve vient après les acteurs dans le parcours.



Templates `$3E53/$3E76/$3EB6` : descripteur, puissance, offset Y=-8, longueur/période d'animation et quatre vecteurs de vitesse. Initialisation : état 2, flags 13h, compteur 80h. Limites extérieures X<8/X>=248 et Y<8/Y>=152, ou compteur nul : effacement des 48 octets. Le type 12h a une animation manuelle toutes les deux images ; même après un effacement, la routine peut laisser la phase à 1, comportement conservé. Les limites de donjon et les dégâts restent absents.



`validate_ranged.py` vérifie 99 images et 1 584 mises à jour d'entités sur trois tireurs et les trois types de projectiles : créations, mouvements, animations et disparitions, puis le cas de réserve pleine (le tireur avance quand même vers la récupération). Les données proviennent de la ROM ; les états de test sont injectés uniquement dans l'émulateur. La régression complète passe. L'exécution normale contient maintenant cinq ennemis actifs dans A4 ; le rapport vertical reste incomplet (82 images identiques sur 161, premières différences à 3082, et 27 images de préparation différentes).



Observation SMS réelle : `sms-ranged-observe`, scénario habituel jusqu'à A4 puis héros immobile, captures tous les dix pas jusqu'à 4400. Un projectile 10h en slot C780 est présent de 3680 à 3750. De 3680 à 3740, 60 pas simulés reproduisent les 48 octets exacts. À 3740 : flags=13h, compteur=65, Y=25,5, X=120, vitesse Y=-384. À 3750 : flags=15h, compteur=4, Y=28,5, vitesse Y=+384 ; PV du héros toujours 24. À 3760, le slot est effacé. Le renvoi au contact du héros n'est pas encore porté ; examiner `$2346/$2768` et les branches du héros/projectile pour le reproduire avant de revendiquer le combat.





## Renvoi au bouclier : première branche de collision du héros



`$2DBE` appelle `$2346` avant le mouvement du héros, puis `$2E08` traite le contact. Le test s’exécute sur les images paires de C02F pour le héros d’indice 0. Les boîtes viennent de la ROM `$8100..$81FF` et les indices des descripteurs de sprites ; les 16 poses normales du héros conservent leurs indices extraits. Le parcours natif examine les huit acteurs puis les huit projectiles, dans cet ordre. La source parcourt aussi les slots précédents C4B0..C5D0 ; leurs comportements ne sont pas encore présents dans le port.



Les additions 8 bits et leurs retenues sont conservées : le début de la boîte cible doit produire une retenue, la fin ne doit pas en produire ; le début est strictement inférieur à la fin de la boîte du héros et la fin est supérieure ou égale au début. Un premier contact non bloquable interrompt la recherche. La cible doit avoir le flag 10h, et sa puissance ne doit pas dépasser la valeur ROM `$32269 + niveau de bouclier`. Le niveau initial C0F2=1 vaut 8. Haut/Gauche acceptent une vitesse entrante positive, Bas/Droite une vitesse négative ; une vitesse nulle ne peut pas être renvoyée. Le composant concerné est inversé, le compteur devient 10 et les flags passent de 13h à 15h (collision désactivée). Le pas commun s’exécute ensuite : compteur 9 et premier mouvement renvoyé dès cette image.



`validate_shield.py` capture une nouvelle trace SMS fine, de 3740 à 3760. Une seule injection native place le projectile C780 de 3740 et aligne le compteur : ses 48 octets correspondent aux vingt images suivantes, renvoi à 3745, dernier pas à 3754 puis effacement à 3755. Une référence séparée reproduit également la trace SMS. Dix-huit cas natifs isolés couvrent les quatre sens entrants/sortants, seuil égal de puissance, boucliers supérieurs, vitesse nulle, image impaire, délai, collision désactivée, absence de contact et priorité au premier contact. Leurs 768 octets d’acteurs sont vérifiés. Ces injections appartiennent aux tests ; aucun état capturé n’est intégré dans la ROM.



Seule la branche de renvoi réussi est portée. La marche normale actuellement portée suppose le héros en état 1 et sur terrain normal ; les restrictions originales pour l’eau et les autres états restent à connecter avec ces comportements. Un refus de renvoi ne déclenche pas encore `$37DA` (dégâts/recul) ni l’effacement du projectile de `$2E9F`. La défense, les PV, l’inventaire et le son 98h restent à intégrer. Le calendrier natif et le hasard ne reproduisent pas encore une partie SMS complète. Prochaine cible : `$37DA`, contact non bloqué et état blessé du héros, avant les attaques à l’épée.





## Blessure du héros sur terrain normal



`$2346` établit désormais le premier contact avant le comportement du héros. Il ajoute le flag 04h à la cible et calcule les dégâts à partir de la défense de la mise à jour précédente, puis `$2C8D` recalcule cette défense : `(bouclier-1)*2 + (armure-1)*4` pour l’équipement normal. Un résultat attaque-défense strictement positif est conservé, même 1 ; sinon les dégâts valent 2. Le cache de défense antérieur a été confirmé par un cas de changement d’équipement dans l’image courante. Le test séparé `validate_damage.py` couvre ce détail.



Le comportement de marche choisit la direction/vitesse avant `$2E08`, mais l’intégration de position se fait après la résolution du contact, dans `$26E5`. Le code natif sépare maintenant `move_hero` de `integrate_hero`, pour conserver cet ordre pendant un coup reçu en marchant. Un projectile non renvoyé est effacé sur 48 octets ; une cible de contact sans le flag 10h doit rester présente. Le son 91h/98h n’est pas encore porté.



`$37DA` choisit l’axe par la direction de la cible (<2 vertical, sinon horizontal), et le côté par la comparaison de leurs coordonnées entières. Un recul vers Haut/Gauche avec coordonnée <17, ou vers Bas avec Y>=160/Droite avec X>=240, retourne avant toute remise à zéro. Sinon X/Y sont arrondis par `(coordonnée+4)&F8h`, fractions, vitesses, pose et compteur sont remis à zéro, et l’état du héros devient 0. Le bit 80h du sondage de terrain interdit le décalage ; sinon il vaut ±8 pixels sur l’axe choisi. Le prochain comportement d’état 0 repasse en état 1.



La blessure charge 48 dans C305, puis le pas commun le décrémente dans cette même image : 47 et flag visible effacé. Le bit 1 du compteur règle le clignotement ; tout compteur de blessure non nul empêche un nouveau contact. `$27CF` soustrait les dégâts aux PV et sature à zéro. Le HUD `$1EEE/$1EF4` construit trois cœurs pour les 24 PV initiaux : plein 8Bh, partiel 8Fh moins la moitié des PV restants, vide 8Fh. La construction intervient à la phase 1 du cycle de quatre images ; l’image suivante présente les tuiles préparées. Le code natif suit ce délai, avec phase contrôlée dans les tests. La phase de partie complète reste à rendre fidèle.



`validate_damage.py` injecte une situation initiale identique dans les deux émulateurs, puis laisse évoluer le héros et le projectile sur 60 pas sans nouvelle injection : douze champs du héros et les 768 octets d’acteurs correspondent, les 60 mises à jour du HUD et 58 images affichées sont identiques après normalisation des palettes. Une autre exécution compare vingt et un cas contre la SMS : reculs dans les quatre directions, limites et murs, blessure déjà active, défense inférieure/égale/supérieure, dégât de 1, attaque nulle, saturation des PV à zéro, coup reçu pendant la marche, équipement modifié et contact sans le flag projectile (la cible demeure présente). Les états et cartes injectés restent exclusivement dans les tests.



L’état de mort est encore incomplet : à zéro PV le port passe en état 8 et arrête la marche, mais la séquence `$371D`, la perte de vie et le retour en jeu restent à traduire. Les équipements et défenses sont représentés pour la logique de collision, pas encore pour l’inventaire ni tous leurs graphismes. Les terrains spéciaux, dégâts du héros aux ennemis, attaques, sons et progression restent absents. Prochaine cible : mort/retour en jeu puis attaque de base et dommages aux ennemis, en conservant la comparaison avec l’exécution source.





## Mort, fondu et menu de reprise



`$2DFD` vérifie les PV après le comportement du héros : zéro charge l’état 8. À l’image suivante `$371D` passe à l’état 9, remet les vitesses à zéro, charge 90 dans C304, efface C305/C31D/C30B, active la visibilité et désactive la collision. Le pas commun décrémente le compteur dès cette image. L’état 9 conserve la pose 0 et sélectionne le bitmap par C02F bit 1. À compteur nul, il efface le flag visible et demande l’état principal 14h.



C042 est une banque graphique, pas un nombre de tuiles : `$370C` charge la banque 5 et la table `$3D77` fournit A140h/A1A1h. Les ressources effectives sont ROM `$16140..$16201`, deux flux de 97 octets (en-tête 4, puis trois plans pour quatre motifs). Le port les extrait depuis la ROM et conserve le descripteur normal 80A0h. Les sous-entités C330..C4AF effacées par `$2D7C` ne sont pas encore actives dans le port ; les acteurs de salle et projectiles continuent pendant la mort, puis se figent dans le menu.



Le cycle de palette extérieur `$699C -> bank 5 BD9B` copie quatre valeurs de `$17DB7` vers les couleurs 12..15, une fois par huit images, avec offset `(C02F & 18h)>>3`. `$1DF6` sélectionne les couleurs d’armure et alterne la couleur 31 entre 1/2. Ces règles sont désormais utilisées par le port ; le flux de compteur d’une partie normale reste différent de la SMS. Les tests de mort alignent explicitement ce compteur.



`$257D/$263E` grise uniquement les seize premières couleurs, à partir de la somme des trois composantes et de la table `$2670` : les niveaux 0/15h/2Ah/3Fh. La seconde palette est conservée pour le menu et le HUD. Le fondu `$0ACE` traite les composantes par pas 10h, 4 et 1. Chaque changement appelle `$0B92`, qui attend deux IRQ par appel (CALL 0B95 puis continuation en 0B95). Le port conserve ces deux attentes. Le sprite est masqué au premier transfert, après la dernière image visible de mort.



Le texte GAME OVER / CONTINUE / FIN vient des glyphes originaux chargés par `$0C68`, à partir des treize caractères uniques de `$267C`. Les mots de carte sont `$268A..$26B5`, le cadre mesure 11×6 et commence en D7D6h. Le port met à jour seulement ce rectangle, conformément à la commande IRQ 2, ce qui permet de reproduire son apparition. Un fond noir sur le plan B compense la transparence du curseur sur Mega Drive. Un changement de sélection est présenté à l’IRQ suivante ; Haut/Bas ne confirment pas, seules les touches d’action le font. La sélection initiale vaut 1 (reprise).



`validate_death.py` compare 92 états de mort, treize champs du héros/état principal et les 768 octets des acteurs. Les 118 images de mort/fondu/apparition du menu correspondent après normalisation des palettes. Deux scénarios vérifient 130 images de sélection, les directions et la confirmation. Une reprise restaure 24 PV, applique `(or >> 2)*3` (100 devient 75), retourne à la salle 95h avec les coordonnées initiales Y=112/X=136 et reproduit la scène finale. Le rechargement restaure les ressources, les graphismes et le fond du plan B ; les pointeurs de décompression sont réinitialisés à chaque reprise. FIN remonte les appels monde/dialogue/nom/menu jusqu’au titre natif et conserve l’or.



La reprise utilise encore le chargeur de la clairière déjà porté. Les images intermédiaires de préparation ne sont pas toutes fidèles : `$246F`, le fondu de sortie `$0B12`, puis la révélation `$1FA7..$2010` restent à intégrer à ce parcours. La table `$2011..$2050` décrit seize contours successifs, révélés toutes les deux IRQ. Le point de reprise initial est vérifié, mais les points intérieurs C0C4/C0BA et les sauvegardes ne sont pas encore portés. FIN entre dans le titre, dont le rythme global était déjà incomplet. Ces écarts figurent explicitement dans `death_report.json` ; aucune reprise entière à rythme identique n’est revendiquée.



Prochaine cible : fondu/rechargement/révélation de la reprise, puis attaques et dommages infligés aux ennemis. Le son demeure absent et le jeu complet n’est pas encore porté.


La régression du rendu a isolé six images avec des pixels du héros absents après ajout de l’animation de palette. Les descripteurs et motifs étaient exacts. Le transfert des sprites avant les couleurs, avec écriture des seules couleurs modifiées, corrige ces images. Le test de rendu contrôle sa phase initiale de palette et d’horloge ; il ne prouve pas encore le calendrier global du jeu.


La reprise au point initial traduit maintenant `$0B12` et `$0AA4` : ordre des composantes 1/4/16 vers le noir, puis 16/4/1 depuis le noir, avec deux interruptions par modification. La préparation conserve la carte complète en RAM et remplit la carte VDP avec `$18FF`, comme `$1FA7`. Les seize entrées ROM `$2011..$2050` font apparaître les périmètres selon `$1FBC..$2002` ; le fond noir de palette SMS 1 et le fond vert de palette SMS 0 sont reproduits séparément sur BG_B.

Le transfert natif regroupe les mots de chaque côté en une rangée ou une colonne. Le côté gauche passe en premier pour achever ses tuiles avant les premières lignes visibles : l’ordre Z80 case par case, reproduit naïvement avec les appels SGDK, manquait 88 pixels en haut à gauche à la dernière étape. Le résultat présenté et les cartes transférées sont identiques aux seize étapes SMS. Les transferts n’utilisent aucun état capturé embarqué.

Le chargement source bloque sa mise à jour d’horloge pendant ses sections DI. `world_clock_shift` soustrait les interruptions SGDK écoulées pendant la préparation native ; les routines de simulation consultent désormais l’octet effectif via `world_clock()`. Cela ne rend pas encore les instants de chargement identiques : le rapport conserve les paires d’images des palettes, avec un décalage d’une puis deux images en reprise. Ne pas annoncer de fidélité temporelle complète.

`validate_resume.py` compare les neuf palettes de chaque fondu, reconstitue les contours depuis la table ROM, vérifie les 768 mots de premier plan et de fond par étape dans la VRAM Mega Drive, et vérifie la même progression dans la VRAM SMS. Seize images de décor sont ensuite comparées à phase égale, sans masquer les bords. Les mutations de RAM ne servent qu’à déclencher une mort contrôlée, fixer l’horloge initiale et poser 100 pièces ; elles sont enregistrées dans les métadonnées de capture.


Les attaques entrent maintenant par la pression fraîche C de `$2DC4..$2DEE`, avec les entrées primaire `$2FAA` (état 2) et secondaire `$2FB4` (état 4). `$34A7/$34BD` passent à l’état suivant, initialisent C30E à FF, puis `$3661` lit les flux de poses `$3635/$3642/$364B/$3658`. Le flag C0EE choisit le flux rapide ; son rôle complet dans l’inventaire n’est pas encore établi. Une direction ne change que si le masque cardinal vaut exactement 1/2/4/8. Le mouvement déjà commencé demeure intégré pendant l’attaque, tandis qu’un bouton C maintenu empêche un nouveau pas normal sans déclencher une autre attaque.

`$2D8A` calcule la puissance avec `table[selected*4 + inventory[selected]]` : le deuxième `EX DE,HL` est essentiel, l’index n’est pas un groupe de cinq. L’extraction couvre les quatre variantes de la table de graphismes `$3B67` et les quatre tables de descripteurs à partir de banque 12 `$80A0`, sur huit poses par direction. Les motifs comptent quatre à huit tuiles et les descripteurs quatre à huit sprites. Les graphismes de mort ont une clé distincte 128/129, pour éviter l’ancienne confusion avec les nouvelles poses d’attaque.

Pour la collision d’un ennemi avec le héros, `$2346` utilise C31B de l’ennemi et C31C du héros, sur la parité de l’index d’objet ; les noms attaque/défense de ces champs ne sont donc pas à interpréter comme deux boîtes classiques indépendantes. La boîte du héros vient du rendu précédent, mais ses coordonnées et sa puissance viennent du comportement courant. `$23F3` accumule les dommages, écrit le pointeur C300 et ajoute le flag 04 au héros. `$2768` applique ces dommages après l’intégration et le compteur de blessure. Le recul `$2838..$28E1` suit la direction du héros, arrondit les coordonnées selon l’axe, teste les murs/limites et remet fractions, vitesses et compteur à zéro. Un coup non létal établit 32 après la décrémentation commune ; un coup létal conserve le type en offset 7 et devient type 1, état 0.

`$4C7E` est également porté : si un ennemi terrestre mode 2 survit, il passe mode 1 et copie 21h octets dans son slot apparié C780 + (index&7)*30h, avec dégâts temporairement nuls durant la copie. Les nouveaux clones sont ensuite parcourus dans le même tour. Les tableaux de tests conservent les divergences qui commencent à la prochaine décision aléatoire ; ils ne prétendent pas reproduire le flux du registre R.

Les particules de mort type 1 (`$4AEE/$4AFB/$4B30`) et l’allocation d’objets (`$4B42..$4BA3`) sont maintenant traduites. La fidélité des choix aléatoires et des récompenses de boss reste ouverte. Les tests de transformation létale, explosion et allocation sont séparés pour distinguer leurs preuves.

Pour les objets laissés au sol, `$4B30` attend la pose 4 de l’explosion (descripteur `$90CC`, cinq poses, période 4). `$4B42` applique la liste d’exceptions en banque 12 `$A26D`, la classe C0BA, puis `$A2AE` choisit seuil/type d’objet à partir d’un octet aléatoire. `$4B6E` cherche le premier des sept records libres C4B0..C5D0, écrit type/état/flags et les coordonnées entières du mort. `$57EB` efface ensuite les 48 octets de celui-ci ; C0A2 décrémente. La fonction `$04E1` fait évoluer un seed de 16 bits C028, mais retourne `R XOR L` après la mise à jour : porter le seed seul ne reproduira pas les tirages. Le nombre d’instructions exécutées et les interruptions interviennent toujours via R.

La trace instrumentée `sms-combat-trace` porte la couverture à 6 983 instructions, 14 042 octets classifiés et 5 070 points d’instruction exécutés. Elle suit la marche/attaque primaire, puis une attaque secondaire avec sélection et niveau mutés à l’image 2853. Les trois traces précédentes restent fusionnées dans le manifeste. La reconstruction exacte des seize banques demeure requise après cette extension ; les octets inconnus restent en DB.


Les sept records C4B0..C5D0 sont conservés séparément des seize acteurs C600..C8D0. Le contact parcourt les sept objets avant les ennemis et le comportement des objets est exécuté avant celui des ennemis, comme les indices source 9..31. Les boîtes de collision sont actualisées après comportement lorsque le sprite est visible, conformément à `$09EE`. Le tri de profondeur est calculé une seule fois, puis partagé par les passes avant/après le héros ; le double tri retardait le transfert SAT et supprimait une ligne dans deux images du test de rendu.

`$2907/$2926/$2939/$2946` initialise l’objet, attend le héros à l’état 1, compte 240 mises à jour, puis fait clignoter 120 mises à jour avant effacement. `$2ADD` traite le contact : pièces +1/+5 (maximum 255), vie +8/+24, magie +8, et gel avec délai 255 des acteurs de type >=20h. Les plafonds de vie/magie proviennent des capacités du héros. Les objets B/C/D partagent le style C0A3 et chargent 128 octets de motifs depuis la banque 4 ; un style incompatible efface le nouvel objet. La remise à zéro du style au chargement natif reste limitée au parcours extérieur actuellement pris en charge.

Le HUD de magie utilise l’attribut SMS 19h : son bit 0 ajoute 256 au numéro de tuile. Les mots natifs conservent ce bit. Le compteur est préparé dans la phase d’horloge 2 et transféré après le délai observé de deux images ; l’or est préparé en phase 3. Les tests suivent les états RAM et les pixels après ramassage.

Validation : six types, 40 mises à jour chacun, 228 images de ramassage ; sept emplacements remplis, expiration entière sur 370 mises à jour et 368 images ; explosion sans tirage sur 30 mises à jour/28 images ; trois scénarios de création sur quatre mises à jour. Les classes d’exception 9 (grand cœur pour tous les tirages) et 7 (aucun objet) permettent une comparaison source/native sans prétendre reproduire R. La classe générale et les autres classes utilisent encore `random()` SGDK. Le type E et les sons restent à porter.

Prochaine cible : inventaire et sélection des objets avec les commandes normales, puis autres comportements d’ennemis/interactions. La séquence Z80 R, les classes de salle intérieures, les scripts et sauvegardes restent nécessaires pour un jeu complet fidèle.


La trace additionnelle `sms-loot-trace` observe les comportements des six types d’objets, leur expiration et deux explosions. Ses initialisations contrôlées sont consignées dans `capture.json`. Fusionnée avec les quatre traces précédentes, elle porte la classification à 7 385 débuts d’instruction, 14 889 octets et 5 528 débuts exécutés. Les banques restent réassemblées octet pour octet ; cette couverture partielle n’est pas une décompilation complète.

Le test de dommages suit maintenant aussi les quatre morts létales sur 40 mises à jour chacune, jusqu’à effacement de l’acteur après explosion. Il vérifie 664 mises à jour au total dans les vingt scénarios ; les records de butin et les choix de hasard restent traités séparément.


`$2516..$2529` entre dans l’état 10h sur une pression fraîche du bouton 1. `$70F2..$7218` charge le menu natif. Les ressources banque 5 `$B609` et `$B7B5` sont décodées avec les mêmes quatre/deux flux RLE ; la carte de droite reprend huit rangées de 28 octets suivant `$7357`. La fonte `$87C6` est monochrome, masque 3, avec le plan 0 rempli. Le curseur utilise les cinq motifs banque 4 `$A4D4`, les positions `$736B` et le descripteur `$7383`. Le marqueur de carte utilise `$BC91` et la phase 04h de C02F.

La boucle `$714D` utilise B=15/C=6 : après les deux armes, elle charge quinze flags C0E2..C0F0, puis l’armure et le bouclier. Le menu affiche ainsi dix-sept emplacements d’icônes et deux équipements, même si la sélection `$72C4` est limitée à douze cases. La sélection accepte uniquement un objet possédé ; les indices 9/11 sont encore limités au parcours extérieur normal actuellement porté. `$722A` choisit l’icône selon l’arme et remappe les couleurs via `$1DD2` (table 30h de `$1D0D`).

Les motifs du menu sont convertis sur les plages 0..123, 176..207 et 496..500 ; reconvertir 512 motifs retardait l’ouverture et perdait les premières commandes. La fermeture recharge les 193 motifs du décor et le héros, en conservant la carte et les acteurs. La sélection source occupe trois images, avec deux images supplémentaires sans avancer C02F : cette pause est reproduite. Les quatre premières images de recoloration restent inexactes (116/160/175/182 pixels dans le test). Leur traitement exact requerra le calendrier des accès VDP de `$1D0D`, et ne doit pas être confondu avec les états/logiques de menu déjà concordants.

Validation d’inventaire : 89 états de curseur/objet choisi, 85 images identiques à phase contrôlée, trois panneaux avec tous les flags de possession, armure/bouclier 1..3, armes de niveaux testés, 255 clés ; fermeture par bouton 1, puis 31 états d’attaque secondaire sans mutation de sélection. Les flags de possession sont initialisés uniquement dans l’émulateur de test. Les acquisitions, scripts, usage des autres objets, salles intérieures et sons restent incomplets.

La sixième trace `sms-inventory-trace` observe l’ouverture, la sélection secondaire, la fermeture et l’attaque après retour ; seule la possession initiale de l’arme est mutée. La classification fusionnée atteint 7421 instructions, 14959 octets et 5800 débuts exécutés.

Prochaine traduction concrète : usage des objets via la table `$2EDB` désormais sélectionnable. `inventory_actions.json` conserve les douze adresses de routines. Le sort de soin (indice 7, `$3021`) passe par `$30BB`, qui soustrait le coût `$30D2[selected&3]` uniquement si la magie suffit, puis ajoute 16 PV sans dépasser C0DA (32 dans la classe C041=2 non portée). Les autres routines doivent conserver leurs propres conditions et effets, sans être ramenées aux deux attaques déjà présentes.

La régression de reprise a rencontré une capture noire initiale après l’écriture du marqueur de phase 3, avant le premier changement de palette. Elle est conservée comme `fade_in_initial_black_hold_frames`, séparément des neuf paliers. Les neuf palettes, les seize cartes/contours et seize images restent exacts à phase égale. Toutes les validations du jalon portent le même binaire, selon `inventory_milestone_audit.json`. Lors des acquisitions futures, les champs C0E0/C0E1/C0EE devront rester cohérents avec les scalaires natifs de niveau principal, arme secondaire et attaque rapide ; la possession d’autres items ne reproduit pas encore leurs effets.


Les cases 7/8 sont désormais dispatchées par la pression fraîche de `$2DC4`. La puissance C319 utilise le niveau de l’objet réellement sélectionné, et non le niveau principal pour tous les objets. `$30BB` soustrait `$30D2[selected&3]` avec refus en cas de retenue. `$3021` coûte 24, puis ajoute 16 PV et limite à C0DA sur le terrain normal ; il paie également à pleine santé. La classe C041=2 qui double l’apport n’est pas encore portée.

`$30D6/$601C` ne consomme pas la potion lorsque C318=C0DA. Sinon la vie augmente d’un point et `$1E38/$1E9C` prépare impérativement la phase santé, puis `$0B92` attend deux interruptions. Le natif conserve les acteurs pendant la boucle, force la préparation HUD à chaque point et reproduit les deux attentes. À pleine vie C0E8 est effacé, `$7226` remet C0DF à zéro et `$722A` restaure l’icône principale. La recoloration finale respecte les deux images supplémentaires qui n’avancent pas l’horloge logique, comme le menu déjà porté.

La barre santé prépare C0DA>>3 cœurs, avec les mêmes glyphes pleins/partiels/vides, et transfère ce nombre de mots. Les changements de capacité invalidant le cache sont suivis pour la vie et la magie, même si leur valeur courante ne change pas. Les cas capacité 48/vie 24 et magie 48 vérifient ces agrandissements dans les images. La capacité initiale reste 24.

Validation : 455 états/427 images pour le soin, 400 états/380 images pour la potion ; deux parcours d’inventaire par les boutons, sans mutation du choix ni de l’état d’action. Seule la possession, la vie initiale et le retrait des ennemis sont posés dans ces parcours. Le soin manque/paie avec 0/23/24/48 de magie ; les cas de vie pleine, limitation, bouton maintenu puis nouvelle pression sont inclus. Les sons et acquisitions restent absents. Prochaine cible : sorts offensifs des cases 4/5 et objet temporaire 6 avec C330 et les états héros 6/7/10/11, puis autres objets et leurs transitions.

La trace `sms-heal-potion-trace` observe un soin, puis une potion avec capacité 48 et vie 5. Les initialisations sont enregistrées dans `capture.json`. Le corpus fusionné atteint 7498 instructions, 15101 octets et 5877 débuts exécutés.


Le rechargement source `$24C5..$24CF` efface C090..C0AF par LDIR, ce qui confirme explicitement la remise à zéro de C0A3 (style partagé des objets au sol). `$24D1..$24DC` efface ensuite les sept records de butin. Cette partie du natif est donc fondée sur des instructions identifiées, et non uniquement sur l’hypothèse initiale.

La reprise avec capacité 48 a révélé C0DB=24 après Continue, même lorsque 40 points de magie étaient présents à la mort. Le natif restaure maintenant vie et magie à 24, conserve les capacités et dessine trois unités pleines suivies de trois vides. `validate_resume_capacity.py` vérifie 31 états et 31 images du HUD ; son échec précédent montrait la magie 40 au lieu de 24. Les sons, autres points de reprise et autres classes restent séparément incomplets.

L’observation du fondu natif peut interrompre sa boucle pendant l’écriture des 32 valeurs RAM. `resume_fade_step` n’avance qu’après cette boucle complète ; le test compare désormais les palettes des étapes préparées, sans classer une écriture RAM initiale partielle comme un dixième palier. La séquence de neuf paliers et les seize images finales restent exigées. Le compteur est uniquement un marqueur de diagnostic, pas une entrée de la logique de jeu.

`offensive_item_next.json` conserve les points d’entrée, descripteurs et tables de vitesse des prochains sorts. La case 4 alloue le type 3 dans C330, paie uniquement lorsque C0C6=0 puis cycle sur deux bits, et refuse si C330 est déjà actif. La case 5 alloue le type 4 et doit également traduire `$3A9A` et ses mutations de métatuiles ; un projectile visuel seul ne reproduirait pas son effet. Les deux activent les états héros 10/11, avec descripteur `$83E3`, trois phases et table de bitmaps `$3D7B`. La case 6 charge C090 depuis C0E6 et passe par les états 6/7. La physique, les collisions, le rendu et les mutations du décor doivent être portés ensemble, avec la bonne priorité d’objet C330 avant les autres acteurs.


La case 4 est maintenant native : `$3050..$30A6`, `$376C..$37B2` et `$393A..$39BB`. `world_spell_state[48]` représente C330, est remis à zéro lors du chargement de salle et est rendu avant les sept records de butin puis les seize acteurs à profondeur égale. Le lancement charge six motifs de héros par direction ; les sprites du projectile utilisent les motifs permanents B0..B9, selon les descripteurs $8411/$8419. Les collisions sont engagées après le comportement, uniquement si le record est visible ; le délai de blessure copié du héros suit `$273D..$2753`. La copie de record reste limitée aux champs natifs déjà représentés ; les autres états et données du héros ne sont pas intégralement traduits.

Les ennemis testent C300 puis C330 conformément au groupe `$242D` (neuf records source). Le natif représente actuellement ces deux candidats d’attaque ; les sept autres records auxiliaires restent absents. Le pointeur de contact `$C330` reste dans 1E/1F et détermine la direction du recul. Les 23 scénarios feu valident 1 800 mises à jour et 1 708 images normalisées. Sons et acquisitions restent absents.

Pour la case 5, `$3AA9` lit les paires ROM `$3AF7` puis `$3AFF` comme BC : premier octet signé = décalage Y, second = décalage X. `$3591` parcourt les records de quatre octets jusqu’au premier zéro. Il remplace la cellule `$DC00+index`, puis éventuellement la cellule suivante à +16 si elle correspond au troisième octet du record. `$35B7` traite séparément la cellule de progression C06E ; `$35D4` copie huit octets du métatile C900 vers deux rangées D600 et ajoute une commande 2×2 à la file C034. Le projectile doit disparaître si cette file a avancé, selon `$3A5A`. Les modifications de cellules, la file d’affichage et les conditions de progression doivent rester cohérentes ; un simple remplacement graphique serait incomplet. Ces tables sont conservées dans `offensive_item_next.json`.

Les optimiseurs GCC peuvent nommer un symbole local partagé `sms_vram.lto_priv.0`. Les lecteurs de symboles des validateurs normalisent ce suffixe avant de calculer les adresses ; cette adaptation conserve le binaire et n’assouplit pas les comparaisons d’état ou d’image.


Audit courant : `validation/fire_milestone_audit.json`, 28 rapports du même binaire, suite générale et trois tests feu avec code 0. Le parcours d’inventaire source/natif produit quatre tirs pour huit points de magie sans écrire de choix, d’état d’action ni d’horloge. Prochain contrôle transversal : une mort pendant le lancement peut laisser `hero_casting` actif dans le natif, car le passage 8→9 ne l’efface pas encore. Il faut capturer cette branche, corriger le choix de descripteur au passage à la mort, puis vérifier les interactions avec les transitions. Les tests actuels de mort commencent hors lancement.


### Reprise du 9 octobre : intro / PSG / village

Le binaire courant est de 512 Kio. `intro.inc`, `sound.inc` et `intro_data.c` ajoutent la séquence précédant le titre et le lecteur des treize pistes PSG. Les rapports `intro_report.json`, `music_report.json`, `village_doors_report.json` appartiennent au SHA-256 `23328340deb7ee7ce0eae1fbab2bb4510efb001e7618be5617f5b52f363e5be3`. Les preuves portent sur 65 cartes de récit, 23 400 états musicaux/PSG audibles et les deux parcours vers les maisons 0/2 (60 états, 42 images avec quatre motifs animés exclus). Voir les limites explicites dans ces rapports ; aucune preuve de jeu complet.

Le lecteur musical reproduit aussi le comportement inhabituel de `$8344` : la commande 83h de modulation consulte un octet à l’adresse fréquence+1 dans la fenêtre ROM fixe. `sound_low_rom` préserve les 1 025 octets nécessaires à cette lecture ; ils ne sont pas exécutés. La compensation 60 Hz est appliquée après le compteur de tempo, comme `$8000`, et les percussions ne mettent pas l’enveloppe à jour dans l’IRQ de chargement d’une nouvelle note. Le test PSG a détecté puis fait corriger l’oubli d’écriture d’une fréquence lors d’une note sans modulation.

Les portes utilisent X136/Y64 et X72/Y96 dans la salle 94. Pour la seconde, un parcours de test passe sous les obstacles : Down 2950..2965, Left 3000..3023, Up 3050..3061, puis Up 3100..3110. La sortie intérieure passe par X136/Y160. La première maison est celle de sauvegarde ; la seconde contient d’autres PNJ/objets. Les dialogues et transactions restent à traduire. `sms-shop-talk` contient des observations contrôlées par commandes normales mais la capture à 4000 peut être l’inventaire, pas un dialogue : ne pas la citer comme preuve d’un magasin.

`hero_casting` est maintenant effacé au passage de mort 8→9. Le test de retour après mort admet la séquence d’intro avant le titre, nouvellement rétablie. Le test isolé de rendu conserve 3 images avec quelques pixels différents en haut (lignes 0..6), interdit tout écart plus bas et signale `top_edge_rendering_exact=false`. La cause temporelle reste à démontrer. Corriger ces différences reste nécessaire pour la fidélité complète.


Jalon du 9 octobre — intro / PSG / village / conversations : binaire `0da4eef867f1f761afd48938e9c761d30f6e575333bfab204c5b81e47ee43000`, 512 Kio. Suite générale avec feu et quatre validations du jalon : code 0 ; audit 32 rapports de même hash, original inchangé, banques reconstruisibles. DMA_setBufferSize(2048) corrige une allocation nulle après ajout du snapshot de dialogue (taille statique 0x1c50). Six bitmaps PNJ exacts et un parcours naturel d’ouverture/fermeture ; confirmation par action et Droite contrôlée. Les états et images des maisons restent comparés à phase équivalente, avec exclusions documentées.

À poursuivre : menus de sauvegarde déclenchés par 669D (C0A7=E0/E1/E2, C01D=16h) ; achats, quêtes et autres scripts ; restauration précise des poses après dialogue / maintien de Haut ; bruitages et arbitrage ; classes de terrain et progression ; RNG Z80 R ; pixels des huit lignes supérieures et délais absolus ; somme additive standard de l’en-tête (le build actuel produit le XOR replié SGDK, explicitement contrôlé dans l’audit). Le portage complet demeure actif et incomplet.

Correctif après retour utilisateur (écran noir avant dialogue) : VDP reste actif dans le mode overlay et lors de la restauration. Le snapshot de motifs a été corrigé de `$0000..$103F` vers `$2000..$303F`, destination réelle de upload_dialog_bitmap. Validation PNJ : six bitmaps exacts, 4 096 octets des 128 motifs restaurés, fermeture Droite, parcours naturel, 162 frames VDP actif sans écran noir. Audit dédié conserve la séparation des preuves de la précédente régression complète.

Recherche sauvegarde : handler état 16h = 7390 ; table 73DD = 73E5 (sauver), 7452, 7685, 79DA. Sélecteurs AC27 donnent E=0/1/2, pas E0/E1/E2. 73E5 copie C0B0..C2FF (250h bytes) vers slots 8400/8800/8C00, met C0D9=vie, C0C2=C0BB, numéro choisi+1 à C036/8030. Portrait bank7 pointeurs AB2B : AB39/AE69/B0F1/B41C ; fond/cadre 727A, liste 782C, confirmation oui/non 6093→60F5, trois emplacements 7716. Capture source naturelle `sms-save-natural` à 3600 : menu de sauvegarde, sans injection. Code de sauvegarde natif pas encore ajouté : poursuivre cette recherche après correctif.

Sauvegarde premi�re maison d�sormais native : save.inc, SRAM impaire 8 Kio, trois slots avec payload canonique 592 octets, metadata30, s�lection Continuer et retour au village apr�s mort. Les tests couvrent trois relancements froids, choix Oui/Non, annulation, slot vide, remplacement et pr�servation des autres slots. Le VDP reste actif � l�entr�e et � la sortie du service (666 images v�rifi�es). La r�gression compl�te du nouveau binaire est encore en cours ; aucun audit final valid� avant son terme. Le handler merchant7452 (X40/Y88, E=1) et healer7685 (X216/Y88, E=2) restent � traduire ; merchant_reference.json contient les tables et une capture source contr�l�e. Les masques d�ennemis des salles non vides et la progression non port�e restent � relier � game_save_state.

Audit final sauvegarde : `validation/save_milestone_audit.json`, SHA-256 `851e84ecfa4ca8fbd169024d9e45c2c0fbadf92ee00d04f677f9f9722ac18135`, 33 rapports du m�me binaire, suites g�n�rale et intro/musique/portes/PNJ code 0. Trois slots et SRAM test�s par relancement froid. Affichage conversations : 162 frames ; service sauvegarde : 666 frames VDP actif et HUD visible. Prochaine �tape utile : marchand et soigneur dans cette m�me maison, puis autres scripts et progression. Aucun processus de r�gression encore actif.


Premier marchand natif v�rifi� : `merchant.inc`, village94 maison0 X40/Y88, clefs60 / plume60 / huile130. Acquisition cases9/2, plafond99clefs, refus de possession et de monnaie, paiement unitaire avec deux attentes, annulation et restauration. Assets ROM-only `extract_merchant.py` : portrait bank7 AE69, libell�s bank3 BED1/BEC3/BEB5 (ROM FED1/FEC3/FEB5), textes bank3. Initialement les libell�s avaient �t� pris dans bank7 ; la comparaison graphique a d�tect� et fait corriger l�adresse. La RAM D100 source est ensuite r�utilis�e par le curseur aux offsets17/19 ; comparer le bitmap rendu dans VRAM2000..303F (4160 octets) plut�t qu�exiger un scratch devenu record de sprite.

Audit `validation/merchant_patch_audit.json`, SHA `c926b3472f95e7a1ee3e3fb87b7fc6899c4f1ae126d3e314db428975a729306b`. Sept transactions contr�l�es + parcours naturel sans injection, 1554 images VDP/HUD. Cinq validateurs cibl�s code0 (marchand, sauvegarde, inventaire, portes, PNJ) ; ancienne r�gression compl�te conserv�e s�par�ment. Aucun test en cours. Prochain : soigneur7685, village94 prix table7700, portrait bank7 B0F1. Puis toutes les variantes merchant7538/75B2/75BE et autres salles/scripts, progression, bruitages, RNG, d�lais et somme additive. Le portage complet reste incomplet.


Soigneur gratuit village94 traduit : `healer.inc`, `$7685..$76FD`, portrait bank7 B0F1, texte bank3 CD3F/CCC7/CCF5. Service X216/Y88 nord. Vie=capacit�, magie/or inchang�s, Oui/Non, nuit volontairement noire et message final. Le wait_frame SGDK acc�l�re lorsque VDPd�sactiv� ; VDP_waitVInt remplace les 60 attentes de nuit, maintenant 62 frames d�sactiv�es avec la pr�paration, exactement comme les cinq cas source. La priorit� confirmation>direction du Oui/Non a �t� corrig�e conform�ment �6123 ; source Save retest�e. Parcours naturel : Up3350..3370, Right3430..3478, Up3550..3650 apr�s entr�e maison ; C4000 puisC4300 pour sortie. Aucun placement RAM dans ce parcours. Dur�e nuit62 source/natif, mais d�calage absolu +1frame explicitement rapport�.

Audit `validation/healer_patch_audit.json`, SHA `9edd80f8ff17e4500f19aebc4f25b88a24385fa0ef18f344e01652113218006e`. Sept rapports cibl�s de m�me binaire, validateurs tous code0. Tous les processus de cette passe sont termin�s ; la suite g�n�rale compl�te ant�rieure reste au hash851e84ec. Le signalement du titre a �t� retir� par l�utilisateur ("ah j�ai rien dit") ; aucune modification titre effectu�e.

� poursuivre : sortir du p�rim�tre premi�re maison/village94 en traduisant toutes les salles/services. Tables marchand794A/7538/75B2 et healer7700. Le soignant payant utilise le contr�le `#` dans son texte CC7B et un nombre indirect via DCE0/DCE4 ; le renderer partag� ne d�veloppe pas encore ce contr�le. Il faut traduire cette expansion, toutes les marchandises (bouclier, soin, huile/item2, plume/item9, clef, potion/item8), et les variantes de rechargement magique75BE. Les sept services du quatri�me s�lecteur79DA, qu�tes/progression, acquisition et monde persistent restent incomplets. Puis bruitages/arbitrage, RNGsource, d�lais globaux, rendu sup�rieur, somme additive. Garder le but du portage fid�le complet intact.


Extension portes en validation : extract_doors.py lit le pointeur de script B762+room*2, puis uniquement le pr�fixe inconditionnel LD BC/LD E/CALL6594. 134 portes, 116 salles ext�rieures, 29 int�rieurs avec sortie standard65D0. Conversion C060 = Y*8+X/4-6 : X=((BC&63)+6)*4,Y=(BC>>6)*8. Les scripts ult�rieurs/gates ne sont pas contourn�s. main.check_village_door utilise doors_data.c ; entr�e136/152, retourcoordonn�es et salle m�moris�es. Les classes de terrain/donjon et scripts de qu�te restent incomplets.

Persistance18E9 int�gr�e : game_save_state[150+room] re�oit les huit types non nuls des records primaires (slot0bit7,slot7bit0) lors du d�part de salle, lecture du masque au prochain chargement. Les records auxiliaires8..15 ne sont pas compt�s. serialize_game_save n��crase plus le masque ext�rieur avec0. Sans cette correction, le premier retour d�une porte depuis17 rechargeait les ennemis que la SMS avait retir�s. 134 entr�es/sorties contr�l�es passent, puis audit_door_masks.py compare268 octets persistants des captures. Les patterns80/01/55/AA passent aussi via fixtures de records vivants ; ils couvrent les huit positions de bit.

Une fixture suppl�mentaire FF for�ant huit records type20 arbitraires a corrompu la RAM source au-del� de la transition (room=051C,hero=1C40/1C41,state=CD). Elle n�est pas retenue comme une v�rification de gameplay valide. Ne pas pr�senter ce test comme pass� ; �tablir une fixture source l�gitime � huit records avec les compteurs/descripteurs coh�rents pour approfondir. Les captures et le log d��chec `work/door-living-mask-0xff.log` sont conserv�s. Les quatre autres configurations comparent des sorties originales effectives diff�rentes de l��tat initialFF.

Binaire courant21d50e81217ea77c1e22daa0502c46ee39795ae22ca253810bd2946c02dcc870. Handles encore � v�rifier : suite g�n�rale1347 active ; intro/musique/village67397 termin�e code0 ; portes134cas20532 termin�es code0 ; auditmasquescode0. Le full_milestone_audit ne doit �tre ex�cut� qu�apr�s r�ussite de la suite g�n�rale. Aucun audit final de ce jalon n�est encore revendiqu�.


Audit final portes/persistance : hash `21d50e81217ea77c1e22daa0502c46ee39795ae22ca253810bd2946c02dcc870`, 512 Kio, 42 rapports courants dans `validation/full_milestone_audit.json`. G�n�ral1347 et intro/musique/village67397 termin�s code0 ; portes13420532 termin�es code0 ; quatre fixtures de masques80/01/55/AA et268comparaisons de masques code0. Aucun processus de validation actif. La suite g�n�rale a ex�cut� son contenu au d�marrage ; les nouveaux tests de portes/masques ajout�s pendant cette passe ont �t� ex�cut�s s�par�ment, pas revendiqu�s comme faisant partie de son AST d�j� charg�. Les futures passes du script incluent ces tests.

Prochaine �tape : rendre les services des autres villages effectifs en d�codant leurs scripts int�rieurs. Les maisons0/1 peuvent partager sauvegarde/marchand/soigneur, mais le d�clenchement actuel reste li� au retour94. Traduire les dialogues667E par tables de retour de salle, les s�lecteurs669D, les tables marchand794A/7538/75B2 et les healers7700. Les portes simples ouvrent d�sormais ces lieux ; ne pas confondre cela avec leurs achats, scripts de qu�tes, progression ou accessibilit� naturelle enti�rement port�s. �tendre les v�rifications visuelles et les fondus une fois les scripts complets. Conserv�es : original RNG absent, SFX/arbitrage absent, acteurs conditionnels1805, variantes de terrain/donjon, rendu sup�rieur et somme additive MD � normaliser.


Current inns milestone: see [paid healer milestone](paid_healer_milestone.md) (ROM SHA-256 0eed8abc602a04228bf06a097137adac6846370dfb9bcc78decbb3373ac9ed58).


Current merchant milestone: [all merchants](all_merchants_milestone.md) (ROM SHA-256 7d4aeaa6bac07f0cdcc34f6dc20db97ed914710f8d2b906a1ddad993c101ec97).


Current save-point milestone: [all save points](all_save_milestone.md) (ROM SHA-256 e06442f35bc8d7c3f920cdeceb74008c561cb814b76fd2cdda462cbffb61e286).


Current mobile-actor milestone: [mobile actors](mobile_actors_milestone.md) (ROM SHA-256 ba3ec0e14ecedffe1f83ce30bc5347b436a270e754f0b5b2c6b2258140f39780).

Current flying actors milestone: [23..25 and13/15](flying_actors_milestone.md).

Current resting/emerging actors milestone: [2C/2E/2F and14](emerging_actors_milestone.md).

Current fixed-shooter milestone: [2D and5878 placement](fixed_shooter_milestone.md).

Current jumping actors milestone: [31/32 and30 shadows](jumping_actors_milestone.md).

Current water actors milestone: [33/34 emergence and leaps](water_jump_milestone.md).

Current hidden-trap milestone: [35, placement defaults and16](trap_walker_milestone.md).


Latest: [Mega Drive additive checksum milestone](md_checksum_milestone.md) (ROM 5d10a02a).


Latest: [Walkers36/37 and versioned ROMs](burst_walkers_milestone.md) (ROM7ab95bef).

Audio milestone: [sfx_milestone.md](sfx_milestone.md).

Version v0011: [timing_services_milestone.md](timing_services_milestone.md). Numbered ROMs: [versions](../versions/README.md).

Version v0013: [loading_timing_milestone.md](loading_timing_milestone.md).


Title cadence v0016: [details](title_cadence_milestone.md).


Title loading v0017: [details](title_loading_milestone.md).


Scroll objects v0019: [details](scroll_objects_milestone.md).


Walkers38/39 and bouncing1F v0020: [details](bouncing_shooters_milestone.md).


Charging actors3A/3B v0021: [details](charging_actors_milestone.md).


Dashing actor3C v0023: [details](dashing_actor_milestone.md).


Pursuit shooters3D/3E and1A v0024: [details](pursuit_shooters_milestone.md).


Hopping actor3F v0025: [details](hopping_actor_milestone.md).


Actors40/41 and shots1B/1D v0026: [details](ambusher_milestone.md).


Orbit actor 42 / projectile 1C and scrolling regression checks: analysis/orbit_milestone.md (v0027).


First-scene intro reveal cadence and remaining bootstrap offsets: analysis/reveal_milestone.md (v0030).


All three intro scenes measured; remaining hardware sprite-table differences: analysis/intro_scene_diagnostics.md (unchanged v0030).


Deferred intro sprite upload and remaining SAT differences: analysis/intro_sat_milestone.md (v0031).


SMS overflow-dependent projectile allocation and remaining limits: analysis/sprite_overflow_milestone.md (v0032).


All 512 actor lists/assets and dungeon walkers 43..45 / projectile70: analysis/dungeon_walkers_milestone.md (v0033). Natural dungeon progression remains pending.

See [v0034 dungeon resource/base-room milestone](dungeon_world_milestone.md). Next: entrance 6560/exit 654D, room metadata 1976, conditional cells 1A7C, class-2 scrolling and progression.


Dungeon entrances milestone v0039: [report](dungeon_doors_milestone.md). Dungeon scrolling and conditional progression remain incomplete.


Dungeon scrolling v0040: [report](dungeon_scroll_milestone.md). Next: metadata 1976 and persistent cells 1A7C/1BCD; puzzle progression remains incomplete.


Persistent room cells v0041: [report](room_cells_milestone.md). Next: natural dungeon puzzle/key triggers and persistence.


Dungeon key-door dispatch v0042: [report](key_doors_milestone.md). Next: live controller opening, repeated contact, crossing/re-entry and save/Continue verification.


Additional v0042 live key-door/Continue/cold-load checks: [report](key_door_gameplay_milestone.md). Next: 5E90/1DE2 redraw latency, room-clear and puzzle scripts.


Key-door redraw timing v0043: [report](key_redraw_milestone.md). PAL pause aligned, NTSC one frame early; upward loading still differs. Next: precise IRQ/upload phase and room-clear scripts.

Room-clear passages and dungeon floor animation v0045: [report](room_clear_milestone.md). Next: loading/animation phase, prolonged DOWN in room 17D, then clear rewards and push blocks.

Cleared dungeon loading v0046: [report](empty_dungeon_loading_milestone.md). 17D long hold now source-aligned; generic loading budget still approximate, including one-frame-late horizontal cases. Next: IRQ phase, clear rewards and push blocks.

Clear rewards and collectible keys v0048: [report](clear_rewards_milestone.md). Next: C0A8/C0A9 push-block passages and 5ECD rewards; natural progression and timing remain incomplete.

Combat shutters v0049: [report](shutters_milestone.md). C0A8/C0A9 are shutter state, not push blocks. Next: actual contact puzzles (5C96/5CFB), natural progression and remaining timing.

Contact script inventory: contact_script_reference.json (47 calls: 7 stationary passages, 1 cell mutation, 3 empty-cell triggers, 36 internal portals). Generated by tools/extract_contact_scripts.py. Not yet enabled in production. Next implement complete C0A6 flags and compare to source 5B5A, then dispatch contact routines in original order.

Complete contact flags v0050: [report](contact_flags_milestone.md). 8192 isolated cases and PAL/NTSC live cache/shutter regressions pass. Next: translate actual contact effects in source script order; internal portals need full room loading/placement.

Eleven contact effects v0051: [report](contact_effects_milestone.md). 8192 isolated cases and 44 live PAL/NTSC contacts pass; remote target-room flags and repeat guards preserved. Next: 36 internal portals with original room loading/placement/timing, then remaining puzzle progression.

Internal portal source reference (production v0051): [report](portal_source_milestone.md). 72 source scenarios and 1440 full wipe frame maps verified. No native portal implementation yet; next translate source order, twenty-step wipe, arrival and dynamic loading.

Native internal portals v0054: [report](native_portals_milestone.md). 36 portals / 72 live crossings and 1440 visible wipe frames match; resume 47 exact, 25 one frame late. Next: refine state-8 IRQ/loading phase, remaining puzzle scripts and natural dungeon progression.


2026-10-10: v0056 adds 31 stationary room puzzle scripts. See analysis/stationary_puzzles_milestone.md. 496 selected fixtures and 124 live PAL/NTSC cases match SMS states; full game remains incomplete.


2026-10-12: v0060 adds ten stationary item rewards and the 6317 acquisition frontend. See analysis/item_acquisition_milestone.md. 160 targeted grant cases, 44 live PAL/NTSC cases, 20 stable VDP/sprite checks, ten save/cold-load cases. Post-confirmation animated-floor phase offsets remain; full game incomplete.


2026-10-12: v0063 dungeon bitmap animation and item recovery: [report](dungeon_bitmaps_milestone.md). Next: natural clock reset semantics, remaining one-frame NTSC recovery, then natural progression and missing abilities. Full game incomplete.


Natural new-game clock research after v0063: analysis/world_clock_reset_research.md; validation/world_clock_diagnostic.json. PAL/NTSC original-ROM profiles confirm inter-page clock reset, distinct final any-key wait, and 29-frame-early native first-room activation. Production unchanged; implement separate waits and measured IRQ accounting next.


2026-10-12: v0064 fixes final dialogue acknowledgement inputs and stable marker. See final_dialogue_milestone.md. Next implement genuine inter-page reset/scroll, initial loader work and IRQ suppression; initial room remains 33 NTSC / 31 PAL frames early. Full game incomplete.


2026-10-12: v0070 staged dialogue scroll/renderer and free-night timing; see dialogue_scroll_milestone.md. First presentation of all four poses matches in PAL/NTSC opening test, final-pose duration still differs. Next: source 0786 post-scroll upload, genuine C02F reset and initial loader accounting. Full game incomplete.


2026-10-12: v0071 post-scroll publication, see postscroll_milestone.md. Four complete pose frame lists match in natural first-scroll PAL/NTSC test. Next measure and port source 1197..11B4 story setup (music, palette, font, fade), then C02F resets and initial loader work. Full game incomplete.


Opening setup v0076: source story entry now matches at frame 1490 NTSC / 1489 PAL. Actual CRAM 0..30 matches for 41 frames per region, and 512 original font bytes / 1024 tile pixels match. Color 31 remains phased differently. First page still 14/9 frames early, initial room 33/31 early. See analysis/opening_setup_milestone.md and versions/v0076-a171c534. Full game unfinished.


Dialogue publications v0080 (1 MiB): source punctuation, spaces and substitution boundaries restored. All 29 distinct complete first-page source bitmap shapes now occur in native VRAM, including the previously absent name-only pose. First page remains 9 frames late PAL/NTSC; initial room remains 33/31 early. Current merchant/NPC/scroll/save/free-healer and bounded movement checks pass. See analysis/dialogue_publication_milestone.md. Full game unfinished.


Dialogue controls v0082: 5C glyph-mode toggle, 24 pause/continuation, forced name mode and whole-word wrap retry ported. 26 controlled original-renderer fixtures pass PAL/NTSC; 16 identical fixtures failed on v0080. NPC/merchant/scroll/final-ack/bounded-motion regressions pass. First page remains 9 NTSC / 10 PAL frames late; first room 33/31 early. Save/free-healer evidence remains v0080. See analysis/dialogue_controls_milestone.md. Full game unfinished; inspect remaining actor/boss/quest states next alongside renderer timing.


## v0084 second offensive spell
Native slot 5 and two-probe terrain replacements added; see analysis/second_spell_milestone.md. Controlled checks: 22 spell, 20 terrain, 4 special-cell cases, PAL/NTSC. Fire has two inherited one-frame PAL state differences and known image differences. Full game and natural progression remain incomplete.


## v0089 water context and thrown axe
Native terrain-context classification, water walking/poses/collision equipment rules, and type-5 thrown axe. 54 controlled water cases and 44 existing spell cases match original states/patterns in PAL/NTSC; normal movement/scroll/enemy timing checks pass. See analysis/thrown_axe_milestone.md. Long fast boundary crossing still has a mutable-map loading-phase mismatch. Natural water routes, shoreline combat, remaining abilities, bosses/quests/ending and full playthrough remain unverified.


## v0092 water departure pose preparation
Arrival pose preparation deferred until after actor loading; six controlled down/left/right cases match source hero states/patterns and hero-only transition SAT in PAL/NTSC. Existing 54 water + 44 spell cases and ordinary timing regressions pass. See analysis/water_cross_pose_milestone.md. Both up departures remain incorrect, NTSC mutable-cell publication is one frame early, software-map staging and post-arrival enemy sprites still differ. Source upward loader/transfer timing is profiled in analysis/water_cross_source_timing.json; continue there without arbitrary frame delays. Full game remains incomplete.


2026-10-12 v0093: upward buffer-exchange work retained in native 68000; seven controlled water-departure pose/state cases pass, NTSC up remains early. 98 water/spell cases and PAL/NTSC movement/three ordinary scroll directions/eight deterministic enemy timing regressions pass on SHA 28ce141a. See analysis/up_scroll_milestone.md and versions/v0093-28ce141a. Complete game, natural route and full audio/framebuffer validation remain unfinished.


2026-10-12 v0095: original fast normal-ground table 3441..3451 ported. Running-boots acquisition and Continue now synchronize speed from inventory byte 14. 16 ground cases, 32 water cases, 44 reward cases and 10 save/cold-load cases pass; approach speeds match SMS for all 8 controlled ground departures. PAL/NTSC ordinary timing regressions pass. Ground arrival poses and NTSC upward phase remain incomplete. v0094 is an intermediate build; use versions/v0095-f2f9fdc1/gaw-megadrive-v0095.bin. See analysis/fast_ground_milestone.md. Full game remains unfinished.


2026-10-12 v0096: fixed inventory-return corruption inside village houses. show_inventory now restores the current exterior/house/dungeon background rather than always exterior patterns. Two natural village-house routes plus exterior pass static background restoration PAL/NTSC; previous v0095 reproduces large house corruption. Inventory navigation and first merchant transaction/refusal/natural-route checks pass. Four source-animated house tiles are separately recorded, not claimed phase-exact. Dungeon branch chosen correctly in code but not covered by these routes. See analysis/inventory_restore_milestone.md and versions/v0096-0faff7e5/gaw-megadrive-v0096.bin. Full port remains unfinished.


2026-10-12 v0097: corrected house bitmap animation target to scratch E0 (original C9E0 relative to C900), instead of 1E0. Four local clock-aligned house cases now match four actual VRAM patterns for 118 frames each (472 exact); previous v0096 differs on 236 of these frames. Six static inventory-return cases and first-merchant transactions/refusals/natural route pass. Full house framebuffers/global phase/all rooms and complete game remain unfinished. See analysis/house_patterns_milestone.md and versions/v0097-51363105/gaw-megadrive-v0097.bin.


2026-10-12 v0099: arrival pose initialization deferred through actor loading for both ground and water, matching 2C63/369F before 2C8D. Hero state/flags initialized with animation. PAL down publication continuation now requires a pending changed bitmap; ordinary PAL regression in intermediate v0098 removed. Fourteen of sixteen controlled directional/terrain/region cases match nine pose/state fields and actual hero VRAM patterns for 151 frames each; matching hero-only SAT during transitions. Two NTSC up cases remain wrong; ground state timing differs on two frames vs one before, although premature pose patterns improve. Ordinary PAL/NTSC movement/three scroll directions/eight deterministic enemies pass. Full game, natural shore routes, complete framebuffer/audio and all scrolling timing remain unfinished. See analysis/arrival_pose_milestone.md; use versions/v0099-eade0289/gaw-megadrive-v0099.bin.


v0100: native forest maze rule 21D7..2236 added; see analysis/forest_maze_milestone.md. 486 source/native cases and six controlled production exits in PAL/NTSC pass. Ordinary timing and inventory returns rechecked. Full natural progression and global timing remain unfinished.


v0101: conditional actor loader 1805..1838 translated; see analysis/actor_progression_milestone.md. 2248 original/native complete loader cases match. Ordinary timing PAL/NTSC, controlled forest maze, inventory returns and dungeon entry/exit regressions pass. Boss fights, progression-object behavior and collection, natural quests and complete playthrough remain unfinished.


v0105: native gem type 0F appearance/collection, nine source reward variants, persistent room/progression marking and gauge restoration; see analysis/gem_milestone.md. 26 controlled PAL/NTSC cases, 18 actual gem/reward sprite checks, 44 existing item reward cases, ordinary timing and inventory returns pass. Next: original boss-death type07 4BA4 onward (progress=1, death particles, gem creation). Natural boss victories, quests, ending, save cold-load gem progression and complete playthrough remain unfinished.


v0108: native boss-death type07 4BA4..4C5C, progression=1, 180-tick wait, bounded death particles and gem creation. Boss theme retained through death/gem wait until collection or room loading; gem collision boxes published in source iteration. See analysis/boss_death_milestone.md. 3108 original/native branch/placement cases, 24 controlled lethal-hit-to-gem chains, cap/contact and ordinary timing/inventory regressions pass. Source random stream, actual boss AI/fights and state14 ending remain incomplete. Next: type64 first boss dispatch 50D3/related bank2 state table, source RNG/refresh, progression save/cold-load and natural playthrough.

Correction to v0108 next-step pointer: type64 dispatch is 506B (not 50D3); inspect that entry and its bank2 state table.


v0110: native first boss type64 (506B -> bank2 A754), three aimed type72/five directional type73 shots; current-frame collision boxes. 1789 explicit-input original/native routine cases and six controlled PAL/NTSC production segments (308 frames, all actor bytes) pass. Ordinary timing, six inventory returns and four lethal-to-gem chains pass. See analysis/first_boss_milestone.md. Original RNG/refresh, already-full fan inherited-IY side effect, natural full fight, other bosses, ending and complete game remain unfinished. Use versions/v0110-c64afe1e/gaw-megadrive-v0110.bin; v0109 is intermediate.


v0111: native type65 boss in room0163 and eight type66 satellites (5071/A86D,512B). Movement, source bounds, orbit, shield destruction and center vulnerability translated. 1138 routine cases, 882 controlled production actor frames, two actual room-entry/load cases (47 relative frames and 20 sprite tiles) pass. First boss, ordinary timing, merchant inventory return and gem-chain regressions pass. See analysis/second_boss_milestone.md. RNG/refresh, natural full fights, other bosses, ending and complete playthrough remain unfinished. Next: type67 5193/bank2 A972.


v0112: native composite type67 boss in room0179, five delayed apparitions, three formations, damage reaction, parent-coordinated fade/removal and projectile15 firing (5193/A972). 870 explicit-input original/native cases; 584 production frames exact plus 340 appearance frames with disclosed random timer differences; two actual room-entry cases (47 relative actor frames, 24 sprite tiles) pass. First/satellite bosses, ordinary timing, inventory return and gem-chain regressions pass. NTSC destination load is one frame late in the entry fixture. See analysis/composite_boss_milestone.md. RNG, natural full fights, other bosses, ending and complete playthrough remain unfinished. Next: types68/69 fixed51AE.


v0113: native shared51AE types68/69 (rooms0175/01C3) and7A/7B dispatch, pursuit, melee, charge, rebounds and reset. 796 explicit-input cases, 772 controlled production frames, four actual room entries (47 relative actor frames,107 sprite tiles,three visible boss SAT lists each) pass. Entry loading remains1..2 frames late. Prior boss/menu/timing/gem regressions pass. See analysis/charging_boss_milestone.md including normal-charge lifetime invariant and forced inherited-E limitation. RNG, natural fights/routes, complete audio, ending and complete playthrough remain unfinished. Next:6A/6B54D3,6C54D9,6D55F1.


v0114: native burst/disappearance bosses6A/6B54D3 (rooms0180/0196) and projectile74.974 explicit-input cases,1008 clock-aligned production frames,4 actual room-entry cases (47 relative actor frames,46 tiles) pass. Unaligned NTSC projectile contact MD2977/SMS2978 and clock phase delta73 remain unresolved; diagnostic archived. Prior boss routines, ordinary PAL/NTSC timing, six inventory returns and two gem chains pass. Merchant menu fix fromv0096 retained. See analysis/burst_boss_milestone.md. Next:6C54D9,6D55F1, source clock/RNG, complete audio/ending/playthrough. Port incomplete.


v0116: native6C54D9 ten states,75 homing/return/bounce and76 animation-driven satellite paths. Removed unsupported16-part actor-renderer cap; type6C uses18 sprites.660 direct cases and1518 clock-aligned production frames pass, including injected surviving/lethal damage. Two actual room01AC entries:47 relative actor frames,81 tiles,108 ordered SAT entries exact; arrival matches in these fixtures. Prior boss/unit/burst/charging-entry/timing/inventory/gem regressions pass. Unaligned NTSC collision phase gap remains. See analysis/sword_boss_milestone.md. v0115 intermediate invisible-boss build superseded. Next:6D55F1, source clock/RNG, full audio, ending/progression/quests/natural playthrough. Port incomplete.


v0118: native6D55F1 ten states, byte-wrapped heroY-16 pursuit, three-shot cycle, shared satellites and post-state item1/level2 damage filter. Added63 shared506B/A754 dispatch with three aimed shots only; extra choice sampled only for64.482+1789 direct cases,1790+244 controlled production frames, four actual entries and198 ordered SAT entries pass. Entry still up to1 frame late; global contact phase gap persists. Prior AI/menu/timing/gem regressions pass. Audit confirms29 loaded types46..62 have no native behavior; next priority. See analysis/final_boss_milestone.md and analysis/pending_actor_types.md. v0117 intermediate superseded. Remaining dungeon AI, clock/RNG, full audio/ending/quests/saves/natural playthrough. Port incomplete.


v0125: start-menu music89 restored, inventory closeA1 removed. Playfield-only blank preserves HUD. Natural exterior/two village shops PAL/NTSC: all black frames and gameplay resume match; silent closure.13 tracks x1800 controlled IRQs pass. Inventory navigation/equipment/secondary attack and six restore cases pass.46..49 native helpers have864 isolated cases, natural production validation pending.25 remaining actor types4A..62; global clock/RNG, complete audio/ending/quests/saves/natural full playthrough unfinished. See analysis/menu_audio_timing_milestone.md. Port incomplete.


v0126: type14 aimed projectile collision descriptor now published in current frame.899 isolated46..49 allocation/state cases and936 explicitly clock-aligned production actor frames pass. Actual112 entry:94 first46 record frames,20 tiles x6 samples,24 ordered SAT entries. Random44/45 neighbors excluded. Natural menu transition/audio89/restore and ordinary timing regressions pass.25 missing behaviors4A..62 remain; global clock/RNG, natural complete fights, remaining audio/ending/quests/saves/full playthrough unfinished. See analysis/dungeon_phase_milestone.md. Port incomplete.


v0129:4A/4B native wandering, pauses and surviving-hit split up to four bodies.848 isolated768-byte cases and440 explicitly clock-aligned production frames pass, including earlier-slot allocation. Dedicated post-loop collision publication fixes newborn copy bounds. Actual125 scroll/load compares24 tiles x6 samples and60 first4A appearance records excluding random X/Y/direction; other actor records excluded.899 prior isolated cases,936 prior production actor frames, six inventory restore routes and ordinary PAL/NTSC timing regressions pass.23 missing types4C..62 remain; global clock/RNG, natural full fights/progression, remaining audio/ending/quests/saves/full playthrough unfinished. See analysis/dungeon_split_milestone.md. Port incomplete.


v0130: native4C cooldown, eight gravity-driven hops and clock-selected temporary32-byte copy (room slots only).2367 isolated768-byte cases and1148 explicitly clock-aligned production frames pass. Actual14E load compares9 tiles x6 samples and60 first4C appearance records excluding random X/Y/direction. Copy/random choices covered only by direct routines.848 prior cases,440 prior production frames, six inventory restore routes, ordinary PAL/NTSC timing and natural music89 regressions pass.22 missing types4D..62 remain; global clock/RNG, natural full fights/progression, remaining audio/ending/quests/saves/full playthrough unfinished. See analysis/dungeon_hop_milestone.md. Port incomplete.


v0131: native4D/4E roaming/border redirects, optional4E aiming, contact8-magic drain with zero saturation and flag consumption.1440 isolated actor+magic cases,1208 explicitly clock-aligned production actor/hero frames and48 contact/HUD frames pass. Source nonzero-vector bound154 updates versus4096 lifetime; forced inheritedE0..3 tested separately. Actual154/11A loads compare66/56 tiles x6 samples each and120 first-actor appearance records excluding random X/Y/direction.2367 prior cases,1148 prior production frames, six inventory restore routes, ordinary PAL/NTSC timing and natural music89 pass.20 missing types4F..62 remain; global clock/RNG, natural full fights/progression, remaining audio/ending/quests/saves/full playthrough unfinished. See analysis/dungeon_drain_milestone.md. Port incomplete.


v0132: native4F/50/51 pursuit,16-segment aligned charge and cardinal projectile18 initialization/flight/collision.1000 isolated cases and1460 explicitly clock-aligned production actor frames pass; full charge uses zero collision-map fixture. Shot chance/allocation covered only by direct routines;18 production flight injected. Actual176/122/1BC loads compare34/80/60 tiles x6 samples each and180 first-actor appearance records excluding random X/Y/direction.1440 prior cases,48 contact/HUD frames, six inventory restore routes, ordinary PAL/NTSC timing and natural music89 pass.17 missing types52..62 remain; global clock/RNG, natural full fights/progression, remaining audio/ending/quests/saves/full playthrough unfinished. See analysis/dungeon_hunter_milestone.md. Port incomplete.


v0135: native52 floor-triggered placement, emergence/aim/pause and8-magic contact. Raw cache low tile words5/6 sampled before hero movement; initial zero-cache predicate and appearance-to-aim fallthrough retained.1965 isolated actor/magic/floor cases and808 explicitly clock-aligned production frames pass. Actual119 inactive3490/armed3500 after hero-only relocation onto unchanged floor72,80; random placement delays still differ (NTSC148 source/21 native, PAL20/42).32 aligned appearance records exclude random X/Y/direction;45 tiles x6 samples match.1000 prior cases,1460 prior production frames,48 contact/HUD frames, six inventory restore routes, ordinary PAL/NTSC timing and natural music89 pass.16 missing types53..62 remain; global clock/RNG, natural full fights/progression, remaining audio/ending/quests/saves/full playthrough unfinished. See analysis/dungeon_ambush_milestone.md. Port incomplete.


[v0137] Menu89 music, silent inventory close and six natural PAL/NTSC transition/restoration routes reverified. Type53 curse/defense/remedy added:1176 routine cases,332 controlled production frames. See analysis/dungeon_curse_milestone.md; natural type53 rooms, cursed inventory phase, curse SRAM roundtrip, armor NPC cure and original RNG/clock remain unproved. v0136 superseded. Port incomplete.


[v0138] Native fixed emitters54/55 and cardinal71:1474 routine cases,1684 controlled production frames, actual143/128 fixed positions and612 tile comparisons. Prior main/actor implementations unchanged;1460 hunter and332 curse frames plus menu89 rechecked. See analysis/dungeon_emitter_milestone.md. Remaining room AI56..62 (13 types), original RNG/clock, full fights/quests/audio/ending/playthrough still incomplete.


[v0140] Native teleport56/59/5A,17/71 allocation and flash collider order.2436 routine cases;2240 controlled frames (80 exclude random parent timer4); actual12C/113/11C resources/appearance; actual12C controlled cycle192 actor/190 SAT frames, initial fixture SAT frame excluded/recorded.1684 prior emitter frames/menu89 pass. v0139 superseded. See analysis/dungeon_teleport_milestone.md. Ten room types57/58 and5B..62 plus RNG/clock, full fights/quests/audio/ending/playthrough remain incomplete.


[v0141] Native57/58 fixed proximity sentinels:1760 routine cases,996 controlled actor/HP frames; actual181/15C all48-byte relative hidden records and528 tiles. Controlled approach130 SAT/record frames after explicit animation reset; unaligned PAL58 phase differs1 tick at3610 (diagnostic retained). Actual15C park258 actor/256 SAT frames with injection SAT frame excluded. Prior teleport2240 frames and192actor/190SAT plus menu89 pass. See analysis/dungeon_sentinel_milestone.md. Eight room types5B..62, load cadence/RNG/clock, full fights/quests/audio/ending/playthrough remain incomplete.


[v0144] Native5B and hero12 grab:2780 routine cases,448 controlled frames with gold HUD/effect state; six directional edge escape, held direction counts once. Actual153 resources plus130 capture state/128 hero+thief SAT frames. Gold HUD moved after actor mutations. v0142/143 superseded. Timing/menu89 and240 loot pickup frames/228 images pass. Legacy loot expiry105-pixel gap3985 also occurs onv0141;370 loot records exact and three prior/current images identical, diagnostic retained. See analysis/dungeon_thief_milestone.md. Seven room types5C..62, RNG/clock/load cadence, natural fights/quests/audio/ending/playthrough remain incomplete.


[v0146] Native5C/5D and post-AI facing damage gate:2704 routine cases,1656 controlled frames including normal C attacks from four sides. Actual16A/129 appearance/resources and256 combat/248 hero+guard SAT frames, real terrain retained with controlled setup. A5 passage effects corrected to sourceDE08 secondary request on three paths; actual129 setup sound checks pass PAL/NTSC. Nine key-door variants,448 thief frames and menu89 regressions pass. v0145 superseded. See analysis/dungeon_guard_milestone.md. Five room types5E..62 plus RNG/clock/load cadence, full fights/quests/audio/ending/playthrough remain incomplete.


v0147: native floor traps5E/projectiles77,2029 original/native cases,1882 controlled production frames and600 actual140 actor/SAT frames in PAL/NTSC. Immutable ROM and7 current reports archived. See analysis/dungeon_floor_trap_milestone.md. Four reviewed actor types5F..62 remain; full port incomplete.


v0148: native fixed patrols61/62;2463 original/native cases,2656 controlled frames,1200 actual127/132 actor/SAT frames PAL/NTSC. ROM/sources/eight current reports archived. See analysis/dungeon_patrol_milestone.md. Two reviewed actor types5F/60 remain; full port incomplete.


v0149: native melee5F/60,1984 original/native cases,1278 controlled production frames,actual117/138 resources and attacks. Known60 PAL sprite-order mismatch at3702 retained; strict attack SAT validator fails. See analysis/dungeon_melee_milestone.md. Next: general source0940 rotation/VDP-overflow ordering. Full port incomplete.


v0152: source0940 rotating object order, visited-record count and pre-IRQ rendering context. The v0149 type60 PAL3702 SAT order gap is resolved.324 matrix SAT frames, four melee attack cases, guard/patrol/overflow/gem/inventory regressions pass. See analysis/sprite_order_milestone.md. SMS scanline pixel clipping/flicker, source auxiliary records and full faithful port remain incomplete.


Ending work afterv0152: original6EBE sequence observed through full credits/title return in PAL/NTSC. Native7027/7061 credits module matches7425 original state/row snapshots. Not yet integrated into game ROM; current numbered production ROM remainsv0152. See analysis/ending_milestone.md and immutable analysis/ending-reference-v0152. Next: ending scene orchestration, centering/gems/palette,28-row VRAM scroll and music/input return. Full port incomplete.


v0158: production6EBE ending integrated: drain,216-tick wait,hero centering,nine gem reveal,palette erase,original narrative/credits and B/C title return.7424 production credit states per region and12 normalized full scene captures exact; full death flag/profile and gameplay/menu/audio regressions checked. Initial clock alignment and residual loading/IRQ/RNG gaps disclosed. See analysis/ending_integration_milestone.md. Immutable ROM/sources/nine current reports archived. Natural complete game and full faithful port remain unproved.


v0161: house quest-giver family61F4/621E/62A9/623F integrated, equipment gifts/cure and265-byte hint supported. Cold load now reads primary offset30 independently of armor41.1836 original/native cases,12 actual gifts, long hint and six distinct-equipment/curse load cases pass; classic save/dialogue regressions pass. Animated NPC phase/publication timing remain unproved. See analysis/house_quest_milestone.md. ROM/sources/seven current reports archived. Full natural progression and full faithful port remain incomplete.


v0162: general ordinary NPC667E dialogue selection replaces six hard-coded conversations:65 original context variants/21 points,1560 original/native selection cases. ActualB3/8F263-byte dialogue bitmap/static restoration verified PAL/NTSC; prior six conversations/walking pass. See analysis/plain_house_milestone.md. Source6497 gold interaction and66B5/66F6 paid game are next NPC classes to investigate. ROM/sources/four current reports archived. Full faithful port incomplete.


v0163: house3F gold gain/loss scripts6497 ported in33 contexts.13992 source/native cases and8 PAL/NTSC live gold/dialogue/HUD/static-restoration checks pass; two-frame unit cadence and revisit guard match. See analysis/house_gold_milestone.md. Paid minigame still unported; full natural progression unverified.


v0166: paid card minigame66B5/66F6 ported natively:10-piece entry, ten cards/three ordinary draws, lucky/inverse effects, payout, replay and return.19491 original/native rule cases and12 PAL/NTSC frontend integrations pass, including inventory roundtrip after first card. Gold8 cases and existing six NPC/walking regressions pass. See analysis/minigame_milestone.md. RNG streams/global timing and full natural progression remain unproved. v0164/v0165 retained as superseded builds.


v0167: conditional6603 house dialogues ported: room02/outsideCE three before/after ninth-crystal texts and room07/outside22 once-only100-piece reward from dungeon4 flag.5040 actual SMS/native comparisons and24 PAL/NTSC live cases pass, including256-unit gold wrap, revisit guard, bitmap/static room/HUD restoration; six prior dialogues/walking pass. See analysis/conditional_house_milestone.md. Next missing classes identified: roomAF5FC7 capacity reward and room9F6036 paid passage. Full faithful port and natural progression remain incomplete/unproved.


v0170: eight fairy5FC7 life/magic contexts ported natively, including CP/SBC carry, once-only flag, special2A/1C reward icons,8-bit capacity +8/clamp128 and refill.11200 actual SMS/native cases,24 PAL/NTSC placed interactions +2 walking approaches pass;128 final HUD words and160 transformed cells exact.12 prior quest gift regressions pass. v0168/v0169 retained as superseded. See analysis/fairy_milestone.md. Next missing class: paid passage6036/616F. Full natural progression, RNG/global timing, clipping and hardware/audio/video remain incomplete/unverified.


v0174: paid passage6036/616F native, six entrances/three bidirectional links,10-piece payment then opening, destination marking and upper exit.18528 original/native cases and20 controlled PAL/NTSC integrations pass; destination enemies seeded cleared before entry. Minigame12/fairy2 regressions pass. Uncontrolled6D->96 later enemy contact differs (diagnostic retained); RNG/global timing/full natural progression still open. See analysis/paid_passage_milestone.md. v0171-173 retained as superseded.


v0175: paid-exit1DEB foreground palette restored after fade;15 fixed sprite colors exact in20 PAL/NTSC passage cases,18528 rules repeated. Earlier v0174 baseline source/regression evidence retained. Uncontrolled6D->96 still has different spawns/contact. Read-only profiles show native simulation32/28 frames early (NTSC/PAL); original foreground load2791792/2828739 T states, actors1494853. See analysis/paid_passage_palette_milestone.md. Next: source-derived loading budget and original RNG; full faithful port remains incomplete.


Loading model afterv0175: complete1780 instruction-derived cost verified over1536 original cases (six rooms,all256 actor masks);96/FF exact1494853 T states. Native hero movement before exit matches source; room ID onset differs because loader ordering. Native reveal phase3 begins4252/4248, simulation4303/4299 versus SMS4335/4327. No production ROM change. Next isolate16D0/190B/1DE2 foreground work from busy waits before integrating a loading budget. See analysis/loading-model-v0175/README.md.


Graphics/map loading research afterv0175: original0C00 model2304 cases exact; full16D0 class0/C0AC0/display-off changed-bank model36 cases exact,982060T; original2279 map preparation192686T. Thirty independent live PAL/NTSC phase comparisons exact. Source hook/DLL/tools/reports/events preserved with hashes in analysis/loading-graphics-v0175. Production ROM byte-identicalv0175; no new release. Next derive190B metadata/transforms and1DE2 HUD,then source wait/clock freeze and subtract native work before timing correction.


Map/HUD loading models afterv0175: original1E4E HUD18042 cases exact (9021 each PAL/NTSC); original190B six paid-exit rooms/all256 flags3072 cases exact under C0AC0/C041!=5. Ten live190B/HUD/VDP/palette phases exact. Full1DE2 caller excluding0B95 save/spin270284/270285T; wait6694/43640T. Prior diagnostic wait selector corrected to anchor after1DE8;1T PAL difference proven palette JR/INC branch,not quantization. Archived sources/reports/logs in analysis/loading-map-hud-v0175 with manifest. Production remains byte-identicalv0175. Next24C5/reveal orchestration,clock freeze/IRQ alignment,native elapsed work,then integration and full route/mask validation. Faithful port remains incomplete.


v0176: paid-exit loading preserves exactly one source logical-clock tick while native conversion IRQ/audio continues. Source24 actual six-route empty/full-mask PAL/NTSC exits; native3072 full-loader cases(all256 masks and clock wrap),18528 rules,20 actual payment/exit/menu integrations pass. ROM1MiB checksum351C,versions/v0176-9a4471c0; full sources/symbols/four current reports/tools/source timing evidence archived115files. Original0397 word-fill2064 cases and live1FA7 clear51628T exact. Physical loading/reveal cadence,source IRQ/RNG and natural full progression remain incomplete. See analysis/paid_passage_clock_milestone.md.


Transition timing afterv0176:24 actual six-route empty/full-mask PAL/NTSC paths;14 contiguous source phases,96 prior component comparisons exact. Fade18 frames both;source contours32 plus1 idle tick,native contour-to-idle33. Native idle6 frames early empty,7..36 NTSC/6..32 PAL early full;uniform32 delay invalid.24C5 history model24 paths/72 RNG calls exact;04E1 seed/cost exhaustive131072 comparisons,refresh output remains unverified. Script/music/return72 comparisons exact. Separate74-marker DLL/raw source-native profiles/models/tables archived109files in analysis/transition-timing-v0176; production ROM and every source file byte-identicalv0176. Next2C63 hero and source audio IRQ phase/cost,then physical loading correction with native elapsed work.

Confirmed outstanding quest-gift issue to investigate: source631A calls193D then1A7C before reward modal,while native check_house_quest currently only calls show_item_reward_text; shared modal does not mark room flag or prepare transformed cells. Fairy has its own explicit flag/prepare_room_cells path. Need compare successful quest-gift flags/cells/revisit behavior,including6451 repeat. Existing gift effect/modal tests do not prove these fields.


v0177: quest gift631A now marks outside class1 bit2 and transforms/builds room before modal backup. v0176 baseline missing flag and primary3 repeat twice reproduced/retained.32 current PAL/NTSC gift contexts(flags0/128),1836 rules,two long hints,20 paid-passage integrations pass.24 real-door cases and8 explicit C7/55 outside-context fixtures; natural reachability of latter unproved. Static cells/maps,38 held tiles,menu/second UP andone reward compare;remaining NPC animation differences retained. All other production files identicalv0176.1MiB checksum3DD6;versions/v0177-3f4dbbc9 has163 source/evidence files andsix current reports. See analysis/quest_gift_persistence_milestone.md. Exterior leave/re-entry/SRAM gift persistence and full natural progression remain open. Timing models next2C63 hero/audio IRQ,then destination/mask loading correction;source refresh RNG/clipping/hardware still unfinished.


v0177 persistence follow-up:12 actual controller exit/re-entry paths,12 full592-byte save/fresh-Continue comparisons and12 cold-house no-repeat cases pass PAL/NTSC. Six real gift doors;initial progression/door fixtures explicit. Re-entry has no RAM writes after3400;world visited1 and traversalC0EC seeded before entrance. Save transfers actual gift state to established save-point route;uninterrupted route not claimed. Cold-house mode removes3100 item/equipment/visit injections and consumes actualSRAM;zero reward phases on two UP/menu attempts. ROM/every production source byte-identicalv0177. Four added reports and278 files archived under versions/v0177-3f4dbbc9/additional-persistence;original163-file snapshot preserved. See analysis/quest_gift_persistence_followup.md. Full natural progression and physical loading/IRQ/hero/RNG/clipping/hardware remain unfinished. Next return to2C63 hero/audio IRQ cost for physical paid-exit loading budget.


v0178: paid-exit music hooks now requestB0 fade before loading andworld82 before reveal,matching16D0/1CAF. MissingB0/late82 reproduced onv0177 PAL/NTSC baseline.24 live six-route mask00/FF music cases,1800 controlled reader/PSG snapshots,3072 native loader clocks,20 paid/menu integrations pass. Onlytwo hooks change;other production sources byte-identicalv0177.1MiB checksum3DDA,versions/v0178-a8d8ee11;193 source/evidence files,five reports archived. Foreground research beforepatch archived117files in analysis/hero-init-v0177:2C63 model13150 cases/475RAMbytes,24live/144phases,and24cumulative to-fade foreground paths/72comparisons exact. No physical frame-delay integration yet. Nextsourceaudio IRQ work/phase,other missinggenericloader audio hooks(ifproved),then foreground/IRQ alignment and subtract native spentwork for loadingbudget. RefreshRNG/fullnaturalprogression/clipping/hardware remain open. See analysis/paid_exit_music_milestone.md.


v0179: standard house/dungeon doors restore exit fade,hidden load,B0/destination music,foreground palette and contour reveal. Baselinev0178 retained in analysis/standard-door-baseline-v0178. Four detailed roundtrips show9 color steps each way/16 contours32ticks;source fades18;one native PAL house exit samples19 fade-in frames with pending initial VBlank. Full physical duration remains unequal.20 dungeon paths,16 gift contexts,12 controller re-entry paths,20 paid scenarios,24 paid music paths,3072 compiled paid-clock cases and3 save slots/Continue pass. Paid music validator now bounds first exit by hero0->1 destination idle;later combat-driven re-entry commands retained separately.1MiB checksum403C,versions/v0179-d018ed93,10reports and308source/selectedevidence files verified. Onlymain.c/paid_passage.inc/newdoor_transition.inc changed;audio reader/actors/quest logic unchanged. See analysis/standard_door_milestone.md. Next model source audio IRQ cost/phase and physical loading work;also investigate pending-VBlank boundary using source gate semantics,without arbitrary fixed frame delays. RNG/combat/fullnaturalplaythrough/clipping/hardware remain open.


v0180: reveal_world initial wait now capturesvtimer,wait_frame,waits until newIRQ before enablingdisplay. Exactonlymain.c patch;globalwait/audio/loader/othermodules identicalv0179. SGDKdisplay-off VBlankstatus returns without freshIRQ;dedicated1792-call scanlinesweep(224positions xdisplayon/off xexisting/fresh xregions) reproduces216NTSC/224PAL zero-tick disabledcalls;freshgate all1tick.12baselinefiles includingharness retainedanalysis/reveal-wait-v0179. Eight standarddoor transitions nowall18fade-in frames(previousPALhouseexit19),9colorsteps/16contours32ticks.20paidscenarios,3save/coldContinue slots,16deathContinuecontourimages,31capacityHUDsamples pass.1MiB checksum442A,versions/v0180-3f155979;6reports,2158source/selectedrawfiles archivedandverified. Seeanalysis/reveal_wait_milestone.md. NextsourceaudioIRQcost/phase andphysical loadingbudget;no fixed framedelay orcomplete timingclaim. RefreshRNG/combat/naturalplaythrough/hardware remainopen.


IRQ research afterv0180: separate read-only audioirq DLL records0137/01E3/0202/0205/0226 andfull-gatedaudio calls.24 six-route mask00/FF region paths preserve originalcyclearrays exactlyagainstarchivedv0179.675audio-onlyIRQs pass4050wrapper/state comparisons;C02Funchanged,bank/SP restored,C030decrement correct. Wrapper442/454T toRET excludingreader;wholefixedoverhead524/536T. Loadingreader observed657..17835T,notpredicted. Complete16D0..0ACE IRQbudget closeswithzeroresidual on24paths using measuredreader/fullgatedspans+derivedwrapper/vector/RET.124files archived/verifiedanalysis/audio-irq-v0180;analysis/audio_irq_cost_report.json andanalysis/audio_irq_milestone.md. ROM/allproductionsources identicalv0180. Next independentlypredictbank6reader branchwork andIRQphase fromstate,thencombinewithforegroundbudget/subtractnativespentwork. No physicaldelayintegrated;RNG/combat/fullnaturalprogression/hardware remainopen. Gitlocalprojectinitialized with180ROMs,tagv0180;verify_git_roms.py checksallreleasehashes. KeepGitupdated forfuturechanges;no remoteconfigured.


Audio prefix research afterv0180: independent original807E tempo/80C8 fade models predictstate400bytes andinstructioncost,including83EF stop/mute.10240isolated sourcecases(1024tempo+4096fade perregion) exact;wholebank6unpatched,IRQsdisabled. Live6D->96/fullmask PAL/NTSC2404helpercalls(601tempo+601fade perregion) state/cost exact;cyclearrays identicalarchivedv0179.147files archived/verifiedanalysis/audio-prefix-v0180;analysis/audio_prefix_cost_report.json,live_audio_prefix_cost_report.json,audio_prefix_milestone.md. ProductionROM/everyproductionsource byte-identicalv0180 and180GitROMhasheschecked. Nextarbitration8097,dispatch80FF/B0/musicstart andchannel/envelopecosts,thenfutureIRQphase/loadingalignment. No physicaldelayintegrated;RNG/combat/naturalprogression/hardware remainopen.


Audio arbitration research afterv0180: original8097 independent state/cost model processes3requests DE06/07/08 using8AD5 priorities,DE11 threshold andDE05 command.56288isolated originalcases(allbyte requests/sixpriorities+14musicB0 x29effects x29effects xpriority0/1),cost/all400RAMbytes exact. Live6D->96/fullmask PAL/NTSC1202arbitrationcalls plus2404tempo/fade checks pass;originalcyclearrays identicalv0179.133files archived/verifiedanalysis/audio-arbitration-v0180;analysis/audio_arbitration_cost_report.json,live_audio_arbitration_cost_report.json,audio_arbitration_milestone.md. ROM/allproductionfiles identicalv0180;180GitROMhashesverified. Next80FF dispatch(B0/musicstart/SFX) thenchannels/envelopes tocomplete futureaudioIRQcost prediction beforephysical loadingalignment. SourcefreshRNG/combat/fullnaturalprogression/hardware remainopen.


Audio dispatch research afterv0180: independent80FF state/cost model covers13music starts,29effects,80idle,B0fade/B1stop/B2release/B3restore andlow/highreset branches.48000isolated originalstates pass400RAMbyte/cost checks;8noiseownershipflags x4DE0F x3DE0E patterns. Excludes8E/8F,AD/AE/AF andB4(jump7000 inside unrelatedfixedROM instruction). Live6D->96/fullmaskPALNTSC4808four-helper predictions including1202dispatchcalls and3606consecutive-state links exact;commands80/B0/82/98;cyclearrays identicalv0179.134files archived/verifiedanalysis/audio-dispatch-v0180;analysis/audio_dispatch_cost_report.json,live_audio_dispatch_cost_report.json,audio_dispatch_milestone.md. ProductionROM/allsources identicalv0180 and180GitROMhashesverified. Next7channel/envelope paths plusreaderentry/regiongating tofinishfutureaudioIRQcost prediction,thenphysical loadingalignment. RNG/combat/fullnaturalprogression/hardware remainopen.


Envelope research afterv0180: independent854B ADSR andtable models predict400RAMbytes,A andinstructioncost;tables alsoDE/caller-frame unwind.80384isolatedADSRcases and26800tablecases(all16tables/allvalidstreamoffsets,explicitDE0x8A0B/899E/89A1) exact PAL/NTSC;2160unitunwinds. Table83 reads(++DE),notassumedadjacentoperand;arbitraryuncapturedRAM remainsunsupported. Live6D->96/fullmask1932NTSC+2313PAL=4245envelopecalls exact incl820+981=1801unwinds,originalcyclearrays identicalv0179. Live modes0/1/2/6/7/8/16;noADSRobservedonthisroute.157files archivedverifiedanalysis/audio-envelopes-v0180;analysis/audio_envelope_milestone.md andthreecurrentreports. ProductionROM/allproductionfiles identicalv0180,180GitROMhasheschecked. Nextpitch82C5,sequence8357/8365 andchannel84C7/864F plusreaderentry/regiongating,thenfutureIRQ/physical loadingprediction. README nowconciseUTF8,currentROMblockauto-updated;updateitsworkparagraphratherthanappendingtechnicaljournals. Gitlocalonly,no remoteconfigured.


Git instruction: user explicitly requests staying LOCAL for now;allproject will be copied to a NEW repository later. Existing GitHubspamkenny02-commits/goldenaxe has an independentV51src/md/tests implementation,not an ancestor of thisSGDKproject. Fetched/read-only comparison anddry-run only;NO PUSH performed. Origin removed topreventconfusion;localbranch renamedmain;alllocalhistory/180ROMs retained. Do not sync/push tooldGitHubrepo. Pitchresearch now118800unitcases+181livecost/state/HL comparisons;liveonlymode0,unwind81/82unverified.138files archivedanalysis/audio-pitch-research-v0180,productionidenticalv0180. Nextsequence8357/8365 andchannel84C7/864F +readergating.


v0181: actual8357 raw16-bit note path83D1..83EC always jumps839B duration multiply,evenwhenbit7set. Prior nativecommonif(note&128) reusedduration/rewoundcursorincorrectly. Original8357 vs compiledproductionnativeharness1080boundarycases reproducedallmismatchesv0180;13baselinefiles preservedanalysis/raw-note-duration-v0180. Corrected onlysound.inc durationreusecondition toexclude non-noise rawmode8;all400audioRAMbytes exact on1080currentcases.13music23400+29effects19140+87/B0/82fade1800=44340IRQreader/audiblePSGregister snapshots pass. Nativeharness/allresourcesunmodifiedproduction;fixturesreadactualROM8421 bytes21,3D,84 as rawtone;naturalreachabilitynotclaimed.1MiB checksum686D,versions/v0181-97313b55,5reports/114source-selectedevidencefiles verified. READMEcurrentversionauto-updatedandcorrectionlisted. Nextcontinue original8357/8365 ordinarynotes/commands/channelcostprediction;physical loading/IRQ/RNG/fullnaturalprogression/hardware remainopen. Stay LOCAL main,no remote/push;newrepo laterperuser.

2026-10-15: original8357 notes/control cost model: 103424 unit cases,384 F1/F2 DE0E=0 termination cases,212 live6D->96 calls exact PAL/NTSC. Evidence: audio_note_sequence_milestone.md. v0181 unchanged. Remaining restoration8211,other commands,noise864F,whole channels/reader then physical loading integration.

2026-10-15 v0182: native F3 ownership termination corrected,400 source/native cases (120 prior mismatches,zero after),44340 audio regression snapshots pass.20 deterministic commands59904 source cost cases,F3 ownership3840 cases pass;R-dependent commands,EF data target,restoration8211 and noise/full channels/reader cost remain open. See audio_ownership_milestone.md.

2026-10-15 v0183: borrowed-noise rest preserves PSG output, matching863E.18432 source/model/compiled-native cases:400 RAM bytes/helper Tstates/noise PSG registers exact;baseline144 PSG divergences (RAM already matched).13 music/29 SFX/fade44340 regressions pass. Next864F full noise channel,other channels/reader/IRQ loading costs. See noise_note_milestone.md.

2026-10-15: original864F noise-channel cost composition:39360 unit cases +1102 live6D->96 calls exact400 bytes/Tstates,PAL/NTSC;F6/F7 included,zero ignored live calls,sourcecyclearrays equalv0179. ROMv0183 unchanged. Other noise commands,whole tone channels/reader and physical loading integration remain open. See audio_noise_channel_milestone.md.

2026-10-15: original84C7 tone-channel cost composition:20680 sampled unit cases +3372 live6D->96 calls exact400 bytes/Tstates,PAL/NTSC;zero ignored calls. Livepitchmode0,5 channels active (DF60 absent),envelopes2/6/7/8/16;unitpitch0/1/128. ROMv0183 unchanged. Next fullreader81F8/restoration8211/R-controls/gating,then physical loading integration. See audio_tone_channel_milestone.md.

2026-10-15: original8000 reader composition:1202/1202 live6D->96 calls exact400 bytes/DE/Tstates,all IRQ1A2/1A5 and202/205 spans counted;33480 priority-effect cases and10752 reader-gate cases pass. Tone20680/noise39360 matrices also verifyDE (ADSR D/E effects modeled). ROMv0183 unchanged. Remaining R-controls/standalone8211/non-F6F7noise/other contexts;next physical IRQ/loading integration. See audio_reader_milestone.md.

2026-10-15: 24 paid exits,13725 observed0B95..0BB3 waits match170T beforeEI +4EI +29N +24final;stack22,C02E0,clock+1.14424 full8000 reader calls exact. Complete16D0..0ACE foreground (including both waits) closes;audio-onlyIRQ costs predicted,full-gatedIRQ spans still observed. ROMv0183 unchanged;next fullIRQVDP/palette/Vcounter and raster phase before native timing integration. See save_wait_milestone.md.

2026-10-15: originalfull-gatedIRQ0137..01E2 model:13749 live calls/24paths +2880 isolated cases exact9 stages/336 RAM bytes. Complete conditional16D0..0ACE wall budget now closes with foreground/waits +675 predicted audio-onlyIRQs +48 predicted fullIRQs;14424 readers exact. Palette/wait branch decisions,IRQchronology,inputports/historyRNG remain observed inputs. Next future raster/IRQ phase and polling prediction before native delays. ROMv0183 unchanged. See full_irq_milestone.md.

2026-10-15: palette0186 loop decisions predicted from IRQ-entry raster phase/prefix costs on13749 calls/24paths;zero observed loop counts as prediction inputs.149500 controlled VC mappings match actual GPG vdp_hvc_r. Conditional loading budgets still exact with predicted palette loops. EntryIRQ phase,0B95 decisions/historyRNG remain observed. Next wait-entry phase +IRQ latch/IFF/state snapshots to predict0B95 waits,future interrupt scheduling/native integration. ROMv0183 unchanged. See irq_raster_milestone.md.

2026-10-15: 0B95 wait scheduling predicted from post-interrupt-check entry phase/latches/IFF +336RAM/400audio bytes:13725 waits/24paths exact loops/wall/IRQ costs/accept offsets/clock;6156 synthetic DI/EI/pending contexts pass including PALlatched andprefix audio->full IRQ.24 loading budgets still exact with predicted waits/fullIRQ cost. Entry phases and foreground-between-wait IRQchronology/historyRNG still observed;next foreground phase prediction/native integration. ROMv0183 unchanged. See wait_raster_milestone.md.

2026-10-16: single-entry 1FA7..0ACE phase prediction validated on 24 paid exits and 7220 isolated contexts. Five checkpoints and all IRQ offsets match; source traces equal v0179. Status-read VINT suppression and vector acknowledgement coalescence covered. Entry to second wait is predicted rather than observed. Source native files unchanged; ROM v0183. Earlier loading/history RNG and native timing integration remain open. See reveal_phase_milestone.md and reveal-phase-research-v0183.

2026-10-16: single-entry graphics-prefix 16D0..1706 phase prediction validated on all 24 paid exits. Original pattern RLE instructions, DI/EI boundaries, C031 writes and B0 request timing independently produce wall time, final phase, 331 RAM/400 sound bytes and all IRQ offsets. No observed future IRQ schedule used. Native ROM v0183 unchanged. Next: 1706 onward RAM metatiles, terrain and map/HUD phase propagation. See graphics_prefix_phase_milestone.md.

2026-10-16: complete class0 graphics routine 16D0..24B9 now predicts six checkpoint phases/states and all IRQ offsets on 24 paid exits from one entry snapshot. RAM plane decoder, extra metatiles, terrain and DI/EI SRAM copy are instruction-planned. No intermediate observed inputs used. 331 RAM bytes/400 sound bytes compared at each point; decoded RAM/VRAM/SRAM data outside snapshot excluded. Next: map190B/HUD and actor/history phase chaining; native ROM remains v0183. See graphics_load_phase_milestone.md.

2026-10-16: chain16D0 graphics through190B map return24BC verified on24 paid exits at9 checkpoints. Phase/331 RAM/400 audio/all IRQ offsets predicted without intermediate snapshots; room andpersistent bit0 supplied. DefaultFF coordinate copies decoded motif0 (XOR A at1AB4) into DDBC/DDFC queue area; modeled without RAM exclusions. Diagnostic D0F8 captures are unused inputs. ROM004D mask annotation corrected. Native v0183 unchanged; next HUD/save-wait phase andactors/history. See world_map_phase_milestone.md.

2026-10-16: graphics/map/HUD chain16D0..24BF matches24 paid exits at16 checkpoints,including computed0B95 entry andfullIRQ VBlank wait,DI map transfer/status acknowledge andpalette restore. 16HUD bytes from16D0 supplement336 RAM/400 audio; no intermediate observed phase/IRQ chronology used. Gauges/room map instruction plans close existing cost totals. NativeROM v0183 unchanged; next actor clear/history/R-based RNG andactor/hero/setup tail phase. See map_hud_phase_milestone.md.

2026-10-16: original04E1 output/R sample/return R/seed/cost verified in135168 isolated cases (all65536 seeds plus256R for8 seeds,PAL/NTSC). Local entry-after-M1 contract:17/18 further fetches tosampleR,21/22 total routine fetches. 72 live history calls on24 paths match,none interrupted; entryR still observed. GPG IM1 acknowledge has no explicit R increment,hardware convention remains unproved. Next: predict refresh through foreground andreader/IRQ paths before native RNG replacement. NativeROM v0183 unchanged. See rng_refresh_milestone.md.

2026-10-16: M1 fetch-count models for original tempo807E/fade80C8/stop83EF/arbitration8097 pass66530 isolated PAL/NTSC executions. Absolute read-only M1 counter,logical R delta,cost/all400 sound bytes compare. Stop includes394 LDIR and10 OTIR repetitions:829 fetches. No native changes; dispatch/channels/IRQ wrapper plusforeground refresh progression remain open before RNG replacement. See audio_prefix_refresh_milestone.md.

2026-10-16: original80FF dispatch and81F8 priority effect/restoration M1/R models pass81480 isolated PAL/NTSC cases (48000 dispatch,33480 priority). Compare absolute fetch count,R delta,cost/all400 state bytes. Shared8424 lookup9 and81CA copy40 M1,83EF stop829 M1. Existing supported command boundaries retained. Next: channel/envelope/sequence andIRQ wrapper M1 composition beforefull load refresh prediction. NativeROM v0183 unchanged. See audio_control_refresh_milestone.md.

2026-10-16:854B ADSR/table envelope M1/R models pass107184 isolated PAL/NTSC executions (80384 ADSR,26800 tables),including2160 caller-frame unwinds. Absolute M1,logical R,cost/all400 state bytes,A/DE/unwind compare. Original routines/bank6 intact; explicit DE caller input. Next: pitch/sequence andcomplete channel/IRQ M1 composition; no full loadR ornative RNG replacement yet. NativeROM v0183 unchanged. See audio_envelope_refresh_milestone.md.

2026-10-16:82C5 pitch/vibrato M1/R model passes118832 PAL/NTSC original executions,including32 positive unwind probes. RawM1/logicalR/cost/all400 sound bytes/HL/unwind compare; tableDE checked. Synthetic modes41/index127 and45/index21 use unchanged ROM pointers/bytes81/82;not claimed valid music metadata. Next: note/sequence commands andfullchannel/IRQ M1 composition beforeloadR/native RNG replacement. NativeROM v0183 unchanged. See audio_pitch_refresh_milestone.md.

2026-10-16:8357 notes/deterministic sequence M1 model passes167552 PAL/NTSC original executions,including816 caller unwinds. Exact prior fixture hashes replayed;absoluteM1/logicalR/cost/all400 sound bytes/DE/unwind compare. Generated semantic model audited to cost-planSHA,three BIT(HL)12T overrides andexplicit duration-multiply fetch loops;deterministic regeneration verified. R-based commands andnonzero8211 restoration remain unsupported. Next fullchannel/IRQ fetch composition andload-entryR;native v0183 unchanged. See audio_note_sequence_refresh_milestone.md.

2026-10-16:84C7 M1 composition (sequence/pitch/envelope pluswrapper) passes20680 isolated PAL/NTSC executions and3372 live6D->96/full-mask calls. RawM1/logicalR/cost/all400 sound bytes/DE/unwind compare. Live old824-byte records byte-identical andsourcecycle traces equalv0179;observed livepitch0. Live R delta=helperM1,unit CALLentry delta=M1+1. Generated model SHA audit/deterministic regeneration checked. Next noise/whole reader/IRQ M1 andload-entryR;native v0183 unchanged. See audio_tone_channel_refresh_milestone.md.

2026-10-16:864F noise M1 composition (8679 note/envelopes pluswrapper) passes39360 isolated PAL/NTSC executions and1102 live6D->96/full-mask calls. AbsoluteM1/logicalR/cost/all400 state/DE/unwind compare;old824-byte captures identical andsourcecycles equalv0179. Explicit dispatch aggregates109T=15M1 and18T=2M1;duration count reused. F6/F7 supported,other noise commands open. Next whole reader/IRQ M1 andload-entryR;native v0183 unchanged. See audio_noise_channel_refresh_milestone.md.

2026-10-16:8000 complete supported reader M1 composition passes10752 gate/compensation unit cases and14424 livecalls on24 paid exits. Allprefix/channel counts+wrapper instructions independently produceM1;R/cost/all400 state/DE compare. Prior824-byte records identical,sourcecycles equalv0179,both IRQcallreturn sites checked. Initial readerR observed;next IRQ wrapper/fullIRQ andforeground fetch progression forload-entryR. Unsupported commands/restoration remainopen;nativeROM v0183 unchanged. See audio_reader_refresh_milestone.md.

2026-10-16:0137..0226 audio-only wrapper M1/R stage model passes15360 isolated cases(all256 C030 counters) and675 live audio-onlyIRQ spans across24 paid exits. Six38..42 vector instructions andreader verified on14424 events. OldIRQ/state/readerM1 records identical,sourcecycles equalv0179. LiveC030 allzero;nonzero branch covered byunit. LocalGPG IM1 acknowledgeR increment unproved/notadded;finalRET livepoint is beforeexecution,unit verifiesit. Next fullgatedIRQ/foreground M1 forload-entryR;nativeROM v0183 unchanged. See audio_irq_refresh_milestone.md.

2026-10-16: Full gated IRQ M1/R composed across nine stages; 2880 controlled cases and 13749 live calls / 24 paths exact. Raster palette predicted; prior state/cost/reader captures and v0179 source cycles unchanged. Entry R/raster/input remain observed; foreground refresh/actor-history propagation and native integration still pending. ROM v0183 unchanged. See full_irq_refresh_milestone.md.

2026-10-16: Graphics prefix 16D0..1706 now predicts M1/R from single observed entry with scheduled audio IRQs: 24 paths exact, 122703 foreground M1, NTSC 5484 IRQ M1/15 IRQs, PAL 5604/13. Old phase/state captures and v0179 cycles unchanged. Explicit RES7,B vs terminal DJNZ distinction. Remaining graphics/map/HUD/waits/actor-history refresh propagation and native integration pending. See graphics_prefix_refresh_milestone.md. ROM v0183 unchanged.

2026-10-16: Class0 graphics refresh composed 16D0..24B9 from one entry state: 24 paths / 144 checkpoints exact M1/R/phase/331RAM/400audio. 137614 foreground M1, NTSC 6250 IRQ M1/17 IRQs, PAL 6132/14. Includes RAM planes, metatiles, terrain and DI/EI SRAM copy. Prior raw captures/sourcecycles unchanged; default timing regression passes. Map/HUD/waits/actor-history and native integration pending. ROM v0183 unchanged. See graphics_load_refresh_milestone.md.
