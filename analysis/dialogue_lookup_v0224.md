# V224 : recherche directe des caracteres de dialogue

La recherche descendante de 191 entrees est remplacee par une table de
256 octets dans le jeu 68000. La table est generee au build a partir du
charset extrait de la SMS. Elle conserve le dernier doublon, le remplacement
B0 par le tiret, le glyphe de repli 80 et le passage en petite police.

La meme premiere page du recit entre en attente a l'image 1603 au lieu de
1606 en NTSC. La SMS atteint cette attente a 1596 : il reste sept images
de retard. En PAL, l'attente reste a 1601 contre 1583 sur SMS. Le debut du
recit reste a 1490 sur les deux ROMs MD. Aucun pourcentage global de vitesse
ou de fidelite n'est deduit de cette mesure.

Les fonctions C exactes avant/apres sont compilees sur l'hote et comparees
pour les 256 octets dans les deux modes de police : 512 cas identiques.
Les 26 fixtures de texte executees dans les ROMs SMS et 68000 passent.
Les 37 publications terminees de la premiere page (29 bitmaps distincts)
sont conservees dans l'ordre en PAL et NTSC. Les quatre poses du premier
scrolling et leurs durees restent identiques a la source. Le controle des
302 images de texte interieur ne trouve aucun pixel incoherent avec la VRAM.
La validation d'une page intermediaire continue a rejeter les directions.

Le portage complet, les autres conversations, le hasard Z80 et la cadence
globale restent incomplets ou non verifies. Cette version optimise le texte,
sans pretendre resoudre tous les delais de dialogue.

Reproduction :

- `./build.ps1`
- `python tools/profile_dialogue_preparation.py` (puis `--pal`)
- `python tools/validate_dialogue_controls.py`
- `python tools/validate_dialogue_scroll.py`
- `python tools/validate_dialogue_vblank.py`
- `python tools/validate_dialogue_page_buttons.py`
- `python tools/validate_dialogue_lookup_release.py`

Les profils historiques v0223 et les profils v0224 sont conserves dans
analysis. La validation du gain les compare sans modifier les ROMs jouables.
