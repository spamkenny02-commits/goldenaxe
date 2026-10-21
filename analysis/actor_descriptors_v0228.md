# V228 : descriptions graphiques lues directement par le68000

Le build produit8425 mots a partir des8426 octets du bloc de descriptions
de la SMS. Il couvre chaque decalage d'un octet, y compris les adresses impaires.
Le68000 lit ces valeurs dans son ordre d'octets natif. Les descriptions du
cristal et de la hache conservent leurs chemins speciaux. Le chemin courant
est integre aux appelants ; les cas rares restent dans une fonction separee.
La table utilise16850 octets de ROM et aucun tampon RAM supplementaire.
La cartouche tient toujours dans1Mio et la fin de BSS resteE43C.

La v227 est une compilation intermediaire conservee : ses valeurs sont exactes,
mais le compilateur avait remplace des lectures integrees par des appels,
ce qui ralentissait la scene mesuree. Utiliser la v228.

Les helpers C exacts avant/apres passent les65536 adresses16bits dans le banc
hote. Le miroir de test est complete apres la fin du bloc pour tester le repli
sans lecture indefinie ; cela ne rend pas valides les adresses hors bloc dans
le jeu. Tous les8425 mots sont aussi verifies dans le binaire68000.

Sur les memes scenes figees des ROMs226/228 en PAL/NTSC, les90 plans de sprites
restent identiques :4423680 pixels compares. La preparation avant masquage de
la scene a douze acteurs prend environ5% de temps en moins. Le cas heros seul
reste pratiquement identique. Les mesures peuvent inclure les interruptions ;
ce ne sont pas des pourcentages globaux de FPS. Douze compositions independantes
de VRAM/CRAM restent coherentes.

Le parcours depuis une nouvelle partie jusqu'au premier boss, au cristal et
a la sortie est rejoue sur228 sans mort. Les256 drapeaux persistants et1280
octets de carte finale correspondent a la SMS. La fenetre du cristal, le passage
de24 a32 points de vie, la recharge et la musique finale sont verifies. Le flux
de boutons se rejoue dans un processus neuf, avec RAM et PNG finaux identiques
a sa propre execution. Le pilote d'attaque a ete ajuste dans les outils pour
eviter un blocage d'alignement ; la logique de combat du jeu n'est pas modifiee.

Dans ce passage, les182 observations etat/compteur de disparition du boss
correspondent a la SMS sans image repetee. Cela ne prouve pas tous les delais :
les rencontres et particules different encore, et le hasard Z80 reste incomplet.
Les salles annexes, les autres donjons, la campagne et la console reelle restent
a couvrir. L'essai23 incomplet est conserve comme diagnostic du pilote.

Reproduction :

- `./build.ps1`
- `python tools/validate_actor_descriptor_words.py`
- `python tools/validate_sprite_mask_production.py --descriptors`
- `python tools/validate_world_frame_coherence.py`
- `python tools/verify_first_dungeon_story.py --verify-existing --native-final md-auto-25 --native-modal md-auto-24`
- `python tools/summarize_actor_descriptor_release.py`
