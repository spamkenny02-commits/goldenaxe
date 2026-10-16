# Enveloppes natives et registre audio DE — v0188

La routine 854B est maintenant traduite dans `source_audio_envelope.c` :
mode nul, ADSR et les 16 tables de volume. Le composant fournit les 400 octets
de l'état, les cycles Z80, les lectures M1, A, DE, le retour anticipé du
canal et les écritures PSG. Les coûts ne pilotent pas encore l'horloge du jeu.

La commande de table83 incrémente DE puis lit à cette adresse. L'ancien
lecteur natif utilisait l'octet suivant dans la table d'enveloppe. Le jeu
conserve désormais `sound_source_de` entre les canaux : file prioritaire,
séquences, initialisation de modulation, transposition, enveloppes et
restauration. Les 32 premiers Kio de ROM fixe sont disponibles pour ces
lectures, à la place du seul fragment0000..0400. Les autres ressources de
`intro_data.c` restent identiques ; la ROM jouable reste à1Mio.

Les terminaisons81/82 de la table de hauteur quittent maintenant le canal
avant l'enveloppe et l'écriture de fréquence, conformément au déroulement
source. Les indices qui atteignent ces chemins dans les tests sont
synthétiques et hors des huit tables de hauteur habituelles.

## Vérifications ciblées

- 53 600 cas sur hôte puis sur code68000 sous Genesis Plus GX, en PAL et
  NTSC : 40 192 ADSR, 13 400 tables, huit refus de lecture hors mémoire
  capturée. Les fixtures reconstruisent sans perte les 400 octets et les
  comparent directement ; T/M1/A/DE, retour anticipé et décision PSG passent.
  Les entrées sont distribuées sur les sept emplacements de canaux.
- Les modèles ADSR/table proviennent des comparaisons précédentes des
  instructions854B/8602/863E originales, avec état, cycles, M1, R, A et DE.
- Dans la ROM jouable : 32 scénarios (13 musiques, bruitageA6 et deux
  scénarios prioritaires/restauration, dans deux régions) ×700 retours =
  22 400 comparaisons de DE et de399 octets, hors routage GG. Le DE source
  est observé au retour réel du lecteur8000, sans le déduire du modèle.
- 48 cas supplémentaires, après injection contrôlée et une interruption :
  table83 avec dix DE différents produits par le canal précédent, six
  limites ADSR avec/sans emprunt du bruit, deux terminaisons de hauteur81/82,
  le tout en PAL et NTSC. DE et les400 octets correspondent à la ROM SMS
  exécutée et au modèle indépendant.
- Régressions : 13 musiques, 29 bruitages ordinaires, 29 effets prioritaires
  dans les deux régions, fondu87/B0/82 et parcours naturels du menu.

## Limites et suite

Le composant lit la ROM fixe, la banque6 et la fenêtre RAM sonore DE00..DF8F.
Les autres zones RAM et leurs miroirs ne sont pas encore capturés dans son
interface ; une lecture non disponible est refusée sans mutation. Les tests
ne prouvent pas tous les états possibles ni les événements naturels du jeu
qui y conduisent. Les formes d'onde et la console physique restent hors
validation.

Il reste à traduire le comptage des hauteurs, des séquences et des canaux,
compléter les commandes hors modèle (notamment F2 du canal de bruit), puis
raccorder l'interruption dynamique, l'horloge, R et le hasard original.
Le hasard SGDK et les budgets fixes restent en production. La partie complète
et la fidélité globale du portage restent à vérifier.
