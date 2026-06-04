# HorRAGor BOT Partie 2 : L'Agent de l'Horreur
Ce projet consiste à transformer la base de données de films d'horreur de la Partie 1 en une application Web d'IA complète et industrielle.

Les apprenants vont concevoir le "cerveau" du bot en développant un agent conversationnel autonome (RAG avancé) avec LangGraph (boucle ReAct). Cet agent sera doté d'outils spécifiques : un index FAISS pour valider rapidement les identifiants, des fonctions SQL sécurisées sur Supabase pour les infos de base, un moteur de recommandation sémantique (PGVector) pour trouver des films similaires, et un module de web-scraping à la demande (Wikipédia) pour enrichir les synopsis.

Un nœud d'évaluation (Juge) automatisé auditera chaque réponse pour bloquer les hallucinations. Le moteur d'IA sera exposé via une API FastAPI et intégré dans une interface de chat dynamique avec Streamlit.

## Ressources
Voir le fichier '../HoRAGor BOT Partie 2.pdf'

## Contexte du projet
Le développeur IA conçoit et déploie une architecture applicative complète de bout en bout (Full-Stack IA). Il orchestre les scripts de données issus de la phase précédente en créant un agent autonome basé sur une architecture ReAct (Reason + Act) à l'aide de LangGraph. Il encapsule les accès à la base de données relationnelle Supabase sous forme de fonctions Python sécurisées (Tools) pour interdire la génération de requêtes SQL brutes par l'IA. Pour optimiser les performances de routage, il implémente un index en mémoire vive via FAISS permettant la validation instantanée des identifiants de films.

De plus, il intègre une fonction de scraping dynamique à la demande (Wikipedia) pour approfondir les synopsis et un outil de similarité sémantique via Supabase PGVector pour automatiser les recommandations de films. Afin de sécuriser les réponses délivrées, il met en place un nœud d'évaluation automatisé (Juge) qui audite et valide la fidélité de la réponse du modèle avant affichage. Enfin, il expose l'intégralité de ce moteur d'IA à travers une API REST asynchrone développée avec FastAPI, puis conçoit une interface utilisateur de chat dynamique avec Streamlit, connectée à l'API via des requêtes HTTP.

## Modalités pédagogiques
Projet en groupe de 3, un superviseur qui doit intéragir avec les deux autres membres pour orchestrer le travail.
Le travail sera découpé en 2 temps.
- Un apprenant est en charge de l'application
- Un apprenant est en charge de l'api
- Un apprenant est en charge de la bdd FAISS

Puis en groupe vous développerez la boucle ReAct et les tools

## Modalités d'évaluation
L'évaluation prendra la forme d'une soutenance orale de 20 minutes (15 min de démonstration/présentation du code + 5 min de questions-réponses) devant un jury. Les critères sont répartis sur les trois piliers du projet :
- Qualité du code et Industrialisation
- Performance de l'IA Agentic et du RAG
- Interface Applicative (Front + API)

## Livrables
- Le Code Source Applicatif : Un dépôt Git propre et structuré contenant l'intégralité du code (Front Streamlit, API FastAPI, et le moteur LangGraph).
- La Configuration Industrielle : Un fichier pyproject.toml valide et configuré via l'écosystème uv.
- Le Schéma du Graphe : Le diagramme de flux technique exporté (généré via Mermaid) décrivant l'enchaînement de l'agent, des outils et du juge.
- Le Support de Pitch (1 à 2 Slides maximum)

## Critères de performance
- Le routage doit être instantané grâce à l'indexation locale dans FAISS pour valider l'existence du film et récupérer son identifiant.
- L'interface Streamlit ne doit subir aucun gel d'écran grâce à l'asynchronisme des routes de FastAPI.
- Le taux d'hallucination factuelle doit être égal à 0% sur les métadonnées de base (réalisateur, année, genre), l'agent ayant l'obligation stricte d'utiliser les données brutes renvoyées par le connecteur SQL.
- La gestion des limites de connaissances doit être maîtrisée, l'agent devant répondre poliment qu'il ne sait pas si un film est totalement absent de la base et de Wikipédia, plutôt que d'inventer une réponse.
- L'activation du module de web-scraping doit être strictement sélective, ne se déclenchant que si et seulement si la question exige des détails approfondis introuvables en base SQL, afin d'optimiser la fenêtre de contexte.
- Aucune requête SQL brute générée par le LLM ne doit transiter vers Supabase, l'agent devant exclusivement passer par des arguments de fonctions Python typées et sécurisées.