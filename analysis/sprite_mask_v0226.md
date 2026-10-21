# V226 : masque de sprites plus rapide, premier cristal et sortie verifies

Le calcul du masque SMS est allege dans la ROM68000 : les sprites entierement
dans les192 lignes emploient huit bits constants ; les sprites coupes conservent
le traitement general. Le parcours des192 compteurs est saute quand la liste
contient au plus huit entrees. Les recherches de motifs ignores ne parcourent
plus les clones deja ajoutes par ce meme passage, qui utilisent une autre plage
de tuiles. La limite de huit sprites par ligne et le terminateurD0 sont conserves.

Les fonctions C exactes avant/apres passent133120 cas compiles sur l'hote :
comptes0..64,256 valeursY,quatre dispositions,deux modes de preparation et0..4
transferts de base. Ce banc utilise des stubs VDP ; il ne mesure pas le68000.

Les ROMs jouables225/226 sont ensuite executees sur les memes fixtures PAL/NTSC.
Les90 images de plans de sprites sont identiques :4423680 pixels compares.
Les cas couvrent heros seul,12 acteurs superposes,coupes haute/basse etD0.
Le temps median entre entree et retour de la routine baisse de21 a86% selon
le cas. Ce temps peut inclure les interruptions : ce n'est pas un gain global
de FPS. Douze compositions independantes de VRAM/CRAM restent coherentes.

La cadence globale reste incomplete. Un passage naturel de disparition du
boss montre encore cinq images avec le meme compteur sur226, contre une dans
un passage225 et aucune dans le passage SMS. Les rencontres, attaques et
particules different ; ces parcours ne constituent pas une comparaison de
performance a charge identique. Les fixtures identiques prouvent le gain du
masque, sans prouver la disparition de tous les depassements de frame.

Le parcours critique du premier donjon est maintenant verifie depuis une
nouvelle partie :13 salles distinctes, deux cles obtenues/deux consommees,
interrupteur194,boss68,vaincu,cristal acquis et sortie versB9. La capacite de
vie passe de24 a32,la recharge avance d'un point toutes les deux images et
le drapeau du premier cristal reste80 apres la sortie. La musique de la fenetre
est restauree vers le theme exterieur a la fin du parcours.

La SMS finit sans mort ; le parcours226 utilise une mort et le Continue normal.
Les boutons complets se rejouent dans des processus neufs, sans observation
RAM,avec RAM finale et PNG identiques a leur propre execution. La carte finale
et les256 drapeaux persistants correspondent entre SMS/MD. Les durees,PV et
decisions aleatoires ne sont pas identiques. Le flux Z80 R reste a porter.

La fenetre LE CRISTAL est comparee a un instant stable :150 mots de carte,
les pixels des tuiles utilisees et9600 pixels RGB apres normalisation de palette.
Les captures de la ROM SMS et de la ROM226 ont ete inspectees. Les salles
annexes et leurs objets,les autres donjons,la campagne entiere,la console reelle
et la fidelite complete du son/hasard/cadence restent hors de cette preuve.

Reproduction :

- `python tools/validate_sprite_mask_equivalence.py`
- `python tools/validate_sprite_mask_production.py`
- `python tools/validate_world_frame_coherence.py`
- `python tools/verify_first_dungeon_story.py --verify-existing`
- `python tools/summarize_sprite_mask_release.py`

Les rapports de parcours conservent leurs prefixages et leurs boutons. Les
essais de pilote echoues et profils sont conserves comme diagnostics. Aucune
RAM/ROM/SRAM preparee n'alimente les parcours naturels retenus.
