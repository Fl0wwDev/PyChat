import socket
import threading
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot
from PyQt5.QtWidgets import QApplication
from mysql.connector import Error
import time
import mysql.connector


# Classe pour gérer les interactions avec la base de données
class DatabaseManager:
    """
    Gère les interactions avec la base de données MySQL.

    Attributes:
        db_config (dict): Configuration de la base de données.
    """
    def __init__(self):
        # Configuration de la base de données
        self.db_config = {
            "host": "localhost",
            "user": "root",
            "password": "votre_mot_de_passe",
            "database": "SAE"
        }
    # Exécute une requête SQL
    def execute_query(self, query, params=None):
        """
        Exécute une requête SQL sur la base de données.

        Args:
            query (str): La requête SQL à exécuter.
            params (tuple, optional): Les paramètres à utiliser avec la requête.

        Returns:
            list: Résultats de la requête pour les requêtes SELECT, sinon None.
        """

        # Gestion de la connexion à la base de données et exécution de la requête
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            if query.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
                return results
            connection.commit()
            return None
        except Error as e:
            print(f"Erreur base de données: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                
    # Bannit un utilisateur en ajoutant son nom d'utilisateur à la table des utilisateurs bannis            
    def ban_user(self, username):
        """
        Bannit un utilisateur en ajoutant son nom d'utilisateur à la table des utilisateurs bannis.

        Args:
            username (str): Le nom d'utilisateur à bannir.
        """
        # Requête SQL pour bannir un utilisateur
        sql = "INSERT INTO banned_users (username) VALUES (%s)"
        val = (username,)
        self.execute_query(sql, val)
        
    # Vérifie si un utilisateur est banni
    def is_user_banned(self, username):
        """
        Vérifie si un utilisateur est banni.

        Args:
            username (str): Le nom d'utilisateur à vérifier.

        Returns:
            bool: True si l'utilisateur est banni, False sinon.
        """
        # Requête SQL pour vérifier si un utilisateur est banni
        sql = "SELECT username FROM banned_users WHERE username = %s"
        val = (username,)
        result = self.execute_query(sql, val)
        return len(result) > 0
    
    # Débannit un utilisateur
    def deban_user(self, username):
        """
        Débannit un utilisateur.

        Args:
            username (str): Le nom d'utilisateur à débannir.
        """
        # Requête SQL pour débannir un utilisateur
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            sql = "DELETE FROM banned_users WHERE username = %s"
            val = (username,)
            cursor.execute(sql, val)
            connection.commit()
        except Error as e:
            print(f"Erreur lors de la suppression de l'utilisateur banni: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

# Classe principale du serveur
class ServerBackend(QObject):
    """
    Classe principale du serveur, gérant les connexions clients et la communication.

    Attributes:
        new_message (pyqtSignal): Signal émis lors de la réception d'un nouveau message.
        new_connection (pyqtSignal): Signal émis lors de la connexion d'un nouveau client.
    """
    new_message = pyqtSignal(str)
    new_connection = pyqtSignal(str)

    def __init__(self, host, port):
        """
        Initialise le serveur avec l'adresse et le port spécifiés.

        Args:
            host (str): L'adresse du serveur.
            port (int): Le port du serveur.
        """
        super().__init__()
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}
        self.running = True
        self.db_manager = DatabaseManager()

    # Envoie un message à tous les clients connectés
    def send_server_message(self, message):
        """
        Envoie un message de la part du serveur à tous les clients connectés.

        Args:
            message (str): Le message à envoyer.
        """
        formatted_message = f"Server:{message}"
        self.broadcast_message(formatted_message)
        
    # Envoie l'historique des messages à un client spécifique
    def send_message_history_to_client(self, client_socket):
        """
        Envoie l'historique des messages à un client spécifique.

        Args:
            client_socket (socket): Le socket du client auquel envoyer l'historique.
        """
        message_history = self.get_message_history()
        history_messages = []

        for message in message_history:
            username, content, timestamp = message
            # Formatez l'horodatage pour n'inclure que l'heure et les minutes
            formatted_timestamp = timestamp.strftime("%H:%M")
            formatted_message = f"history {formatted_timestamp} - {username}: {content}"
            history_messages.append(formatted_message)

        # Joindre tous les messages historiques avec des sauts de ligne
        full_history = "\n".join(history_messages)
        self.send_message_to_client(client_socket, full_history)
        
    # Sauvegarde un message dans la base de données
    def save_message_to_db(self, username, channel, message):
        """
        Sauvegarde un message dans la base de données.

        Args:
            username (str): Le nom d'utilisateur qui a envoyé le message.
            channel (str): Le canal où le message a été envoyé.
            message (str): Le contenu du message.
        """
        try:
            sql = "INSERT INTO messages (username, content) VALUES (%s, %s)"
            val = (username, f"{channel}:{message}")

            result = self.db_manager.execute_query(sql, val)
        except mysql.connector.Error as err:
            print(f"Erreur lors de l'insertion du message: {err}")
            
    # Récupère l'historique des messages de la base de données        
    def get_message_history(self):
        """
        Récupère l'historique des messages de la base de données.

        Returns:
            list: Une liste des messages enregistrés dans la base de données.
        """
        query = "SELECT username, content, timestamp FROM messages"
        return self.db_manager.execute_query(query)
    

    def start(self):
        """
        Démarre le serveur et commence à écouter les nouvelles connexions.
        """
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        threading.Thread(target=self.accept_clients, daemon=True).start()
        
    # Accepte les clients et les ajoute à la liste des clients
    def accept_clients(self):
        """
        Accepte les clients et les ajoute à la liste des clients.
        """
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"Nouvelle tentative de connexion de {client_address}")

                # Attendre brièvement pour que le message du client arrive
                time.sleep(0.5)  # Attendre 0.5 seconde (ajuster selon les besoins)

                try:
                    message = client_socket.recv(1024).decode()
                    if message.startswith("Username:"):
                        username = message.split(":", 1)[1]
                    else:
                        print("Format de message inattendu pour le nom d'utilisateur")
                        client_socket.close()
                        continue
                except Exception as e:
                    print(f"Erreur lors de la réception du nom d'utilisateur: {e}")
                    client_socket.close()
                    continue

                # Vérifier si l'utilisateur est banni
                if self.db_manager.is_user_banned(username):
                    print(f"L'utilisateur banni {username} a tenté de se connecter.")
                    client_socket.close()  # Fermer la connexion
                    continue  # Passer à la prochaine tentative de connexion
                
                self.send_message_history_to_client(client_socket)

                # Si l'utilisateur n'est pas banni, procédez normalement
                threading.Thread(target=self.client_thread, args=(client_socket, username)).start()

            except Exception as e:
                print(f"Erreur lors de l'acceptation d'une nouvelle connexion: {e}")
                
    # Gère la communication avec un client
    def client_thread(self, client_socket, username):
        """
        Gère la communication avec un client connecté.

        Args:
            client_socket (socket): Le socket du client.
            username (str): Le nom d'utilisateur du client.
        """
        # Ajoutez le client à la liste des clients actifs
        print(username)
        self.clients[client_socket] = {'address': client_socket.getpeername(), 'username': username}
        print(f"Nom d'utilisateur '{username}' reçu de {client_socket.getpeername()}")

        while self.running:
            try:
                message = client_socket.recv(1024).decode()
                if not message:
                    break  # Sortir de la boucle si aucun message n'est reçu

                # Traitement des messages normaux
                formatted_message = f"{username}:{message}"
                self.new_message.emit(formatted_message)  # Emettre un signal pour l'UI
                self.broadcast_message(formatted_message)  # Diffuser le message à tous les clients

            except Exception as e:
                print(f"Erreur: {e}")
                break

        # Nettoyage après la déconnexion du client
        client_socket.close()
        if client_socket in self.clients:
            del self.clients[client_socket]
        print(f"Client déconnecté: {username}")


    # Envoie un message à un canal spécifique
    def send_message_to_channel(self, channel_name, message):
        """
        Envoie un message à un canal spécifique.

        Args:
            channel_name (str): Le nom du canal où envoyer le message.
            message (str): Le message à envoyer.
        """
        formatted_message = f"{channel_name}: {message}"
        for client_socket in self.clients.keys():
            client_socket.send(formatted_message.encode())

     # Traite les commandes d'administration (kick, ban, etc.)
    def handle_command(self, command, args):
        """
        Traite une commande d'administration envoyée par un client.

        Args:
            command (str): La commande à exécuter.
            args (str): Les arguments de la commande.
        """
        if command == "kick":
            self.kick_user(args)
        elif command == "kill":
            self.kill_server()
        elif command == "ban":
            self.ban_user(args)
        elif command == "deban":
            self.deban_user(args)
            
    # Expulse un utilisateur
    def kick_user(self, username):
        """
        Expulse un utilisateur du serveur.

        Args:
            username (str): Le nom d'utilisateur de l'utilisateur à expulser.
        """
        client_to_kick = None
        for client_socket, info in self.clients.items():
            if info['username'] == username and client_socket.fileno() != -1:
                client_to_kick = client_socket
                break

        if client_to_kick:
            try:
                client_to_kick.close()
            except Exception as e:
                print(f"Erreur lors de la fermeture du socket pour {username}: {e}")

            if client_to_kick in self.clients:
                del self.clients[client_to_kick]
                print(f"L'utilisateur {username} a été expulsé.")
        else:
            print(f"L'utilisateur {username} introuvable ou déjà déconnecté.")
            
    # Ferme le serveur
    def kill_server(self):
        """
        Arrête le serveur et ferme toutes les connexions.
        """
        print("Fermeture du serveur...")  # Message de débogage
        self.running = False
        self.server_socket.close()
        for client_socket in list(self.clients.keys()):
            client_socket.close()
        self.clients.clear()
        QApplication.quit()
         
    # Bannit un utilisateur
    def ban_user(self, username):
        """
        Bannit un utilisateur et ferme sa connexion.

        Args:
            username (str): Le nom d'utilisateur de l'utilisateur à bannir.
        """
        self.kick_user(username)
        self.db_manager.ban_user(username)
        self.broadcast_message(f"Server: L'utilisateur {username} a été banni.")
        print(f"L'utilisateur {username} a été banni.")
        
    # Débannit un utilisateur
    def deban_user(self, username):
        """
        Débannit un utilisateur.

        Args:
            username (str): Le nom d'utilisateur de l'utilisateur à débannir.
        """
        self.db_manager.deban_user(username)
        self.broadcast_message(f"Server: L'utilisateur {username} a été débanni.")
        print(f"L'utilisateur {username} a été débanni.")
        
    # Envoie un message à un client spécifique
    def send_message_to_client(self, client_socket, message):
        """
        Envoie un message à un client spécifique.

        Args:
            client_socket (socket): Le socket du client.
            message (str): Le message à envoyer.
        """
        client_socket.send(message.encode())

    # Diffuse un message à tous les clients connectés
    def broadcast_message(self, message):
        """
        Diffuse un message à tous les clients connectés.

        Args:
            message (str): Le message à diffuser.
        """
        for client_socket in self.clients.keys():
            try:
                if client_socket.fileno() != -1:  # Vérifiez si le socket est toujours ouvert
                    client_socket.send(message.encode())
                    print(f"Message envoyé à {self.clients[client_socket]['username']}")  # Debug

                    # Extraction des informations du message pour les stocker dans la base de données
                    parts = message.split(':', 2)
                    if len(parts) == 3:
                        username, channel, msg = parts
                        self.save_message_to_db(username, channel, msg)
            except Exception as e:
                print(f"Erreur lors de l'envoi du message: {e}")
