# Golden Axe Warrior — portage Mega Drive



Objectif : reconstruire le jeu de la ROM fournie et porter sa logique Z80 vers du code natif 68000, avec SGDK pour le matériel Mega Drive. La fidélité passe avant les améliorations.



**État du 9 octobre 2026 : portage natif partiel. Intro avant le titre, lecteur musical PSG, accès aux deux maisons du village et six conversations de villageois, titre, menus, premier dialogue, déplacements et transitions extérieures, six types d’ennemis, projectiles, bouclier, attaques primaire/secondaire, dommages, mort/reprise, premiers objets au sol, menu d’inventaire, soin, potion et sort de feu sont traduits. Le jeu complet n’est pas porté.**



## Résultats disponibles



- `gaw-megadrive.bin` : ROM Mega Drive de 512 Kio. Elle affiche le titre, permet de passer au menu, saisir un nom, lire le premier dialogue et déplacer le héros dans la salle initiale `$0095`, avec HUD. La marche sur terrain normal et ses collisions sont traduites ; les passages horizontaux vers le village `$0094` et le retour sont vérifiés. Le chargeur natif initialise les ennemis et leurs tuiles ; le moteur de sprites et les premiers états de déplacement sont intégrés. Les types $20..$22 et $26..$28 apparaissent et se déplacent dans le jeu normal ; les premiers peuvent tirer des projectiles. Le héros peut maintenant les renvoyer avec son bouclier, ou subir des dégâts avec recul, invulnérabilité et clignotement sur terrain normal. La vie affichée est mise à jour. La mort, son fondu et le menu de reprise sont maintenant portés ; la reprise restaure la clairière initiale et retire un quart de l’or selon l’arrondi original. Les fondus et seize contours de reprise sont vérifiés à phase égale ; leur calendrier absolu et le retour au titre restent incomplets. Le hasard et les délais de chargement restent à rendre fidèles à la SMS. Les attaques primaire/secondaire et dommages aux ennemis sont traduits pour les cas testés. Les cinq poses d’explosion et les sept emplacements de butin normal sont intégrés : or, vie, magie et gel des ennemis. Les autres terrains, scripts, inventaire complet, ennemis/boss, interactions et sauvegardes restent à porter. Le lecteur des treize pistes musicales PSG est porté en C/68000 ; les bruitages et leur arbitrage restent absents. L’intro avant le titre et les portes des deux maisons du village sont intégrées, avec leurs ressources originales ; les dialogues intérieurs, achats et sauvegardes restent à traduire. `gaw-title-megadrive.bin` conserve le même binaire pour les anciens liens.

- `megadrive/src/main.c` : décompression et séquence de titre réécrites en C, compilées pour le 68000. Il n'y a pas d'interpréteur Z80 dans ce code.

- `analysis/bank_00.asm` à `bank_0f.asm` : sources Z80 réassemblables. Les instructions identifiées par analyse statique et par huit traces d’exécution sont désassemblées ; les octets non classifiés restent en `DB`.

- `analysis/code.json`, `manifest.json`, `fixed_listing.txt` : instructions, graphe de contrôle, accès matériels et sauts non résolus.

- `analysis/megadrive_68000_listing.txt` : désassemblage du binaire compilé.

- `validation/reassembled.sms` : ROM Master System reconstruite, identique octet pour octet à l'entrée.

- `validation/report.json` : vérifications de reconstruction, de RAM et d'image.

- `validation/sms_vs_md.png` : comparaison des deux exécutions dans Genesis Plus GX ; SMS à gauche, Mega Drive à droite.

- `validation/name_sms_vs_md.png` : comparaison après saisie de deux caractères et retour du curseur avec le bouton d'effacement.

- `validation/dialogue_sms_vs_md.png` : première page du dialogue, après acceptation du nom `A`.

- `validation/world_sms_vs_md.png` : premier écran du monde ; 49 152 pixels comparés sans différence après normalisation des palettes.

- `validation/movement_sms_vs_md.gif`, `movement_report.json` : parcours dans quatre directions, glissement le long des obstacles et arrêt contre les murs, comparé sur 371 images consécutives.

- `validation/transition_sms_vs_md.gif`, `transition_report.json` : transition horizontale vers le village et retour, avec 118 images vérifiées et tables d'arrivée identiques.

- `validation/vertical_sms_vs_md.gif`, `vertical_report.json` : défilement sud `$0094 → $00A4`, 71 images du défilement vérifiées ; les objets natifs apparaissent ensuite avec un calendrier différent. Arrivée complète encore non fidèle.

- `tools/extract_world.py`, `analysis/world_assets.json` : reconstruction depuis la ROM de la carte, des métatuiles, du HUD et des motifs visibles ; aucun état capturé n'est incorporé comme ressource.

- `tools/actor_reference.py`, `analysis/actor_loading_reference.json` : traduction de référence du chargement des ennemis de salle. Pour `$00A4`, 768 octets d'état et 1 952 octets de motifs sont identiques à la SMS officielle. Le placement accepte explicitement les valeurs du registre Z80 `R` ; la séquence de hasard d’origine et les autres comportements restent à porter.

- `megadrive/src/actors.c`, `analysis/actor_assets.json`, `validation/actor_report.json` : chargeur 68000 intégré aux entrées de salles. Ressources de 33 types extraites depuis la ROM ; état et allocation vérifiés dans `$0094` et `$00A4`, avec comparaison des tuiles du VDP Mega Drive. Les conditions de progression et les délais d'origine restent à traduire.

- `tools/sprite_reference.py`, `validation/actor_sprite_report.json` : décodage et rendu natif des descripteurs d'ennemis, vérifiés sur 60 états et 1 004 sprites. Le test isolé injecte les états SMS précédents dans l'émulateur et compare 59 images ; il ne valide pas encore la simulation du jeu. Les états capturés ne sont pas incorporés au binaire. Le test initialise aussi l’horloge et la palette à partir des règles ROM. Les transferts de sprites précèdent ceux de palette ; seules les couleurs modifiées sont écrites, pour respecter la fenêtre de transfert du VDP.

- `tools/actor_tick_reference.py`, `validation/actor_tick_report.json` : compteurs communs traduits en 68000 (mouvement en virgule fixe, animation, délai et clignotement). Une seule injection initiale permet de vérifier 47 mises à jour natives successives de l'apparition du type `$26`. Huit cas supplémentaires vérifient les bornes signées des compteurs et la remise à zéro des fractions. Les dommages et les comportements des autres types restent à porter.

- `tools/actor_ai_reference.py`, `validation/actor_ai_report.json` : états `$2/$4/$6/$8` des types `$26..$28` traduits en C natif : fin d'apparition, choix de direction, collisions de terrain et poursuite du mouvement. Test isolé sur 59 mises à jour du premier ennemi et 32 cas de décision. Le hasard SGDK est provisoire ; la séquence Z80 `R` et les dommages restent à porter. Le placement est maintenant connecté au jeu normal.

- `validation/actor_spawn_report.json` : exécution normale sans injection, avec cinq ennemis actifs dans `$00A4`. Les règles de placement et de déplacement sont vérifiées sur 89 images / 1 424 mises à jour d’entité, en utilisant les valeurs réellement tirées par le hasard natif. Un test contrôlé reproduit les 48 octets d'un placement SMS ; cela ne prouve pas la séquence de hasard ou les délais d'origine.

- `validation/ranged_report.json` : types `$20..$22`, attente de tir et réserve de huit projectiles `$10..$12` en code natif. Test isolé de 99 images / 1 584 mises à jour, avec création, mouvement, expiration et réserve pleine. Le déplacement d’un tir SMS réel est aussi reproduit sur 60 pas (48 octets). Les dégâts au héros et les réflexions au bouclier sont vérifiés séparément. La suppression des tirs liée à la saturation des sprites et les limites de donjon restent à porter.

- `validation/shield_report.json` : renvoi des projectiles au bouclier traduit depuis `$2346/$2E08`. Un test contrôlé reproduit 20 images SMS et les 48 octets du projectile, y compris le renvoi à 3745 et son expiration. Dix-huit cas vérifient les directions, la puissance, la parité et les refus. Les coups non bloqués et le recul sont maintenant vérifiés séparément ; les états du héros hors marche normale, l’inventaire et le son restent à porter.

- `validation/damage_report.json`, `damage_sms_vs_md.gif` : dommages au héros sur terrain normal, recul sur huit pixels, compteur de blessure et clignotement. Comparaison de 60 pas, 768 octets d’acteurs par image, 12 champs du héros, 60 états du HUD et 58 images normalisées. Vingt et un cas SMS/68000 couvrent les quatre reculs, murs, limites, défense, invulnérabilité, vie à zéro et coup reçu en marchant. La mort et son menu sont vérifiés séparément ; les attaques du héros et les dégâts aux ennemis sont vérifiés séparément.

- `validation/death_report.json`, `death_sms_vs_md.gif` : mort en 90 pas, deux images du héros extraites de la banque 5, fondu grisé, textes et curseur d’origine. Comparaison de 92 états, 118 images de mort/fondu/menu et 130 images de sélection. La reprise rend 24 PV et transforme 100 pièces en 75, avec scène finale identique à la SMS. « FIN » retourne au titre. La préparation de reprise et le titre gardent des écarts de rythme ; les autres points de reprise et le son restent absents.
- `tools/validate_resume.py`, `validation/resume_report.json`, `resume_sms_vs_md.gif` : reprise au point initial `$0095`, avec les fondus `$0B12/$0AA4` et la révélation `$1FA7`. Les deux suites de neuf palettes, les seize cartes successives de 768 mots et seize images à phase égale sont identiques à la SMS. Les contours sont extraits de la table ROM `$2011..$2050`. Le chargement conserve un décalage d’une à deux images ; cette preuve ne couvre pas les autres points de reprise ni le calendrier absolu.
- `validation/attack_report.json`, `attack_motion_report.json`, `attack_sms_vs_md.gif` : attaques primaire et secondaire, quatre directions, rythmes normal/rapide, graphismes jusqu’à huit tuiles. Seize cas vérifient 544 pas et 512 images. Une autre séquence vérifie 70 pas/images avec attaque pendant un déplacement, maintien du bouton, directions combinées et seconde pression. Le bouton C déclenche l’attaque primaire initiale ; la sélection d’équipement par inventaire reste à porter.
- `validation/enemy_damage_report.json` : vingt cas de coup primaire comparent les PV, le dommage minimal de deux, le recul limité par le décor, la blessure de 32 pas, la copie dans le slot de dédoublement et la transformation puis les états d’explosion d’un ennemi mort. Les copies et l’application du coup sont exactes ; la suite du dédoublement diverge avec les décisions aléatoires. Les particules et objets au sol disposent désormais de tests distincts ; le flux aléatoire des objets n’est pas fidèle.

- `analysis/banked_listing.txt` : instructions des banques commutées confirmées par une exécution instrumentée.



La ROM source reste intacte à son emplacement d'origine. Une copie de travail est conservée dans `input/original.sms`.



## Source de référence



Fichier fourni : `D:\Cartmod\GoldenAxeWarrior\chat\Golden Axe Warrior (USA, Europe).sms`



Taille : 262 144 octets, seize banques de 16 Kio.



SHA-256 : `852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9`



L'exécution affiche du texte français malgré le nom du fichier. L'analyse et le portage utilisent exactement cette version, sans la remplacer par une autre ROM.



## Ce qui est vérifié



Les seize fichiers ASM se réassemblent avec SjASM et reproduisent les 262 144 octets de la ROM. Cela prouve une reconstruction binaire sans perte, **pas une décompilation complète** : les zones non classifiées restent des données brutes.



L'analyse initiale a retrouvé 5 516 instructions par accessibilité statique. Avec les traces de démarrage, création du personnage, transitions, attaques et objets au sol, le corpus atteint 7 498 instructions et 15 101 octets classifiés. Les traces réunies confirment 5 877 adresses d'instructions. Une instruction accessible par analyse statique n'est pas automatiquement du code confirmé par une trace d'exécution : seules les entrées portant `executions` ont cette preuve. Les autres parcours, sauts indirects et banques restent à examiner. `analyze_rom.py` accepte plusieurs `--trace` et conserve leur provenance dans le manifeste.



Pour le titre, les deux cartes produites par le code 68000 sont identiques à celles observées dans la RAM de l'exécution SMS. Les 449 tuiles sont contrôlées pixel par pixel après conversion planaire vers les pixels à quatre bits de la Mega Drive.



L'image finale, soit 49 152 pixels, correspond à celle de la SMS après normalisation des palettes. Les valeurs RGB brutes diffèrent : les palettes matérielles sont différentes. Les captures comparent le même état visuel, pas le même numéro d'image. Le rythme global, le fondu et le passage vers le menu doivent encore être ajustés et validés.



Trois scénarios supplémentaires sont vérifiés contre l'exécution SMS : menu initial, saisie du nom initiale et saisie `AB` suivie d'un retour du curseur. Chacun présente zéro différence de pixels après normalisation des couleurs. Les cadres et polices sont reconstruits depuis les ressources ROM ; les curseurs utilisent les descripteurs de sprites relatifs originaux, convertis en sprites Mega Drive.



La validation du nom reconvertit les identifiants de tuiles en caractères, retire les espaces finaux et refuse un nom vide. La première page du dialogue, avec le nom `A`, est vérifiée pixel par pixel et octet par octet dans son tampon bitmap de 1 040 octets. La police proportionnelle, les accents et les retours à la ligne viennent des données et routines de la ROM. Le code rend aussi la suite du message après confirmation, mais la vérification actuelle couvre sa première page. Les autres commandes de script (`#`, `$`, changement de casse, etc.) restent à porter.



Le chargement natif de la salle `$0095` traduit les flux RLE du décor, ses métatuiles et attributs de collision, la carte 16 × 10, le HUD et le héros en trois plans graphiques. La carte affichée de 1 536 octets et tous les motifs visibles correspondent à l'exécution SMS. La comparaison d'image couvre aussi le sprite du héros. Le fond vert de la zone de jeu et le fond noir du HUD sont reproduits avec un second plan Mega Drive, pour compenser la transparence de l'index zéro.



La marche normale traduit `$3295..$33DA` et l'intégration des vitesses `$26E5..$2718`. Les sondages de collision forment une grille de douze mots autour du héros. Les mêmes branches de glissement et la même table de vitesses sont utilisées ; chaque pas de huit pixels dure cinq images. Les seize poses de marche viennent de la ROM. Sur le parcours vérifié de 371 images, positions en virgule fixe, directions, animations et compteur de mouvement sont identiques à la SMS. Les images sont également identiques après normalisation des palettes, sans décaler les numéros d'image. Ce parcours inclut 41 images immobiles avec une direction maintenue contre un obstacle. Les graphismes sont préparés avant la fenêtre d'affichage afin d'éviter des poses partiellement remplacées ; la priorité du héros reproduit son passage derrière les tuiles du décor. Ces vérifications ne couvrent pas encore la totalité des états du héros ni la boucle de jeu complète `$24F3`.



Les 225 cartes extérieures de classe normale sont décodées et vérifiées structurellement comme grilles 16 × 10 ; leurs flux compressés, totalisant 20 641 octets, sont incorporés au projet natif. Cela ne prouve pas le portage de toutes ces salles : changements de terrain, objets, portes, modifications de carte et scripts restent incomplets. L'aller-retour `$0095 → $0094 → $0095` et les cartes d'arrivée sont vérifiés. Le défilement horizontal utilise le mode ligne du VDP : seuls les 160 pixels de hauteur du monde se déplacent, le HUD reste fixe. Les 118 captures vérifient l'état, les positions et les pixels sans décalage temporel.



Le défilement sud `$0094 → $00A4` utilise maintenant des métatuiles déjà converties et copie vingt rangées par DMA, sans reconvertir 640 tuiles à chaque image. Les 71 images jusqu’à la fin du défilement sont identiques, et la carte d’arrivée correspond octet pour octet. Le parcours actuel comporte 82 images identiques sur 161 ; les différences commencent à 3082 lorsque les premiers ennemis natifs apparaissent. Les états de salle et du héros correspondent sur 161 images. L'état de préparation des objets reste incorrect sur 27 images : la SMS initialise les objets entre les images 3070 et 3096, tandis que le prototype reprend déjà le gameplay. Les cinq ennemis sont actifs, mais leur calendrier et leurs positions diffèrent avec le hasard SGDK provisoire ; les dégâts et les combats du héros restent absents. Le rapport signale explicitement que l'entrée complète n'est pas terminée. Les autres sorties verticales et les classes de décor 1/2 restent à vérifier/porter.



## Commandes du prototype



- A/B/C/Start au titre : passer au menu.

- Haut/Bas : sélectionner Nouveau ou Continuer ; confirmer Nouveau ouvre la saisie.

- Directions dans la saisie : sélectionner un caractère, CORR ou FIN, avec répétition lors d'un appui prolongé.

- C : écrire le caractère ou activer CORR. B : revenir au caractère précédent. Start fonctionne aussi comme confirmation dans cette interface.

- FIN valide un nom non vide et ouvre le premier dialogue ; C/Start permet de poursuivre son texte puis d'afficher la salle initiale. Les directions déplacent ensuite le héros. Le passage vers le village se trouve à gauche, vers Y=88. L'attaque et les interactions ne sont pas encore actives. Continuer attend le portage des sauvegardes.



Le port conserve une image de 256 × 192 pixels, centrée dans le mode Mega Drive 256 × 224, avec des bandes noires de 16 pixels.



## Correspondances déjà établies



| Adresse Z80 | Fonction | Port 68000 |

|---|---|---|

| `$0000`, `$0089` | Reset, pile et configuration initiale du mapper | Démarrage SGDK, configuration vidéo native |

| `$00D2` | Dispatch par état à partir de `$C01D` | À porter pour l'ensemble du jeu |

| `$00DC`–`$00F3` | Table de douze états | Extraite dans `manifest.json` |

| `$032A` | RLE de quatre flux entrelacés, graphismes | `decode_planes`, stride 4 |

| `$0BD3` | Littéraux ou suites incrémentales vers `$D100` | `decode_map` |

| `$0BFE` | RLE de deux flux entrelacés, cartes de tuiles | `decode_planes`, stride 2 |

| `$146D`–`$14EC` | Chargement et séquence de titre | `title_sequence`, partiel |

| `$165C`–`$167E` | Trois cartes d'animation des lettres | `copy_rows` dans `title_sequence` |

| `$169C`, `$0ADE` | Fondu par composante de palette | `fade_title_palette`, rythme à aligner |

| `$163F` | Affichage progressif des huit premières lignes | Boucle native de `title_sequence` |

| `$161D` | Clignotement du message de démarrage | Boucle native de `title_sequence` |

| `$16C0` → `$14ED` | Bouton de démarrage, transition vers le menu | Transition native vers `start_menu` |

| `$0877` | Cadre avec neuf motifs | `draw_frame` |

| `$0812` | Texte et table de caractères `$8A8E` | `draw_text` |

| `$0365`, `$0C36`, `$0C51` | Polices monochromes et fond de glyphe | `load_mono` et chargements de `start_menu` |

| `$1101`–`$118D` | Interface de saisie du nom | `enter_character_name` |

| `$12C1`–`$133B` | Déplacement et répétition du curseur | Boucle native dans `enter_character_name` |

| `$0A78` | Descripteurs de sprites relatifs | `add_sms_sprite_frame`, sprites SGDK |

| `$1214`–`$125F` | Valider et nettoyer le nom | `finish_name` |

| `$0524`–`$07EE` | Texte bitmap proportionnel, retour à la ligne, pages | Sous-ensemble pour le premier message dans `opening_dialogue` |

| `$16D0`, `$190B`, `$2279`, `$1E4E` | Décor, salle, métatuiles et HUD | `enter_initial_room`, salle `$0095` |

| `$369F`, `$3B07`, `$09xx` | Graphismes et descripteur du héros | Chargement de la pose initiale et sprites SGDK |

| `$3295..$33DA`, `$26E5..$2718`, `$230E` | Marche normale, glissement, intégration et collision | `move_hero`, `collision_direction`, mises à jour de sprites |

| `$2051`, `$21A1`, `$21C5/$21CB`, `$217D` | Sorties, destination, défilement horizontal | `begin_room_transition`, `step_room_transition`, défilement VDP par ligne |

| `$0AD1/$0ADE`, `$0B12/$0AA4`, `$1FA7..$2010` | Fondus et révélation au rechargement | `fade_world_palette`, `reveal_world`, calendrier à aligner |
| État `$0C`, `$24F3` | Boucle du jeu | Portage partiel |



## Étapes nécessaires avant une version jouable



1. Résoudre les sauts indirects et les banques de code, identifier les tables d'état et la carte RAM ; obtenir une reconstruction Z80 commentée avec les données et les pointeurs nommés.

2. Étendre l'initialisation à l'état complet de partie et porter la sélection des sauvegardes. La salle initiale, la validation du nom et la première page du dialogue sont portées et vérifiées.

3. Étendre les déplacements et collisions aux autres terrains, puis porter les transitions de salles et les mises à jour du HUD.

4. Porter les objets, ennemis, combats, inventaire, dialogues et progression.

5. Adapter les sprites et les interruptions de ligne ; conserver les effets observés dans le jeu original.

6. Porter le son PSG et les sauvegardes ; vérifier les différences PAL/NTSC.

7. Valider des parcours de jeu complets, puis seulement ouvrir une phase d'amélioration.



## Reproduire le travail



Depuis le dossier du chat, les dépendances téléchargées résident dans `work/` :



- SGDK : commit `ee6870a6010b1e341ca36078f581a68a26c9a543`, compilateur 68000 GCC 13.2 et SjASM fournis par le projet.

- z80dis : commit `c1e11aed5a5f00c40c07d838f0fdcd282840d0b5`.

- Genesis Plus GX : cœur Windows x64 de Libretro. Empreinte SHA-256 de l'archive téléchargée : `2251ed05a0f6062d045ba9c6d251c6688bd053835dfd7e1e211b140291868c48`.

- Python 3.13 avec Pillow, Java 25 pour les outils SGDK.



```powershell

python outputs/gaw-md/tools/analyze_rom.py 'D:\Cartmod\GoldenAxeWarrior\chat\Golden Axe Warrior (USA, Europe).sms' --trace outputs/gaw-md/validation/sms-world --trace outputs/gaw-md/validation/sms-transition --trace outputs/gaw-md/validation/sms-vertical --trace outputs/gaw-md/validation/sms-combat-trace --trace outputs/gaw-md/validation/sms-loot-trace --trace outputs/gaw-md/validation/sms-inventory-trace --trace outputs/gaw-md/validation/sms-heal-potion-trace

python outputs/gaw-md/tools/extract_title.py

python outputs/gaw-md/tools/extract_menu.py

python outputs/gaw-md/tools/extract_world.py

& ./outputs/gaw-md/build.ps1

python outputs/gaw-md/tools/run_core.py outputs/gaw-md/input/original.sms --frames 1000 --out outputs/gaw-md/validation/sms --capture 600,800,900,950,1000 --press 200:220:0

python outputs/gaw-md/tools/run_core.py outputs/gaw-md/gaw-title-megadrive.bin --frames 800 --out outputs/gaw-md/validation/md --capture 30,120,300,450,650,700,750,800

```



Les captures de menu, de saisie et d'effacement doivent également être régénérées avec le binaire courant avant `validate.py`. Les séquences exactes sont enregistrées dans chaque `validation/*/capture.json` ; `tools/regression.ps1` exécute tous ces scénarios.



```powershell

& ./outputs/gaw-md/tools/regression.ps1

```



Pour la couverture de code, `tools/instrument_core.py` ajoute un observateur des adresses d'instructions dans le checkout local de Genesis Plus GX, commit `58c341487e5bfcf979ea68413c7987633adb0c56`. Ce cœur reste dans `work/` et ne fait pas partie de la ROM Mega Drive. Il expose uniquement des compteurs et les fenêtres du mapper. La trace principale est conservée dans `validation/sms-world/trace_*.bin` et porte l'empreinte de la ROM analysée. Les états `$00`, `$12`, `$04` et `$0C` y sont observés. L'état `$0C` correspond à la boucle de jeu à `$24F3`, dans la salle initiale `$0095`. Les régressions sans instrumentation utilisent `sms-world-check`, afin de préserver la provenance de la trace.



Les valeurs de `$C01D` sont des offsets en octets dans la table de mots `$00DC` : `$12` sélectionne donc l'entrée `$1101`, et `$04` sélectionne `$2433`.



`build.ps1` accepte `-Sgdk` et `-Java` pour d'autres installations. Le projet SGDK reste dans `megadrive/`. La vérification des captures nécessite le cœur dans `work/libretro/genesis_plus_gx_libretro.dll`.



La compilation peut afficher une erreur 127 ignorée lors du nettoyage d'un fichier temporaire LTO par le make fourni. L'édition de liens réussit, et le binaire résultant démarre dans le cœur de vérification. Ce détail de la chaîne de compilation reste à nettoyer.



## Documentation des outils utilisés



- [SGDK, source officielle](https://github.com/Stephane-D/SGDK)

- [z80dis, source officielle](https://github.com/lwerdna/z80dis)

- [Genesis Plus GX, source Libretro](https://github.com/libretro/Genesis-Plus-GX)



Les bibliothèques et outils tiers gardent leurs licences respectives. Les sources et graphismes du jeu proviennent de la ROM locale fournie.


La validation du dialogue d’ouverture conserve un écart de 32 pixels au repère Mega Drive 2008 : il concerne exclusivement la flèche de confirmation. Le texte bitmap reste identique. L’image complète correspond au repère 2012, à phase de clignotement égale ; le rythme absolu du dialogue reste à aligner.

La trace `sms-combat-trace` ajoute l’attaque primaire par boutons réels, puis une attaque secondaire avec mutation contrôlée de C0DF/C0E1 à l’image 2853. Son origine et ses mutations figurent dans `capture.json` ; la trace ne valide donc pas encore la sélection d’équipement par le menu du jeu.


## Explosions et butin — 8 octobre

`validate_particles.py` compare les cinq poses d’explosion, 30 états complets et 28 images, puis l’effacement particulier du type original zéro. `validate_drop.py` compare trois scénarios de création avec des classes indépendantes du tirage : grand cœur garanti, aucun objet, et sept emplacements occupés. Le premier emplacement libre et la décrémentation du nombre d’ennemis concordent.

`validate_loot.py` contrôle les six types normaux `$08..$0D`, le contact, les plafonds de vie/magie/or et l’affichage des compteurs. Le gel est vérifié sur un ennemi actif. Les sept objets sont suivis jusqu’à leur expiration, avec clignotement et 368 images de rendu identiques. Les mutations initiales servent uniquement aux tests, sont enregistrées dans `capture.json` et ne figurent pas dans la ROM native. Comparaisons d’images après conversion de la palette Mega Drive vers les couleurs SMS et retrait des marges verticales.

La liste d’exceptions et les seuils ROM de création sont utilisés par le jeu natif. Le tirage reste fourni par SGDK : la séquence dépendante du registre Z80 R n’est pas reproduite. Le type `$0E`, les récompenses de boss et la persistance entre salles restent incomplets. Les sons de ramassage sont absents.

Démonstrations comparées : `validation/particles_sms_vs_md.gif`, `validation/loot_sms_vs_md.gif`. Relancer `tools/regression.ps1` pour reconstruire et exécuter tous les tests du jalon.

La régression complète et le test létal étendu passent sur le binaire SHA-256 `5afc855dfb732d4a1ba9c7991c8946daa2db2157c91e75222b14bebbc89e9b9a`. Les 20 rapports natifs correspondent à ce binaire ; les deux noms de ROM sont identiques et la reconstruction SMS reste exacte. Audit : `validation/loot_milestone_audit.json`.


## Inventaire natif — 8 octobre

Dans le monde, **B** ouvre l’inventaire. Les directions déplacent le curseur dans les douze cases ; **C** choisit un objet possédé et **B** ferme le menu. Une case vide refuse la sélection. Les icônes, la carte extérieure, les textes d’armure/bouclier et les clés proviennent de la ROM originale. Les niveaux d’armure/bouclier 1..3, l’équipement principal 1..3 et l’arme secondaire 1..2 sont testés.

Le menu conserve le monde et les acteurs en RAM pendant la pause, puis restaure les motifs du décor et l’icône du HUD. Une arme secondaire choisie dans le menu déclenche son attaque par C après fermeture. Le test pose uniquement la possession initiale en RAM de l’émulateur ; les acquisitions et scripts d’inventaire restent à porter. Les autres cases peuvent être sélectionnées. Le soin et la potion sont maintenant traduits ; les autres effets restent à porter.

`validation/inventory_report.json` compare 89 états de navigation, 85 images de menu identiques et trois panneaux d’équipement. Les quatre images pendant la recoloration progressive de l’icône diffèrent encore ; elles sont listées avec leur nombre de pixels, sans masquer ces régions. Les 31 états d’une attaque secondaire après fermeture concordent. La phase initiale du clignotement est contrôlée pour cette comparaison ; le calendrier complet d’entrée/sortie n’est pas revendiqué exact. Animation : `validation/inventory_sms_vs_md.gif`.

Le binaire d’inventaire vérifié a pour SHA-256 `60332582ab7412e7f3decbd287b0bdaab9b26cb5f5f8334594b5ef644ac1b1d4`. Les 21 rapports natifs correspondent à ce binaire. Le fondu de reprise possède une image noire initiale séparée des neuf changements de palette ; le vérificateur conserve cette attente dans son rapport. Audit : `validation/inventory_milestone_audit.json`. La ROM SMS originale sur D: et sa reconstruction sont inchangées.


## Soin et potion natifs — 8 octobre

Le sort de soin (case 7) consomme 24 points de magie et rend 16 PV, limités par la capacité du héros. Il consomme sa magie même si la vie est déjà pleine, et une pression maintenue ne l’active qu’une fois. Une nouvelle pression peut l’activer de nouveau si la magie suffit. La case et sa possession sont conservées.

La potion (case 8) restaure la vie un point à la fois, avec deux attentes d’affichage par point. Elle ne consomme pas de magie. À la fin, elle disparaît de l’inventaire et l’arme principale est sélectionnée. À pleine vie, elle est conservée. Les sons restent absents. Les barres HUD suivent désormais les capacités de vie/magie au lieu d’imposer trois unités ; les capacités 24 et 48 sont comparées avec la SMS.

`validate_heal.py` contrôle sept scénarios, 455 états et 427 images. `validate_potion.py` contrôle cinq scénarios, 400 états et 380 images. `validate_healing_route.py` atteint les deux effets avec les commandes normales d’inventaire, à partir d’une possession initiale contrôlée uniquement dans l’émulateur. L’acquisition des objets par les scripts/chests reste à porter. Les autres classes de terrain et la variante de soin de la classe C041=2 restent à traduire.

Animations comparées : `validation/heal_sms_vs_md.gif` et `validation/potion_sms_vs_md.gif`.

Continue restaure désormais aussi la magie à 24 et conserve les capacités augmentées. Avec les deux capacités à 48, le test dédié vérifie 31 états et 31 images du HUD après reprise.

La régression complète `tools/regression.ps1` termine avec le code 0 sur le binaire SHA-256 `22cfb077d5c03b4f5b9b186819badac383ad2565121aa939df7732236fd31320`. Les 25 rapports natifs correspondent au même binaire et la reconstruction SMS reste exacte. Audit : `validation/heal_potion_milestone_audit.json`. Le jeu complet n’est pas encore porté.


## Sort de feu natif — 8 octobre

La case 4 active le projectile de feu de type 3, dans le record auxiliaire C330. Le premier tir d’un cycle dépense huit points de magie, puis trois tirs sont disponibles sans nouvelle dépense. C0C6 revient ensuite à zéro. Une pression maintenue ne répète pas le tir ; un projectile encore présent refuse une nouvelle activation. Sans magie suffisante au début d’un cycle, l’arme principale est sélectionnée et son icône rétablie avec l’attente observée dans la SMS.

Le héros utilise le descripteur de lancement $83E3 pendant quatre mises à jour, avec phases 0..3, puis reprend son comportement normal. Les six motifs par direction proviennent de $3D7B. Le projectile se déplace de trois pixels par mise à jour, avec l’origine propre à chaque direction et les deux descripteurs de puissance de la ROM. Il disparaît aux limites et sur les catégories de terrain $80/$A0. Les ennemis examinent le héros avant le projectile ; les dégâts, la puissance minimale, le recul et la conversion létale suivent les routines Z80 traduites.

`validate_fire.py` vérifie onze scénarios : quatre directions, deux niveaux, magie insuffisante, cycles de tirs, bouton maintenu et copie du clignotement après blessure. Il compare 1 320 états et 1 276 images normalisées. `validate_fire_damage.py` compare douze scénarios de collisions avec ennemis, 480 états et 432 images normalisées. Les possessions, positions et certains ennemis sont initialisés uniquement dans l’émulateur ; leurs acquisitions dans le jeu restent à porter. Les premières images de déplacement forcé du héros sont exclues de la comparaison graphique. Comparaison : `validation/fire_sms_vs_md.gif`, SMS à gauche et Mega Drive à droite.

La trace instrumentée `sms-fire-trace` complète le corpus : 7 608 débuts d’instruction, 15 363 octets classifiés et 5 987 débuts exécutés. Ces sources sont partiellement désassemblées ; la reconstruction exacte des banques ne prouve pas une décompilation complète. La case 5 et ses mutations de décor, l’effet temporaire de la case 6, les sons et les autres classes de terrain restent à traduire.


Le parcours `validate_fire_route.py` sélectionne la case 4 depuis l’inventaire par les boutons, ferme le menu et lance quatre tirs : magie finale 16, charge revenue à zéro et possession conservée. Il initialise uniquement la possession, la vie et le retrait des ennemis ; le choix d’objet, l’état d’action et l’horloge sont atteints par le jeu. Le calendrier absolu du menu reste imparfait.

Le jalon feu est validé sur le binaire SHA-256 `511c5fdfaa82f61f8fab1c20149dd0e2288160ac34b62c891d394a0f2e6c4bb4` : suite générale avec `-SkipFire` et trois validateurs feu exécutés séparément, tous avec code 0. Les 28 rapports natifs correspondent au même binaire. Les seize banques SMS se reconstruisent exactement, et le fichier fourni sur D: reste inchangé. Audit : `validation/fire_milestone_audit.json`. Les interactions du lancement avec la mort et les transitions restent à étendre aux prochains tests ; le jeu complet reste incomplet.

## Intro, musique et portes — 9 octobre 2026

La ROM contient maintenant la séquence avant le titre : trois scènes, texte français de l’entrée, révélations des motifs et animations de palette/sprites. `intro.inc` traduit les routines `$0C98..$10BE`. `intro_report.json` vérifie les 65 états de texte/carte (1 536 octets chacun), sans bouton ni mutation mémoire, jusqu’au retour au titre. Le calendrier absolu et toutes les phases de sprites ne sont pas encore vérifiés. `validation/md-intro-music.wav` provient de l’exécution de la ROM native dans l’émulateur.

`sound.inc` traduit le lecteur musical de la banque 6, avec quatre canaux, notes, durées, enveloppes, modulations, appels et boucles. `music_report.json` vérifie les treize commandes `$81..$8D`, chacune sur 1 800 IRQ : 23 400 états des quatre records et des registres PSG audibles concordent avec le moteur Z80. Le registre de bruit conservé pendant le silence est exclu de la comparaison audible. Ces tests contrôlent la commande et la phase de compensation 60 Hz ; ils ne prouvent pas l’identité des échantillons audio ni l’ensemble du routage des bruitages. Les pistes de l’intro, du titre et des classes extérieures/intérieures sont intégrées.

Les scripts `$6594/$65D0` permettent l’entrée depuis le village `$0094` vers les maisons `$0000/$0002`, puis la sortie vers la position mémorisée. Les décors, métatuiles et motifs animés proviennent de la ROM. `village_doors_report.json` suit les deux parcours par des commandes normales, sans injection RAM : 60 états de salle/héros et 42 comparaisons du terrain sont vérifiés. Les images excluent quatre motifs animés par l’horloge ; leurs phases, le HUD et les fondus/délais du chargement restent incomplets. La sauvegarde et le premier marchand sont d�crits dans les jalons suivants.

La ROM est rembourrée à 512 Kio et son en-tête ainsi que sa somme de contrôle SGDK sont recalculés. Un test isolé des sprites observe encore quelques pixels différents dans les huit lignes supérieures après l’activation du lecteur sonore par interruption ; son rapport conserve les différences, sans les présenter comme une égalité d’image complète. Les listes de sprites et indices de collision de ce test restent exacts.

Les six conversations informatives des maisons sont traduites depuis `$667E` et les tables de la banque 2. Le tampon bitmap de chacun des six textes est identique aux 1 040 octets de la SMS ; les fenêtres sont comparées hors clignotement du marqueur de confirmation. Six cas contrôlent la position initiale dans l’émulateur, et un septième atteint le premier villageois de la maison 2 par les boutons seuls, ouvre le dialogue et le referme. La fermeture restaure les motifs, la carte et les métatuiles sauvegardés, sans réinitialiser les personnages. Rapport : `validation/house_dialogue_report.json`. La confirmation accepte les boutons d’action et les nouvelles pressions directionnelles ; un cas vérifie la fermeture par Droite. Les délais absolus, les menus de sauvegarde et les transactions restent à compléter.

Le hasard SGDK reste provisoire : le test de collision du feu rapporte explicitement les différences de butin après une mort plutôt que d’affirmer une reproduction du flux Z80 `R`. Les états du héros, du projectile et des ennemis sont vérifiés séparément de ce butin.

Jalon vérifié sur la ROM SHA-256 `0da4eef867f1f761afd48938e9c761d30f6e575333bfab204c5b81e47ee43000` : suite générale avec le feu, intro, treize pistes, portes et conversations terminent avec le code 0. Les 32 rapports correspondent à ce même binaire. Les trois copies de ROM sont identiques, les seize banques SMS se reconstruisent exactement et le fichier fourni sur D: est inchangé. Audit : `validation/intro_music_village_milestone_audit.json`.

Le tampon DMA de copie est explicitement limité à 2 Kio : seuls les petits rectangles des animations intérieures utilisent cette copie, ce qui laisse la RAM nécessaire au tampon de dialogue. Son allocation est vérifiée dans la RAM de l’émulateur. `tools/regression_intro_music_village.ps1` rejoue les quatre validations de ce jalon après compilation.

L’audit de l’en-tête contrôle la somme XOR repliée produite par `sizebnd.jar` de cette version de SGDK. Elle diffère de la somme additive Mega Drive usuelle ; ce détail d’en-tête reste à normaliser avant une livraison matérielle finale. Les tests émulateur de cette ROM passent.

Correctif PNJ du 9 octobre : l’ouverture et la fermeture des conversations gardent le VDP actif ; 162 images du parcours naturel vérifient l’absence d’écran désactivé/noir. La sauvegarde/restauration des motifs vise désormais `$2000..$303F`, réellement utilisés par le bitmap, au lieu de la plage `$0000`. Les six bitmaps et 4 096 octets restaurés par cas sont contrôlés. Binaire SHA-256 `ecf204fdd627956fb051211713ed41a5b601c1bb8a969a60cc4d4d62abaa0105`. Audit spécifique : `validation/npc_no_black_patch_audit.json`. Ce correctif a ses propres tests ; les rapports de la suite générale précédente restent associés à leur ancien hash.


Sauvegarde native en cours de validation générale : la première personne de la maison 0 (X136/Y72, face au nord) affiche le panneau source avec portrait, Oui/Non et trois emplacements. Les 592 octets `$C0B0..$C2FF` sont enregistrés dans une SRAM Mega Drive de 8 Kio sur la ligne d’octets impairs, avec espacement source de 1 Kio entre emplacements. « Continuer » sélectionne un emplacement et retrouve le point du village à X136/Y112 ; le menu présélectionne Continuer quand une sauvegarde existe. Les textes, le curseur et ses motifs sont extraits de la ROM. Les menus du marchand et du soigneur ne sont pas encore portés.

`validate_save.py` contrôle les trois blocs contre la SRAM SMS, neuf images normalisées du panneau et de la sélection, puis 63 états/carte de reprise après relancement. Le troisième cas contrôle des valeurs initiales de vie, capacités, magie, or, clefs, possession de feu et charge du sort dans l’émulateur ; les deux premiers parcours n’injectent aucun état. Les contrôles supplémentaires couvrent Non, annulation, remplacement d’un emplacement occupé, conservation des autres emplacements, Continuer vide et mort/reprise au village sauvegardé avec pénalité d’or. Les délais absolus et les services d’autres villages restent incomplets ; les masques persistants d’ennemis des salles non vides et la progression non portée restent à relier au bloc.

Le panneau de sauvegarde garde �galement le VDP actif � l�ouverture et � la fermeture : 111 images par phase et par emplacement sont contr�l�es, soit 666 images. Le HUD reste affich� pendant le remplacement du portrait par le d�cor. La reprise par Continuer est test�e avec une nouvelle instance de l��mulateur et le fichier SRAM, sans restauration de savestate.

Jalon sauvegarde et correctif affichage v�rifi�s sur la ROM SHA-256 `851e84ecfa4ca8fbd169024d9e45c2c0fbadf92ee00d04f677f9f9722ac18135` (512 Kio). Les suites `tools/regression.ps1` et `tools/regression_intro_music_village.ps1` terminent avec le code 0 ; les 33 rapports de l�audit correspondent � ce binaire. Les copies de ROM sont identiques, les seize banques SMS se reconstruisent exactement et le fichier original sur D: est inchang�. Audit : `validation/save_milestone_audit.json`. Les contr�les cibl�s de sauvegarde et de conversations ont aussi termin� avec le code 0 sur cette ROM. Le portage complet reste incomplet.


## Premier marchand natif � 9 octobre 2026

Le vendeur de la maison 0, X40/Y88 face au nord, propose la clef (60 cornes), la plume magique (60) et l�huile magique (130). `merchant.inc` traduit la branche du village 94 de `$7452/$78CE`, les v�rifications de quantit� et de possession, le refus faute d�or et la d�duction progressive de monnaie `$61E7`. La clef augmente C0DE, la plume poss�de la case 9 et l�huile la case 2 ; les autres inventaires et boutiques restent � porter. Les portraits et libell�s viennent des banques 7 et 3 de la ROM, via `tools/extract_merchant.py`. Le code d�affichage et de restauration est partag� avec la sauvegarde, sans d�sactiver le VDP.

`validate_merchant.py` compare les trois achats et quatre refus � la SMS : or insuffisant, 99 clefs, plume d�j� poss�d�e, huile d�j� poss�d�e. Les sept cas contr�lent initialement la position et les statistiques uniquement dans l��mulateur ; s�lection, achat et sortie utilisent les boutons. Chaque panneau initial est identique apr�s normalisation de palette ; les 4 160 octets VRAM du message de transaction et deux �tats de r�sultat sont compar�s. Les 1 554 images d�entr�e/sortie contr�lent le HUD visible et le VDP actif. Un huiti�me parcours atteint le vendeur en contournant les meubles, refuse un achat sans or et sort sans aucune injection m�moire. Les d�lais absolus des transitions et les bruitages restent incomplets.

Binaire SHA-256 `c926b3472f95e7a1ee3e3fb87b7fc6899c4f1ae126d3e314db428975a729306b`, 512 Kio. Les validations du marchand, de sauvegarde/Continue, d�inventaire, des portes et des six conversations terminent avec le code 0 ; cinq rapports cibl�s appartiennent � cette ROM. Audit : `validation/merchant_patch_audit.json`. La pr�c�dente suite compl�te reste associ�e au SHA `851e84ecfa4ca8fbd169024d9e45c2c0fbadf92ee00d04f677f9f9722ac18135` ; elle n�est pas pr�sent�e comme une r�gression compl�te de ce correctif. Le fichier SMS original est inchang�. Le marchand est ajout� au script de r�gression g�n�ral pour les passes suivantes.


## Premier soigneur natif � 9 octobre 2026

La personne � X216/Y88 dans la premi�re maison du village94 offre une nuit gratuite, conform�ment � la table `$7700`. `healer.inc` traduit `$7685..$76FD` : confirmation Oui/Non, fondu volontaire pour la nuit, attente de 60 interruptions, vie restaur�e � sa capacit� maximale, message de d�part et retour � la pi�ce. La magie et l�or restent inchang�s. L�ouverture et la fermeture ordinaires gardent le VDP actif ; le noir pendant la nuit fait partie de la s�quence source. `VDP_waitVInt()` assure les 60 IRQ lorsque le VDP est d�sactiv�, car la fonction d�attente utilis�e ailleurs peut alors revenir imm�diatement. Les textes et le portrait bank7 B0F1 sont extraits de la ROM par `extract_healer.py`. Les soignants payants des autres villages restent � porter.

`validate_healer.py` couvre vie9/capacit�24, capacit�48, vie d�j� pleine, refus et confirmation simultan�e avec Bas. Il compare les panneaux initiaux, 4160 octets VRAM des messages de d�part et deux �tats finaux par cas. Les cinq intervals de d�sactivation VDP concordent avec la SMS : 62 images observ�es, comprenant l�attente de 60 IRQ et la pr�paration de l�affichage. Les 1110 images d�entr�e/sortie ordinaires gardent le HUD visible. La confirmation a la priorit� sur la direction, comme `$6123`. `validate_healer_natural.py` atteint le service par les boutons seuls, passe la nuit et ressort sans injection RAM ; les 18 comparaisons de champs et la dur�e de d�sactivation concordent. Ce parcours pr�sente toutefois un d�calage absolu d�une image (source4019..4080, natif4020..4081), conserv� dans le rapport plut�t que d�clar� exact.

Binaire SHA-256 `9edd80f8ff17e4500f19aebc4f25b88a24385fa0ef18f344e01652113218006e`, 512 Kio. Les tests du soigneur et de son parcours naturel, du marchand, de sauvegarde/Continue, d�inventaire, des portes et des six conversations terminent avec le code0. Sept rapports cibl�s correspondent au m�me binaire ; audit `validation/healer_patch_audit.json`. La pr�c�dente suite compl�te conserve son hash851e84ec ; elle n�a pas �t� rejou�e int�gralement sur ce correctif. L�original SMS reste inchang�. Le titre n�a pas �t� modifi� dans ce jalon, apr�s retrait du signalement utilisateur. Le portage complet reste incomplet.


## Portes et persistance des acteurs � 9 octobre 2026

Les entr�es natives ne sont plus limit�es au village94. `extract_doors.py` extrait 134 portes simples de 116 salles ext�rieures depuis la table de scripts bank2 `$B762`. Il accepte uniquement le pr�fixe inconditionnel `LD BC / LD E / CALL $6594`, puis s�arr�te au premier autre instruction ; les contr�les de qu�te ne sont pas contourn�s. `doors_data.c` fournit les coordonn�es et les destinations � la routine 68000. La salle/position de retour est m�moris�e, l�entr�e place le h�ros en X136/Y152, et les 29 int�rieurs concern�s ont leur sortie standard `$65D0`.

La routine `$18E9` est �galement traduite : les huit records primaires d�acteurs sont conserv�s en masque, slot0 dans le bit7 et slot7 dans le bit0. Le masque est enregistr� avant le changement de salle, utilis� au rechargement et conserv� dans le bloc SRAM. Les records auxiliaires8..15 sont exclus comme dans la SMS. La s�rialisation ne force plus le masque ext�rieur � z�ro. La persistance des acteurs est ainsi reli�e au parcours et � la sauvegarde ; les conditions de chargement li�es � l�histoire et la progression restent � traduire.

`validate_expanded_doors.py` compare les 134 entr�es et sorties � la SMS, chacune sur trois �tats. Les salles de d�part sont pr�par�es par un checkpoint SRAM contr�l�, les acteurs sont retir�s et la derni�re �tape de d�placement est initialis�e dans l��mulateur pour isoler la transition. Ces tests ne prouvent pas l�acc�s naturel aux 116 salles ni leurs qu�tes. `audit_door_masks.py` compare 268 octets de masque dans ces captures. Quatre fixtures de survivants v�rifient les patterns80,01,55,AA contre la source ; la v�rification couvre l�ordre de chacun des huit bits. Une fixture for�ant huit records type20 arbitraires a corrompu l�ex�cution source et n�est pas retenue comme preuve de gameplay valide ; elle reste document�e dans `analysis/world_next.md`.

La suite g�n�rale et la suite intro/musique/village terminent avec le code0 sur la ROM SHA-256 `21d50e81217ea77c1e22daa0502c46ee39795ae22ca253810bd2946c02dcc870`, 512 Kio. Les 134 portes et les quatre masques de survivants ont �t� v�rifi�s s�par�ment sur ce m�me binaire. Les 42 rapports de l�audit sont associ�s � ce hash ; copies de ROM identiques, reconstruction SMS exacte et original sur D: inchang�. Audit : `validation/full_milestone_audit.json`. La v�rification des portes �tend les �tats et la persistance ; les images de tous ces lieux, les d�lais de fondu, les dialogues des autres villages, les acteurs conditionnels, qu�tes, donjons et autres classes de terrain ne sont pas pr�sent�s comme port�s ou int�gralement v�rifi�s. Le portage complet reste incomplet.


Current inns milestone: see [paid healer milestone](analysis/paid_healer_milestone.md) (ROM SHA-256 0eed8abc602a04228bf06a097137adac6846370dfb9bcc78decbb3373ac9ed58).


Current merchant milestone: [all merchants](analysis/all_merchants_milestone.md) (ROM SHA-256 7d4aeaa6bac07f0cdcc34f6dc20db97ed914710f8d2b906a1ddad993c101ec97).


Current save-point milestone: [all save points](analysis/all_save_milestone.md) (ROM SHA-256 e06442f35bc8d7c3f920cdeceb74008c561cb814b76fd2cdda462cbffb61e286).


Current mobile-actor milestone: [mobile actors](analysis/mobile_actors_milestone.md) (ROM SHA-256 ba3ec0e14ecedffe1f83ce30bc5347b436a270e754f0b5b2c6b2258140f39780).

Current flying actors milestone: [23..25 and13/15](analysis/flying_actors_milestone.md).

Current resting/emerging actors milestone: [2C/2E/2F and14](analysis/emerging_actors_milestone.md).

Current fixed-shooter milestone: [2D and5878 placement](analysis/fixed_shooter_milestone.md).

Current jumping actors milestone: [31/32 and30 shadows](analysis/jumping_actors_milestone.md).

Current water actors milestone: [33/34 emergence and leaps](analysis/water_jump_milestone.md).

Current hidden-trap milestone: [35, placement defaults and16](analysis/trap_walker_milestone.md).


Latest: [Mega Drive additive checksum milestone](analysis/md_checksum_milestone.md) (ROM 5d10a02a).


Latest: [Walkers36/37 and versioned ROMs](analysis/burst_walkers_milestone.md) (ROM7ab95bef).

[Versioned ROM catalogue](versions/README.md)

Audio milestone: [sfx_milestone.md](analysis/sfx_milestone.md).

Version v0011: [timing_services_milestone.md](analysis/timing_services_milestone.md). Numbered ROMs: [versions](versions/README.md).

Version v0013: [loading_timing_milestone.md](analysis/loading_timing_milestone.md).


Title cadence v0016: [details](analysis/title_cadence_milestone.md).


Title loading v0017: [details](analysis/title_loading_milestone.md).


Scroll objects v0019: [details](analysis/scroll_objects_milestone.md).


Walkers38/39 and bouncing1F v0020: [details](analysis/bouncing_shooters_milestone.md).


Charging actors3A/3B v0021: [details](analysis/charging_actors_milestone.md).


Dashing actor3C v0023: [details](analysis/dashing_actor_milestone.md).


Pursuit shooters3D/3E and1A v0024: [details](analysis/pursuit_shooters_milestone.md).


Hopping actor3F v0025: [details](analysis/hopping_actor_milestone.md).


Actors40/41 and shots1B/1D v0026: [details](analysis/ambusher_milestone.md).


Orbit actor 42 / projectile 1C and scrolling regression checks: analysis/orbit_milestone.md (v0027).


First-scene intro reveal cadence and remaining bootstrap offsets: analysis/reveal_milestone.md (v0030).


All three intro scenes measured; remaining hardware sprite-table differences: analysis/intro_scene_diagnostics.md (unchanged v0030).


Deferred intro sprite upload and remaining SAT differences: analysis/intro_sat_milestone.md (v0031).


SMS overflow-dependent projectile allocation and remaining limits: analysis/sprite_overflow_milestone.md (v0032).


All 512 actor lists/assets and dungeon walkers 43..45 / projectile70: analysis/dungeon_walkers_milestone.md (v0033). Natural dungeon progression remains pending.

Dungeon base-room milestone v0034: [details](analysis/dungeon_world_milestone.md). All 512 source maps and native base-room loads checked; natural dungeon entrance/progression still pending.


Dungeon entrances milestone v0039: [report](analysis/dungeon_doors_milestone.md).


Dungeon scrolling v0040: [report](analysis/dungeon_scroll_milestone.md).


Persistent room cells v0041: [report](analysis/room_cells_milestone.md).


Dungeon key-door dispatch v0042: [report](analysis/key_doors_milestone.md).


Additional v0042 live controller/save checks: [report](analysis/key_door_gameplay_milestone.md).


Key-door redraw timing v0043: [report](analysis/key_redraw_milestone.md).

Room-clear passages and dungeon floor animation v0045: [report](analysis/room_clear_milestone.md). 49 handlers; source/native fixtures and live crossing checks. Loading phase and prolonged movement in room 17D remain to resolve.

Cleared dungeon loading v0046: [report](analysis/empty_dungeon_loading_milestone.md). Room 17D long-hold and floor-phase discrepancy resolved in PAL/NTSC fixtures; other IRQ/loading offsets remain.

Clear rewards and collectible keys v0048: [report](analysis/clear_rewards_milestone.md). 20 more reward handlers (69 total), 99-key cap and cold-save persistence checked. Next: 5ECD and push-block passage state.

Combat shutters and 27 additional completion handlers v0049: [report](analysis/shutters_milestone.md). C0A8/C0A9 are shutter state, not push blocks. Actual contact puzzles and natural progression remain incomplete.

Complete contact flags v0050: [report](analysis/contact_flags_milestone.md). 8192 isolated cases and PAL/NTSC live cache/shutter regressions pass. Next: translate actual contact effects in source script order; internal portals need full room loading/placement.

Eleven contact effects v0051: [report](analysis/contact_effects_milestone.md). 8192 isolated cases and 44 live PAL/NTSC contacts pass; remote target-room flags and repeat guards preserved. Next: 36 internal portals with original room loading/placement/timing, then remaining puzzle progression.

Internal portal source reference (production v0051): [report](analysis/portal_source_milestone.md). 72 source scenarios and 1440 full wipe frame maps verified. No native portal implementation yet; next translate source order, twenty-step wipe, arrival and dynamic loading.

Native internal portals v0054: [report](analysis/native_portals_milestone.md). 36 portals / 72 live crossings and 1440 visible wipe frames match; resume 47 exact, 25 one frame late. Next: refine state-8 IRQ/loading phase, remaining puzzle scripts and natural dungeon progression.


2026-10-10: v0056 adds 31 stationary room puzzle scripts. See analysis/stationary_puzzles_milestone.md. 496 selected fixtures and 124 live PAL/NTSC cases match SMS states; full game remains incomplete.


2026-10-12: v0060 adds ten stationary item rewards and the 6317 acquisition frontend. See analysis/item_acquisition_milestone.md. 160 targeted grant cases, 44 live PAL/NTSC cases, 20 stable VDP/sprite checks, ten save/cold-load cases. Post-confirmation animated-floor phase offsets remain; full game incomplete.


2026-10-12: ROM v0063 adds original SRAM-derived dungeon bitmap animation and improves item-message recovery timing. See analysis/dungeon_bitmaps_milestone.md. PAL controlled recovery matches; NTSC retains one-frame scan-phase offset. Natural global clock phase and full game remain unverified.


2026-10-12: ROM v0064 separates final dialogue acknowledgement from inter-page blinking; all six SMS final inputs pass PAL/NTSC. See analysis/final_dialogue_milestone.md. Initial loading and global clock phase still differ.


2026-10-12: ROM v0070 restores four dialogue scroll poses (2,3,3,2), faster exact tile conversion and single-word marker updates. Source/native first pose frames match in the opening PAL/NTSC test. Free-night display intervals also match in ten cases. See analysis/dialogue_scroll_milestone.md. Full dialogue/global clock/loading fidelity still incomplete.


2026-10-12: ROM v0071 restores the extra source 06D6 post-scroll bitmap publication. Complete first-scroll pose frame lists now match PAL/NTSC. See analysis/postscroll_milestone.md. Startup/dialogue/global-clock timing still differs.


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


v0176: paid-exit loading preserves exactly one source logical-clock tick while native conversion IRQ/audio continues. Source24 actual six-route empty/full-mask PAL/NTSC exits; native3072 full-loader cases(all256 masks and clock wrap),18528 rules,20 actual payment/exit/menu integrations pass. ROM1MiB checksum351C,versions/v0176-9a4471c0; full sources/symbols/four current reports/tools/source timing evidence archived115files. Original0397 word-fill2064 cases and live1FA7 clear51628T exact. Physical loading/reveal cadence,source IRQ/RNG and natural full progression remain incomplete. See analysis/paid_passage_clock_milestone.md.


v0177: quest gift631A now marks outside class1 bit2 and transforms/builds room before modal backup. v0176 baseline missing flag and primary3 repeat twice reproduced/retained.32 current PAL/NTSC gift contexts(flags0/128),1836 rules,two long hints,20 paid-passage integrations pass.24 real-door cases and8 explicit C7/55 outside-context fixtures; natural reachability of latter unproved. Static cells/maps,38 held tiles,menu/second UP andone reward compare;remaining NPC animation differences retained. All other production files identicalv0176.1MiB checksum3DD6;versions/v0177-3f4dbbc9 has163 source/evidence files andsix current reports. See analysis/quest_gift_persistence_milestone.md. Exterior leave/re-entry/SRAM gift persistence and full natural progression remain open. Timing models next2C63 hero/audio IRQ,then destination/mask loading correction;source refresh RNG/clipping/hardware still unfinished.


v0177 persistence follow-up:12 actual controller exit/re-entry paths,12 full592-byte save/fresh-Continue comparisons and12 cold-house no-repeat cases pass PAL/NTSC. Six real gift doors;initial progression/door fixtures explicit. Re-entry has no RAM writes after3400;world visited1 and traversalC0EC seeded before entrance. Save transfers actual gift state to established save-point route;uninterrupted route not claimed. Cold-house mode removes3100 item/equipment/visit injections and consumes actualSRAM;zero reward phases on two UP/menu attempts. ROM/every production source byte-identicalv0177. Four added reports and278 files archived under versions/v0177-3f4dbbc9/additional-persistence;original163-file snapshot preserved. See analysis/quest_gift_persistence_followup.md. Full natural progression and physical loading/IRQ/hero/RNG/clipping/hardware remain unfinished. Next return to2C63 hero/audio IRQ cost for physical paid-exit loading budget.


v0178: paid-exit music hooks now requestB0 fade before loading andworld82 before reveal,matching16D0/1CAF. MissingB0/late82 reproduced onv0177 PAL/NTSC baseline.24 live six-route mask00/FF music cases,1800 controlled reader/PSG snapshots,3072 native loader clocks,20 paid/menu integrations pass. Onlytwo hooks change;other production sources byte-identicalv0177.1MiB checksum3DDA,versions/v0178-a8d8ee11;193 source/evidence files,five reports archived. Foreground research beforepatch archived117files in analysis/hero-init-v0177:2C63 model13150 cases/475RAMbytes,24live/144phases,and24cumulative to-fade foreground paths/72comparisons exact. No physical frame-delay integration yet. Nextsourceaudio IRQ work/phase,other missinggenericloader audio hooks(ifproved),then foreground/IRQ alignment and subtract native spentwork for loadingbudget. RefreshRNG/fullnaturalprogression/clipping/hardware remain open. See analysis/paid_exit_music_milestone.md.


v0179: standard house/dungeon doors restore exit fade,hidden load,B0/destination music,foreground palette and contour reveal. Baselinev0178 retained in analysis/standard-door-baseline-v0178. Four detailed roundtrips show9 color steps each way/16 contours32ticks;source fades18;one native PAL house exit samples19 fade-in frames with pending initial VBlank. Full physical duration remains unequal.20 dungeon paths,16 gift contexts,12 controller re-entry paths,20 paid scenarios,24 paid music paths,3072 compiled paid-clock cases and3 save slots/Continue pass. Paid music validator now bounds first exit by hero0->1 destination idle;later combat-driven re-entry commands retained separately.1MiB checksum403C,versions/v0179-d018ed93,10reports and308source/selectedevidence files verified. Onlymain.c/paid_passage.inc/newdoor_transition.inc changed;audio reader/actors/quest logic unchanged. See analysis/standard_door_milestone.md. Next model source audio IRQ cost/phase and physical loading work;also investigate pending-VBlank boundary using source gate semantics,without arbitrary fixed frame delays. RNG/combat/fullnaturalplaythrough/clipping/hardware remain open.


v0180: reveal_world initial wait now capturesvtimer,wait_frame,waits until newIRQ before enablingdisplay. Exactonlymain.c patch;globalwait/audio/loader/othermodules identicalv0179. SGDKdisplay-off VBlankstatus returns without freshIRQ;dedicated1792-call scanlinesweep(224positions xdisplayon/off xexisting/fresh xregions) reproduces216NTSC/224PAL zero-tick disabledcalls;freshgate all1tick.12baselinefiles includingharness retainedanalysis/reveal-wait-v0179. Eight standarddoor transitions nowall18fade-in frames(previousPALhouseexit19),9colorsteps/16contours32ticks.20paidscenarios,3save/coldContinue slots,16deathContinuecontourimages,31capacityHUDsamples pass.1MiB checksum442A,versions/v0180-3f155979;6reports,2158source/selectedrawfiles archivedandverified. Seeanalysis/reveal_wait_milestone.md. NextsourceaudioIRQcost/phase andphysical loadingbudget;no fixed framedelay orcomplete timingclaim. RefreshRNG/combat/naturalplaythrough/hardware remainopen.


IRQ research afterv0180: separate read-only audioirq DLL records0137/01E3/0202/0205/0226 andfull-gatedaudio calls.24 six-route mask00/FF region paths preserve originalcyclearrays exactlyagainstarchivedv0179.675audio-onlyIRQs pass4050wrapper/state comparisons;C02Funchanged,bank/SP restored,C030decrement correct. Wrapper442/454T toRET excludingreader;wholefixedoverhead524/536T. Loadingreader observed657..17835T,notpredicted. Complete16D0..0ACE IRQbudget closeswithzeroresidual on24paths using measuredreader/fullgatedspans+derivedwrapper/vector/RET.124files archived/verifiedanalysis/audio-irq-v0180;analysis/audio_irq_cost_report.json andanalysis/audio_irq_milestone.md. ROM/allproductionsources identicalv0180. Next independentlypredictbank6reader branchwork andIRQphase fromstate,thencombinewithforegroundbudget/subtractnativespentwork. No physicaldelayintegrated;RNG/combat/fullnaturalprogression/hardware remainopen. Gitlocalprojectinitialized with180ROMs,tagv0180;verify_git_roms.py checksallreleasehashes. KeepGitupdated forfuturechanges;no remoteconfigured.


Audio prefix research afterv0180: independent original807E tempo/80C8 fade models predictstate400bytes andinstructioncost,including83EF stop/mute.10240isolated sourcecases(1024tempo+4096fade perregion) exact;wholebank6unpatched,IRQsdisabled. Live6D->96/fullmask PAL/NTSC2404helpercalls(601tempo+601fade perregion) state/cost exact;cyclearrays identicalarchivedv0179.147files archived/verifiedanalysis/audio-prefix-v0180;analysis/audio_prefix_cost_report.json,live_audio_prefix_cost_report.json,audio_prefix_milestone.md. ProductionROM/everyproductionsource byte-identicalv0180 and180GitROMhasheschecked. Nextarbitration8097,dispatch80FF/B0/musicstart andchannel/envelopecosts,thenfutureIRQphase/loadingalignment. No physicaldelayintegrated;RNG/combat/naturalprogression/hardware remainopen.
