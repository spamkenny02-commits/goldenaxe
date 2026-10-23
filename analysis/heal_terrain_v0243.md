# v0243 : bonus de terrain du soin

La routine SMS 3021..3041 double le soin lorsque C041 vaut 2.
La version MD ajoute désormais 32 points dans ce contexte et 16 ailleurs,
puis limite la vie au maximum. Le coût reste 24 points de magie, même lorsque
la vie est pleine. L'objet et sa sélection sont conservés.

Six cas dans chaque région PAL/NTSC : terrain ordinaire, terrain amélioré,
plafonnement, vie pleine, magie insuffisante et terrain amélioré de donjon.
Les mots des deux tuiles sous le héros sont contrôlés ; la classification
du terrain s'exécute normalement sur les deux machines. Un appui maintenu
puis un second appui vérifient la distinction entre maintien et activation.
Les 52 états consécutifs par cas correspondent, soit 624 comparaisons.

Ces essais fournissent la possession, les ressources, la classe de salle,
les deux tuiles et une phase initiale. Ils ne prouvent ni une acquisition
naturelle, ni les pixels complets, ni les formes d'onde audio.

Le sort de la sixième case n'est pas activé dans cette version. Les routines
30A7, 37B3/37BD et 6AFB..6EEF ainsi que les deux ressources graphiques sont
identifiées dans screen_spell_source.asm et screen_spell_reference.json.
Il reste à porter ensemble ses animations, les dégâts et la restauration.

Rapport : [heal_terrain_release_v0243_report.json](heal_terrain_release_v0243_report.json).
