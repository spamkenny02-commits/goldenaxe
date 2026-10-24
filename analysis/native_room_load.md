# Chargement natif continu : graphismes, historique et liste d'ennemis

Travail du 24 octobre 2026, apres v0275. La ROM jouable reste v0275 : le
chargement du jeu ne passe pas encore par cette nouvelle chaine.

`source_room_load_class0` compose les routines natives depuis 16D0 jusqu'a
1780 : graphismes, carte, HUD, attente, palette, effacement des anciens
objets et tirages de reapparition. La graine vit dans le contexte IRQ et
l'historique dans les 16 derniers octets de la page DC. Une seule horloge
traverse toutes ces etapes, sans remplacement intermediaire de R, de la
phase, de la graine ou de l'etat musical.

`source_room_load_class0_actors` prolonge cette chaine jusqu'a 1853 avec
`source_actor_list` : effacement des 16 enregistrements, copie des huit
types de la salle, statistiques, persistance, remplacement des boss vaincus
et compteur. Les vues du numero de salle, des masques et du compteur doivent
etre partagees avec celles du chargement. La copie des ressources utilise
les octets ROM, avec les frontieres d'instruction et d'interruption source.
Les erreurs conservent les effets deja executes ; aucun retour arriere ni
nouvelle tentative sur l'etat partiel n'est autorise.

## Preuves et limites

- 24 sorties SMS de passages payants, six destinations exterieures, masques
  00/FF, NTSC/PAL. Les captures de reference sont verifiees par les SHA des
  archives precedentes et la ROM SMS d'origine. La preparation de ces scenes
  est controlee : il ne s'agit pas d'une campagne naturelle.
- Depuis une seule entree 16D0 observee par scene, 22 points correspondent
  jusqu'a 1853 : phase, duree, R, M1, calendrier des IRQ, 331 octets du
  contexte RAM compact et 400 octets musicaux. La graine finale, l'historique,
  les 256 masques, les 768 octets d'ennemis et leur compteur correspondent.
  Les 72 tirages utilisent l'horloge calculee, sans lecture des valeurs
  aleatoires intermediaires dans les captures.
- Les deux variantes (arret1780 et arret1853) sont compilees en 68000 :
  chacune execute les 24 vecteurs dans les deux regions sans divergence,
  soit 96 executions de chaine. Les IRQ physiques MD sont coupees ; les IRQ
  SMS et leur lecteur musical actif sont executes dans l'horloge virtuelle.
- Le module de liste est aussi compare au Z80 original sur 9 216 cas :
  512 salles, six masques et trois progressions. Les 90 cas avec boss vivant
  couvrent notamment 30 remplacements par le cristal et 30 suppressions.
  Ces cas unitaires ont leurs interruptions source coupees. Le remplacement
  de boss interrompu et son execution 68000 ne sont pas prouves par ce banc.

La composition du chargement reste limitee aux six destinations de carte
exterieure deja prises en charge par `source_world_map_load`, avec classe0
changee, bit de sauvegarde0 actif et C0AC nul. Le module de liste peut lire
les 512 listes originales ; cela n'etend pas la portee du chargeur de carte.
La permutation physique des banques est representee par des pointeurs ROM.

1853 precede l'allocation et le chargement des graphismes des ennemis : cette
partie, l'initialisation finale du heros et le retour au jeu restent a porter
sur la meme horloge. L'entree de cette horloge depuis le boot, les autres
classes de carte, le rendu physique, son budget CPU et la campagne complete
restent ouverts. Les durees des cartouches de diagnostic incluent copies et
comparaisons ; elles ne prouvent pas la cadence d'un chargement jouable.

Rapports : [chaine1780](native_room_load_report.json),
[chaine1853](native_room_load_actors_report.json),
[68000 jusqu'a1780](native_room_load_68k_report.json),
[68000 jusqu'a1853](native_room_load_actors_68k_report.json),
[listes et boss](native_actor_list_report.json).
