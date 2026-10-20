# Ordonnancement video/son pendant le chargement

Aucune des cinq politiques mesurees ne remplace le chemin de reference.
La ROM jouable reste v0203. Les nouvelles options restent desactivees par
defaut; aucun code natif du moteur ne change dans ce jalon.

Les [mesures comparees](md_class0_hidden_scheduling_comparison_report.json)
portent sur48 cas par region. L'attente finale de livraison audio est courte
(910 a1351 ticks) et ne contient aucun DMA. Y ajouter du service video
n'offre pas de gain exploitable.

Les lots de64 tentatives/4succes font passer2736 des3504DMA pendant le
chargeur, contre248/268 en reference NTSC/PAL. Mais ils retardent les PSG
jusqu'a5492505/5674755ticks, contre318720/290235. La diminution du reliquat
video ne constitue donc pas une amelioration de fidelite.

Le controle d'avance logique garde une reserve de17100ticks. Sa premiere
version lit directement l'horloge du producteur et invalide son compteur:
erreur0x401, aucun DMA, essai NTSC rejete et conserve. La version corrigee
utilise une copie privee de l'observateur; elle passe les donnees/horloges,
mais l'avance courante ne couvre pas le cout du travail natif suivant.
Les retards PSG restent proches de4millions de ticks. Cette reserve ne
constitue pas une preuve d'echeance.

L'attente d'une nouvelle sequence de publication avant de retenter un
transfert et le service aux deux fonctions de repetition ont aussi ete
mesures. Ils conservent les donnees mais degradent certains delais audio
ou le reaffichage. Ils restent des options de diagnostic.

L'[audit physique](md_class0_hidden_scheduling_physical_report.json) verifie
35040DMA dans les cinq variantes et deux regions, avec signatures natives
revues, affichage coupe, H32 et intervalle prive Z80 strictement sous17100.
La nouvelle allocation de registres du backoff est verifiee explicitement;
la liberation du bus passe par A0 au lieu de A1. Les images VRAM/CRAM et
les etats finaux restent ceux de la reference. Ces bancs sans relectures
intermediaires ne prouvent pas tous les checkpoints ni le jeu complet.

Le rapport mesure maintenant aussi le delai entre le reaffichage du banc
et la fin logique source24BF. Ce point est un repere mesure, pas encore
l'echeance d'activation d'affichage originale SMS. Aucun critere de cadence
complete n'est declare satisfait.

La generation par defaut reste identique octet par octet a1652230 pour
huit combinaisons de scene et quatre configurations d'horloge. Le prochain
travail doit mesurer le cout des refus d'admission DMA et de WAIT avant de
changer encore la politique de service. Les longs lots video sont ecartes.

Les captures, y compris le prototype invalide, sont conservees dans
md-class0-hidden-scheduling-v0203 avec verification integrale avant nettoyage.

Archive finalisee :1122references compressees;236595029octets generes retires,
180359118octets nets liberes. La reanalyse depuis les objets gzip restitue
exactement le rapport physique. Les rapports de comparaison et de defauts
regeneres concordent aussi avec les empreintes du manifeste.
