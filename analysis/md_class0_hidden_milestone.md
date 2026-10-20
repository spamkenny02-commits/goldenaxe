# Chargement class0 avec affichage coupe

Le module natif peut maintenant transferer les motifs et la carte sur toute
l'image H32/224 quand le caller garde l'affichage coupe. Il conserve les blocs
RAM de 1 a 4 motifs, la capacite refresh, les autorisations Z80 et la garde
d'age. Il exclut les valeurs V brutes 229 a 234 et refuse ce chemin si
l'affichage est actif. Aucun passage H40. begin_hidden ne retablit jamais
l'affichage : le caller garde la responsabilite de la publication finale.

Les trois variantes executent chacune 48 chargements source par region.
Les motifs residents, 193 nouveaux motifs, 768 mots de carte et 32 couleurs
concordent avec les references. La RAM et l'image finale concordent aussi
avec le coeur sans instrumentation. Les deux variantes de diagnostic relisent
186624 mots par region sans ecart; le mode complet compare 768 checkpoints
RAM/audio par region. Les contrats natifs passent 57 controles de span et
35 controles de flux par region.

| Variante | Images du banc NTSC / PAL | DMA durant le chargeur NTSC / PAL |
| --- | ---: | ---: |
| hidden-readback | 6490 / 5437 | 312 / 292 |
| hidden-proof | 6676 / 5592 | 324 / 300 |
| hidden-production (options sans relecture) | 6490 / 5437 | 248 / 268 |

Ces images couvrent les 48 essais, pas une transition du jeu. Le nom
production ne signifie pas que le module est integre dans la ROM jouable.

L'[audit physique](md_class0_hidden_physical_report.json) identifie les
21024 DMA par une signature native unique revue, y compris la liberation
BUSREQ via A1. Les sequences de suppression/restauration du bit d'affichage
sont liees aux PC des marqueurs observes. Chaque transfert et chaque plage
palette tracee se trouvent dans cet intervalle. Le compteur horizontal est
controle contre la table H32 du coeur. Les valeurs V dupliquees sont exclues,
les phases source et l'ordre motifs/carte sont verifies. Le maximum de
retention du bus est 6130 ticks; le maximum entre echantillons prives Z80
est 16770 ticks, strictement sous 17100. Les plages CPU palette tracees
restent sous 24704 ticks sans BUSREQ. Le chemin sans trace est controle par
les donnees finales, sans pretendre mesurer sa plage CPU.

La reanalyse des trois anciens noyaux visibles donne exactement le meme
rapport que l'audit archive precedent. Le nouveau chemin ne remplace pas
leur garde VBlank.

Il reste jusqu'a 8.46 images de DMA apres la fin logique du chargeur. Les
2976 octets PSG par region concordent, sans emission anticipee ni ecart
d'intervalle intrarafale, mais les retards maxima restent 346575/379260 ticks
avec relecture, 2952315/2918520 avec les checkpoints complets, et
318720/290235 sans relecture (NTSC/PAL). Aucun seuil n'accepte ces retards
comme cadence fidele. La restauration d'affichage du banc attend la vidange;
elle ne prouve pas l'echeance originale du jeu SMS.

Prochaine etape : servir les travaux video pendant les attentes de livraison
audio, puis confronter la publication a l'echeance source. Les sprites,
les IRQ natives, le boot et le jeu complet restent a integrer/verifier.
La ROM jouable reste v0203, inchangee. Les preuves seront conservees dans
md-class0-hidden-v0203 apres relecture SHA/gzip complete, avant nettoyage.
