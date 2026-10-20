# Rafraichissement prive de l'horloge et autorisations DMA datees

La ROM jouable reste **v0203**, SHA-256
`7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7`.
Ce jalon concerne le chemin experimental natif 68000 avec sortie PSG Z80.
Il ne constitue pas une integration du nouveau moteur dans le jeu.

## Defauts observes et correction

Elargir la fenetre aux lignes brutes224..228 avec l'ancien pilote semblait
fonctionner sur un atlas seul, mais le service pendant le son a revele des
prelevements espaces de17145 ticks, au-dessus de la borne stricte17100.
Les essais qui debordent le blanking ou cette borne sont rejetes, meme si
les pixels finaux ou les compteurs natifs semblent corrects.

`md_psg_refresh_z80.asm` reprend le pilote existant et met a jour son compteur
prive apres la publication coherente. Le tuple publie sequence/V/compteur
reste inchange ; la relecture privee ne publie pas de second tuple.
Le profil ready3 expose explicitement cette capacite. Les blocs128octets
avec relecture et service pendant le son passent ensuite PAL/NTSC, avec
un maximum16785 ticks entre prelevements. Les essais complets et les blocs
partiels1/2/3tuiles passent separement.

Le passage a256octets a expose deux autres echecs : un depart trop tardif
(V252) et une autorisation trop ancienne. `md_psg_grant_z80.asm` publie donc
une autorisation fraiche encodee `(V << 1) | 1` apres une publication et un
rafraichissement prive. Le profil ready7 annonce cette capacite supplementaire.
Les consommateurs booleens existants acceptent toujours toute valeur non nulle.
Le compteur prive est controle independamment : lire un nouveau V pour
l'autorisation ne doit pas masquer un intervalle trop long entre ses mises a jour.

L'API optionnelle accepte1..8tuiles avec un jeton distinctD600. Au-dessus
de4tuiles, elle exige cette capacite, aucun descripteur PSG en attente ou
en cours, et un V d'autorisation dans la meme ligne que la garde sous BUSACK.
Les controles sont refaits sous le bus. Le banc adaptatif choisit4tuiles
lorsque des ecritures sonores sont en attente et8sinon. Les tonalites PSG
deja actives continuent ; le test ne coupe pas le son pour transferer.
Les lignes brutes229..234 sont exclues ; le profil7 exclut aussi252.
L'ancienne API1..4 et son pilote restent disponibles et inchanges.

## Preuves et limites

Le [service adaptatif pendant la livraison audio](md_z80_psg_video_source_span8_stamped_delivery_report.json)
passe48cas par region :2976octets PSG par region,393216mots video relus
sans difference,512tuiles finales comparees a une conversion planaire
independante, et RAM/VRAM/image identiques avec le coeur sans instrumentation.
Les tailles observees sont40blocs4 +3052blocs8 en NTSC,44blocs4 +3050blocs8
en PAL. Les emissions anticipees et les intervalles intrarafale sont controles.

L'[analyse des chemins physiques compiles](md_z80_stamped_video_windows_report.json)
retrouve3092/3094transferts, tous integralement en VBlank ; maintien maximal
du bus9649ticks, garde-vers-liberation8354ticks. Seulement7/11transferts
precedent le dernier octet PSG, et aucun ne precede la fin du chargement.
L'intervalle maximal entre mises a jour privees vaut15615/15870ticks,
strictement sous17100 ; les lectures V supplementaires ne remplacent pas ce controle.

Le [banc complet des16etats intermediaires](md_z80_psg_video_source_span8_stamped_proof_report.json)
passe aussi PAL/NTSC, avec3072blocs de8tuiles et393216mots relus par region.
Il termine en23968/13770images ; ses copies de diagnostic ajoutent une charge
qui interdit de comparer directement cette duree au banc allege.

Les [609 controles natifs par region](md_video_span_contract_stamped_grant_report.json)
verifient les frontieres, les deux masques de fenetre, les modes, les capacites,
les rejets atomiques et la conservation du jeton. Les rejets verifies ne lisent
pas le faisceau et ne prennent pas le bus. Le [test audio long](md_z80_psg_stamped_output_core_report.json)
passe48cas source et26synthetiques par region, avec pression de file,
bouclages des curseurs8bits, compteur16bits et dates source32bits.

Ces tests ne prouvent pas un debit suffisant pour le rendu du jeu. Le banc
avec relecture finit en16326/10594images, contre14047/9148pour les blocs4
rafraichis : le nombre de commandes diminue, mais le temps total regresse.
Ce protocole est un resultat de surete experimental, pas un gain de cadence.
L'ancienne API avec l'ancien pilote reproduit exactement le noyau, les evenements
et la RAM de la reference precedente.

Carte, palettes, sprites, service durant les vrais calculs, IRQ natives et
echeances de rendu restent a integrer et mesurer. Les marqueurs PSG ajoutent
des ecritures et empechent encore une preuve de l'onde sonore originale.
Le Git reste local. L'archive `md-z80-refresh-grants-v0203` conserve
3600references compressees, y compris les essais rejetes. La relecture complete
avec empreintes a precede la suppression de4164853060octets generes ;
3277462378octets nets liberes (environ3,05Gio). Une seconde relecture
independante passe. La reanalyse apres nettoyage reproduit le rapport physique
octet pour octet depuis cette archive.
