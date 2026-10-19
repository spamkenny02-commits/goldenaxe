# Réduction de latence du service PSG Z80

Le programme Z80 de sortie sépare désormais ses relevés internes de ligne de
la publication d'une horloge au 68000. Le compteur interne reste en mémoire Z80,
sans registres alternatifs. Durant la copie, la préparation, l'attente critique
et la rafale, le numéro de séquence public reste impair : le client 68000 ne peut
pas accepter un ancien horodatage. La publication reprend pendant les périodes
d'attente éloignées de l'échéance ou lorsque la file est vide.

Le relevé après révocation de l'accord BUSREQ est conservé : le 68000 peut avoir
arrêté le Z80 avant cette révocation. La copie des six octets de métadonnées est
déroulée avec six LDI ; les valeurs restent copiées localement avant acquittement
du descripteur. Les rafales de sortie et le protocole 68000 restent inchangés.

Les mesures suivantes portent sur les mêmes 24 chargements source, deux origines
logiques et deux régions physiques. Elles incluent les cas synthétiques et la
session longue. Les horodatages proviennent de l'observateur Genesis Plus GX.

| Version du service | Retard maximal NTSC, ticks maître | PAL |
| --- | ---: | ---: |
| Premier service conservé | 182 865 | 182 460 |
| Suppression du relevé au milieu de la copie | 149 400 | 153 930 |
| Relevés privés pendant le traitement | 87 810 | 87 405 |
| Relevés privés, métadonnées déroulées | **84 390** | **84 345** |

Le retard maximal baisse d'environ 54 %, à environ 1,6 ms. Il demeure excessif :
les sorties entre descripteurs proches accumulent encore du retard. Cette étape
valide un transport plus rapide, pas un ordonnanceur fidèle prêt à intégrer.
Le retard minimal n'est pas amélioré (3 960 ticks dans les deux régions).

Le [rapport final](md_z80_psg_private_unroll_report.json) conserve les empreintes
du noyau, du pilote, de ses sources et des captures. Les 5 952 octets source,
leur ordre et les points de contrôle natifs restent exacts. Les 488 intervalles
internes de rafale contrôlés restent exactement à 315 ou 630 ticks. Les sessions
longues conservent la saturation et les rebouclages de curseur, compteur et date.
L'état RAM final et l'image d'arrêt concordent avec le cœur sans observateur.
La vérification des publications repose sur les lectures physiques indépendantes,
et ne déduit pas l'heure du seul compteur publié par le pilote.

Deux réductions plus agressives sont écartées et conservées dans l'archive :

* `lean-fetch` supprime aussi le relevé d'entrée après BUSREQ : cinq échecs natifs
  en NTSC, avec une erreur d'horloge. Le test s'arrête avant le PAL.
* `copy-prepare` conserve les publications complètes mais supprime le relevé après
  copie : le cas NTSC 74 atteint un intervalle de lecture de 17 220 ticks,
  au-delà de la borne de 17 100. Il est rejeté avant le PAL.

Les variantes acceptées intermédiaires disposent de rapports séparés. L'option
`--variant` du banc crée des répertoires et rapports distincts afin de conserver
la provenance de chaque mesure. L'ancien rapport n'est pas réécrit.

Le producteur source termine toujours avant la restitution temporisée. Le calcul
68000 simultané est un témoin polynomial, pas encore le véritable chargement.
Ces tests masquent les interruptions natives et n'exercent pas de DMA vidéo.
Ils ne prouvent ni la cadence globale depuis le boot, ni l'intégration complète,
ni le fonctionnement sur console réelle. L'arrêt immédiat sur erreur reste à
définir ; l'API actuelle ne fournit que l'arrêt après vidage.

La prochaine étape doit préparer les descripteurs suivants pendant les attentes,
pour éviter de tout copier et préparer après la dernière sortie de la rafale
précédente. Elle devra conserver l'horloge non ambiguë, l'acquittement après copie,
la protection BUSREQ, puis mesurer les échéances avec le vrai producteur vivant.

La ROM jouable recommandée reste **v0203**, inchangée. Les captures et sources
sont conservées dans `analysis/md-z80-psg-latency-v0203` avant nettoyage vérifié
des fichiers générés. Le Git reste local et le portage complet reste en cours.
