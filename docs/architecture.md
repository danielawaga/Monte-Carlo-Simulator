# Architecture

Le projet suit une architecture en couches:

1. **Modélisation (`models`, `distributions`, `io/validators`)**
   - décrit les objets métier;
   - définit les distributions probabilistes;
   - valide les paramètres d'entrée.

2. **Moteur (`engine`)**
   - génère les tirages vectorisés;
   - agrège les coûts/délais;
   - prépare les futures extensions de corrélation et convergence.

3. **Restitution (`analysis`, `visualization`, `io/exporters`, `streamlit_app`)**
   - calcule les statistiques;
   - produit les graphiques;
   - exporte les résultats;
   - expose une interface utilisateur.

La couche `application` orchestre ces composants sans contenir la logique mathématique.
