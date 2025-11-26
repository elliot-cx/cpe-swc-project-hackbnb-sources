# Rapport de Correction des Failles de Sécurité

Ce rapport détaille les failles de sécurité corrigées au sein du projet, expliquant la vulnérabilité, ses conséquences potentielles et la résolution appliquée pour chacune.

---

## 1. Injection SQL

*   **Fichier concerné** : `back/api/rooms/rooms_api.py`
*   **Vulnérabilité** : La fonction `list_rooms` construisait une requête SQL brute en utilisant une f-string avec des données fournies par l'utilisateur (`text(f"category = '{category}'")`). Cette méthode ne nettoyant pas l'entrée utilisateur, elle permettait l'exécution de code SQL arbitraire.
*   **Conséquences** : Un attaquant aurait pu manipuler la requête pour contourner les filtres, lire, modifier ou supprimer des informations de l'ensemble de la base de données (par exemple, les utilisateurs, les réservations, etc.).
*   **Résolution** : La requête SQL brute a été remplacée par une requête paramétrée sécurisée via SQLAlchemy (`Room.query.filter_by(category=category)`), qui neutralise les entrées malveillantes.

---

## 2. Lecture Arbitraire de Fichier (Path Traversal)

*   **Fichier concerné** : `back/api/uploads/uploads_api.py`
*   **Vulnérabilité** : L'endpoint `GET /uploads/` permettait aux utilisateurs de spécifier un nom de fichier via le paramètre `name`. Ce nom était ensuite directement concaténé à un chemin de répertoire, rendant possible la lecture de fichiers arbitraires en exploitant des séquences comme `../../`.
*   **Conséquences** : Cette faille permettait de lire des fichiers sensibles sur le serveur, tels que le code source de l'application, les fichiers de configuration, ou même la base de données SQLite (`instance/db.sqlite`).
*   **Résolution** : L'implémentation de `werkzeug.utils.secure_filename` a été ajoutée pour nettoyer et valider le nom de fichier fourni par l'utilisateur. Cela garantit que seul un nom de fichier sûr et valide peut être utilisé, empêchant ainsi l'accès non autorisé à d'autres répertoires.

---

## 3. Server-Side Request Forgery (SSRF)

*   **Fichiers concernés** : `back/api/bookings/bookings_api.py` et `back/services/stripe.py`
*   **Vulnérabilité** : L'endpoint `GET /bookings/<reference>/checkout-lines` acceptait un `checkout_session_id` directement de l'utilisateur pour construire une URL vers l'API Stripe. Sans validation, un attaquant aurait pu forger cet ID pour tenter de faire effectuer des requêtes par le serveur vers des services internes ou externes.
*   **Conséquences** : Un attaquant aurait pu potentiellement utiliser le serveur comme proxy pour scanner des réseaux internes, ou interagir avec des services tiers, et dans le cas de Stripe, tenter de récupérer des informations sensibles sur d'autres sessions (e-mails, adresses, etc.) si l'API le permettait.
*   **Résolution** : Une validation stricte du format du `checkout_session_id` a été ajoutée dans `back/services/stripe.py` à l'aide d'une expression régulière (`^cs_(test|live)_[a-zA-Z0-9]{24,}$`). Si l'ID ne correspond pas au format attendu, une erreur est levée, empêchant la construction d'URLs malveillantes.

---

## 4. Génération Non Sécurisée de Chaîne Aléatoire (D4)

*   **Fichier concerné** : `back/api/bookings/bookings_api.py`
*   **Vulnérabilité** : Le `checkout_confirmation_secret` était généré en se basant sur `time.time()`. L'horodatage étant une valeur prévisible, un attaquant aurait pu deviner le secret généré.
*   **Conséquences** : En devinant le secret de confirmation, un attaquant aurait pu valider une réservation sans avoir payé, exploitant la logique de confirmation de paiement.
*   **Résolution** : La génération a été remplacée par `secrets.token_hex(32)` du module `secrets` de Python, qui fournit une source d'aléa cryptographiquement forte et rend le secret impossible à deviner.

---

## 5. Exposition de l'Adresse E-mail de l'Hôte (D5)

*   **Fichier concerné** : `back/api/rooms/rooms_models.py`
*   **Vulnérabilité** : La méthode `Room.to_dict()` exposait l'intégralité de l'objet `host_user`, y compris l'adresse e-mail, dans les réponses de l'API listant les chambres.
*   **Conséquences** : Cette fuite d'information permettait à n'importe quel utilisateur de l'API de collecter les adresses e-mail des hôtes, ce qui pourrait être utilisé pour du spam, du phishing ou d'autres attaques.
*   **Résolution** : La méthode `Room.to_dict()` a été modifiée pour construire manuellement un dictionnaire pour l'hôte, n'incluant que son `id` et son `name`, et en omettant l'adresse e-mail.

---

## 6. En-têtes de Sécurité Manquantes (D7)

*   **Fichier concerné** : `back/app.py`
*   **Vulnérabilité** : L'application Flask n'envoyait pas d'en-têtes de sécurité HTTP. Notamment, l'absence de `Content-Security-Policy` (CSP) rendait l'application vulnérable à des attaques de type Cross-Site Scripting (XSS), par exemple si la description d'une annonce contenait du code HTML ou JavaScript malveillant.
*   **Conséquences** : Un attaquant aurait pu injecter des scripts dans les navigateurs des utilisateurs, permettant de voler des cookies de session, de rediriger les utilisateurs vers des sites malveillants, ou d'altérer le contenu de la page.
*   **Résolution** : Un gestionnaire `after_request` a été ajouté pour inclure des en-têtes de sécurité stricts à chaque réponse, notamment un `Content-Security-Policy` restrictif, pour empêcher l'exécution de scripts non autorisés.

---

## 7. Exposition de la Version du Serveur (D8)

*   **Fichier concerné** : `nginx/nginx.conf`
*   **Vulnérabilité** : Le serveur Nginx exposait son numéro de version dans l'en-tête HTTP `Server`.
*   **Conséquences** : Cette information, bien que non directement exploitable, aide un attaquant à cibler des vulnérabilités connues pour une version spécifique de Nginx, accélérant ainsi le processus d'attaque.
*   **Résolution** : La directive `server_tokens off;` a été ajoutée à la configuration de Nginx pour supprimer le numéro de version de l'en-tête `Server`.

---

## 8. Clé API Codée en Dur dans l'Historique Git

*   **Fichier concerné** : `back/services/stripe.py`
*   **Vulnérabilité** : Une clé API Stripe a été accidentellement committée dans l'historique du dépôt Git.
*   **Conséquences** : Toute personne ayant accès à l'historique du dépôt pouvait récupérer cette clé et l'utiliser pour effectuer des opérations non autorisées sur le compte Stripe associé, telles que la création de paiements, l'accès à des informations financières, etc.
*   **Résolution** : L'historique Git a été entièrement réécrit avec `git filter-branch` pour supprimer définitivement la clé de tous les commits. La clé a été remplacée par un appel à `os.getenv('STRIPE_API_KEY')` pour la charger de manière sécurisée depuis l'environnement.