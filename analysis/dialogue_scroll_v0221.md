# V0221 : fin du défilement du dialogue

La v0220 attendait une image supplémentaire en NTSC après chacune des quatre
poses du défilement. Les instructions SMS 068D..06D6 montrent qu’après la
quatrième pose, le terminateur zéro conduit directement à la republication du
bitmap : aucun cinquième déplacement des lignes ne précède cet appel.
La v0221 conserve l’attente entre les trois premières poses et supprime celle
qui suivait la quatrième. Le même chemin est utilisé par le récit et les
conversations ; aucun texte ou écran précalculé n’est injecté en production.

## Résultats ciblés

Sur le premier défilement naturel après création du personnage, sans injection
RAM, les 130 motifs de chaque pose concordent avec la source. Les images de
présentation complète sont :

| Déplacement cumulé | NTSC SMS et MD | PAL SMS et MD |
| --- | --- | --- |
| 2 pixels | 2202–2203 | 2202 |
| 5 pixels | 2205–2206 | 2204 |
| 8 pixels | 2208–2209 | 2206 |
| 10 pixels | 2211–2214 | 2208–2210 |

Le premier bitmap complet suivant apparaît aux images 2215–2217 sur les deux
machines en NTSC. En PAL il apparaît à 2211 sur les deux machines, mais dure
jusqu’à 2213 sur MD et 2212 sur SMS. Cet écart reste explicitement ouvert.
Le contrôle strict des quatre poses, qui échouait en v0220, passe désormais.

Les régressions ciblées couvrent aussi les six conversations de PNJ et un
trajet naturel de conversation/restauration en NTSC, les six boutons de
validation finale du récit dans les deux régions, et 302 images cohérentes
de texte du premier PNJ en PAL/NTSC. Le contrôle des pixels de texte est lié
au SHA exact de cette ROM et conserve le correctif VBlank de la v0220.

Les registres vidéo extraits et les snapshots de motifs en fin d’image ne
prouvent pas chaque cycle de transfert ni tous les pixels pendant celui-ci.
Les autres pages, la cadence complète, le hasard Z80, tous les parcours et la
console physique restent à terminer ou vérifier.

ROM : versions/v0221-0cc51636/gaw-megadrive-v0221.bin, 1 Mio.
SHA-256 : 0cc51636efdff6e1bed7c0e74808d0ce5589f9333718abdccb392cef7daa1013.
Checksum Mega Drive : 1087.
