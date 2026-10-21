# Historique résolu par v0218

L’arrêt SAT et la publication ont été intégrés dans la ROM jouable v0218.
Voir [le jalon final](world_publication_v0218.md). Le compte rendu ci-dessous
conserve les constats des prototypes et ne décrit plus l’état courant.

---

# WIP : terminateur SAT SMS D0 et publication raster PAL

Ne pas recommander les ROMs v0211..v0214. La ROM racine, la sortie ROM/symboles
et le README pointent de nouveau vers v0210. Les sources main.c restent
modifiees en local pour poursuivre le travail; Git main distant reste41c93c4.

La correction courante conserve le code chaud de v0210 et coupe le lien
MD precedant le premier Y source208. Si le marqueur est en tete, l'entree0
est entierement vide et non liee. Les autres acteurs restent en RAM.
Le chemin rare est `terminate_world_sprite_list`, cold/noinline.

Le diagnostic v0214 (b224e777, checksum712F) verifie40 images sur4 variantes:
marqueur en tete et apres prefixe, NTSC/PAL. Les entrees8 sont cachees en tete;
les prefixes24 en NTSC/28 en PAL sont conserves, les queues28/24 cachees.
Types d'acteurs, salle et etat12 restent inchanges. Le controle strict sans
`--diagnostic` refuse la ROM a cause du raster PAL; le rapport porte
explicitement `release_accepted:false`.

Les captures naturelles NTSC testees restent identiques. En PAL, image3120,
5 pixels (169,36)..(174,37) deviennent verts alors que la reference v0210
et le plan VRAM final attendent les couleurs3/3/14/14/1. La VRAM finale
reconstruite concorde: le controle des seuls octets VRAM aurait manque le bug.
Ne pas assouplir ce gate pour declarer la ROM jouable validee.

Les variantes211 (retour count aux appelants),212 (fusion des scans) et213
(coupure directe des liens) ont aussi montre des differences raster naturelles;
212 deplace meme la phase d'un acteur NTSC.214 isole le chemin rare mais ne
resout pas le moment de publication. Toutes les ROMs sont conservees.

Suite: instrumenter les ecritures effectives SAT/tuiles autour PAL3120, puis
rendre la publication atomique au bon VBlank. Le double buffer de clones ne
suffit pas a prouver la coherence du SAT pendant le balayage. Examiner aussi
les appels multiples update_hero_sprites dans une meme image et le contexte
sprite cache du VDP. Une mise en file VBlank doit conserver la cadence source
et ne pas decaler arbitrairement toutes les poses d'une image.

Fichiers:tools/validate_playable_sprite_end.py; son mode strict reste le gate.
Les snapshots candidat/main/symboles sont dans validation/playable-sprite-end-v0214
ou l'archive de preuves. Pas de nouveau push de code non valide.
