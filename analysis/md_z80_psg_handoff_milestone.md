# Passage direct entre commandes PSG préparées

Le pilote expérimental à seize tampons conserve désormais ses en-têtes dans
une page alignée, `0200..02FF`. Les curseurs locaux avancent par addition de
16 sur l'octet bas, sans test de dépassement de page. Les valeurs restent dans
la page `1800..18FF`. Le protocole interprocesseur, ses dates et ses valeurs
restent inchangés. Les chargements et le lecteur source restent en 68000.

Après une rafale, le Z80 effectue un relevé de ligne puis examine la commande
locale suivante. Si sa ligne est atteinte, il charge directement ses registres
de sortie ; si elle est passée, il émet directement. Ce chemin conserve l'accord
BUSREQ révoqué, `busy` actif et la séquence publique impaire. Il évite de refaire
ces écritures et un relevé tout juste effectué. Les commandes sur une ligne
future repassent par le chemin général. Une échéance dépassée après une véritable
attente verticale conserve un nouveau relevé avant émission.

Le [rapport retenu](md_z80_psg_ready_handoff_report.json) correspond exactement
aux sources et captures conservées. Les résultats sont mesurés dans Genesis Plus GX.

| Variante | Retard maximal NTSC, ticks maître | PAL |
| --- | ---: | ---: |
| Préparation anticipée précédente | 32 385 | 33 795 |
| Suppression du relevé tardif systématique | 24 150 | 24 300 |
| Tampons alignés, sans garde d'attente spécifique | 21 720 | 21 675 |
| Garde rétablie après attente verticale | 24 300 | 24 705 |
| Garde conservée, passage direct sur ligne atteinte | **21 720** | **20 985** |

Le retard maximal descend autour de 0,4 ms, mais demeure supérieur à une ligne
vidéo. Le retard minimal mesuré est de 3 705 / 3 525 ticks. Ce pilote ne satisfait
toujours pas une livraison fidèle aux échéances source et reste hors du jeu jouable.

Les 5 952 octets issus des 24 chargements natifs, avec deux origines et deux
régions physiques, conservent ordre et points de contrôle. Les 24 rafales
partielles, les 64 commandes mixtes parcourant les seize positions et les
512 commandes longues restent testées par région. Les 1 192 intervalles internes
à 315/630 ticks sont exacts. La profondeur de quinze commandes préparées et les
64 préparations de la session finale restent observées. Les saturations et
rebouclages des curseurs, du compteur et des dates restent exercés.

Les 2 067 publications d'horloge observées concordent avec les lectures vidéo
physiques indépendantes. Les écarts de compteur sont au plus de cinq lignes.
L'intervalle de lecture maximal est de 16 935 / 16 890 ticks, sous la borne de
17 100 dans ces cas ; cette marge étroite ne prouve pas toutes les phases
possibles. Les prises de bus restent bornées et sans chevauchement des intervalles
internes des rafales vérifiées. Le calcul 68000 témoin, la RAM finale et l'image
d'arrêt restent conformes à leurs contrôles indépendants.

Deux extensions aux commandes futures sont rejetées : `ready-near` (trois lignes)
atteint 17 820 ticks entre lectures sur le cas NTSC 171 ; `ready-two-lines`
atteint 17 520 sur le cas NTSC 151. Les bancs s'arrêtent avant le PAL. Leurs
captures et sources sont conservées, mais le fichier du pilote est restauré
octet pour octet depuis la variante `ready-handoff` vérifiée.

La ROM jouable reste **v0203**. La préparation source se termine encore avant
la restitution ; le calcul parallèle est un témoin polynomial. Les DMA,
interruptions natives, entrées, phase depuis le boot, abandon immédiat et console
réelle ne sont pas validés par ce banc. La prochaine étape reste la réduction
de l'attente finale et du coût de sortie, avec une marge d'horloge prouvée,
puis le raccordement au vrai producteur vivant. Le portage complet est en cours.

L'archive locale `analysis/md-z80-psg-handoff-v0203` conserve ces essais avant
nettoyage avec décompression et vérification des empreintes. Sources, ROM SMS,
ROMs numérotées et historique Git sont préservés. Aucun envoi Git distant.
