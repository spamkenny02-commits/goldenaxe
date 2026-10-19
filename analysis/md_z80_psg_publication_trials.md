# Essais de publication native : aucun changement retenu

Cinq essais ont été exécutés avec le chargement 68000 réel et le pilote
Z80 huit/vingt. Les mesures restent celles d'un banc instrumenté sans
affichage, DMA ou interruptions natives. La ROM jouable reste **v0203**.

| Essai allégé | Retard maximal NTSC | PAL |
| --- | ---: | ---: |
| Référence huit/vingt | **169 395** | **169 605** |
| Planification spécialisée des paquets à un octet | 169 605 | 169 455 |
| Contrôle anticipé de l'accord avant préparation du transfert | 176 730 | 191 805 |
| Descripteurs différés, nouvelle tentative au paquet suivant | 4 014 570 | 3 928 890 |
| Différés, service aux fonctions d'horloge source | 1 057 245 | 1 068 015 |
| Différés, service supplémentaire aux blocs d'horloge inline | 1 343 730 | 1 335 375 |

Les nombres sont en ticks maître. L'essai à un octet réduit le temps cumulé
des callbacks d'environ 5 à 6 %, mais pas le pire retard. Le contrôle anticipé
évite des calculs pendant certaines attentes, mais son changement de cadence
ne constitue pas une amélioration dans les deux régions.

Le report non bloquant conserve les descripteurs en ordre dans un tableau
borné à 128 éléments, propre à ces fixtures. Une tentative WAIT/FULL laisse
le lecteur continuer. Les paquets en attente sont réessayés au paquet suivant,
puis vidés au retour du chargement avant lecture de l'horloge partagée.
Sans service pendant les silences, cette stratégie livre certains paquets
beaucoup trop tard. Les wrappers des fonctions execute/repeat/repeat_disabled/
checkpoint réduisent ce problème, mais restent insuffisants. Ajouter des
appels aux blocs inline coûte aussi du temps natif et n'améliore pas le maximum.
Un vrai ordonnanceur devra garantir la fréquence de service dans les calculs
et les silences, avec une file bornée et une maîtrise du coût par publication.

Les cinq essais passent dans chaque région les 48 cas source et 2 976 octets,
les états finaux RAM/audio, traces IRQ, empreintes de données et absence
d'émission anticipée. Les 960 intervalles de rafale contrôlés au total restent
exactement à 315/630 ticks. Les bornes de lecture d'horloge et de prise de bus
sont respectées, et RAM/image d'arrêt concordent avec le cœur sans observateur.
Cela ne suffit pas à valider le timing. Aucun essai ne remplace la référence,
et aucune preuve des seize points intermédiaires n'est revendiquée ici.

Les changements de planification, du contrôle d'accord et de l'en-tête
d'horloge ont été restaurés aux octets du Git précédent. Les variantes de
publication différée restent accessibles dans les outils de mesure ; elles
ne sont pas intégrées au jeu. L'essai inline est conservé dans son archive,
avec son en-tête et les outils capturés, sans laisser de hook actif dans
les sources du portage.

Les temps des marqueurs de callback excluent les tentatives de publication
faites par les wrappers d'horloge. Ils ne mesurent donc pas toute la charge
du producteur pour ces essais. Les marqueurs PSG empêchent toujours de
revendiquer une onde sonore originale non instrumentée.

Les [résultats synthétiques](md_z80_psg_publication_trials_report.json),
rapports détaillés et l'archive locale `md-z80-publication-trials-v0203`
conservent les captures et sources de chaque essai avant nettoyage vérifié.
