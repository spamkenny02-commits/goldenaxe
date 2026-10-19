# Dates vidéo : divisions natives et essais coopératifs écartés

La ROM recommandée reste **v0203**, SHA-256
`7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7`.
Ce jalon améliore un composant du prototype de cadence ; il ne valide pas le
portage complet et n'introduit pas de nouveau comportement dans la ROM jouable.

## Changement conservé

`source_md_psg_plan_beam` calcule la ligne et la position H32 d'une échéance.
L'ancienne formule effectuait plusieurs divisions/modulos logiciels 32 bits.
La nouvelle sépare d'abord le nombre de lignes et le reste horizontal :

* `DIVU.W 3420` calcule quotient et reste ensemble lorsque le quotient tient
  sur 16 bits ; la garde porte sur le mot haut du dividende.
* Le reste horizontal est arrondi vers le haut par une division 16 bits par 20.
* Le nombre de lignes est réduit modulo 262 ou 313 par une division matérielle
  dont le quotient est borné par le contrat d'horizon inférieur à `2^31`.
* Les très grandes échéances conservent le calcul général pour la première
  division. Les contrôles d'erreur restent atomiques.

Le résultat vidéo est identique, y compris au rebouclage 32 bits, au passage
de fin de ligne et aux discontinuités du compteur V. La précision de sortie
n'est pas augmentée par cette optimisation de préparation.

Le [contrôle du planificateur](md_psg_plan_report.json) passe **21 024 flux sur
hôte et 2 024 par région native**, ainsi que **16 950 conversions vidéo sur
chacune des trois plateformes**. Les 4 300 nouveaux cas couvrent notamment le
passage du quotient 65 535 à 65 536, l'horizon `2^31-1`, différentes lignes de
départ et deux origines temporelles. La référence emploie la formule précédente
fondée sur la période et les tables H/V indépendantes du cœur.

Le [rejeu physique reconstruit](md_psg_replay_beam_report.json) vérifie encore
les **5 952 octets** des 24 chargements, leurs états source et leurs origines
normale/rebouclée. Les retards mesurés sont de 297–2 259 ticks maître NTSC et
300–2 408 PAL, sans écriture anticipée. Les écarts changent légèrement avec le
placement du code ; ils restent inférieurs à une ligne. Chaque dernier état
d'horloge correspond à la lecture physique observée. La RAM complète et l'image
de fin sont identiques avec le cœur normal. Le producteur termine toujours
avant ce rejeu : cela ne prouve pas le fonctionnement simultané du jeu.

## Essais de calcul et audio simultanés

Plusieurs variantes ont réellement exécuté le chargement, le lecteur traduit,
la file et les sorties PSG simultanément : service presque par instruction,
points de service plus espacés, cache d'un groupe, cache de 32 groupes préparés
dès publication, puis appelant minimal avec composition forcée en ligne.
Les octets et les états finaux concordent ; **les échéances ne sont pas tenues**.

| Variante | Retard maximal NTSC | Retard maximal PAL |
| --- | ---: | ---: |
| Vérifications presque par instruction | 5 947 525 | 5 986 150 |
| Points de service et ancienne préparation | 5 182 839 | 5 211 992 |
| Un groupe en cache, divisions natives | 4 090 104 | 4 114 873 |
| Cache de 32 groupes, publication par paquet | 4 069 472 | 4 087 662 |
| Appelant minimal forcé en ligne | 6 555 709 | 6 586 650 |

Valeurs en ticks maître. Les variantes diffèrent aussi dans leurs coûts de
préparation et de compilation ; ce tableau n'isole pas le gain d'une routine.
Le profil avec marqueurs confirme qu'une préparation entre deux sorties
rapprochées prend trop longtemps. Les vérifications fréquentes ajoutent aussi
du travail au producteur. Le cache réduit cette préparation pendant les sorties,
mais ne résout pas le problème global de calcul et d'attente.

Les appels de service optionnels ont donc été **restaurés octet pour octet à
leur état précédent**, après archivage vérifié. Le code expérimental restant
est rangé dans `megadrive/research`, hors des sources compilées par SGDK.
Il ne constitue pas un driver pris en charge. Les rapports coopératifs décrivent
leurs sources figées dans l'archive, et non les sources courantes restaurées.

Le banc complet historique conserve les contrôles intermédiaires ; le banc
coopératif sans copies vérifie les traces d'IRQ et les états finaux. L'appelant
minimal omet également les copies de traces d'IRQ et ne prouve donc pas leurs
états intermédiaires. Toutes ces limites sont conservées avec les mesures.

## Conservation et suite

`analysis/md-cooperative-research-v0203` conserve les sources, scripts, ROMs de
diagnostic et captures de toutes les variantes rejetées. Pour reproduire une
variante, restaurer ensemble ses sources figées et son script dans un espace
isolé : le script courant ne contient plus ces options expérimentales.
Le manifeste et les objets compressés permettent une récupération octet pour
octet. **210 872 918 octets générés** ont été retirés après cette vérification ;
l'archive occupe environ 62 Mo, soit environ 149 Mo récupérés à ce stade.

L'archive finale `analysis/md-beam-divu-v0203` conserve séparément les preuves du
changement retenu. Les ROMs numérotées, la ROM SMS et les sources sont préservées.
Le Git reste local.

La suite doit résoudre la livraison physique sans bloquer ni surcharger le
producteur. Une piste à mesurer est un petit service de sorties PSG sur le Z80
matériel, avec une publication entre processeurs distincte de la file 68000
actuelle. La logique du jeu et le lecteur musical traduit resteraient en 68000.
Cela exige des mesures de précision, de débit et de contention ; aucune réussite
de cette piste n'est encore affirmée. DMA, commandes au bon instant, phase depuis
le démarrage et fidélité du jeu complet restent aussi à vérifier.
