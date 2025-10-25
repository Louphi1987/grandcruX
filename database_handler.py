import psycopg2
import os

class DatabaseHandler:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.connection = self._get_connection()  # Se connecter à la base de données à l'initialisation
        self.create_tables()  # Créer les tables une fois la connexion établie


    def _get_connection(self):
        # Analyse l'URL de la forme : postgresql+psycopg2://user:password@host/db
        result = urlparse(self.database_url)

        return psycopg2.connect(
            dbname=result.path[1:],           # enlève le '/' du début
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port or 5432
        )


    def close(self):
        try:
            # Commit des changements (si nécessaire)
            self.conn.commit()
            # Fermeture du curseur
            self.cursor.close()
            # Fermeture de la connexion
            self.conn.close()
        except Exception as e:
            print(f"⚠ Échec de la fermeture de la connexion : {e}")
        
          
    def create_tables(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Crée la table Person
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Person (
                id SERIAL PRIMARY KEY,
                nom TEXT,
                prenom TEXT,
                naissance TEXT,
                lieu TEXT,
                nationalite TEXT,
                mail TEXT,
                tel TEXT,
                domicile TEXT,
                profession TEXT
            )
        """)
        
        # Crée la table Appointment (Rendez-vous)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Appointment (
                id SERIAL PRIMARY KEY,
                person_id INTEGER,
                date TEXT,
                start_time TEXT,
                end_time TEXT,
                feedback TEXT,
                commentaire TEXT,
                production TEXT,
                FOREIGN KEY (person_id) REFERENCES Person(id) ON DELETE CASCADE
            )
        """)
        
        # Crée la table Crédits
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Credit (
                id SERIAL PRIMARY KEY,
                person_id INTEGER,
                montant REAL,
                description TEXT,
                date TEXT,
                FOREIGN KEY (person_id) REFERENCES Person(id) ON DELETE CASCADE
            )
        """)
    
        # Crée la table AuditRemarques
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AuditRemarques (
                id SERIAL PRIMARY KEY,
                id_remarque TEXT,
                contenu TEXT,
                date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
      
        # Crée la table PacteadjointRemarques
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS PacteadjointRemarques (
                id SERIAL PRIMARY KEY,
                id_remarque TEXT,
                contenu TEXT,
                date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crée la table Notes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Notes (
                id SERIAL PRIMARY KEY,
                type_sujet TEXT,
                contenu TEXT,
                date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Crée la table Documents
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Document (
                id SERIAL PRIMARY KEY,
                person_id INTEGER,
                document_type TEXT,
                file_path TEXT,
                FOREIGN KEY (person_id) REFERENCES Person(id) ON DELETE CASCADE
            )
        """)
        
        # Table Profil
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Profil (
                id SERIAL PRIMARY KEY,
                person_id INTEGER UNIQUE,
                type_profil TEXT DEFAULT 'sans objet', -- défensif, neutre, dynamique, sans objet
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (person_id) REFERENCES Person(id) ON DELETE CASCADE
            )
        """)

        # Table ConnaissanceExperience
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ConnaissanceExperience (
                id SERIAL PRIMARY KEY,
                person_id INTEGER NOT NULL,
                produit TEXT NOT NULL,
                connaissance TEXT CHECK (connaissance IN ('✅', '❌', 'sans objet')) DEFAULT 'sans objet',
                experience TEXT CHECK (experience IN ('✅', '❌', 'sans objet')) DEFAULT 'sans objet',
                FOREIGN KEY (person_id) REFERENCES Person(id) ON DELETE CASCADE,
                UNIQUE (person_id, produit)
            )
        """)
        
        # Table Profil
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Fonds (
                id SERIAL PRIMARY KEY,
                nom TEXT,
                description TEXT,
                type_profil_cible TEXT  -- défensif, neutre, dynamique
            )
        """)
        # Table Fonds
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AchatFonds (
                id SERIAL PRIMARY KEY,
                person_id INTEGER REFERENCES Person(id) ON DELETE CASCADE,
                isin TEXT NOT NULL,
                ticker TEXT NOT NULL,  
                nom_fonds TEXT,
                date_achat DATE NOT NULL,
                prix_part NUMERIC(10, 4) NOT NULL,
                quantite NUMERIC(12, 4) NOT NULL,
                devise TEXT DEFAULT 'EUR',
                frais_achat NUMERIC(10, 2) DEFAULT 0.00,
                source TEXT, 
                commentaire TEXT,
                date_enregistrement TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.close()
        conn.commit()
        conn.close()
        
        
        
        
    # Création d'une personne
    def create_person(self, nom: str, prenom: str, naissance: str, lieu: str, nationalite: str, mail: str, tel: str, domicile: str, profession: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Person (nom, prenom, naissance, lieu, nationalite, mail, tel, domicile, profession)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (nom, prenom, naissance, lieu, nationalite, mail, tel, domicile, profession))
        cursor.close()
        conn.commit()
        conn.close()

    # Récupérer les données du client à partir de son ID (utilisé pour le drop-documents)
    def get_person_by_id(self, client_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, prenom FROM Person WHERE id = %s", (client_id,))
        client = cursor.fetchone()  # Récupère une seule ligne
        cursor.close()
        conn.close()
        return client

        # Récupérer toutes les personnes
    def get_all_persons(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nom, prenom, naissance, lieu, nationalite, mail, tel, domicile, profession
            FROM Person
        """)
        persons = cursor.fetchall()
        cursor.close()
        conn.close()
        return persons

    def delete_client(self, client_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Person WHERE id = %s", (client_id,))
        cursor.close()
        conn.commit()
        conn.close()

    # Ajouter un rendez-vous (Appointment)
    def add_appointment(self, person_id: int, date: str, start_time: str, end_time: str, feedback: str, commentaire: str, production: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Appointment (person_id, date, start_time, end_time, feedback, commentaire, production)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (person_id, date, start_time, end_time, feedback, commentaire, production))
        cursor.close()
        conn.commit()
        conn.close()
        
        
    # Obtenir les rendez-vous d'un client spécifique
    def get_appointments_for_client(self, person_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, start_time, end_time, feedback, commentaire, production
            FROM Appointment
            WHERE person_id = %s
            ORDER BY date, start_time
        """, (person_id,))
        appointments = cursor.fetchall()
        cursor.close()
        conn.close()
        return appointments
        
    def get_appointments_for_date_and_client(self, date: str, person_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, start_time, end_time, feedback, commentaire, production
            FROM Appointment
            WHERE date = %s AND person_id = %s
        """, (date, person_id))
        appointments = cursor.fetchall()
        cursor.close()
        conn.close()
        return appointments
        
    def get_all_appointments(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, a.date, a.start_time, a.end_time, a.feedback, a.commentaire, p.nom, p.prenom
            FROM Appointment a
            JOIN Person p ON a.person_id = p.id
        """)
        appointments = cursor.fetchall()
        cursor.close()
        conn.close()
        return appointments
            
    # Ajouter un crédit pour une personne spécifique
    def add_credit(self, person_id: int, montant: float, description: str, date: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Credit (person_id, montant, description, date)
            VALUES (%s, %s, %s, %s)
        """, (person_id, montant, description, date))
        cursor.close()
        conn.commit()
        conn.close()

    # Obtenir les crédits pour une personne
    def get_credits_for_person(self, person_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT montant, description, date
            FROM Credit
            WHERE person_id = %s
        """, (person_id,))
        credits = cursor.fetchall()
        cursor.close()
        conn.close()
        return credits
    
    # Ajouter une remarque dans AuditRemarques
    def add_remarque(self, id_remarque: str, contenu: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO AuditRemarques (id_remarque, contenu)
            VALUES (%s, %s)
        """, (id_remarque, contenu))
        cursor.close()
        conn.commit()
        conn.close()

        # Récupérer une remarque dans AuditRemarques
    def get_remarque(self, id_remarque: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT contenu
            FROM AuditRemarques
            WHERE id_remarque = %s
            ORDER BY id DESC
        """, (id_remarque,))
        remarque = cursor.fetchone()
        cursor.close()
        conn.close()
        return remarque[0] if remarque else ""
        
    # Récupérer toutes les remarques (id_remarque + contenu de AuditRemarques)
    def get_all_remarques(self, id_remarque: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT contenu
            FROM AuditRemarques
            WHERE id_remarque = %s
            ORDER BY id DESC
            LIMIT 1
        """, (id_remarque,))
        remarques = cursor.fetchone()
        cursor.close()
        conn.close()
        return remarques
        
    def get_all_remarquescommentairesAudit(self, id_remarque: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT contenu, date_modification
            FROM AuditRemarques
            WHERE id_remarque = %s
            ORDER BY date_modification DESC
        """, (id_remarque,))
        remarques = cursor.fetchall()
        cursor.close()
        conn.close()
        return remarques
        
    # Ajouter une remarque dans PacteadjointRemarques
    def add_remarque_PA(self, id_remarque: str, contenu: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO PacteadjointRemarques (id_remarque, contenu)
            VALUES (%s, %s)
        """, (id_remarque, contenu))
        cursor.close()
        conn.commit()
        conn.close()

    # Récupérer une remarque dans PacteadjointRemarques
    def get_remarque_PA(self, id_remarque: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT contenu
            FROM PacteadjointRemarques
            WHERE id_remarque = %s
            ORDER BY date_modification DESC
        """, (id_remarque,))
        remarque = cursor.fetchone()
        cursor.close()
        conn.close()
        return remarque[0] if remarque else ""
        
    # Récupérer toutes les remarques pour un id_remarque dans PacteadjointRemarques
    def get_all_remarques_PA(self, id_remarque: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT contenu, date_modification
            FROM PacteadjointRemarques
            WHERE id_remarque = %s
            ORDER BY date_modification DESC
        """, (id_remarque,))
        remarques = cursor.fetchall()
        cursor.close()
        conn.close()
        return remarques


    def add_note(self, type_sujet: str, contenu: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Notes (type_sujet, contenu)
            VALUES (%s, %s)
        """, (type_sujet, contenu))
        cursor.close()
        conn.commit()
        conn.close()


    def get_all_notes(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT type_sujet, date_modification, contenu
            FROM Notes
            ORDER BY date_modification DESC
        """)
        notes = cursor.fetchall()
        cursor.close()
        conn.close()
        return notes

    def save_document(self, person_id: int, document_type: str, file_path: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Document (person_id, document_type, file_path)
            VALUES (%s, %s, %s)
        """, (person_id, document_type, file_path))
        cursor.close()
        conn.commit()
        conn.close()

    def view_documents(self, client_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT document_type, file_path 
            FROM Document 
            WHERE person_id = %s
        """, (client_id,))
        documents = cursor.fetchall()
        cursor.close()
        conn.close()
        return documents
        
    def create_profil(self, person_id: int, type_profil: str = 'sans objet'):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Profil (person_id, type_profil)
            VALUES (%s, %s)
            ON CONFLICT (person_id) DO UPDATE SET
                type_profil = EXCLUDED.type_profil,
                date_creation = CURRENT_TIMESTAMP
        """, (person_id, type_profil))
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_profil_by_person(self, person_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT type_profil FROM Profil WHERE person_id = %s
        """, (person_id,))
        profil = cursor.fetchone()
        cursor.close()
        conn.close()
        return profil

    PRODUITS = [
        "epargne_pension",
        "epargne_long_terme",
        "branche_21",
        "structure_100",
        "structure_sans_protection",
        "fonds_sans_protection",
        "branche_23",
        "etf",
        "obligation",
        "obligation_complexe",
        "action",
        "hedge_fund"
    ]

    def create_connaissance_experience(self, person_id: int, produit: str, connaissance: str, experience: str):
        # Valeurs par défaut si vide
        if connaissance == '':
            connaissance = 'sans objet'
        if experience == '':
            experience = 'sans objet'

        # Normalisation (enlever U+FE0F si présent)
        connaissance = connaissance.replace('\uFE0F', '')
        experience = experience.replace('\uFE0F', '')

        # Validation stricte (avec les emojis "propres")
        assert connaissance in ['✅', '❌', 'sans objet'], "Valeur de connaissance invalide"
        assert experience in ['✅', '❌', 'sans objet'], "Valeur d'expérience invalide"
        assert produit in self.PRODUITS, "Produit invalide"

        # Insertion/Update dans la base
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ConnaissanceExperience (person_id, produit, connaissance, experience)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (person_id, produit) DO UPDATE SET
                connaissance = EXCLUDED.connaissance,
                experience = EXCLUDED.experience
        """, (person_id, produit, connaissance, experience))
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_connaissance_by_person(self, person_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT produit, connaissance, experience FROM ConnaissanceExperience WHERE person_id = %s
        """, (person_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return {row[0]: {"connaissance": row[1], "experience": row[2]} for row in rows}

    def initialiser_connaissance_experience(self, person_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        for produit in self.PRODUITS:
            cursor.execute("""
                INSERT INTO ConnaissanceExperience (person_id, produit, connaissance, experience)
                VALUES (%s, %s, 'sans objet', 'sans objet')
                ON CONFLICT (person_id, produit) DO NOTHING
            """, (person_id, produit))
        conn.commit()
        cursor.close()
        conn.close()

    def insert_achat_fonds(self, person_id, isin, ticker, nom_fonds,
                           date_achat, prix_part, quantite, devise,
                           frais_achat=0.00, source=None, commentaire=None):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
          INSERT INTO AchatFonds (
            person_id, isin, ticker, nom_fonds,
            date_achat, prix_part, quantite, devise,
            frais_achat, source, commentaire
          ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (person_id, isin, ticker, nom_fonds,
              date_achat, prix_part, quantite, devise,
              frais_achat, source, commentaire))
        conn.commit()
        cur.close()
        conn.close()

    def add_fund_purchase(self, person_id, isin, ticker, nom_fonds, date_achat, prix_part, quantite, frais=0.0,
                          source=None,
                          commentaire=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO AchatFonds (person_id, isin, ticker, nom_fonds, date_achat, prix_part, quantite, frais_achat, source, commentaire)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (person_id, isin, ticker, nom_fonds, date_achat, prix_part, quantite, frais, source, commentaire))
        conn.commit()
        cursor.close()
        conn.close()

    def delete_fund_purchase(self, achat_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM AchatFonds WHERE id = %s", (achat_id,))
        conn.commit()
        cursor.close()
        conn.close()

    def partial_sell(self, achat_id, quantite_vendue):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT quantite FROM AchatFonds WHERE id = %s", (achat_id,))
        result = cursor.fetchone()

        if result:
            quantite_existante = float(result[0])
            quantite_restante = round(quantite_existante - quantite_vendue, 6)

            if quantite_restante >= 0.0001:
                cursor.execute(
                    "UPDATE AchatFonds SET quantite = %s WHERE id = %s",
                    (quantite_restante, achat_id)
                )
            else:
                cursor.execute(
                    "DELETE FROM AchatFonds WHERE id = %s",
                    (achat_id,)
                )

            conn.commit()

        cursor.close()
        conn.close()

    def get_achats_fonds(self, client_id):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
          SELECT isin, ticker, nom_fonds, date_achat, prix_part, quantite, devise
          FROM AchatFonds
          WHERE person_id = %s
          ORDER BY date_achat
        """, (client_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [
            {
                "isin": r[0],
                "ticker": r[1],
                "nom_fonds": r[2],
                "date_achat": r[3].isoformat(),
                "prix_part": float(r[4]),
                "quantite": float(r[5]),
                "devise": r[6],
            }
            for r in rows
        ]

    def update_fund_quantity(self, achat_id, nouvelle_quantite):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE AchatFonds
            SET quantite = %s
            WHERE id = %s
        """, (nouvelle_quantite, achat_id))
        conn.commit()
        cursor.close()
        conn.close()

    def get_achat_id(self, person_id, ticker):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM AchatFonds
            WHERE person_id = %s AND ticker = %s
            ORDER BY date_achat ASC
            LIMIT 1
        """, (person_id, ticker))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        return row[0] if row else None

    def get_valeur_part(self, ticker):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT valeur_part FROM Fonds WHERE ticker = %s", (ticker,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            return float(result[0])
        return None
