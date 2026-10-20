# Fond class0 natif : motifs ROM, carte MD et palettes

La ROM jouable reste v0203, SHA-256
`7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7`.
Le nouveau module `md_class0_video_stream` n'est pas encore raccorde au jeu.
Il remplace l'atlas de diagnostic dans les nouveaux noyaux par un vrai fond
class0 et son HUD, sans sprites ni garantie de cadence complete.

## Donnees et propriete

Le point1706 libere193motifs issus de la ressource ROM du chargeur class0.
Le module copie au plus4motifs convertis dans son tampon RAM, prepare un
jeton DMA et le conserve pendant WAIT. Cette copie evite les traverses
impossibles d'une frontiere ROM128Kio au milieu d'un motif32octets.
Les193motifs forment49blocs (48de4, puis1de1).

Le point1deb traduit768mots de table SMS avec le module `source_class0_video`
existant et conserve la copie dans le flux. Les24lignes de32mots sont
transferees a BG_A, lignes2a25, avec un pas physique128octets (plan64x32).
Les indices de motifs, palettes, priorites et retournements sont preserves.
Le point24bf copie et convertit32couleurs. Elles partent par CPU apres les
motifs et la carte, avec une garde de blanking. Le module ne change pas H32.

Le flux possede son jeton, son tampon et ses copies de carte/palette jusqu'a
la fin. Il exige un objet initialement nul, un seul proprietaire du VDP,
les IRQ natives masquees et une disposition stable H32/224/BG_A64x32.
Les entrees nulles, les ordres de phases invalides et la reutilisation d'un
flux actif sont rejetes. Une erreur reste memorisee. Un vrai abandon/reprise
du moteur complet et l'integration dans la boucle du jeu restent a faire.

Le banc initialise les motifs residents avec les ressources ROM utilisees
par `enter_initial_room` : menu3040, nombres1e00, policeHUD1a00, motifsHUD3600,
et l'icone1d80 remappee. Le module ne les recharge pas : les319emplacements
hors du prefixe sont verifies intacts. Cette initialisation de ressources
ne prouve pas le deroulement complet du boot ni tous les etats d'inventaire.

## Verification des donnees et du son

Trois variantes finales passent48cas source par region physique PAL/NTSC :

| Variante | Images totales NTSC / PAL | DMA avant fin du chargement NTSC / PAL |
| --- | ---: | ---: |
| [16etats, relectures et trace palette](md_z80_psg_class0_scene_bounded_proof_report.json) | 12210 / 8881 | 25 / 42 |
| [Allegee, relectures, palette sans trace](md_z80_psg_class0_scene_bounded_native_report.json) | 12188 / 8812 | 12 / 15 |
| [Sans relectures de diagnostic](md_z80_psg_class0_scene_production_report.json) | 13086 / 8144 | 12 / 13 |

Le nom de la derniere variante designe les options du chemin, pas une
integration de production. Le temps NTSC augmente en supprimant les
relectures : la phase des tentatives reste determinante. La grande majorite
des3504DMA par region termine encore apres le chargement. Aucune echeance
par image ni vitesse equivalente au jeu SMS n'est etablie.

Chaque cas valide49blocs de motifs,24lignes et une publication de couleurs.
Les modes avec relecture comparent par region185088mots VRAM et1536mots CRAM,
soit186624mots sans difference. Sur les deux variantes et deux regions,
cela represente746496mots relus. Le dernier etat physique verifie en plus
les193motifs face au miroir source reel, les319motifs residents, les768mots
traduits et les32couleurs, independamment des compteurs du flux.

Les2976octets PSG, dates logiques, IRQ et etats finaux concordent par region.
Le mode complet compare directement chacun des16etats RAM/audio avec la
reference immuable en ROM :768comparaisons de checkpoints par region,
sans recopier cette reference dans l'etat execute. Les snapshots d'horloge
restent controles. Aucune emission anticipee ni deviation des intervalles
intrarafale n'est acceptee ; aucun seuil de retard ne declare la cadence valide.
La RAM/VRAM/image finale concorde avec le coeur sans instrumentation.

## Garde physique et defauts detectes

Le premier prototype reserve encore11776octets de snapshots inutilises dans
le banc allege, en plus du nouveau flux. SGDK s'arrete dans VDP_resetScreen
pour manque de memoire avant le premier cas. Le noyau, la RAM et la pile
sont conserves. Le mode allege n'alloue plus ce grand tampon ; le mode complet
compare les etats aux checkpoints plutot que d'en conserver une seconde copie.

Une seconde verification expose une admission trop tardive des lectures CRAM :
la publication et ses32relectures prennent environ7,2lignes, et certains
spans commencent a la ligne physique255ou256 puis traversent le debut d'image.
Les lectures de diagnostic depassent le blanking meme si les etats natifs
et l'horloge PSG passent. Ces essais sont retires du chemin retenu.

La nouvelle garde admet la palette seulement en V brut235..243, en H32,
avec de la marge avant la fin du blanking NTSC. Les compteurs de relecture
sont accumules localement. Leur cout reste important : le maximum observe
vaut24668ticks. Le changement de fenetre, et non une promesse d'acceleration,
etablit ici la securite du span complet.

L'[analyse physique](md_class0_scene_physical_report.json) retrouve21024DMA
par signature exacte du code compile, puis controle toutes les gardes HV,
les maintiens et les disponibilites des phases. Tous restent en VBlank.
Les maintiens maximaux valent6998ticks. Les96spans CPU traces de publication
et relecture palette restent aussi en VBlank, sous8lignes, sans prise du bus
Z80. Cette duree CPU n'est pas la borne de l'horloge privee : le Z80 continue
a la mettre a jour. Sa borne stricte reste17100ticks, et le maximum constate
sur les six captures vaut16785. Aucun assouplissement de cette borne n'a lieu.

Le module normal n'emet aucun marqueur PSG. Un crochet active uniquement dans
le banc trace la palette ; deux variantes testent le chemin sans ce crochet.
Les autres marqueurs du banc subsistent : l'onde sonore originale complete
n'est donc toujours pas prouvee. La fenetre CPU du chemin sans trace n'a pas
une mesure directe de debut/fin ; il garde les controles natifs et CRAM decrits.
Les [29controles d'interface par region](md_class0_stream_contract_bounded_report.json)
verifient aussi ordre, copies possedees, jeton conserve, faute persistante
et rejets avant lecture HV ou prise du bus.

## Integration suivante

Ce banc garde l'affichage actif pour exercer les transferts contraints.
Le vrai changement de banque classe0 se deroule affichage coupe : il faut
maintenant exploiter ce contrat avec des blocs courts H32 egalement durant
les lignes normalement actives, toujours sous les gardes de l'horloge.
Le vieux chemin monolithique H40 ne convient pas directement : le compteur
horizontal utilise par le son doit garder sa convention H32.
Ensuite viennent la publication de l'image complete au bon point source,
les sprites, les IRQ natives, les autres classes de graphismes et les entrees
au depart du vrai boot. Aucun jeu complet ni materiel reel n'est valide ici.

Le README et le Git restent locaux. L'archive `md-class0-scene-v0203` conserve
1790references compressees, prototypes et defauts compris. La relecture complete
et les empreintes precedent la suppression de1488923376octets generes ;
1164567172octets nets liberes (environ1,08Gio). La relecture independante passe
et la reanalyse depuis les captures archivees reproduit le rapport physique
octet pour octet apres nettoyage.
