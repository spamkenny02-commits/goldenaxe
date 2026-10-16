# Initialisation des acteurs et registre R (2026-10-16)

Le calcul depuis 16D0 atteint maintenant 1853, juste avant l'allocation
des motifs d'acteurs. Apres les trois tirages d'historique, il efface les
768 octets d'acteurs, lit les huit types de salle, applique les statistiques,
efface les slots selon la persistance et calcule le nombre d'acteurs actifs.
Le masque de persistance provient de l'etat produit par l'historique,
pas d'une mesure intermediaire.

Les 24 scenarios controles passent cinq nouveaux points (17AE,17DE,1805,
1839,1853), soit 35 points par scenario et 840 comparaisons au total.
Chaque nouveau point compare M1/R, phase, duree, 331 octets RAM, 400 octets
audio et les 768 octets d'acteurs. Le nombre C0A2 est compare a 1853.
Les 72 tirages aleatoires precedents restent verifies directement en A.
Les offsets IRQ et les traces SMS completes correspondent aux references.

Le banc isole reutilise la fixture du cout complet des acteurs. Ses six
salles et leurs 256 masques de persistance, soit 1 536 cas, correspondent
pour les durees, M1, R, 768 octets d'acteurs et le compte actif. Il inclut
les slots effaces et les masques mixtes absents des parcours 00/FF.
La routine 1780 et la banque de types/statistiques originales sont intactes.
Le caller synthetique desactive les IRQ ; le modele isole ignore donc les
frontieres IRQ et ne revendique pas une comparaison de phase dans ce banc.
Les IRQ et la phase sont compares sur les 24 parcours en jeu.

Les instructions LD HL,(nn) sont distinguees des LDIR ; ADD IX,DE et
PUSH IX sont comptes avec leurs prefixes, ainsi que RLC C et RES 0,C.
La branche de suppression de boss est explicitement hors perimetre.
Le modele conserve les statistiques et les octets de slots effaces, sans
simuler encore le decodage/allocation des motifs a partir de 1853.

Le coeur distinct ajoute cinq points et un contexte de 769 octets
(acteurs768 et compte1). Son fichier C de travail est restaure apres
compilation. Outils, fixture, captures, references et coeur sont archives
localement avec manifeste SHA-256. ROM v0183 et sources natives inchangees.

Limites : six salles ordinaires, classe 0, contexte HUD de base, bit
persistant 0 actif. Le contenu graphique des acteurs, leur palette,
le heros et la fin du chargement restent a enchainer. C01B/C020..23 et
les sorties hors snapshots restent exclus des comparaisons. Autres
classes/boss, commandes audio non couvertes, fidelite materielle et partie
complete restent ouverts. Le hasard et les delais ne sont pas encore
integres au portage natif.

Reproduire :

- `python tools/build_actor_prefix_refresh_core.py`
- Capturer les six routes et masques 00/FF via
  `profile_paid_passage_loader_phases.main`, repertoire
  `actor-prefix-refresh/TT-MM`, coeur
  `genesis_plus_gx_actorprefixrefresh_libretro.dll`, `capture_music=True`.
- `python tools/validate_actor_prefix_refresh.py`
- `python tools/validate_actor_prefix_refresh_unit.py`
- `python tools/archive_actor_prefix_refresh_research.py`
